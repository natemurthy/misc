"""
1989: Watkins' Q-learning, tabular, over a discretized state.

Reference
    C. J. C. H. Watkins, "Learning from Delayed Rewards", PhD thesis,
    University of Cambridge, 1989.
    C. J. C. H. Watkins, P. Dayan, "Q-learning", Machine Learning 8:279-292,
    1992 (convergence proof).

What changed from 1988
    TD(lambda) learns state values V(s) and needs a model f(s, a) to pick the
    action with the best successor. Q-learning learns action values Q(s, a)
    directly, so the greedy action is argmax_a Q(s, a): no model, no lookahead.
    It is also off-policy: the target uses max_a' Q(s', a') regardless of which
    action the exploring behavior policy actually takes next, so it estimates
    the optimal Q* while behaving epsilon-greedily.

Update rule (one-step, tabular)
    y_t = r_t                                  if s_{t+1} is terminal
        = r_t + gamma * max_a' Q(s_{t+1}, a')  otherwise
    Q(s_t, a_t) <- Q(s_t, a_t) + alpha * (y_t - Q(s_t, a_t))

The state is aggregated by a uniform grid over (theta, theta_dot) only; cart
position and velocity are ignored (bins = 1). See README.md in this directory
for the full MDP and Bellman formulation.
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import BaseAgent, GridDiscretizer  # noqa: E402


class QLearningAgent(BaseAgent):
    name = "1989_qlearning"

    def __init__(self, bins=(1, 1, 8, 16), alpha=0.1, gamma=0.99,
                 epsilon=1.0, epsilon_min=0.01, epsilon_decay=0.999, seed=None):
        super().__init__(seed)
        self.grid = GridDiscretizer(bins)
        self.bins = self.grid.bins
        self.alpha, self.gamma = alpha, gamma
        self.epsilon, self.epsilon_min, self.epsilon_decay = epsilon, epsilon_min, epsilon_decay
        self.q = np.zeros(self.bins + (2,))

    # kept as public attributes/methods for gym/main.py and older callers
    @property
    def lows(self):
        return self.grid.lows

    @property
    def highs(self):
        return self.grid.highs

    def discretize(self, obs):
        return self.grid.index(obs)

    # ---- policy ----------------------------------------------------------- #
    def act(self, obs):
        if not self.frozen and self.rng.random() < self.epsilon:
            return self._random_action()
        q = self.q[self.discretize(obs)]
        if q[0] == q[1]:  # ties: random while learning, deterministic when frozen
            return self._tie_break()
        return int(np.argmax(q))

    # ---- learning --------------------------------------------------------- #
    def _learn(self, obs, action, reward, next_obs, terminated):
        s, s_next = self.discretize(obs), self.discretize(next_obs)
        target = reward if terminated else reward + self.gamma * np.max(self.q[s_next])
        self.q[s + (action,)] += self.alpha * (target - self.q[s + (action,)])

    def _end_episode(self):
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def freeze(self):
        super().freeze()
        self.epsilon = 0.0

    # ---- bookkeeping ------------------------------------------------------ #
    def stats(self):
        return {"eps": self.epsilon}

    def hparams(self):
        return dict(bins=list(self.bins), alpha=self.alpha, gamma=self.gamma,
                    epsilon_min=self.epsilon_min, epsilon_decay=self.epsilon_decay)

    def state_dict(self):
        return {"q": self.q, "epsilon": np.array(self.epsilon)}

    def load_state_dict(self, d):
        self.q = np.array(d["q"], dtype=np.float64)
        if "epsilon" in d:
            self.epsilon = float(d["epsilon"])

    @classmethod
    def load(cls, path, seed=None):
        data = np.load(path, allow_pickle=False)
        if "__meta__" in data.files:
            return super().load(path, seed=seed)
        # legacy format written by the original single-file main.py
        agent = cls(bins=tuple(int(b) for b in data["bins"]), seed=seed)
        agent.q = np.array(data["q"], dtype=np.float64)
        return agent


Agent = QLearningAgent
