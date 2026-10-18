"""Tests for the hand-tuned linear bang-bang controller and the oc/main.py driver."""

import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from common import CartPoleEnv
from linear_controller.soln import (
    DEFAULT_GAINS,
    LinearBangBangController,
    max_recoverable_angle,
    recovers,
    tune,
)

OC_DIR = Path(__file__).resolve().parent.parent


def _episode(ctrl, env, theta0_deg=None, x0=None):
    obs, _ = env.reset(options={"theta0": math.radians(theta0_deg) if theta0_deg is not None else None, "x0": x0})
    steps, terminated, truncated = 0, False, False
    while not (terminated or truncated):
        obs, _, terminated, truncated, _ = env.step(ctrl.act(obs))
        steps += 1
    return steps, terminated


def test_actions_are_bang_bang_and_deterministic():
    ctrl = LinearBangBangController()
    rng = np.random.default_rng(0)
    for _ in range(50):
        obs = rng.uniform(-0.2, 0.2, size=4)
        a = ctrl.act(obs)
        assert a in (0, 1) and isinstance(a, int)
        assert a == ctrl.act(obs)
        assert a == int(ctrl.feedback(obs) > 0)


def test_balances_standard_task_from_random_starts():
    ctrl = LinearBangBangController()
    for seed in range(5):
        env = CartPoleEnv(seed=seed)
        steps, terminated = _episode(ctrl, env)
        assert steps == 500 and not terminated


def test_recovers_from_full_12_degree_band():
    ctrl = LinearBangBangController()
    env = CartPoleEnv(seed=1)
    for th in (-11.9, -8, 8, 11.9):
        steps, terminated = _episode(ctrl, env, theta0_deg=th)
        assert steps == 500 and not terminated, f"failed from {th} degrees"


def test_recovers_from_20_degrees_with_wide_limit_but_not_from_40():
    assert recovers(DEFAULT_GAINS, 20.0)
    assert not recovers(DEFAULT_GAINS, 40.0)


def test_envelope_matches_documented_values():
    """~34 degrees centered; more with track behind the fall, less with track in front."""
    centered = max_recoverable_angle(DEFAULT_GAINS, 0.0)
    behind = max_recoverable_angle(DEFAULT_GAINS, -1.5)
    ahead = max_recoverable_angle(DEFAULT_GAINS, 1.5)
    assert 30 < centered < 38
    assert behind > centered > ahead
    assert ahead < 25


@pytest.mark.slow
def test_tune_recovers_default_gains_or_better():
    best, angle = tune(k_thetadot=(0.35, 0.5), k_x=(0.02, 0.05), k_xdot=(0.1, 0.2))
    assert angle >= max_recoverable_angle(DEFAULT_GAINS) - 1e-6
    assert len(best) == 4


def test_save_load_round_trip(tmp_path):
    ctrl = LinearBangBangController((1.0, 0.3, 0.01, 0.15))
    ctrl.save(tmp_path / "k.npz")
    loaded = LinearBangBangController.load(tmp_path / "k.npz")
    assert np.allclose(loaded.gains, ctrl.gains)


def run_cli(*args):
    return subprocess.run([sys.executable, str(OC_DIR / "main.py"), *args],
                          cwd=OC_DIR, capture_output=True, text=True, timeout=600)


@pytest.mark.slow
def test_cli_run_headless():
    out = run_cli("--mode", "run", "--no-render", "--episodes", "3", "--theta-limit", "45", "--theta0", "25", "--x0", "-1.0")
    assert out.returncode == 0, out.stderr
    assert out.stdout.count("reached the 500-step limit") == 3


@pytest.mark.slow
def test_cli_envelope_and_validation():
    out = run_cli("--mode", "envelope")
    assert out.returncode == 0, out.stderr
    assert "x0 = +0.0 m" in out.stdout
    out = run_cli("--mode", "run", "--no-render", "--theta0", "12")
    assert out.returncode == 2
    out = run_cli("--mode", "run", "--no-render", "--theta-limit", "-1")
    assert out.returncode == 2
