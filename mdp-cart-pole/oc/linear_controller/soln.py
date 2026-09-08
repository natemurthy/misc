"""
Hand-tuned linear state feedback with a bang-bang output: the reference controller.

    u = sign( k_theta * theta + k_thetadot * theta_dot + k_x * x + k_xdot * x_dot )

with u = +1 meaning push right (action 1) and u = -1 push left (action 0). No
learning happens: the four gains are fixed numbers chosen by a search over a
small grid that maximizes the widest pole angle the controller can recover
from within the +/-2.4 m track (see `tune`). It runs on the same CartPoleEnv
as the reinforcement-learning solutions in ../../rl.

Why it is here
    This is the simplest controller in the optimal-control lineage: full-state
    linear feedback through a saturating (sign) actuator. It is what a
    linear-quadratic regulator produces once you take the sign of its output,
    except that an LQR derives the gains from the cart-pole system model and a cost
    function via the Riccati equation, whereas these were found by trial. The
    next step in this directory replaces the search with that derivation.

    It also serves the rl/ solutions as a yardstick: the 1992 REINFORCE policy
    is a linear-logistic unit over the same four state variables, so the two
    have identical form and differ only in how the gains were obtained.
"""

import math
import sys
from pathlib import Path

import numpy as np

RL_DIR = Path(__file__).resolve().parents[2] / "rl"
if str(RL_DIR) not in sys.path:
    sys.path.insert(0, str(RL_DIR))
from common import BaseAgent, CartPoleEnv  # noqa: E402

# (k_theta, k_thetadot, k_x, k_xdot) from tune(); recovers from ~34 deg at rest, centered
DEFAULT_GAINS = (1.0, 0.35, 0.02, 0.2)


class LinearBangBangController(BaseAgent):
    name = "linear_controller"
    supports_wide_angles = True

    def __init__(self, gains=DEFAULT_GAINS, seed=None):
        super().__init__(seed)
        self.gains = np.array(gains, dtype=np.float64)
        assert self.gains.shape == (4,), "gains are (k_theta, k_thetadot, k_x, k_xdot)"

    def feedback(self, obs):
        """The linear combination k . (theta, theta_dot, x, x_dot) before the sign."""
        x, x_dot, theta, theta_dot = (float(v) for v in obs)
        k1, k2, k3, k4 = self.gains
        return k1 * theta + k2 * theta_dot + k3 * x + k4 * x_dot

    def act(self, obs):
        u = self.feedback(obs)
        if u == 0.0:
            return self._tie_break()
        return int(u > 0)

    # ---- no learning; interface kept so main.py-style loops and tests work ---- #
    def stats(self):
        return {}

    def hparams(self):
        return dict(gains=[float(g) for g in self.gains])

    def state_dict(self):
        return {"gains": self.gains}

    def load_state_dict(self, d):
        self.gains = np.array(d["gains"], dtype=np.float64)


Agent = LinearBangBangController


# --------------------------------------------------------------------------- #
# Recovery envelope and gain search                                           #
# --------------------------------------------------------------------------- #
def recovers(gains, theta0_deg, x0=0.0, theta_limit_deg=60.0, steps=500):
    """
    True if the controller keeps the pole inside +/-theta_limit and the cart on
    the track for `steps` steps, starting at rest from angle theta0_deg and
    position x0. The wide default limit makes this a test of recovery, not of
    the standard 12 degree task.
    """
    ctrl = LinearBangBangController(gains)
    env = CartPoleEnv(seed=0, theta_limit_deg=theta_limit_deg)
    obs, _ = env.reset(options={"theta0": math.radians(theta0_deg), "x0": x0})
    env.state[1] = 0.0  # at rest: no cart or pole velocity
    env.state[3] = 0.0
    obs = env._obs()
    for _ in range(steps):
        obs, _, terminated, _, _ = env.step(ctrl.act(obs))
        if terminated:
            return False
    return True


def max_recoverable_angle(gains, x0=0.0, lo=1.0, hi=45.0, iters=12, **kw):
    """Largest start angle (degrees) recovers() succeeds from, by bisection. Assumes monotonicity."""
    if not recovers(gains, lo, x0, **kw):
        return 0.0
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if recovers(gains, mid, x0, **kw):
            lo = mid
        else:
            hi = mid
    return lo


def tune(k_theta=(1.0,), k_thetadot=(0.2, 0.35, 0.5, 0.8), k_x=(0.0, 0.02, 0.05, 0.1, 0.2),
         k_xdot=(0.0, 0.05, 0.1, 0.2, 0.4), x0=0.0, verbose=False):
    """
    Grid search for the gains with the widest recovery envelope from rest at x0.
    k_theta is fixed at 1 because only the ratios matter to a sign function.
    Returns (best_gains, best_angle_deg).
    """
    best = (0.0, None)
    for g1 in k_theta:
        for g2 in k_thetadot:
            for g3 in k_x:
                for g4 in k_xdot:
                    g = (g1, g2, g3, g4)
                    ang = max_recoverable_angle(g, x0)
                    if verbose:
                        print(f"gains {g}: recovers to {ang:5.1f} deg")
                    if ang > best[0]:
                        best = (ang, g)
    return best[1], best[0]
