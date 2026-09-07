# 2013: Deep Q-Network (Mnih et al.)

**Lineage:** [1983 actor-critic](../1983_actor_critic/README.md) → [1986 backprop actor-critic](../1986_actor_critic_backprop/README.md) → [1988 TD(λ)](../1988_td/README.md) → [1989 Q-learning](../1989_qlearning/README.md) → [1990 Dyna](../1990_dyna/README.md) → [1992 REINFORCE](../1992_reinforce/README.md) → [1999 continuous Q-learning](../1999_qlearning_continuous/README.md) → [2011 NFQCA](../2011_nfqca/README.md) → **2013 DQN** → [2015 DDPG](../2015_ddpg/README.md) → [2015 TRPO](../2015_trpo/README.md) → [2017 PPO](../2017_ppo/README.md) → [2018 SAC](../2018_sac/README.md)

**Previous:** [2011, neural fitted Q iteration with continuous actions](../2011_nfqca/README.md)

**Next:** [2015, DDPG: the same stabilizers applied to a continuous actor-critic](../2015_ddpg/README.md)

## References

- V. Mnih, K. Kavukcuoglu, D. Silver, A. Graves, I. Antonoglou, D. Wierstra and M. Riedmiller, ["Playing Atari with Deep Reinforcement Learning"](https://arxiv.org/abs/1312.5602), arXiv 1312.5602, 2013. Seven Atari games from pixels with one network and one set of hyperparameters.
- V. Mnih et al., ["Human-level control through deep reinforcement learning"](https://doi.org/10.1038/nature14236), *Nature* 518:529-533, 2015. Forty-nine games, human-level on twenty-nine, and the target network used here.

Riedmiller, an author of both, is also the author of NFQ; DQN is where the fitted-Q idea of the [previous solution](../2011_nfqca/README.md) meets Lin's experience replay and large-scale stochastic gradient descent.

## What changed from 1989 and 1999

Nothing about the target. It is still Watkins' $y = r + \gamma \max_{a'} Q(s', a')$, and the policy is still $\arg\max_a Q(s, a)$. What changed is how a neural network is trained toward that target without the instability that made the [1999 solution](../1999_qlearning_continuous/README.md) so hard to tune:

- **Experience replay.** Every transition goes into a large buffer and updates use uniformly sampled minibatches, which breaks the correlation between consecutive samples and reuses each transition many times. This is [Lin (1992)](../1990_dyna/README.md#what-changed-from-1989) at scale.
- **A target network.** The bootstrap value $\max_{a'} Q(s', a')$ is computed by a copy of the network that is only refreshed every few hundred steps, so the regression target stands still while the online network is fit to it. This is the fitted-Q idea from [NFQ](../2011_nfqca/README.md) made incremental.
- **Minibatch SGD with an adaptive optimizer and a Huber loss** instead of one sample at a time with a fixed step and a hand-clipped gradient.

Actions are discrete again. DQN takes a maximum over a finite action set, which is exactly what wire fitting was invented to avoid; the continuous line resumes with [DDPG](../2015_ddpg/README.md), which applies these same three stabilizers to an actor-critic.

## The method

Network $Q_\theta(s, \cdot)$: 4 → 128 → 128 → 2 with ReLU units, one output per action. Target network $Q_{\theta^-}$ is a copy of $\theta$ refreshed every `target_update` steps.

Each step: act $\varepsilon$-greedily, store $(s, a, r, s', \text{term})$ in a buffer of 50 000, sample a minibatch of 64 and take one Adam step on

$$
L(\theta) = \frac{1}{B}\sum_i \ell_{\text{Huber}}\Big( r_i + \gamma\,(1-\text{term}_i)\max_{a'} Q_{\theta^-}(s'_i, a') - Q_\theta(s_i, a_i) \Big),
$$

where $\ell_{\text{Huber}}$ is the smooth-L1 loss, quadratic for small errors and linear for large ones. Terminated transitions bootstrap nothing; truncated ones (the 500-step cap) bootstrap normally. $\varepsilon$ decays from 1 to 0.05 by a factor 0.995 per episode; learning starts once 1000 transitions are stored.

## Implementation notes and deviations

- This is the first solution in the repository that uses a framework. `soln.py` is PyTorch on the CPU (see [`common/deep.py`](../common/deep.py)); everything before it is numpy. For a network this size the CPU is the faster device, and `CARTPOLE_TORCH_DEVICE=mps` moves it to the GPU if you want to check.
- The 2013 paper had no target network and used RMSProp; the target network is from the 2015 paper and Adam is a later convention. Both are standard in every DQN implementation since.
- Reward is used unscaled (+1 per step), so $Q$ values reach about 100. The Huber loss keeps single large errors from dominating.
- The width and step size were set by a sweep with `hparam_sweep.py`. The first defaults, 64 units and Adam at 1e-3, reached a 100-episode average above 300 and then collapsed to below 50 by the end of a 5000-episode run, and the checkpointed greedy policy held the pole for only about 100 steps: the instability DQN is known for, even here. Of eight settings tried on two seeds, 128 units at 5e-4 and, equally, 64 units at 2.5e-4 with a 1000-step target refresh and batches of 128 reached the 500-step cap from both 0° and 11° on both seeds. The wider network was kept because it learns faster.
- Per-agent random generators make runs reproducible by seed, which the shared test suite checks for every solution.

## Run

```sh
python ../main.py --mode train --soln 2013_dqn --no-render
python ../main.py --mode infer --soln 2013_dqn --theta0 -11
pytest ../tests -k 2013
```

## Result

Seed 0, 5000 training episodes with full-range starts, frozen policy, 20 episodes per start angle:

| start angle | 0° | −8° | +8° | −11° | +11° |
|---|---|---|---|---|---|
| mean steps (max 500) | 500 | 500 | 500 | 500 | 500 |

The 100-episode average peaked at 385.4 at episode 2712 and had drifted down to 130 by the end of the run, so the best-checkpoint rule matters more for DQN than for any other solution here: the saved greedy policy holds the pole from every start angle even though the network kept training past its best. Training took 246 s on one CPU core with PyTorch: 0.77 M environment steps at about 3,123 steps/s, or 320 µs per step, one minibatch of 64 per step.

## Limitations

- Discrete actions only. On this two-action problem that is no loss, but it is the reason the continuous line branches off with DDPG.
- Still an off-policy bootstrapped method with the maximization bias Thrun and Schwartz identified in 1993; Double DQN (2015) and dueling networks (2016) are the fixes, not included here.
- Sample-inefficient by the standards of the [2011 solution](../2011_nfqca/README.md), which fits to convergence on every transition it has ever seen; DQN's advantage is that it scales to problems where that is impossible.
