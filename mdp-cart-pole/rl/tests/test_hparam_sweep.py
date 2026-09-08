"""Tests for the parallel hyperparameter sweep harness (hparam_sweep.py)."""

import json
import subprocess
import sys

import pytest

from rl_helpers import ROOT
import hparam_sweep as sweep


def test_parse_config():
    assert sweep.parse_config("") == {}
    assert sweep.parse_config("hidden=64, advantage_k=0.3,bins=(1,1,4,8),name=abc") == {
        "hidden": 64, "advantage_k": 0.3, "bins": (1, 1, 4, 8), "name": "abc"}
    with pytest.raises(ValueError):
        sweep.parse_config("nokey")


@pytest.mark.slow
def test_sweep_runs_configs_and_seeds_in_parallel():
    results = sweep.sweep("1989_qlearning", [{}, {"alpha": 0.2}], seeds=[0, 1], episodes=30,
                          eval_angles=(0,), eval_episodes=1, workers=2)
    assert len(results) == 4
    assert {(json.dumps(r["hparams"]), r["seed"]) for r in results} == {
        ("{}", 0), ("{}", 1), ('{"alpha": 0.2}', 0), ('{"alpha": 0.2}', 1)}
    for r in results:
        assert r["episodes_run"] == 30 and not r["aborted"]
        assert "0" in r["eval"] and r["eval"]["0"] > 0


def test_sweep_is_deterministic_per_seed():
    a = sweep.sweep("1992_reinforce", [{}], seeds=[3], episodes=20, eval_episodes=1, workers=1)
    b = sweep.sweep("1992_reinforce", [{}], seeds=[3], episodes=20, eval_episodes=1, workers=1)
    assert a[0]["eval"] == b[0]["eval"]


def test_early_stop_aborts_hopeless_job():
    # a random-like policy cannot average 400 steps after 120 episodes
    results = sweep.sweep("1989_qlearning", [{}], seeds=[0], episodes=300, eval_episodes=1,
                          early_stop=(120, 400.0), workers=1)
    assert results[0]["aborted"] and results[0]["episodes_run"] == 120


@pytest.mark.slow
def test_cli_table_and_json(tmp_path):
    out = subprocess.run(
        [sys.executable, str(ROOT / "hparam_sweep.py"), "--soln", "1989_qlearning", "--config", "",
         "--config", "alpha=0.2", "--seeds", "0", "--episodes", "20", "--eval-angles", "0", "5",
         "--eval-episodes", "1", "--workers", "2", "--json", str(tmp_path / "r.json")],
        cwd=ROOT, capture_output=True, text=True, timeout=600)
    assert out.returncode == 0, out.stderr
    assert "best100" in out.stdout and "2 jobs" in out.stdout
    data = json.loads((tmp_path / "r.json").read_text())
    assert len(data) == 2 and data[1]["hparams"] == {"alpha": 0.2}


@pytest.mark.slow
def test_cli_refuses_wide_limit_for_grid_solutions():
    out = subprocess.run([sys.executable, str(ROOT / "hparam_sweep.py"), "--soln", "1989_qlearning",
                          "--theta-limit", "30", "--episodes", "5"], cwd=ROOT, capture_output=True, text=True)
    assert out.returncode == 2
