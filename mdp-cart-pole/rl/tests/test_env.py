"""Unit tests for the shared CartPole MDP (common/env.py)."""

import math

import numpy as np
import pytest

from common import CartPoleEnv


def test_reset_returns_obs_and_info():
    env = CartPoleEnv(seed=0)
    obs, info = env.reset()
    assert obs.shape == (4,) and obs.dtype == np.float32
    assert info == {}
    assert np.all(np.abs(obs) <= 0.05)


def test_reset_options_override_position_and_angle():
    env = CartPoleEnv(seed=0)
    obs, _ = env.reset(options={"x0": 1.5, "theta0": -0.14})
    assert obs[0] == pytest.approx(1.5)
    assert obs[2] == pytest.approx(-0.14, abs=1e-6)
    assert abs(obs[1]) <= 0.05 and abs(obs[3]) <= 0.05  # velocities still random


def test_reset_seed_is_reproducible():
    a, _ = CartPoleEnv().reset(seed=7)
    b, _ = CartPoleEnv().reset(seed=7)
    assert np.array_equal(a, b)


def test_step_returns_five_tuple_and_constant_reward():
    env = CartPoleEnv(seed=0)
    env.reset()
    out = env.step(1)
    assert len(out) == 5
    obs, reward, terminated, truncated, info = out
    assert obs.dtype == np.float32
    assert reward == 1.0
    assert terminated is False and truncated is False
    assert info == {}


def test_step_rejects_bad_action():
    env = CartPoleEnv(seed=0)
    env.reset()
    with pytest.raises(AssertionError):
        env.step(2)


def test_dynamics_matches_hand_computation():
    """One Euler step from a known state, computed independently of the class."""
    state = np.array([0.1, -0.2, 0.05, 0.3])
    nxt = CartPoleEnv.dynamics(state, 1)
    g, mc, mp, l, F, tau = 9.8, 1.0, 0.1, 0.5, 10.0, 0.02
    x, xd, th, thd = state
    temp = (F + mp * l * thd**2 * math.sin(th)) / (mc + mp)
    thacc = (g * math.sin(th) - math.cos(th) * temp) / (l * (4 / 3 - mp * math.cos(th) ** 2 / (mc + mp)))
    xacc = temp - mp * l * thacc * math.cos(th) / (mc + mp)
    expected = [x + tau * xd, xd + tau * xacc, th + tau * thd, thd + tau * thacc]
    assert np.allclose(nxt, expected)


def test_dynamics_is_pure():
    state = np.array([0.0, 0.0, 0.1, 0.0])
    before = state.copy()
    CartPoleEnv.dynamics(state, 0)
    assert np.array_equal(state, before)


def test_pushing_right_accelerates_cart_right_and_pole_left():
    upright = np.array([0.0, 0.0, 0.0, 0.0])
    nxt = CartPoleEnv.dynamics(upright, 1)
    assert nxt[1] > 0  # cart velocity increases
    assert nxt[3] < 0  # pole angular velocity goes negative (pole tips left)


def test_terminates_on_angle_threshold():
    env = CartPoleEnv(seed=0)
    env.reset(options={"theta0": math.radians(11.9)})
    env.state[3] = 5.0  # falling fast to the right
    _, _, terminated, _, _ = env.step(1)
    assert terminated


def test_terminates_on_position_threshold():
    env = CartPoleEnv(seed=0)
    env.reset(options={"x0": 2.39})
    env.state[1] = 3.0
    _, _, terminated, _, _ = env.step(1)
    assert terminated


def test_truncates_at_500_steps_with_stabilizing_controller():
    env = CartPoleEnv(seed=1)
    obs, _ = env.reset()
    steps, terminated, truncated = 0, False, False
    while not (terminated or truncated):
        a = 1 if (obs[2] + 0.5 * obs[3] + 0.05 * obs[0] + 0.1 * obs[1]) > 0 else 0
        obs, _, terminated, truncated, _ = env.step(a)
        steps += 1
    assert truncated and not terminated
    assert steps == CartPoleEnv.max_episode_steps == 500


def test_random_policy_fails_quickly():
    env = CartPoleEnv(seed=3)
    rng = np.random.default_rng(3)
    lengths = []
    for _ in range(50):
        env.reset()
        done, n = False, 0
        while not done:
            _, _, term, trunc, _ = env.step(int(rng.integers(2)))
            done = term or trunc
            n += 1
        lengths.append(n)
    assert 10 < np.mean(lengths) < 40  # the well-known ~22-step random baseline


def test_continuous_mode_scales_force():
    """u = 0.5 must accelerate the cart exactly half as hard as a full push."""
    s0 = np.zeros(4)
    full = CartPoleEnv.dynamics(s0, 1)
    half = CartPoleEnv.dynamics_force(s0, CartPoleEnv.action_to_force(0.5))
    assert half[1] == pytest.approx(0.5 * full[1])
    env = CartPoleEnv(seed=0, continuous=True)
    env.reset()
    env.state = s0.copy()
    obs, *_ = env.step(0.5)
    assert np.allclose(obs, half, atol=1e-6)


def test_continuous_mode_clips_and_accepts_discrete_actions():
    assert CartPoleEnv.action_to_force(3.0) == CartPoleEnv.force_mag
    assert CartPoleEnv.action_to_force(-7.5) == -CartPoleEnv.force_mag
    assert CartPoleEnv.action_to_force(1) == CartPoleEnv.force_mag  # ints still mean full pushes
    assert CartPoleEnv.action_to_force(0) == -CartPoleEnv.force_mag
    with pytest.raises(AssertionError):
        CartPoleEnv.action_to_force(float("nan"))
    with pytest.raises(AssertionError):
        CartPoleEnv.action_to_force(2)


def test_theta_limit_widens_termination():
    wide = CartPoleEnv(seed=0, theta_limit_deg=30)
    assert wide.theta_limit_deg == pytest.approx(30)
    assert CartPoleEnv.theta_threshold_radians == pytest.approx(math.radians(12))  # class default untouched
    wide.reset(options={"theta0": math.radians(20)})
    wide.state[3] = 0.0
    _, _, terminated, _, _ = wide.step(1)
    assert not terminated  # 20 degrees is inside a 30 degree limit
    std = CartPoleEnv(seed=0)
    std.reset(options={"theta0": math.radians(11.99)})
    std.state[3] = 2.0
    _, _, terminated, _, _ = std.step(1)
    assert terminated
    with pytest.raises(AssertionError):
        CartPoleEnv(theta_limit_deg=0)


def test_is_terminal_accepts_explicit_threshold():
    s = np.array([0, 0, math.radians(20), 0])
    assert CartPoleEnv.is_terminal(s)
    assert not CartPoleEnv.is_terminal(s, math.radians(30))


def test_discrete_mode_rejects_floats():
    env = CartPoleEnv(seed=0)
    env.reset()
    with pytest.raises(AssertionError):
        env.step(0.5)


gymnasium = pytest.importorskip("gymnasium", reason="gymnasium not installed; skipping parity check")


def test_matches_gymnasium_cartpole_v1_trajectory():
    """Same start state and action sequence must give the same trajectory as the reference."""
    ref = gymnasium.make("CartPole-v1").unwrapped
    ref.reset(seed=0)
    env = CartPoleEnv()
    env.reset()
    env.state = np.array(ref.state, dtype=np.float64)
    rng = np.random.default_rng(0)
    for _ in range(60):
        a = int(rng.integers(2))
        ro, rr, rterm, _, _ = ref.step(a)
        oo, orr, oterm, _, _ = env.step(a)
        assert np.allclose(ro, oo, atol=1e-5)
        assert rr == orr and rterm == oterm
        if rterm:
            break
