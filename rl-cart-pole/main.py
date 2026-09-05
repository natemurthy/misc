"""
Simple CartPole RL simulator with live visualization.

Physics, observation space, action space, rewards and termination rules match
Gymnasium's CartPole-v1:
    https://gymnasium.farama.org/environments/classic_control/cart_pole/

Only numpy, matplotlib and tqdm are required.

Usage:
    # Training: learn a policy, save the best Q-table to disk when done.
    # Each training episode starts with the pole at a random angle anywhere in
    # the full +/-12 degree range so the agent learns to recover, not just balance.
    python main.py --mode train                          # renders every 100th episode
    python main.py --mode train --no-render              # fastest (~15 s for 5000 episodes)
    python main.py --mode train --theta-range 3          # narrow starts, like Gymnasium
    python main.py --mode train --model my_policy.npz

    # Inference: load a saved Q-table, run greedily with no exploration/learning
    python main.py --mode infer                          # renders every episode
    python main.py --mode infer --episodes 5 --model my_policy.npz
    python main.py --mode infer --x0 1.5 --theta0 -8    # start off-center, pole tilted 8 deg left

    # Baseline
    python main.py --mode infer --agent random
"""

import argparse
import math
import sys

import numpy as np
import matplotlib
from tqdm import tqdm

# Use an interactive backend if available; fall back gracefully.
try:
    matplotlib.use("MacOSX" if sys.platform == "darwin" else "TkAgg")
except Exception:
    pass
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


# --------------------------------------------------------------------------- #
# Environment                                                                 #
# --------------------------------------------------------------------------- #
class CartPoleEnv:
    """
    Re-implementation of Gymnasium's CartPole-v1 that follows the Gymnasium
    Env API without importing the library:

        obs, info = env.reset(seed=None, options=None)
        obs, reward, terminated, truncated, info = env.step(action)

    Observation: float32 [x, x_dot, theta, theta_dot]
    Action:      0 = push cart left, 1 = push cart right
    Reward:      +1 for every step taken (including the terminating step)
    Terminated:  |theta| > 12 deg  or  |x| > 2.4
    Truncated:   episode length reaches 500 (Gymnasium does this with a
                 TimeLimit wrapper; here it is built in)

    reset() accepts options={"x0": meters, "theta0": radians} to override the
    initial cart position and pole angle. See gym/ for the same
    problem written against the real library.
    """

    gravity = 9.8
    masscart = 1.0
    masspole = 0.1
    total_mass = masspole + masscart
    length = 0.5  # actually half the pole's length
    polemass_length = masspole * length
    force_mag = 10.0
    tau = 0.02  # seconds between state updates

    theta_threshold_radians = 12 * 2 * math.pi / 360
    x_threshold = 2.4
    max_episode_steps = 500

    # Stand-ins for gymnasium.spaces.Discrete(2) and spaces.Box(-high, high).
    # Gymnasium uses 2x the thresholds for the observation bounds so that a
    # terminal observation is still inside the box.
    n_actions = 2
    observation_high = np.array(
        [x_threshold * 2, np.finfo(np.float32).max, theta_threshold_radians * 2, np.finfo(np.float32).max],
        dtype=np.float32,
    )
    metadata = {"render_modes": []}

    def __init__(self, seed=None, render_mode=None):
        self.rng = np.random.default_rng(seed)
        self.render_mode = render_mode
        self.state = None
        self.steps = 0

    def _obs(self):
        return np.array(self.state, dtype=np.float32)

    def reset(self, *, seed=None, options=None):
        """
        Reset to a random state and return (obs, info), as in Gymnasium.

        seed:    reseeds the environment's RNG if given.
        options: optional dict. "x0" (meters) and "theta0" (radians) override
                 the cart position and pole angle; all other state variables
                 are drawn uniformly from [-0.05, 0.05] as in Gymnasium.
        """
        if seed is not None:
            self.rng = np.random.default_rng(seed)
        options = options or {}
        self.state = self.rng.uniform(low=-0.05, high=0.05, size=(4,))
        if options.get("x0") is not None:
            self.state[0] = options["x0"]
        if options.get("theta0") is not None:
            self.state[2] = options["theta0"]
        self.steps = 0
        return self._obs(), {}

    def step(self, action):
        """Advance one step and return (obs, reward, terminated, truncated, info)."""
        assert action in (0, 1), f"invalid action {action}"
        x, x_dot, theta, theta_dot = self.state
        force = self.force_mag if action == 1 else -self.force_mag
        costheta = math.cos(theta)
        sintheta = math.sin(theta)

        # Equations of motion (Barto, Sutton & Anderson 1983), Euler integration
        temp = (force + self.polemass_length * theta_dot**2 * sintheta) / self.total_mass
        thetaacc = (self.gravity * sintheta - costheta * temp) / (
            self.length * (4.0 / 3.0 - self.masspole * costheta**2 / self.total_mass)
        )
        xacc = temp - self.polemass_length * thetaacc * costheta / self.total_mass

        x = x + self.tau * x_dot
        x_dot = x_dot + self.tau * xacc
        theta = theta + self.tau * theta_dot
        theta_dot = theta_dot + self.tau * thetaacc

        self.state = np.array([x, x_dot, theta, theta_dot], dtype=np.float64)
        self.steps += 1

        terminated = bool(
            x < -self.x_threshold
            or x > self.x_threshold
            or theta < -self.theta_threshold_radians
            or theta > self.theta_threshold_radians
        )
        truncated = self.steps >= self.max_episode_steps
        reward = 1.0
        return self._obs(), reward, terminated, truncated, {}

    def close(self):
        pass


# --------------------------------------------------------------------------- #
# Agents                                                                      #
# --------------------------------------------------------------------------- #
class RandomAgent:
    def __init__(self, seed=None):
        self.rng = np.random.default_rng(seed)

    def act(self, obs):
        return int(self.rng.integers(2))

    def learn(self, obs, action, reward, next_obs, done):
        pass

    def end_episode(self):
        pass


class QLearningAgent:
    """Tabular Q-learning over a discretized state space."""

    def __init__(
        self,
        bins=(1, 1, 8, 16),  # ignore x/x_dot; pole angle + angular velocity are what matter
        alpha=0.1,
        gamma=0.99,
        epsilon=1.0,
        epsilon_min=0.01,
        epsilon_decay=0.999,
        seed=None,
    ):
        self.bins = bins
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.rng = np.random.default_rng(seed)

        # Clip velocities to a sensible range so the bins stay meaningful.
        self.lows = np.array([-2.4, -3.0, -0.21, -3.5])
        self.highs = np.array([2.4, 3.0, 0.21, 3.5])
        self.q = np.zeros(tuple(bins) + (2,))

    def discretize(self, obs):
        ratios = (np.clip(obs, self.lows, self.highs) - self.lows) / (self.highs - self.lows)
        idx = (ratios * (np.array(self.bins) - 1)).round().astype(int)
        return tuple(idx)

    def act(self, obs):
        if self.rng.random() < self.epsilon:
            return int(self.rng.integers(2))
        q = self.q[self.discretize(obs)]
        if q[0] == q[1]:  # break ties randomly so unvisited states carry no left/right bias
            return int(self.rng.integers(2))
        return int(np.argmax(q))

    def learn(self, obs, action, reward, next_obs, done):
        s, s_next = self.discretize(obs), self.discretize(next_obs)
        target = reward if done else reward + self.gamma * np.max(self.q[s_next])
        self.q[s + (action,)] += self.alpha * (target - self.q[s + (action,)])

    def end_episode(self):
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def save(self, path):
        np.savez(
            path,
            q=self.q,
            bins=np.array(self.bins),
            lows=self.lows,
            highs=self.highs,
            epsilon=self.epsilon,
        )

    @classmethod
    def load(cls, path, seed=None):
        data = np.load(path)
        agent = cls(bins=tuple(int(b) for b in data["bins"]), seed=seed)
        agent.q = data["q"]
        agent.lows = data["lows"]
        agent.highs = data["highs"]
        return agent

    def freeze(self):
        """Switch to pure inference: greedy policy, no exploration, no updates."""
        self.epsilon = 0.0
        self.epsilon_min = 0.0
        self.learn = lambda *args, **kwargs: None
        self.end_episode = lambda: None


# --------------------------------------------------------------------------- #
# Visualization                                                               #
# --------------------------------------------------------------------------- #
class Renderer:
    """Live matplotlib view: cart/pole on top, episode returns on the bottom."""

    def __init__(self, env, title="CartPole RL"):
        self.env = env
        plt.ion()
        self.fig, (self.ax_sim, self.ax_curve) = plt.subplots(
            2, 1, figsize=(8, 7), gridspec_kw={"height_ratios": [2, 1]}
        )
        self.fig.canvas.manager.set_window_title(title)
        self.fig.suptitle(title, fontsize=12)

        # --- simulation panel ---
        ax = self.ax_sim
        ax.set_xlim(-env.x_threshold - 0.6, env.x_threshold + 0.6)
        ax.set_ylim(-0.5, 1.6)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)
        ax.axhline(0, color="#888888", lw=1)  # track
        for xb in (-env.x_threshold, env.x_threshold):
            ax.axvline(xb, color="#cc4444", lw=1, ls="--")  # boundaries

        self.cart_w, self.cart_h = 0.5, 0.3
        self.cart = Rectangle((0, 0), self.cart_w, self.cart_h, color="#3b6ea5")
        ax.add_patch(self.cart)
        (self.pole,) = ax.plot([], [], color="#d38b2c", lw=6, solid_capstyle="round")
        (self.axle,) = ax.plot([], [], "o", color="#222222", ms=5)
        self.text = ax.text(
            0.02, 0.95, "", transform=ax.transAxes, va="top", family="monospace", fontsize=9
        )

        # --- learning-curve panel ---
        self.ax_curve.set_xlabel("episode")
        self.ax_curve.set_ylabel("Total reward per episode (= steps survived)")
        self.ax_curve.set_ylim(0, env.max_episode_steps + 10)
        self.ax_curve.grid(alpha=0.3)
        (self.curve,) = self.ax_curve.plot([], [], color="#aaaaaa", lw=1, label="total reward")
        (self.avg_curve,) = self.ax_curve.plot([], [], color="#3b6ea5", lw=2, label="100-ep avg")
        self.ax_curve.legend(loc="upper left")

        self.fig.tight_layout()
        self.fig.show()

    def draw_frame(self, obs, episode, step, epsilon):
        x, x_dot, theta, theta_dot = obs
        self.cart.set_xy((x - self.cart_w / 2, 0))
        pole_len = 2 * self.env.length
        tip_x = x + pole_len * math.sin(theta)
        tip_y = self.cart_h + pole_len * math.cos(theta)
        self.pole.set_data([x, tip_x], [self.cart_h, tip_y])
        self.axle.set_data([x], [self.cart_h])
        self.text.set_text(
            f"episode {episode:4d}  step {step:3d}  eps {epsilon:.3f}\n"
            f"x={x:+.3f}  x_dot={x_dot:+.3f}\n"
            f"theta={math.degrees(theta):+.2f} deg  theta_dot={theta_dot:+.3f}"
        )
        self._flush()

    def update_curve(self, returns):
        ep = np.arange(1, len(returns) + 1)
        self.curve.set_data(ep, returns)
        window = 100
        avg = [np.mean(returns[max(0, i - window + 1) : i + 1]) for i in range(len(returns))]
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
# Main loop                                                                   #
# --------------------------------------------------------------------------- #
def main():
    p = argparse.ArgumentParser(description="CartPole RL simulator with live visualization")
    p.add_argument(
        "--mode",
        choices=["train", "infer"],
        default="train",
        help="train: learn and save a policy; infer: load a saved policy and run it greedily",
    )
    p.add_argument("--agent", choices=["qlearning", "random"], default="qlearning")
    p.add_argument("--model", default="cartpole_q.npz", help="path to save/load the Q-table")
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
    args = p.parse_args()

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
    theta0_rad = math.radians(args.theta0) if args.theta0 is not None else None

    training = args.mode == "train"
    if args.episodes is None:
        args.episodes = 5000 if training else 10
    if args.render_every is None:
        args.render_every = 100 if training else 1

    env = CartPoleEnv(seed=args.seed)
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

    renderer = None if args.no_render else Renderer(
        env, title=f"CartPole RL — {'TRAINING' if training else 'INFERENCE (greedy, frozen policy)'}"
    )
    frame_dt = 1.0 / args.fps

    returns = []
    start_rng = np.random.default_rng(args.seed + 1)
    theta_range_rad = math.radians(args.theta_range)
    best_avg, best_q, best_episode = -np.inf, None, 0
    pbar = tqdm(total=args.episodes, desc="train", unit="ep", dynamic_ncols=True) if training else None
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
                    renderer.draw_frame(obs, episode, step, getattr(agent, "epsilon", 0.0))
                    plt.pause(frame_dt)
            agent.end_episode()
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
                print(
                    f"episode {episode:4d} | total reward {total:5.0f} | "
                    f"avg100 {np.mean(returns[-100:]):6.1f}"
                )
    except KeyboardInterrupt:
        if pbar is not None:
            pbar.close()
        print("\ninterrupted")
    if pbar is not None:
        pbar.close()

    if returns:
        print(f"\n[{args.mode}] ran {len(returns)} episodes, best episode reward {max(returns):.0f}, "
              f"mean {np.mean(returns):.1f}, final avg100 {np.mean(returns[-100:]):.1f}")
    if training and isinstance(agent, QLearningAgent) and returns:
        if best_q is not None:
            agent.q = best_q
            print(f"checkpoint: best avg100 = {best_avg:.1f} at episode {best_episode}")
        agent.save(args.model)
        print(f"saved Q-table to {args.model}")
    env.close()
    if renderer is not None and renderer.is_open():
        plt.ioff()
        print("close the window to exit")
        plt.show()


if __name__ == "__main__":
    main()
