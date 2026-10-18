"""Prefetch the Chronos-2 checkpoint from HuggingFace.

The download is split out of example_amzn_chronos2_solar.py so that running a forecast
never downloads the model: the solar script resolves the checkpoint against the local
HuggingFace cache only (snapshot_download(local_files_only=True)) and exits with an
error if this prefetch hasn't been run. (The solar script still hits the network each
run for the Open-Meteo SSRD history -- that data is per-run current by design.)

snapshot_download pulls the full repo (~480 MB, dominated by model.safetensors) into
~/.cache/huggingface, and the solar script hands the resulting local path straight to
Chronos2Pipeline.from_pretrained, so inference-time model loading is fully offline.
"""

import structlog
from huggingface_hub import snapshot_download

log = structlog.get_logger()

HF_REPO = "amazon/chronos-2"


def prefetch_checkpoint():
    try:
        path = snapshot_download(HF_REPO, local_files_only=True)
        log.info("Checkpoint already cached", repo=HF_REPO, path=path)
        return
    except Exception:
        pass
    log.info("Downloading Chronos-2 checkpoint from HuggingFace (~480 MB)", repo=HF_REPO)
    path = snapshot_download(HF_REPO)
    log.info("Checkpoint downloaded", path=path)


if __name__ == "__main__":
    prefetch_checkpoint()
