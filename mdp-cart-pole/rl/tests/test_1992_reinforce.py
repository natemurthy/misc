"""Tests for the 1992 REINFORCE solution (Williams): the shared agent interface, and recovery from
wide angles with a widened failure limit."""

import pytest

from interface_checks import AgentInterfaceTests
from rl_helpers import LEARN_THRESHOLD, evaluate, load_agent_class, train


class TestInterface(AgentInterfaceTests):
    solution = "1992_reinforce"


@pytest.mark.slow
def test_reinforce_recovers_beyond_12_degrees_with_wider_limit():
    """With --theta-limit 30 the linear REINFORCE policy learns to recover from a 20 degree start,
    which is inside the ~34 degree physical envelope of the 2.4 m track."""
    agent = load_agent_class("1992_reinforce")(seed=0)
    train(agent, episodes=1500, seed=0, theta_range_deg=30.0, theta_limit_deg=30.0)
    assert evaluate(agent, episodes=10, seed=99, theta0_deg=20.0, theta_limit_deg=30.0) >= LEARN_THRESHOLD
