# 1992: REINFORCE (Williams), Monte Carlo policy gradient

**Lineage:** [1983 actor-critic](../1983_actor_critic/README.md) → [1986 backprop actor-critic](../1986_actor_critic_backprop/README.md) → [1988 TD(λ)](../1988_td/README.md) → [1989 Q-learning](../1989_qlearning/README.md) → [1990 Dyna](../1990_dyna/README.md) → **1992** → [1999 continuous Q-learning](../1999_qlearning_continuous/README.md) → [2011 NFQCA](../2011_nfqca/README.md) → [2013 DQN](../2013_dqn/README.md) → [2015 DDPG](../2015_ddpg/README.md) → [2015 TRPO](../2015_trpo/README.md) → [2017 PPO](../2017_ppo/README.md) → [2018 SAC](../2018_sac/README.md)

**Previous:** [1990, Dyna-Q](../1990_dyna/README.md)

**Next:** [1999, Q-learning with a continuous force](../1999_qlearning_continuous/README.md)

## Reference

R. J. Williams, ["Simple Statistical Gradient-Following Algorithms for Connectionist Reinforcement Learning"](https://doi.org/10.1007/BF00992696), *Machine Learning* 8:229-256, 1992. The algorithm first appeared in Williams' Northeastern University technical reports of 1986-1988.

## What changed from the value-based line

Everything from 1988 to 1990 learns a value function and derives the policy from it by taking a maximum. REINFORCE has no value function at all. It parameterizes the policy directly, $\pi_\theta(a \mid s)$, and adjusts $\theta$ to increase expected return by stochastic gradient ascent. Williams' contribution was the proof that the simple update

$$
\theta \leftarrow \theta + \alpha \sum_{t} (G_t - b)\, \nabla_\theta \log \pi_\theta(a_t \mid s_t)
$$

follows an *unbiased* estimate of $\nabla_\theta \mathbb E[G]$, where $G_t$ is the return from step $t$ and $b$ is any baseline that does not depend on the action. The 1983 ASE was a one-step, critic-driven instance of this same form without the theory; REINFORCE makes the policy-gradient idea rigorous and separates it from the critic. Modern actor-critic methods rejoin the two branches by using a learned value function as the baseline $b$.

Compared with the value-based methods this brings:

- **Direct optimization of the objective.** No Bellman equation, no maximum over actions, so it extends to continuous and high-dimensional action spaces where $\arg\max_a$ is intractable.
- **Smooth, stochastic policies** with natural exploration built in.
- **Higher variance.** Each update waits for an episode to end and uses the full Monte Carlo return, which is noisy. The baseline exists to reduce that variance without introducing bias.

## The method

**Policy.** Linear-logistic over the normalized state plus a bias term, $\phi(s) = (x/2.4,\ \dot x/3,\ \theta/0.21,\ \dot\theta/3.5,\ 1)$:

$$
\pi_\theta(\text{right} \mid s) = \sigma(\theta^\top \phi(s)), \qquad
\nabla_\theta \log \pi_\theta(a \mid s) = \big(a - \sigma(\theta^\top \phi(s))\big)\, \phi(s).
$$

A linear policy is sufficient to balance the cart-pole; it has five parameters.

**Episode update.** Actions are sampled from $\pi_\theta$ for a whole episode. At the end, discounted returns $G_t = \sum_{k \ge 0} \gamma^k r_{t+k+1}$ are computed backwards and the gradient step above is applied once, with $\alpha = 0.001$ and $\gamma = 0.99$.

**Baseline.** A *constant reinforcement baseline* in Williams' terminology: an exponential moving average of past episodes' returns from the first step, $b \leftarrow b + 0.05\,(G_0 - b)$.

Inference (`freeze()`) takes the more probable action, $a = [\sigma(\theta^\top\phi(s)) > 0.5]$.

## Implementation notes

- With $\alpha = 0.002$ the policy reaches 500 steps and then occasionally overshoots and collapses; $\alpha = 0.001$ is stable across seeds.
- REINFORCE's `learn()` only records the transition. All parameter movement happens in `end_episode()`. The `BaseAgent` interface supports this because `main.py` calls `end_episode()` after every episode for every solution.

## Wider angles

This solution reads the raw scaled state, so it accepts `--theta-limit` above 12° (see [Wider angles](../README.md#wider-angles)). Its linear policy has the same form as a linear state-feedback controller, and trained on ±40° starts it recovered from 20° every time and from 30° in three of ten attempts, failing by running out of track, which is close to the ~34° physical envelope.

## Run

```sh
python ../main.py --mode train --soln 1992_reinforce --no-render
python ../main.py --mode infer --soln 1992_reinforce --theta0 11
pytest ../tests -k reinforce
```

## Result

Seed `[0, 5000]` training episodes with full-range starts, frozen policy, 20 episodes per start angle:

| start angle | 0° | −8° | +8° | −11° | +11° |
|---|---|---|---|---|---|
| mean steps (max 500) | 500 | 500 | 500 | 500 | 500 |

The 100-episode average first reached 500 at episode 1582. The learned policy is five numbers.

## Limitations

- Sample-inefficient in general: one update per episode, from a noisy return. On CartPole that is hidden by the fact that a linear policy is enough.
- The constant baseline is crude. A state-dependent baseline, i.e. a critic, is the natural improvement, and taking it leads straight back to the actor-critic architecture of 1983, now with a theory on both sides.
