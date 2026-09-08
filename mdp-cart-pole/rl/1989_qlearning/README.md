# 1989: Q-learning (Watkins)

**Lineage:** [1983 actor-critic](../1983_actor_critic/README.md) → [1986 backprop actor-critic](../1986_actor_critic_backprop/README.md) → [1988 TD(λ)](../1988_td/README.md) → **1989** → [1990 Dyna](../1990_dyna/README.md) → [1992 REINFORCE](../1992_reinforce/README.md) → [1999 continuous Q-learning](../1999_qlearning_continuous/README.md) → [2005 NAC](../2005_nac/README.md) → [2007 CACLA](../2007_cacla/README.md) → [2011 NFQCA](../2011_nfqca/README.md) → [2011 PILCO](../2011_pilco/README.md) → [2013 DQN](../2013_dqn/README.md) → [2015 DDPG](../2015_ddpg/README.md) → [2015 TRPO](../2015_trpo/README.md) → [2017 PPO](../2017_ppo/README.md) → [2018 SAC](../2018_sac/README.md)

**Previous:** [1988, TD(λ) with model-based lookahead](../1988_td/README.md)

**Next:** [1990, adding a learned model and planning](../1990_dyna/README.md)

This directory holds the default solution used by `main.py`, and this README also carries the full formulation of the shared MDP that every other solution links to.

## References

- C. J. C. H. Watkins, [*Learning from Delayed Rewards*](https://www.cs.rhul.ac.uk/~chrisw/new_thesis.pdf), PhD thesis, University of Cambridge, 1989. Introduces Q-learning.
- C. J. C. H. Watkins and P. Dayan, ["Q-learning"](https://doi.org/10.1007/BF00992698), *Machine Learning* 8:279-292, 1992. The convergence proof.

## What changed from 1988

TD(λ) learns the value of *states*, $V(s)$, and needs a model $f(s, a)$ to compare the actions available from a state. Watkins' idea was to learn the value of *state-action pairs* instead:

$$
Q^{\ast}(s, a) = \text{expected return from taking } a \text{ in } s \text{ and acting optimally afterwards.}
$$

With $Q$ in hand the greedy action is $\arg\max_a Q(s, a)$, a table lookup. No model, no lookahead. Two further properties fall out of the same change:

- **Off-policy.** The update target uses $\max_{a'} Q(s', a')$, the value of the best next action, regardless of which action the exploring agent actually takes next. So Q-learning estimates the *optimal* value function while behaving ε-greedily. TD(λ) and the actor-critics estimate the value of the policy being followed.
- **A theory.** Watkins showed Q-learning is a sample-based, asynchronous form of value iteration from dynamic programming, and Watkins and Dayan proved it converges to $Q^{\ast}$ on a finite MDP if every pair is visited infinitely often and the step sizes decay appropriately. This is the point where reinforcement learning and dynamic programming become one subject.

The rest of this file gives the MDP, the Bellman equation Q-learning solves, the concrete algorithm, and the physical reasons behind the problem's bounds.


## Tabular Q-learning

This is a **model-free** method. Although $f(s, a)$ is written above, the agent never evaluates it, never learns an approximation of it, and never plans by rolling it forward. It only observes sampled transitions $(s_t, a_t, r_{t+1}, s_{t+1})$ and updates value estimates from them. The [1988](../1988_td/README.md) solution uses $f$ to act, and the [1990](../1990_dyna/README.md) solution learns an approximation of it to plan; neither is needed here.

**State aggregation.** $\mathcal S$ is continuous, so the agent works with a discretized state $\phi(s)$ (`common.features.GridDiscretizer`). Cart position and velocity are collapsed into a single bin each; the pole angle and angular velocity are clipped and mapped onto uniform grids:

$$
\phi(s) = \left(
\mathrm{round}\!\Big(7 \cdot \tfrac{\mathrm{clip}(\theta, -0.21, 0.21) + 0.21}{0.42}\Big),\;
\mathrm{round}\!\Big(15 \cdot \tfrac{\mathrm{clip}(\dot\theta, -3.5, 3.5) + 3.5}{7}\Big)
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

**Convergence.** Watkins' theorem guarantees $Q \to Q^{\ast}$ for a finite MDP when every state-action pair is visited infinitely often and step sizes satisfy the Robbins-Monro conditions. Neither holds exactly here: $\alpha$ is constant and $\phi$ makes the aggregated process only approximately Markov. In practice the learned table is a good approximation of $Q^{\ast}$ on the discretized problem, which is all inference needs.

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

## Run

```sh
python ../main.py --mode train --no-render                 # 1989_qlearning is the default --soln
python ../main.py --mode infer --theta0 -11
pytest ../tests -k 1989
```

Q-tables saved by the original single-file version of this project (before the solutions were split into directories) still load.

## Result

Seed `[0, 5000]` training episodes with full-range starts, frozen policy, 20 episodes per start angle:

| start angle | 0° | −8° | +8° | −11° | +11° |
|---|---|---|---|---|---|
| mean steps (max 500) | 492 | 500 | 500 | 495 | 487 |

Best 100-episode training average 479 at episode 4782. Tabular Q-learning is the slowest of the six to converge on this task, in part because it throws each transition away after a single update. The [1990 Dyna](../1990_dyna/README.md) solution addresses exactly that.

[barto1983]: https://github.com/david78k/pendulum/blob/master/c/anderson/Neuronlike%20Adaptive%20Elements%20That%20Can%20Solve%20Difficult%20Learning%20Control%20Problems%20Barto1983.pdf
