"""
1992: Williams' REINFORCE -- Monte Carlo policy gradient with a baseline.

Reference
    R. J. Williams, "Simple Statistical Gradient-Following Algorithms for
    Connectionist Reinforcement Learning", Machine Learning 8:229-256, 1992.
    (The algorithm first appeared in Williams' 1986-1988 technical reports.)

What changed from the value-based line (1988-1990)
    Everything before this learns a value function and derives the policy from
    it. REINFORCE has no value function at all. It parameterizes the policy
    directly, pi_theta(a | s), runs a whole episode, and moves theta along an
    unbiased sample of the gradient of expected return:

        theta <- theta + alpha * sum_t (G_t - b) * grad_theta log pi_theta(a_t | s_t)

    G_t is the discounted return from step t and b is a "reinforcement
    baseline" that does not change the expectation of the gradient but
    reduces its variance. This is the ancestor of every modern policy-gradient
    method; the 1983 ASE was a one-step, critic-driven precursor of the same
    idea, and REINFORCE is what makes it rigorous.

Policy used here
    Linear-logistic over the normalized state plus a bias:
        z = theta . [x, x_dot, theta_pole, theta_dot, 1]
        pi(right | s) = sigmoid(z),   pi(left | s) = 1 - sigmoid(z)
        grad_theta log pi(a | s) = (a - sigmoid(z)) * features
    A linear policy is enough to balance CartPole. The baseline b is an
    exponential moving average of past episode returns (a constant baseline in
    Williams' terminology).
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import BaseAgent, normalize_obs  # noqa: E402


def _sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


class ReinforceAgent(BaseAgent):
    name = "1992_reinforce"

    def __init__(self, alpha=0.001, gamma=0.99, baseline_rate=0.05, seed=None):
        super().__init__(seed)
        self.alpha, self.gamma, self.baseline_rate = alpha, gamma, baseline_rate
        self.theta = np.zeros(5)
        self.baseline = 0.0
        self._episode = []  # (features, action, reward)

    @staticmethod
    def _features(obs):
        return np.append(normalize_obs(obs), 1.0)

    # ---- policy ----------------------------------------------------------- #
    def act(self, obs):
        p = _sigmoid(self.theta @ self._features(obs))
        if self.frozen:
            return int(p > 0.5) if p != 0.5 else self._tie_break()
        return int(self.rng.random() < p)

    # ---- learning: store the episode, update at the end ------------------- #
    def _learn(self, obs, action, reward, next_obs, terminated):
        self._episode.append((self._features(obs), action, reward))

    def _end_episode(self):
        if not self._episode:
            return
        T = len(self._episode)
        returns = np.empty(T)
        g = 0.0
        for t in range(T - 1, -1, -1):
            g = self._episode[t][2] + self.gamma * g
            returns[t] = g

        grad = np.zeros_like(self.theta)
        for (phi, a, _), G in zip(self._episode, returns):
            p = _sigmoid(self.theta @ phi)
            grad += (G - self.baseline) * (a - p) * phi
        self.theta += self.alpha * grad

        # constant baseline: EMA of the (undiscounted-from-start) episode return
        self.baseline += self.baseline_rate * (returns[0] - self.baseline)
        self._episode = []

    # ---- bookkeeping ------------------------------------------------------ #
    def stats(self):
        return {"baseline": float(self.baseline), "|theta|": float(np.abs(self.theta).mean())}

    def hparams(self):
        return dict(alpha=self.alpha, gamma=self.gamma, baseline_rate=self.baseline_rate)

    def state_dict(self):
        return {"theta": self.theta, "baseline": np.array(self.baseline)}

    def load_state_dict(self, d):
        self.theta = np.array(d["theta"], dtype=np.float64)
        if "baseline" in d:
            self.baseline = float(d["baseline"])


Agent = ReinforceAgent
