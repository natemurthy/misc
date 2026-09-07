"""
CartPole from the optimal-control side: run, tune or map the envelope of a controller.

Controllers live in subdirectories with a soln.py exposing `Agent`, like ../rl.
The environment and the live visualization are shared with ../rl/common.

    python main.py --mode run                            # default gains, renders every episode
    python main.py --mode run --theta-limit 45 --theta0 30 --x0 -1.0
    python main.py --mode run --gains 1 0.35 0.02 0.2 --no-render --episodes 20
    python main.py --mode tune                           # grid-search the gains, print the best
    python main.py --mode envelope                       # max recoverable angle vs start position
"""

import argparse
import importlib
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
RL_DIR = HERE.parent / "rl"
for d in (HERE, RL_DIR):
    if str(d) not in sys.path:
        sys.path.insert(0, str(d))

from common import CartPoleEnv  # noqa: E402
from common.render import Renderer, plt  # noqa: E402

CONTROLLERS = ["linear_controller"]


def load_controller(name):
    return importlib.import_module(f"{name}.soln")


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="CartPole with classical controllers (see ../rl for the learning side)")
    p.add_argument("--mode", choices=["run", "tune", "envelope"], default="run",
                   help="run: play episodes with fixed gains; tune: grid-search the gains for the widest "
                        "recovery; envelope: max recoverable angle vs. cart start position")
    p.add_argument("--ctrl", choices=CONTROLLERS, default="linear_controller")
    p.add_argument("--gains", type=float, nargs=4, default=None, metavar=("K_THETA", "K_THETADOT", "K_X", "K_XDOT"),
                   help="feedback gains; default: the tuned values in the controller's soln.py")
    p.add_argument("--episodes", type=int, default=10)
    p.add_argument("--render-every", type=int, default=1)
    p.add_argument("--fps", type=float, default=50.0)
    p.add_argument("--no-render", action="store_true")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--theta-limit", type=float, default=12.0, metavar="DEGREES",
                   help="absolute pole angle at which an episode terminates (default 12; a controller "
                        "can be asked to recover from wider angles, up to the ~34 degree track envelope)")
    p.add_argument("--x0", type=float, default=None, metavar="METERS",
                   help="initial cart position, -2.4 < x0 < 2.4 (default: random in [-0.05, 0.05])")
    p.add_argument("--theta0", type=float, default=None, metavar="DEGREES",
                   help="initial pole angle, strictly inside +/- --theta-limit (default: random in about [-2.9, 2.9])")
    args = p.parse_args(argv)
    if not args.theta_limit > 0:
        p.error(f"--theta-limit={args.theta_limit} must be positive")
    if args.x0 is not None and abs(args.x0) >= CartPoleEnv.x_threshold:
        p.error(f"--x0={args.x0} is outside the track (-2.4, 2.4)")
    if args.theta0 is not None and abs(args.theta0) >= args.theta_limit:
        p.error(f"--theta0={args.theta0} would terminate immediately; must be inside +/-{args.theta_limit} degrees")
    return args


def run_episodes(args, ctrl, env, renderer=None):
    frame_dt = 1.0 / args.fps
    theta0 = math.radians(args.theta0) if args.theta0 is not None else None
    totals = []
    for episode in range(1, args.episodes + 1):
        render = renderer is not None and (episode % args.render_every == 0 or episode == 1)
        obs, _ = env.reset(options={"x0": args.x0, "theta0": theta0})
        done, steps, terminated = False, 0, False
        while not done:
            obs, _, terminated, truncated, _ = env.step(ctrl.act(obs))
            done = terminated or truncated
            steps += 1
            if render:
                if not renderer.is_open():
                    return totals
                renderer.draw_frame(obs, episode, steps, {"u": ctrl.feedback(obs)})
                plt.pause(frame_dt)
        totals.append(steps)
        if terminated:
            cause = "pole angle" if abs(obs[2]) > env.theta_threshold_radians else "track"
        else:
            cause = "reached the 500-step limit"
        print(f"episode {episode:3d} | steps {steps:3d} | {cause}")
        if renderer is not None:
            renderer.update_curve(totals)
    return totals


def main(argv=None):
    args = parse_args(argv)
    mod = load_controller(args.ctrl)
    gains = tuple(args.gains) if args.gains is not None else mod.DEFAULT_GAINS

    if args.mode == "tune":
        print("grid-searching gains for the widest recovery from rest at the track center ...")
        best, angle = mod.tune(verbose=True)
        print(f"\nbest gains (k_theta, k_thetadot, k_x, k_xdot) = {best}: recovers from up to {angle:.1f} deg")
        return
    if args.mode == "envelope":
        print(f"gains {gains}: largest start angle recovered from, at rest, by cart start position")
        for x0 in (-2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0):
            print(f"  x0 = {x0:+.1f} m : {mod.max_recoverable_angle(gains, x0):5.1f} deg  (pole leaning right)")
        return

    ctrl = mod.Agent(gains, seed=args.seed)
    env = CartPoleEnv(seed=args.seed, theta_limit_deg=args.theta_limit)
    print(f"[{args.ctrl}] gains {tuple(float(g) for g in ctrl.gains)}, theta limit {args.theta_limit} deg, {args.episodes} episodes")
    renderer = None if args.no_render else Renderer(env, title=f"CartPole OC [{args.ctrl}] — fixed gains, no learning")
    totals = run_episodes(args, ctrl, env, renderer)
    if totals:
        print(f"\nmean steps {np.mean(totals):.1f} over {len(totals)} episodes; {sum(t >= 500 for t in totals)} reached the cap")
    env.close()
    if renderer is not None and renderer.is_open():
        plt.ioff()
        print("close the window to exit")
        plt.show()


if __name__ == "__main__":
    main()
