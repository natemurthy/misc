# 2011: Neural Fitted Q Iteration with Continuous Actions (Hafner and Riedmiller)

**Lineage:** [1983 actor-critic](../1983_actor_critic/README.md) → [1986 backprop actor-critic](../1986_actor_critic_backprop/README.md) → [1988 TD(λ)](../1988_td/README.md) → [1989 Q-learning](../1989_qlearning/README.md) → [1990 Dyna](../1990_dyna/README.md) → [1992 REINFORCE](../1992_reinforce/README.md) → [1999 continuous Q-learning](../1999_qlearning_continuous/README.md) → [2005 NAC](../2005_nac/README.md) → [2007 CACLA](../2007_cacla/README.md) → **2011 NFQCA** → [2011 PILCO](../2011_pilco/README.md) → [2013 DQN](../2013_dqn/README.md) → [2015 DDPG](../2015_ddpg/README.md) → [2015 TRPO](../2015_trpo/README.md) → [2017 PPO](../2017_ppo/README.md) → [2018 SAC](../2018_sac/README.md)

**Previous:** [2007, CACLA: the actor follows the taken action on positive TD error](../2007_cacla/README.md)

**Next:** [2011, PILCO: a learned Gaussian-process model in place of a critic](../2011_pilco/README.md)

## References

- R. Hafner and M. Riedmiller, ["Reinforcement learning in feedback control: Challenges and benchmarks from technical process control"](https://doi.org/10.1007/s10994-011-5235-4), *Machine Learning* 84:137-169, 2011. Introduces NFQCA and evaluates it on cart-pole among other control benchmarks.
- M. Riedmiller, ["Neural Fitted Q Iteration - First Experiences with a Data Efficient Neural Reinforcement Learning Method"](https://doi.org/10.1007/11564096_32), ECML 2005. The discrete NFQ this extends, demonstrated on the cart-pole regulator with a few hundred transitions.
- D. Ernst, P. Geurts and L. Wehenkel, "Tree-Based Batch Mode Reinforcement Learning", *JMLR* 6, 2005. Fitted Q iteration with trees; NFQ is the neural-network case.

## What changed from 1999

The [1999 agent](../1999_qlearning_continuous/README.md) updated its network after every step on the single transition just seen, with the bootstrap target moving under it. Its README documents what that cost. Riedmiller's fitted Q iteration removes the moving target by turning Q-learning into a sequence of ordinary supervised regressions:

1. Keep every transition seen so far in a dataset $D$.
2. With the current network frozen, compute the Q-learning target $y_i$ for every transition in $D$.
3. Train the network to convergence on the fixed pairs $\{(s_i, a_i) \to y_i\}$ with a batch optimizer.
4. Repeat from step 2.

Within one fit nothing bootstraps, so the network cannot chase itself, and a batch optimizer with adaptive per-weight steps (Rprop) can be run hard without a hand-tuned learning rate. NFQ solved the discrete cart-pole with a few hundred transitions, an order of magnitude less data than online Q-learning needed. NFQCA keeps the structure and adds a second network, the actor $\pi_\phi(s)$, trained on the same batch to maximize $Q(s, \pi_\phi(s))$. That gives a continuous action without wire fitting's interpolation, and it is the structure DDPG inherits four years later.

## The method

Two networks: critic $Q_\theta(s, a)$ on the concatenated state and action, 5 → 32 → 32 → 1, and actor $\pi_\phi(s)$, 4 → 32 → 32 → 1 with a tanh output so $u \in [-1, 1]$; tanh hidden units in both, as in the paper.

Data collection: act with $\pi_\phi(s)$ plus Gaussian noise (standard deviation decaying from 0.3 to 0.05), store every transition. Every `fit_every` episodes (5), run a fit on all stored transitions:

$$
\text{for } k = 1..K:\qquad
y_i \leftarrow r_i + \gamma\,(1-\text{term}_i)\, Q_\theta\big(s'_i, \pi_\phi(s'_i)\big) \quad \text{(both networks frozen)},
$$

$$
\theta \leftarrow \arg\min_\theta \frac{1}{|D|}\sum_i \big(Q_\theta(s_i, a_i) - y_i\big)^2 \quad (\text{30 Rprop steps}), \qquad
\phi \leftarrow \arg\max_\phi \frac{1}{|D|}\sum_i Q_\theta\big(s_i, \pi_\phi(s_i)\big) \quad (\text{15 Rprop steps}),
$$

with $K = 2$ iterations per fit, $\gamma = 0.99$, and rewards scaled by 0.1. The scale matters: at 0.01, the value the 1999 agent uses, the critic's targets are too small relative to the noise in the actor's inputs and the fit never leaves the random baseline; at 0.1 it learns within a few hundred episodes. The actor update is the deterministic policy gradient, $\nabla_\phi Q(s, \pi_\phi(s))$, computed by backpropagating through the critic, three years before Silver et al. named it.

## Implementation notes and deviations

- First PyTorch solution in the lineage (CPU; see [`common/deep.py`](../common/deep.py)). Rprop is `torch.optim.Rprop`, the same algorithm the paper used.
- The paper trains each fit to convergence with hundreds of Rprop epochs and sometimes re-initializes the network each iteration; here fits are capped at 30 critic and 15 actor epochs and the networks carry over, which is the usual "warm start" variant and much cheaper.
- NFQ's "hint-to-goal" trick, adding artificial transitions that pin the value of goal states, is omitted; with +1 per step the goal region is every non-failing state, so there is nothing to pin.
- The dataset is capped at 50 000 transitions in a ring buffer; the paper's growing batch is unbounded.

## Run

```sh
python ../main.py --mode train --soln 2011_nfqca --no-render
python ../main.py --mode infer --soln 2011_nfqca --theta0 -11
pytest ../tests -k 2011
```

## Result

Seed 0, 5000 training episodes with full-range starts, frozen policy, 20 episodes per start angle:

| start angle | 0° | −8° | +8° | −11° | +11° |
|---|---|---|---|---|---|
| mean steps (max 500) | 500 | 500 | 500 | 500 | 491 |

The 100-episode average first reached 500 at episode 2050. Training took 1595 s on one CPU core with PyTorch: 1.92 M environment steps at about 1,203 steps/s, or 831 µs per step. It is the slowest run in the repository by wall clock because every fifth episode refits both networks on the entire dataset, and the dataset grows to its 50 000-transition cap; per environment step the cost is still modest.

## Limitations

- Each fit costs time proportional to the whole dataset, so per-episode cost grows as data accumulates; DQN's minibatches fix this at the price of a moving target.
- Exploration is unstructured Gaussian noise on a deterministic actor, the weak point DDPG inherits and SAC finally addresses.
- Like every fitted method, it can only be as good as the batch it has: states never visited are extrapolated by the network with no correction until they are visited.
