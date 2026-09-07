# 1988: TD(λ) (Sutton), used for control by one-step lookahead

**Lineage:** [1983 actor-critic](../1983_actor_critic/README.md) → [1986 backprop actor-critic](../1986_actor_critic_backprop/README.md) → **1988** → [1989 Q-learning](../1989_qlearning/README.md) → [1990 Dyna](../1990_dyna/README.md) → [1992 REINFORCE](../1992_reinforce/README.md) → [1999 continuous Q-learning](../1999_qlearning_continuous/README.md) → [2011 NFQCA](../2011_nfqca/README.md) → [2013 DQN](../2013_dqn/README.md) → [2015 DDPG](../2015_ddpg/README.md) → [2015 TRPO](../2015_trpo/README.md) → [2017 PPO](../2017_ppo/README.md) → [2018 SAC](../2018_sac/README.md)

**Previous:** [1986, networks in place of the BOXES decoder](../1986_actor_critic_backprop/README.md)

**Next:** [1989, action values remove the need for a model](../1989_qlearning/README.md)

## Reference

R. S. Sutton, ["Learning to Predict by the Methods of Temporal Differences"](https://doi.org/10.1007/BF00115009), *Machine Learning* 3:9-44, 1988. ([author's copy with erratum](http://incompleteideas.net/papers/sutton-88-with-erratum.pdf))

## What changed from 1986

The 1983 and 1986 systems each contained a critic whose update rule was justified by analogy and by working. Sutton's 1988 paper pulled that rule out, named it TD(λ), and analysed it on its own as a method for *prediction*: learning to estimate the expected future reward from a state under a fixed policy. The paper showed that TD methods use experience more efficiently than supervised (Monte Carlo) fitting of the same targets, gave the λ-trace its general form, and proved convergence for TD(0) with linear function approximation.

The improvement is conceptual rather than architectural. Every value-based method after this, including the Q-learning in the next directory, is a TD method, and the actor-critic's critic is understood as TD(λ) running inside a larger system.

## The method

TD(λ) learns a state-value table $V$ over an aggregated state $\phi(s)$ (`common.features.GridDiscretizer`, here 3 × 3 × 16 × 32 over $x, \dot x, \theta, \dot\theta$):

$$
\delta_t = r_t + \gamma V(\phi(s_{t+1})) - V(\phi(s_t)) \qquad (V = 0 \text{ on failure}),
$$

$$
z \leftarrow \gamma\lambda\, z,\quad z[\phi(s_t)] = 1 \quad\text{(replacing trace)},\qquad
V \leftarrow V + \alpha\, \delta_t\, z .
$$

with $\alpha = 0.1$, $\gamma = 0.99$, $\lambda = 0.8$.

### From prediction to control

TD(λ) alone does not choose actions. Following Samuel's checkers program (1959) and, later, Tesauro's TD-Gammon (1992), the learned state values are turned into a controller by looking one step ahead with a model of the environment and taking the action whose successor is worth most:

$$
a_t = \arg\max_{a \in \{0,1\}} \Big[ r + \gamma\, V\big(\phi(f(s_t, a))\big) \Big],
$$

where $f$ is the true one-step dynamics, `CartPoleEnv.dynamics`, and the bracket is just $r$ when $f(s_t, a)$ is a failure state. Exploration is ε-greedy over this choice, with ε decaying from 1 to 0.01 over training.

So this solution is **model-free in learning** ($V$ is fit from sampled transitions and never uses $f$) but **model-based in acting**. The test `test_1988_lookahead_uses_no_model_at_learning_time` checks exactly that split. Removing the need for $f$ at decision time is what Q-learning does next.

## Implementation notes

- A finer grid than the Q-learning solution's (16 × 32 versus 8 × 16 over the pole variables, plus 3 × 3 over the cart) is used because the lookahead compares two successor states that are only 0.02 s apart. On a coarse grid they often land in the same cell and the comparison is a tie.
- Replacing traces (set to 1) are used rather than accumulating ones; on a tabular representation they are better behaved with a constant step size.

## Run

```sh
python ../main.py --mode train --soln 1988_td --no-render
python ../main.py --mode infer --soln 1988_td --theta0 -8
pytest ../tests -k 1988
```

## Result

Seed `[0, 5000]` training episodes with full-range starts, frozen policy, 20 episodes per start angle:

| start angle | 0° | −8° | +8° | −11° | +11° |
|---|---|---|---|---|---|
| mean steps (max 500) | 486 | 457 | 467 | 479 | 447 |

Best 100-episode training average 474. The grid has 4608 cells and $V$ is a single number per cell, so this is still a small table.

## Limitations

- Needs the model $f$ to act. In the real world that means either knowing the dynamics or learning them first.
- Value estimates are for the *behaviour* policy (on-policy). As ε decays the policy changes under the values, which is workable here but has no guarantee.
- Tabular over an aggregated state, with the same coarse-cell artefacts as the Q-learning solution.
