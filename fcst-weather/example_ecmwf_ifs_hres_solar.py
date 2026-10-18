"""Hourly surface solar radiation from IFS HRES ssrd + clear-sky disaggregation.

AIFS ENS 2.0's native step is 6 h with no hourly mode (see README). This example instead
uses the physics-based IFS HRES ssrd forecast (3-hourly steps), differences its
since-start accumulations into per-window energies, and disaggregates each 3 h window
into hourly means using a clear-sky profile: within a window, each hour receives energy
proportional to its clear-sky irradiance. The window's total energy is preserved and the
cloudiness signal stays IFS's own (per 3 h window), so this works in cloudy regions too
-- what it cannot capture is cloud evolution *within* a window.

The ssrd fields are read from ifs_hres_ssrd.npz, written by
example_ecmwf_aifs_ens_prefetch.py -- run that first; this script does no downloading.

Requires pvlib (pip install pvlib); the Haurwitz clear-sky model is used because it
needs no turbidity tables, and only the *relative* hourly weights matter here.
"""

from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pvlib
import structlog

log = structlog.get_logger()

GRID = 0.25  # Open data regular lat/lon grid spacing (721 x 1440 points).
STATE_PATH = Path(__file__).parent / "ifs_hres_ssrd.npz"  # Written by the prefetch.

# Target location coordinates (San Leandro, CA)
TARGET_LAT = 37.72
TARGET_LON = -122.16


def grid_indices(lat, lon):
    """Closest open-data grid point: latitudes run 90..-90, longitudes -180..179.75."""
    lat_idx = int(round((90 - lat) / GRID))
    lon_idx = int(round(((lon + 180) % 360) / GRID)) % 1440
    return lat_idx, lon_idx


def disaggregate_window(location, window_start, window_hours, window_joules):
    """Split one ssrd accumulation window into hourly mean fluxes (W/m^2).

    Each hour is weighted by its mean clear-sky irradiance (10-minute samples), so the
    hourly values follow the diurnal shape while summing back to the window's energy.
    """
    weights = []
    for h in range(window_hours):
        samples = pd.date_range(window_start + pd.Timedelta(hours=h), periods=6, freq="10min")
        weights.append(location.get_clearsky(samples, model="haurwitz")["ghi"].mean())
    total = sum(weights)
    if total <= 0:
        # Fully dark window: no clear-sky shape to follow; spread evenly (~0 in practice).
        return [window_joules / (window_hours * 3600.0)] * window_hours
    return [float(window_joules * w / total / 3600.0) for w in weights]


def main():
    if not STATE_PATH.exists():
        log.error("No prefetched IFS ssrd; run example_ecmwf_aifs_ens_prefetch.py first", path=str(STATE_PATH))
        raise SystemExit(1)

    lat_idx, lon_idx = grid_indices(TARGET_LAT, TARGET_LON)
    with np.load(STATE_PATH) as data:
        date = datetime.fromisoformat(data["__date__"].item())
        # ssrd at the target point, in J/m^2 accumulated since forecast start.
        ssrd_by_step = {
            int(name.removeprefix("step_")): float(data[name][lat_idx, lon_idx])
            for name in data.files
            if name.startswith("step_")
        }
    steps = sorted(ssrd_by_step)

    age_hours = (datetime.now(timezone.utc).replace(tzinfo=None) - date).total_seconds() / 3600
    log.info("Using IFS HRES cycle", date=str(date), age_hours=round(age_hours, 1), steps=steps)
    if age_hours > 12:
        log.warning("IFS ssrd is stale; re-run example_ecmwf_aifs_ens_prefetch.py for the latest cycle")

    location = pvlib.location.Location(TARGET_LAT, TARGET_LON, tz="UTC")
    base = pd.Timestamp(date, tz="UTC")

    log.info("Hourly surface solar radiation forecast", lat=TARGET_LAT, lon=TARGET_LON)
    for prev, cur in zip(steps, steps[1:]):
        # ssrd is accumulated since forecast start; difference consecutive steps to get
        # each window's energy (clamped: accumulations are monotonic up to GRIB noise).
        window_hours = cur - prev
        window_joules = max(ssrd_by_step[cur] - ssrd_by_step[prev], 0.0)
        window_start = base + pd.Timedelta(hours=prev)
        log.info(
            "IFS window mean SSRD",
            window_end=f"{base + pd.Timedelta(hours=cur):%Y-%m-%d %H:%M} UTC",
            ssrd_w_m2=round(window_joules / (window_hours * 3600), 1),
        )
        # The hourly-mean SSRD flux is what solar folks report as hourly-mean GHI.
        hourly = disaggregate_window(location, window_start, window_hours, window_joules)
        for h, mean_w_m2 in enumerate(hourly):
            hour_end = window_start + pd.Timedelta(hours=h + 1)
            log.info(
                "Hourly mean SSRD",
                valid_time=f"{hour_end:%Y-%m-%d %H:%M} UTC",
                ssrd_w_m2=round(mean_w_m2, 1),
            )


if __name__ == "__main__":
    main()
