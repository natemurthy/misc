# 1989: Q-learning (Watkins)

**Lineage:** [1983 actor-critic](../1983_actor_critic/README.md) → [1986 backprop actor-critic](../1986_actor_critic_backprop/README.md) → [1988 TD(λ)](../1988_td/README.md) → **1989** → [1990 Dyna](../1990_dyna/README.md) → [1992 REINFORCE](../1992_reinforce/README.md)

**Previous:** [1988, TD(λ) with model-based lookahead](../1988_td/README.md)

**Next:** [1990, adding a learned model and planning](../1990_dyna/README.md)

This directory holds the default solution used by `main.py`, and this README also carries the full formulation of the shared MDP that every other solution links to.

## References

- C. J. C. H. Watkins, [*Learning from Delayed Rewards*](https://www.cs.rhul.ac.uk/~chrisw/new_thesis.pdf), PhD thesis, University of Cambridge, 1989. Introduces Q-learning.
- C. J. C. H. Watkins and P. Dayan, ["Q-learning"](https://doi.org/10.1007/BF00992698), *Machine Learning* 8:279-292, 1992. The convergence proof.

## What changed from 1988

TD(λ) learns the value of *states*, $V(s)$, and needs a model $f(s, a)$ to compare the actions available from a state. Watkins' idea was to learn the value of *state-action pairs* instead:

$$
Q^*(s, a) = \text{expected return from taking } a \text{ in } s \text{ and acting optimally afterwards.}
$$

With $Q$ in hand the greedy action is $\arg\max_a Q(s, a)$, a table lookup. No model, no lookahead. Two further properties fall out of the same change:

- **Off-policy.** The update target uses $\max_{a'} Q(s', a')$, the value of the best next action, regardless of which action the exploring agent actually takes next. So Q-learning estimates the *optimal* value function while behaving ε-greedily. TD(λ) and the actor-critics estimate the value of the policy being followed.
- **A theory.** Watkins showed Q-learning is a sample-based, asynchronous form of value iteration from dynamic programming, and Watkins and Dayan proved it converges to $Q^*$ on a finite MDP if every pair is visited infinitely often and the step sizes decay appropriately. This is the point where reinforcement learning and dynamic programming become one subject.

The rest of this file gives the MDP, the Bellman equation Q-learning solves, the concrete algorithm, and the physical reasons behind the problem's bounds.

## RL formulation

### The Markov decision process

The problem is the finite-horizon, discounted MDP $(\mathcal S, \mathcal A, P, R, \gamma, \rho_0)$:

- **State** $s = (x, \dot x, \theta, \dot\theta) \in \mathcal S \subset \mathbb R^4$: cart position and velocity, pole angle from vertical and angular velocity.
- **Action** $a \in \mathcal A = \{0, 1\}$: apply a horizontal force $F = -10\,\text{N}$ (push left) or $F = +10\,\text{N}$ (push right) to the cart for one time step $\tau = 0.02\,\text{s}$.
- **Transition** $P(s' \mid s, a)$ is deterministic, $s' = f(s, a)$, given by Euler integration of the cart-pole equations of motion from [Barto, Sutton and Anderson (1983)][barto1983], without their friction terms:

$$
\ddot\theta = \frac{g\sin\theta - \cos\theta \cdot \tfrac{F + m_p l \dot\theta^2 \sin\theta}{m_c + m_p}}
                   {l\left(\tfrac{4}{3} - \tfrac{m_p \cos^2\theta}{m_c + m_p}\right)},
\qquad
\ddot x = \frac{F + m_p l \dot\theta^2 \sin\theta}{m_c + m_p} - \frac{m_p l \ddot\theta \cos\theta}{m_c + m_p},
$$

$$
x' = x + \tau\dot x,\quad \dot x' = \dot x + \tau\ddot x,\quad
\theta' = \theta + \tau\dot\theta,\quad \dot\theta' = \dot\theta + \tau\ddot\theta,
$$

  with $g = 9.8$, cart mass $m_c = 1.0$, pole mass $m_p = 0.1$ and pole half-length $l = 0.5$. In code this is `CartPoleEnv.dynamics` in `common/env.py`.
- **Reward** $R(s, a, s') = 1$ for every transition, including the one that terminates. Return is therefore the number of steps survived.
- **Terminal states** $\mathcal S_{\text{term}} = \{ s : |x| > 2.4 \ \text{or}\ |\theta| > 12^\circ \}$. Episodes are also truncated at $T = 500$ steps; truncation is a horizon, not a failure, and is treated differently in the update below.
- **Discount** $\gamma = 0.99$.
- **Start distribution** $\rho_0$: all four components uniform in $[-0.05, 0.05]$, except that in training the angle is drawn uniformly from $[-12^\circ, 12^\circ]$ (see `--theta-range`). Changing $\rho_0$ changes which states are visited during learning but does not change $P$, $R$ or the optimal value function.

The objective is to find a policy $\pi : \mathcal S \to \mathcal A$ maximizing the expected discounted return (the sum of rewards, called "total reward" in the plots)

$$
G_t = \sum_{k=0}^{\infty} \gamma^k r_{t+k+1}.
$$

Because every reward is 1, an episode that survives $n$ more steps has $G_t = (1 - \gamma^n)/(1 - \gamma)$, which saturates at $1/(1-\gamma) = 100$. So the discount gives an effective planning horizon of about 100 steps (2 s), and maximizing return is the same as surviving longer.

A note on words. The per-step +1 is the *reward*. Its sum over an episode is what the literature calls the *return*. The plots and console output say "total reward" instead, since to a programmer "return" reads as a function returning.

### Bellman optimality

The optimal action-value function $Q^*(s, a)$ is the expected return from taking $a$ in $s$ and acting optimally thereafter. It is the unique fixed point of the Bellman optimality equation, which for this deterministic environment reads

$$
Q^*(s, a) =
\begin{cases}
1, & f(s, a) \in \mathcal S_{\text{term}} \\
1 + \gamma \max_{a'} Q^*\big(f(s, a), a'\big), & \text{otherwise.}
\end{cases}
$$

The optimal policy is greedy with respect to $Q^*$:

$$
\pi^*(s) = \arg\max_{a \in \{0, 1\}} Q^*(s, a).
$$

Every solution in this repository is trying to find $\pi^*$ for this one equation. They differ in what they estimate (a state value, an action value, or the policy directly) and in whether they use $f$.

### Model-free, off-policy, tabular Q-learning

This is a **model-free** method. Although $f(s, a)$ is written above, the agent never evaluates it, never learns an approximation of it, and never plans by rolling it forward. It only observes sampled transitions $(s_t, a_t, r_{t+1}, s_{t+1})$ and updates value estimates from them. The [1988](../1988_td/README.md) solution uses $f$ to act, and the [1990](../1990_dyna/README.md) solution learns an approximation of it to plan; neither is needed here.

**State aggregation.** $\mathcal S$ is continuous, so the agent works with a discretized state $\phi(s)$ (`common.features.GridDiscretizer`). Cart position and velocity are collapsed into a single bin each; the pole angle and angular velocity are clipped and mapped onto uniform grids:

$$
\phi(s) = \left(
\operatorname{round}\!\Big(7 \cdot \tfrac{\operatorname{clip}(\theta, -0.21, 0.21) + 0.21}{0.42}\Big),\;
\operatorname{round}\!\Big(15 \cdot \tfrac{\operatorname{clip}(\dot\theta, -3.5, 3.5) + 3.5}{7}\Big)
\right) \in \{0..7\} \times \{0..15\}.
$$

**The learned object is a table, not a network.** The action-value estimate is an array $Q \in \mathbb R^{8 \times 16 \times 2}$, i.e. 256 numbers, one per (angle bin, angular-velocity bin, action), initialized to zero. This is what `--mode train` produces and what the saved `.npz` contains.

**Update rule.** After each transition the single visited entry is moved toward the sampled Bellman target:

$$
Q\big(\phi(s_t), a_t\big) \leftarrow Q\big(\phi(s_t), a_t\big) + \alpha\Big[ y_t - Q\big(\phi(s_t), a_t\big) \Big],
\qquad
y_t =
\begin{cases}
r_{t+1}, & s_{t+1} \in \mathcal S_{\text{term}} \\
r_{t+1} + \gamma \max_{a'} Q\big(\phi(s_{t+1}), a'\big), & \text{otherwise,}
\end{cases}
$$

with learning rate $\alpha = 0.1$. The bracketed quantity is the temporal-difference error. The target bootstraps on truncated (step 500) transitions but not on terminated ones: hitting the horizon is not a failure and should not zero out the future value.

**Behavior policy.** Actions during training are $\varepsilon$-greedy,

$$
a_t =
\begin{cases}
\text{uniform random}, & \text{with probability } \varepsilon_k \\
\arg\max_a Q(\phi(s_t), a), & \text{otherwise (ties broken at random),}
\end{cases}
\qquad
\varepsilon_k = \max(0.01,\ 0.999^{k})
$$

after $k$ completed episodes, so exploration decays from 1 to its floor over roughly 4600 episodes.

**Checkpoint selection.** Tabular Q-learning with a constant step size and aggregated states does not converge monotonically, so the training loop keeps the Q-table from the episode with the highest 100-episode moving-average return and saves that.

**Convergence.** Watkins' theorem guarantees $Q \to Q^*$ for a finite MDP when every state-action pair is visited infinitely often and step sizes satisfy the Robbins-Monro conditions. Neither holds exactly here: $\alpha$ is constant and $\phi$ makes the aggregated process only approximately Markov. In practice the learned table is a good approximation of $Q^*$ on the discretized problem, which is all inference needs.

**If this were a neural network.** The formulation above is the same one a Deep Q-Network uses; only the function class changes. A DQN replaces the table with a parametric $Q_w(s, a)$ that reads the raw continuous state and trains $w$ by gradient descent on the squared TD error over a replay buffer $\mathcal D$,

$$
\mathcal L(w) = \mathbb E_{(s, a, r, s') \sim \mathcal D}\Big[\big(r + \gamma \max_{a'} Q_{w^-}(s', a') - Q_w(s, a)\big)^2\Big],
$$

with a slowly updated copy $w^-$ of the weights as the bootstrap target. Nothing in this repository does that; it is mentioned only to place the tabular method.

### Inference

`--mode infer` loads the table and runs the greedy policy with $\varepsilon = 0$ and no updates. At each step it computes the bin index, reads two numbers and picks the larger:

$$
a_t = \pi(s_t) = \arg\max_{a \in \{0,1\}} Q\big(\phi(s_t), a\big).
$$

That is the entire computation, a constant-time lookup. The only randomness is the environment's start state (unless `--x0`/`--theta0` are given). Exact ties, which occur only in cells the table never visited, resolve to "push left" so that a frozen policy is reproducible.

### Why these ranges

The bounds appear in three places: the termination thresholds that define the task, the clipping ranges used by $\phi$, and the CLI validation for `--x0`, `--theta0` and `--theta-range`. They all trace back to the physics.

**Pole angle, ±12° (0.2095 rad).** This is the failure threshold from [Barto, Sutton and Anderson (1983)][barto1983] and is kept by Gymnasium. Physically it marks the region where the pole is still meaningfully "balanced":

- The upright pole is an unstable equilibrium. Within ±12°, $\sin\theta \approx \theta$ to better than 1%, so the dynamics are close to the linear inverted pendulum for which stabilizing control is well posed.
- Recoverability is a matter of torque budget. From the $\ddot\theta$ equation, gravity's angular acceleration at 12° is about 3.3 rad/s² while the cart's push can supply about 14 rad/s² in the opposite direction. The controller therefore has roughly a four-to-one margin at the edge of the band, which is why a policy trained on the full range recovers from 11° starts. Beyond the band the margin keeps shrinking, and past about 43° (where $\tan\theta = F/(m_c+m_p)g$) a single-force bang-bang controller cannot bring the pole back. The 12° threshold is a conservative task definition well inside the physical limit, not the limit itself.
- Angular velocity matters as much as angle. A pole at 11° already falling outward at several rad/s cannot be saved even though the angle is in range. That is why $\phi$ discretizes $\dot\theta$ with more bins (16) than $\theta$ (8), and why it clips $\dot\theta$ at ±3.5 rad/s (200°/s): at that rate the pole crosses the whole 24° band in six steps, and anything faster is effectively already lost.

**Cart position, ±2.4 m.** The cart runs on a finite 4.8 m track, again from the [1983 setup][barto1983]. Leaving the track is a failure. Without a position bound the agent could "balance" indefinitely by accelerating in one direction, so the bound is what makes this a balancing task rather than a chasing task. This solution's policy ignores $x$ and $\dot x$, so its only failures from valid starts are drifting off the track over a long episode. The 1983 and 1988 solutions include cart bins and do not have this failure mode.

**Cart velocity, ±3 m/s.** This appears only as the clipping range of $\phi$ (unused while $\dot x$ has a single bin) and is not a physical limit. The environment never caps $\dot x$. With a 10 N force on 1.1 kg total mass the cart accelerates at about 9.1 m/s², or 0.18 m/s per step, so reaching 3 m/s from rest takes 16 steps of pushing in one direction, by which point the cart has already travelled most of the track.

**Initial-state band, ±0.05.** Gymnasium's reset draws all four state variables from $[-0.05, 0.05]$ in SI units (meters, m/s, radians, rad/s), i.e. about ±2.9° of tilt. That is small enough that a trivial policy can balance for a while, which is why training on it alone produces an agent that cannot recover from an 8° start. The `--theta-range` default of 12 widens the angle draw to the whole recoverable band while leaving the velocity bands at Gymnasium's values. `--x0` and `--theta0` must be strictly inside the termination thresholds because a start exactly on or beyond them terminates before the agent acts.

## Run

```sh
python ../main.py --mode train --no-render                 # 1989_qlearning is the default --soln
python ../main.py --mode infer --theta0 -11
pytest ../tests -k 1989
```

Q-tables saved by the original single-file version of this project (before the solutions were split into directories) still load.

## Result

Seed 0, 5000 training episodes with full-range starts, frozen policy, 20 episodes per start angle:

| start angle | 0° | −8° | +8° | −11° | +11° |
|---|---|---|---|---|---|
| mean steps (max 500) | 492 | 500 | 500 | 495 | 487 |

Best 100-episode training average 479 at episode 4782. Tabular Q-learning is the slowest of the six to converge on this task, in part because it throws each transition away after a single update. The [1990 Dyna](../1990_dyna/README.md) solution addresses exactly that.

[barto1983]: https://github.com/david78k/pendulum/blob/master/c/anderson/Neuronlike%20Adaptive%20Elements%20That%20Can%20Solve%20Difficult%20Learning%20Control%20Problems%20Barto1983.pdf
