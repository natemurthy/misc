# 1990: Dyna-Q (Sutton), learning plus planning with a learned model

**Lineage:** [1983 actor-critic](../1983_actor_critic/README.md) → [1986 backprop actor-critic](../1986_actor_critic_backprop/README.md) → [1988 TD(λ)](../1988_td/README.md) → [1989 Q-learning](../1989_qlearning/README.md) → **1990** → [1992 REINFORCE](../1992_reinforce/README.md)

**Previous:** [1989, Q-learning](../1989_qlearning/README.md)

**Next:** [1992, dropping the value function entirely](../1992_reinforce/README.md)

## References

- R. S. Sutton, ["Integrated Architectures for Learning, Planning, and Reacting Based on Approximating Dynamic Programming"](http://incompleteideas.net/papers/sutton-90.pdf), *Proceedings of the Seventh International Conference on Machine Learning*, 1990.
- R. S. Sutton, ["Dyna, an Integrated Architecture for Learning, Planning, and Reacting"](https://doi.org/10.1145/122344.122377), *SIGART Bulletin* 2(4), 1991.

## What changed from 1989

Q-learning uses each real transition once and discards it. Dyna keeps a *model* of the environment, learned from those same transitions, and after every real step spends some computation "planning": drawing simulated transitions from the model and applying the very same Q-learning update to them. Learning from real experience, learning the model, and planning with the model all share one Q-table and one update rule, so planning is nothing more than Q-learning on remembered experience.

Two things are new in the lineage:

- **Explicitly model-based.** The [1988](../1988_td/README.md) solution used the *true* dynamics to look ahead. Dyna *learns* its model from data, so it needs no prior knowledge of the plant, and yet it can still do the extra value propagation that a model makes possible.
- **Sample efficiency traded for computation.** Real environment steps are usually the expensive resource. Dyna lets the agent squeeze more value updates out of each one, at the cost of CPU time between steps.

Dyna also anticipates experience replay: a buffer of past transitions replayed through the same update is a Dyna sample model in all but name.

## The method

Tabular Dyna-Q over the same aggregated state $\phi(s)$ as the 1989 solution (8 × 16 over $\theta, \dot\theta$):

```
observe (s, a, r, s', terminal)
Q(s,a) <- Q(s,a) + α [ y - Q(s,a) ]                 direct RL     (identical to 1989)
Model(s,a) <- Model(s,a) ∪ {(r, s', terminal)}      model learning
repeat n times:                                      planning
    (s, a)  <- a previously visited state-action pair, chosen uniformly
    (r, s', terminal) ~ Model(s, a)
    Q(s,a) <- Q(s,a) + α [ y - Q(s,a) ]
```

with $y = r$ on failure and $y = r + \gamma \max_{a'} Q(s', a')$ otherwise, $\alpha = 0.1$, $\gamma = 0.99$, $n = 5$ planning steps, and the same ε schedule as Q-learning.

### The model is a sample model

Sutton's 1990 paper assumed a deterministic world and stored one outcome per $(s, a)$. On this problem the *aggregated* state makes transitions between cells stochastic: two real states in the same cell can land in different cells. A one-outcome model then plans on stale, possibly unrepresentative successors, and in testing it made the agent markedly worse than plain Q-learning. So `soln.py` keeps the 32 most recent outcomes per $(s, a)$ and samples one when planning. That is the *sample model* form of Dyna-Q described in Sutton and Barto's textbook.

The model is training state only; `save()` writes just the Q-table, so a saved Dyna policy is a Q-learning policy and the two are interchangeable at inference.

## Implementation notes

- `test_dyna_with_zero_planning_steps_is_exactly_qlearning` checks that with $n = 0$ this agent reproduces the 1989 agent's training trajectory step for step. The planning loop is the only difference.
- More planning steps are not better here. With 20 steps the agent plans too heavily on outcomes gathered under earlier, more exploratory behaviour and its policy degrades late in training. Five was the best of the values tried.

## Run

```sh
python ../main.py --mode train --soln 1990_dyna --no-render
python ../main.py --mode infer --soln 1990_dyna --theta0 -8
pytest ../tests -k dyna
```

## Result

Seed 0, 5000 training episodes with full-range starts, frozen policy, 20 episodes per start angle:

| start angle | 0° | −8° | +8° | −11° | +11° |
|---|---|---|---|---|---|
| mean steps (max 500) | 495 | 488 | 307 | 425 | 257 |

Best 100-episode training average 247.

## Limitations, and an honest note on this benchmark

Dyna's advantage is largest when reward is sparse and real steps are scarce: a maze with one goal, a robot with a slow clock. CartPole with +1 per step is dense-reward and cheap to simulate, and the aggregated state makes the learned model noisy. On this task Dyna is roughly on par with Q-learning per episode and noticeably slower per second, and its results vary more between seeds. It is included because it is the first learned-model method in the lineage, not because it wins here.
