import pickle
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import structlog
import torch
from aurora import AuroraV1p5, Batch, Metadata, insolation, rollout
from aurora.normalisation import locations
from huggingface_hub import hf_hub_download

log = structlog.get_logger()


# pip install microsoft-aurora

STATE_PATH = Path(__file__).parent / "aurora_input_state.npz"  # Written by the prefetch.
STATIC_NAME = "aurora-0.25-v1.5-static.pickle"

# 1. Initialize the Aurora 1.5 model
# Aurora 1.5 includes surface radiation fluxes (e.g. ssrd_1h) and prescribed solar insolation.
# The pretrained checkpoint and static-variables pickle (HuggingFace ikwessel/aurora-1.5)
# are resolved against the local cache only -- downloading is split into
# example_msft_aurora_prefetch.py, which uses the same repo/filename/revision defaults,
# so this never touches the network.
try:
    ckpt_path = hf_hub_download(
        repo_id=AuroraV1p5.default_checkpoint_repo,
        filename=AuroraV1p5.default_checkpoint_name,
        revision=AuroraV1p5.default_checkpoint_revision,
        local_files_only=True,
    )
    static_path = hf_hub_download(
        repo_id=AuroraV1p5.default_checkpoint_repo,
        filename=STATIC_NAME,
        revision=AuroraV1p5.default_checkpoint_revision,
        local_files_only=True,
    )
except Exception:
    log.error("Aurora checkpoint/static vars not cached; run example_msft_aurora_prefetch.py first")
    raise SystemExit(1)

log.info("Loading Aurora 1.5 Foundation Model", checkpoint=ckpt_path)
model = AuroraV1p5()
model.load_checkpoint_local(ckpt_path)
model.eval()

# Run inference on GPU (a2-highgpu-1g provides 1x NVIDIA A100 40GB).
device = "cuda" if torch.cuda.is_available() else "cpu"
log.info("Using device", device=device)
model = model.to(device)

# 2. Define target location coordinates (San Leandro, CA)
TARGET_LAT = 37.72
TARGET_LON = -122.16

# 3. Load the prefetched ECMWF open data initial conditions
# The real atmospheric state Aurora steps forward from: 14 surface fields plus z/u/v/t/q
# at 13 pressure levels, at t-6h and t0, saved by the prefetch on Aurora's native
# 0.25-degree grid. The forecast is initialized from the saved cycle time, not "now".
if not STATE_PATH.exists():
    log.error("No prefetched input state; run example_msft_aurora_prefetch.py first", path=str(STATE_PATH))
    raise SystemExit(1)

with np.load(STATE_PATH) as data:
    init_time = datetime.fromisoformat(data["__date__"].item())
    state = {name: data[name] for name in data.files if name != "__date__"}

age_hours = (datetime.now(timezone.utc).replace(tzinfo=None) - init_time).total_seconds() / 3600
log.info("Using initial conditions", date=str(init_time), age_hours=round(age_hours, 1), num_fields=len(state))
if age_hours > 12:
    log.warning("Input state is stale; re-run example_msft_aurora_prefetch.py for the latest cycle")

# Aurora operates on a global 0.25-degree grid.
latitudes = np.linspace(90, -90, 721, dtype=np.float32)
longitudes = np.linspace(0, 359.75, 1440, dtype=np.float32)
H, W = len(latitudes), len(longitudes)

# Convert targeted -122.16 longitude to 0-360 scale
lon_360 = TARGET_LON % 360

# Locate closest matrix indices for your target coordinate
lat_idx = np.abs(latitudes - TARGET_LAT).argmin()
lon_idx = np.abs(longitudes - lon_360).argmin()

# 4. Assemble the input batch
# The model needs a 2-step history; `time` in the metadata is the time of the *last* step.
T = 2
history_times = [init_time - timedelta(hours=6), init_time]

# Input surface variables are the model's surface variables minus the output-only ones
# (i10fg, blh, uvb_1h, ssrd_1h, ttr_1h, ...), which the model zero-pads internally.
input_surf_vars = [v for v in model.surf_vars if v not in model.output_only_surf_vars]

# Open data lacks four of the input fields: the low/mid/high cloud-cover split (it only
# publishes total cloud cover, which IS real here via tcc) and sea-ice concentration.
# Fill those with their normalisation means -- i.e. climatology-constant fields.
CLIMATOLOGY_FILLED = ("lcc", "mcc", "hcc", "ci")

surf_vars = {}
for v in input_surf_vars:
    if v == "insolation":
        # Prescribed top-of-atmosphere solar insolation, computed for each history time.
        sol = np.stack(
            [insolation([t], latitudes, longitudes, enforce_2d=True)[0] for t in history_times]
        )
        surf_vars[v] = torch.tensor(sol, dtype=torch.float32)[None]  # (1, T, H, W)
    elif v in CLIMATOLOGY_FILLED:
        surf_vars[v] = torch.full((1, T, H, W), locations[v], dtype=torch.float32)
    else:
        surf_vars[v] = torch.from_numpy(state[v])[None]  # (1, T, H, W)

# GRIB packing can nudge values slightly out of physical range (e.g. tiny negative snow
# depths), and "scaled_*" variables are log-transformed on the way in, so clamp each
# variable to its valid physical range using the model's own clipping ranges.
for v, bounds in model.rollout_input_clipping.items():
    if v in surf_vars:
        surf_vars[v] = surf_vars[v].clamp(min=bounds.get("min"), max=bounds.get("max"))

# Static fields (orography, land-sea mask, soil/vegetation-type one-hots, ...) come from
# the pickle shipped alongside the checkpoint, already on the same grid orientation.
with open(static_path, "rb") as f:
    static_data = pickle.load(f)
static_vars = {
    v: torch.as_tensor(np.asarray(static_data[v]), dtype=torch.float32) for v in model.static_vars
}

atmos_levels = (50, 100, 150, 200, 250, 300, 400, 500, 600, 700, 850, 925, 1000)
atmos_vars = {
    v: torch.stack([torch.from_numpy(state[f"{v}_{l}"]) for l in atmos_levels], dim=1)[None]
    for v in model.atmos_vars
}  # (1, T, C, H, W)
# Specific humidity must be non-negative (GRIB packing can dip below zero at top levels).
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
# preceding hour in J/m^2; dividing by 3600 s gives the hourly-mean flux in W/m^2
# (what the solar industry reports as hourly-mean GHI). Irradiance is non-negative,
# but nothing constrains the regression output: night-time values can dip slightly
# below zero, so clamp to the physical range (as the Chronos example does).
log.info("Solar irradiance forecast", lat=TARGET_LAT, lon=TARGET_LON)
for pred in predictions:
    valid_time = pred.metadata.time[0]
    # Tensor shape mapping: (batch, time, lat, lon)
    ssrd_joules = max(0.0, pred.surf_vars["ssrd_1h"][0, 0, lat_idx, lon_idx].item())
    log.info(
        "Predicted hourly mean SSRD",
        valid_time=f"{valid_time:%Y-%m-%d %H:%M} UTC",
        ssrd_w_m2=round(ssrd_joules / 3600, 1),
    )
