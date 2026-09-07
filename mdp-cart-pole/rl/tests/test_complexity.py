"""Tests for complexity.py, the implementation-complexity report."""

import subprocess
import sys
import textwrap

import pytest

import complexity
from conftest import ROOT, SOLUTIONS


def test_sloc_excludes_blanks_comments_and_docstrings(tmp_path):
    f = tmp_path / "m.py"
    f.write_text(textwrap.dedent('''
        """Module docstring
        spanning lines."""
        # a comment

        def f(x):
            """Docstring."""
            if x:      # trailing comment
                return 1
            return 0
    '''))
    sloc, branches = complexity.sloc_and_branches(f)
    assert sloc == 4  # def, if, return 1, return 0
    assert branches == 2  # 1 + one if


def test_measure_numpy_solution_has_expected_shape():
    r = complexity.measure("1989_qlearning")
    assert r["framework"] == "numpy"
    assert r["shared_modules"] == ["common/env.py", "common/agent.py", "common/features.py"]
    assert r["own_sloc"] > 20 and r["total_sloc"] == r["own_sloc"] + r["shared_sloc"]
    assert r["learned_params"] == 1 * 1 * 8 * 16 * 2 + 1  # Q-table plus the saved epsilon scalar
    assert r["hyperparams"] == 5


@pytest.mark.skipif("2013_dqn" not in SOLUTIONS, reason="PyTorch not installed")
def test_measure_torch_solution_counts_deep_module():
    r = complexity.measure("2013_dqn")
    assert r["framework"] == "PyTorch"
    assert "common/deep.py" in r["shared_modules"]
    assert r["learned_params"] > 10_000  # two 128-unit layers, online and target copies


def test_markdown_has_one_row_per_solution():
    rows = [complexity.measure(s) for s in SOLUTIONS]
    md = complexity.markdown(rows)
    assert md.count("\n") == len(SOLUTIONS) + 1  # header + separator + rows, no trailing newline
    for s in SOLUTIONS:
        assert f"`{s}`" in md


def test_cli_runs():
    out = subprocess.run([sys.executable, str(ROOT / "complexity.py")], cwd=ROOT, capture_output=True, text=True, timeout=300)
    assert out.returncode == 0, out.stderr
    assert "| solution | own SLOC |" in out.stdout
