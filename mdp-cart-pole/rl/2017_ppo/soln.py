"""
2017: Proximal Policy Optimization (Schulman et al.), the clipped surrogate.

Reference
    J. Schulman, F. Wolski, P. Dhariwal, A. Radford, O. Klimov, "Proximal
    Policy Optimization Algorithms", arXiv 1707.06347, 2017.
    https://arxiv.org/abs/1707.06347

What changed from TRPO (2015)
    TRPO keeps each policy update inside a trust region by solving a
    constrained problem: a conjugate-gradient solve against the Fisher matrix
    plus a backtracking line search on the KL divergence, once per batch. PPO
    gets the same effect from a loss function. The probability ratio
    rho = pi_new(a|s) / pi_old(a|s) is clipped to [1 - eps, 1 + eps] inside the
    surrogate objective, so the gradient vanishes once a sample has moved the
    policy far enough in the direction its advantage points. That removes the
    second-order machinery entirely and lets the same batch be reused for
    several epochs of ordinary minibatch Adam, which TRPO cannot do safely.
    The result is simpler, cheaper per update and less sensitive to its few
    hyperparameters, which is why it became the default policy-gradient method
    and the canonical first example on Gymnasium's CartPole-v1.

Algorithm (per batch of `batch_steps` transitions)
    V(s') for every stored step                                (no gradient)
    delta_t = r_t + gamma * (1 - terminated_t) * V(s'_t) - V(s_t)
    A_t     = delta_t + gamma * lam * (1 - done_t) * A_{t+1}    (GAE, reset at episode ends)
    R_t     = A_t + V(s_t);  A normalized to zero mean, unit std
    repeat `epochs` times over shuffled minibatches:
        rho   = exp(log pi(a|s) - log pi_old(a|s))
        L_pi  = -mean( min(rho * A, clip(rho, 1-eps, 1+eps) * A) )
        L_v   = mse(V(s), R)
        loss  = L_pi + vf_coef * L_v - ent_coef * entropy
        Adam step on policy and value networks, gradient norm clipped
    discard the batch (on-policy: data from the old policy is not reused
    beyond these epochs)
"""

import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common.deep import DEVICE, TorchAgent, mlp, obs_tensor  # noqa: E402
from common.features import normalize_obs  # noqa: E402


class PPOAgent(TorchAgent):
    name = "2017_ppo"
    supports_wide_angles = True  # reads the raw scaled state

    def __init__(self, hidden=64, lr=3e-4, gamma=0.99, lam=0.95, batch_steps=2048, minibatch=64, epochs=10,
                 clip=0.2, ent_coef=0.0, vf_coef=0.5, max_grad_norm=0.5, seed=None):
        super().__init__(seed)
        self.hidden, self.lr, self.gamma, self.lam = hidden, lr, gamma, lam
        self.batch_steps, self.minibatch, self.epochs = batch_steps, minibatch, epochs
        self.clip, self.ent_coef, self.vf_coef, self.max_grad_norm = clip, ent_coef, vf_coef, max_grad_norm
        self.pi = mlp([4, hidden, hidden, 2], nn.Tanh)
        self.vf = mlp([4, hidden, hidden, 1], nn.Tanh)
        self.register(pi=self.pi, vf=self.vf)
        self.opt = torch.optim.Adam(list(self.pi.parameters()) + list(self.vf.parameters()), lr=lr)
        self._reset_rollout()
        self._last = None  # (logp, value) recorded by act() for the following _learn()
        self._last_kl = 0.0
        self._last_clipfrac = 0.0
        self.updates = 0

    def _reset_rollout(self):
        self._obs, self._act, self._logp, self._rew = [], [], [], []
        self._val, self._term, self._next_obs, self._done = [], [], [], []

    # ---- policy ----------------------------------------------------------- #
    def act(self, obs):
        x = obs_tensor(obs)
        with torch.no_grad():
            logits = self.pi(x)
            logp_all = F.log_softmax(logits, dim=-1)
        if self.frozen:
            if logits[0] == logits[1]:
                return self._tie_break()
            return int(torch.argmax(logits))
        probs = torch.exp(logp_all).cpu().numpy().astype(np.float64)
        probs /= probs.sum()
        a = int(self.rng.choice(2, p=probs))
        with torch.no_grad():
            v = float(self.vf(x))
        self._last = (float(logp_all[a]), v)
        return a

    # ---- rollout collection ---------------------------------------------- #
    def _learn(self, obs, action, reward, next_obs, terminated):
        if self._last is None:  # learn() without a preceding act(): recompute what act() would have stored
            x = obs_tensor(obs)
            with torch.no_grad():
                self._last = (float(F.log_softmax(self.pi(x), dim=-1)[int(action)]), float(self.vf(x)))
        logp, v = self._last
        self._last = None
        self._obs.append(normalize_obs(obs))
        self._act.append(int(action))
        self._logp.append(logp)
        self._rew.append(float(reward))
        self._val.append(v)
        self._term.append(float(terminated))
        self._next_obs.append(normalize_obs(next_obs))
        self._done.append(0.0)
        if len(self._obs) >= self.batch_steps:
            self._update()

    def _end_episode(self):
        if self._done:
            self._done[-1] = 1.0  # episode boundary (termination or truncation)

    # ---- PPO update ------------------------------------------------------- #
    def _update(self):
        obs = torch.as_tensor(np.array(self._obs), dtype=torch.float32, device=DEVICE)
        next_obs = torch.as_tensor(np.array(self._next_obs), dtype=torch.float32, device=DEVICE)
        act = torch.as_tensor(self._act, dtype=torch.long, device=DEVICE)
        logp_old = torch.as_tensor(self._logp, dtype=torch.float32, device=DEVICE)
        rew = np.array(self._rew, dtype=np.float64)
        val = np.array(self._val, dtype=np.float64)
        term = np.array(self._term, dtype=np.float64)
        done = np.array(self._done, dtype=np.float64)
        done[-1] = 1.0  # the batch ends here; the last step's successor is bootstrapped through V(s') below

        with torch.no_grad():
            v_next = self.vf(next_obs).squeeze(1).cpu().numpy().astype(np.float64)
        deltas = rew + self.gamma * (1.0 - term) * v_next - val
        adv = np.zeros_like(deltas)
        running = 0.0
        for t in range(len(deltas) - 1, -1, -1):
            running = deltas[t] + self.gamma * self.lam * (1.0 - done[t]) * running
            adv[t] = running
        ret = torch.as_tensor(adv + val, dtype=torch.float32, device=DEVICE)
        adv = torch.as_tensor((adv - adv.mean()) / (adv.std() + 1e-8), dtype=torch.float32, device=DEVICE)

        n = len(self._obs)
        kls, clipfracs = [], []
        for _ in range(self.epochs):
            perm = self.rng.permutation(n)
            for start in range(0, n, self.minibatch):
                idx = torch.as_tensor(perm[start:start + self.minibatch], dtype=torch.long, device=DEVICE)
                logits = self.pi(obs[idx])
                logp_all = F.log_softmax(logits, dim=-1)
                logp = logp_all.gather(1, act[idx].unsqueeze(1)).squeeze(1)
                ratio = torch.exp(logp - logp_old[idx])
                a = adv[idx]
                pi_loss = -torch.min(ratio * a, torch.clamp(ratio, 1.0 - self.clip, 1.0 + self.clip) * a).mean()
                v_loss = F.mse_loss(self.vf(obs[idx]).squeeze(1), ret[idx])
                entropy = -(torch.exp(logp_all) * logp_all).sum(dim=1).mean()
                loss = pi_loss + self.vf_coef * v_loss - self.ent_coef * entropy
                self.opt.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(list(self.pi.parameters()) + list(self.vf.parameters()), self.max_grad_norm)
                self.opt.step()
                with torch.no_grad():
                    kls.append(float((logp_old[idx] - logp).mean()))
                    clipfracs.append(float((torch.abs(ratio - 1.0) > self.clip).float().mean()))
        self._last_kl = float(np.mean(kls))
        self._last_clipfrac = float(np.mean(clipfracs))
        self.updates += 1
        self._reset_rollout()

    # ---- bookkeeping ------------------------------------------------------ #
    def stats(self):
        return {"kl": self._last_kl, "clipfrac": self._last_clipfrac}

    def hparams(self):
        return dict(hidden=self.hidden, lr=self.lr, gamma=self.gamma, lam=self.lam, batch_steps=self.batch_steps,
                    minibatch=self.minibatch, epochs=self.epochs, clip=self.clip, ent_coef=self.ent_coef,
                    vf_coef=self.vf_coef, max_grad_norm=self.max_grad_norm)


Agent = PPOAgent
