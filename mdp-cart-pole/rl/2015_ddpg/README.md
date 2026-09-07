# 2015: Deep Deterministic Policy Gradient (Lillicrap et al.)

**Lineage:** [1983 actor-critic](../1983_actor_critic/README.md) → [1986 backprop actor-critic](../1986_actor_critic_backprop/README.md) → [1988 TD(λ)](../1988_td/README.md) → [1989 Q-learning](../1989_qlearning/README.md) → [1990 Dyna](../1990_dyna/README.md) → [1992 REINFORCE](../1992_reinforce/README.md) → [1999 continuous Q-learning](../1999_qlearning_continuous/README.md) → [2011 NFQCA](../2011_nfqca/README.md) → [2013 DQN](../2013_dqn/README.md) → **2015 DDPG** → [2015 TRPO](../2015_trpo/README.md) → [2017 PPO](../2017_ppo/README.md) → [2018 SAC](../2018_sac/README.md)

**Previous:** [2013 DQN](../2013_dqn/README.md)

**Next:** [2015 TRPO](../2015_trpo/README.md)

## Reference

- T. P. Lillicrap, J. J. Hunt, A. Pritzel, N. Heess, T. Erez, Y. Tassa, D. Silver and D. Wierstra, ["Continuous control with deep reinforcement learning"](https://arxiv.org/abs/1509.02971), arXiv 1509.02971, 2015 (ICLR 2016).
- D. Silver, G. Lever, N. Heess, T. Degris, D. Wierstra and M. Riedmiller, ["Deterministic Policy Gradient Algorithms"](https://proceedings.mlr.press/v32/silver14.html), ICML 2014. The gradient theorem DDPG rests on.

## What changed

Two threads of the lineage meet here. [NFQCA (2011)](../2011_nfqca/README.md) already had a critic $Q(s, a)$ and a deterministic actor $\pi(s)$ trained to maximize $Q(s, \pi(s))$, but it refit both networks from scratch on the whole stored batch every few episodes, because training a Q-network online had never been made stable. [DQN (2013)](../2013_dqn/README.md) made it stable, for discrete actions, with two devices: a large replay buffer sampled uniformly in minibatches so consecutive transitions are decorrelated, and a separate target network so the bootstrap target does not move with every update.

DDPG puts DQN's two devices under NFQCA's actor-critic. The result is an off-policy, online, continuous-action method that updates after every step from a minibatch, with target copies of both actor and critic that trail the online networks by a slow exponential average rather than DQN's periodic hard copy. The actor's gradient is the deterministic policy gradient of Silver et al. (2014): differentiate the critic with respect to the action at $a = \pi(s)$ and chain through the actor. This is the same quantity NFQCA's actor step computes on a batch, now computed on a minibatch every step. Relative to the [1999 wire-fitted agent](../1999_qlearning_continuous/README.md), the continuous maximization over actions is no longer an interpolation trick; it is a second network trained to perform it.

## The method

Networks: actor $\pi_\theta(s) \in [-1, 1]$ (tanh output), critic $Q_\phi(s, a)$, and target copies $\pi_{\theta'}$, $Q_{\phi'}$. Each environment step stores $(s, a, r, s', d)$ in a replay buffer and, once the buffer holds enough transitions, samples a minibatch $B$.

Critic target and loss, with $d = 1$ on failure:

$$
y = r + \gamma\,(1 - d)\, Q_{\phi'}\big(s', \pi_{\theta'}(s')\big), \qquad
L(\phi) = \frac{1}{|B|} \sum_{(s,a,r,s',d) \in B} \big(Q_\phi(s, a) - y\big)^2 .
$$

Actor update, the deterministic policy gradient:

$$
\nabla_\theta J \approx \frac{1}{|B|} \sum_{s \in B} \nabla_a Q_\phi(s, a)\big|_{a = \pi_\theta(s)}\, \nabla_\theta \pi_\theta(s),
\qquad \text{implemented as minimizing } -\frac{1}{|B|}\sum_{s \in B} Q_\phi\big(s, \pi_\theta(s)\big).
$$

Soft target updates after each step:

$$
\phi' \leftarrow \tau\,\phi + (1 - \tau)\,\phi', \qquad \theta' \leftarrow \tau\,\theta + (1 - \tau)\,\theta' .
$$

Exploration adds Ornstein-Uhlenbeck noise to the actor's output during training, $n_{t+1} = n_t + \theta_{\text{OU}}(0 - n_t) + \sigma\,\epsilon_t$, $a_t = \mathrm{clip}(\pi_\theta(s_t) + n_t, -1, 1)$, which produces temporally correlated exploration suited to inertial systems. The frozen policy is $\pi_\theta(s)$ with no noise.

## Implementation notes and deviations

- `soln.py` uses PyTorch on the CPU through the shared helpers in `common/deep.py` (network builder, replay buffer, soft update, per-agent random generators so runs are reproducible by seed). Actor and critic are `4 → 64 → 64 → 1` ReLU networks; the critic takes the state and action concatenated.
- Defaults: actor step size $10^{-4}$, critic $10^{-3}$, $\gamma = 0.99$, $\tau = 0.005$, minibatch 64, buffer 50 000, learning starts after 1000 transitions, OU noise with $\theta_{\text{OU}} = 0.15$ and $\sigma$ decaying from 0.2 to 0.05 by a factor 0.995 per episode and reset to zero at episode start.
- Rewards are scaled by 0.1 inside the agent so the critic's values are of order 10 rather than 100. Positive scaling does not change the optimal policy.
- The paper uses batch normalization and $L_2$ weight decay on the critic; neither is used here, the networks and state being small. The paper's OU noise has a fixed scale; here it decays per episode so the frozen policy is not far from the exploring one late in training.
- The action is one-dimensional (a force fraction), so the actor's output layer has a single unit.

## Run

```sh
python ../main.py --mode train --soln 2015_ddpg --no-render
python ../main.py --mode infer --soln 2015_ddpg --theta0 -11
python ../main.py --mode train --soln 2015_ddpg --no-render --theta-limit 30   # wide angles are supported
pytest ../tests -k ddpg
```

## Result

Seed 0, 5000 training episodes with full-range starts, frozen policy, 20 episodes per start angle:

| start angle | 0° | −8° | +8° | −11° | +11° |
|---|---|---|---|---|---|
| mean steps (max 500) | 500 | 500 | 500 | 500 | 500 |

The 100-episode average peaked at 475.5 at episode 3102. Training took 618 s on one CPU core with PyTorch: 0.96 M environment steps at about 1,551 steps/s, or 645 µs per step. The 100-episode average never quite reached 500 during training (best 475.5), yet the frozen deterministic actor from that checkpoint holds the pole from every start angle; the exploration noise, not the policy, was costing the last few steps.

## Limitations

- Known to be brittle: DDPG overestimates Q-values because the actor exploits the critic's errors, and results vary with the seed. In a 400-episode smoke test on two seeds the 100-episode average reached 144 and 227 steps, still well short of the cap. The fixes came later: twin critics and delayed actor updates in TD3 (2018), and the entropy-regularized stochastic actor of [SAC (2018)](../2018_sac/README.md).
- Deterministic policy plus additive noise is a weak exploration strategy when the reward is dense but the failure signal is sparse, as here.
- Off-policy learning from a replay buffer means the data distribution lags the policy; the on-policy line, [TRPO (2015)](../2015_trpo/README.md) and [PPO (2017)](../2017_ppo/README.md), gives up sample reuse for a monotone-improvement guarantee instead.
