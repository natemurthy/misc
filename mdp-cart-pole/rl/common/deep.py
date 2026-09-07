"""
Shared PyTorch pieces for the 2011-2018 solutions (NFQCA, DQN, DDPG, TRPO, PPO, SAC).

The 1983-1999 solutions are numpy only. From 2011 on the methods rely on
automatic differentiation (second derivatives for TRPO, reparameterized
sampling for SAC), so they use PyTorch on the CPU. This module keeps the
framework-facing code in one place:

    mlp(sizes, ...)            plain fully connected network
    TorchAgent                 BaseAgent subclass: seeding, state_dict <-> numpy,
                               per-agent random generators so runs are reproducible
    ReplayBuffer               ring buffer of transitions, samples torch batches
    soft_update / hard_update  target-network updates
    obs_tensor                 normalized observation as a float32 tensor

Threads are pinned to one per process so that hparam_sweep.py's worker
processes do not fight over cores (set CARTPOLE_TORCH_THREADS to override).

Everything runs on the CPU by default. Set CARTPOLE_TORCH_DEVICE=mps (Apple
GPU) or cuda to move models and batches there; for networks this small the
CPU is faster, since kernel-launch latency dominates the arithmetic.
"""

import os

import numpy as np
import torch
import torch.nn as nn

from .agent import BaseAgent
from .features import normalize_obs

torch.set_num_threads(int(os.environ.get("CARTPOLE_TORCH_THREADS", "1")))
DEVICE = torch.device(os.environ.get("CARTPOLE_TORCH_DEVICE", "cpu"))


def mlp(sizes, activation=nn.Tanh, output_activation=None):
    layers = []
    for i in range(len(sizes) - 1):
        layers.append(nn.Linear(sizes[i], sizes[i + 1]))
        if i < len(sizes) - 2:
            layers.append(activation())
    if output_activation is not None:
        layers.append(output_activation())
    return nn.Sequential(*layers)


def obs_tensor(obs):
    return torch.as_tensor(normalize_obs(obs), dtype=torch.float32, device=DEVICE)


def to_device(*tensors):
    return tuple(t.to(DEVICE) for t in tensors)


def soft_update(target, source, tau):
    with torch.no_grad():
        for t, s in zip(target.parameters(), source.parameters()):
            t.mul_(1.0 - tau).add_(s, alpha=tau)


def hard_update(target, source):
    target.load_state_dict(source.state_dict())


class ReplayBuffer:
    """Fixed-size ring buffer. Actions are stored as float (scalar action per step)."""

    def __init__(self, capacity, obs_dim=4):
        self.capacity = capacity
        self.obs = np.zeros((capacity, obs_dim), dtype=np.float32)
        self.act = np.zeros(capacity, dtype=np.float32)
        self.rew = np.zeros(capacity, dtype=np.float32)
        self.next_obs = np.zeros((capacity, obs_dim), dtype=np.float32)
        self.term = np.zeros(capacity, dtype=np.float32)
        self.n = 0
        self.pos = 0

    def add(self, obs, act, rew, next_obs, term):
        i = self.pos
        self.obs[i], self.act[i], self.rew[i], self.next_obs[i], self.term[i] = obs, act, rew, next_obs, float(term)
        self.pos = (i + 1) % self.capacity
        self.n = min(self.n + 1, self.capacity)

    def sample(self, batch_size, rng):
        idx = rng.integers(self.n, size=batch_size)
        return to_device(torch.from_numpy(self.obs[idx]), torch.from_numpy(self.act[idx]), torch.from_numpy(self.rew[idx]),
                         torch.from_numpy(self.next_obs[idx]), torch.from_numpy(self.term[idx]))

    def all(self):
        return to_device(torch.from_numpy(self.obs[: self.n]), torch.from_numpy(self.act[: self.n]),
                         torch.from_numpy(self.rew[: self.n]), torch.from_numpy(self.next_obs[: self.n]),
                         torch.from_numpy(self.term[: self.n]))

    def __len__(self):
        return self.n


class TorchAgent(BaseAgent):
    """
    BaseAgent with torch bookkeeping. Subclasses register their modules in
    self.modules (name -> nn.Module) and use self.gen (torch.Generator) and
    self.rng (numpy) for every random draw, so two agents built with the same
    seed behave identically regardless of what else runs in the process.
    """

    def __init__(self, seed=None):
        super().__init__(seed)
        torch.manual_seed(0 if seed is None else int(seed))  # network initialization
        self.gen = torch.Generator().manual_seed(0 if seed is None else int(seed) + 12345)
        self.modules = {}

    def randn(self, *shape):
        """Standard normal noise from this agent's generator; accepts randn(2, 3), randn((2, 3)) or randn(())."""
        if len(shape) == 1 and isinstance(shape[0], (tuple, list, torch.Size)):
            shape = tuple(shape[0])
        return torch.randn(tuple(shape), generator=self.gen).to(DEVICE)

    def register(self, **modules):
        """Move modules to DEVICE and record them for state_dict()/snapshot()."""
        for name, m in modules.items():
            self.modules[name] = m.to(DEVICE)
        return [self.modules[n] for n in modules]

    def state_dict(self):
        out = {}
        for name, module in self.modules.items():
            for k, v in module.state_dict().items():
                out[f"{name}.{k}"] = v.detach().cpu().numpy().copy()
        return out

    def load_state_dict(self, d):
        for name, module in self.modules.items():
            sd = {k[len(name) + 1:]: torch.as_tensor(np.array(v)) for k, v in d.items() if k.startswith(name + ".")}
            module.load_state_dict(sd)
