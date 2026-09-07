# 2018: Soft Actor-Critic (Haarnoja, Zhou, Abbeel and Levine)

**Lineage:** [1983 actor-critic](../1983_actor_critic/README.md) → [1986 backprop actor-critic](../1986_actor_critic_backprop/README.md) → [1988 TD(λ)](../1988_td/README.md) → [1989 Q-learning](../1989_qlearning/README.md) → [1990 Dyna](../1990_dyna/README.md) → [1992 REINFORCE](../1992_reinforce/README.md) → [1999 continuous Q-learning](../1999_qlearning_continuous/README.md) → [2011 NFQCA](../2011_nfqca/README.md) → [2013 DQN](../2013_dqn/README.md) → [2015 DDPG](../2015_ddpg/README.md) → [2015 TRPO](../2015_trpo/README.md) → [2017 PPO](../2017_ppo/README.md) → **2018 SAC**

**Previous:** [2017 PPO](../2017_ppo/README.md)

**Next:** end of the reinforcement-learning lineage. The hand-off to the optimal-control lineage is in [`../../mpc/README.md`](../../mpc/README.md): SAC's deterministic mean action is a graded force, directly comparable with linear state feedback and LQR on the same plant.

## References

- T. Haarnoja, A. Zhou, P. Abbeel and S. Levine, ["Soft Actor-Critic: Off-Policy Maximum Entropy Deep Reinforcement Learning with a Stochastic Actor"](https://arxiv.org/abs/1801.01290), *ICML* 2018.
- T. Haarnoja et al., ["Soft Actor-Critic Algorithms and Applications"](https://arxiv.org/abs/1812.05905), arXiv 1812.05905, 2018. Adds the automatic temperature adjustment used here.
- Related: S. Fujimoto, H. van Hoof and D. Meger, ["Addressing Function Approximation Error in Actor-Critic Methods"](https://arxiv.org/abs/1802.09477) (TD3), *ICML* 2018, for the twin-critic minimum that SAC also adopts.

## What changed from DDPG

DDPG works when it works. Its deterministic actor has no exploration of its own, so noise is added from outside and tuned per task; its single critic overestimates, and the actor climbs the overestimate; and its results swing with the seed. SAC keeps DDPG's off-policy actor-critic with replay and target networks and changes the objective being optimized. Instead of expected return alone it maximizes return plus the entropy of the policy at every state, weighted by a temperature $\alpha$:

$$
J(\pi) = \sum_t \mathbb E_{(s_t, a_t) \sim \pi}\Big[ r_t + \alpha\, \mathcal H\big(\pi(\cdot \mid s_t)\big) \Big].
$$

Four things follow from that one change:

- **A stochastic policy whose spread is optimized.** The actor is a Gaussian squashed through tanh. Where the critic is flat the entropy bonus keeps the policy wide, so it explores; where one action is clearly better the policy narrows on its own. Exploration is no longer an add-on.
- **A soft Bellman target.** The value of the next state includes the entropy of the next action, so the critic learns the maximum-entropy value function rather than the ordinary one.
- **Twin critics.** Two Q-networks are trained on the same targets and the minimum of the two is used everywhere a value is read. This counteracts the maximization bias that Thrun and Schwartz described in 1993 and that DDPG's single critic feeds.
- **Automatic temperature.** $\alpha$ is itself learned so that the policy's entropy stays near a target, here $-1$, minus the action dimension. The original SAC needed $\alpha$ hand-tuned per reward scale; with this it does not.

The practical result is the off-policy continuous-control method that runs with one set of defaults across tasks. In the lineage it is where the actor-critic of 1983, the replay of 1992 and the stabilizers of 2013 meet a principled account of exploration.

## The method

**Policy.** $\pi_\phi(a \mid s)$ is a Gaussian in a pre-squash variable $u$, mapped to the action range by $\tanh$:

$$
u = \mu_\phi(s) + \sigma_\phi(s)\, \epsilon, \quad \epsilon \sim \mathcal N(0, 1), \qquad a = \tanh(u), \qquad
\log \pi_\phi(a \mid s) = \log \mathcal N\big(u; \mu_\phi(s), \sigma_\phi(s)\big) - \log\big(1 - a^2 + \varepsilon\big).
$$

Writing the sample as a deterministic function of $\epsilon$ is the reparameterization trick; it lets the actor loss be differentiated through the sampled action.

**Critics.** Two networks $Q_{\theta_1}, Q_{\theta_2}$ on $(s, a)$ with slowly tracking targets $\bar\theta_i \leftarrow \tau\theta_i + (1-\tau)\bar\theta_i$. For a replayed transition $(s, a, r, s', d)$, with $a' \sim \pi_\phi(\cdot \mid s')$ sampled fresh:

$$
y = r + \gamma (1 - d)\Big[ \min_i Q_{\bar\theta_i}(s', a') - \alpha \log \pi_\phi(a' \mid s') \Big], \qquad
L_Q = \sum_{i=1}^{2} \big(Q_{\theta_i}(s, a) - y\big)^2 .
$$

**Actor.** With $\tilde a \sim \pi_\phi(\cdot \mid s)$ reparameterized,

$$
L_\pi = \mathbb E_{s}\Big[ \alpha \log \pi_\phi(\tilde a \mid s) - \min_i Q_{\theta_i}(s, \tilde a) \Big].
$$

**Temperature.** With target entropy $\bar{\mathcal H} = -1$,

$$
L_\alpha = \mathbb E_{s}\Big[ -\log\alpha\,\big(\log \pi_\phi(\tilde a \mid s) + \bar{\mathcal H}\big) \Big],
$$

descended in $\log \alpha$ so that $\alpha$ stays positive. When the policy is more random than the target this pushes $\alpha$ down, and when it is more deterministic it pushes $\alpha$ up.

Inference (`freeze()`) applies the deterministic mean action $\tanh(\mu_\phi(s))$.

## Implementation notes and deviations

- `soln.py` is PyTorch on the CPU (see `common/deep.py`): actor `4 → 64 → 64 → 2` producing mean and log-std (log-std clamped to $[-5, 2]$), twin critics `5 → 64 → 64 → 1` on the concatenated state and action, ReLU throughout. All random draws use per-agent generators, so a seed reproduces a run exactly.
- Rewards are scaled by 0.1 inside the agent so that Q-values are order 10 rather than 100. With automatic temperature SAC is far less sensitive to reward scale than the original paper's fixed-$\alpha$ version, but the scaling keeps the critics' early targets modest.
- One gradient update per environment step after 1000 warm-up transitions, batch 128, buffer 100 000, Adam at $3 \times 10^{-4}$ for actor, critics and temperature, $\tau = 0.005$, $\gamma = 0.99$. These are the paper's defaults apart from network width.
- The temperature is held in a one-parameter module so it is saved and restored with the networks.
- On this task $\alpha$ collapses to about $10^{-3}$ within a few hundred episodes: once the pole is balanced the entropy bonus is worth almost nothing relative to the +1 per step, and the policy becomes nearly deterministic. That is the mechanism working as intended.

## Run

```sh
python ../main.py --mode train --soln 2018_sac --no-render
python ../main.py --mode infer --soln 2018_sac --theta0 -11
python ../main.py --mode train --soln 2018_sac --no-render --theta-limit 30    # wider angles
pytest ../tests -k 2018
```

The progress bar's diagnostics are the current temperature `alpha` and the last critic loss.

## Result

Seed 0, 5000 training episodes with full-range starts, frozen (mean-action) policy, 20 episodes per start angle:

| start angle | 0° | −8° | +8° | −11° | +11° |
|---|---|---|---|---|---|
| mean steps (max 500) | 500 | 500 | 500 | 500 | 500 |

The 100-episode average first reached 500 at episode 351, the fewest episodes of any solution in the repository, and stayed there: the final 100-episode average was 499.1, with no late collapse of the kind DQN and DDPG show. The price is wall clock. Training took 4290 s (71 min) on one CPU core with PyTorch: 2.21 M environment steps at about 515 steps/s, or 1941 µs per step. Every step trains two critics, the actor and the temperature on a minibatch of 128, and because the agent balances from episode 350 onward, almost every one of the 5000 episodes runs the full 500 steps. Per unit of *experience* SAC is the most efficient method here; per unit of compute it is the least.

## Limitations

- Per step it is the most expensive learner in the repository: five networks, three optimizers, two forward passes of the actor per update. Cart-pole does not need any of that, and the tabular methods reach the same 500 steps.
- The maximum-entropy objective changes what is optimal. When entropy is worth something, the policy deliberately does not commit fully, so the learned Q-values are not the ordinary optimal values and a very small $\alpha$ is needed before the greedy mean action is the true optimum. Automatic temperature handles this here because the +1-per-step reward dwarfs the entropy term.
- Like every off-policy method with bootstrapping and function approximation it has no convergence guarantee. In practice it is markedly more reliable than DDPG on the same seeds, which is the whole point.
