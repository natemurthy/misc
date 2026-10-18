"""
Live matplotlib view.

Left column:  cart/pole on top, total reward per episode on the bottom.
Right column: phase portrait of the pole, theta vs theta_dot, one trace per
              rendered episode with earlier episodes fading out.
"""

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


class PhasePortrait:
    """
    Trajectory of each rendered episode through the (theta, theta_dot) plane.

    The closed loop of cart-pole system plus policy is a dynamical system; this is its
    state-space picture. A good policy spirals in toward the origin and then
    chatters in a small cycle around it (bang-bang control). A failing one
    spirals out through the +/-12 degree lines. Earlier episodes are kept at
    fading opacity so a multi-episode run accumulates into one picture.
    """

    KEEP = 8  # episodes retained on screen

    def __init__(self, ax, theta_limit_deg=12.0, theta_dot_limit=3.0):
        self.ax = ax
        self.theta_dot_limit = theta_dot_limit
        ax.set_title("phase portrait (closed loop)", fontsize=10)
        ax.set_xlabel("pole angle θ (deg)")
        ax.set_ylabel("pole angular velocity θ̇ (rad/s)")
        ax.set_xlim(-theta_limit_deg - 2, theta_limit_deg + 2)
        ax.set_ylim(-theta_dot_limit, theta_dot_limit)  # fixed; traces beyond it run off-axis
        for xb in (-theta_limit_deg, theta_limit_deg):
            ax.axvline(xb, color="#cc4444", lw=1, ls="--")  # termination
        ax.axhline(0, color="#bbbbbb", lw=0.8)
        ax.axvline(0, color="#bbbbbb", lw=0.8)
        ax.plot([0], [0], "+", color="#222222", ms=10, mew=1.5)  # upright, at rest
        ax.grid(alpha=0.3)
        self.label = ax.text(0.02, 0.98, "", transform=ax.transAxes, va="top", fontsize=9)
        # current state; becomes an up/down caret on the axis edge when theta_dot is out of range.
        # Clipping is switched off in unclip_head() only after the figure is laid out: an empty
        # unclipped artist gives tight_layout a degenerate bounding box and it shrinks every axes.
        (self.head,) = ax.plot([], [], "o", color="#d38b2c", ms=6, zorder=5)
        self.traces = []  # Line2D per retained episode, oldest first
        self.current_episode = None
        self.xs, self.ys = [], []

    def _new_trace(self, episode):
        for k, line in enumerate(reversed(self.traces)):
            line.set_alpha(max(0.08, 0.5 * 0.7**k))
            line.set_linewidth(0.9)
        (line,) = self.ax.plot([], [], color="#3b6ea5", lw=1.4, alpha=1.0, zorder=4)
        self.traces.append(line)
        while len(self.traces) > self.KEEP:
            self.traces.pop(0).remove()
        self.current_episode = episode
        self.xs, self.ys = [], []
        self.label.set_text(f"episode {episode}")

    def unclip_head(self):
        """Let the edge carets draw fully on the axis boundary. Call after tight_layout()."""
        self.head.set_clip_on(False)

    def align_to(self, top_ax, bottom_ax):
        """
        Match this axes' vertical extent to the drawn boxes of two stacked axes.
        Axes with a fixed aspect ratio (the cart/pole panel, an image) shrink
        inside their grid cell at draw time, so the grid cell's top is not where
        the panel's top actually is. Call after layout and on every redraw.
        """
        top_ax.apply_aspect()
        bottom_ax.apply_aspect()
        t, b, me = top_ax.get_position(), bottom_ax.get_position(), self.ax.get_position()
        self.ax.set_position([me.x0, b.y0, me.width, t.y1 - b.y0])

    def add(self, obs, episode):
        if episode != self.current_episode:
            self._new_trace(episode)
        theta_deg, theta_dot = math.degrees(float(obs[2])), float(obs[3])
        self.xs.append(theta_deg)
        self.ys.append(theta_dot)
        self.traces[-1].set_data(self.xs, self.ys)  # off-range segments are clipped by the axes
        lim = self.theta_dot_limit
        if theta_dot > lim:
            self.head.set_marker("^")
            self.head.set_data([theta_deg], [lim])
        elif theta_dot < -lim:
            self.head.set_marker("v")
            self.head.set_data([theta_deg], [-lim])
        else:
            self.head.set_marker("o")
            self.head.set_data([theta_deg], [theta_dot])


class Renderer:
    def __init__(self, env, title="CartPole RL"):
        self.env = env
        plt.ion()
        self.fig = plt.figure(figsize=(14.4, 7))
        gs = self.fig.add_gridspec(2, 2, width_ratios=[3, 3], height_ratios=[2, 1])
        self.ax_sim = self.fig.add_subplot(gs[0, 0])
        self.ax_curve = self.fig.add_subplot(gs[1, 0])
        self.ax_phase = self.fig.add_subplot(gs[:, 1])  # full height of the right column
        self.phase = PhasePortrait(self.ax_phase, math.degrees(env.theta_threshold_radians))
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
        self.phase.unclip_head()
        self.phase.align_to(self.ax_sim, self.ax_curve)
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
        self.phase.add(obs, episode)
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
        self.phase.align_to(self.ax_sim, self.ax_curve)  # keeps alignment after a window resize
        self.fig.canvas.draw_idle()
        self.fig.canvas.flush_events()
        plt.pause(0.001)

    def is_open(self):
        return plt.fignum_exists(self.fig.number)
