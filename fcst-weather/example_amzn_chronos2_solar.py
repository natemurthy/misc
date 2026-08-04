"""Hourly solar irradiance forecast with Amazon Chronos-2 on Open-Meteo history.

Unlike Aurora / AIFS (physics-informed global weather models that need gridded
atmospheric initial states), Chronos-2 is a pretrained time-series foundation model:
it forecasts the next 24 hours of SSRD purely from the recent history of that single
series -- here, the last 30 days of hourly shortwave radiation at the target point,
pulled from the Open-Meteo API. No grid, no atmospheric variables, no GPU required
(CPU inference takes seconds at this context length).
"""

import os
import tempfile
from datetime import datetime, timedelta, timezone

# Triton JIT-compiles small CUDA helper modules with the compiler named by $CC and
# inherits its stderr, and Python 3.14's pyconfig.h redefining _POSIX_C_SOURCE after
# cuda.h makes gcc print harmless redefinition warnings on the first (uncached) run.
# Triton offers no flag hook and doesn't shell-split $CC, so point it at a wrapper
# that adds -w; only compiler diagnostics are silenced, Python stderr is untouched.
if "CC" not in os.environ:
    _cc_wrapper = os.path.join(tempfile.gettempdir(), "cc-nowarn.sh")
    with open(_cc_wrapper, "w") as f:
        f.write('#!/bin/sh\nexec gcc -w "$@"\n')
    os.chmod(_cc_wrapper, 0o755)
    os.environ["CC"] = _cc_wrapper

import requests
import structlog
import torch
from chronos import Chronos2Pipeline
from huggingface_hub import snapshot_download

log = structlog.get_logger()


# pip install chronos-forecasting requests

HF_REPO = "amazon/chronos-2"

# 1. Initialize the Chronos-2 model
# The pretrained checkpoint (~120M params) is resolved against the local HuggingFace
# cache only -- downloading is split into example_amzn_chronos2_prefetch.py -- and the
# local path is handed to from_pretrained, so model loading never touches the network.
try:
    model_path = snapshot_download(HF_REPO, local_files_only=True)
except Exception:
    log.error("Chronos-2 checkpoint not cached; run example_amzn_chronos2_prefetch.py first")
    raise SystemExit(1)

log.info("Loading Chronos-2 Foundation Model", checkpoint=model_path)
device = "cuda" if torch.cuda.is_available() else "cpu"
log.info("Using device", device=device)
pipeline = Chronos2Pipeline.from_pretrained(model_path, device_map=device)

# 2. Define target location coordinates (San Leandro, CA)
TARGET_LAT = 37.72
TARGET_LON = -122.16

HISTORY_DAYS = 30
FORECAST_HOURS = 24

# Current UTC time truncated to the hour -- the same ts_init convention as the Aurora
# example; the forecast covers the 24 hours following this timestamp.
init_time = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0, tzinfo=None)

# 3. Pull the last 30 days of hourly SSRD history from Open-Meteo
# past_days serves recent history (model analysis / best match), forecast_days=1 fills
# today's hours up to init_time; anything past init_time is dropped below.
resp = requests.get(
    "https://api.open-meteo.com/v1/forecast",
    params={
        "latitude": TARGET_LAT,
        "longitude": TARGET_LON,
        "hourly": "shortwave_radiation",
        "past_days": HISTORY_DAYS,
        "forecast_days": 1,
        "timezone": "UTC",
    },
    timeout=30,
)
resp.raise_for_status()
hourly = resp.json()["hourly"]

# Open-Meteo's shortwave_radiation is the mean flux over the *preceding* hour in W/m^2
# (i.e. hourly-mean GHI: a value stamped T covers the hour ending at T), matching the
# hour-ending convention the Aurora example derives from ssrd_1h. Keep only hours fully
# elapsed by init_time, then take the trailing 30 days as the model context.
history = [
    (t, v)
    for t, v in zip(hourly["time"], hourly["shortwave_radiation"])
    if v is not None and datetime.fromisoformat(t) <= init_time
]
history = history[-HISTORY_DAYS * 24 :]
context = torch.tensor([v for _, v in history], dtype=torch.float32)
log.info(
    "Fetched Open-Meteo SSRD history",
    points=len(context),
    start=f"{history[0][0]} UTC",
    end=f"{history[-1][0]} UTC",
)

# 4. Execute Forecast Prediction
# Chronos-2 is probabilistic: one forward pass yields quantiles for all 24 hourly steps
# (no autoregressive rollout needed at this horizon). The median is the point forecast;
# the 0.1/0.9 quantiles bound an 80% prediction interval.
log.info("Running Chronos-2 inference for hourly solar irradiance forecasting")
with torch.inference_mode():
    # A single tensor input must be 3-d: (n_series, n_variates, history_length).
    quantiles, mean = pipeline.predict_quantiles(
        context[None, None, :],
        prediction_length=FORECAST_HOURS,
        quantile_levels=[0.1, 0.5, 0.9],
    )
# predict_quantiles returns one tensor per input series, each shaped
# (n_variates, prediction_length, quantile_levels) -- take our single series/variate.
# Irradiance is non-negative, but nothing constrains the predicted quantiles: night-time
# values can dip slightly below zero, so clamp to the physical range.
forecast = quantiles[0].clamp(min=0)

# 5. Log the hourly forecast for the next 24 hours
log.info("Solar irradiance forecast", lat=TARGET_LAT, lon=TARGET_LON)
for h in range(FORECAST_HOURS):
    valid_time = init_time + timedelta(hours=h + 1)
    p10, median, p90 = (forecast[0, h, i].item() for i in range(3))
    log.info(
        "Predicted hourly mean SSRD",
        valid_time=f"{valid_time:%Y-%m-%d %H:%M} UTC",
        ssrd_w_m2=round(median, 1),
        p10_w_m2=round(p10, 1),
        p90_w_m2=round(p90, 1),
    )
