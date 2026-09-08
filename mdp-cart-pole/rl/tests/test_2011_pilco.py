"""
Tests for the 2011 PILCO solution (Deisenroth and Rasmussen): GP model, moment matching, cost,
model use, action hold, and the shared agent interface.

A PILCO fit (GP marginal likelihood, then L-BFGS on the policy through 30 moment-matching steps)
costs a few seconds and happens at every episode end while learning. This module therefore fits
ONCE, in the module-scoped `pilco_fit` fixture (rl_helpers.fit_pilco: two trials, two fits, under a
counter on the true dynamics). The interface checks run on a pre-fitted agent whose fit budget is
spent, and the model-use checks read the fit record, so no test here refits. Everything in this
file is `fast` by the suite's convention; the one fit is paid in the fixture.
"""

import math

import numpy as np
import pytest

from common import CartPoleEnv
from interface_checks import AgentInterfaceTests
from rl_helpers import fit_pilco, load_agent_class, make_env, prefitted_pilco_class

torch = pytest.importorskip("torch")

DT = torch.float64


@pytest.fixture(scope="module")
def pilco_fit():
    """The one PILCO fit of this module: two trials, two GP fits, a few seconds."""
    return fit_pilco(seed=0)


@pytest.fixture
def agent():
    return load_agent_class("2011_pilco")(seed=0)


class TestInterface(AgentInterfaceTests):
    solution = "2011_pilco"

    @pytest.fixture(autouse=True)
    def _agent_class(self, pilco_fit):
        # a fitted agent with its fit budget spent: act/learn/freeze/save/load without refitting
        self.agent_class = prefitted_pilco_class(pilco_fit)


def _synthetic_gp(agent, n=40):
    """Give the agent's GP a smooth synthetic dataset and moderate hyperparameters."""
    gen = torch.Generator().manual_seed(3)
    X = torch.rand(n, 5, generator=gen, dtype=DT) * 2 - 1
    Y = torch.stack([torch.sin(2 * X[:, 0]) * X[:, 4], X[:, 1] ** 2, torch.cos(X[:, 2] + X[:, 3]), 0.5 * X[:, 4]], 1)
    agent.gp.set_data(X, Y)
    with torch.no_grad():
        agent.gp.log_ell.fill_(math.log(0.7))
        agent.gp.log_sf.fill_(0.0)
        agent.gp.log_sn.fill_(math.log(0.01))
        beta, iK = agent.gp.posterior()
    return X, Y, beta, iK, gen


def test_gp_mean_reproduces_targets_at_training_inputs(agent):
    X, Y, beta, iK, _ = _synthetic_gp(agent)
    with torch.no_grad():
        pred = (agent.gp.kernel(X, X) @ beta[:, :, None]).squeeze(-1).T
    assert torch.allclose(pred, Y, atol=1e-3)


def test_marginal_likelihood_fit_recovers_a_noise_free_function(agent):
    X, Y, *_ = _synthetic_gp(agent, n=60)
    before = agent.gp.nlml().item()
    after = agent._optimize(agent.gp.parameters(), agent.gp.nlml, 30)
    assert after < before
    assert torch.exp(agent.gp.log_sn).max().item() < 0.05, "noise-free targets should get a small noise estimate"


def test_moment_matching_agrees_with_monte_carlo(agent):
    X, Y, beta, iK, gen = _synthetic_gp(agent)
    mu = torch.tensor([0.2, -0.1, 0.3, 0.0, 0.1], dtype=DT)
    A = torch.randn(5, 5, generator=gen, dtype=DT) * 0.15
    S = A @ A.T + 0.01 * torch.eye(5, dtype=DT)
    with torch.no_grad():
        M, V, C = agent.gp.predict_gaussian(mu, S, beta, iK)
        xs = mu + torch.randn(100_000, 5, generator=gen, dtype=DT) @ torch.linalg.cholesky(S).T
        Ks = agent.gp.kernel(xs, X)                                        # (4, N, n)
        means = (Ks @ beta[:, :, None]).squeeze(-1)                         # GP posterior mean at each sample
        variances = torch.exp(2 * agent.gp.log_sf)[:, None] - torch.einsum("ani,aij,anj->an", Ks, iK, Ks)
        M_mc = means.mean(1)
        V_mc = torch.cov(means) + torch.diag(variances.mean(1))
        C_mc = torch.linalg.solve(S, (xs - mu).T @ (means.T - M_mc) / xs.shape[0])
    assert torch.allclose(M, M_mc, atol=5e-3)
    assert torch.allclose(V, V_mc, atol=5e-3)
    assert torch.allclose(C, C_mc, atol=1e-2)
    assert torch.allclose(V, V.T) and torch.linalg.eigvalsh(V).min() > 0


def test_squashed_control_moments_agree_with_monte_carlo(agent):
    gen = torch.Generator().manual_seed(4)
    mu = torch.tensor([0.1, 0.0, -0.3, 0.2], dtype=DT)
    B = torch.randn(4, 4, generator=gen, dtype=DT) * 0.3
    S = B @ B.T + 0.01 * torch.eye(4, dtype=DT)
    with torch.no_grad():
        agent.policy.w.copy_(torch.tensor([0.5, -1.0, 2.0, 0.7], dtype=DT))
        agent.policy.b.fill_(0.2)
        mu_u, var_u, cxu = agent.control_moments(mu, S)
        xs = mu + torch.randn(200_000, 4, generator=gen, dtype=DT) @ torch.linalg.cholesky(S).T
        u = agent.policy.squash(xs @ agent.policy.w + agent.policy.b)
        cost = 1 - torch.exp(-0.5 * torch.einsum("ni,ij,nj->n", xs, agent.W, xs))
    # tolerances are about five Monte Carlo standard errors at this sample size
    assert abs(mu_u.item() - u.mean().item()) < 1e-2
    assert abs(var_u.item() - u.var().item()) < 1e-2
    assert torch.allclose(cxu, ((xs - mu) * (u - u.mean())[:, None]).mean(0), atol=1e-2)
    assert abs(agent.expected_saturating_cost(mu, S).item() - cost.mean().item()) < 1e-2


def test_saturating_cost_is_zero_at_target_and_one_far_away(agent):
    tiny = 1e-12 * torch.eye(4, dtype=DT)
    assert agent.expected_saturating_cost(torch.zeros(4, dtype=DT), tiny).item() == pytest.approx(0.0, abs=1e-9)
    far = torch.tensor([1.0, 0.0, 0.0, 0.0], dtype=DT)      # cart 2.4 m off center, in normalized units
    assert agent.expected_saturating_cost(far, tiny).item() > 0.999
    tilted = torch.tensor([0.0, 0.0, 1.0, 0.0], dtype=DT)   # pole at the 12 degree limit
    c = agent.expected_saturating_cost(tilted, tiny).item()
    assert 0.0 < c < 1.0
    # velocities carry no cost of their own
    fast = torch.tensor([0.0, 1.0, 0.0, 1.0], dtype=DT)
    assert agent.expected_saturating_cost(fast, tiny).item() == pytest.approx(0.0, abs=1e-9)


def test_squash_is_bounded_and_odd(agent):
    v = torch.linspace(-10, 10, 1001, dtype=DT)
    u = agent.policy.squash(v)
    assert u.abs().max().item() <= 1.0 + 1e-12
    assert torch.allclose(u, -agent.policy.squash(-v))
    assert agent.policy.squash(torch.tensor(math.pi / 2, dtype=DT)).item() == pytest.approx(1.0)


def test_action_is_held_for_hold_steps_while_learning(agent):
    env = make_env(agent, 0)
    obs, _ = env.reset()
    actions = []
    for _ in range(3 * agent.hold):
        a = agent.act(obs)
        actions.append(a)
        nxt, r, term, trunc, _ = env.step(a)
        agent.learn(obs, a, r, nxt, term)
        obs = nxt
        if term or trunc:
            break
    for k in range(0, len(actions) - agent.hold + 1, agent.hold):
        assert len(set(actions[k:k + agent.hold])) == 1
    # the recorded transitions span exactly one hold each
    assert len(agent.data_x) == len(actions) // agent.hold


def test_transitions_are_recorded_at_the_coarse_time_step(agent):
    env = make_env(agent, 0)
    obs, _ = env.reset()
    trajectory = [np.asarray(obs, dtype=np.float64)]
    for _ in range(agent.hold):
        a = agent.act(obs)
        nxt, r, term, trunc, _ = env.step(a)
        agent.learn(obs, a, r, nxt, term)
        obs = nxt
        trajectory.append(np.asarray(obs, dtype=np.float64))
    assert len(agent.data_x) == 1
    assert np.allclose(agent.data_x[0], trajectory[0])
    assert np.allclose(agent.data_x[0] + agent.data_y[0], trajectory[-1])


# ---- the fitted model: all from this module's single fit (the `pilco_fit` fixture) -------------- #
# fit_pilco() runs 3 episodes with max_fits=2 under a counter on CartPoleEnv.dynamics(_force) that
# is active only around the agent's own calls. The tests below read that record; none refits.

def test_learning_never_calls_the_true_dynamics(pilco_fit):
    """PILCO plans on its own learned GP; the environment's model must stay off limits."""
    assert pilco_fit["fits"] == 2 and pilco_fit["n_data"] > 0
    assert pilco_fit["dynamics_calls"] == 0


def test_learning_stops_after_max_fits(pilco_fit):
    """The third episode ran after the two-fit budget was spent and must not have touched the model."""
    assert pilco_fit["episodes"] == 3 and pilco_fit["fits"] == 2
    assert pilco_fit["state_unchanged_after_budget"]


def test_two_fits_already_learn_from_near_upright(pilco_fit):
    """Data efficiency, the point of the method: after two trials of about 20 steps each (a few
    tenths of a second of experience) the fitted controller clears the suite's learning threshold,
    about five times the random baseline, from Gymnasium's default start."""
    first, last = pilco_fit["returns"][0], pilco_fit["returns"][-1]
    assert first < 60 and last >= 100, pilco_fit["returns"]


def test_saved_model_contains_the_gp_and_the_policy(pilco_fit, tmp_path):
    agent = prefitted_pilco_class(pilco_fit)(seed=0)
    assert agent.gp.X.shape[0] == pilco_fit["n_data"] > 0
    agent.save(tmp_path / "m.npz")
    loaded = load_agent_class("2011_pilco").load(tmp_path / "m.npz")
    assert torch.equal(loaded.gp.X, agent.gp.X) and torch.equal(loaded.gp.Y, agent.gp.Y)
    assert torch.equal(loaded.policy.w, agent.policy.w) and torch.equal(loaded.policy.b, agent.policy.b)
    # a loaded (frozen) model acts exactly like the one that was saved
    loaded.freeze(); agent.freeze()
    obs = np.array([0.1, -0.2, 0.05, 0.3])
    assert loaded.act(obs) == agent.act(obs)


def test_first_learning_trials_are_always_rendered():
    """main.py animates PILCO's few, slow learning trials regardless of --render-every."""
    import main

    agent = load_agent_class("2011_pilco")(seed=0)
    assert agent.render_first_episodes == 18  # 15 fits + 3 deployed episodes
    assert load_agent_class("2011_pilco")(seed=0, max_fits=4).render_first_episodes == 7
    assert all(main.episode_is_rendered(e, 100, agent) for e in range(1, 19))
    assert not main.episode_is_rendered(19, 100, agent) and main.episode_is_rendered(100, 100, agent)
    # every other solution keeps the old rule: episode 1 and every render_every-th
    other = load_agent_class("1989_qlearning")(seed=0)
    assert [e for e in range(1, 201) if main.episode_is_rendered(e, 100, other)] == [1, 100, 200]
