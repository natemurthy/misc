# 1983: Actor-critic on BOXES (Barto, Sutton and Anderson)

**Lineage:** start → [1986 backprop actor-critic](../1986_actor_critic_backprop/README.md) → [1988 TD(λ)](../1988_td/README.md) → [1989 Q-learning](../1989_qlearning/README.md) → [1990 Dyna](../1990_dyna/README.md) → [1992 REINFORCE](../1992_reinforce/README.md) → [1999 continuous Q-learning](../1999_qlearning_continuous/README.md) → [2005 NAC](../2005_nac/README.md) → [2007 CACLA](../2007_cacla/README.md) → [2011 NFQCA](../2011_nfqca/README.md) → [2011 PILCO](../2011_pilco/README.md) → [2013 DQN](../2013_dqn/README.md) → [2015 DDPG](../2015_ddpg/README.md) → [2015 TRPO](../2015_trpo/README.md) → [2017 PPO](../2017_ppo/README.md) → [2018 SAC](../2018_sac/README.md)

**Next:** [1986, replacing the hand-built state decoder with networks](../1986_actor_critic_backprop/README.md)

## Reference

A. G. Barto, R. S. Sutton and C. W. Anderson, ["Neuronlike Adaptive Elements That Can Solve Difficult Learning Control Problems"][barto1983], *IEEE Transactions on Systems, Man, and Cybernetics* SMC-13(5), 1983.

The state decoder comes from D. Michie and R. A. Chambers, "BOXES: An experiment in adaptive control", *Machine Intelligence* 2, 1968.

This is the paper that made cart-pole the standard reinforcement-learning benchmark. The physical system, the ±12° and ±2.4 m failure thresholds and the 0.02 s Euler integration used by every solution in this repository are taken from it; see [the MDP definition](../README.md#the-markov-decision-process).

## The method

Two "neuron-like" elements share a fixed 162-way one-hot encoding of the state, $x_t \in \{0,1\}^{162}$, produced by the BOXES decoder (`common.features.boxes_index`). Each state variable is cut into a few regions, 3 × 3 × 6 × 3 over $(x, \dot x, \theta, \dot\theta)$, and the state's box is the one active input.

**ASE, the Associative Search Element, is the actor.** It has one weight per box and emits a noisy sign:

$$
y_t = \mathrm{sign}\big(w^\top x_t + \eta_t\big),\qquad \eta_t \sim \mathcal N(0, \sigma^2),
$$

with $y_t = +1$ meaning push right. Its weights are updated by an eligibility trace of past (state, action) pairs, scaled by an internal reinforcement $\hat r_t$:

$$
e_i \leftarrow \delta\, e_i + (1-\delta)\, y_t\, x_{i,t}, \qquad
w_i \leftarrow w_i + \alpha\, \hat r_t\, e_i .
$$

**ACE, the Adaptive Critic Element, is the critic.** It predicts the value of the current box, $p_t = v^\top x_t$, and turns the sparse external reward into a dense internal one, the temporal-difference error:

$$
\hat r_t = r_t + \gamma\, p_{t+1} - p_t \qquad (p_{t+1} = 0 \text{ on failure}),
$$

$$
\bar x_i \leftarrow \lambda\, \bar x_i + (1-\lambda)\, x_{i,t}, \qquad
v_i \leftarrow v_i + \beta\, \hat r_t\, \bar x_i .
$$

The ACE is where temporal-difference learning was born. $\hat r_t$ is exactly the TD error that [Sutton (1988)](../1988_td/README.md) later isolated and analysed, and the pair of traces $e$ and $\bar x$ are eligibility traces.

## Why this was a breakthrough

Before 1983 the cart-pole had been attacked by BOXES itself, which kept statistics per box and did not generalize credit across time, and by supervised methods that needed a teacher. The ASE/ACE pair learned to balance from nothing but a failure signal, and did so far faster than BOXES, because the critic converts one delayed failure into a graded signal on every step leading up to it. That decomposition into an actor that acts and a critic that evaluates is the template for every actor-critic method since.

## Implementation notes and deviations

`soln.py` follows the paper's equations exactly. Two things differ.

- **Reward.** The paper delivers −1 at failure and 0 otherwise. This repository fixes the MDP to Gymnasium's +1 per step so every solution solves the same problem. The two rewards give different value functions but the same ordering of policies.
- **Actor step size.** With +1 reward and a zero-initialized critic, $\hat r_t$ is +1 on every early step. The paper's $\alpha = 1000$ would then lock the actor into whichever action it happened to take first. $\alpha$ is reduced to 0.5; $\beta = 0.5$, $\gamma = 0.95$, $\delta = 0.9$, $\lambda = 0.8$ and $\sigma = 0.01$ are the paper's values.

Friction terms in the paper's equations of motion are omitted, as in Gymnasium. Their effect is negligible (a 0.0005 N cart friction against a 10 N push).

Inference (`freeze()`) sets the noise to zero, so the policy is the sign of the box's weight. Exact ties, which only occur in boxes never visited, resolve to "push left" for reproducibility.

## Run

```sh
python ../main.py --mode train --soln 1983_actor_critic --no-render
python ../main.py --mode infer --soln 1983_actor_critic --theta0 -11
pytest ../tests -k 1983
```

## Result

Seed `[0, 5000]` training episodes with full-range starts, frozen policy, 20 episodes per start angle:

| start angle | 0° | −8° | +8° | −11° | +11° |
|---|---|---|---|---|---|
| mean steps (max 500) | 500 | 500 | 500 | 500 | 492 |

The 100-episode average first reached 500 at episode 1602. Because the BOXES decoder covers cart position, this policy also keeps the cart centered, which the angle-only Q-learning grid cannot.

## Limitations

- The decoder is hand-designed for this one task. Changing the physical system means redesigning the boxes. Removing that dependence is the point of the [1986 solution](../1986_actor_critic_backprop/README.md).
- Learning is on-policy and there is no convergence theory for the combined system. That theory arrives piecemeal with TD(λ) in 1988 and Q-learning in 1989.

[barto1983]: https://github.com/david78k/pendulum/blob/master/c/anderson/Neuronlike%20Adaptive%20Elements%20That%20Can%20Solve%20Difficult%20Learning%20Control%20Problems%20Barto1983.pdf
