"""
2011: Neural Fitted Q iteration with Continuous Actions (Hafner and Riedmiller).

Reference
    R. Hafner, M. Riedmiller, "Reinforcement learning in feedback control:
    Challenges and benchmarks from technical process control", Machine Learning
    84:137-169, 2011.   https://doi.org/10.1007/s10994-011-5235-4
    M. Riedmiller, "Neural Fitted Q Iteration - First Experiences with a Data
    Efficient Neural Reinforcement Learning Method", ECML 2005 (the discrete
    NFQ this extends; demonstrated on cart-pole).

What changed from 1999
    Gaskett's agent updated its network after every step on one transition,
    which is where its instability came from. NFQ turns Q-learning into a
    sequence of supervised regression problems: keep every transition seen so
    far, compute the Q-learning target for all of them with the current
    network, then train the network to convergence on that fixed dataset with
    a batch optimizer (Rprop), and repeat. Nothing bootstraps mid-fit, so the
    target does not chase the network. NFQCA adds a second network, the actor
    pi(s), trained to maximize Q(s, pi(s)) on the same batch, which gives a
    continuous action without wire fitting's interpolation.

    This is the bridge between the 1999 agent and DDPG (2015): same
    actor-critic-on-a-batch structure, but DDPG replaces the growing batch and
    the periodic full fits with a replay buffer, minibatches and slowly moving
    target networks.

Algorithm (per fit, every `fit_every` episodes, on all stored transitions D)
    repeat `iterations` times:
        y_i = r_i + gamma * Q(s'_i, pi(s'_i))          for all i, with Q, pi frozen
        train Q on {(s_i, a_i) -> y_i} for `critic_epochs` full-batch Rprop steps
        train pi to maximize mean_i Q(s_i, pi(s_i))    for `actor_epochs` Rprop steps
Exploration is Gaussian noise on pi(s) while collecting data, decayed per episode.
"""

import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common.deep import ReplayBuffer, TorchAgent, mlp, obs_tensor  # noqa: E402
from common.features import normalize_obs  # noqa: E402


class NFQCAAgent(TorchAgent):
    name = "2011_nfqca"
    continuous_actions = True
    supports_wide_angles = True

    def __init__(self, hidden=32, gamma=0.99, fit_every=5, iterations=2, critic_epochs=30, actor_epochs=15,
                 buffer_size=50000, sigma=0.3, sigma_min=0.05, sigma_decay=0.99, reward_scale=0.1, seed=None):
        super().__init__(seed)
        self.hidden, self.gamma, self.fit_every, self.iterations = hidden, gamma, fit_every, iterations
        self.critic_epochs, self.actor_epochs, self.buffer_size = critic_epochs, actor_epochs, buffer_size
        self.sigma, self.sigma_min, self.sigma_decay, self.reward_scale = sigma, sigma_min, sigma_decay, reward_scale
        self.actor = mlp([4, hidden, hidden, 1], nn.Tanh, output_activation=nn.Tanh)
        self.critic = mlp([5, hidden, hidden, 1], nn.Tanh)
        self.register(actor=self.actor, critic=self.critic)
        # Rprop, as in the NFQ papers: a full-batch method whose step sizes adapt per weight
        self.opt_critic = torch.optim.Rprop(self.critic.parameters(), lr=0.01)
        self.opt_actor = torch.optim.Rprop(self.actor.parameters(), lr=0.01)
        self.buf = ReplayBuffer(buffer_size)
        self.episodes = 0
        self._last_loss = 0.0

    # ---- policy ----------------------------------------------------------- #
    def act(self, obs):
        with torch.no_grad():
            u = float(self.actor(obs_tensor(obs)))
        if self.frozen:
            return u
        return float(np.clip(u + self.rng.normal(0.0, self.sigma), -1.0, 1.0))

    # ---- data collection; learning happens in fit() ----------------------- #
    def _learn(self, obs, action, reward, next_obs, terminated):
        self.buf.add(normalize_obs(obs), action, reward * self.reward_scale, normalize_obs(next_obs), terminated)

    def _end_episode(self):
        self.episodes += 1
        self.sigma = max(self.sigma_min, self.sigma * self.sigma_decay)
        if self.episodes % self.fit_every == 0 and len(self.buf) >= 32:
            self.fit()

    def fit(self):
        s, a, r, s2, term = self.buf.all()
        sa = torch.cat([s, a.unsqueeze(1)], dim=1)
        for _ in range(self.iterations):
            with torch.no_grad():  # fixed targets for this iteration
                a2 = self.actor(s2)
                y = r + self.gamma * (1.0 - term) * self.critic(torch.cat([s2, a2], dim=1)).squeeze(1)
            for _ in range(self.critic_epochs):
                loss = F.mse_loss(self.critic(sa).squeeze(1), y)
                self.opt_critic.zero_grad()
                loss.backward()
                self.opt_critic.step()
            for _ in range(self.actor_epochs):
                q = self.critic(torch.cat([s, self.actor(s)], dim=1))
                actor_loss = -q.mean()
                self.opt_actor.zero_grad()
                actor_loss.backward()
                self.opt_actor.step()
            self._last_loss = loss.item()

    # ---- bookkeeping ------------------------------------------------------ #
    def stats(self):
        return {"sigma": 0.0 if self.frozen else self.sigma, "fit_loss": self._last_loss, "data": float(len(self.buf))}

    def hparams(self):
        return dict(hidden=self.hidden, gamma=self.gamma, fit_every=self.fit_every, iterations=self.iterations,
                    critic_epochs=self.critic_epochs, actor_epochs=self.actor_epochs, buffer_size=self.buffer_size,
                    sigma_min=self.sigma_min, sigma_decay=self.sigma_decay, reward_scale=self.reward_scale)


Agent = NFQCAAgent
