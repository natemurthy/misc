"""
Shared helpers for the rl/ test suite: solution list, headless train/evaluate loops.

Kept out of conftest.py on purpose. This repository has two test suites (rl/tests
and oc/tests), each with its own conftest.py; when both are collected in one
session, `import conftest` is ambiguous, so test files import from here instead.

Run everything:                pytest            (from rl/ or from the repository root)
Only the quick tests:          pytest -m fast    (unit + CLI; a few seconds)
Only the learning tests:       pytest -m slow
One solution's learning test:  pytest -k 1989 tests/test_learning.py
"""


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
