"""
Method-specific tests for the 2005 Natural Actor-Critic: the Gaussian score
function, the LSTD-Q(lambda) statistics, the compatible critic recovering a known
advantage, and the identity "critic weights w = natural gradient" (Peters et al.
2005, Eq. 5) checked against F^-1 g computed from the same samples.
"""

import numpy as np
import pytest

from interface_checks import AgentInterfaceTests
from rl_helpers import load_agent_class

Agent = load_agent_class("2005_nac")


class TestInterface(AgentInterfaceTests):
    solution = "2005_nac"


def _log_pi(agent, obs, u):
    mu, sigma = agent.mean(obs), agent.sigma
    return -0.5 * ((u - mu) / sigma) ** 2 - np.log(sigma) - 0.5 * np.log(2 * np.pi)


def test_score_matches_finite_differences():
    agent = Agent(seed=0)
    rng = np.random.default_rng(1)
    agent.theta[:-1] = rng.normal(0, 0.5, size=5)
    agent.theta[-1] = -0.3  # sigma = sigmoid(-0.3) ~ 0.43, well above the floor
    for _ in range(5):
        obs = rng.uniform(-0.2, 0.2, size=4)
        u = rng.normal(agent.mean(obs), agent.sigma)
        analytic = agent.score(obs, u)
        numeric = np.empty_like(analytic)
        h = 1e-6
        for i in range(len(agent.theta)):
            agent.theta[i] += h
            up = _log_pi(agent, obs, u)
            agent.theta[i] -= 2 * h
            dn = _log_pi(agent, obs, u)
            agent.theta[i] += h
            numeric[i] = (up - dn) / (2 * h)
        assert np.allclose(analytic, numeric, atol=1e-5), (analytic, numeric)


def test_frozen_policy_is_the_clipped_mean_and_training_policy_is_stochastic():
    agent = Agent(seed=0)
    agent.theta[:-1] = np.array([0.3, -0.2, 2.0, 1.0, 0.1])
    obs = np.array([0.1, -0.2, 0.05, 0.3])
    samples = {agent.act(obs) for _ in range(20)}
    assert len(samples) > 1 and all(isinstance(a, float) and -1 <= a <= 1 for a in samples)
    agent.freeze()
    assert agent.act(obs) == float(np.clip(agent.mean(obs), -1, 1))
    big = np.array([0.0, 0.0, 0.2, 3.0])  # mean far outside [-1, 1]
    assert agent.mean(big) > 1 and agent.act(big) == 1.0


def test_sigma_is_floored():
    agent = Agent(seed=0, sigma_min=0.05)
    agent.theta[-1] = -50.0
    assert agent.sigma == 0.05
    assert np.all(np.isfinite(agent.score(np.zeros(4), 0.3)))


def test_lstd_statistics_one_step():
    """z <- lam z + phi_hat, A <- A + z (phi_hat - gamma phi_tilde)^T, b <- b + z r; phi_tilde = 0 on failure."""
    agent = Agent(seed=0, lam=0.0, gamma=0.9, reward_scale=1.0)
    obs, nxt, u = np.array([0.1, 0.2, -0.05, 0.4]), np.array([0.11, 0.25, -0.04, 0.5]), 0.3
    phi_hat = np.concatenate((agent._value_features(obs), agent.score(obs, u)))
    phi_tilde = np.concatenate((agent._value_features(nxt), np.zeros(agent.n_pol)))

    agent._learn(obs, u, 1.0, nxt, terminated=False)
    assert np.allclose(agent.z, phi_hat)
    assert np.allclose(agent.A, np.outer(phi_hat, phi_hat - 0.9 * phi_tilde))
    assert np.allclose(agent.b, phi_hat)
    assert agent.n == 1

    fresh = Agent(seed=0, lam=0.0, gamma=0.9, reward_scale=1.0)
    fresh._learn(obs, u, 1.0, nxt, terminated=True)
    assert np.allclose(fresh.A, np.outer(phi_hat, phi_hat))  # next-state block dropped at failure


def test_traces_accumulate_with_lambda_and_reset_at_episode_end():
    agent = Agent(seed=0, lam=0.5, min_steps=10**9)  # min_steps huge: no actor step, we only look at z
    obs = np.array([0.1, 0.2, -0.05, 0.4])
    phi_hat = np.concatenate((agent._value_features(obs), agent.score(obs, 0.2)))
    agent._learn(obs, 0.2, 1.0, obs, False)
    agent._learn(obs, 0.2, 1.0, obs, False)
    assert np.allclose(agent.z, 1.5 * phi_hat)
    agent._end_episode()
    assert np.all(agent.z == 0)


@pytest.mark.slow
def test_compatible_critic_recovers_known_advantage_and_natural_gradient():
    """
    One state (s = 0, so only the bias and xi columns of the compatible features are live),
    reward r(u) = -u^2, every step terminal, lambda = 0: LSTD-Q reduces to least squares.
    With u ~ N(mu, sigma^2):  V = -(mu^2 + sigma^2),  w_bias = -2 mu sigma^2,
    w_xi = -sigma^2 / (1 - sigma), which are exactly F^-1 grad J for J(mu, xi) = V.
    """
    mu, sigma = 0.3, 0.5
    agent = Agent(seed=0, lam=0.0, reward_scale=1.0, ridge=1e-8, sigma0=sigma)
    agent.theta[4] = mu
    obs = np.zeros(4)
    rng = np.random.default_rng(0)
    n = 20000
    us = rng.normal(mu, sigma, size=n)
    scores, advantages = [], []
    for u in us:
        agent._learn(obs, float(u), -u * u, obs, terminated=True)
        scores.append(agent.score(obs, u))
        advantages.append(-u * u + mu**2 + sigma**2)
    w = agent.solve()
    assert np.isclose(agent.v[0], -(mu**2 + sigma**2), atol=0.02)
    assert np.isclose(w[4], -2 * mu * sigma**2, atol=0.02)
    assert np.isclose(w[5], -(sigma**2) / (1 - sigma), atol=0.03)
    assert np.allclose(w[:4], 0, atol=1e-6)  # dead columns, held at zero by the ridge

    # Eq. (5): the compatible weights equal the natural gradient F^-1 g, computed here from
    # the same samples with the vanilla gradient estimate g = mean(A * score) and F = mean(score score^T).
    S, adv = np.array(scores), np.array(advantages)
    live = [4, 5]
    F = (S[:, live].T @ S[:, live]) / n
    g = (S[:, live] * adv[:, None]).mean(axis=0)
    assert np.allclose(np.linalg.solve(F, g), w[live], atol=0.03)


def test_actor_step_is_alpha_times_w_and_statistics_are_forgotten():
    agent = Agent(seed=0, alpha=0.7, beta=0.5, update_every=1, min_steps=1)
    rng = np.random.default_rng(3)
    for _ in range(40):
        obs = rng.uniform(-0.2, 0.2, size=4)
        agent._learn(obs, float(rng.normal(0, 0.4)), 1.0, obs + 0.01, False)
    A_before, b_before, n_before = agent.A.copy(), agent.b.copy(), agent.n
    theta_before = agent.theta.copy()
    expected_w = np.linalg.solve(agent.A + agent.ridge * np.eye(agent.A.shape[0]), agent.b)[agent.n_val:]
    agent._end_episode()
    assert np.allclose(agent.theta - theta_before, 0.7 * expected_w)
    assert np.allclose(agent.A, 0.5 * A_before) and np.allclose(agent.b, 0.5 * b_before)
    assert agent.n == 0.5 * n_before


def test_no_actor_step_below_min_steps_or_before_direction_settles():
    agent = Agent(seed=0, min_steps=100, update_every=3, epsilon=0.0)
    rng = np.random.default_rng(4)
    theta0 = agent.theta.copy()
    for ep in range(3):
        for _ in range(20):
            obs = rng.uniform(-0.2, 0.2, size=4)
            agent._learn(obs, float(rng.normal(0, 0.4)), 1.0, obs + 0.01, False)
        agent._end_episode()
    assert np.array_equal(agent.theta, theta0)  # 60 < 100 samples: forced update refused
    agent.min_steps = 1
    agent._end_episode()  # epsilon = 0 never converges, but the forced update is now allowed
    assert not np.array_equal(agent.theta, theta0)


def test_learn_uses_the_unclipped_sample_behind_act():
    agent = Agent(seed=0)
    agent.theta[4] = 5.0  # mean far right, nearly every sample clips to +1
    obs = np.zeros(4)
    a = agent.act(obs)
    assert a == 1.0 and agent._raw > 1.0
    phi_hat_raw = np.concatenate((agent._value_features(obs), agent.score(obs, agent._raw)))
    agent._learn(obs, a, 1.0, obs, True)
    assert np.allclose(agent.z, phi_hat_raw)


@pytest.mark.parametrize("key", ["alpha", "gamma", "lam", "beta", "epsilon", "update_every", "min_steps",
                                 "ridge", "reward_scale", "sigma0", "sigma_min"])
def test_hparams_round_trip(key):
    agent = Agent(seed=0)
    assert key in agent.hparams()
    assert Agent(seed=0, **agent.hparams()).hparams() == agent.hparams()
