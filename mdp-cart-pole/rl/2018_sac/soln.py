"""
2018: Soft Actor-Critic (Haarnoja et al.), maximum-entropy off-policy actor-critic.

Reference
    T. Haarnoja, A. Zhou, P. Abbeel, S. Levine, "Soft Actor-Critic: Off-Policy
    Maximum Entropy Deep Reinforcement Learning with a Stochastic Actor",
    ICML 2018.   https://arxiv.org/abs/1801.01290
    T. Haarnoja et al., "Soft Actor-Critic Algorithms and Applications", arXiv
    1812.05905, 2018 (automatic temperature tuning, used here).

What changed from DDPG (2015)
    DDPG's deterministic actor has no exploration of its own (noise is bolted
    on) and its single critic overestimates. SAC changes the objective:

        J(pi) = sum_t E[ r_t + alpha * H(pi(. | s_t)) ],

    reward plus a bonus for policy entropy, weighted by a temperature alpha.
    That gives
      * a stochastic actor, a tanh-squashed Gaussian, whose spread is part of
        what is optimized: it explores where uncertain and commits where sure;
      * a soft Bellman target that includes the entropy of the next action;
      * twin critics Q1, Q2 with the minimum used in every target and in the
        actor loss, against the maximization bias Thrun and Schwartz described
        in 1993 (and Fujimoto et al. formalized as TD3 in 2018);
      * alpha itself learned by gradient descent so that the policy entropy
        stays near a target value (-|A| = -1 here), removing the one knob SAC
        was otherwise sensitive to.
    The result is the off-policy continuous-control method that works out of
    the box across tasks where DDPG needs per-task tuning.

Algorithm (one update per environment step after `learning_starts`)
    sample minibatch (s, a, r, s', term) from the replay buffer
    a' ~ pi(. | s'),  y = r + gamma * (1 - term) * ( min(Q1t, Q2t)(s', a') - alpha * log pi(a' | s') )
    critic loss    = mse(Q1(s,a), y) + mse(Q2(s,a), y)
    a~ ~ pi(. | s) by reparameterization,  actor loss = mean( alpha * log pi(a~ | s) - min(Q1, Q2)(s, a~) )
    alpha loss     = mean( -log_alpha * ( log pi(a~ | s) + target_entropy ) )   (stop-gradient inside)
    soft-update Q1t, Q2t toward Q1, Q2 with tau
"""

import math
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common.deep import ReplayBuffer, TorchAgent, hard_update, mlp, obs_tensor, soft_update  # noqa: E402
from common.features import normalize_obs  # noqa: E402

LOG_STD_MIN, LOG_STD_MAX = -5.0, 2.0


class _LogAlpha(nn.Module):
    """Holds the learnable log-temperature so it is saved with the other parameters."""

    def __init__(self, init_alpha):
        super().__init__()
        self.log_alpha = nn.Parameter(torch.tensor(math.log(init_alpha), dtype=torch.float32))

    @property
    def alpha(self):
        return self.log_alpha.exp()


class SACAgent(TorchAgent):
    name = "2018_sac"
    continuous_actions = True
    supports_wide_angles = True

    def __init__(self, hidden=64, lr=3e-4, gamma=0.99, tau=0.005, batch_size=128, buffer_size=100000,
                 learning_starts=1000, init_alpha=0.2, target_entropy=-1.0, reward_scale=0.1, seed=None):
        super().__init__(seed)
        self.hidden, self.lr, self.gamma, self.tau = hidden, lr, gamma, tau
        self.batch_size, self.buffer_size, self.learning_starts = batch_size, buffer_size, learning_starts
        self.init_alpha, self.target_entropy, self.reward_scale = init_alpha, target_entropy, reward_scale

        self.actor = mlp([4, hidden, hidden, 2], nn.ReLU)          # -> (mean, log_std)
        self.q1 = mlp([5, hidden, hidden, 1], nn.ReLU)
        self.q2 = mlp([5, hidden, hidden, 1], nn.ReLU)
        self.q1_target = mlp([5, hidden, hidden, 1], nn.ReLU)
        self.q2_target = mlp([5, hidden, hidden, 1], nn.ReLU)
        hard_update(self.q1_target, self.q1)
        hard_update(self.q2_target, self.q2)
        self.temperature = _LogAlpha(init_alpha)
        self.register(actor=self.actor, q1=self.q1, q2=self.q2, q1_target=self.q1_target,
                      q2_target=self.q2_target, temperature=self.temperature)

        self.opt_actor = torch.optim.Adam(self.actor.parameters(), lr=lr)
        self.opt_critic = torch.optim.Adam(list(self.q1.parameters()) + list(self.q2.parameters()), lr=lr)
        self.opt_alpha = torch.optim.Adam(self.temperature.parameters(), lr=lr)
        self.buf = ReplayBuffer(buffer_size)
        self._last_critic_loss = 0.0

    # ---- squashed Gaussian policy ---------------------------------------- #
    def _dist(self, s):
        out = self.actor(s)
        mean, log_std = out[..., 0], out[..., 1].clamp(LOG_STD_MIN, LOG_STD_MAX)
        return mean, log_std

    def _sample(self, s):
        """Reparameterized action in [-1, 1] and its log-density under the squashed Gaussian."""
        mean, log_std = self._dist(s)
        std = log_std.exp()
        eps = self.randn(tuple(mean.shape))  # works for 0-d (single state) and (B,) batches
        pre = mean + std * eps
        a = torch.tanh(pre)
        logp = -0.5 * eps**2 - log_std - 0.5 * math.log(2 * math.pi)    # Normal log-density of pre
        logp = logp - torch.log(1.0 - a**2 + 1e-6)                       # tanh change of variables
        return a, logp

    def _q(self, net, s, a):
        return net(torch.cat([s, a.unsqueeze(-1)], dim=-1)).squeeze(-1)

    # ---- policy ----------------------------------------------------------- #
    def act(self, obs):
        s = obs_tensor(obs)
        with torch.no_grad():
            if self.frozen:
                mean, _ = self._dist(s)
                return float(torch.tanh(mean))
            a, _ = self._sample(s)
        return float(a)

    # ---- learning --------------------------------------------------------- #
    def _learn(self, obs, action, reward, next_obs, terminated):
        self.buf.add(normalize_obs(obs), action, reward * self.reward_scale, normalize_obs(next_obs), terminated)
        if len(self.buf) < max(self.learning_starts, self.batch_size):
            return
        s, a, r, s2, term = self.buf.sample(self.batch_size, self.rng)
        alpha = self.temperature.alpha.detach()

        # critics: soft Bellman target with the entropy of the next action
        with torch.no_grad():
            a2, logp2 = self._sample(s2)
            q_next = torch.min(self._q(self.q1_target, s2, a2), self._q(self.q2_target, s2, a2))
            y = r + self.gamma * (1.0 - term) * (q_next - alpha * logp2)
        critic_loss = F.mse_loss(self._q(self.q1, s, a), y) + F.mse_loss(self._q(self.q2, s, a), y)
        self.opt_critic.zero_grad()
        critic_loss.backward()
        self.opt_critic.step()

        # actor: maximize soft value of its own (reparameterized) action
        a_new, logp = self._sample(s)
        q_new = torch.min(self._q(self.q1, s, a_new), self._q(self.q2, s, a_new))
        actor_loss = (alpha * logp - q_new).mean()
        self.opt_actor.zero_grad()
        actor_loss.backward()
        self.opt_actor.step()

        # temperature: keep policy entropy near the target
        alpha_loss = -(self.temperature.log_alpha * (logp.detach() + self.target_entropy)).mean()
        self.opt_alpha.zero_grad()
        alpha_loss.backward()
        self.opt_alpha.step()

        soft_update(self.q1_target, self.q1, self.tau)
        soft_update(self.q2_target, self.q2, self.tau)
        self._last_critic_loss = critic_loss.item()

    # ---- bookkeeping ------------------------------------------------------ #
    def stats(self):
        return {"alpha": self.temperature.alpha.item(), "critic_loss": self._last_critic_loss}

    def hparams(self):
        return dict(hidden=self.hidden, lr=self.lr, gamma=self.gamma, tau=self.tau, batch_size=self.batch_size,
                    buffer_size=self.buffer_size, learning_starts=self.learning_starts, init_alpha=self.init_alpha,
                    target_entropy=self.target_entropy, reward_scale=self.reward_scale)


Agent = SACAgent
