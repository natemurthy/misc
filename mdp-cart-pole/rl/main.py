"""
CartPole RL simulator with live visualization: one MDP, six historical solutions.

The environment (common/env.py) matches Gymnasium's CartPole-v1. The learner is
chosen with --soln from the numbered directories, each of which holds a soln.py
implementing one approach from the reinforcement-learning lineage:

    1983_actor_critic            Barto, Sutton & Anderson: ASE/ACE on BOXES
    1986_actor_critic_backprop   Anderson: actor-critic with backprop networks
    1988_td                      Sutton: TD(lambda) value learning + lookahead
    1989_qlearning               Watkins: tabular Q-learning            (default)
    1990_dyna                    Sutton: Dyna-Q, learning + planning
    1992_reinforce               Williams: REINFORCE policy gradient

Only numpy, matplotlib and tqdm are required.

Usage:
    # Training: learn a policy, save the best checkpoint to disk when done.
    # Each training episode starts with the pole at a random angle anywhere in
    # the full +/-12 degree range so the agent learns to recover, not just balance.
    python main.py --mode train                              # Q-learning, renders every 100th episode
    python main.py --mode train --soln 1983_actor_critic     # a different solution
    python main.py --mode train --no-render                  # fastest
    python main.py --mode train --theta-range 3              # narrow starts, like Gymnasium
    python main.py --mode train --model my_policy.npz

    # Inference: load a saved policy, run it deterministically with no learning
    python main.py --mode infer                              # renders every episode
    python main.py --mode infer --soln 1992_reinforce --episodes 5
    python main.py --mode infer --x0 1.5 --theta0 -8         # start off-center, pole tilted 8 deg left

    # Baseline
    python main.py --mode infer --agent random
"""

import argparse
import importlib
import math
import sys
from pathlib import Path

import numpy as np
from tqdm import tqdm

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from common import CartPoleEnv, RandomAgent  # noqa: E402
from common.render import Renderer, plt  # noqa: E402  (chooses the matplotlib backend)

SOLUTIONS = [
    "1983_actor_critic",
    "1986_actor_critic_backprop",
    "1988_td",
    "1989_qlearning",
    "1990_dyna",
    "1992_reinforce",
]
DEFAULT_SOLUTION = "1989_qlearning"


def load_solution(name):
    """Import <name>/soln.py and return its module. Exposes module.Agent."""
    if name not in SOLUTIONS:
        raise ValueError(f"unknown solution {name!r}; choose from {SOLUTIONS}")
    return importlib.import_module(f"{name}.soln")


# Backward-compatible names for code that imported them from the original
# single-file main.py (gym/main.py loads this module by path and uses these).
QLearningAgent = load_solution("1989_qlearning").QLearningAgent


# --------------------------------------------------------------------------- #
# CLI                                                                         #
# --------------------------------------------------------------------------- #
def parse_args(argv=None):
    p = argparse.ArgumentParser(description="CartPole RL simulator with live visualization")
    p.add_argument(
        "--mode", choices=["train", "infer"], default="train",
        help="train: learn and save a policy; infer: load a saved policy and run it deterministically",
    )
    p.add_argument(
        "--soln", choices=SOLUTIONS, default=DEFAULT_SOLUTION,
        help=f"which solution directory's soln.py to use (default: {DEFAULT_SOLUTION})",
    )
    p.add_argument(
        "--agent", choices=["soln", "qlearning", "random"], default="soln",
        help="soln: the learner selected by --soln (default); qlearning: alias that forces "
             "--soln 1989_qlearning; random: uniform random baseline, does not learn",
    )
    p.add_argument("--model", default=None,
                   help="path to save/load the learned parameters (default: cartpole_<soln>.npz)")
    p.add_argument("--episodes", type=int, default=None,
                   help="number of episodes (default: 5000 for train, 10 for infer)")
    p.add_argument("--render-every", type=int, default=None,
                   help="render every Nth episode (default: 100 for train, 1 for infer)")
    p.add_argument(
        "--theta-range", type=float, default=12.0, metavar="DEGREES",
        help="[train only] each training episode starts with the pole at a uniformly random "
             "angle in [-DEGREES, +DEGREES]. Valid range: 0 <= DEGREES <= 12. Default 12, the "
             "full recoverable range. Gymnasium's default start corresponds to about 2.9.",
    )
    p.add_argument("--fps", type=float, default=50.0, help="frames per second when rendering")
    p.add_argument("--no-render", action="store_true")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument(
        "--x0", type=float, default=None, metavar="METERS",
        help="[infer only] initial cart position in meters. Valid range: -2.4 < x0 < 2.4 "
             "(0 is the center of the track, negative is left, positive is right; the episode "
             "terminates when |x| reaches 2.4). Default: random in [-0.05, 0.05].",
    )
    p.add_argument(
        "--theta0", type=float, default=None, metavar="DEGREES",
        help="[infer only] initial pole angle in degrees. Valid range: -12 < theta0 < 12 "
             "(0 is upright, negative tilts left, positive tilts right; the episode terminates "
             "when |theta| reaches 12). Default: random in about [-2.9, 2.9].",
    )
    p.epilog = (
        "initial-state notes (infer mode): the cart starts on a track spanning -2.4 m to 2.4 m "
        "and the pole must stay within 12 degrees of upright, so --x0 and --theta0 must lie "
        "strictly inside those limits or the episode would end on step 0. Initial velocities "
        "are always drawn uniformly from [-0.05, 0.05]. Without these flags, position and angle "
        "are also drawn from [-0.05, 0.05] (in meters and radians respectively), as in Gymnasium. "
        "In train mode the start angle is instead drawn uniformly from +/- --theta-range degrees."
    )
    args = p.parse_args(argv)

    if args.agent == "qlearning":
        args.soln = "1989_qlearning"
    if args.model is None:
        args.model = f"cartpole_{args.soln}.npz"
    if args.mode == "train" and (args.x0 is not None or args.theta0 is not None):
        p.error("--x0/--theta0 are only valid with --mode infer")
    if not 0 <= args.theta_range <= 12:
        p.error(f"--theta-range={args.theta_range} invalid; valid range is 0 <= theta-range <= 12 degrees")
    if args.x0 is not None and abs(args.x0) >= CartPoleEnv.x_threshold:
        p.error(f"--x0={args.x0} is outside the track; valid range is "
                f"-{CartPoleEnv.x_threshold} < x0 < {CartPoleEnv.x_threshold} meters")
    if args.theta0 is not None and abs(math.radians(args.theta0)) >= CartPoleEnv.theta_threshold_radians:
        p.error(f"--theta0={args.theta0} would terminate immediately; valid range is "
                f"-12 < theta0 < 12 degrees (0 = upright)")

    training = args.mode == "train"
    if args.episodes is None:
        args.episodes = 5000 if training else 10
    if args.render_every is None:
        args.render_every = 100 if training else 1
    return args


# --------------------------------------------------------------------------- #
# Train / infer loop, shared by every solution                                #
# --------------------------------------------------------------------------- #
def make_agent(args):
    training = args.mode == "train"
    if args.agent == "random":
        if training:
            print("note: random agent does not learn; nothing will be saved")
        return RandomAgent(seed=args.seed)
    AgentCls = load_solution(args.soln).Agent
    if training:
        return AgentCls(seed=args.seed)
    try:
        agent = AgentCls.load(args.model, seed=args.seed)
    except FileNotFoundError:
        sys.exit(f"no saved model at {args.model}; run with --mode train --soln {args.soln} first")
    agent.freeze()
    print(f"[infer] {args.soln}: loaded {args.model}; {args.episodes} deterministic episodes, no learning")
    return agent


def run(args, env, agent, renderer=None):
    """Run args.episodes episodes. Returns (returns, best_snapshot, best_avg, best_episode)."""
    training = args.mode == "train"
    learner = training and not isinstance(agent, RandomAgent)
    frame_dt = 1.0 / args.fps
    theta0_rad = math.radians(args.theta0) if args.theta0 is not None else None
    start_rng = np.random.default_rng(args.seed + 1)
    theta_range_rad = math.radians(args.theta_range)

    returns = []
    best_avg, best_snap, best_episode = -np.inf, None, 0
    pbar = tqdm(total=args.episodes, desc=f"train {args.soln}", unit="ep", dynamic_ncols=True) if training else None
    try:
        for episode in range(1, args.episodes + 1):
            render = renderer is not None and (episode % args.render_every == 0 or episode == 1)
            if training:
                # Start anywhere in the recoverable range so the agent learns to recover.
                theta0_rad = start_rng.uniform(-theta_range_rad, theta_range_rad)
            obs, _ = env.reset(options={"x0": args.x0, "theta0": theta0_rad})
            total = 0.0
            done = False
            step = 0
            while not done:
                action = agent.act(obs)
                next_obs, reward, terminated, truncated, _ = env.step(action)
                done = terminated or truncated
                agent.learn(obs, action, reward, next_obs, terminated)
                obs = next_obs
                total += reward
                step += 1
                if render:
                    if not renderer.is_open():
                        raise KeyboardInterrupt
                    renderer.draw_frame(obs, episode, step, agent.stats())
                    plt.pause(frame_dt)
            agent.end_episode()
            returns.append(total)
            if learner and len(returns) >= 100:
                avg = np.mean(returns[-100:])
                if avg > best_avg:
                    best_avg, best_snap, best_episode = avg, agent.snapshot(), episode

            if renderer is not None:
                if not renderer.is_open():
                    break
                renderer.update_curve(returns)
            if pbar is not None:
                pbar.update(1)
                postfix = {"reward": f"{total:.0f}", "avg100": f"{np.mean(returns[-100:]):.1f}",
                           "best": f"{best_avg:.1f}" if best_snap is not None else "-"}
                postfix.update({k: f"{v:.3f}" for k, v in agent.stats().items()})
                pbar.set_postfix(postfix)
            elif episode % 10 == 0 or render:
                print(f"episode {episode:4d} | total reward {total:5.0f} | avg100 {np.mean(returns[-100:]):6.1f}")
    except KeyboardInterrupt:
        if pbar is not None:
            pbar.close()
        print("\ninterrupted")
    if pbar is not None:
        pbar.close()
    return returns, best_snap, best_avg, best_episode


def main(argv=None):
    args = parse_args(argv)
    training = args.mode == "train"
    env = CartPoleEnv(seed=args.seed)
    agent = make_agent(args)
    label = args.soln if args.agent != "random" else "random baseline"
    renderer = None if args.no_render else Renderer(
        env, title=f"CartPole RL [{label}] — {'TRAINING' if training else 'INFERENCE (deterministic, frozen policy)'}"
    )

    returns, best_snap, best_avg, best_episode = run(args, env, agent, renderer)

    if returns:
        print(f"\n[{args.mode}] {label}: ran {len(returns)} episodes, best episode reward {max(returns):.0f}, "
              f"mean {np.mean(returns):.1f}, final avg100 {np.mean(returns[-100:]):.1f}")
    if training and not isinstance(agent, RandomAgent) and returns:
        if best_snap is not None:
            agent.restore(best_snap)
            print(f"checkpoint: best avg100 = {best_avg:.1f} at episode {best_episode}")
        agent.save(args.model)
        print(f"saved {args.soln} parameters to {args.model}")
    env.close()
    if renderer is not None and renderer.is_open():
        plt.ioff()
        print("close the window to exit")
        plt.show()


if __name__ == "__main__":
    main()
