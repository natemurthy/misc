# 2007: Continuous Actor Critic Learning Automaton (Van Hasselt and Wiering)

**Lineage:** [1983 actor-critic](../1983_actor_critic/README.md) → [1986 backprop actor-critic](../1986_actor_critic_backprop/README.md) → [1988 TD(λ)](../1988_td/README.md) → [1989 Q-learning](../1989_qlearning/README.md) → [1990 Dyna](../1990_dyna/README.md) → [1992 REINFORCE](../1992_reinforce/README.md) → [1999 continuous Q-learning](../1999_qlearning_continuous/README.md) → [2005 NAC](../2005_nac/README.md) → **2007 CACLA** → [2011 NFQCA](../2011_nfqca/README.md) → [2011 PILCO](../2011_pilco/README.md) → [2013 DQN](../2013_dqn/README.md) → [2015 DDPG](../2015_ddpg/README.md) → [2015 TRPO](../2015_trpo/README.md) → [2017 PPO](../2017_ppo/README.md) → [2018 SAC](../2018_sac/README.md)

**Previous:** [2005, natural actor-critic](../2005_nac/README.md)

**Next:** [2011, NFQCA: fitted Q iteration with a learned continuous actor](../2011_nfqca/README.md)

## References

- H. van Hasselt and M. A. Wiering, ["Reinforcement Learning in Continuous Action Spaces"](https://hadovanhasselt.com/wp-content/uploads/2015/12/reinforcement_learning_in_continuous_action_spaces.pdf), *Proc. IEEE Symposium on Approximate Dynamic Programming and Reinforcement Learning (ADPRL)*, pp. 272-279, 2007 ([IEEE](https://ieeexplore.ieee.org/document/4220844)). Introduces CACLA and CACLA+Var and compares them with wire fitting and gradient ascent on the value on a tracking task and a cart pole.
- H. van Hasselt, "Reinforcement Learning in Continuous State and Action Spaces", in M. Wiering and M. van Otterlo (eds.), *Reinforcement Learning: State of the Art*, Springer, 2012. The fuller treatment of CACLA, with its relation to policy-gradient and value-based methods spelled out.
- C. Gaskett, D. Wettergreen and A. Zelinsky, "Q-Learning in Continuous State and Action Spaces", AI'99, 1999. Wire fitting, the continuous-Q alternative CACLA was measured against; this repository's [1999 solution](../1999_qlearning_continuous/README.md).

## What changed

**From the 1986 backprop actor-critic.** Anderson's actor is a probability of pushing right, moved along $\delta\,\nabla \log\pi(a\mid s)$: the TD error's sign *and* size scale every step, and the action is one of two pushes. CACLA keeps the two-network structure and replaces the stochastic actor with a deterministic continuous action $\mathrm{Ac}(s) \in [-1, 1]$, explored by adding Gaussian noise. The actor update is not a policy gradient at all: it is a supervised regression of $\mathrm{Ac}(s)$ toward the action that was actually taken, performed only when the TD error is positive. The size of $\delta$ never enters the actor, so the actor's step size is invariant to the scale of the reward, and a bad action leaves the actor untouched rather than pushing it toward some unknown other action.

**From the 1999 continuous Q-learning.** Wire fitting learns $Q(s, u)$ over the whole action continuum and reads the greedy action off an interpolator whose maximum is at the best wire. CACLA learns no action values: the critic is a plain state-value function $V(s)$, cheaper and easier to fit, and the policy lives entirely in the actor. Acting is one forward pass with no maximization, closed-form or otherwise. In the paper's own comparison wire fitting never balanced their cart pole for 100 s under Gaussian exploration; CACLA did in every run.

**From the 2005 natural actor-critic.** NAC still follows a gradient of the policy's log-likelihood, corrected by the Fisher metric and estimated from a batch by least squares. CACLA has no likelihood to differentiate (the actor is a point, not a distribution), no Fisher matrix and no batch: every step either regresses the actor toward $a_t$ or does nothing. It is the simplest possible continuous actor-critic, and its cost per step is two forward passes and at most two backward ones.

**Forward.** DDPG (2015) also keeps a deterministic actor with Gaussian exploration, but moves it by differentiating a learned critic $Q(s, a)$ with respect to the action. CACLA gets a direction without ever differentiating the critic, from the sign of a one-step comparison.

## The method

Two networks on the normalized state $x = s / \text{scale}$: a critic $V_\theta(x)$, 4 → 64 tanh → 1, and an actor $\mathrm{Ac}_\phi(x) = \tanh(\cdot)$, 4 → 64 tanh → 1, so the force fraction lies in $[-1, 1]$. The action taken while learning is

$$
a_t = \operatorname{clip}\big(\mathrm{Ac}_\phi(x_t) + \epsilon_t,\ -1,\ 1\big), \qquad \epsilon_t \sim \mathcal N(0, \sigma^2),
$$

with $\sigma = 0.3$ held constant; the frozen policy is $\mathrm{Ac}_\phi(x)$ itself. The critic is a TD(λ) state-value learner with accumulating traces on the network parameters,

$$
\delta_t = r_t + \gamma\, V_\theta(x_{t+1}) - V_\theta(x_t), \qquad
e_t = \gamma\lambda\, e_{t-1} + \nabla_\theta V_\theta(x_t), \qquad
\theta \leftarrow \theta + \alpha_c\, \delta_t\, e_t,
$$

with $V_\theta(x_{t+1}) = 0$ on failure; $\lambda = 0$ recovers the paper's TD(0). The actor update is the paper's equation for the continuous case:

$$
\text{if } \delta_t > 0:\qquad \phi \leftarrow \phi + \alpha_a\, \big(a_t - \mathrm{Ac}_\phi(x_t)\big)\, \nabla_\phi \mathrm{Ac}_\phi(x_t),
$$

and nothing otherwise. The paper's argument for the one-sided rule: a positive $\delta$ says $a_t$ was better than the current actor output, so move toward it; a negative $\delta$ says it was worse, but "updating away from the last action" is "equivalent to updating towards some unknown action, which is not necessarily better than our present approximation". On their cart pole, allowing the negative updates made CACLA fail to balance for 100 s in every run and sometimes diverge to a policy that toppled the pole with every action.

**CACLA+Var.** To let unusually good outcomes count for more without reintroducing the magnitude of $\delta$, the paper keeps a running variance of the TD error,

$$
\mathrm{var}_{t+1} = (1 - \beta)\,\mathrm{var}_t + \beta\,\delta_t^2, \qquad \beta = 0.001,\ \mathrm{var}_0 = 1,
$$

and repeats the actor update $\lceil \delta_t / \sqrt{\mathrm{var}_t}\,\rceil$ times when $\delta_t > 0$, i.e. once per standard deviation the target lies above the old value. In the paper's experiments this variant learned the cart pole fastest. It is the `var=True` constructor flag here (`--hparam var=True`), with the repeats capped at `max_updates` (10) and the actor's output recomputed before each repeat.

The paper's experiments: feedforward networks with 12 hidden units (sigmoid onto $[-1, 1]$, linear output), learning rate 0.01 for every network, inputs and rewards linearly scaled to $[-1, 1]$, Gaussian exploration with $\sigma = 0.1$ and no decay (ε-greedy, decayed from 1 to 0.01, was the alternative and did worse), $\gamma \in \{0, 0.8, 0.9, 0.95, 0.99\}$ with the best reported, 102 400 learning steps, 20 runs, and Gaussian noise of standard deviation 0.3 added to both actions and rewards. Their cart pole: 1 kg cart, 0.1 kg pole, 1 m pole, 0.1 s steps, reward $+1$ while $|\phi| < 12°$ and $|x| < 1$ m and $-1$ otherwise, reset on failure, success meaning a policy that balances for 100 s. Under Gaussian exploration CACLA ($\gamma = 0.8$) and CACLA+Var ($\gamma = 0.95$) succeeded in 100% of runs, gradient ascent on the value in 20%, wire fitting in 0%; under ε-greedy the figures were 40%, 80%, 15% and 10%.

## Implementation notes and deviations

- Pure numpy with hand-written backpropagation for both two-layer networks, in the style of the [1986 solution](../1986_actor_critic_backprop/README.md); the actor and critic have separate parameters and the critic is never differentiated with respect to the action.
- **What the +1-per-step reward required.** The paper's reward is $-1$ at failure and $+1$ otherwise, so a failing action produces a large negative $\delta$ on its own. Here every step pays $+1$ and failure only ends the episode. Rewards are scaled by `reward_scale = 0.01` so the critic's targets are $O(1)$ (the optimal policy is invariant to positive scaling), and the critic's output bias starts at $r/(1-\gamma) = 1$, the value of a state that never fails, as the 1986 and 1999 agents do. This matters more for CACLA than for either of them: with an all-zero critic every early $\delta$ is positive, and a positive $\delta$ is exactly what fires an actor update, so the actor would spend the first hundreds of episodes regressing toward its own exploration noise. Since only the critic sees the reward, the actor's step size is unaffected by the scaling, as the paper says it should be.
- **A discriminative critic is not optional.** The actor learns from the sign of $\delta$ alone. If the critic is flat over the states visited, $\delta = r - (1-\gamma) V$ is positive on every non-failure step regardless of the action, the sign carries no information about $a_t$, and the actor drifts. That was the failure mode of the paper's settings on this task: a 12-unit critic with weights of scale 0.1 and TD(0) at rate 0.01 could not tell states 8° apart after a thousand episodes, and roughly 95% of steps had $\delta > 0$. Three changes fix it. The critic has 64 hidden units; the input weights of both networks start at unit scale (the output weights at 0.1), so the tanh units already span the normalized state and the critic can separate states from the first episode; and the critic uses TD(λ) with $\lambda = 0.7$, which propagates the failure signal back along the episode instead of one state per visit. The critic's learning rate stays at the paper's 0.01: with 64 unit-scale features and traces, 0.1 diverged within 200 episodes.
- **Exploration** is Gaussian with $\sigma = 0.3$ rather than 0.1, and is not decayed, as in the paper. The one-step effect of a 0.1 perturbation (1 N for 20 ms) on $V(s')$ is below the critic's resolution here; the paper's cart pole stepped at 0.1 s. Decaying $\sigma$ hurt in every schedule tried, because learning stops when the noise does and the schedule cannot know when the actor is good enough. The actor's step size stays at the paper's 0.01: the actor follows noise at rate $\alpha_a \sigma$ per positive-$\delta$ step, and at 0.05 that random walk saturated the tanh output before the critic could steer it.
- **CACLA+Var is off by default.** On seed 0 the plain and +Var versions reached the 500-step cap at the same episode with these settings; on seeds 1 and 2 the plain version's frozen policy was as good or better (498/500 versus 120/500 steps from upright), and its behavior is the one the README above describes. The paper's speed advantage for +Var came with $\mathrm{var}_0 = 1$ on rewards in $[-1, 1]$; with rewards scaled to 0.01 the running variance takes thousands of steps to fall to the scale of the actual TD errors, so the multiple updates arrive late. Both are one flag apart.
- $\gamma = 0.99$ matches the rest of the repository. The paper's best cart-pole results used 0.8 and 0.95 but it also reports that CACLA's performance "barely decreases" at 0.99, unlike the value-based methods, which is what happened here.
- The agent reads the raw scaled state, so it accepts `--theta-limit` above 12° (see [Wider angles](../README.md#wider-angles)).

### Tuning with `hparam_sweep.py`

The paper's own settings did not learn here, so CACLA's defaults were arrived at by comparison rather than transcription, and the comparisons were run with [`../hparam_sweep.py`](../README.md#hyperparameter-sweeps): every (configuration, seed) pair trains in its own process with the same loop and best-checkpoint rule as `main.py`, then the frozen policy is scored from 0° and 11°. Three seeds and the full 5,000 episodes each, because CACLA's learning starts late (episode 450 on seed 0, later on others) and its outcome varies more across seeds than across most of its settings, so a two-seed sweep at a short budget would have been misleading in both directions. Fifteen 5,000-episode jobs finish in under a minute in numpy. The questions asked were the ones the implementation notes above answer: does the paper's configuration (12 hidden units, TD(0), $\sigma = 0.1$) work with the +1-per-step reward; which of the three departures from it (wider critic, traces, more exploration) actually matters; and whether CACLA+Var, the paper's faster variant, should be the default.

```sh
python ../hparam_sweep.py --soln 2007_cacla --episodes 5000 --seeds 0 1 2 --eval-angles 0 11 \
    --config "" --config "var=True" --config "hidden=12,lam=0.0,sigma=0.1,sigma_min=0.1" \
    --config "sigma=0.1,sigma_min=0.1" --config "lam=0.0"
```

Frozen policy, mean steps from 0° / 11°, seeds 0, 1, 2:

| setting | seed 0 | seed 1 | seed 2 |
|---|---|---|---|
| defaults (64 hidden, $\lambda = 0.7$, $\sigma = 0.3$) | 500 / 500 | 498 / 406 | 500 / 500 |
| `var=True` (CACLA+Var) | 500 / 302 | 120 / 128 | 500 / 434 |
| the paper's settings: 12 hidden, TD(0), $\sigma = 0.1$ | 500 / 446 | 28 / 8 | 24 / 7 |
| $\sigma = 0.1$ alone | 491 / 315 | 36 / 21 | 157 / 161 |
| TD(0) alone ($\lambda = 0$) | 258 / 259 | 41 / 51 | 500 / 259 |

The paper's configuration works on one seed in three and stays at the random baseline on the other two; each of the three departures is load-bearing, since removing exploration noise or traces alone loses two seeds. CACLA+Var is worse than plain CACLA on every seed here, for the reason given above (its running variance starts far above the scale of the 0.01-scaled TD errors), so it stays a flag. Note also that only seed 0 reached a 100-episode training average of 500, at episode 3642; seeds 1 and 2 peaked at 290 and 334 while their frozen policies balance, because the training policy carries constant $\sigma = 0.3$ noise. The training average understates CACLA, which is why the sweep scores frozen policies.

## Run

```sh
python ../main.py --mode train --soln 2007_cacla --no-render
python ../main.py --mode train --soln 2007_cacla --no-render --hparam var=True   # CACLA+Var
python ../main.py --mode infer --soln 2007_cacla --theta0 -11
pytest ../tests -k "2007 or cacla"
```

`../tests/test_2007_cacla.py` runs the shared interface checks and tests the update rule directly: a negative TD error leaves the actor unchanged while a positive one moves it toward the taken action, the hand-written network gradients match finite differences, and CACLA+Var performs more updates for a large error.

## Result

Seed 0, 5000 training episodes with full-range starts, frozen policy, 20 episodes per start angle:

| start angle | 0° | −8° | +8° | −11° | +11° |
|---|---|---|---|---|---|
| mean steps (max 500) | 500 | 500 | 500 | 500 | 500 |

The 100-episode average first reached 500 at episode 3642 and stayed there to the end, even though the training policy carries constant exploration noise of $\sigma = 0.3$. Training took 43.2 s on one CPU core in numpy: 1.48 M environment steps at about 34,200 steps/s, or 29 µs per step, 116 episodes/s. Per step that is close to the 1986 networks (two forward passes, a critic backward pass and, on positive-$\delta$ steps, an actor backward pass), even with 64-unit layers, because no action maximization is ever performed. On seeds 1 and 2 the frozen policy reached 498 and 500 steps from upright but the noisy training average did not reach the cap within 5000 episodes (best 290 and 334).

## Limitations

- The actor learns only from the sign of a one-step comparison, so it learns nothing at all until the critic is accurate to within one action's effect on $V$, and nothing from failures directly: a bad action is simply not reinforced. On this task that made the method very sensitive to the critic's capacity, initialization and step size, more so than any earlier solution.
- With no negative updates, a positive $\delta$ produced by critic error is indistinguishable from a genuinely good action, and the actor regresses toward noise at rate $\alpha_a \sigma$ on every such step. The step size and the exploration noise cannot be tuned independently.
- The paper notes that the tabular version can converge to sub-optimal policies under stochastic transitions, since it optimizes the *probability* of a positive $\delta$ rather than its expected value; CartPole's dynamics are deterministic, so this does not bite here.
- Constant exploration means the training returns never show the policy's true quality; the frozen policy is far better than the 100-episode average during most of the run, and best-checkpoint selection on noisy returns is what picks the saved policy.
