"""
1986-1989: Anderson's actor-critic with multilayer networks trained by backprop.

Reference
    C. W. Anderson, "Learning and Problem Solving with Multilayer Connectionist
    Systems", PhD thesis, University of Massachusetts Amherst, 1986.
    C. W. Anderson, "Strategy Learning with Multilayer Connectionist
    Representations", Proc. 4th International Workshop on Machine Learning, 1987.
    C. W. Anderson, "Learning to Control an Inverted Pendulum Using Neural
    Networks", IEEE Control Systems Magazine, 9(3), 1989.

What changed from 1983
    The 162-box hand-built decoder is replaced by two small networks that take
    the raw (normalized) state and learn their own hidden features. One network
    is the critic (evaluation network), the other the actor (action network).
    Both are two-layer: input -> tanh hidden -> output.

Update rules (with eligibility traces, as in the ASE/ACE these nets replace)
    V(s)      = critic(s)                          value prediction
    p(s)      = sigmoid(actor(s))                  P(action = right)
    rhat      = r + gamma * V(s') - V(s)           (V(s') = 0 on failure)
    e_c      <- gamma * lambda * e_c + dV/dw                   critic trace
    e_a      <- gamma * lambda * e_a + (a - p) * dz/dw         actor trace
                                                   ((a - p) dz/dw = grad log pi(a|s))
    critic   += lr_c * rhat * e_c                  TD(lambda), semi-gradient
    actor    += lr_a * rhat * e_a

Implementation notes
    Pure numpy; gradients are written out by hand for the two-layer nets.
    Anderson used gamma = 0.9, five hidden units, and different step sizes for
    hidden and output layers. Here gamma matches the rest of the repository
    (0.99), the hidden layer is wider, and rewards are scaled by reward_scale
    inside the agent so the critic's targets are O(1); positive scaling does
    not change the optimal policy. See __init__ for why the critic's output
    bias is initialized to r/(1-gamma).
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import BaseAgent, normalize_obs  # noqa: E402

def _sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


class _TwoLayerNet:
    """in -> tanh(hidden) -> linear out (scalar). Hand-written forward/backward."""

    def __init__(self, n_in, n_hidden, rng, scale=0.1):
        self.W1 = rng.normal(0.0, scale, size=(n_hidden, n_in))
        self.b1 = np.zeros(n_hidden)
        self.W2 = rng.normal(0.0, scale, size=(n_hidden,))
        self.b2 = 0.0
        self.reset_traces()

    def forward(self, x):
        h = np.tanh(self.W1 @ x + self.b1)
        return float(self.W2 @ h + self.b2), h

    def reset_traces(self):
        self.eW1 = np.zeros_like(self.W1)
        self.eb1 = np.zeros_like(self.b1)
        self.eW2 = np.zeros_like(self.W2)
        self.eb2 = 0.0

    def accumulate(self, x, h, g, decay):
        """e <- decay * e + g * d(out)/d(params)."""
        dh = g * self.W2 * (1.0 - h**2)
        self.eW2 = decay * self.eW2 + g * h
        self.eb2 = decay * self.eb2 + g
        self.eW1 = decay * self.eW1 + np.outer(dh, x)
        self.eb1 = decay * self.eb1 + dh

    def apply(self, delta, lr):
        """params += lr * delta * e."""
        self.W2 += lr * delta * self.eW2
        self.b2 += lr * delta * self.eb2
        self.W1 += lr * delta * self.eW1
        self.b1 += lr * delta * self.eb1

    def grad_step(self, x, h, g, lr):
        """One-step (no trace) move along g * d(out)/d(params); used in tests."""
        dh = g * self.W2 * (1.0 - h**2)
        self.W2 += lr * g * h
        self.b2 += lr * g
        self.W1 += lr * np.outer(dh, x)
        self.b1 += lr * dh

    def params(self, prefix):
        return {f"{prefix}W1": self.W1, f"{prefix}b1": self.b1,
                f"{prefix}W2": self.W2, f"{prefix}b2": np.array(self.b2)}

    def load(self, d, prefix):
        self.W1 = np.array(d[f"{prefix}W1"], dtype=np.float64)
        self.b1 = np.array(d[f"{prefix}b1"], dtype=np.float64)
        self.W2 = np.array(d[f"{prefix}W2"], dtype=np.float64)
        self.b2 = float(d[f"{prefix}b2"])


class ActorCriticBackpropAgent(BaseAgent):
    name = "1986_actor_critic_backprop"

    def __init__(self, hidden=16, lr_actor=0.1, lr_critic=0.1, gamma=0.99, lam=0.8,
                 reward_scale=0.01, seed=None):
        super().__init__(seed)
        self.hidden, self.lr_actor, self.lr_critic, self.gamma = hidden, lr_actor, lr_critic, gamma
        self.lam, self.reward_scale = lam, reward_scale
        self.critic = _TwoLayerNet(4, hidden, self.rng)
        self.actor = _TwoLayerNet(4, hidden, self.rng)
        # Start the critic at the value of a state that never fails, r/(1-gamma).
        # With +1-per-step reward an all-zero critic makes every early TD error
        # positive, which reinforces whatever action was taken and collapses the
        # policy before the critic can learn. Initialized this way, TD errors are
        # ~0 on ordinary steps and strongly negative at failures, which is the
        # signal the 1983/1986 papers' -1 failure reward provided directly.
        self.critic.b2 = reward_scale / (1.0 - gamma)
        self._last_delta = 0.0

    # ---- policy ----------------------------------------------------------- #
    def act(self, obs):
        z, _ = self.actor.forward(normalize_obs(obs))
        p = _sigmoid(z)
        if self.frozen:
            return int(p > 0.5) if p != 0.5 else self._tie_break()
        return int(self.rng.random() < p)

    # ---- learning --------------------------------------------------------- #
    def _learn(self, obs, action, reward, next_obs, terminated):
        x = normalize_obs(obs)
        r = reward * self.reward_scale

        v, h_c = self.critic.forward(x)
        v_next = 0.0 if terminated else self.critic.forward(normalize_obs(next_obs))[0]
        delta = r + self.gamma * v_next - v
        self._last_delta = delta

        decay = self.gamma * self.lam
        # critic: TD(lambda) with accumulating traces on the network parameters
        self.critic.accumulate(x, h_c, 1.0, decay)
        self.critic.apply(delta, self.lr_critic)

        # actor: trace of grad log pi(a|s); for a Bernoulli(sigmoid(z)) policy,
        # d log pi / dz = a - p
        z, h_a = self.actor.forward(x)
        p = _sigmoid(z)
        self.actor.accumulate(x, h_a, action - p, decay)
        self.actor.apply(delta, self.lr_actor)

    def _end_episode(self):
        self.critic.reset_traces()
        self.actor.reset_traces()

    # ---- bookkeeping ------------------------------------------------------ #
    def stats(self):
        return {"td_err": float(self._last_delta)}

    def hparams(self):
        return dict(hidden=self.hidden, lr_actor=self.lr_actor, lr_critic=self.lr_critic,
                    gamma=self.gamma, lam=self.lam, reward_scale=self.reward_scale)

    def state_dict(self):
        return {**self.critic.params("critic_"), **self.actor.params("actor_")}

    def load_state_dict(self, d):
        self.critic.load(d, "critic_")
        self.actor.load(d, "actor_")


Agent = ActorCriticBackpropAgent
