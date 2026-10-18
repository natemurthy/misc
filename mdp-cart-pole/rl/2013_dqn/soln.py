"""
2013: Deep Q-Network (Mnih et al.), Q-learning with a neural network made stable.

Reference
    V. Mnih et al., "Playing Atari with Deep Reinforcement Learning", arXiv
    1312.5602, 2013.   https://arxiv.org/abs/1312.5602
    V. Mnih et al., "Human-level control through deep reinforcement learning",
    Nature 518, 2015 (adds the target network).

What changed from 1989/1999
    The update is still Watkins' Q-learning target, y = r + gamma * max_a' Q(s', a'),
    and the greedy policy is still argmax_a Q(s, a). Three additions make it
    work with a neural network where the 1999 wire-fitted net was fragile:
      * a large replay buffer sampled uniformly in minibatches, which breaks the
        correlation between consecutive transitions;
      * a separate target network, copied from the online network every few
        hundred steps, so the bootstrap target does not move with every update;
      * minibatch stochastic gradient descent with an adaptive optimizer and a
        Huber loss, instead of one sample at a time with a fixed step.
    Actions are discrete again (push left / push right): DQN takes the max over
    a finite action set, which is exactly what the 1999 method was built to
    avoid. The continuous line continues with DDPG (2015).

On this MDP the network is 4 -> 128 -> 128 -> 2 and the whole method is overkill
in the best sense: it is the same machinery that plays Atari from pixels,
applied to a four-number state. The width and the step size (5e-4) come from a
sweep: 64 units with lr 1e-3 learned quickly and then collapsed late in a long
run, the classic DQN instability.
"""

import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common.deep import DEVICE, ReplayBuffer, TorchAgent, hard_update, mlp, obs_tensor  # noqa: E402
from common.features import normalize_obs  # noqa: E402


class DQNAgent(TorchAgent):
    name = "2013_dqn"

    def __init__(self, hidden=128, lr=5e-4, gamma=0.99, batch_size=64, buffer_size=50000, learning_starts=1000,
                 target_update=500, epsilon=1.0, epsilon_min=0.05, epsilon_decay=0.995, seed=None):
        super().__init__(seed)
        self.hidden, self.lr, self.gamma, self.batch_size = hidden, lr, gamma, batch_size
        self.buffer_size, self.learning_starts, self.target_update = buffer_size, learning_starts, target_update
        self.epsilon, self.epsilon_min, self.epsilon_decay = epsilon, epsilon_min, epsilon_decay
        self.q = mlp([4, hidden, hidden, 2], nn.ReLU)
        self.q_target = mlp([4, hidden, hidden, 2], nn.ReLU)
        hard_update(self.q_target, self.q)
        self.register(q=self.q, q_target=self.q_target)
        self.opt = torch.optim.Adam(self.q.parameters(), lr=lr)
        self.buf = ReplayBuffer(buffer_size)
        self.steps = 0
        self._last_loss = 0.0

    # ---- policy ----------------------------------------------------------- #
    def act(self, obs):
        if not self.frozen and self.rng.random() < self.epsilon:
            return self._random_action()
        with torch.no_grad():
            q = self.q(obs_tensor(obs))
        if q[0] == q[1]:
            return self._tie_break()
        return int(torch.argmax(q))

    # ---- learning --------------------------------------------------------- #
    def _learn(self, obs, action, reward, next_obs, terminated):
        self.buf.add(normalize_obs(obs), action, reward, normalize_obs(next_obs), terminated)
        self.steps += 1
        if len(self.buf) < max(self.learning_starts, self.batch_size):
            return
        s, a, r, s2, term = self.buf.sample(self.batch_size, self.rng)
        with torch.no_grad():
            y = r + self.gamma * (1.0 - term) * self.q_target(s2).max(dim=1).values
        q_sa = self.q(s).gather(1, a.long().unsqueeze(1)).squeeze(1)
        loss = F.smooth_l1_loss(q_sa, y)
        self.opt.zero_grad()
        loss.backward()
        self.opt.step()
        self._last_loss = loss.item()
        if self.steps % self.target_update == 0:
            hard_update(self.q_target, self.q)

    def _end_episode(self):
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def freeze(self):
        super().freeze()
        self.epsilon = 0.0

    # ---- bookkeeping ------------------------------------------------------ #
    def stats(self):
        return {"eps": self.epsilon, "loss": self._last_loss}

    def hparams(self):
        return dict(hidden=self.hidden, lr=self.lr, gamma=self.gamma, batch_size=self.batch_size,
                    buffer_size=self.buffer_size, learning_starts=self.learning_starts,
                    target_update=self.target_update, epsilon_min=self.epsilon_min, epsilon_decay=self.epsilon_decay)


Agent = DQNAgent
