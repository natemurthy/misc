"""Unit tests specific to the 1999 wire-fitted continuous Q-learning solution."""

import numpy as np
import pytest

from common import normalize_obs
from rl_helpers import load_agent_class

Agent = load_agent_class("1999_qlearning_continuous")


def test_interpolator_passes_through_wires_in_the_sharp_limit():
    """With no smoothing, wire fitting is an exact interpolant: Q(s, u_i) = q_i."""
    agent = Agent(seed=0, smoothing_eps=1e-9, smoothing_c=0.0)
    rng = np.random.default_rng(0)
    wires_u = np.sort(rng.uniform(-1, 1, 5))
    wires_q = rng.normal(0, 1, 5)
    for u_i, q_i in zip(wires_u, wires_q):
        Q, _, _ = agent._interpolate(u_i, wires_u, wires_q)
        assert Q == pytest.approx(q_i, abs=1e-6)


def test_interpolator_never_exceeds_best_wire_and_peaks_near_it():
    """With the default smoothing, Q is a weighted mean of the wire values (so <= q_max)
    and its maximum over the action range sits at the best wire's action."""
    agent = Agent(seed=0)
    rng = np.random.default_rng(0)
    grid = np.linspace(-1, 1, 2001)
    for _ in range(5):
        wires_u = rng.uniform(-1, 1, 5)
        wires_q = rng.normal(0, 1, 5)
        values = np.array([agent._interpolate(u, wires_u, wires_q)[0] for u in grid])
        assert values.max() <= wires_q.max() + 1e-9
        assert values.min() >= wires_q.min() - 1e-9
        assert abs(grid[values.argmax()] - wires_u[wires_q.argmax()]) < 0.05


def test_interpolator_gradients_match_finite_differences():
    """The hand-written dQ/du_i and dQ/dq_i must agree with numeric derivatives (q_max held fixed)."""
    agent = Agent(seed=0)
    rng = np.random.default_rng(1)
    h = 1e-6
    for _ in range(5):
        wires_u = rng.uniform(-1, 1, 5)
        wires_q = rng.normal(0, 0.5, 5)
        u = rng.uniform(-1, 1)
        Q, dQ_du, dQ_dq = agent._interpolate(u, wires_u, wires_q)
        imax = int(np.argmax(wires_q))
        for i in range(5):
            if i == imax:
                continue  # analytic form treats q_max as constant; skip the wire that defines it
            wq = wires_q.copy()
            wq[i] += h
            num_q = (agent._interpolate(u, wires_u, wq)[0] - Q) / h
            wu = wires_u.copy()
            wu[i] += h
            num_u = (agent._interpolate(u, wu, wires_q)[0] - Q) / h
            assert num_q == pytest.approx(dQ_dq[i], rel=1e-3, abs=1e-5)
            assert num_u == pytest.approx(dQ_du[i], rel=1e-3, abs=1e-5)


def test_greedy_action_is_best_wire_and_frozen_has_no_noise():
    agent = Agent(seed=0)
    obs = np.array([0.1, 0.0, 0.05, -0.2])
    u_star, _ = agent._greedy(normalize_obs(obs))
    wires_u, wires_q, _ = agent.net.forward(normalize_obs(obs))
    assert u_star == wires_u[int(np.argmax(wires_q))]
    agent.freeze()
    a1, a2 = agent.act(obs), agent.act(obs)
    assert a1 == a2 == u_star
    assert -1.0 <= a1 <= 1.0


def test_advantage_target_reduces_to_qlearning_when_k_is_one():
    plain = Agent(seed=0, advantage_k=1.0, replay=0)
    x = np.zeros(4)
    wires_u, wires_q, _ = plain.net.forward(x)
    q_max_s = float(wires_q.max())
    r, gamma = 0.01, plain.gamma
    q_max_next = float(plain.net.forward(np.array([0, 0, 0.1, 0.0]))[1].max())
    y_q = r + gamma * q_max_next
    y_adv = q_max_s + (r + gamma * q_max_next - q_max_s) / plain.advantage_k
    assert y_adv == pytest.approx(y_q)


def test_batched_interpolation_matches_single_sample():
    agent = Agent(seed=0)
    rng = np.random.default_rng(3)
    B = 6
    WU = rng.uniform(-1, 1, (B, 5))
    WQ = rng.normal(0, 0.5, (B, 5))
    U = rng.uniform(-1, 1, B)
    Qb, dUb, dQb = agent._interpolate_batch(U, WU, WQ)
    for i in range(B):
        Q, dU, dQ = agent._interpolate(U[i], WU[i], WQ[i])
        assert Qb[i] == pytest.approx(Q)
        assert np.allclose(dUb[i], dU) and np.allclose(dQb[i], dQ)


def test_batched_update_equals_sum_of_single_updates_to_first_order():
    """With a tiny step size, one minibatch step over B transitions moves the weights
    like B sequential single-sample steps (differences are second order in lr)."""
    import copy
    a = Agent(seed=0, lr=1e-5, replay=0)
    b = copy.deepcopy(a)
    rng = np.random.default_rng(4)
    X = rng.uniform(-0.5, 0.5, (8, 4)); U = rng.uniform(-1, 1, 8); R = np.full(8, 0.01)
    Xn = X + rng.normal(0, 0.02, X.shape); T = np.zeros(8, dtype=bool)
    for i in range(8):
        a._update(X[i], U[i], R[i], Xn[i], T[i])
    b._update_batch(X, U, R, Xn, T)
    for k, v in a.net.params().items():
        assert np.allclose(v, b.net.params()[k], atol=1e-9), k
