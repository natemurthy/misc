"""Fixtures for the mpc/ test suite. Run with `pytest` from the mpc/ directory."""

import sys
from pathlib import Path

MPC_DIR = Path(__file__).resolve().parent.parent
RL_DIR = MPC_DIR.parent / "rl"
for d in (MPC_DIR, RL_DIR):
    if str(d) not in sys.path:
        sys.path.insert(0, str(d))
