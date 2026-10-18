"""
1999: Gaskett, Wettergreen & Zelinsky -- Q-learning in continuous state and
action spaces with a wire-fitted neural network and advantage learning.

Reference
    C. Gaskett, D. Wettergreen, A. Zelinsky, "Q-Learning in Continuous State
    and Action Spaces", Proc. 12th Australian Joint Conference on Artificial
    Intelligence (AI'99), LNCS 1747, 1999.
    https://users.cecs.anu.edu.au/~rsl/rsl_papers/99ai.kambara.pdf
    Wire fitting:        L. C. Baird & A. H. Klopf, "Reinforcement learning with
                         high-dimensional continuous actions", Wright Lab TR, 1993.
    Advantage learning:  L. C. Baird, "Advantage updating", Wright Lab TR, 1993;
                         M. E. Harmon & L. C. Baird, "Multi-player residual
                         advantage learning with general function approximation",
                         Wright Lab TR, 1996.

What changed from 1989/1992
    Every earlier solution chooses between two fixed pushes. Here the action is
    a continuous force u in [-1, 1] (times 10 N) and the agent learns a
    Q-function over that continuum without ever discretizing it. The environment
    is run in continuous mode (CartPoleEnv(continuous=True)); the cart-pole system, reward,
    thresholds and start distribution are unchanged.

Architecture: wire-fitted neural network (WFNN)
    A single MLP maps the state to n "wires", each an action u_i(s) in [-1, 1]
    and a value q_i(s). Wire fitting interpolates them into a Q-function over
    all actions,

        d_i(u) = |u - u_i|^2 + c * (q_max - q_i) + eps
        Q(s, u) = sum_i q_i / d_i  /  sum_i 1 / d_i ,

    whose maximum over u is always at the wire with the largest q. So the
    greedy continuous action is read off the network in closed form: no inner
    optimization, no action grid. Q-learning targets are backpropagated through
    the interpolator to the wire outputs and then through the network.

Advantage learning
    The paper adopts Baird's advantage learning to sharpen the differences
    between actions, which are otherwise tiny relative to the values themselves
    (1 vs 100 here). The target for the taken action is

        y = A_max(s) + ( r + gamma * A_max(s') - A_max(s) ) / k,     0 < k <= 1,

    which is ordinary Q-learning when k = 1 and scales up action differences
    by 1/k when k < 1. The greedy policy is unchanged; only learnability is.

Other choices
    * Exploration is Gaussian noise on the greedy action, decayed per episode.
    * Each real step also replays a few stored transitions (Lin 1992); the paper
      likewise reuses past experience. The replayed transitions are updated as
      one minibatch (summed gradients) rather than one after another; on this
      tiny network that is about five times cheaper per transition and, if
      anything, steadier.
    * Rewards are scaled by reward_scale so values are O(1), as in the 1986
      solution; the optimal policy is invariant to positive scaling.
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import BaseAgent, normalize_obs  # noqa: E402


class _WireNet:
    """MLP: state(4) -> tanh(hidden) -> [n wire actions (tanh), n wire values (linear)]."""

    def __init__(self, n_wires, hidden, rng, scale=0.1):
        self.n = n_wires
        self.W1 = rng.normal(0.0, scale, size=(hidden, 4))
        self.b1 = np.zeros(hidden)
        self.W2 = rng.normal(0.0, scale, size=(2 * n_wires, hidden))
        self.b2 = np.zeros(2 * n_wires)
        # start the wires spread across the action range instead of all at 0
        self.b2[:n_wires] = np.arctanh(np.linspace(-0.8, 0.8, n_wires))

    def forward(self, x):
        h = np.tanh(self.W1 @ x + self.b1)
        z = self.W2 @ h + self.b2
        u = np.tanh(z[: self.n])
        q = z[self.n :]
        return u, q, h

    def backward(self, x, h, u, g_u, g_q, lr):
        """Ascend along g_u . du/dparams + g_q . dq/dparams."""
        g_z = np.concatenate([g_u * (1.0 - u**2), g_q])
        dh = (self.W2.T @ g_z) * (1.0 - h**2)
        self.W2 += lr * np.outer(g_z, h)
        self.b2 += lr * g_z
        self.W1 += lr * np.outer(dh, x)
        self.b1 += lr * dh

    def forward_batch(self, X):
        """X: (B, 4) -> U (B, n), Q (B, n), H (B, hidden)."""
        H = np.tanh(X @ self.W1.T + self.b1)
        Z = H @ self.W2.T + self.b2
        return np.tanh(Z[:, : self.n]), Z[:, self.n :], H

    def backward_batch(self, X, H, U, G_u, G_q, lr):
        """Summed over the batch, so B samples move the weights as B sequential steps would (to first order)."""
        G_z = np.concatenate([G_u * (1.0 - U**2), G_q], axis=1)
        dH = (G_z @ self.W2) * (1.0 - H**2)
        self.W2 += lr * G_z.T @ H
        self.b2 += lr * G_z.sum(axis=0)
        self.W1 += lr * dH.T @ X
        self.b1 += lr * dH.sum(axis=0)

    def params(self):
        return {"W1": self.W1, "b1": self.b1, "W2": self.W2, "b2": self.b2}

    def load(self, d):
        self.W1, self.b1 = np.array(d["W1"], dtype=np.float64), np.array(d["b1"], dtype=np.float64)
        self.W2, self.b2 = np.array(d["W2"], dtype=np.float64), np.array(d["b2"], dtype=np.float64)


class WireFittedQAgent(BaseAgent):
    name = "1999_qlearning_continuous"
    supports_wide_angles = True  # reads the raw scaled state; no 12-degree decoder or grid
    continuous_actions = True  # main.py runs the environment in continuous mode

    def __init__(self, n_wires=5, hidden=32, lr=0.01, gamma=0.99, advantage_k=0.5,
                 smoothing_c=1.0, smoothing_eps=0.3, sigma=0.5, sigma_min=0.05, sigma_decay=0.998,
                 replay=8, buffer_size=20000, reward_scale=0.01, max_grad_norm=1.0,
                 batched_replay=True, seed=None):
        super().__init__(seed)
        self.n_wires, self.hidden, self.lr, self.gamma = n_wires, hidden, lr, gamma
        self.advantage_k, self.smoothing_c, self.eps = advantage_k, smoothing_c, smoothing_eps
        self.sigma, self.sigma_min, self.sigma_decay = sigma, sigma_min, sigma_decay
        self.replay, self.buffer_size, self.reward_scale = replay, buffer_size, reward_scale
        self.max_grad_norm, self.batched_replay = max_grad_norm, bool(batched_replay)
        self.net = _WireNet(n_wires, hidden, self.rng)
        # Start every wire's value at r/(1-gamma), the value of a state that never
        # fails, for the same reason as the 1986 critic: otherwise every early TD
        # error is positive and the values drift before failures are ever seen.
        self.net.b2[n_wires:] = reward_scale / (1.0 - gamma)
        # replay buffer as preallocated arrays (ring): x, u, r, x_next, terminated
        self._bx = np.zeros((buffer_size, 4))
        self._bu = np.zeros(buffer_size)
        self._br = np.zeros(buffer_size)
        self._bxn = np.zeros((buffer_size, 4))
        self._bt = np.zeros(buffer_size, dtype=bool)
        self._bn = 0      # number of stored transitions (<= buffer_size)
        self._bpos = 0    # next write position
        self._last_err = 0.0

    # ---- wire fitting --------------------------------------------------- #
    def _interpolate(self, u, wires_u, wires_q):
        """Q(s, u) from the wires, plus dQ/du_i and dQ/dq_i (q_max held fixed)."""
        q_max = wires_q.max()
        d = (u - wires_u) ** 2 + self.smoothing_c * (q_max - wires_q) + self.eps
        w = 1.0 / d
        D = w.sum()
        Q = float((w * wires_q).sum() / D)
        dw_dq = self.smoothing_c / d**2
        dw_du = 2.0 * (u - wires_u) / d**2
        dQ_dq = w / D + (wires_q - Q) / D * dw_dq
        dQ_du = (wires_q - Q) / D * dw_du
        return Q, dQ_du, dQ_dq

    def _interpolate_batch(self, U, WU, WQ):
        """Batched _interpolate: U (B,), WU/WQ (B, n) -> Q (B,), dQ/dU_i (B, n), dQ/dQ_i (B, n)."""
        q_max = WQ.max(axis=1, keepdims=True)
        diff = U[:, None] - WU
        d = diff**2 + self.smoothing_c * (q_max - WQ) + self.eps
        w = 1.0 / d
        D = w.sum(axis=1, keepdims=True)
        Q = (w * WQ).sum(axis=1) / D[:, 0]
        dw_dq = self.smoothing_c / d**2
        dw_du = 2.0 * diff / d**2
        dQ_dq = w / D + (WQ - Q[:, None]) / D * dw_dq
        dQ_du = (WQ - Q[:, None]) / D * dw_du
        return Q, dQ_du, dQ_dq

    def _update_batch(self, X, U, R, Xn, T):
        """One minibatch step of advantage learning over B transitions."""
        WU, WQ, H = self.net.forward_batch(X)
        Q, dQ_du, dQ_dq = self._interpolate_batch(U, WU, WQ)
        a_max_s = WQ.max(axis=1)
        a_max_next = self.net.forward_batch(Xn)[1].max(axis=1)
        a_max_next[T] = 0.0
        target = a_max_s + (R + self.gamma * a_max_next - a_max_s) / self.advantage_k
        err = target - Q
        G_u, G_q = err[:, None] * dQ_du, err[:, None] * dQ_dq
        if self.max_grad_norm:  # clip each sample's gradient separately, as the sequential version did
            norm = np.sqrt((G_u**2).sum(axis=1) + (G_q**2).sum(axis=1))
            scale = np.minimum(1.0, self.max_grad_norm / np.maximum(norm, 1e-12))
            G_u, G_q = G_u * scale[:, None], G_q * scale[:, None]
        self.net.backward_batch(X, H, WU, G_u, G_q, self.lr)
        return err

    def _greedy(self, x):
        u, q, _ = self.net.forward(x)
        return float(u[int(np.argmax(q))]), float(q.max())

    # ---- policy ----------------------------------------------------------- #
    def act(self, obs):
        u_star, _ = self._greedy(normalize_obs(obs))
        if self.frozen:
            return u_star
        return float(np.clip(u_star + self.rng.normal(0.0, self.sigma), -1.0, 1.0))

    # ---- learning --------------------------------------------------------- #
    def _update(self, x, u, r, x_next, terminated):
        wires_u, wires_q, h = self.net.forward(x)
        Q, dQ_du, dQ_dq = self._interpolate(u, wires_u, wires_q)
        a_max_s = float(wires_q.max())
        a_max_next = 0.0 if terminated else self._greedy(x_next)[1]
        target = a_max_s + (r + self.gamma * a_max_next - a_max_s) / self.advantage_k
        err = target - Q
        g_u, g_q = err * dQ_du, err * dQ_dq
        norm = float(np.sqrt((g_u**2).sum() + (g_q**2).sum()))
        if self.max_grad_norm and norm > self.max_grad_norm:  # keep one bad sample from wrecking the net
            g_u, g_q = g_u * (self.max_grad_norm / norm), g_q * (self.max_grad_norm / norm)
        self.net.backward(x, h, wires_u, g_u, g_q, self.lr)
        return err

    def _learn(self, obs, action, reward, next_obs, terminated):
        x, x_next = normalize_obs(obs), normalize_obs(next_obs)
        u, r = float(action), reward * self.reward_scale
        self._last_err = self._update(x, u, r, x_next, terminated)   # the real transition
        i = self._bpos                                                # store it
        self._bx[i], self._bu[i], self._br[i], self._bxn[i], self._bt[i] = x, u, r, x_next, terminated
        self._bpos = (i + 1) % self.buffer_size
        self._bn = min(self._bn + 1, self.buffer_size)
        if self.replay and self._bn > 1:
            k = self.rng.integers(self._bn, size=self.replay)
            if self.batched_replay:                                   # one minibatch, summed gradients
                self._update_batch(self._bx[k], self._bu[k], self._br[k], self._bxn[k], self._bt[k])
            else:                                                     # one after another, targets refreshed
                for j in k:
                    self._update(self._bx[j], self._bu[j], self._br[j], self._bxn[j], bool(self._bt[j]))

    def _end_episode(self):
        self.sigma = max(self.sigma_min, self.sigma * self.sigma_decay)

    # ---- bookkeeping ------------------------------------------------------ #
    def stats(self):
        return {"sigma": 0.0 if self.frozen else self.sigma, "td_err": float(self._last_err)}

    def hparams(self):
        return dict(n_wires=self.n_wires, hidden=self.hidden, lr=self.lr, gamma=self.gamma,
                    advantage_k=self.advantage_k, smoothing_c=self.smoothing_c, smoothing_eps=self.eps,
                    sigma_min=self.sigma_min, sigma_decay=self.sigma_decay, replay=self.replay,
                    buffer_size=self.buffer_size, reward_scale=self.reward_scale,
                    max_grad_norm=self.max_grad_norm, batched_replay=self.batched_replay)

    def state_dict(self):
        return {**self.net.params(), "sigma": np.array(self.sigma)}

    def load_state_dict(self, d):
        self.net.load(d)
        if "sigma" in d:
            self.sigma = float(d["sigma"])


Agent = WireFittedQAgent
