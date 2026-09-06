"""
1983: Barto, Sutton & Anderson's ASE/ACE actor-critic on the BOXES state decoder.

Reference
    A. G. Barto, R. S. Sutton, C. W. Anderson, "Neuronlike Adaptive Elements
    That Can Solve Difficult Learning Control Problems", IEEE Transactions on
    Systems, Man, and Cybernetics, SMC-13(5), 1983.

Architecture
    x_t  in {0,1}^162   one-hot BOXES decoding of the state (common.features.boxes_index)

    ASE (Associative Search Element)  -- the actor
        y_t = sign( w . x_t + noise ),   noise ~ N(0, sigma^2)
        action = right if y_t = +1 else left
        e_i  <- delta * e_i + (1 - delta) * y_t * x_i(t)          eligibility trace
        w_i  <- w_i + alpha * rhat_t * e_i

    ACE (Adaptive Critic Element)  -- the critic
        p_t   = v . x_t                                              value prediction
        rhat_t = r_t + gamma * p_{t+1} - p_t     (p_{t+1} = 0 on failure)  internal reinforcement
        xbar_i <- lambda * xbar_i + (1 - lambda) * x_i(t)             critic trace
        v_i   <- v_i + beta * rhat_t * xbar_i

The paper's reward is a failure signal (-1 when the pole falls or the cart
leaves the track, 0 otherwise). This repository fixes the MDP to Gymnasium's
+1-per-step reward so every solution solves the same problem. With that
reward the untrained critic sees rhat = +1 on every step, which the paper's
alpha = 1000 would turn into an immediate, permanent commitment to whichever
action happened first. The actor step size is therefore reduced (see
DEFAULTS); the structure of the update is unchanged.
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import BaseAgent, boxes_index, N_BOXES  # noqa: E402

# Paper values: alpha=1000, beta=0.5, gamma=0.95, delta=0.9, lam=0.8, sigma=0.01.
DEFAULTS = dict(alpha=0.5, beta=0.5, gamma=0.95, delta=0.9, lam=0.8, sigma=0.01)


class ActorCriticBoxesAgent(BaseAgent):
    name = "1983_actor_critic"

    def __init__(self, alpha=DEFAULTS["alpha"], beta=DEFAULTS["beta"], gamma=DEFAULTS["gamma"],
                 delta=DEFAULTS["delta"], lam=DEFAULTS["lam"], sigma=DEFAULTS["sigma"], seed=None):
        super().__init__(seed)
        self.alpha, self.beta, self.gamma = alpha, beta, gamma
        self.delta, self.lam, self.sigma = delta, lam, sigma
        self.w = np.zeros(N_BOXES)      # ASE weights (actor)
        self.v = np.zeros(N_BOXES)      # ACE weights (critic)
        self.e = np.zeros(N_BOXES)      # ASE eligibility trace
        self.xbar = np.zeros(N_BOXES)   # ACE trace
        self._last_y = 0

    # ---- policy ----------------------------------------------------------- #
    def act(self, obs):
        i = boxes_index(obs)
        if i < 0:  # already failed; action is irrelevant
            return self._random_action()
        s = self.w[i] + (0.0 if self.frozen else self.rng.normal(0.0, self.sigma))
        if s == 0.0:
            y = 1 if self._tie_break() == 1 else -1
        else:
            y = 1 if s > 0 else -1
        self._last_y = y
        return 1 if y > 0 else 0

    # ---- learning --------------------------------------------------------- #
    def _learn(self, obs, action, reward, next_obs, terminated):
        i = boxes_index(obs)
        if i < 0:
            return
        y = 1 if action == 1 else -1
        j = -1 if terminated else boxes_index(next_obs)
        p_next = 0.0 if j < 0 else self.v[j]
        rhat = reward + self.gamma * p_next - self.v[i]

        # traces include the current (state, action) before the weight step
        self.e *= self.delta
        self.e[i] += (1.0 - self.delta) * y
        self.xbar *= self.lam
        self.xbar[i] += 1.0 - self.lam

        self.w += self.alpha * rhat * self.e
        self.v += self.beta * rhat * self.xbar

    def _end_episode(self):
        self.e[:] = 0.0
        self.xbar[:] = 0.0

    # ---- bookkeeping ------------------------------------------------------ #
    def stats(self):
        return {"sigma": 0.0 if self.frozen else self.sigma, "|w|": float(np.abs(self.w).mean())}

    def hparams(self):
        return dict(alpha=self.alpha, beta=self.beta, gamma=self.gamma,
                    delta=self.delta, lam=self.lam, sigma=self.sigma)

    def state_dict(self):
        return {"w": self.w, "v": self.v}

    def load_state_dict(self, d):
        self.w = np.array(d["w"], dtype=np.float64)
        self.v = np.array(d["v"], dtype=np.float64)


Agent = ActorCriticBoxesAgent
