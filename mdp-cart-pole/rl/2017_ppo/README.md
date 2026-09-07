# 2017: Proximal Policy Optimization (Schulman, Wolski, Dhariwal, Radford and Klimov)

**Lineage:** [1983 actor-critic](../1983_actor_critic/README.md) → [1986 backprop actor-critic](../1986_actor_critic_backprop/README.md) → [1988 TD(λ)](../1988_td/README.md) → [1989 Q-learning](../1989_qlearning/README.md) → [1990 Dyna](../1990_dyna/README.md) → [1992 REINFORCE](../1992_reinforce/README.md) → [1999 continuous Q-learning](../1999_qlearning_continuous/README.md) → [2011 NFQCA](../2011_nfqca/README.md) → [2013 DQN](../2013_dqn/README.md) → [2015 DDPG](../2015_ddpg/README.md) → [2015 TRPO](../2015_trpo/README.md) → **2017 PPO** → [2018 SAC](../2018_sac/README.md)

**Previous:** [2015 TRPO](../2015_trpo/README.md)

**Next:** [2018 SAC](../2018_sac/README.md)

## Reference

J. Schulman, F. Wolski, P. Dhariwal, A. Radford and O. Klimov, ["Proximal Policy Optimization Algorithms"](https://arxiv.org/abs/1707.06347), arXiv 1707.06347, 2017. The advantage estimator is from J. Schulman, P. Moritz, S. Levine, M. Jordan and P. Abbeel, ["High-Dimensional Continuous Control Using Generalized Advantage Estimation"](https://arxiv.org/abs/1506.02438), arXiv 1506.02438, 2015.

## What changed from TRPO

TRPO answers the question REINFORCE left open, how far to move the policy on one batch of data, with a constraint: maximize the surrogate objective subject to a bound on the KL divergence from the old policy. Enforcing that constraint costs a conjugate-gradient solve against the Fisher information matrix and a backtracking line search, and it permits exactly one gradient step per batch, after which the data is stale.

PPO keeps the question and the answer but changes the mechanism. Instead of a constraint it modifies the objective: the probability ratio $\rho_t = \pi_\theta(a_t \mid s_t) / \pi_{\theta_{\text{old}}}(a_t \mid s_t)$ is clipped to $[1-\epsilon, 1+\epsilon]$, and the surrogate takes the minimum of the clipped and unclipped terms. Once a sample has pushed the policy far enough in the direction its advantage favours, its gradient is zero; samples pushing the other way are never clipped, so the objective is a pessimistic lower bound on the unclipped one. That is the whole trust region, expressed as a loss.

Two consequences follow. The second-order machinery disappears: no Fisher-vector products, no line search, just Adam. And because the clipped objective stays sound as the policy drifts from the one that collected the data, the same batch can be reused for several epochs of minibatch gradient descent, which TRPO cannot do. PPO is therefore simpler, cheaper per update, more sample-efficient, and less sensitive to its few hyperparameters. It became the default policy-gradient method and, on Gymnasium's `CartPole-v1`, the standard first example in every RL library.

## The method

Actor and critic are separate networks, $\pi_\theta(a \mid s)$ a softmax over two logits and $V_\phi(s)$ a scalar, each `4 → 64 → 64` with tanh hidden units. One Adam optimizer updates both.

**Advantages.** After $T$ steps have been collected (across episode boundaries), generalized advantage estimation with $\gamma$ and $\lambda$:

$$
\delta_t = r_t + \gamma\,(1 - \text{term}_t)\,V_\phi(s_{t+1}) - V_\phi(s_t), \qquad
\hat A_t = \delta_t + \gamma\lambda\,(1 - \text{done}_t)\,\hat A_{t+1}, \qquad
\hat R_t = \hat A_t + V_\phi(s_t).
$$

$\text{term}_t$ is set on the transition into a failure state (its successor has no value); $\text{done}_t$ marks every episode boundary, including truncation at 500 steps, and stops the recursion from crossing it. Advantages are normalized to zero mean and unit variance within the batch.

**Clipped surrogate.** With $\rho_t(\theta) = \exp\big(\log \pi_\theta(a_t \mid s_t) - \log \pi_{\theta_{\text{old}}}(a_t \mid s_t)\big)$,

$$
L^{\text{CLIP}}(\theta) = \mathbb{E}_t\Big[\min\big(\rho_t(\theta)\,\hat A_t,\; \mathrm{clip}(\rho_t(\theta),\, 1-\epsilon,\, 1+\epsilon)\,\hat A_t\big)\Big].
$$

**Total loss**, minimized over `epochs` passes of shuffled minibatches from the same batch:

$$
L(\theta, \phi) = -L^{\text{CLIP}}(\theta) + c_v \,\big(V_\phi(s_t) - \hat R_t\big)^2 - c_e\, H\big[\pi_\theta(\cdot \mid s_t)\big],
$$

with the gradient norm clipped before each Adam step. The batch is discarded afterwards: the method is on-policy.

**Inference** is $a = \arg\max_a \pi_\theta(a \mid s)$ with no sampling.

## Implementation notes and deviations

- Defaults: hidden 64, learning rate $3\times10^{-4}$, $\gamma = 0.99$, $\lambda = 0.95$, batch 2048 steps, 10 epochs of minibatch 64, $\epsilon = 0.2$, value coefficient $c_v = 0.5$, entropy coefficient $c_e = 0$, gradient norm clipped at 0.5. These are the paper's MuJoCo settings apart from the network width and the omitted entropy bonus, which the two-action problem does not need.
- `act()` samples from the softmax with the agent's own numpy generator and remembers the log-probability and value for the `learn()` call that follows, so the stored old log-probabilities are exactly those of the collecting policy. `end_episode()` marks the last stored step as an episode boundary. The update fires from inside `learn()` whenever 2048 steps have accumulated, which can be mid-episode; the final step of a batch is bootstrapped through $V(s')$ rather than treated as terminal.
- With the full-range ±12° start distribution, early episodes are short, so the first 2048-step batch spans well over 100 episodes and the first update arrives late. This is why the learning test budget for this solution counts episodes, not updates.
- The value function shares the optimizer with the policy but not the network, as in the paper's continuous-control experiments.
- Runs on the CPU under PyTorch; see `common/deep.py`. Two agents built with the same seed produce identical trajectories.

## Run

```sh
python ../main.py --mode train --soln 2017_ppo --no-render
python ../main.py --mode infer --soln 2017_ppo --theta0 -11
python ../main.py --mode train --soln 2017_ppo --no-render --theta-limit 30    # accepts wider angles
pytest ../tests -k 2017
```

## Result

Seed 0, 5000 training episodes with full-range starts, frozen policy, 20 episodes per start angle:

| start angle | 0° | −8° | +8° | −11° | +11° |
|---|---|---|---|---|---|
| mean steps (max 500) | 500 | 500 | 500 | 500 | 500 |

The 100-episode average first reached 500 at episode 512. Training took 363 s on one CPU core with PyTorch: 2.32 M environment steps at about 6,400 steps/s, or 156 µs per step. Reaching the cap at episode 512 makes PPO the fastest learner in the lineage in episodes, which is why it is the canonical first example on Gymnasium's CartPole-v1.

## Limitations

- On-policy and sample-hungry compared with the replay-based methods: every batch is used for a handful of epochs and thrown away, and each update needs 2048 fresh environment steps. That is negligible here, where a step costs 3 µs, and decisive when the environment is a robot.
- The clipping heuristic bounds the ratio per sample, not the KL divergence per update; large policy changes are still possible in principle, and the stored `kl` diagnostic is the thing to watch.
- The two-action policy is the simplest case of the method. Its strength, and the reason it is the default in practice, shows on continuous and high-dimensional action spaces, where the same code applies with a Gaussian policy head.
