"""
CartPole-v1 with a configurable start distribution, registered with Gymnasium.

This is the one piece of environment code the project still owns when using
Gymnasium: the physics, spaces, reward, termination and rendering all come
from gymnasium.envs.classic_control.CartPoleEnv. We subclass it only to control
where episodes start.

    import cartpole_env                      # registers CartPoleFullRange-v0
    env = gym.make("CartPoleFullRange-v0", theta_range=math.radians(12))
    obs, info = env.reset(seed=0)                                # random start
    obs, info = env.reset(options={"x0": 1.5, "theta0": -0.14})  # exact start

Compare with reset() in ../main.py, which takes the same options dict.
"""

import gymnasium as gym
import numpy as np
from gymnasium.envs.classic_control.cartpole import CartPoleEnv


class CartPoleFullRangeEnv(CartPoleEnv):
    """
    CartPole-v1 whose initial pole angle can be drawn from a wide band.

    Constructor
        theta_range: if > 0, every reset draws theta uniformly from
                     [-theta_range, theta_range] radians instead of Gymnasium's
                     default [-0.05, 0.05]. Cart position and both velocities
                     keep the default band.

    reset(options=...) keys, all optional
        "x0":          exact initial cart position in meters
        "theta0":      exact initial pole angle in radians
        "theta_range": per-call override of the constructor value
    Any other keys (Gymnasium's "low"/"high" reset bounds) pass through.
    """

    def __init__(self, render_mode=None, theta_range=0.0):
        super().__init__(render_mode=render_mode)
        self.theta_range = float(theta_range)

    def reset(self, *, seed=None, options=None):
        options = dict(options or {})
        x0 = options.pop("x0", None)
        theta0 = options.pop("theta0", None)
        theta_range = options.pop("theta_range", self.theta_range)

        # Base class seeds self.np_random and draws the default [-0.05, 0.05] state.
        _, info = super().reset(seed=seed, options=options or None)

        if theta_range > 0:
            self.state[2] = self.np_random.uniform(-theta_range, theta_range)
        if x0 is not None:
            self.state[0] = x0
        if theta0 is not None:
            self.state[2] = theta0

        if self.render_mode == "human":
            self.render()
        return np.array(self.state, dtype=np.float32), info


gym.register(
    id="CartPoleFullRange-v0",
    entry_point=CartPoleFullRangeEnv,
    max_episode_steps=500,  # gym.make wraps the env in TimeLimit for us
    reward_threshold=475.0,
)
