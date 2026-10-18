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
    # same convention as rl/tests: everything not marked slow (i.e. under 0.1 s) is fast.
    # Only this suite's items: the hook is session-wide and rl/tests/conftest.py has its own.
    here = Path(__file__).resolve().parent
    for item in items:
        if Path(str(item.fspath)).resolve().is_relative_to(here) and "slow" not in item.keywords:
            item.add_marker(pytest.mark.fast)
