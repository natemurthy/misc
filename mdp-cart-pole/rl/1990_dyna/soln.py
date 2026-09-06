"""
1990: Sutton's Dyna-Q -- Q-learning plus a learned model used for planning.

Reference
    R. S. Sutton, "Integrated Architectures for Learning, Planning, and
    Reacting Based on Approximating Dynamic Programming", Proc. 7th
    International Conference on Machine Learning, 1990.
    R. S. Sutton, "Dyna, an Integrated Architecture for Learning, Planning,
    and Reacting", SIGART Bulletin 2(4), 1991.

What changed from 1989
    Q-learning throws each real transition away after one update. Dyna keeps
    a model of the environment learned from those transitions and, after every
    real step, performs n extra "planning" updates on simulated transitions
    drawn from the model. The learner and the planner share one Q-table and
    one update rule, so planning is just Q-learning on remembered experience.
    This is the first explicitly *model-based* solution in the lineage (the
    1988 lookahead used the true model; Dyna learns one).

Algorithm (Dyna-Q, tabular, sample model)
    real step:  observe (s, a, r, s', terminal)
                Q(s,a) <- Q(s,a) + alpha * (y - Q(s,a))            [direct RL]
                Model(s,a) <- Model(s,a) + {(r, s', terminal)}        [model learning]
    planning:   repeat n times
                    (s, a) <- a previously seen state-action pair
                    (r, s', terminal) ~ Model(s, a)                   [sample the model]
                    Q(s,a) <- Q(s,a) + alpha * (y - Q(s,a))        [planning]

Sutton's 1990 paper assumes a deterministic world and stores one outcome per
(s, a). The state aggregation here (same (theta, theta_dot) grid as the 1989
solution) makes transitions between cells stochastic, so the model keeps the
most recent MODEL_CAPACITY outcomes per cell and samples one. That is the
"sample model" form of Dyna-Q from Sutton & Barto's textbook.
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import BaseAgent, GridDiscretizer  # noqa: E402

MODEL_CAPACITY = 32  # outcomes remembered per (state, action)


class DynaQAgent(BaseAgent):
    name = "1990_dyna"

    def __init__(self, bins=(1, 1, 8, 16), alpha=0.1, gamma=0.99, planning_steps=5,
                 epsilon=1.0, epsilon_min=0.01, epsilon_decay=0.999, seed=None):
        super().__init__(seed)
        self.grid = GridDiscretizer(bins)
        self.bins = self.grid.bins
        self.alpha, self.gamma, self.planning_steps = alpha, gamma, int(planning_steps)
        self.epsilon, self.epsilon_min, self.epsilon_decay = epsilon, epsilon_min, epsilon_decay
        n = self.grid.n_states
        self.q = np.zeros((n, 2))
        # sample model over flat state indices: ring buffer of (s', r, terminal) per (s, a)
        self.model_next = np.zeros((n, 2, MODEL_CAPACITY), dtype=np.int64)
        self.model_reward = np.zeros((n, 2, MODEL_CAPACITY))
        self.model_term = np.zeros((n, 2, MODEL_CAPACITY), dtype=bool)
        self.model_count = np.zeros((n, 2), dtype=np.int64)  # total outcomes ever stored
        self._seen_list = []  # flat (s*2 + a) indices, for uniform sampling

    # ---- policy ----------------------------------------------------------- #
    def act(self, obs):
        if not self.frozen and self.rng.random() < self.epsilon:
            return self._random_action()
        q = self.q[self.grid.flat(obs)]
        if q[0] == q[1]:
            return self._tie_break()
        return int(np.argmax(q))

    # ---- learning --------------------------------------------------------- #
    def _q_update(self, s, a, r, s_next, terminal):
        target = r if terminal else r + self.gamma * np.max(self.q[s_next])
        self.q[s, a] += self.alpha * (target - self.q[s, a])

    def _learn(self, obs, action, reward, next_obs, terminated):
        s, s_next = self.grid.flat(obs), self.grid.flat(next_obs)
        self._q_update(s, action, reward, s_next, terminated)            # direct RL

        c = self.model_count[s, action]                                  # model learning
        if c == 0:
            self._seen_list.append(s * 2 + action)
        slot = c % MODEL_CAPACITY
        self.model_next[s, action, slot] = s_next
        self.model_reward[s, action, slot] = reward
        self.model_term[s, action, slot] = terminated
        self.model_count[s, action] = c + 1

        if self.planning_steps and self._seen_list:                      # planning
            picks = self.rng.integers(len(self._seen_list), size=self.planning_steps)
            for k in picks:
                ps, pa = divmod(self._seen_list[k], 2)
                slot = self.rng.integers(min(self.model_count[ps, pa], MODEL_CAPACITY))
                self._q_update(ps, pa, self.model_reward[ps, pa, slot],
                               self.model_next[ps, pa, slot], self.model_term[ps, pa, slot])

    def _end_episode(self):
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def freeze(self):
        super().freeze()
        self.epsilon = 0.0

    # ---- bookkeeping ------------------------------------------------------ #
    def stats(self):
        return {"eps": self.epsilon, "model": float(len(self._seen_list))}

    def hparams(self):
        return dict(bins=list(self.bins), alpha=self.alpha, gamma=self.gamma,
                    planning_steps=self.planning_steps,
                    epsilon_min=self.epsilon_min, epsilon_decay=self.epsilon_decay)

    def state_dict(self):
        # The model is training state, not part of the policy; only Q is saved.
        return {"q": self.q, "epsilon": np.array(self.epsilon)}

    def load_state_dict(self, d):
        self.q = np.array(d["q"], dtype=np.float64)
        if "epsilon" in d:
            self.epsilon = float(d["epsilon"])


Agent = DynaQAgent
