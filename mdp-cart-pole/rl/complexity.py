"""
Measure the implementation complexity of every solution and print a Markdown table.

For each directory in main.SOLUTIONS:
  own SLOC        source lines in soln.py: no blank lines, comments or docstrings
  branches        cyclomatic-style count of decision points in soln.py
                  (1 + if / for / while / ternary / boolean operator / except / comprehension)
  shared SLOC     source lines of the common/ modules the solution depends on
                  (env, agent and features for all; deep for the PyTorch solutions)
  network arch    the neural networks the agent trains, read off the constructed agent: layer
                  widths of each torch nn.Linear chain or hand-written numpy W1/W2 pair; '-' if none
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


def _torch_chains(agent):
    """(name, activation, [in, h, ..., out]) for every registered nn.Module that is a chain of Linear layers."""
    import torch.nn as nn
    out = []
    for name, module in getattr(agent, "modules", {}).items():
        linears = [m for m in module.modules() if isinstance(m, nn.Linear)]
        if not linears:
            continue
        act = next((type(m).__name__ for m in module.modules() if not isinstance(m, (nn.Linear, nn.Sequential))), "")
        out.append((name, act, [linears[0].in_features] + [m.out_features for m in linears]))
    return out


def _numpy_chains(agent):
    """The numpy solutions write their own two-layer nets as objects holding W1 (hidden, in) and W2."""
    out = []
    for name, obj in vars(agent).items():
        W1, W2 = getattr(obj, "W1", None), getattr(obj, "W2", None)
        if W1 is None or W2 is None or getattr(W1, "ndim", 0) != 2:
            continue
        out.append((name, "Tanh", [W1.shape[1], W1.shape[0], W2.shape[0] if W2.ndim == 2 else 1]))
    return out


def network_architecture(agent):
    """One cell: 'MLP (tanh): actor 4 × 16 × 1, critic 4 × 16 × 1', target copies collapsed; '-' without nets."""
    chains = _torch_chains(agent) if hasattr(agent, "modules") else _numpy_chains(agent)
    if not chains:
        return "-"
    groups = {}  # shape -> [names]
    for name, act, shape in chains:
        groups.setdefault(tuple(shape), []).append(name)
    parts = []
    for shape, names in groups.items():
        bases = [n for n in names if not n.endswith("_target")]
        label = "/".join(bases) + (" (+ target)" if len(bases) < len(names) else "")
        parts.append(f"{label} {' × '.join(map(str, shape))}")
    acts = {act.lower() for _, act, _ in chains}
    return f"MLP ({', '.join(sorted(acts))}): " + ", ".join(parts)


# Learners that are differentiated with PyTorch but are not neural networks, so the layer-width
# extraction above finds nothing; described by hand so the cell explains itself instead of reading "-".
NON_NETWORK_LEARNERS = {
    "2011_pilco": "GP dynamics model + 5-parameter linear controller",
}


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
        "network_architecture": NON_NETWORK_LEARNERS.get(soln) or network_architecture(agent),
        "learned_params": int(sum(int(v.size) for v in agent.state_dict().values())),
        "hyperparams": len(agent.hparams()),
        "continuous_actions": bool(getattr(agent, "continuous_actions", False)),
        "framework": "PyTorch" if "common/deep.py" in deps else "numpy",
    }


def markdown(rows):
    head = ("| Solution | Own SLOC | Branches | Shared SLOC | Total SLOC | Network architecture | Learned params | "
            "Hyperparams | Library |")
    sep = "|---|---|---|---|---|---|---|---|---|"
    body = [f"| [`{r['solution']}/`]({r['solution']}/README.md) | {r['own_sloc']} | {r['branches']} | {r['shared_sloc']} | {r['total_sloc']} | "
            f"{r['network_architecture']} | {r['learned_params']:,} | {r['hyperparams']} | {r['framework']} |" for r in rows]
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
