"""Fixtures for the oc/ test suite. Run with `pytest` from the oc/ directory, or from the
repository root to run it together with rl/tests."""

import sys
from pathlib import Path

import pytest

OC_DIR = Path(__file__).resolve().parent.parent
RL_DIR = OC_DIR.parent / "rl"
for d in (OC_DIR, RL_DIR):
    if str(d) not in sys.path:
        sys.path.insert(0, str(d))


def pytest_collection_modifyitems(items):
    # same convention as rl/tests: everything not marked slow is fast
    for item in items:
        if "slow" not in item.keywords:
            item.add_marker(pytest.mark.fast)
