"""Live matplotlib view: cart/pole on top, total reward per episode on the bottom."""

import math
import sys

import matplotlib
import numpy as np

# Use an interactive backend if available; fall back gracefully.
try:
    matplotlib.use("MacOSX" if sys.platform == "darwin" else "TkAgg")
except Exception:
    pass
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402


class Renderer:
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
        self.ax_curve.set_ylabel("Total reward per episode\n(= steps survived)")
        self.ax_curve.set_ylim(0, env.max_episode_steps + 10)
        self.ax_curve.grid(alpha=0.3)
        (self.curve,) = self.ax_curve.plot([], [], color="#aaaaaa", lw=1, label="total reward")
        (self.avg_curve,) = self.ax_curve.plot([], [], color="#3b6ea5", lw=2, label="100-ep mov avg")
        self.ax_curve.legend(loc="upper left")

        self.fig.tight_layout()
        self.fig.show()

    def draw_frame(self, obs, episode, step, stats=None):
        x, x_dot, theta, theta_dot = obs
        self.cart.set_xy((x - self.cart_w / 2, 0))
        pole_len = 2 * self.env.length
        tip_x = x + pole_len * math.sin(theta)
        tip_y = self.cart_h + pole_len * math.cos(theta)
        self.pole.set_data([x, tip_x], [self.cart_h, tip_y])
        self.axle.set_data([x], [self.cart_h])
        extra = "  ".join(f"{k} {v:.3f}" for k, v in (stats or {}).items())
        self.text.set_text(
            f"episode {episode:4d}  step {step:3d}  {extra}\n"
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
