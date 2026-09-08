"""Tests for the 1988 TD(λ) solution (Sutton): the shared agent interface, and that the true
dynamics are used only to act (one-step lookahead), never to learn."""

import numpy as np
import pytest

from common import CartPoleEnv
from interface_checks import AgentInterfaceTests
from rl_helpers import load_agent_class


class TestInterface(AgentInterfaceTests):
    solution = "1988_td"


@pytest.mark.slow
def test_1988_lookahead_uses_no_model_at_learning_time(monkeypatch):
    """TD(lambda) must learn V from samples only; the model is used in act(), not in learn()."""
    agent = load_agent_class("1988_td")(seed=0)
    calls = {"n": 0}
    real = CartPoleEnv.dynamics

    def counting(state, action):
        calls["n"] += 1
        return real(state, action)

    monkeypatch.setattr(CartPoleEnv, "dynamics", staticmethod(counting))
    obs = np.zeros(4, dtype=np.float32)
    nxt = np.array([0, 0, 0.01, 0.05], dtype=np.float32)
    agent.learn(obs, 1, 1.0, nxt, False)
    agent.end_episode()
    assert calls["n"] == 0
    agent.freeze()  # greedy: every act() looks one step ahead for each action
    agent.act(obs)
    assert calls["n"] == 2
