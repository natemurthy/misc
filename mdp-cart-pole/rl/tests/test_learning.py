"""
Integration tests: each solution must actually learn to balance the pole.

Every agent is trained headlessly from scratch with a fixed seed on the
full-range start distribution (pole angle uniform in +/-12 degrees) for a
budget of episodes calibrated per method, keeping the best checkpoint. The
frozen policy is then run from Gymnasium's default near-upright start and must
survive on average at least LEARN_THRESHOLD steps, roughly five times the
random baseline (~22). These are marked `slow`; run only the quick tests with

    pytest -m fast

The budgets are deliberately small so the whole file runs in well under a
minute. They are not the recommended training lengths; main.py's default is
5000 episodes.
"""

import numpy as np
import pytest

from conftest import evaluate, train

LEARN_THRESHOLD = 100.0

# episodes needed, with seed 0, to clear LEARN_THRESHOLD with margin
BUDGET = {
    "1983_actor_critic": 1000,
    "1986_actor_critic_backprop": 400,
    "1988_td": 600,
    "1989_qlearning": 800,
    "1990_dyna": 600,
    "1992_reinforce": 400,
}


@pytest.mark.slow
def test_solution_learns_to_balance(agent_class, solution_name):
    agent = agent_class(seed=0)
    rets = train(agent, episodes=BUDGET[solution_name], seed=0)
    assert np.mean(rets[:50]) < 60, "sanity: untrained policy should not already balance"
    score = evaluate(agent, episodes=10, seed=99)
    assert score >= LEARN_THRESHOLD, (
        f"{solution_name}: frozen policy averaged {score:.1f} steps after "
        f"{BUDGET[solution_name]} episodes (threshold {LEARN_THRESHOLD})"
    )


def test_dyna_with_zero_planning_steps_is_exactly_qlearning():
    """Dyna-Q's direct-RL path is Q-learning; with no planning the two must agree step for step."""
    from conftest import load_agent_class

    q = load_agent_class("1989_qlearning")(seed=3)
    dyna = load_agent_class("1990_dyna")(seed=3, planning_steps=0)
    rq = train(q, episodes=60, seed=3, checkpoint=False)
    rd = train(dyna, episodes=60, seed=3, checkpoint=False)
    assert rq == rd
    assert np.allclose(q.q.reshape(-1, 2), dyna.q)


def test_dyna_planning_performs_extra_updates():
    """With planning on, one real transition must change more of the table than the one visited cell."""
    from common import CartPoleEnv
    from conftest import load_agent_class

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


@pytest.mark.slow
def test_1988_lookahead_uses_no_model_at_learning_time(monkeypatch):
    """TD(lambda) must learn V from samples only; the model is used in act(), not in learn()."""
    from common import CartPoleEnv
    from conftest import load_agent_class

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
