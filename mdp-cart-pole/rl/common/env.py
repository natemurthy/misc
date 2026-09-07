"""
The CartPole MDP, shared by every solution in this repository.

Re-implementation of Gymnasium's CartPole-v1 that follows the Gymnasium Env API
without importing the library:

    obs, info = env.reset(seed=None, options=None)
    obs, reward, terminated, truncated, info = env.step(action)

Observation: float32 [x, x_dot, theta, theta_dot]
Action:      0 = push cart left, 1 = push cart right           (default, as Gymnasium)
             CartPoleEnv(continuous=True) instead takes a float u in [-1, 1]
             and applies force u * 10 N; ints 0/1 still mean full left/right.
             Only the 1999 continuous Q-learning solution uses this mode.
Reward:      +1 for every step taken (including the terminating step)
Terminated:  |theta| > theta_limit (12 deg by default)  or  |x| > 2.4
             CartPoleEnv(theta_limit_deg=...) widens the angle limit; the class
             attribute theta_threshold_radians keeps the 12 deg default for
             code that needs the standard task (the BOXES decoder, the grids).
Truncated:   episode length reaches 500 (Gymnasium does this with a TimeLimit
             wrapper; here it is built in)

reset() accepts options={"x0": meters, "theta0": radians} to override the
initial cart position and pole angle. See ../gym/ for the same problem written
against the real library.

The one-step dynamics are also exposed as CartPoleEnv.dynamics(state, action)
so that solutions which need a model of the environment (the 1988 TD(lambda)
lookahead) can call it explicitly. Model-free solutions never touch it.
"""

import math

import numpy as np


class CartPoleEnv:
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

    def __init__(self, seed=None, render_mode=None, continuous=False, theta_limit_deg=None):
        self.rng = np.random.default_rng(seed)
        self.render_mode = render_mode
        self.continuous = bool(continuous)
        if theta_limit_deg is not None:
            assert theta_limit_deg > 0, "theta_limit_deg must be positive"
            # instance attribute shadows the 12 deg class default
            self.theta_threshold_radians = math.radians(float(theta_limit_deg))
        self.state = None
        self.steps = 0

    @property
    def theta_limit_deg(self):
        return math.degrees(self.theta_threshold_radians)

    # ------------------------------------------------------------------ #
    # Pure functions of the MDP                                           #
    # ------------------------------------------------------------------ #
    @classmethod
    def dynamics(cls, state, action):
        """One Euler step for a discrete action (0 = full push left, 1 = full push right)."""
        return cls.dynamics_force(state, cls.force_mag if action == 1 else -cls.force_mag)

    @classmethod
    def action_to_force(cls, action):
        """Map an action to a force in newtons. Ints/bools 0/1 are full pushes; floats are
        a fraction u in [-1, 1] of force_mag (used in continuous mode)."""
        if isinstance(action, (bool, np.bool_)) or isinstance(action, (int, np.integer)):
            assert action in (0, 1), f"invalid discrete action {action}"
            return cls.force_mag if action == 1 else -cls.force_mag
        u = float(action)
        assert math.isfinite(u), f"invalid continuous action {action}"
        return cls.force_mag * max(-1.0, min(1.0, u))

    @classmethod
    def dynamics_force(cls, state, force):
        """
        One Euler step of the cart-pole equations of motion under a horizontal
        force (newtons). Pure function: state in, next state out, no side effects.

        Equations from Barto, Sutton & Anderson (1983), without their friction
        terms, exactly as in Gymnasium. Paper:
        https://github.com/david78k/pendulum/blob/master/c/anderson/Neuronlike%20Adaptive%20Elements%20That%20Can%20Solve%20Difficult%20Learning%20Control%20Problems%20Barto1983.pdf
        """
        x, x_dot, theta, theta_dot = (float(v) for v in state)
        costheta = math.cos(theta)
        sintheta = math.sin(theta)

        temp = (force + cls.polemass_length * theta_dot**2 * sintheta) / cls.total_mass
        thetaacc = (cls.gravity * sintheta - costheta * temp) / (
            cls.length * (4.0 / 3.0 - cls.masspole * costheta**2 / cls.total_mass)
        )
        xacc = temp - cls.polemass_length * thetaacc * costheta / cls.total_mass

        return np.array(
            [
                x + cls.tau * x_dot,
                x_dot + cls.tau * xacc,
                theta + cls.tau * theta_dot,
                theta_dot + cls.tau * thetaacc,
            ],
            dtype=np.float64,
        )

    @classmethod
    def is_terminal(cls, state, theta_threshold=None):
        """Failure test. Uses the standard 12 deg limit unless a threshold (radians) is given."""
        lim = cls.theta_threshold_radians if theta_threshold is None else theta_threshold
        x, _, theta, _ = state
        return bool(x < -cls.x_threshold or x > cls.x_threshold or theta < -lim or theta > lim)

    # ------------------------------------------------------------------ #
    # Gymnasium-style API                                                 #
    # ------------------------------------------------------------------ #
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
        if self.continuous:
            self.state = self.dynamics_force(self.state, self.action_to_force(action))
        else:
            assert isinstance(action, (int, np.integer, bool, np.bool_)) and action in (0, 1), f"invalid action {action}"
            self.state = self.dynamics(self.state, action)
        self.steps += 1
        terminated = self.is_terminal(self.state, self.theta_threshold_radians)
        truncated = self.steps >= self.max_episode_steps
        reward = 1.0
        return self._obs(), reward, terminated, truncated, {}

    def close(self):
        pass
