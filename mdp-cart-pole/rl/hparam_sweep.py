"""
Parallel hyperparameter sweeps for any solution, headless.

Each (configuration, seed) pair is one job: train from scratch with the same
loop as main.py (full-range starts, best-checkpoint selection), then run the
frozen policy from a few start angles. Jobs run in a process pool, so a sweep
of 8 configurations x 2 seeds finishes in the time of the slowest job on a
machine with 16 cores.

    python hparam_sweep.py --soln 1999_qlearning_continuous --theta-limit 30 --episodes 4000 \\
        --seeds 0 1 --eval-angles 12 20 25 --workers 8 \\
        --config "hidden=64,advantage_k=0.3" \\
        --config "hidden=128,advantage_k=0.3,lr=0.005" \\
        --early-stop 1000:30

--config is repeatable; "" (empty) means the solution's defaults. Values are
Python literals. --early-stop EPISODE:AVG aborts a job whose 100-episode
average is still below AVG at EPISODE, which prunes hopeless configurations
early (a random policy averages ~22 steps). Results print as a table and can
be saved with --json.
"""

import argparse
import ast
import importlib
import json
import math
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from common import CartPoleEnv  # noqa: E402


def _split_top_level(text):
    """Split on commas that are not inside (), [] or {} so tuple-valued items survive."""
    items, depth, cur = [], 0, []
    for ch in text:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == "," and depth == 0:
            items.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    items.append("".join(cur))
    return items


def parse_config(text):
    """'hidden=64,advantage_k=0.3,bins=(1,1,4,8)' -> dict of Python literals; '' -> {}."""
    out = {}
    for item in filter(None, (t.strip() for t in _split_top_level(text))):
        key, _, raw = item.partition("=")
        if not _:
            raise ValueError(f"config item {item!r} is not KEY=VALUE")
        try:
            out[key.strip()] = ast.literal_eval(raw.strip())
        except (ValueError, SyntaxError):
            out[key.strip()] = raw.strip()
    return out


def run_job(job):
    """Train one configuration with one seed and evaluate it. Runs in a worker process."""
    t0 = time.time()
    mod = importlib.import_module(f"{job['soln']}.soln")
    hparams = job["hparams"]
    agent = mod.Agent(seed=job["seed"], **hparams)
    continuous = getattr(agent, "continuous_actions", False)
    env = CartPoleEnv(seed=job["seed"], continuous=continuous, theta_limit_deg=job["theta_limit"])
    start_rng = np.random.default_rng(job["seed"] + 1)
    rng_range = math.radians(job["theta_range"])

    returns, best, snap, best_ep, aborted = [], -np.inf, None, 0, False
    for ep in range(1, job["episodes"] + 1):
        obs, _ = env.reset(options={"theta0": start_rng.uniform(-rng_range, rng_range)})
        done, total = False, 0.0
        while not done:
            a = agent.act(obs)
            nxt, r, term, trunc, _ = env.step(a)
            done = term or trunc
            agent.learn(obs, a, r, nxt, term)
            obs = nxt
            total += r
        agent.end_episode()
        returns.append(total)
        if len(returns) >= 100:
            avg = float(np.mean(returns[-100:]))
            if avg > best:
                best, snap, best_ep = avg, agent.snapshot(), ep
        es = job["early_stop"]
        if es and ep == es[0] and best < es[1]:
            aborted = True
            break

    if snap is not None:
        agent.restore(snap)
    agent.freeze()
    eval_env = CartPoleEnv(seed=job["eval_seed"], continuous=continuous, theta_limit_deg=job["theta_limit"])
    evals = {}
    for deg in job["eval_angles"]:
        totals = []
        for sign in (1, -1):
            for _ in range(job["eval_episodes"]):
                obs, _ = eval_env.reset(options={"theta0": math.radians(sign * deg)})
                done, n = False, 0
                while not done:
                    obs, _, term, trunc, _ = eval_env.step(agent.act(obs))
                    done = term or trunc
                    n += 1
                totals.append(n)
        evals[str(deg)] = float(np.mean(totals))

    return {
        "soln": job["soln"], "hparams": hparams, "seed": job["seed"], "episodes_run": len(returns),
        "aborted": aborted, "best_avg100": float(best) if snap is not None else float("nan"),
        "best_episode": best_ep, "eval": evals, "seconds": round(time.time() - t0, 1),
    }


def sweep(soln, configs, seeds, episodes, theta_limit=12.0, theta_range=None, eval_angles=(0,),
          eval_episodes=5, eval_seed=99, early_stop=None, workers=None):
    """Run all configs x seeds in parallel. configs: list of dicts. Returns list of result dicts."""
    jobs = [
        dict(soln=soln, hparams=cfg, seed=seed, episodes=episodes, theta_limit=theta_limit,
             theta_range=theta_limit if theta_range is None else theta_range,
             eval_angles=list(eval_angles), eval_episodes=eval_episodes, eval_seed=eval_seed,
             early_stop=early_stop)
        for cfg in configs for seed in seeds
    ]
    workers = workers or max(1, min(len(jobs), (os.cpu_count() or 2) - 1))
    if workers == 1:
        return [run_job(j) for j in jobs]
    ctx = mp.get_context("spawn")  # portable; each worker re-imports the solution module
    with ctx.Pool(workers) as pool:
        return pool.map(run_job, jobs)


def format_table(results, eval_angles):
    cfg_width = max(8, max(len(json.dumps(r["hparams"])) for r in results))
    head = f"{'config':<{cfg_width}}  seed  {'best100':>7}  {'at ep':>5}  " + "  ".join(f"{a:>5}°" for a in eval_angles) + "   time"
    lines = [head, "-" * len(head)]
    for r in results:
        ev = "  ".join(f"{r['eval'][str(a)]:6.0f}" for a in eval_angles)
        flag = " (aborted)" if r["aborted"] else ""
        lines.append(f"{json.dumps(r['hparams']):<{cfg_width}}  {r['seed']:>4}  {r['best_avg100']:7.1f}  {r['best_episode']:>5}  {ev}  {r['seconds']:5.0f}s{flag}")
    return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(description="parallel hyperparameter sweep for one solution")
    p.add_argument("--soln", required=True)
    p.add_argument("--config", action="append", default=[], metavar="KEY=VALUE,...",
                   help="one configuration; repeatable; '' for the defaults")
    p.add_argument("--seeds", type=int, nargs="+", default=[0, 1])
    p.add_argument("--episodes", type=int, default=3000)
    p.add_argument("--theta-limit", type=float, default=12.0)
    p.add_argument("--theta-range", type=float, default=None, help="training start range (default: = --theta-limit)")
    p.add_argument("--eval-angles", type=float, nargs="+", default=[0.0])
    p.add_argument("--eval-episodes", type=int, default=5, help="per angle and sign")
    p.add_argument("--early-stop", default=None, metavar="EPISODE:AVG",
                   help="abort a job whose best 100-episode average is below AVG at EPISODE")
    p.add_argument("--workers", type=int, default=None, help="process count (default: cores - 1)")
    p.add_argument("--json", default=None, help="also write results to this file")
    args = p.parse_args(argv)

    configs = [parse_config(c) for c in (args.config or [""])]
    early = None
    if args.early_stop:
        ep, _, avg = args.early_stop.partition(":")
        early = (int(ep), float(avg))
    if args.theta_limit > 12 and not importlib.import_module(f"{args.soln}.soln").Agent.supports_wide_angles:
        p.error(f"{args.soln} does not support --theta-limit above 12")

    t0 = time.time()
    results = sweep(args.soln, configs, args.seeds, args.episodes, args.theta_limit, args.theta_range,
                    args.eval_angles, args.eval_episodes, early_stop=early, workers=args.workers)
    print(format_table(results, args.eval_angles))
    print(f"\n{len(results)} jobs in {time.time() - t0:.0f}s wall")
    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=1))
        print(f"wrote {args.json}")


if __name__ == "__main__":
    main()
