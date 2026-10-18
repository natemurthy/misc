"""
2015: Deep Deterministic Policy Gradient (Lillicrap et al.), DQN's stabilizers
applied to a continuous actor-critic.

Reference
    T. P. Lillicrap et al., "Continuous control with deep reinforcement
    learning", arXiv 1509.02971, 2015.   https://arxiv.org/abs/1509.02971
    D. Silver et al., "Deterministic Policy Gradient Algorithms", ICML 2014
    (the gradient theorem DDPG rests on).

What changed from 2011/2013
    NFQCA (2011) already had the structure: a critic Q(s, a) and a deterministic
    actor pi(s) trained to maximize Q(s, pi(s)) on stored data. But it refit both
    networks from scratch on the growing batch every few episodes. DQN (2013)
    showed that a neural Q-function can be trained online if transitions are
    replayed uniformly from a large buffer and the bootstrap target comes from
    a slowly changing copy of the network. DDPG combines the two: NFQCA's
    actor-critic on continuous actions, DQN's replay buffer and target
    networks, with the target networks updated by a slow exponential average
    (soft update) instead of DQN's periodic hard copy. The actor's update is
    the deterministic policy gradient (Silver et al. 2014),

        grad_theta J = E_s[ grad_a Q(s, a)|_{a = pi(s)} * grad_theta pi(s) ],

    which is what NFQCA's actor step computes on a batch; here it is computed
    on a minibatch after every environment step.

Algorithm (per step, once learning_starts transitions are stored)
    store (s, a, r, s', terminal); sample a minibatch
    y = r + gamma * (1 - terminal) * Q'(s', pi'(s'))           target networks
    critic: minimize mean (Q(s, a) - y)^2
    actor:  maximize mean Q(s, pi(s))
    Q' <- tau * Q + (1 - tau) * Q',  pi' <- tau * pi + (1 - tau) * pi'
Exploration is Ornstein-Uhlenbeck noise added to pi(s), as in the paper, with
its scale decayed per episode.
"""

import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common.deep import ReplayBuffer, TorchAgent, hard_update, mlp, obs_tensor, soft_update  # noqa: E402
from common.features import normalize_obs  # noqa: E402


class DDPGAgent(TorchAgent):
    name = "2015_ddpg"
    continuous_actions = True
    supports_wide_angles = True

    def __init__(self, hidden=64, lr_actor=1e-4, lr_critic=1e-3, gamma=0.99, tau=0.005, batch_size=64,
                 buffer_size=50000, learning_starts=1000, ou_theta=0.15, ou_sigma=0.2, sigma_min=0.05,
                 sigma_decay=0.995, reward_scale=0.1, seed=None):
        super().__init__(seed)
        self.hidden, self.lr_actor, self.lr_critic, self.gamma, self.tau = hidden, lr_actor, lr_critic, gamma, tau
        self.batch_size, self.buffer_size, self.learning_starts = batch_size, buffer_size, learning_starts
        self.ou_theta, self.ou_sigma, self.sigma_min, self.sigma_decay = ou_theta, ou_sigma, sigma_min, sigma_decay
        self.reward_scale = reward_scale
        self.sigma = ou_sigma
        self.actor = mlp([4, hidden, hidden, 1], nn.ReLU, output_activation=nn.Tanh)
        self.critic = mlp([5, hidden, hidden, 1], nn.ReLU)
        self.actor_target = mlp([4, hidden, hidden, 1], nn.ReLU, output_activation=nn.Tanh)
        self.critic_target = mlp([5, hidden, hidden, 1], nn.ReLU)
        hard_update(self.actor_target, self.actor)
        hard_update(self.critic_target, self.critic)
        self.register(actor=self.actor, critic=self.critic, actor_target=self.actor_target,
                      critic_target=self.critic_target)
        self.opt_actor = torch.optim.Adam(self.actor.parameters(), lr=lr_actor)
        self.opt_critic = torch.optim.Adam(self.critic.parameters(), lr=lr_critic)
        self.buf = ReplayBuffer(buffer_size)
        self.noise = 0.0  # Ornstein-Uhlenbeck state (one-dimensional action)
        self._last_loss = 0.0

    # ---- policy ----------------------------------------------------------- #
    def act(self, obs):
        with torch.no_grad():
            u = float(self.actor(obs_tensor(obs)))
        if self.frozen:
            return u
        # OU process: dx = theta * (0 - x) dt + sigma dW, with dt = 1 step
        self.noise += self.ou_theta * (0.0 - self.noise) + self.sigma * self.rng.normal()
        return float(np.clip(u + self.noise, -1.0, 1.0))

    # ---- learning --------------------------------------------------------- #
    def _learn(self, obs, action, reward, next_obs, terminated):
        self.buf.add(normalize_obs(obs), action, reward * self.reward_scale, normalize_obs(next_obs), terminated)
        if len(self.buf) < max(self.learning_starts, self.batch_size):
            return
        s, a, r, s2, term = self.buf.sample(self.batch_size, self.rng)
        with torch.no_grad():
            a2 = self.actor_target(s2)
            y = r + self.gamma * (1.0 - term) * self.critic_target(torch.cat([s2, a2], dim=1)).squeeze(1)
        q = self.critic(torch.cat([s, a.unsqueeze(1)], dim=1)).squeeze(1)
        critic_loss = F.mse_loss(q, y)
        self.opt_critic.zero_grad()
        critic_loss.backward()
        self.opt_critic.step()

        actor_loss = -self.critic(torch.cat([s, self.actor(s)], dim=1)).mean()
        self.opt_actor.zero_grad()
        actor_loss.backward()
        self.opt_actor.step()

        soft_update(self.critic_target, self.critic, self.tau)
        soft_update(self.actor_target, self.actor, self.tau)
        self._last_loss = critic_loss.item()

    def _end_episode(self):
        self.noise = 0.0
        self.sigma = max(self.sigma_min, self.sigma * self.sigma_decay)

    # ---- bookkeeping ------------------------------------------------------ #
    def stats(self):
        return {"sigma": 0.0 if self.frozen else self.sigma, "critic_loss": self._last_loss}

    def hparams(self):
        return dict(hidden=self.hidden, lr_actor=self.lr_actor, lr_critic=self.lr_critic, gamma=self.gamma,
                    tau=self.tau, batch_size=self.batch_size, buffer_size=self.buffer_size,
                    learning_starts=self.learning_starts, ou_theta=self.ou_theta, ou_sigma=self.ou_sigma,
                    sigma_min=self.sigma_min, sigma_decay=self.sigma_decay, reward_scale=self.reward_scale)


Agent = DDPGAgent
