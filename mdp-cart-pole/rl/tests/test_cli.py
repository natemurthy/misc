"""End-to-end tests of main.py's command line, run as subprocesses with rendering off."""

import subprocess
import sys
from pathlib import Path

import pytest

from conftest import ROOT, SOLUTIONS

MAIN = ROOT / "main.py"


def run_cli(*args, cwd=ROOT):
    return subprocess.run(
        [sys.executable, str(MAIN), *args],
        cwd=cwd, capture_output=True, text=True, timeout=600,
    )


@pytest.mark.parametrize("soln", SOLUTIONS)
def test_train_then_infer_round_trip(soln, tmp_path):
    model = tmp_path / f"{soln}.npz"
    out = run_cli("--mode", "train", "--soln", soln, "--no-render", "--episodes", "40", "--model", str(model))
    assert out.returncode == 0, out.stderr
    assert model.exists()
    assert f"saved {soln} parameters" in out.stdout

    out = run_cli("--mode", "infer", "--soln", soln, "--no-render", "--episodes", "2",
                  "--model", str(model), "--x0", "0.5", "--theta0", "-4")
    assert out.returncode == 0, out.stderr
    assert f"[infer] {soln}" in out.stdout
    assert "ran 2 episodes" in out.stdout


def test_default_model_path_follows_solution(tmp_path):
    out = run_cli("--mode", "train", "--soln", "1992_reinforce", "--no-render", "--episodes", "5", cwd=tmp_path)
    assert out.returncode == 0, out.stderr
    assert (tmp_path / "cartpole_1992_reinforce.npz").exists()


def test_agent_qlearning_alias_forces_1989(tmp_path):
    out = run_cli("--mode", "train", "--agent", "qlearning", "--soln", "1992_reinforce",
                  "--no-render", "--episodes", "5", cwd=tmp_path)
    assert out.returncode == 0, out.stderr
    assert (tmp_path / "cartpole_1989_qlearning.npz").exists()


def test_random_agent_needs_no_model(tmp_path):
    out = run_cli("--mode", "infer", "--agent", "random", "--no-render", "--episodes", "3", cwd=tmp_path)
    assert out.returncode == 0, out.stderr
    assert "random baseline" in out.stdout


def test_infer_without_model_fails_cleanly(tmp_path):
    out = run_cli("--mode", "infer", "--no-render", "--model", str(tmp_path / "missing.npz"))
    assert out.returncode != 0
    assert "no saved model" in (out.stdout + out.stderr)


@pytest.mark.parametrize("bad", [
    ["--mode", "train", "--x0", "1.0"],
    ["--mode", "infer", "--x0", "2.4"],
    ["--mode", "infer", "--theta0", "12"],
    ["--mode", "train", "--theta-range", "13"],
    ["--soln", "nope"],
])
def test_argument_validation(bad):
    out = run_cli(*bad, "--no-render")
    assert out.returncode == 2  # argparse error
    assert "error" in out.stderr


def test_legacy_qtable_format_still_loads(tmp_path):
    """Q-tables saved by the original single-file script (no __meta__) must still run."""
    import numpy as np
    legacy = tmp_path / "legacy.npz"
    np.savez(legacy, q=np.zeros((1, 1, 8, 16, 2)), bins=np.array([1, 1, 8, 16]),
             lows=np.array([-2.4, -3.0, -0.21, -3.5]), highs=np.array([2.4, 3.0, 0.21, 3.5]), epsilon=0.01)
    out = run_cli("--mode", "infer", "--no-render", "--episodes", "1", "--model", str(legacy))
    assert out.returncode == 0, out.stderr


def test_help_lists_every_solution():
    out = run_cli("--help")
    assert out.returncode == 0
    for s in SOLUTIONS:
        assert s in out.stdout


def test_gym_driver_still_imports_parent_agents():
    """gym/main.py loads this repo's main.py by path and relies on QLearningAgent/RandomAgent."""
    gym_main = ROOT / "gym" / "main.py"
    if not gym_main.exists():
        pytest.skip("gym/ directory not present")
    pytest.importorskip("gymnasium")
    code = (
        "import importlib.util, sys; "
        f"spec = importlib.util.spec_from_file_location('gymmain', r'{gym_main}'); "
        "m = importlib.util.module_from_spec(spec); sys.argv = ['x']; spec.loader.exec_module(m); "
        "assert m.QLearningAgent.__name__ == 'QLearningAgent'; assert m.RandomAgent.__name__ == 'RandomAgent'; print('ok')"
    )
    out = subprocess.run([sys.executable, "-c", code], cwd=ROOT / "gym", capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr
    assert "ok" in out.stdout
