"""
Measure the implementation complexity of every solution and print a Markdown table.

For each directory in main.SOLUTIONS:
  own SLOC        source lines in soln.py: no blank lines, comments or docstrings
  branches        cyclomatic-style count of decision points in soln.py
                  (1 + if / for / while / ternary / boolean operator / except / comprehension)
  shared SLOC     source lines of the common/ modules the solution depends on
                  (env, agent and features for all; deep for the PyTorch solutions)
  learned params  total size of the arrays returned by Agent.state_dict() at default settings
  hyperparams     number of entries in Agent.hparams()

Usage:
    python complexity.py            # Markdown table on stdout
    python complexity.py --json     # machine-readable

These are measures of what you have to read and tune, not of how hard the
mathematics is; see the "Complexity" section of README.md for the rubric that
covers the latter. Solutions that need PyTorch are skipped if it is not installed.
"""

import argparse
import ast
import importlib
import io
import json
import sys
import tokenize
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import main as driver  # noqa: E402

BRANCH_NODES = (ast.If, ast.For, ast.While, ast.IfExp, ast.BoolOp, ast.ExceptHandler, ast.comprehension)


def sloc_and_branches(path):
    """Return (source lines of code, decision points) for one Python file."""
    src = Path(path).read_text()
    tree = ast.parse(src)
    doc_lines = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", None)
            if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) \
                    and isinstance(body[0].value.value, str):
                doc_lines.update(range(body[0].lineno, body[0].end_lineno + 1))
    skip = {tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT,
            tokenize.ENCODING, tokenize.ENDMARKER}
    code_lines = set()
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type in skip or tok.start[0] in doc_lines:
            continue
        code_lines.add(tok.start[0])
    branches = 1 + sum(isinstance(n, BRANCH_NODES) for n in ast.walk(tree))
    return len(code_lines), branches


def shared_modules(soln):
    """common/ files a solution depends on, from its imports."""
    src = (HERE / soln / "soln.py").read_text()
    mods = ["common/env.py", "common/agent.py"]  # every agent subclasses BaseAgent and runs in the env
    if any(k in src for k in ("normalize_obs", "GridDiscretizer", "boxes_index", "from common import", "common.features")):
        mods.append("common/features.py")
    if "common.deep" in src:
        mods.append("common/deep.py")
    return mods


def measure(soln):
    try:
        mod = importlib.import_module(f"{soln}.soln")
    except ModuleNotFoundError as e:
        if e.name == "torch":
            return None
        raise
    agent = mod.Agent(seed=0)
    own, branches = sloc_and_branches(HERE / soln / "soln.py")
    deps = shared_modules(soln)
    shared = sum(sloc_and_branches(HERE / d)[0] for d in deps)
    return {
        "solution": soln,
        "own_sloc": own,
        "branches": branches,
        "shared_sloc": shared,
        "shared_modules": deps,
        "total_sloc": own + shared,
        "learned_params": int(sum(int(v.size) for v in agent.state_dict().values())),
        "hyperparams": len(agent.hparams()),
        "continuous_actions": bool(getattr(agent, "continuous_actions", False)),
        "framework": "PyTorch" if "common/deep.py" in deps else "numpy",
    }


def markdown(rows):
    head = "| solution | own SLOC | branches | shared SLOC | total SLOC | learned params | hyperparams | framework |"
    sep = "|---|---|---|---|---|---|---|---|"
    body = [f"| `{r['solution']}` | {r['own_sloc']} | {r['branches']} | {r['shared_sloc']} | {r['total_sloc']} | "
            f"{r['learned_params']:,} | {r['hyperparams']} | {r['framework']} |" for r in rows]
    return "\n".join([head, sep, *body])


def main(argv=None):
    p = argparse.ArgumentParser(description="implementation-complexity table for every solution")
    p.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    args = p.parse_args(argv)
    rows = [r for r in (measure(s) for s in driver.SOLUTIONS) if r is not None]
    skipped = [s for s in driver.SOLUTIONS if s not in {r["solution"] for r in rows}]
    if args.json:
        print(json.dumps(rows, indent=1))
    else:
        print(markdown(rows))
        if skipped:
            print(f"\n(skipped, PyTorch not installed: {', '.join(skipped)})")


if __name__ == "__main__":
    main()
