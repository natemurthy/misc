"""Prefetch the Aurora 1.5 checkpoint, static variables, and initial conditions.

Downloads are split out of example_msft_aurora_solar.py so that running a forecast
never triggers a download. All three steps are skipped when already current:

- The ~5 GB checkpoint is fetched from HuggingFace with the same repo/filename/revision
  defaults the AuroraV1p5 class carries, so a prefetch here is always a cache hit in the
  solar script (which resolves with local_files_only=True). Downloaded once.
- The ~150 MB static-variables pickle (aurora-0.25-v1.5-static.pickle) comes from the
  same HuggingFace repo: Aurora 1.5's 36 static fields include vegetation- and soil-type
  one-hots that cannot be derived from forecast streams. Downloaded once.
- The initial conditions -- the real atmospheric state Aurora steps forward from -- are
  retrieved from ECMWF open data (the same source and mirror machinery as the AIFS
  prefetch) and saved to aurora_input_state.npz next to this file, stamped with their
  cycle. Re-downloaded whenever a newer cycle (00/06/12/18 UTC) has published; skipped
  otherwise.

Unlike the AIFS prefetch, no regridding is needed (Aurora runs natively on the 0.25 deg
lat/lon grid open data is published on) and only the HRES "oper" stream is used -- none
of the ensemble/wave stream complexity.

Open data covers 14 of Aurora 1.5's 18 input surface fields plus z/u/v/t/q on all 13
pressure levels. The four it lacks -- the low/mid/high cloud-cover split (lcc/mcc/hcc;
open data only publishes total cloud cover) and sea-ice concentration (ci) -- are filled
with their normalisation means by the solar script.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import earthkit.data as ekd
import numpy as np
import structlog
from aurora import AuroraV1p5
from ecmwf.opendata import Client as OpendataClient
from huggingface_hub import hf_hub_download

log = structlog.get_logger()

# Persist downloaded GRIBs across runs: earthkit's default cache policy is "temporary",
# which deletes the cache when the process exits, so without this an interrupted
# prefetch restarts its downloads from zero instead of resuming.
try:
    ekd.settings.set("cache-policy", "user")
except AttributeError:  # renamed in later earthkit-data versions
    ekd.config.set("cache-policy", "user")

STATIC_NAME = "aurora-0.25-v1.5-static.pickle"

# Open-data source mirror; see example_ecmwf_aifs_ens_prefetch.py and the README for
# the quirks of the alternatives ("ecmwf", "aws", "google").
SOURCE = "azure"
G = 9.80665  # Gravity, for the geopotential height -> geopotential conversion.
STATE_PATH = Path(__file__).parent / "aurora_input_state.npz"

# Aurora 1.5 input fields retrievable from the 0.25 deg oper stream. "sd" is stored
# under Aurora's name "scaled_sd" (the model log-transforms it internally; the batch
# carries the raw snow depth), and soil fields are renamed sot_1/vsw_1 -> stl1/swvl1.
PARAM_SFC = ["2t", "2d", "10u", "10v", "100u", "100v", "msl", "sp", "skt", "tcwv", "tcc", "sd"]
PARAM_SOIL = ["vsw", "sot"]
SOIL_LEVELS = [1]
PARAM_PL = ["gh", "t", "u", "v", "q"]
LEVELS = [50, 100, 150, 200, 250, 300, 400, 500, 600, 700, 850, 925, 1000]


def get_open_data(date, param, levelist=[], **kwargs):
    """Fetch fields at t-6h and t0 on the native 0.25 deg grid (no regridding).

    Returns a dict mapping field name ("param" or "param_level") to an array of shape
    (2, 721, 1440): the two history times Aurora needs, longitudes shifted to 0-360.
    """
    fields = defaultdict(list)
    for d in [date - timedelta(hours=6), date]:
        data = ekd.from_source(
            "ecmwf-open-data", date=d, param=param, levelist=levelist, source=SOURCE, **kwargs
        )
        for f in data:
            # Open data is between -180 and 180; shift it to 0-360.
            assert f.to_numpy().shape == (721, 1440)
            values = np.roll(f.to_numpy(), -f.shape[1] // 2, axis=1)
            name = f"{f.metadata('param')}_{f.metadata('levelist')}" if levelist else f.metadata("param")
            fields[name].append(values)

    for name, values in fields.items():
        assert len(values) == 2, f"{name}: expected both history times, got {len(values)}"
        fields[name] = np.stack(values).astype(np.float32)

    return dict(fields)


def build_fields(date):
    """Retrieve and transform all open-data input fields for one cycle."""
    fields = {}
    fields.update(get_open_data(date, param=PARAM_SFC, levtype="sfc"))
    soil = get_open_data(date, param=PARAM_SOIL, levelist=SOIL_LEVELS)
    fields.update(get_open_data(date, param=PARAM_PL, levelist=LEVELS))

    # Rename to Aurora's variable names (see PARAM_SFC comment).
    fields["scaled_sd"] = fields.pop("sd")
    fields["stl1"] = soil["sot_1"]
    fields["swvl1"] = soil["vsw_1"]

    # Open data provides geopotential height (gh); the model expects geopotential (z).
    for level in LEVELS:
        fields[f"z_{level}"] = fields.pop(f"gh_{level}") * G

    return fields


def prefetch_checkpoint():
    repo = AuroraV1p5.default_checkpoint_repo
    revision = AuroraV1p5.default_checkpoint_revision
    for name, size in [(AuroraV1p5.default_checkpoint_name, "~5 GB"), (STATIC_NAME, "~150 MB")]:
        try:
            path = hf_hub_download(repo_id=repo, filename=name, revision=revision, local_files_only=True)
            log.info("Already cached", repo=repo, name=name, path=path)
            continue
        except Exception:
            pass
        log.info(f"Downloading from HuggingFace ({size})", repo=repo, name=name)
        path = hf_hub_download(repo_id=repo, filename=name, revision=revision)
        log.info("Downloaded", path=path)


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
    date = client.latest(stream="oper", type="fc")
    if cached_state_date(STATE_PATH) == date:
        log.info("Input state already current", date=str(date), path=str(STATE_PATH))
        return
    log.info("Retrieving ECMWF open data initial conditions", date=str(date), source=SOURCE)
    fields = build_fields(date)
    np.savez(STATE_PATH, __date__=date.isoformat(), **fields)
    log.info(
        "Input state saved",
        date=str(date),
        num_fields=len(fields),
        size_mb=round(STATE_PATH.stat().st_size / 1e6),
        path=str(STATE_PATH),
    )


def main():
    prefetch_checkpoint()
    prefetch_input_state()


if __name__ == "__main__":
    main()
