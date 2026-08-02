"""Prefetch the AIFS ENS 2.0 checkpoint and the ECMWF open data sets.

Downloads are split out of the example_ecmwf_*_solar.py scripts so that running them
never triggers a download. All three steps are skipped when already current:

- The HuggingFace checkpoint is first resolved offline against the local cache
  (snapshot_download(local_files_only=True)); snapshot_download is the same call
  anemoi-inference uses to resolve {"huggingface": ...} checkpoints, so a prefetch here
  is always a cache hit there.
- The AIFS input state is saved to aifs_ens_input_state.npz next to this file, stamped
  with its cycle; if that still matches the latest cycle fully published across the
  oper/enfo/waef streams, the download is skipped.
- The IFS HRES 3-hourly ssrd fields (for example_ecmwf_ifs_hres_solar.py) are saved to
  ifs_hres_ssrd.npz the same way, checked against the latest oper-stream cycle.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import earthkit.data as ekd
import earthkit.regrid as ekr
import numpy as np
import structlog
from ecmwf.opendata import Client as OpendataClient

log = structlog.get_logger()

# Persist downloaded GRIBs across runs: earthkit's default cache policy is "temporary",
# which deletes the cache when the process exits, so without this an interrupted
# prefetch restarts its downloads from zero instead of resuming.
try:
    ekd.settings.set("cache-policy", "user")
except AttributeError:  # renamed in later earthkit-data versions
    ekd.config.set("cache-policy", "user")

# See README.md ("Setup" section) for the environment setup.

HF_REPO = "ecmwf/aifs-ens-2.0"
# Open-data source. "ecmwf" is the direct portal (rate-limited); "aws" and "azure" are
# mirrors that multiurl explicitly supports ("aws" can throttle with "503 Slow Down"
# right after a new cycle publishes). Do NOT use "google": multiurl (<= 0.3.9) lacks a
# GCS special case for single-range requests, so indexed retrievals 400 there.
SOURCE = "azure"
MEMBER = 1  # Ensemble member for the initial conditions (operational runs use 1-50).
G = 9.80665  # Gravity, for the geopotential height -> geopotential conversion.
STATE_PATH = Path(__file__).parent / "aifs_ens_input_state.npz"

# IFS HRES ssrd fields for example_ecmwf_ifs_hres_solar.py: 3-hourly accumulations,
# stored as global grids so the solar script can extract any target location.
IFS_STATE_PATH = Path(__file__).parent / "ifs_hres_ssrd.npz"
IFS_STEP_HOURS = 3
IFS_LEAD_TIME = 24

# Input parameters as retrieved from ECMWF open data in the official notebook.
PARAM_SFC = ["10u", "10v", "2d", "2t", "msl", "skt", "sp", "tcw", "sd"]
PARAM_SFC_FC = ["lsm", "z", "slor", "sdor"]  # Constant surface fields (no member number).
PARAM_WAVE = ["wmb", "h1012", "h1214", "h1417", "h1721", "h2125", "h2530", "cdww", "mwd", "mwp", "swh"]
PARAM_SOIL = ["vsw", "sot"]
SOIL_LEVELS = [1, 2]
PARAM_PL = ["gh", "t", "u", "v", "w", "q"]
LEVELS = [1000, 925, 850, 700, 600, 500, 400, 300, 250, 200, 150, 100, 50, 10]


def latest_common_cycle(client):
    """Most recent cycle (00/06/12/18 UTC) fully published across the streams we use.

    Each stream publishes on its own schedule after a cycle: right as a new cycle lands,
    the HRES (oper) stream can be up while the ensemble (enfo) and wave (waef) streams
    still 404.
    """
    return min(
        client.latest(stream="oper", type="fc"),
        client.latest(stream="enfo", type="pf"),
        client.latest(stream="waef", type="pf"),
    )


def get_open_data(date, param, levelist=[], number=None, **kwargs):
    """Fetch fields at t-6h and t0 and regrid them from 0.25 deg to the model's N320 grid.

    Returns a dict mapping field name ("param" or "param_level") to an array of shape
    (2, 542080): the two history times, flattened onto the N320 reduced Gaussian grid.
    """
    fields = defaultdict(list)
    for d in [date - timedelta(hours=6), date]:
        if number is None:
            data = ekd.from_source(
                "ecmwf-open-data", date=d, param=param, levelist=levelist, source=SOURCE, **kwargs
            )
        else:
            kwargs.setdefault("stream", "enfo")
            data = ekd.from_source(
                "ecmwf-open-data",
                date=d,
                param=param,
                levelist=levelist,
                number=[number],
                source=SOURCE,
                **kwargs,
            )

        for f in data:
            # Open data is between -180 and 180; shift it to 0-360.
            assert f.to_numpy().shape == (721, 1440)
            values = np.roll(f.to_numpy(), -f.shape[1] // 2, axis=1)
            values = ekr.interpolate(values, {"grid": (0.25, 0.25)}, {"grid": "N320"})
            name = f"{f.metadata('param')}_{f.metadata('levelist')}" if levelist else f.metadata("param")
            fields[name].append(values)

    for name, values in fields.items():
        fields[name] = np.stack(values)

    return fields


def build_fields(date):
    """Retrieve and transform all input fields for one cycle, ready for the runner."""
    fields = {}
    fields.update(get_open_data(date, param=PARAM_SFC, number=MEMBER, levtype="sfc"))
    fields.update(get_open_data(date, param=PARAM_SFC_FC, levtype="sfc"))
    # Ensemble wave fields come from the "waef" stream.
    fields.update(get_open_data(date, param=PARAM_WAVE, stream="waef", number=MEMBER))
    soil = get_open_data(date, param=PARAM_SOIL, levelist=SOIL_LEVELS, number=MEMBER)
    fields.update(get_open_data(date, param=PARAM_PL, levelist=LEVELS, number=MEMBER))

    # Mean wave direction is fed to the model as its sine and cosine.
    mwd = fields.pop("mwd")
    mwd_rad = np.deg2rad(mwd)
    fields["cos_mwd"] = np.cos(mwd_rad)
    fields["sin_mwd"] = np.sin(mwd_rad)

    # Soil parameters are retrieved as vsw/sot at levels 1-2 and renamed for the model.
    mapping = {"sot_1": "stl1", "sot_2": "stl2", "vsw_1": "swvl1", "vsw_2": "swvl2"}
    for k, v in soil.items():
        fields[mapping[k]] = v

    # Open data provides geopotential height (gh); the model expects geopotential (z).
    for level in LEVELS:
        gh = fields.pop(f"gh_{level}")
        fields[f"z_{level}"] = gh * G

    # AIFS ENS 2.0 has no specific humidity variable at 10 hPa (q inputs stop at 50 hPa),
    # so open data's q_10 is unknown to the checkpoint metadata and crashes the runner.
    fields.pop("q_10")

    return fields


def prefetch_checkpoint():
    from huggingface_hub import snapshot_download

    try:
        path = snapshot_download(HF_REPO, local_files_only=True)
        log.info("Checkpoint already cached", repo=HF_REPO, path=path)
        return
    except Exception:
        pass
    log.info("Downloading checkpoint from HuggingFace (~2.55 GB)", repo=HF_REPO)
    path = snapshot_download(HF_REPO)
    log.info("Checkpoint downloaded", path=path)


def cached_state_date(path):
    """Cycle of a saved .npz state file, or None if absent/unreadable."""
    if not path.exists():
        return None
    try:
        with np.load(path) as data:
            return datetime.fromisoformat(data["__date__"].item())
    except Exception:
        log.warning("Existing state file unreadable; will re-download", path=str(path))
        return None


def prefetch_input_state():
    client = OpendataClient(SOURCE)
    date = latest_common_cycle(client)
    if cached_state_date(STATE_PATH) == date:
        log.info("Input state already current", date=str(date), path=str(STATE_PATH))
        return
    log.info("Retrieving ECMWF open data initial conditions", date=str(date), source=SOURCE, member=MEMBER)
    fields = build_fields(date)
    np.savez(STATE_PATH, __date__=date.isoformat(), **fields)
    log.info(
        "Input state saved",
        date=str(date),
        num_fields=len(fields),
        size_mb=round(STATE_PATH.stat().st_size / 1e6),
        path=str(STATE_PATH),
    )


def prefetch_ifs_ssrd():
    client = OpendataClient(SOURCE)
    # The IFS fetch only needs the oper stream, which publishes ahead of enfo/waef, so
    # its latest cycle can be newer than the AIFS input state's.
    date = client.latest(stream="oper", type="fc")
    if cached_state_date(IFS_STATE_PATH) == date:
        log.info("IFS ssrd already current", date=str(date), path=str(IFS_STATE_PATH))
        return
    steps = list(range(0, IFS_LEAD_TIME + 1, IFS_STEP_HOURS))
    log.info("Retrieving IFS HRES ssrd forecast", date=str(date), source=SOURCE, steps=steps)
    data = ekd.from_source(
        "ecmwf-open-data", date=date, param="ssrd", step=steps, levtype="sfc", source=SOURCE
    )
    fields = {}
    for f in data:
        arr = f.to_numpy()
        assert arr.shape == (721, 1440)
        fields[f"step_{int(f.metadata('step'))}"] = arr
    missing = [s for s in steps if f"step_{s}" not in fields]
    assert not missing, f"steps missing from retrieval: {missing}"
    np.savez(IFS_STATE_PATH, __date__=date.isoformat(), **fields)
    log.info(
        "IFS ssrd saved",
        date=str(date),
        num_steps=len(fields),
        size_mb=round(IFS_STATE_PATH.stat().st_size / 1e6),
        path=str(IFS_STATE_PATH),
    )


def main():
    prefetch_checkpoint()
    prefetch_input_state()
    prefetch_ifs_ssrd()


if __name__ == "__main__":
    main()
