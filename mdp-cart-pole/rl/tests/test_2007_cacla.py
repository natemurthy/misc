"""Unit tests specific to the 2007 CACLA solution (Van Hasselt & Wiering)."""

import numpy as np
import pytest

from common import normalize_obs
from interface_checks import AgentInterfaceTests
from rl_helpers import load_agent_class

Agent = load_agent_class("2007_cacla")

OBS = np.array([0.1, -0.2, 0.05, 0.3])


class TestInterface(AgentInterfaceTests):
    solution = "2007_cacla"


def _actor_params(agent):
    return {k: v.copy() for k, v in agent.actor.params("a_").items()}


def _critic_params(agent):
    return {k: v.copy() for k, v in agent.critic.params("c_").items()}


def _force_delta(agent, obs, sign):
    """Set the critic's output bias so the TD error of a non-terminal self-transition has the given sign."""
    x = normalize_obs(obs)
    # delta = r + gamma * V(x) - V(x) = r - (1 - gamma) V(x); choose V(x) around r / (1 - gamma)
    v_zero = agent.reward_scale / (1.0 - agent.gamma)
    v_now = agent.critic.forward(x)[0]
    agent.critic.b2 += (v_zero - v_now) - sign * 0.5  # V below the fixpoint -> delta > 0; above -> delta < 0


def test_negative_td_error_leaves_actor_unchanged():
    agent = Agent(seed=0, lr_actor=0.1)
    _force_delta(agent, OBS, sign=-1)
    before = _actor_params(agent)
    agent.learn(OBS, 0.7, 1.0, OBS, False)
    assert agent._last_delta < 0
    assert agent._last_updates == 0
    for k, v in before.items():
        assert np.array_equal(agent.actor.params("a_")[k], v), k


def test_positive_td_error_moves_actor_toward_taken_action():
    agent = Agent(seed=0, lr_actor=0.1)
    _force_delta(agent, OBS, sign=+1)
    x = normalize_obs(OBS)
    u_before = agent._mean(x)[0]
    taken = 0.9 if u_before < 0.5 else -0.9
    agent.learn(OBS, taken, 1.0, OBS, False)
    assert agent._last_delta > 0
    assert agent._last_updates == 1
    u_after = agent._mean(x)[0]
    assert abs(taken - u_after) < abs(taken - u_before)
    # and the update is a regression toward the action, not away from it: no overshoot
    assert (u_after - u_before) * (taken - u_before) > 0


def test_critic_always_updates_regardless_of_sign():
    for sign in (-1, +1):
        agent = Agent(seed=0)
        _force_delta(agent, OBS, sign=sign)
        before = _critic_params(agent)
        agent.learn(OBS, 0.0, 1.0, OBS, False)
        changed = any(not np.array_equal(agent.critic.params("c_")[k], v) for k, v in before.items())
        assert changed, f"critic did not move for delta sign {sign}"


def test_network_gradients_match_finite_differences():
    agent = Agent(seed=3, hidden=8)
    net = agent.critic
    rng = np.random.default_rng(3)
    x = rng.uniform(-1, 1, 4)
    out, h = net.forward(x)
    gW1, gb1, gW2, gb2 = net.grads(x, h)
    eps = 1e-6
    for name, grad in (("W1", gW1), ("b1", gb1), ("W2", gW2)):
        arr = getattr(net, name)
        for idx in np.ndindex(arr.shape):
            arr[idx] += eps
            plus = net.forward(x)[0]
            arr[idx] -= 2 * eps
            minus = net.forward(x)[0]
            arr[idx] += eps
            assert (plus - minus) / (2 * eps) == pytest.approx(grad[idx], rel=1e-4, abs=1e-7), (name, idx)
    net.b2 += eps
    plus = net.forward(x)[0]
    net.b2 -= 2 * eps
    minus = net.forward(x)[0]
    assert (plus - minus) / (2 * eps) == pytest.approx(gb2, rel=1e-6)


def test_td0_trace_equals_one_step_gradient():
    """With lam = 0 (the paper's TD(0)) the eligibility trace is exactly the current gradient."""
    agent = Agent(seed=0, lam=0.0)
    x = normalize_obs(OBS)
    _, h = agent.critic.forward(x)
    agent.critic.accumulate(x, h, agent.gamma * agent.lam)
    agent.critic.accumulate(x, h, agent.gamma * agent.lam)  # decay 0: no accumulation
    gW1, gb1, gW2, gb2 = agent.critic.grads(x, h)
    assert np.allclose(agent.critic.eW1, gW1) and np.allclose(agent.critic.eb1, gb1)
    assert np.allclose(agent.critic.eW2, gW2) and agent.critic.eb2 == gb2


def test_cacla_var_performs_more_updates_for_a_large_td_error():
    plain = Agent(seed=0, var=False)
    with_var = Agent(seed=0, var=True, var_init=1e-6)  # tiny running variance: delta is many sigmas
    for agent in (plain, with_var):
        _force_delta(agent, OBS, sign=+1)
        agent.learn(OBS, 0.5, 1.0, OBS, False)
        assert agent._last_delta > 0
    assert plain._last_updates == 1
    assert with_var._last_updates > 1
    assert with_var._last_updates <= with_var.max_updates


def test_cacla_var_tracks_running_variance_and_plain_does_not():
    plain = Agent(seed=0, var=False)
    with_var = Agent(seed=0, var=True, var_beta=0.5, var_init=1.0)
    for agent in (plain, with_var):
        _force_delta(agent, OBS, sign=-1)
        agent.learn(OBS, 0.0, 1.0, OBS, False)
    assert plain.var == 1.0
    assert with_var.var == pytest.approx(0.5 * 1.0 + 0.5 * with_var._last_delta**2)


def test_frozen_act_is_actor_mean_and_training_act_is_noisy():
    agent = Agent(seed=0, sigma=0.3, sigma_min=0.3)
    x = normalize_obs(OBS)
    mean = agent._mean(x)[0]
    samples = [agent.act(OBS) for _ in range(20)]
    assert len(set(samples)) > 1 and all(-1.0 <= a <= 1.0 for a in samples)
    agent.freeze()
    a = agent.act(OBS)
    assert isinstance(a, float) and a == pytest.approx(mean)
    assert agent.act(OBS) == a


def test_actor_output_and_taken_action_stay_in_range():
    agent = Agent(seed=1, sigma=2.0, sigma_min=2.0)  # absurd noise: clipping must hold
    for _ in range(50):
        a = agent.act(OBS)
        assert -1.0 <= a <= 1.0
    rng = np.random.default_rng(0)
    for _ in range(50):
        u = agent._mean(rng.uniform(-3, 3, 4))[0]
        assert -1.0 < u < 1.0


def test_critic_starts_at_value_of_a_never_failing_state():
    agent = Agent(seed=0, reward_scale=0.01, gamma=0.99)
    assert agent.critic.b2 == pytest.approx(1.0)
    # a non-terminal self-transition then has TD error ~0 up to the tiny random hidden contribution
    x = np.zeros(4)
    v = agent.critic.forward(x)[0]
    delta = 0.01 + 0.99 * v - v
    assert abs(delta) < 0.05


def test_state_dict_round_trips_sigma_and_variance():
    agent = Agent(seed=0, var=True, sigma=0.3, sigma_min=0.3)
    agent.var = 0.123
    d = agent.snapshot()
    other = Agent(seed=1, var=True)
    other.load_state_dict(d)
    assert other.var == pytest.approx(0.123) and other.sigma == pytest.approx(0.3)
    assert np.allclose(other.actor.W1, agent.actor.W1)
