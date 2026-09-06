"""
1988: Sutton's TD(lambda) for prediction, used for control via one-step lookahead.

Reference
    R. S. Sutton, "Learning to Predict by the Methods of Temporal Differences",
    Machine Learning 3:9-44, 1988.

What the paper is, and is not
    TD(lambda) is a *prediction* method: it learns the value V(s) of the states
    visited under whatever policy generated the data. It does not by itself
    say which action to take. Its contribution was to isolate the critic
    update inside the 1983 ACE, give it the lambda-trace in its modern form,
    and prove convergence for linear function approximation.

How it is turned into a controller here
    The same way Samuel (checkers, 1959) and later Tesauro (TD-Gammon, 1992)
    used a learned state-value function: evaluate each candidate action by
    looking one step ahead with a model of the environment and pick the action
    whose successor state has the highest predicted value.

        a_t = argmax_a  [ r + gamma * V(phi(f(s_t, a))) ]     (0 if f(s_t,a) is terminal)

    f is CartPoleEnv.dynamics, the true one-step model. So this solution is
    model-free in *learning* (V is learned from sampled transitions) but
    model-based in *acting*. Removing that dependence on f is exactly what
    Q-learning does next (see ../1989_qlearning).

Learning rule (TD(lambda) with replacing traces over a state aggregation)
    delta_t = r_t + gamma * V(s_{t+1}) - V(s_t)          (V = 0 on failure)
    z      <- gamma * lambda * z ;  z[phi(s_t)] = 1
    V      <- V + alpha * delta_t * z

Exploration is epsilon-greedy over the lookahead choice, decayed per episode.
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import BaseAgent, CartPoleEnv, GridDiscretizer  # noqa: E402


class TDLambdaLookaheadAgent(BaseAgent):
    name = "1988_td"

    def __init__(self, bins=(3, 3, 16, 32), alpha=0.1, gamma=0.99, lam=0.8,
                 epsilon=1.0, epsilon_min=0.01, epsilon_decay=0.999, seed=None):
        super().__init__(seed)
        self.grid = GridDiscretizer(bins)
        self.bins = self.grid.bins
        self.alpha, self.gamma, self.lam = alpha, gamma, lam
        self.epsilon, self.epsilon_min, self.epsilon_decay = epsilon, epsilon_min, epsilon_decay
        self.v = np.zeros(self.grid.n_states)
        self.z = np.zeros(self.grid.n_states)

    # ---- policy: one-step lookahead with the model ------------------------ #
    def _lookahead_value(self, obs, action):
        nxt = CartPoleEnv.dynamics(obs, action)
        if CartPoleEnv.is_terminal(nxt):
            return 1.0  # reward for the step, then nothing
        return 1.0 + self.gamma * self.v[self.grid.flat(nxt)]

    def act(self, obs):
        if not self.frozen and self.rng.random() < self.epsilon:
            return self._random_action()
        q0, q1 = self._lookahead_value(obs, 0), self._lookahead_value(obs, 1)
        if q0 == q1:
            return self._tie_break()
        return int(q1 > q0)

    # ---- learning: TD(lambda) on V ---------------------------------------- #
    def _learn(self, obs, action, reward, next_obs, terminated):
        s = self.grid.flat(obs)
        v_next = 0.0 if terminated else self.v[self.grid.flat(next_obs)]
        delta = reward + self.gamma * v_next - self.v[s]
        self.z *= self.gamma * self.lam
        self.z[s] = 1.0  # replacing trace
        self.v += self.alpha * delta * self.z

    def _end_episode(self):
        self.z[:] = 0.0
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    # ---- bookkeeping ------------------------------------------------------ #
    def stats(self):
        return {"eps": 0.0 if self.frozen else self.epsilon}

    def hparams(self):
        return dict(bins=list(self.bins), alpha=self.alpha, gamma=self.gamma, lam=self.lam,
                    epsilon_min=self.epsilon_min, epsilon_decay=self.epsilon_decay)

    def state_dict(self):
        return {"v": self.v, "epsilon": np.array(self.epsilon)}

    def load_state_dict(self, d):
        self.v = np.array(d["v"], dtype=np.float64)
        if "epsilon" in d:
            self.epsilon = float(d["epsilon"])


Agent = TDLambdaLookaheadAgent
