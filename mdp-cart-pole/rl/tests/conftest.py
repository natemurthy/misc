"""
pytest configuration for the rl/ suite: fixtures and the fast/slow marking hook.
Helper functions live in rl_helpers.py (see the note there on why).
"""

import pytest

from rl_helpers import SOLUTIONS, load_agent_class  # noqa: F401  (re-exported for convenience)


def pytest_collection_modifyitems(items):
    for item in items:
        if "slow" not in item.keywords:
            item.add_marker(pytest.mark.fast)


@pytest.fixture(params=SOLUTIONS, ids=lambda s: s)
def solution_name(request):
    return request.param


@pytest.fixture
def agent_class(solution_name):
    return load_agent_class(solution_name)
