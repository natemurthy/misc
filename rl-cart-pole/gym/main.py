"""
CartPole RL simulator, Gymnasium edition.

Same problem, same tabular Q-learning agent and same CLI as ../main.py, but the
environment comes from Farama's Gymnasium instead of being hand-written:

  * physics, spaces, reward and termination:  gymnasium's CartPole-v1
  * 500-step truncation:                      TimeLimit wrapper (via gym.make)
  * per-episode return bookkeeping:            RecordEpisodeStatistics wrapper
  * simulation frames:                         env.render() with render_mode="rgb_array"
  * MP4 recording:                             RecordVideo wrapper (--record-video)
  * wide-angle start distribution:             CartPoleFullRange-v0 in cartpole_env.py

The agent is imported unchanged from the parent directory to make the point
that Gymnasium touches only the environment side of the loop.

Usage:
    python main.py --mode train                        # renders every 100th episode
    python main.py --mode train --no-render
    python main.py --mode infer --theta0 -11
    python main.py --mode infer --record-video videos  # write MP4s instead of watching
    python main.py --mode infer --agent random
"""

import argparse
import importlib.util
import math
import pathlib
import sys

import gymnasium as gym
import numpy as np
from gymnasium.wrappers import RecordEpisodeStatistics, RecordVideo
from tqdm import tqdm

import cartpole_env  # noqa: F401  (import registers CartPoleFullRange-v0)

# --------------------------------------------------------------------------- #
# Reuse the agents from ../main.py without turning the repo into a package.   #
# --------------------------------------------------------------------------- #
_PARENT = pathlib.Path(__file__).resolve().parent.parent / "main.py"
_spec = importlib.util.spec_from_file_location("tabular_cartpole", _PARENT)
tabular = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tabular)
QLearningAgent, RandomAgent = tabular.QLearningAgent, tabular.RandomAgent

import matplotlib.pyplot as plt  # noqa: E402  (parent module has chosen the backend)


# --------------------------------------------------------------------------- #
# Visualization: Gymnasium's frame on top, learning curve below               #
# --------------------------------------------------------------------------- #
class FrameRenderer:
    """Shows env.render() RGB frames in matplotlib alongside the learning curve."""

    def __init__(self, title, max_return):
        plt.ion()
        self.fig, (self.ax_img, self.ax_curve) = plt.subplots(
            2, 1, figsize=(8, 7.5), gridspec_kw={"height_ratios": [2, 1]}
        )
        self.fig.canvas.manager.set_window_title(title)
        self.fig.suptitle(title, fontsize=12)

        self.ax_img.set_axis_off()
        self.img = None
        self.text = self.ax_img.text(
            0.02, 0.97, "", transform=self.ax_img.transAxes, va="top", family="monospace", fontsize=9
        )

        self.ax_curve.set_xlabel("episode")
        self.ax_curve.set_ylabel("Total reward per episode (= steps survived)")
        self.ax_curve.set_ylim(0, max_return + 10)
        self.ax_curve.grid(alpha=0.3)
        (self.curve,) = self.ax_curve.plot([], [], color="#aaaaaa", lw=1, label="total reward")
        (self.avg_curve,) = self.ax_curve.plot([], [], color="#3b6ea5", lw=2, label="100-ep avg")
        self.ax_curve.legend(loc="upper left")
        self.fig.tight_layout()
        self.fig.show()

    def draw_frame(self, frame, obs, episode, step, epsilon):
        if self.img is None:
            self.img = self.ax_img.imshow(frame)
        else:
            self.img.set_data(frame)
        x, x_dot, theta, theta_dot = obs
        self.text.set_text(
            f"episode {episode:4d}  step {step:3d}  eps {epsilon:.3f}\n"
            f"x={x:+.3f}  x_dot={x_dot:+.3f}\n"
            f"theta={math.degrees(theta):+.2f} deg  theta_dot={theta_dot:+.3f}"
        )
        self._flush()

    def update_curve(self, returns):
        ep = np.arange(1, len(returns) + 1)
        self.curve.set_data(ep, returns)
        avg = [np.mean(returns[max(0, i - 99) : i + 1]) for i in range(len(returns))]
        self.avg_curve.set_data(ep, avg)
        self.ax_curve.set_xlim(0, max(10, len(returns)))
        self._flush()

    def _flush(self):
        self.fig.canvas.draw_idle()
        self.fig.canvas.flush_events()
        plt.pause(0.001)

    def is_open(self):
        return plt.fignum_exists(self.fig.number)


# --------------------------------------------------------------------------- #
# Main                                                                        #
# --------------------------------------------------------------------------- #
def parse_args():
    p = argparse.ArgumentParser(
        description="CartPole RL simulator built on Gymnasium (see ../main.py for the dependency-free version)"
    )
    p.add_argument("--mode", choices=["train", "infer"], default="train",
                   help="train: learn and save a policy; infer: load a saved policy and run it greedily")
    p.add_argument("--agent", choices=["qlearning", "random"], default="qlearning")
    p.add_argument("--model", default="cartpole_q_gym.npz", help="path to save/load the Q-table")
    p.add_argument("--episodes", type=int, default=None,
                   help="number of episodes (default: 5000 for train, 10 for infer)")
    p.add_argument("--render-every", type=int, default=None,
                   help="render (and record, if --record-video) every Nth episode "
                        "(default: 100 for train, 1 for infer)")
    p.add_argument("--theta-range", type=float, default=12.0, metavar="DEGREES",
                   help="[train only] start each episode with the pole at a uniform random angle in "
                        "[-DEGREES, +DEGREES]. Valid range 0 <= DEGREES <= 12. Default 12.")
    p.add_argument("--fps", type=float, default=50.0, help="frames per second when rendering live")
    p.add_argument("--no-render", action="store_true", help="no live window (recording still works)")
    p.add_argument("--record-video", metavar="DIR", default=None,
                   help="write an MP4 of every rendered episode to DIR using gymnasium's RecordVideo")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--x0", type=float, default=None, metavar="METERS",
                   help="[infer only] initial cart position. Valid range -2.4 < x0 < 2.4 "
                        "(0 = track center, negative = left). Default: random in [-0.05, 0.05].")
    p.add_argument("--theta0", type=float, default=None, metavar="DEGREES",
                   help="[infer only] initial pole angle. Valid range -12 < theta0 < 12 "
                        "(0 = upright, negative = tilted left). Default: random in about [-2.9, 2.9].")
    args = p.parse_args()

    if args.mode == "train" and (args.x0 is not None or args.theta0 is not None):
        p.error("--x0/--theta0 are only valid with --mode infer")
    if not 0 <= args.theta_range <= 12:
        p.error(f"--theta-range={args.theta_range} invalid; valid range is 0 <= theta-range <= 12 degrees")
    if args.x0 is not None and abs(args.x0) >= 2.4:
        p.error(f"--x0={args.x0} is outside the track; valid range is -2.4 < x0 < 2.4 meters")
    if args.theta0 is not None and abs(args.theta0) >= 12:
        p.error(f"--theta0={args.theta0} would terminate immediately; valid range is -12 < theta0 < 12 degrees")

    training = args.mode == "train"
    if args.episodes is None:
        args.episodes = 5000 if training else 10
    if args.render_every is None:
        args.render_every = 100 if training else 1
    return args


def main():
    args = parse_args()
    training = args.mode == "train"
    live = not args.no_render
    need_frames = live or args.record_video is not None

    # ---- environment: gym.make + wrappers -------------------------------- #
    env = gym.make(
        "CartPoleFullRange-v0",
        render_mode="rgb_array" if need_frames else None,
        theta_range=math.radians(args.theta_range) if training else 0.0,
    )
    env = RecordEpisodeStatistics(env)  # adds info["episode"]["r"] / ["l"] at episode end
    if args.record_video is not None:
        env = RecordVideo(
            env,
            video_folder=args.record_video,
            episode_trigger=lambda ep: (ep + 1) % args.render_every == 0 or ep == 0,
            name_prefix=f"cartpole-{args.mode}",
        )
    max_steps = env.spec.max_episode_steps

    # ---- agent ------------------------------------------------------------ #
    if args.agent == "random":
        agent = RandomAgent(seed=args.seed)
        if training:
            print("note: random agent does not learn; nothing will be saved")
    elif training:
        agent = QLearningAgent(seed=args.seed)
    else:
        try:
            agent = QLearningAgent.load(args.model, seed=args.seed)
        except FileNotFoundError:
            sys.exit(f"no saved model at {args.model}; run with --mode train first")
        agent.freeze()
        print(f"[infer] loaded {args.model}; {args.episodes} greedy episodes, no learning")

    title = f"CartPole RL (Gymnasium) — {'TRAINING' if training else 'INFERENCE (greedy, frozen policy)'}"
    renderer = FrameRenderer(title, max_steps) if live else None
    frame_dt = 1.0 / args.fps
    reset_options = {"x0": args.x0, "theta0": math.radians(args.theta0) if args.theta0 is not None else None}

    returns = []
    best_avg, best_q, best_episode = -np.inf, None, 0
    pbar = tqdm(total=args.episodes, desc="train", unit="ep", dynamic_ncols=True) if training else None
    try:
        for episode in range(1, args.episodes + 1):
            render = live and (episode % args.render_every == 0 or episode == 1)
            obs, info = env.reset(seed=args.seed if episode == 1 else None, options=reset_options)
            done = False
            step = 0
            while not done:
                action = agent.act(obs)
                next_obs, reward, terminated, truncated, info = env.step(action)
                done = terminated or truncated
                agent.learn(obs, action, reward, next_obs, terminated)
                obs = next_obs
                step += 1
                if render:
                    if not renderer.is_open():
                        raise KeyboardInterrupt
                    renderer.draw_frame(env.render(), obs, episode, step, getattr(agent, "epsilon", 0.0))
                    plt.pause(frame_dt)
            agent.end_episode()
            total = float(info["episode"]["r"])  # from RecordEpisodeStatistics
            returns.append(total)
            if training and isinstance(agent, QLearningAgent) and len(returns) >= 100:
                avg = np.mean(returns[-100:])
                if avg > best_avg:
                    best_avg, best_q, best_episode = avg, agent.q.copy(), episode

            if renderer is not None:
                if not renderer.is_open():
                    break
                renderer.update_curve(returns)
            if pbar is not None:
                pbar.update(1)
                pbar.set_postfix(
                    reward=f"{total:.0f}",
                    avg100=f"{np.mean(returns[-100:]):.1f}",
                    best=f"{best_avg:.1f}" if best_q is not None else "-",
                    eps=f"{getattr(agent, 'epsilon', 0.0):.3f}",
                )
            elif episode % 10 == 0 or render:
                print(f"episode {episode:4d} | total reward {total:5.0f} | avg100 {np.mean(returns[-100:]):6.1f}")
    except KeyboardInterrupt:
        if pbar is not None:
            pbar.close()
        print("\ninterrupted")
    if pbar is not None:
        pbar.close()
    env.close()  # flushes any in-progress video

    if returns:
        print(f"\n[{args.mode}] ran {len(returns)} episodes, best episode reward {max(returns):.0f}, "
              f"mean {np.mean(returns):.1f}, final avg100 {np.mean(returns[-100:]):.1f}")
    if training and isinstance(agent, QLearningAgent) and returns:
        if best_q is not None:
            agent.q = best_q
            print(f"checkpoint: best avg100 = {best_avg:.1f} at episode {best_episode}")
        agent.save(args.model)
        print(f"saved Q-table to {args.model}")
    if args.record_video is not None:
        print(f"videos written to {args.record_video}/")
    if renderer is not None and renderer.is_open():
        plt.ioff()
        print("close the window to exit")
        plt.show()


if __name__ == "__main__":
    main()
