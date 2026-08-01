from datetime import datetime, timedelta, timezone

import numpy as np
import structlog
import torch
from aurora import AuroraV1p5, Batch, Metadata, insolation, rollout
from aurora.normalisation import level_to_str, locations, scales

log = structlog.get_logger()


# pip install microsoft-aurora

# 1. Initialize the Aurora 1.5 model
# Aurora 1.5 includes surface radiation fluxes (e.g. ssrd_1h) and prescribed solar insolation.
log.info("Loading Aurora 1.5 Foundation Model")
model = AuroraV1p5()
# Downloads the pretrained Aurora 1.5 checkpoint from HuggingFace (ikwessel/aurora-1.5).
model.load_checkpoint()
model.eval()

# Run inference on GPU (a2-highgpu-1g provides 1x NVIDIA A100 40GB).
device = "cuda" if torch.cuda.is_available() else "cpu"
log.info("Using device", device=device)
model = model.to(device)

# 2. Define target location coordinates (San Leandro, CA)
TARGET_LAT = 37.72
TARGET_LON = -122.16

# 3. Formulate structural gridded inputs
# Aurora operates on a global 0.25-degree grid.
latitudes = np.linspace(90, -90, 721, dtype=np.float32)
longitudes = np.linspace(0, 359.75, 1440, dtype=np.float32)
H, W = len(latitudes), len(longitudes)

# Convert targeted -122.16 longitude to 0-360 scale
lon_360 = TARGET_LON % 360

# Locate closest matrix indices for your target coordinate
lat_idx = np.abs(latitudes - TARGET_LAT).argmin()
lon_idx = np.abs(longitudes - lon_360).argmin()

# 4. Mock the required atmospheric input tensors
# In practice, you would load real atmospheric initial states from ERA5 or IFS via cdsapi.
# The model needs a 2-step history; `time` in the metadata is the time of the *last* step.
#
# Mock values are sampled near each variable's normalisation statistics: uniform values
# in [0, 1) are hundreds of standard deviations out of distribution for physical fields
# like msl (~101,325 Pa), which blows up activations under fp16 autocast and yields NaNs.
def mock_field(name, *shape):
    return locations[name] + 0.1 * scales[name] * torch.randn(*shape)


T = 2
# Current UTC time truncated to the hour; Aurora metadata times are naive UTC.
init_time = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0, tzinfo=None)
history_times = [init_time - timedelta(hours=6), init_time]

# Input surface variables are the model's surface variables minus the output-only ones
# (i10fg, blh, uvb_1h, ssrd_1h, ttr_1h, ...), which the model zero-pads internally.
input_surf_vars = [v for v in model.surf_vars if v not in model.output_only_surf_vars]

surf_vars = {}
for v in input_surf_vars:
    if v == "insolation":
        # Prescribed top-of-atmosphere solar insolation, computed for each history time.
        sol = np.stack(
            [insolation([t], latitudes, longitudes, enforce_2d=True)[0] for t in history_times]
        )
        surf_vars[v] = torch.tensor(sol, dtype=torch.float32)[None]  # (1, T, H, W)
    else:
        surf_vars[v] = mock_field(v, 1, T, H, W)

# The model does not clip user-provided first-step inputs (clamp_at_first_step=False),
# and "scaled_*" variables are log-transformed on the way in, so even a few negative
# mock values (e.g. scaled_sd) become NaN and poison the entire forecast. Clamp each
# mocked variable to its valid physical range using the model's own clipping ranges.
for v, bounds in model.rollout_input_clipping.items():
    if v in surf_vars:
        surf_vars[v] = surf_vars[v].clamp(min=bounds.get("min"), max=bounds.get("max"))

static_vars = {v: mock_field(v, H, W) for v in model.static_vars}

atmos_levels = (50, 100, 150, 200, 250, 300, 400, 500, 600, 700, 850, 925, 1000)
# Atmospheric normalisation statistics are per pressure level, keyed "{var}_{level}".
atmos_vars = {
    v: torch.stack(
        [mock_field(f"{v}_{level_to_str(l)}", 1, T, H, W) for l in atmos_levels], dim=2
    )
    for v in model.atmos_vars
}
# Specific humidity must be non-negative (mocks at the top levels can dip below zero).
atmos_vars["q"] = atmos_vars["q"].clamp(min=0)

input_batch = Batch(
    surf_vars=surf_vars,
    static_vars=static_vars,
    atmos_vars=atmos_vars,
    metadata=Metadata(
        lat=torch.from_numpy(latitudes),
        lon=torch.from_numpy(longitudes),
        time=(init_time,),
        atmos_levels=atmos_levels,
    ),
)

# 5. Execute Rollout Prediction
# Aurora's base time-step is 6 hours. Aurora 1.5 supports variable lead times, so we
# sub-step each main step hourly: 4 main steps x 6 fine lead times = 24 hourly forecasts.
log.info("Running forward rollout for hourly solar irradiance forecasting")
input_batch = input_batch.to(device)
with torch.inference_mode():
    # Inference runs on the GPU; each prediction is offloaded to CPU as it is produced
    # so the 24 global-grid forecasts don't accumulate in GPU memory during the rollout.
    predictions = [
        pred.to("cpu")
        for pred in rollout(model, input_batch, steps=4, fine_lead_times=[1, 2, 3, 4, 5, 6])
    ]

# 6. Extract surface solar radiation for your coordinates
# "ssrd_1h" is surface shortwave (solar) radiation downwards, accumulated over the
# preceding hour in J/m^2; dividing by 3600 s gives the mean flux in W/m^2.
log.info("Solar irradiance forecast", lat=TARGET_LAT, lon=TARGET_LON)
for pred in predictions:
    valid_time = pred.metadata.time[0]
    # Tensor shape mapping: (batch, time, lat, lon)
    ssrd_joules = pred.surf_vars["ssrd_1h"][0, 0, lat_idx, lon_idx].item()
    log.info(
        "Predicted GHI",
        valid_time=f"{valid_time:%Y-%m-%d %H:%M} UTC",
        ghi_w_m2=round(ssrd_joules / 3600, 1),
    )
