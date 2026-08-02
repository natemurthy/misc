import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pvlib
import structlog
import torch
from anemoi.inference.runners.simple import SimpleRunner

from example_ecmwf_ifs_hres_solar import disaggregate_window

log = structlog.get_logger()

# Silence two known-benign upstream warnings so the forecast output stays readable:
# - anemoi-inference patches its own (nominally immutable) DotDict config at load time;
# - anemoi-models' imputer uses a list-based tensor index that torch deprecated. It
#   fires once per rollout step. Revisit if anemoi is upgraded past 0.8.x/0.11.x.
warnings.filterwarnings("ignore", message="Modifying an instance of DotDict")
warnings.filterwarnings("ignore", message="Using a non-tuple sequence for multidimensional indexing")

# See README.md ("Setup" section) for the environment setup. Downloads (checkpoint and
# open data initial conditions) live in example_ecmwf_aifs_ens_prefetch.py -- run that
# first; this script only loads what was prefetched and runs inference.

# 1. Configure the AIFS ENS 2.0 run
# AIFS ENS 2.0 runs on the N320 reduced Gaussian grid (~0.25 deg, 542,080 points) with a
# 6-hour time step, and predicts ssrd as an output-only diagnostic.
CHECKPOINT = {"huggingface": "ecmwf/aifs-ens-2.0"}
STEP_HOURS = 6
LEAD_TIME = 24  # Forecast horizon in hours: 4 six-hourly forecast states.
STATE_PATH = Path(__file__).parent / "aifs_ens_input_state.npz"  # Written by the prefetch.

# 2. Define target location coordinates (San Leandro, CA)
TARGET_LAT = 37.72
TARGET_LON = -122.16

# 3. Load the prefetched initial conditions
if not STATE_PATH.exists():
    log.error("No prefetched input state; run example_ecmwf_aifs_ens_prefetch.py first", path=str(STATE_PATH))
    raise SystemExit(1)

with np.load(STATE_PATH) as data:
    DATE = datetime.fromisoformat(data["__date__"].item())
    fields = {name: data[name] for name in data.files if name != "__date__"}

age_hours = (datetime.now(timezone.utc).replace(tzinfo=None) - DATE).total_seconds() / 3600
log.info("Using initial conditions", date=str(DATE), age_hours=round(age_hours, 1), num_fields=len(fields))
if age_hours > 12:
    log.warning("Input state is stale; re-run example_ecmwf_aifs_ens_prefetch.py for the latest cycle")

input_state = dict(date=DATE, fields=fields)

# 4. Load the AIFS ENS 2.0 runner
# The checkpoint resolves against the local HuggingFace cache populated by the prefetch;
# anemoi-inference builds the model architecture from the checkpoint metadata.
device = "cuda" if torch.cuda.is_available() else "cpu"
log.info("Using device", device=device)
log.info("Loading AIFS ENS 2.0 checkpoint")
runner = SimpleRunner(CHECKPOINT, device=device)

# 5. Execute the forecast, extracting surface solar radiation for your coordinates
# The runner yields the SAME state dict each step, mutated in place -- collecting the
# states in a list gives N references to the final step. Extract per step instead.
log.info("Running 6-hourly forecast for solar irradiance", lead_time_hours=LEAD_TIME, lat=TARGET_LAT, lon=TARGET_LON)
location = pvlib.location.Location(TARGET_LAT, TARGET_LON, tz="UTC")
point_idx = None
for state in runner.run(input_state=input_state, lead_time=LEAD_TIME):
    if point_idx is None:
        # States carry the grid as flat latitude/longitude arrays (0-360 scale); locate
        # the closest N320 point once.
        latitudes = state["latitudes"]
        longitudes = state["longitudes"]
        point_idx = np.argmin((latitudes - TARGET_LAT) ** 2 + (longitudes - TARGET_LON % 360) ** 2)
    if "ssrd" not in state["fields"]:
        log.error("ssrd missing from forecast state", available=sorted(state["fields"]))
        raise KeyError("ssrd")
    # "ssrd" is surface shortwave (solar) radiation downwards, accumulated in J/m^2 over
    # the preceding 6-hour step; dividing by 21,600 s gives the window-mean flux in
    # W/m^2 (a 6 h-mean GHI -- coarser than the hourly-mean GHI convention).
    ssrd_joules = float(state["fields"]["ssrd"][point_idx])
    log.info(
        "Predicted 6h mean SSRD",
        valid_time=f"{state['date']:%Y-%m-%d %H:%M} UTC",
        ssrd_w_m2=round(ssrd_joules / (STEP_HOURS * 3600), 1),
    )
    # 6. Post-process: disaggregate the 6 h window into hourly means using the clear-sky
    # profile shared with the IFS HRES example. Note the model gives no cloud timing
    # within the window -- the IFS script's 3 h windows preserve that better.
    window_start = pd.Timestamp(state["date"], tz="UTC") - pd.Timedelta(hours=STEP_HOURS)
    for h, mean_w_m2 in enumerate(disaggregate_window(location, window_start, STEP_HOURS, ssrd_joules)):
        log.info(
            "Hourly mean SSRD (disaggregated)",
            valid_time=f"{window_start + pd.Timedelta(hours=h + 1):%Y-%m-%d %H:%M} UTC",
            ssrd_w_m2=round(mean_w_m2, 1),
        )
