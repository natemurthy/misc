"""
State representations shared by the solutions.

The MDP state is continuous, s = (x, x_dot, theta, theta_dot). Every solution
here works from some fixed transformation of it:

  GridDiscretizer  uniform bins per variable -> a tuple / flat index
                   (1988 TD(lambda), 1989 Q-learning, 1990 Dyna-Q)
  boxes_index      the 162-region BOXES decoder of Michie & Chambers (1968) as
                   used by Barto, Sutton & Anderson (1983) -> int in [0, 162)
  normalize_obs    scale each variable to roughly [-1, 1] for function
                   approximators (1986 backprop actor-critic, 1992 REINFORCE)
"""

import math

import numpy as np

# Rough scale of each state variable, used for clipping and normalization.
STATE_SCALE = np.array([2.4, 3.0, 0.21, 3.5])


class GridDiscretizer:
    """Uniform state aggregation. bins=(bx, bxdot, btheta, bthetadot); 1 = ignore."""

    def __init__(self, bins=(1, 1, 8, 16), lows=None, highs=None):
        self.bins = tuple(int(b) for b in bins)
        self.lows = np.array(lows if lows is not None else -STATE_SCALE, dtype=np.float64)
        self.highs = np.array(highs if highs is not None else STATE_SCALE, dtype=np.float64)
        self._bins_arr = np.array(self.bins)
        self.n_states = int(np.prod(self.bins))

    def index(self, obs):
        """Tuple index into an array of shape self.bins."""
        ratios = (np.clip(obs, self.lows, self.highs) - self.lows) / (self.highs - self.lows)
        idx = (ratios * (self._bins_arr - 1)).round().astype(int)
        return tuple(idx)

    def flat(self, obs):
        """Single integer in [0, n_states)."""
        return int(np.ravel_multi_index(self.index(obs), self.bins))


# --------------------------------------------------------------------------- #
# BOXES decoder, Barto/Sutton/Anderson 1983, Fig. 3 and accompanying text     #
# --------------------------------------------------------------------------- #
N_BOXES = 162  # 3 (x) * 3 (x_dot) * 6 (theta) * 3 (theta_dot)

_ONE_DEG = math.radians(1)
_SIX_DEG = math.radians(6)
_FIFTY_DEG_S = math.radians(50)


def boxes_index(obs):
    """
    Map a state to one of 162 boxes exactly as in the 1983 paper:

        x:         (-2.4, -0.8], (-0.8, 0.8), [0.8, 2.4)          3 regions
        x_dot:     (-inf, -0.5], (-0.5, 0.5), [0.5, inf)          3 regions
        theta:     <-6, [-6,-1), [-1,0), [0,1), [1,6], >6 degrees   6 regions
        theta_dot: (-inf, -50], (-50, 50), [50, inf) deg/s        3 regions

    Returns -1 if the state is already outside the failure thresholds.
    """
    x, x_dot, theta, theta_dot = (float(v) for v in obs)
    if abs(x) > 2.4 or abs(theta) > math.radians(12):
        return -1

    if x < -0.8:
        bx = 0
    elif x < 0.8:
        bx = 1
    else:
        bx = 2

    if x_dot < -0.5:
        bxd = 0
    elif x_dot < 0.5:
        bxd = 1
    else:
        bxd = 2

    if theta < -_SIX_DEG:
        bt = 0
    elif theta < -_ONE_DEG:
        bt = 1
    elif theta < 0:
        bt = 2
    elif theta < _ONE_DEG:
        bt = 3
    elif theta < _SIX_DEG:
        bt = 4
    else:
        bt = 5

    if theta_dot < -_FIFTY_DEG_S:
        btd = 0
    elif theta_dot < _FIFTY_DEG_S:
        btd = 1
    else:
        btd = 2

    return ((bx * 3 + bxd) * 6 + bt) * 3 + btd


def normalize_obs(obs):
    """Scale the four state variables to roughly [-1, 1] (not clipped)."""
    return np.asarray(obs, dtype=np.float64) / STATE_SCALE
