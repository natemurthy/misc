"""
Shared helpers for the rl/ test suite: solution list, headless train/evaluate loops.

Kept out of conftest.py on purpose. This repository has two test suites (rl/tests
and oc/tests), each with its own conftest.py; when both are collected in one
session, `import conftest` is ambiguous, so test files import from here instead.

Run everything:                pytest            (from rl/ or from the repository root)
Only the quick tests:          pytest -m fast    (every test under 0.1 s; a few seconds in total)
Everything slower:             pytest -m slow    (learning runs, subprocess CLI checks)
One solution's tests:          pytest tests/test_1989_qlearning.py    (interface + method-specific)
One solution's learning test:  pytest -k 1989 tests/test_learning.py
"""


import contextlib
import importlib
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import main.py once so its SOLUTIONS list is the single source of truth.
import main as driver  # noqa: E402
from common import CartPoleEnv  # noqa: E402

SOLUTIONS = list(driver.SOLUTIONS)
LEARN_THRESHOLD = 100.0  # steps a frozen policy must average to count as having learned (random: ~22)
try:
    import torch  # noqa: F401
    HAVE_TORCH = True
except ModuleNotFoundError:
    HAVE_TORCH = False
    SOLUTIONS = [s for s in SOLUTIONS if s not in driver.TORCH_SOLUTIONS]


def load_agent_class(name):
    return importlib.import_module(f"{name}.soln").Agent


def make_env(agent, seed=0, theta_limit_deg=None):
    """Environment in the action mode the agent expects (continuous for the 1999+ continuous solutions)."""
    return CartPoleEnv(seed=seed, continuous=getattr(agent, "continuous_actions", False),
                       theta_limit_deg=theta_limit_deg)


def train(agent, episodes, seed=0, theta_range_deg=12.0, checkpoint=True, theta_limit_deg=None):
    """
    Headless training loop mirroring main.run(): full-range start angles and
    best-checkpoint selection on a 50-episode moving average. Returns the list
    of episode returns and leaves `agent` holding the best snapshot.
    """
    env = make_env(agent, seed, theta_limit_deg)
    start_rng = np.random.default_rng(seed + 1)
    rets, best, snap = [], -np.inf, None
    for _ in range(episodes):
        theta0 = start_rng.uniform(-math.radians(theta_range_deg), math.radians(theta_range_deg))
        obs, _ = env.reset(options={"theta0": theta0})
        done, total = False, 0.0
        while not done:
            a = agent.act(obs)
            nxt, r, term, trunc, _ = env.step(a)
            done = term or trunc
            agent.learn(obs, a, r, nxt, term)
            obs = nxt
            total += r
        agent.end_episode()
        rets.append(total)
        if checkpoint and len(rets) >= 50:
            avg = np.mean(rets[-50:])
            if avg > best:
                best, snap = avg, agent.snapshot()
    if snap is not None:
        agent.restore(snap)
    return rets


def evaluate(agent, episodes=10, seed=99, theta0_deg=None, x0=None, theta_limit_deg=None):
    """Mean total reward of a frozen agent over `episodes` episodes."""
    agent.freeze()
    env = make_env(agent, seed, theta_limit_deg)
    opts = {"x0": x0, "theta0": math.radians(theta0_deg) if theta0_deg is not None else None}
    totals = []
    for _ in range(episodes):
        obs, _ = env.reset(options=opts)
        done, total = False, 0.0
        while not done:
            obs, r, term, trunc, _ = env.step(agent.act(obs))
            done = term or trunc
            total += r
        totals.append(total)
    return float(np.mean(totals))


# --------------------------------------------------------------------------- #
# PILCO: fit the Gaussian-process model once per session                       #
# --------------------------------------------------------------------------- #
# A PILCO fit (GP marginal likelihood + policy optimization by L-BFGS through 30 moment-matching
# steps) costs a few seconds, and the agent refits at every episode end while learning. Running
# the nine shared interface tests on a fresh agent therefore cost about 150 s. Instead the
# `pilco_fit` session fixture in conftest.py calls fit_pilco() once, and every PILCO test that
# needs a fitted model starts from that record: prefitted_pilco_class() gives the shared
# interface tests an agent whose fit budget is already spent, so nothing refits.

@contextlib.contextmanager
def count_dynamics_calls(counter):
    """Count calls to the environment's true dynamics (both entry points) inside the block."""
    saved = {k: CartPoleEnv.__dict__[k] for k in ("dynamics", "dynamics_force")}
    real, real_force = CartPoleEnv.dynamics, CartPoleEnv.dynamics_force

    def counting(state, action):
        counter["n"] += 1
        return real(state, action)

    def counting_force(state, force):
        counter["n"] += 1
        return real_force(state, force)

    CartPoleEnv.dynamics, CartPoleEnv.dynamics_force = staticmethod(counting), staticmethod(counting_force)
    try:
        yield counter
    finally:
        for k, v in saved.items():
            setattr(CartPoleEnv, k, v)


def fit_pilco(seed=0, max_fits=2, episodes=3):
    """
    Train one PILCO agent for `episodes` episodes with a budget of `max_fits` GP fits and return a
    record of the run. Only the agent's own calls (act, learn, end_episode) run under the
    dynamics counter; the environment's stepping does not, so `dynamics_calls` is the number of
    times the *agent* touched the true model, which must be zero for a model-learning method.
    """
    agent = load_agent_class("2011_pilco")(seed=seed, max_fits=max_fits)
    env = make_env(agent, seed)
    counter = {"n": 0}
    returns, snapshots = [], []
    for _ in range(episodes):
        obs, _ = env.reset()
        done, total = False, 0.0
        while not done:
            with count_dynamics_calls(counter):
                a = agent.act(obs)
            nxt, r, term, trunc, _ = env.step(a)
            with count_dynamics_calls(counter):
                agent.learn(obs, a, r, nxt, term)
            obs, done, total = nxt, term or trunc, total + r
        with count_dynamics_calls(counter):
            agent.end_episode()
        returns.append(total)
        snapshots.append(agent.snapshot())
    after_budget = snapshots[max_fits - 1]
    return {
        "hparams": agent.hparams(), "state": agent.snapshot(), "fits": agent.fits, "episodes": agent.episodes,
        "n_data": len(agent.data_x), "returns": returns, "dynamics_calls": counter["n"],
        "state_unchanged_after_budget": all(np.array_equal(after_budget[k], v) for k, v in snapshots[-1].items()),
    }


def prefitted_pilco_class(record):
    """A PILCO Agent class whose instances start from `record` (see fit_pilco) with the fit budget
    spent: act() runs the fitted controller, learn()/end_episode() record nothing and never refit.
    save()/load() and the rest of the BaseAgent interface are the real ones."""
    Base = load_agent_class("2011_pilco")

    class PrefittedPILCOAgent(Base):
        def __init__(self, seed=None, **hparams):
            super().__init__(seed=seed, **{**record["hparams"], **hparams})
            self.load_state_dict(record["state"])
            self.episodes = self.fits = self.max_fits

    PrefittedPILCOAgent.__name__ = PrefittedPILCOAgent.__qualname__ = Base.__name__ + "Prefitted"
    return PrefittedPILCOAgent
