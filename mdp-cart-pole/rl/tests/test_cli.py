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
    ["--mode", "train", "--theta-limit", "-5"],
    ["--mode", "train", "--theta-limit", "0"],
    ["--mode", "train", "--theta-limit", "30", "--soln", "1989_qlearning"],
    ["--mode", "train", "--theta-limit", "30", "--soln", "1983_actor_critic"],
    ["--mode", "train", "--theta-limit", "30", "--theta-range", "35", "--soln", "1992_reinforce"],
    ["--mode", "infer", "--theta-limit", "30", "--theta0", "30", "--soln", "1992_reinforce"],
])
def test_argument_validation(bad):
    out = run_cli(*bad, "--no-render")
    assert out.returncode == 2  # argparse error
    assert "error" in out.stderr


@pytest.mark.parametrize("soln", ["1986_actor_critic_backprop", "1992_reinforce", "1999_qlearning_continuous"])
def test_theta_limit_accepted_for_wide_angle_solutions(soln, tmp_path):
    model = tmp_path / "m.npz"
    out = run_cli("--mode", "train", "--soln", soln, "--no-render", "--episodes", "10",
                  "--theta-limit", "30", "--model", str(model))
    assert out.returncode == 0, out.stderr
    out = run_cli("--mode", "infer", "--soln", soln, "--no-render", "--episodes", "1",
                  "--theta-limit", "30", "--theta0", "25", "--model", str(model))
    assert out.returncode == 0, out.stderr


def test_wide_angle_recipe_for_1999_runs(tmp_path):
    """The documented wide-angle hyperparameters are accepted and saved (learning itself is too slow to test here)."""
    import json
    import numpy as np
    model = tmp_path / "wide.npz"
    out = run_cli("--mode", "train", "--soln", "1999_qlearning_continuous", "--no-render", "--episodes", "5",
                  "--theta-limit", "30", "--hparam", "hidden=64", "--hparam", "advantage_k=0.3",
                  "--hparam", "lr=0.005", "--model", str(model))
    assert out.returncode == 0, out.stderr
    meta = json.loads(str(np.load(model)["__meta__"]))["hparams"]
    assert meta["hidden"] == 64 and meta["advantage_k"] == 0.3 and meta["lr"] == 0.005
    out = run_cli("--mode", "infer", "--soln", "1999_qlearning_continuous", "--no-render", "--episodes", "1",
                  "--theta-limit", "30", "--theta0", "25", "--model", str(model))
    assert out.returncode == 0, out.stderr


def test_theta_limit_with_random_agent_is_fine():
    out = run_cli("--mode", "infer", "--agent", "random", "--no-render", "--episodes", "2", "--theta-limit", "40")
    assert out.returncode == 0, out.stderr


def test_hparam_overrides_are_applied_and_saved(tmp_path):
    import json
    import numpy as np
    model = tmp_path / "m.npz"
    out = run_cli("--mode", "train", "--soln", "1989_qlearning", "--no-render", "--episodes", "5",
                  "--hparam", "alpha=0.25", "--hparam", "bins=(1,1,4,8)", "--model", str(model))
    assert out.returncode == 0, out.stderr
    meta = json.loads(str(np.load(model)["__meta__"]))["hparams"]
    assert meta["alpha"] == 0.25 and meta["bins"] == [1, 1, 4, 8]
    out = run_cli("--mode", "infer", "--soln", "1989_qlearning", "--no-render", "--episodes", "1", "--model", str(model))
    assert out.returncode == 0, out.stderr  # loads with its saved hyperparameters


def test_hparam_validation():
    assert run_cli("--mode", "train", "--no-render", "--hparam", "nokey").returncode == 2
    assert run_cli("--mode", "infer", "--no-render", "--hparam", "alpha=0.1").returncode == 2
    out = run_cli("--mode", "train", "--no-render", "--episodes", "1", "--hparam", "bogus=1", "--model", "/dev/null")
    assert out.returncode != 0 and "bad --hparam" in (out.stdout + out.stderr)


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
