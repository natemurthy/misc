"""Smoke test for the Aurora 1.5 solar-forecast plumbing in example_msft_aurora_solar.py.

Runs the same batch-construction and rollout code path on a tiny grid with randomly
initialized weights, so it completes in seconds without downloading the multi-GB
pretrained checkpoint. Values are meaningless (and may be NaN under float16 autocast
with random weights); this only validates shapes, variables, and the hourly rollout.
"""

from datetime import datetime, timedelta, timezone

import numpy as np
import torch
from aurora import AuroraV1p5, Batch, Metadata, insolation, rollout

STEPS = 2
FINE_LEAD_TIMES = [1, 2, 3, 4, 5, 6]


def build_batch(model, latitudes, longitudes, init_time):
    H, W, T = len(latitudes), len(longitudes), 2
    history_times = [init_time - timedelta(hours=6), init_time]

    input_surf_vars = [v for v in model.surf_vars if v not in model.output_only_surf_vars]

    surf_vars = {}
    for v in input_surf_vars:
        if v == "insolation":
            sol = np.stack(
                [insolation([t], latitudes, longitudes, enforce_2d=True)[0] for t in history_times]
            )
            surf_vars[v] = torch.tensor(sol, dtype=torch.float32)[None]  # (1, T, H, W)
        else:
            surf_vars[v] = torch.rand(1, T, H, W)

    static_vars = {v: torch.rand(H, W) for v in model.static_vars}

    atmos_levels = (50, 100, 150, 200, 250, 300, 400, 500, 600, 700, 850, 925, 1000)
    atmos_vars = {v: torch.rand(1, T, len(atmos_levels), H, W) for v in model.atmos_vars}

    return Batch(
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


def main():
    print("Initializing Aurora 1.5 with random weights (no checkpoint download)...")
    model = AuroraV1p5()
    model.eval()

    # Tiny global grid instead of the full 721x1440 0.25-degree grid.
    latitudes = np.linspace(90, -90, 33, dtype=np.float32)
    longitudes = np.linspace(0, 354.375, 64, dtype=np.float32)
    # Current UTC time truncated to the hour; Aurora metadata times are naive UTC.
    init_time = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0, tzinfo=None)

    input_batch = build_batch(model, latitudes, longitudes, init_time)

    print("Running hourly sub-stepped rollout...")
    with torch.inference_mode():
        predictions = list(
            rollout(model, input_batch, steps=STEPS, fine_lead_times=FINE_LEAD_TIMES)
        )

    expected = STEPS * len(FINE_LEAD_TIMES)
    assert len(predictions) == expected, f"expected {expected} predictions, got {len(predictions)}"

    for i, pred in enumerate(predictions, start=1):
        assert "ssrd_1h" in pred.surf_vars, "ssrd_1h missing from prediction surface variables"
        # Grid is cropped to a multiple of the patch size (33 -> 32 latitudes).
        assert pred.surf_vars["ssrd_1h"].shape == (1, 1, 32, 64), pred.surf_vars["ssrd_1h"].shape
        expected_time = init_time + timedelta(hours=i)
        assert pred.metadata.time[0] == expected_time, (pred.metadata.time[0], expected_time)

    print(f"OK: {len(predictions)} hourly predictions from {predictions[0].metadata.time[0]} "
          f"to {predictions[-1].metadata.time[0]}, all containing ssrd_1h")


if __name__ == "__main__":
    main()
