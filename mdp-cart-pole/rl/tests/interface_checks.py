"""
The interface every solution's Agent must satisfy, as a reusable test class.

Each tests/test_<solution>.py subclasses AgentInterfaceTests and names its solution; pytest
then collects the checks below for that solution next to the file's method-specific tests.
This module itself is not collected (its name does not start with test_).

    class TestInterface(AgentInterfaceTests):
        solution = "1989_qlearning"

A subclass may override the autouse `_agent_class` fixture to test a differently constructed
agent (the PILCO file supplies a pre-fitted model so nothing refits), or mark an inherited check
slow by overriding it and calling super().
"""

import numpy as np
import pytest

from common import BaseAgent
from rl_helpers import load_agent_class, make_env, train


def rollout(agent, n_steps=30, seed=0):
    """Run a few learning steps so the agent has non-trivial parameters."""
    env = make_env(agent, seed)
    obs, _ = env.reset()
    for _ in range(n_steps):
        a = agent.act(obs)
        nxt, r, term, trunc, _ = env.step(a)
        agent.learn(obs, a, r, nxt, term)
        obs = nxt
        if term or trunc:
            agent.end_episode()
            obs, _ = env.reset()
    agent.end_episode()


class AgentInterfaceTests:
    solution = None  # set by each subclass: the directory name, e.g. "1989_qlearning"

    @pytest.fixture(autouse=True)
    def _agent_class(self):
        self.agent_class = load_agent_class(self.solution)

    def test_is_base_agent_with_name(self):
        agent = self.agent_class(seed=0)
        assert isinstance(agent, BaseAgent)
        assert agent.name == self.solution

    def test_act_returns_valid_action(self):
        agent = self.agent_class(seed=0)
        env = make_env(agent, 0)
        obs, _ = env.reset()
        for _ in range(20):
            a = agent.act(obs)
            if getattr(agent, "continuous_actions", False):
                assert isinstance(a, float) and -1.0 <= a <= 1.0
            else:
                assert a in (0, 1) and isinstance(a, int)
            obs, *_ = env.step(a)

    def test_learn_and_end_episode_run_without_error(self):
        agent = self.agent_class(seed=0)
        rollout(agent, n_steps=200)
        for v in agent.stats().values():
            assert np.isfinite(v)

    def test_save_load_round_trip_preserves_policy(self, tmp_path):
        agent = self.agent_class(seed=0)
        rollout(agent, n_steps=300)
        path = tmp_path / "model.npz"
        agent.save(path)

        loaded = self.agent_class.load(path, seed=0)
        assert loaded.hparams() == agent.hparams()
        for k, v in agent.state_dict().items():
            assert np.allclose(loaded.state_dict()[k], v), f"parameter {k} changed across save/load"

        agent.freeze()
        loaded.freeze()
        rng = np.random.default_rng(1)
        for _ in range(50):
            obs = rng.uniform(-0.15, 0.15, size=4)
            assert agent.act(obs) == loaded.act(obs)

    def test_load_rejects_foreign_file(self, tmp_path):
        path = tmp_path / "junk.npz"
        np.savez(path, foo=np.zeros(3))
        with pytest.raises((ValueError, KeyError)):
            self.agent_class.load(path)

    def test_freeze_stops_learning(self):
        agent = self.agent_class(seed=0)
        rollout(agent, n_steps=100)
        agent.freeze()
        before = agent.snapshot()
        rollout(agent, n_steps=100)
        after = agent.state_dict()
        for k in before:
            assert np.array_equal(before[k], after[k]), f"{k} changed while frozen"

    def test_frozen_policy_is_deterministic(self):
        agent = self.agent_class(seed=0)
        rollout(agent, n_steps=300)
        agent.freeze()
        rng = np.random.default_rng(2)
        for _ in range(50):
            obs = rng.uniform(-0.15, 0.15, size=4)
            first = agent.act(obs)
            # Ties may be broken randomly only when the two action preferences are
            # exactly equal; sampling repeatedly from a generic state must agree.
            assert all(agent.act(obs) == first for _ in range(5))

    def test_snapshot_restore_round_trip(self):
        agent = self.agent_class(seed=0)
        rollout(agent, n_steps=200)
        snap = agent.snapshot()
        rollout(agent, n_steps=200, seed=1)
        agent.restore(snap)
        for k, v in snap.items():
            assert np.array_equal(agent.state_dict()[k], v)

    def test_same_seed_same_training_trajectory(self):
        a = self.agent_class(seed=5)
        b = self.agent_class(seed=5)
        ra = train(a, episodes=20, seed=5, checkpoint=False)
        rb = train(b, episodes=20, seed=5, checkpoint=False)
        assert ra == rb
