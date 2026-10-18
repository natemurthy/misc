"""
2015: Trust Region Policy Optimization (Schulman et al.), policy gradient with a step-size guarantee.

Reference
    J. Schulman, S. Levine, P. Moritz, M. Jordan, P. Abbeel, "Trust Region
    Policy Optimization", ICML 2015, arXiv 1502.05477.
    https://arxiv.org/abs/1502.05477
    S. Kakade, "A Natural Policy Gradient", NIPS 2001 (the natural gradient
    direction TRPO takes).
    J. Schulman et al., "High-Dimensional Continuous Control Using Generalized
    Advantage Estimation", arXiv 1506.02438, 2016 (the advantage estimator
    used here).

What changed from 1992 REINFORCE and the actor-critics
    REINFORCE moves the policy parameters along a noisy gradient with a fixed
    step size; too small and it crawls, too large and one bad batch wrecks the
    policy, with no way back. The 1983 and 1986 actor-critics have the same
    problem with an added critic. TRPO changes the question from "how far in
    parameter space" to "how far in policy space": maximize the surrogate
    objective  E[ pi_new(a|s) / pi_old(a|s) * A(s,a) ]  subject to a bound on
    the mean KL divergence between the old and new policies. Schulman et al.
    prove that a step satisfying such a bound cannot decrease the true return
    by more than a known amount, which is the first monotonic-improvement
    guarantee for a policy gradient method with function approximation.

    In practice the constrained step is a natural gradient (Kakade 2001): the
    update direction is F^{-1} g, where F is the Fisher information matrix of
    the policy (the Hessian of the KL), found by conjugate gradient using
    Fisher-vector products from double backprop, then scaled to hit the KL
    bound exactly and checked with a backtracking line search.

Algorithm (per batch of `batch_steps` steps collected under the current policy)
    A_t   = GAE(gamma, lambda) advantages from a learned value baseline V(s)
    g     = grad_theta  mean_t [ pi_theta(a_t|s_t) / pi_old(a_t|s_t) * A_t ]
    x     = F^{-1} g          by conjugate gradient with Fisher-vector products
    step  = sqrt(2 * max_kl / (x . F x)) * x
    theta <- theta + beta^j * step   for the first j with KL <= max_kl and surrogate improved
    fit V to the empirical returns with Adam
"""

import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn.utils import parameters_to_vector, vector_to_parameters

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common.deep import DEVICE, TorchAgent, mlp, obs_tensor  # noqa: E402
from common.features import normalize_obs  # noqa: E402


class TRPOAgent(TorchAgent):
    name = "2015_trpo"
    supports_wide_angles = True  # reads the raw scaled state; no 12-degree decoder or grid

    def __init__(self, hidden=64, gamma=0.99, lam=0.97, batch_steps=2048, max_kl=0.01, cg_iters=10,
                 cg_damping=0.1, backtrack_iters=10, backtrack_coeff=0.8, vf_lr=1e-3, vf_epochs=10, seed=None):
        super().__init__(seed)
        self.hidden, self.gamma, self.lam, self.batch_steps = hidden, gamma, lam, batch_steps
        self.max_kl, self.cg_iters, self.cg_damping = max_kl, cg_iters, cg_damping
        self.backtrack_iters, self.backtrack_coeff = backtrack_iters, backtrack_coeff
        self.vf_lr, self.vf_epochs = vf_lr, vf_epochs
        self.pi = mlp([4, hidden, hidden, 2], nn.Tanh)
        self.vf = mlp([4, hidden, hidden, 1], nn.Tanh)
        self.register(pi=self.pi, vf=self.vf)
        self.vf_opt = torch.optim.Adam(self.vf.parameters(), lr=vf_lr)
        self._reset_rollout()
        self._last = None  # (logp, value) from the most recent act()
        self._last_kl = 0.0
        self._last_improve = 0.0
        self.updates = 0

    def _reset_rollout(self):
        self.obs_buf, self.act_buf, self.logp_buf, self.rew_buf = [], [], [], []
        self.val_buf, self.term_buf, self.next_obs_buf, self.done_buf = [], [], [], []

    # ---- policy ----------------------------------------------------------- #
    def act(self, obs):
        x = obs_tensor(obs)
        with torch.no_grad():
            logits = self.pi(x)
            if self.frozen:
                if logits[0] == logits[1]:
                    return self._tie_break()
                return int(torch.argmax(logits))
            logp_all = F.log_softmax(logits, dim=-1)
            probs = logp_all.exp().cpu().numpy().astype(np.float64)
            probs /= probs.sum()
            a = int(self.rng.choice(2, p=probs))
            self._last = (float(logp_all[a]), float(self.vf(x)))
        return a

    # ---- rollout collection and trust-region update ----------------------- #
    def _learn(self, obs, action, reward, next_obs, terminated):
        if self._last is None:  # learn() without a preceding act(); evaluate now
            x = obs_tensor(obs)
            with torch.no_grad():
                self._last = (float(F.log_softmax(self.pi(x), dim=-1)[action]), float(self.vf(x)))
        logp, value = self._last
        self._last = None
        self.obs_buf.append(normalize_obs(obs))
        self.act_buf.append(int(action))
        self.logp_buf.append(logp)
        self.rew_buf.append(float(reward))
        self.val_buf.append(value)
        self.term_buf.append(bool(terminated))
        self.next_obs_buf.append(normalize_obs(next_obs))
        self.done_buf.append(bool(terminated))
        if len(self.obs_buf) >= self.batch_steps:
            self.update()

    def _end_episode(self):
        if self.done_buf:
            self.done_buf[-1] = True  # episode boundary, terminated or truncated

    def _advantages(self):
        obs = torch.as_tensor(np.array(self.obs_buf), dtype=torch.float32, device=DEVICE)
        next_obs = torch.as_tensor(np.array(self.next_obs_buf), dtype=torch.float32, device=DEVICE)
        with torch.no_grad():
            v_next = self.vf(next_obs).squeeze(1).cpu().numpy()
        v = np.array(self.val_buf)
        r = np.array(self.rew_buf)
        term = np.array(self.term_buf, dtype=np.float64)
        done = np.array(self.done_buf, dtype=np.float64)
        deltas = r + self.gamma * (1.0 - term) * v_next - v
        adv = np.zeros_like(deltas)
        running = 0.0
        for t in range(len(deltas) - 1, -1, -1):
            running = deltas[t] + self.gamma * self.lam * (1.0 - done[t]) * running
            adv[t] = running
        ret = adv + v
        adv = (adv - adv.mean()) / (adv.std() + 1e-8)
        return obs, torch.as_tensor(adv, dtype=torch.float32, device=DEVICE), torch.as_tensor(ret, dtype=torch.float32, device=DEVICE)

    def _flat_grad(self, y, create_graph=False):
        grads = torch.autograd.grad(y, list(self.pi.parameters()), create_graph=create_graph)
        return torch.cat([g.reshape(-1) for g in grads])

    def update(self):
        obs, adv, ret = self._advantages()
        act = torch.as_tensor(self.act_buf, dtype=torch.long, device=DEVICE)
        logp_old = torch.as_tensor(self.logp_buf, dtype=torch.float32, device=DEVICE)
        with torch.no_grad():
            logits_old = self.pi(obs)
            logp_all_old = F.log_softmax(logits_old, dim=-1)

        def surrogate():
            logp = F.log_softmax(self.pi(obs), dim=-1).gather(1, act.unsqueeze(1)).squeeze(1)
            return (torch.exp(logp - logp_old) * adv).mean()

        def kl():
            logp_all = F.log_softmax(self.pi(obs), dim=-1)
            return (logp_all_old.exp() * (logp_all_old - logp_all)).sum(dim=1).mean()

        def fisher_vector_product(v):
            grad_kl = self._flat_grad(kl(), create_graph=True)
            return self._flat_grad((grad_kl * v).sum()) + self.cg_damping * v

        surr_old = surrogate()
        g = self._flat_grad(surr_old)
        surr_old = surr_old.detach()
        x = self._conjugate_gradient(fisher_vector_product, g)
        step = torch.sqrt(2.0 * self.max_kl / (torch.dot(x, fisher_vector_product(x)) + 1e-8)) * x

        params_old = parameters_to_vector(self.pi.parameters()).detach().clone()
        surr_old = float(surr_old)
        accepted = False
        for j in range(self.backtrack_iters):
            vector_to_parameters(params_old + (self.backtrack_coeff**j) * step, self.pi.parameters())
            with torch.no_grad():
                kl_new, surr_new = float(kl()), float(surrogate())
            if kl_new <= self.max_kl and surr_new > surr_old:
                accepted = True
                self._last_kl, self._last_improve = kl_new, surr_new - surr_old
                break
        if not accepted:
            vector_to_parameters(params_old, self.pi.parameters())
            self._last_kl, self._last_improve = 0.0, 0.0

        for _ in range(self.vf_epochs):  # value baseline fit on the empirical returns
            loss = F.mse_loss(self.vf(obs).squeeze(1), ret)
            self.vf_opt.zero_grad()
            loss.backward()
            self.vf_opt.step()

        self.updates += 1
        self._reset_rollout()

    def _conjugate_gradient(self, Avp, b):
        x = torch.zeros_like(b)
        r = b.clone()
        p = b.clone()
        rdotr = torch.dot(r, r)
        for _ in range(self.cg_iters):
            Ap = Avp(p)
            alpha = rdotr / (torch.dot(p, Ap) + 1e-10)
            x = x + alpha * p
            r = r - alpha * Ap
            new_rdotr = torch.dot(r, r)
            if new_rdotr < 1e-10:
                break
            p = r + (new_rdotr / rdotr) * p
            rdotr = new_rdotr
        return x

    # ---- bookkeeping ------------------------------------------------------ #
    def stats(self):
        return {"kl": self._last_kl, "surr_gain": self._last_improve}

    def hparams(self):
        return dict(hidden=self.hidden, gamma=self.gamma, lam=self.lam, batch_steps=self.batch_steps,
                    max_kl=self.max_kl, cg_iters=self.cg_iters, cg_damping=self.cg_damping,
                    backtrack_iters=self.backtrack_iters, backtrack_coeff=self.backtrack_coeff,
                    vf_lr=self.vf_lr, vf_epochs=self.vf_epochs)


Agent = TRPOAgent
