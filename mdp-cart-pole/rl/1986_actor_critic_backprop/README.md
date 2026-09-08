# 1986: Actor-critic with backprop networks (Anderson)

**Lineage:** [1983 actor-critic](../1983_actor_critic/README.md) → **1986** → [1988 TD(λ)](../1988_td/README.md) → [1989 Q-learning](../1989_qlearning/README.md) → [1990 Dyna](../1990_dyna/README.md) → [1992 REINFORCE](../1992_reinforce/README.md) → [1999 continuous Q-learning](../1999_qlearning_continuous/README.md) → [2005 NAC](../2005_nac/README.md) → [2007 CACLA](../2007_cacla/README.md) → [2011 NFQCA](../2011_nfqca/README.md) → [2011 PILCO](../2011_pilco/README.md) → [2013 DQN](../2013_dqn/README.md) → [2015 DDPG](../2015_ddpg/README.md) → [2015 TRPO](../2015_trpo/README.md) → [2017 PPO](../2017_ppo/README.md) → [2018 SAC](../2018_sac/README.md)

**Previous:** [1983, ASE/ACE on the BOXES decoder](../1983_actor_critic/README.md)

**Next:** [1988, the critic's update isolated as TD(λ)](../1988_td/README.md)

## References

- C. W. Anderson, *Learning and Problem Solving with Multilayer Connectionist Systems*, PhD thesis, University of Massachusetts Amherst, 1986.
- C. W. Anderson, "Strategy Learning with Multilayer Connectionist Representations", *Proceedings of the Fourth International Workshop on Machine Learning*, 1987.
- C. W. Anderson, ["Learning to Control an Inverted Pendulum Using Neural Networks"](https://doi.org/10.1109/37.24809), *IEEE Control Systems Magazine* 9(3), 1989.

Anderson was the third author of the 1983 paper. This line of work is the first neural-network solution to the cart-pole and the direct ancestor of applying deep networks to it.

## What changed from 1983

The 1983 elements were linear in a hand-built feature vector: 162 boxes chosen by a human who already understood the problem. Anderson replaced each element with a two-layer network that reads the raw, normalized four-dimensional state and learns its own hidden features by backpropagation. Everything else about the architecture, an actor that acts and a critic that evaluates, is kept.

The improvement is representational. No one has to decide where the box boundaries go, the same code would work on a different physical system, and the value function can be smooth rather than piecewise constant. The cost is that learning became slower and less predictable, which Anderson reported at the time and which this implementation reproduces: it needs eligibility traces and careful step sizes where the tabular version did not.

## The method

Both networks are `input(4) → tanh(16) → linear(1)`, implemented by hand in numpy in `soln.py` (`_TwoLayerNet`).

**Critic** (Anderson's *evaluation network*): $V(s)$ with TD error

$$
\hat r_t = r_t + \gamma V(s_{t+1}) - V(s_t) \qquad (V = 0 \text{ on failure}).
$$

**Actor** (the *action network*): a logit $z(s)$ giving $\pi(\text{right} \mid s) = \sigma(z(s))$, action sampled from that Bernoulli distribution.

**Updates**, with eligibility traces on every network parameter, decayed by $\gamma\lambda$ each step and reset at episode end:

$$
e^{c} \leftarrow \gamma\lambda\, e^{c} + \nabla_w V(s_t), \qquad
w^{c} \leftarrow w^{c} + \eta_c\, \hat r_t\, e^{c},
$$

$$
e^{a} \leftarrow \gamma\lambda\, e^{a} + (a_t - \sigma(z_t))\, \nabla_w z(s_t), \qquad
w^{a} \leftarrow w^{a} + \eta_a\, \hat r_t\, e^{a}.
$$

$(a_t - \sigma(z_t))\nabla_w z$ is $\nabla_w \log \pi(a_t \mid s_t)$ for a sigmoid-Bernoulli policy, so the actor update is the TD error times the score function: a one-step actor-critic policy gradient, six years before [REINFORCE](../1992_reinforce/README.md) gave that form its theory.

## Implementation notes and deviations

- **Traces are essential here.** A one-step version (no traces) was tried first and never learned: the critic stays nearly flat, so the actor receives almost no signal. With traces the same code reaches the 500-step cap within about 1200 episodes.
- **Critic initialization.** With +1-per-step reward and an all-zero critic, every early TD error is positive, which reinforces whatever action was taken and collapses the policy to always-left or always-right within a few hundred episodes. The critic's output bias is initialized to $r/(1-\gamma)$, the value of a state that never fails, so early TD errors are near zero on ordinary steps and strongly negative at failures. That recreates the shape of the original papers' −1 failure signal without changing the MDP.
- **Reward scaling.** Rewards are multiplied by 0.01 inside the agent so the critic's targets are order 1. Positive scaling does not change the optimal policy.
- Anderson used $\gamma = 0.9$ and five hidden units. Here $\gamma = 0.99$ to match the rest of the repository, 16 hidden units, $\lambda = 0.8$, and step sizes $\eta_a = \eta_c = 0.1$. Critic step sizes of 0.5 and above diverge.

## Wider angles

This solution reads the raw scaled state, so it accepts `--theta-limit` above 12° (see [Wider angles](../README.md#wider-angles)). Trained on ±40° starts it recovered from 20° most of the time but failed by pole angle from 30°.

## Run

```sh
python ../main.py --mode train --soln 1986_actor_critic_backprop --no-render
python ../main.py --mode infer --soln 1986_actor_critic_backprop --theta0 11
pytest ../tests -k 1986
```

## Result

Seed `[0, 5000]` training episodes with full-range starts, frozen policy, 20 episodes per start angle:

| start angle | 0° | −8° | +8° | −11° | +11° |
|---|---|---|---|---|---|
| mean steps (max 500) | 500 | 500 | 500 | 500 | 500 |

The 100-episode average first reached 500 at episode 1242. Training is slower in wall-clock terms than the tabular methods because each step does two forward and backward passes, about 40 seconds for 5000 episodes.

## Limitations

- Sensitive to step sizes and initialization in a way the tabular methods are not. Different seeds occasionally stall for a few hundred episodes before taking off.
- Still a one-step, on-policy method with no convergence guarantee. The value side of this architecture is what the next two solutions put on a firmer footing.
