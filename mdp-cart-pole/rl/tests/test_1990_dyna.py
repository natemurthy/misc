"""Tests for the 1990 Dyna-Q solution (Sutton): the shared agent interface, and that planning is
Q-learning plus extra model-sampled updates."""

import numpy as np

from common import CartPoleEnv
from interface_checks import AgentInterfaceTests
from rl_helpers import load_agent_class, train


class TestInterface(AgentInterfaceTests):
    solution = "1990_dyna"


def test_dyna_with_zero_planning_steps_is_exactly_qlearning():
    """Dyna-Q's direct-RL path is Q-learning; with no planning the two must agree step for step."""
    q = load_agent_class("1989_qlearning")(seed=3)
    dyna = load_agent_class("1990_dyna")(seed=3, planning_steps=0)
    rq = train(q, episodes=60, seed=3, checkpoint=False)
    rd = train(dyna, episodes=60, seed=3, checkpoint=False)
    assert rq == rd
    assert np.allclose(q.q.reshape(-1, 2), dyna.q)


def test_dyna_planning_performs_extra_updates():
    """With planning on, one real transition must change more of the table than the one visited cell."""
    dyna = load_agent_class("1990_dyna")(seed=0, planning_steps=20)
    env = CartPoleEnv(seed=0)
    obs, _ = env.reset()
    # seed the model with a handful of real transitions
    for _ in range(30):
        a = dyna.act(obs)
        nxt, r, term, trunc, _ = env.step(a)
        dyna.learn(obs, a, r, nxt, term)
        obs = nxt
        if term or trunc:
            obs, _ = env.reset()
    assert len(dyna._seen_list) > 1
    before = dyna.q.copy()
    a = dyna.act(obs)
    nxt, r, term, _, _ = env.step(a)
    dyna.learn(obs, a, r, nxt, term)
    changed_cells = np.count_nonzero(np.any(dyna.q != before, axis=1))
    assert changed_cells > 1, "planning should have updated cells beyond the one just visited"
