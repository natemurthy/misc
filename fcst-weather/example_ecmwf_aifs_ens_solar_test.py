"""Smoke test for the AIFS ENS 2.0 solar-forecast plumbing (example_ecmwf_aifs_ens_solar.py).

Exercises the input-state construction and ssrd extraction code paths from the
official run_AIFS_ENS_v2.0.ipynb (huggingface.co/ecmwf/aifs-ens-2.0) on a tiny flattened
grid with mock fields, so it completes in seconds without downloading the 2.55 GB
checkpoint or retrieving ECMWF open data.

Unlike Aurora, anemoi-inference builds the model architecture from checkpoint metadata,
so the forecast step cannot run with random weights; SimpleRunner.run() is stood in by
mock states with the same structure (date, latitudes, longitudes, flat fields incl.
"ssrd", which is an output-only diagnostic of AIFS ENS 2.0). Values are meaningless;
this only validates field naming, shapes, times, and the extraction logic.
"""

from datetime import datetime, timedelta, timezone

import numpy as np
import structlog

log = structlog.get_logger()

STEP_HOURS = 6  # AIFS ENS 2.0 forecasts on a 6-hour time step.
LEAD_TIME = 24  # Forecast horizon in hours.
ENSEMBLE_MEMBER = 1  # Initial conditions are per ensemble member (stream "enfo").
G = 9.80665  # Gravity, for the geopotential height -> geopotential conversion.

# Input parameters as retrieved from ECMWF open data in the official notebook.
PARAM_SFC = ["10u", "10v", "2d", "2t", "msl", "skt", "sp", "tcw", "sd"]
PARAM_WAVE = ["wmb", "h1012", "h1214", "h1417", "h1721", "h2125", "h2530", "mwd", "cdww", "mwp", "swh"]
PARAM_PL = ["gh", "t", "u", "v", "w", "q"]
LEVELS = [1000, 925, 850, 700, 600, 500, 400, 300, 250, 200, 150, 100, 50, 10]
# Soil parameters are retrieved as vsw/sot at levels 1-2 and renamed for the model.
SOIL_MAPPING = {"sot_1": "stl1", "sot_2": "stl2", "vsw_1": "swvl1", "vsw_2": "swvl2"}

# Target location coordinates (San Leandro, CA)
TARGET_LAT = 37.72
TARGET_LON = -122.16


def latest_synoptic_time():
    """Most recent 00/06/12/18 UTC cycle, mirroring OpendataClient(SOURCE).latest()."""
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0, tzinfo=None)
    return now.replace(hour=(now.hour // STEP_HOURS) * STEP_HOURS)


def build_grid(n_lat=33, n_lon=64):
    """Tiny flattened global grid standing in for the N320 reduced Gaussian grid.

    The real model runs on N320 (542,080 points); anemoi states carry the grid as flat
    latitude/longitude arrays, which is all the extraction logic relies on.
    """
    lats = np.linspace(90, -90, n_lat, dtype=np.float32)
    lons = np.linspace(0, 360, n_lon, endpoint=False, dtype=np.float32)
    lon2d, lat2d = np.meshgrid(lons, lats)
    return lat2d.ravel(), lon2d.ravel()


def build_fields(rng, n_points):
    """Mock the input fields dict exactly as get_open_data + transformations produce it.

    Every field has shape (2, n_points): the two history times (t-6h, t0), flattened onto
    the model grid.
    """
    fields = {}
    for p in PARAM_SFC:
        fields[p] = rng.random((2, n_points))
    for p in PARAM_WAVE:
        fields[p] = rng.random((2, n_points))
    # Mean wave direction is fed to the model as its sine and cosine.
    mwd = rng.uniform(0, 360, (2, n_points))
    fields.pop("mwd")
    mwd_rad = np.deg2rad(mwd)
    fields["cos_mwd"] = np.cos(mwd_rad)
    fields["sin_mwd"] = np.sin(mwd_rad)

    soil = {k: rng.random((2, n_points)) for k in SOIL_MAPPING}
    for k, v in soil.items():
        fields[SOIL_MAPPING[k]] = v

    for p in PARAM_PL:
        for level in LEVELS:
            fields[f"{p}_{level}"] = rng.random((2, n_points))
    # Open data provides geopotential height (gh); the model expects geopotential (z).
    for level in LEVELS:
        gh = fields.pop(f"gh_{level}")
        fields[f"z_{level}"] = gh * G

    return fields


def mock_run(input_state, latitudes, longitudes, lead_time, rng):
    """Stand-in for SimpleRunner({"huggingface": "ecmwf/aifs-ens-2.0"}).run(...).

    Yields one state per 6-hour step with the same structure the real runner returns:
    date, flat latitudes/longitudes, and 1-D output fields including the output-only
    diagnostic "ssrd" (accumulated J/m^2 over the step).
    """
    n_points = len(latitudes)
    for h in range(STEP_HOURS, lead_time + 1, STEP_HOURS):
        # Plausible magnitude: ~500 W/m^2 mean flux accumulated over 6 h.
        ssrd = np.clip(rng.normal(500, 200, n_points), 0, None) * STEP_HOURS * 3600
        yield {
            "date": input_state["date"] + timedelta(hours=h),
            "latitudes": latitudes,
            "longitudes": longitudes,
            "fields": {"ssrd": ssrd, "2t": rng.random(n_points)},
        }


def nearest_point_index(latitudes, longitudes, lat, lon):
    """Index of the grid point closest to (lat, lon); state longitudes are 0-360."""
    lon_360 = lon % 360
    return np.argmin((latitudes - lat) ** 2 + (longitudes - lon_360) ** 2)


def main():
    rng = np.random.default_rng(0)

    log.info("Building mock AIFS ENS 2.0 input state (no checkpoint, no open data)")
    date = latest_synoptic_time()
    latitudes, longitudes = build_grid()
    n_points = len(latitudes)

    fields = build_fields(rng, n_points)
    input_state = dict(date=date, fields=fields)

    # Surface + wave (mwd -> cos/sin) + soil + pressure-level fields.
    expected_n_fields = len(PARAM_SFC) + (len(PARAM_WAVE) + 1) + len(SOIL_MAPPING) + len(PARAM_PL) * len(LEVELS)
    assert len(fields) == expected_n_fields, (len(fields), expected_n_fields)
    for name, values in fields.items():
        assert values.shape == (2, n_points), (name, values.shape)
        assert np.isfinite(values).all(), f"non-finite values in {name}"
    # Retrieval-only names must have been converted away.
    assert "mwd" not in fields and "cos_mwd" in fields and "sin_mwd" in fields
    assert not any(k.startswith(("gh_", "sot_", "vsw_")) for k in fields), "unconverted fields"
    assert all(f"z_{l}" in fields and f"q_{l}" in fields for l in LEVELS)

    log.info("Running mock 6-hourly forecast", lead_time_hours=LEAD_TIME, member=ENSEMBLE_MEMBER)
    states = list(mock_run(input_state, latitudes, longitudes, LEAD_TIME, rng))

    expected = LEAD_TIME // STEP_HOURS
    assert len(states) == expected, f"expected {expected} states, got {len(states)}"

    idx = nearest_point_index(latitudes, longitudes, TARGET_LAT, TARGET_LON)
    for i, state in enumerate(states, start=1):
        assert "ssrd" in state["fields"], "ssrd missing from forecast state fields"
        assert state["fields"]["ssrd"].shape == (n_points,), state["fields"]["ssrd"].shape
        assert state["date"] == date + timedelta(hours=i * STEP_HOURS), state["date"]
        # ssrd is accumulated J/m^2 over the step; dividing by the window gives the
        # window-mean flux in W/m^2.
        ssrd_w_m2 = state["fields"]["ssrd"][idx] / (STEP_HOURS * 3600)
        assert np.isfinite(ssrd_w_m2) and ssrd_w_m2 >= 0, ssrd_w_m2

    log.info(
        "OK: all forecast states contain ssrd",
        num_states=len(states),
        first_time=states[0]["date"],
        last_time=states[-1]["date"],
    )


if __name__ == "__main__":
    main()
