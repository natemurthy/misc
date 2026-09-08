# 2015: Trust Region Policy Optimization (Schulman, Levine, Moritz, Jordan and Abbeel)

**Lineage:** [1983 actor-critic](../1983_actor_critic/README.md) → [1986 backprop actor-critic](../1986_actor_critic_backprop/README.md) → [1988 TD(λ)](../1988_td/README.md) → [1989 Q-learning](../1989_qlearning/README.md) → [1990 Dyna](../1990_dyna/README.md) → [1992 REINFORCE](../1992_reinforce/README.md) → [1999 continuous Q-learning](../1999_qlearning_continuous/README.md) → [2005 NAC](../2005_nac/README.md) → [2007 CACLA](../2007_cacla/README.md) → [2011 NFQCA](../2011_nfqca/README.md) → [2011 PILCO](../2011_pilco/README.md) → [2013 DQN](../2013_dqn/README.md) → [2015 DDPG](../2015_ddpg/README.md) → **2015 TRPO** → [2017 PPO](../2017_ppo/README.md) → [2018 SAC](../2018_sac/README.md)

**Previous:** [2015 DDPG](../2015_ddpg/README.md)

**Next:** [2017 PPO](../2017_ppo/README.md)

## Reference

- J. Schulman, S. Levine, P. Moritz, M. Jordan and P. Abbeel, ["Trust Region Policy Optimization"](https://arxiv.org/abs/1502.05477), *ICML* 2015, arXiv 1502.05477.
- S. Kakade, "A Natural Policy Gradient", *NIPS* 2001. The update direction TRPO takes.
- J. Schulman, P. Moritz, S. Levine, M. Jordan and P. Abbeel, ["High-Dimensional Continuous Control Using Generalized Advantage Estimation"](https://arxiv.org/abs/1506.02438), arXiv 1506.02438, 2016. The advantage estimator used here.

## What changed

**From REINFORCE (1992).** REINFORCE follows a noisy estimate of the return's gradient with a fixed step size in parameter space. The same step that is safe when the policy is nearly deterministic can be catastrophic when it is not, because a small change in parameters can be a large change in the distribution over actions, and a policy gradient method that damages its policy also damages the data it will collect next, with no way back. TRPO measures the step in *policy* space instead: it maximizes a surrogate objective, the importance-weighted advantage, subject to a constraint on the mean KL divergence between the old and new policies. The paper proves that improving the surrogate under such a bound cannot decrease the true expected return by more than a known amount, the first monotonic-improvement guarantee for a policy-gradient method with function approximation.

**From the actor-critics (1983, 1986).** Those methods also learned a value function and a policy, but chose their step sizes by hand, and this repository's 1986 README records how narrow the workable band was. TRPO makes the step size a consequence of the trust-region radius, one interpretable number, and lets the line search reject any step that violates it.

**From the value-based line (2013 DQN, 2015 DDPG).** TRPO is on-policy: every batch of experience is collected by the current policy and discarded after one update. It gives up replay's data reuse for the guarantee that the data matches the policy being improved.

## The method

Let $\pi_\theta(a \mid s)$ be the stochastic policy, here a softmax over two logits from a network on the normalized state, and $\pi_{\theta_{\text{old}}}$ the policy that collected the batch. With advantage estimates $\hat A_t$ the trust-region problem is

$$
\max_\theta\ L(\theta) = \mathbb E_t\!\left[ \frac{\pi_\theta(a_t \mid s_t)}{\pi_{\theta_{\text{old}}}(a_t \mid s_t)}\, \hat A_t \right]
\qquad \text{subject to} \qquad
\mathbb E_t\!\left[ D_{\mathrm{KL}}\big(\pi_{\theta_{\text{old}}}(\cdot \mid s_t)\,\|\,\pi_\theta(\cdot \mid s_t)\big) \right] \le \delta .
$$

Expanding the objective to first order and the constraint to second order around $\theta_{\text{old}}$ gives a natural-gradient step (Kakade 2001):

$$
\theta = \theta_{\text{old}} + \sqrt{\frac{2\delta}{g^\top F^{-1} g}}\; F^{-1} g,
\qquad g = \nabla_\theta L\big|_{\theta_{\text{old}}},\quad F = \nabla^2_\theta\, \overline{D_{\mathrm{KL}}}\big|_{\theta_{\text{old}}} .
$$

$F$ is the Fisher information matrix of the policy. It is never formed: $F^{-1} g$ is found by conjugate gradient, which only needs products $F v$, and each of those is a double backpropagation, the gradient of $(\nabla_\theta \overline{D_{\mathrm{KL}}} \cdot v)$. A backtracking line search then shrinks the step by a factor $\beta^j$ until the *exact* KL is within $\delta$ and the surrogate has improved, so the quadratic approximation is checked rather than trusted.

The advantages come from a learned value baseline $V_\phi(s)$ through generalized advantage estimation,

$$
\delta_t = r_t + \gamma\, V_\phi(s_{t+1}) - V_\phi(s_t), \qquad
\hat A_t = \sum_{k \ge 0} (\gamma\lambda)^k\, \delta_{t+k},
$$

with $V_\phi(s_{t+1}) = 0$ on failure and the sum cut at episode boundaries. The baseline is fitted to $\hat A_t + V_\phi(s_t)$ by Adam after each policy step.

## Implementation notes and deviations

- `soln.py` uses PyTorch on the CPU (see `common/deep.py`); autograd's double backpropagation is what makes the Fisher-vector product a few lines rather than a derivation.
- Policy and value networks are each 4 → 64 → 64 with tanh units. Defaults: $\delta = 0.01$, $\gamma = 0.99$, $\lambda = 0.97$, 2048 steps per batch, 10 conjugate-gradient iterations with damping 0.1, 10 backtracking steps with $\beta = 0.8$, value fit with Adam at $10^{-3}$ for 10 full-batch epochs. Advantages are normalized per batch.
- Episodes are usually shorter than a batch, so a batch spans several episodes, including partial ones at either end. Terminated transitions bootstrap from zero; a truncated or cut episode bootstraps from $V_\phi$ of its last next-state, which is the `done` versus `terminated` distinction the environment already makes.
- The 2015 paper used single-path or vine sampling with plain empirical returns; GAE (2016) is the estimator every later TRPO implementation adopted and is used here.
- Actions are discrete. The same code works with a Gaussian policy, but the two-push cart-pole is the standard setting and keeps the comparison to the 1992 policy direct: same task, same objective, different step rule.
- The agent reads the raw scaled state, so it accepts `--theta-limit` above 12° (see [Wider angles](../README.md#wider-angles)).

## Run

```sh
python ../main.py --mode train --soln 2015_trpo --no-render
python ../main.py --mode infer --soln 2015_trpo --theta0 -11
pytest ../tests -k trpo
```

## Result

Seed 0, 5000 training episodes with full-range starts, frozen policy, 20 episodes per start angle:

| start angle | 0° | −8° | +8° | −11° | +11° |
|---|---|---|---|---|---|
| mean steps (max 500) | 500 | 500 | 500 | 500 | 500 |

The 100-episode average first reached 500 at episode 2530. Training took 182 s on one CPU core with PyTorch: 2.21 M environment steps at about 12,196 steps/s, or 82 µs per step. Every trust-region step in the run was accepted with KL at or below 0.01. Learning is monotone in a way none of the earlier methods are: the 100-episode average never fell back once it rose.

## Limitations

- On-policy: each batch is used once, so it needs far more environment steps than DQN or DDPG for the same result. On a cart-pole simulator that steps in microseconds that costs nothing; on a robot it is the reason the off-policy line exists.
- Each update solves a conjugate-gradient problem and a line search, which is heavier per update than a gradient step and awkward with architectures that share parameters between policy and value or use dropout and normalization layers. PPO (2017) keeps the trust-region idea and drops the machinery.
- The KL bound is a bound on the policy distribution, not on performance in the environment; the monotonic-improvement theorem holds for the exact surrogate and constraint, and the sampled, approximate version can still take a bad step.
