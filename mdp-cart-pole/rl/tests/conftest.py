"""
pytest configuration for the rl/ suite: the fast/slow marking hook and the per-solution fixture
used by test_learning.py. Helper functions live in rl_helpers.py (see the note there on why);
the shared agent-interface checks live in interface_checks.py.
"""

from pathlib import Path

import pytest

from rl_helpers import SOLUTIONS

HERE = Path(__file__).resolve().parent


# The rule: a test is `fast` if it finishes in under 0.1 s, otherwise it is marked `slow`
# (measured with `pytest --durations=0 --durations-min=0.1`), with one exception: the PILCO
# file is all fast and pays its single Gaussian-process fit once in a module fixture.
def pytest_collection_modifyitems(items):
    # This hook is session-wide and oc/tests/conftest.py has one too, so each only touches its
    # own suite's items; otherwise the other suite's hook can stamp `fast` before `slow` lands.
    for item in items:
        if Path(str(item.fspath)).resolve().is_relative_to(HERE) and "slow" not in item.keywords:
            item.add_marker(pytest.mark.fast)


@pytest.fixture(params=SOLUTIONS, ids=lambda s: s)
def solution_name(request):
    return request.param
