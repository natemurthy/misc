"""
Common agent interface used by main.py and the tests.

Every solution's agent subclasses BaseAgent and implements:

    act(obs) -> int                                  choose 0 (left) or 1 (right)
    _learn(obs, action, reward, next_obs, terminated) per-step update
    _end_episode()                                   per-episode update / decay
    stats() -> dict                                  small numbers for the progress bar
    hparams() -> dict                                constructor kwargs, JSON-serializable
    state_dict() -> dict[str, np.ndarray]            learned parameters
    load_state_dict(d)

BaseAgent provides freeze() (greedy, no updates), save()/load() as .npz, and
snapshot()/restore() used for best-checkpoint selection during training.
"""

import json

import numpy as np


class BaseAgent:
    name = "base"
    continuous_actions = False   # True: act() returns a force fraction in [-1, 1] instead of 0/1
    supports_wide_angles = False  # True: works with --theta-limit above 12 degrees
    render_first_episodes = 1     # main.py animates episodes 1..N regardless of --render-every; PILCO raises it
                                  # so its handful of slow learning trials can be watched

    def __init__(self, seed=None):
        self.rng = np.random.default_rng(seed)
        self.frozen = False

    # ---- to implement --------------------------------------------------- #
    def act(self, obs):
        raise NotImplementedError

    def _learn(self, obs, action, reward, next_obs, terminated):
        pass

    def _end_episode(self):
        pass

    def stats(self):
        return {}

    def hparams(self):
        return {}

    def state_dict(self):
        return {}

    def load_state_dict(self, d):
        pass

    # ---- provided ------------------------------------------------------- #
    def learn(self, obs, action, reward, next_obs, terminated):
        if not self.frozen:
            self._learn(obs, action, reward, next_obs, terminated)

    def end_episode(self):
        if not self.frozen:
            self._end_episode()

    def freeze(self):
        """Switch to pure inference: deterministic policy, no exploration, no updates."""
        self.frozen = True

    def snapshot(self):
        return {k: np.array(v, copy=True) for k, v in self.state_dict().items()}

    def restore(self, snap):
        self.load_state_dict(snap)

    def save(self, path):
        meta = json.dumps({"agent": type(self).__name__, "hparams": self.hparams()})
        np.savez(path, __meta__=np.array(meta), **self.state_dict())

    @classmethod
    def load(cls, path, seed=None):
        data = np.load(path, allow_pickle=False)
        if "__meta__" not in data.files:
            raise ValueError(f"{path} is not a model saved by {cls.__name__}.save()")
        meta = json.loads(str(data["__meta__"]))
        agent = cls(seed=seed, **meta["hparams"])
        agent.load_state_dict({k: data[k] for k in data.files if k != "__meta__"})
        return agent

    def _random_action(self):
        return int(self.rng.integers(2))

    def _tie_break(self):
        """Action to take when both actions are exactly equally preferred.
        Random while learning (no left/right bias in unvisited states);
        deterministic once frozen so an inference policy is reproducible."""
        return 0 if self.frozen else int(self.rng.integers(2))


class RandomAgent(BaseAgent):
    """Uniform random policy. The baseline every solution should beat (~22 steps)."""

    name = "random"

    def act(self, obs):
        return self._random_action()
