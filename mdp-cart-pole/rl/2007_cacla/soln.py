"""
2007: Van Hasselt & Wiering -- Continuous Actor Critic Learning Automaton (CACLA).

Reference
    H. van Hasselt, M. A. Wiering, "Reinforcement Learning in Continuous Action
    Spaces", Proc. IEEE Int. Symp. on Approximate Dynamic Programming and
    Reinforcement Learning (ADPRL), pp. 272-279, 2007.
    https://hadovanhasselt.com/wp-content/uploads/2015/12/reinforcement_learning_in_continuous_action_spaces.pdf
    H. van Hasselt, "Reinforcement Learning in Continuous State and Action
    Spaces", in Wiering & van Otterlo (eds.), Reinforcement Learning: State of
    the Art, Springer, 2012. The fuller treatment of the same algorithm.

What changed from 1986 and 1999
    The 1986 actor-critic moves its actor along delta * grad log pi(a|s): the
    size and sign of the TD error both scale the step, and the actor is a
    probability over two pushes. The 1999 agent has no actor; it learns
    Q(s, u) over the continuum with wire fitting and reads off the argmax.
    CACLA keeps the 1986 two-network structure but makes the actor a
    deterministic continuous action Ac(s) in [-1, 1], explores with Gaussian
    noise around it, and updates it as a regression toward the action actually
    taken, ONLY on steps whose TD error is positive:

        delta   = r + gamma * V(s') - V(s)               (V(s') = 0 on failure)
        critic  += lr_c * delta * dV/dw                  TD(0), or TD(lambda) with traces
        IF delta > 0:
            actor += lr_a * (a - Ac(s)) * dAc/dw         move Ac(s) toward a

    Only the sign of delta matters to the actor. A negative delta says the
    action was worse than expected, but moving away from it would be a move
    toward some unknown action that is not necessarily better; so the actor
    stays put and the critic alone records the bad news. The paper shows this
    makes the actor's step size invariant to the scale of the reward and far
    more robust than the magnitude-based alternative (CAC), which on their
    cart pole never learned to balance when negative updates were allowed.

CACLA+Var
    A running variance of the TD error, var <- (1 - beta) var + beta delta^2,
    turns an unusually good outcome into several actor updates: the update is
    repeated ceil(delta / sqrt(var)) times when delta > 0. The paper's cart
    pole learned fastest with this variant. It is a constructor flag here.

Implementation notes
    Pure numpy; two hand-written two-layer tanh networks, as in the 1986
    solution. The paper used 12 hidden sigmoid units, a linear output, learning
    rate 0.01 for both networks and constant Gaussian exploration with
    standard deviation 0.1 on inputs and actions scaled to [-1, 1]. Here the
    actor's output goes through a tanh so it lies in [-1, 1] by construction,
    rewards are scaled by reward_scale so the critic's targets are O(1), and
    the critic's output bias is initialized to r/(1-gamma): with the +1-per-
    step reward an all-zero critic makes every early TD error positive, and
    for CACLA a positive TD error is precisely what triggers an actor update,
    so without this the actor would chase random noise until the critic caught
    up. The paper's task used a -1 failure / +1 otherwise reward, which
    provided the negative signal directly.

    Because the actor learns from the SIGN of delta alone, it learns nothing
    until the critic can tell neighbouring states apart: with a flat critic,
    delta = r - (1-gamma) V > 0 on every non-failure step and the actor just
    regresses toward its own exploration noise. So the critic here is wider
    than the paper's (64 units), its input weights start at unit scale so the
    tanh units already span the state space, and it uses TD(lambda = 0.7)
    traces; the exploration noise is 0.3 rather than 0.1 so that one step's
    action has a visible effect on V(s'). The actor step size stays at the
    paper's 0.01: the actor drifts toward noise at rate lr_actor * sigma per
    step, and larger steps let that drift saturate the tanh output.
"""

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import BaseAgent, normalize_obs  # noqa: E402


class _MLP:
    """in -> tanh(hidden) -> linear scalar out. Hand-written backprop, optional eligibility traces."""

    def __init__(self, n_in, n_hidden, rng, scale_in=1.0, scale_out=0.1):
        # Unit-scale input weights spread the tanh units over the (normalized) state
        # so the critic can tell states apart from the start; see the module docstring.
        self.W1 = rng.normal(0.0, scale_in, size=(n_hidden, n_in))
        self.b1 = np.zeros(n_hidden)
        self.W2 = rng.normal(0.0, scale_out, size=(n_hidden,))
        self.b2 = 0.0
        self.reset_traces()

    def forward(self, x):
        h = np.tanh(self.W1 @ x + self.b1)
        return float(self.W2 @ h + self.b2), h

    def grads(self, x, h, g=1.0):
        """g * d(out)/d(params) as (gW1, gb1, gW2, gb2)."""
        dh = g * self.W2 * (1.0 - h**2)
        return np.outer(dh, x), dh, g * h, g

    def reset_traces(self):
        self.eW1 = np.zeros_like(self.W1)
        self.eb1 = np.zeros_like(self.b1)
        self.eW2 = np.zeros_like(self.W2)
        self.eb2 = 0.0

    def accumulate(self, x, h, decay):
        """e <- decay * e + d(out)/d(params); decay = 0 gives the plain one-step gradient."""
        gW1, gb1, gW2, gb2 = self.grads(x, h)
        self.eW1 = decay * self.eW1 + gW1
        self.eb1 = decay * self.eb1 + gb1
        self.eW2 = decay * self.eW2 + gW2
        self.eb2 = decay * self.eb2 + gb2

    def apply(self, delta, lr):
        """params += lr * delta * e."""
        self.W1 += lr * delta * self.eW1
        self.b1 += lr * delta * self.eb1
        self.W2 += lr * delta * self.eW2
        self.b2 += lr * delta * self.eb2

    def step(self, x, h, g, lr):
        """params += lr * g * d(out)/d(params), no trace."""
        gW1, gb1, gW2, gb2 = self.grads(x, h, g)
        self.W1 += lr * gW1
        self.b1 += lr * gb1
        self.W2 += lr * gW2
        self.b2 += lr * gb2

    def params(self, prefix):
        return {f"{prefix}W1": self.W1, f"{prefix}b1": self.b1,
                f"{prefix}W2": self.W2, f"{prefix}b2": np.array(self.b2)}

    def load(self, d, prefix):
        self.W1 = np.array(d[f"{prefix}W1"], dtype=np.float64)
        self.b1 = np.array(d[f"{prefix}b1"], dtype=np.float64)
        self.W2 = np.array(d[f"{prefix}W2"], dtype=np.float64)
        self.b2 = float(d[f"{prefix}b2"])


class CaclaAgent(BaseAgent):
    name = "2007_cacla"
    supports_wide_angles = True  # reads the raw scaled state; no 12-degree decoder or grid
    continuous_actions = True  # main.py runs the environment in continuous mode

    def __init__(self, hidden=64, lr_actor=0.01, lr_critic=0.01, gamma=0.99, lam=0.7,
                 sigma=0.3, sigma_min=0.3, sigma_decay=1.0, reward_scale=0.01,
                 var=False, var_beta=0.001, var_init=1.0, max_updates=10, seed=None):
        super().__init__(seed)
        self.hidden, self.lr_actor, self.lr_critic, self.gamma, self.lam = hidden, lr_actor, lr_critic, gamma, lam
        self.sigma, self.sigma_min, self.sigma_decay = sigma, sigma_min, sigma_decay
        self.reward_scale, self.use_var = reward_scale, bool(var)
        self.var_beta, self.var_init, self.max_updates = var_beta, var_init, max_updates
        self.critic = _MLP(4, hidden, self.rng)
        self.actor = _MLP(4, hidden, self.rng)
        # Value of a state that never fails, so early TD errors are ~0 rather than
        # all positive (see the module docstring: positive delta drives the actor).
        self.critic.b2 = reward_scale / (1.0 - gamma)
        self.var = float(var_init)  # running variance of delta (CACLA+Var)
        self._last_delta, self._last_updates = 0.0, 0

    # ---- policy ----------------------------------------------------------- #
    def _mean(self, x):
        z, h = self.actor.forward(x)
        return math.tanh(z), h

    def act(self, obs):
        u, _ = self._mean(normalize_obs(obs))
        if self.frozen:
            return float(u)
        return float(np.clip(u + self.rng.normal(0.0, self.sigma), -1.0, 1.0))

    # ---- learning --------------------------------------------------------- #
    def _learn(self, obs, action, reward, next_obs, terminated):
        x = normalize_obs(obs)
        r = reward * self.reward_scale

        # critic: TD(lambda) on V(s); lam = 0 is the paper's TD(0)
        v, h_c = self.critic.forward(x)
        v_next = 0.0 if terminated else self.critic.forward(normalize_obs(next_obs))[0]
        delta = r + self.gamma * v_next - v
        self._last_delta = delta
        self.critic.accumulate(x, h_c, self.gamma * self.lam)
        self.critic.apply(delta, self.lr_critic)

        # actor: only the sign of delta matters; on a positive one, regress Ac(s) toward a
        n = 0
        if delta > 0:
            n = 1
            if self.use_var:
                n = min(self.max_updates, int(math.ceil(delta / math.sqrt(self.var))))
            for _ in range(n):
                u, h_a = self._mean(x)
                self.actor.step(x, h_a, (float(action) - u) * (1.0 - u**2), self.lr_actor)
        if self.use_var:
            self.var += self.var_beta * (delta**2 - self.var)
        self._last_updates = n

    def _end_episode(self):
        self.critic.reset_traces()
        self.sigma = max(self.sigma_min, self.sigma * self.sigma_decay)

    # ---- bookkeeping ------------------------------------------------------ #
    def stats(self):
        return {"td_err": float(self._last_delta), "sigma": 0.0 if self.frozen else float(self.sigma),
                "updates": float(self._last_updates)}

    def hparams(self):
        return dict(hidden=self.hidden, lr_actor=self.lr_actor, lr_critic=self.lr_critic, gamma=self.gamma,
                    lam=self.lam, sigma_min=self.sigma_min, sigma_decay=self.sigma_decay,
                    reward_scale=self.reward_scale, var=self.use_var, var_beta=self.var_beta,
                    var_init=self.var_init, max_updates=self.max_updates)

    def state_dict(self):
        return {**self.critic.params("critic_"), **self.actor.params("actor_"),
                "sigma": np.array(self.sigma), "var": np.array(self.var)}

    def load_state_dict(self, d):
        self.critic.load(d, "critic_")
        self.actor.load(d, "actor_")
        if "sigma" in d:
            self.sigma = float(d["sigma"])
        if "var" in d:
            self.var = float(d["var"])


Agent = CaclaAgent
