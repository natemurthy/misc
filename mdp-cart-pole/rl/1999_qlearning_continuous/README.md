# 1999: Q-learning in continuous state and action spaces (Gaskett, Wettergreen and Zelinsky)

**Lineage:** [1983 actor-critic](../1983_actor_critic/README.md) → [1986 backprop actor-critic](../1986_actor_critic_backprop/README.md) → [1988 TD(λ)](../1988_td/README.md) → [1989 Q-learning](../1989_qlearning/README.md) → [1990 Dyna](../1990_dyna/README.md) → [1992 REINFORCE](../1992_reinforce/README.md) → **1999** → [2011 NFQCA](../2011_nfqca/README.md) → [2013 DQN](../2013_dqn/README.md) → [2015 DDPG](../2015_ddpg/README.md) → [2015 TRPO](../2015_trpo/README.md) → [2017 PPO](../2017_ppo/README.md) → [2018 SAC](../2018_sac/README.md)

**Previous:** [1992, REINFORCE](../1992_reinforce/README.md)

**Next:** [2011, neural fitted Q iteration: batch regression instead of a moving target](../2011_nfqca/README.md). The continuous force this solution introduced is also the hand-off point to the optimal-control lineage in [`../../mpc/README.md`](../../mpc/README.md).

## References

- C. Gaskett, D. Wettergreen and A. Zelinsky, ["Q-Learning in Continuous State and Action Spaces"](https://users.cecs.anu.edu.au/~rsl/rsl_papers/99ai.kambara.pdf), *Proceedings of the 12th Australian Joint Conference on Artificial Intelligence* (AI'99), LNCS 1747, 1999. Written at the Australian National University's Robotic Systems Laboratory; the demonstration task is guiding a simulated submersible vehicle to a target position by firing its thrusters, the precursor to the group's *Kambara* underwater robot.
- L. C. Baird and A. H. Klopf, "Reinforcement Learning with High-Dimensional, Continuous Actions", Wright Laboratory technical report WL-TR-93-1147, 1993. Introduces wire fitting.
- L. C. Baird, "Advantage Updating", Wright Laboratory technical report WL-TR-93-1146, 1993; M. E. Harmon and L. C. Baird, "Multi-Player Residual Advantage Learning with General Function Approximation", Wright Laboratory technical report WL-TR-1065, 1996. Introduce advantage updating and its simpler successor, advantage learning.

A note on attribution. Advantage learning is Baird's idea, not this paper's. Gaskett and colleagues adopted it and showed experimentally that it made their continuous-action Q-learning faster and more reliable than the plain Q-learning target; that comparison, and the combination with wire fitting inside a single network, is the paper's contribution.

## What changed from everything before

Every earlier solution in this repository, and Q-learning as Watkins defined it, chooses among a finite set of actions by taking a maximum over them. The cart-pole has two: push left with 10 N or push right with 10 N. That is fine for a table, but real actuators are continuous, and discretizing a continuous action space finely enough to control well makes the maximum expensive and the table enormous.

This paper keeps Q-learning's core, learning $Q(s, a)$ from sampled transitions and acting greedily, and makes both the state and the action continuous with two ideas:

- **Wire fitting** gives a $Q(s, \cdot)$ over the whole continuous action range from a handful of points whose maximum is known by construction, so the greedy continuous action costs one forward pass.
- **Advantage learning** rescales the targets so that the differences between actions, which are what the policy depends on, are large enough to learn with a function approximator.

For this repository the concrete change is that the agent outputs a force $u \in [-1, 1]$, applied as $10u$ newtons. The environment runs in continuous mode (`CartPoleEnv(continuous=True)`); the plant, reward, termination thresholds and start distribution are identical to the other six solutions.

## What continuous state-action modelling buys, and what it costs

The reason to accept this difficulty is realism. A real motor or thruster produces a graded force, not two values. The bang-bang solutions balance the pole by chattering between full pushes, and their phase portraits show it: a limit cycle around the origin whose width is set by how finely the policy can see the state. A continuous policy can apply a small correction to a small error and settle toward the equilibrium rather than orbit it. That is gentler on the hardware, spends less energy, and makes the controller comparable in kind to the linear state-feedback and LQR controllers in `../../mpc`, which also emit a graded force.

The learned Q-function is also a smooth object over actions, so the agent can reason about how good a *nearly* optimal action is, which a table over two actions cannot. This is what lets the greedy action be read off in closed form without an action grid, and what would let the same method scale to several simultaneous actuators, as in the paper's underwater vehicle.

Two honest caveats. First, wire fitting is smooth in the action but the greedy policy is not: the chosen action is whichever wire has the highest value, so as the state moves the policy can jump from one wire to another. In practice the wires move together and the jumps are small, but the policy is piecewise rather than truly smooth. Second, smoothness in the model does not mean smoothness in training. Removing the finite maximum over actions removes the anchor that makes discrete Q-learning forgiving, and the optimization landscape is correspondingly harder, which is the whole of the section above.

## The method

### Wire-fitted neural network Q-learning

A single network maps the normalized state to $n$ *wires*, each an action and a value:

$$
\text{net}(s) = \big(u_1(s), \ldots, u_n(s);\ q_1(s), \ldots, q_n(s)\big), \qquad u_i \in [-1, 1].
$$

Wire fitting (Baird and Klopf) interpolates the wires into a value for any action $u$:

$$
d_i(u) = \lVert u - u_i \rVert^2 + c\,\big(q_{\max} - q_i\big) + \epsilon, \qquad
Q(s, u) = \frac{\sum_i q_i / d_i(u)}{\sum_i 1 / d_i(u)}.
$$

Two properties make this the right interpolator for Q-learning. First, $Q(s, u_i) = q_i$ at every wire, so the wires are points on the function. Second, the interpolation never overshoots, so $\max_u Q(s, u) = q_{\max}$ and the maximizing action is the wire with the largest value. The greedy policy is therefore

$$
\pi(s) = u_{\arg\max_i q_i(s)},
$$

with no search over actions. The smoothing term $c\,(q_{\max} - q_i)$ makes wires with low values influence a narrower region around themselves, and $\epsilon$ keeps the weights finite when $u$ coincides with a wire.

**Learning.** For a transition $(s, u, r, s')$ the target $y$ is computed as below and the error $y - Q(s, u)$ is backpropagated *through the interpolator* to every wire's action and value, then through the network. The interpolator's partial derivatives are written out by hand in `soln.py` (`_interpolate`) and checked against finite differences in the tests. Following common practice, $q_{\max}$ is treated as a constant in those derivatives.

### Advantage learning

With rewards of +1 per step and $\gamma = 0.99$, the value of a well-balanced state is near 100 while the difference between a good and a bad push from that state is a fraction of one. A function approximator fits the large common value easily and the small differences poorly. Baird's advantage learning changes the target so that those differences are scaled up by a factor $1/k$:

$$
y = A_{\max}(s) + \frac{r + \gamma\, A_{\max}(s') - A_{\max}(s)}{k}, \qquad 0 < k \le 1,
$$

where $A_{\max}(s) = \max_i q_i(s)$ and $A_{\max}(s') = 0$ on failure. With $k = 1$ this is exactly the Q-learning target; with $k < 1$ the learned function is an *advantage* function whose maximum over actions still equals the state value but whose gaps between actions are $1/k$ times larger. The greedy policy is unchanged. In this implementation, turning advantage learning off ($k = 1$) roughly halves what the agent achieves in the same number of episodes, which is the effect the paper reports.

### Exploration and experience reuse

Exploration is Gaussian noise added to the greedy action and clipped to $[-1, 1]$, with the standard deviation decayed each episode to a floor. Each real transition is stored in a ring buffer, and after every real step eight stored transitions are replayed through the same update ([Lin 1992](../1990_dyna/README.md#what-changed-from-1989)), which the paper also relies on. The eight are processed as one minibatch with summed gradients rather than one after another. On this tiny network that is about five times cheaper per transition, because the cost is Python and numpy call overhead rather than arithmetic, and to first order it moves the weights exactly as the sequential updates would (a test checks this). The whole agent step went from about 270 µs to about 115 µs.

## Implementation notes and deviations

- `soln.py` is pure numpy: a two-layer network with a tanh hidden layer, wire actions through tanh, wire values linear, and hand-written backpropagation.
- The wire actions are initialized spread across $[-1, 1]$ rather than all at zero, and the wire values are initialized at $r/(1-\gamma)$, the value of a state that never fails, for the same reason as the [1986 critic](../1986_actor_critic_backprop/README.md#implementation-notes-and-deviations): otherwise every early TD error is positive.
- Rewards are scaled by 0.01 inside the agent so values are order 1. Positive scaling does not change the optimal policy.
- The wire-fitting constants matter. With $\epsilon = 10^{-3}$ the interpolator's gradient with respect to a wire's action blows up whenever the taken action lands near that wire, and training diverged; $\epsilon = 0.3$ and $c = 1.0$ are used, chosen by a small sweep in which they were the only setting to reach the 500-step cap on both seeds tried. The gradient of each update is also clipped to unit norm as a safety net.
- The paper's task has a multi-dimensional action (thruster settings). Here the action is one-dimensional, so $\lVert u - u_i \rVert^2$ is a scalar square.



## Run

```sh
python ../main.py --mode train --soln 1999_qlearning_continuous --no-render
python ../main.py --mode infer --soln 1999_qlearning_continuous --theta0 -11
pytest ../tests -k 1999
```

The progress bar's diagnostics are the exploration noise `sigma` and the last TD error.

## Result

Seed `[0, 5000]` training episodes with full-range starts, frozen (noise-free) policy, 20 episodes per start angle:

| start angle | 0° | −8° | +8° | −11° | +11° |
|---|---|---|---|---|---|
| mean steps (max 500) | 500 | 500 | 500 | 500 | 500 |

The 100-episode average first reached 500 at episode 3753. Training took 148 s on one core: 1.16 M environment steps at about 7,829 steps/s, or 128 µs per step. Each step still performs nine network updates (one real transition plus eight replayed), but the eight replayed ones are a single minibatch; before that change the same run took 539 s at 280 µs per step and reached 500 at episode 1963, so batching trades some learning per episode for far more learning per second.

Default hyperparameters: 5 wires, 32 hidden units, step size 0.01, $\gamma = 0.99$, advantage $k = 0.5$, wire-fitting $c = 1.0$ and $\epsilon = 0.3$, exploration noise decaying from 0.5 to 0.05 by a factor 0.998 per episode, 8 replayed transitions per step from a buffer of 20 000 processed as one minibatch (`batched_replay=True`; set it to `False` for the original one-at-a-time updates), rewards scaled by 0.01, gradient norm clipped at 1 per sample.

## Limitations

- The slowest solution in the repository per step: every update does a forward pass for $s$, another for $s'$, the interpolator and its derivatives, and a backward pass, and the replay multiplies that by several. See the timing columns in the [top-level results table](../README.md#results).
- Sensitive to the wire-fitting constants and the step size, and to the seed, more so than any of the discrete methods. Advantage learning helps but does not remove the instability that Q-learning with a network and bootstrapped targets is known for; the fixes for that (target networks, larger replay, double Q) come in the following decade.
- Only the continuous-force ability is new. On a two-action problem the discrete methods are simpler and, here, more reliable. The reason to have this solution is what it enables next: a learned continuous controller that can be set beside a linear-quadratic regulator on the same plant.

## Wider angles

This solution reads the raw scaled state, so it accepts `--theta-limit` above 12° (see [Wider angles](../README.md#wider-angles)). With the 12° defaults it does not learn the 30° task: in every run tried it stayed at the random baseline. With a wider hidden layer, a stronger advantage factor, a smaller step size and a longer budget it does. The validated recipe, with the default batched replay, is

```sh
python ../main.py --mode train --soln 1999_qlearning_continuous --no-render --theta-limit 30 --episodes 8000 \
    --hparam hidden=64 --hparam advantage_k=0.3 --hparam lr=0.005

python ../main.py --mode infer --soln 1999_qlearning_continuous --theta-limit 30 --theta0 25
```

Frozen-policy results after 8000 training episodes on ±30° starts, six episodes per start angle, mean steps out of 500:

| seed | 12° | 20° | 25° | train time |
|---|---|---|---|---|
| 0 | 500 | 500 | 500 | 439 s |
| 1 | 500 | 500 | 500 | 356 s |
| 2 | 500 | 500 | 500 | 294 s |
| 3 | 414 | 367 | 284 | 409 s |

The smaller step size is what the batched replay needs: with eight summed gradients per replay step the default 0.01 is effectively too large, and the same recipe at 0.01 recovered from 25° on one seed in four even with the doubled budget. The one-at-a-time replay (`--hparam batched_replay=False`) reaches the same quality with `hidden=64`, `advantage_k=0.3` and the default step size in 4000 episodes, but each run takes about as long or longer, since it does five times the work per step. A wider 128-unit network with `advantage_k=0.3` and `lr=0.005` also worked in the sequential mode at about three times the compute.

None of this is made the default. On the standard 12° task the shipped defaults reach 500 on the seeds tried, and the two regimes want different settings, which is itself a point made in the section above. Recovery from 25° lands the cart near the end of the track, as the [physical envelope](../README.md#wider-angles) says it must; 30° starts are not recoverable on this track by any controller.

Tuning hyperparameters to find a solution the accepts a larger `—-theta-limit` and results are in the two sections below.

## Finding hyperparameters, and why it is hard here

Every solution in this repository needed some tuning, but this one needed the most, and the wide-angle task (`--theta-limit` above 12°) shows why. The causes are worth recording because they are properties of the method, not accidents of the code.

**A hand-rolled network has none of the modern stabilizers.** The two-layer numpy network is trained by plain stochastic gradient descent on bootstrapped targets from the same network. There is no adaptive optimizer, no target network, no normalization layer, and only a small replay buffer. Every knob therefore interacts with every other: the step size that is stable for 32 hidden units diverges for 64; the smoothing constants of the interpolator change the gradient scale by orders of magnitude; the advantage factor $k$ rescales the targets and so effectively rescales the step size again. A change to one hyperparameter usually forces a re-sweep of two others.

**The interpolator's gradients are sharp.** Wire fitting's weights are $1/d_i$, so its derivative with respect to a wire's action carries a factor $1/d_i^2$. With a small $\epsilon$ that factor explodes whenever the taken action lands near a wire, which is exactly where a good policy spends its time. The first version of this agent diverged for that reason. The fix, a larger $\epsilon$ and gradient clipping, trades away some of the sharpness that makes the interpolant exact at the wires.

**The learning signal is weakest where it is needed most.** With +1 per step the only informative events are failures. On the 12° task a random policy fails in about 20 steps, so the early transitions are rich in failure signal. On the 30° task starts are spread over a much larger region and early episodes are shorter still, so the network must generalize from few failures across a state space several times larger, with inputs that push the tanh units toward saturation. Recovery from a wide angle also fails mostly by running out of track, which assigns blame to the cart variables the network is only starting to use.

**The exploratory policy and the greedy policy disagree.** Training acts with Gaussian noise on the greedy action. Early on that noise does much of the balancing, so a snapshot that scores well under noise can fail when frozen. Until the noise has decayed, the frozen score is not monotone in the training budget, and the best-checkpoint logic can pick a snapshot that only works with the dither.

**Runs are slow, so sweeps are coarse.** A successful configuration plays 500-step episodes for most of training, at nine network updates per step; before the replay was batched one 4000-episode run took five to fifteen minutes, and it still takes several. The sweeps that found the settings below were eight configurations at two seeds each, run as parallel processes (now packaged as [`hparam_sweep.py`](../README.md#hyperparameter-sweeps)), which is enough to find a setting that works and nowhere near enough to characterize it. Seed sensitivity was visible throughout: several settings reached 500 on one seed and stayed at the random baseline on the other. A GPU would not help: the network has 490 parameters and updates one sample at a time, so kernel-launch latency dominates; measured on this machine, PyTorch on the GPU was fifty times slower per update than numpy, and PyTorch on the CPU six times slower. Batching the replay was the change that paid.

**What the sweeps found for wider angles.** At `--theta-limit 30`, training on starts anywhere in ±30°, the 12° defaults did not learn on either seed. Reducing the step size, widening the hidden layer or lowering the advantage factor each produced one seed that recovered from 25°. Combining a wider hidden layer with a lower advantage factor produced recovery from 20° on both seeds and from 25° on most. With the replay then batched, the same combination needed a halved step size and a doubled budget to reach the same quality. The recipe under [Wider angles](#wider-angles) records the validated setting. Use `--hparam KEY=VALUE` to apply it; the values are saved with the model.

**Batched versus one-at-a-time replay is itself a hyperparameter.** Replaying the eight stored transitions as one minibatch (`batched_replay=True`, the default) cuts the wall-clock cost of a step by about 2.4 times and moves the weights identically to first order. It is not identical in effect. The sequential version recomputes each replayed sample's target with the network as updated by the previous sample, and at this step size that second-order difference shows: in an A/B on four seeds, the sequential version reached the 500-step cap on the 12° task in fewer episodes (2223 versus 3753 on seed 0) and recovered from 25° on three of four seeds with the wide-angle recipe, where the batched version did so on one. Per second of compute the batched version still wins on the 12° task, because it runs three to five times more episodes in the same time; on the wide-angle task it needs a longer budget or the sequential mode to match. It is also more seed-dependent on the 12° task: in a four-seed sweep at 2500 episodes the batched default reached the 500-step cap on two seeds and stalled below 250 on the other two, and smaller step sizes (0.005, 0.0025) did not fix that. The learning test in `tests/test_learning.py` therefore runs this solution in sequential mode with a 300-episode budget. The results tables below say which mode produced them.

### Tuning with `hparam_sweep.py`

Everything in this section was found with [`../hparam_sweep.py`](../README.md#hyperparameter-sweeps), which trains every (configuration, seed) pair in its own process and scores the frozen policy from chosen start angles. The pattern that worked, and that is worth repeating for any new regime of this agent:

1. **Start from the defaults and change one thing at a time**, two seeds each, with `--early-stop 1000:30` so settings that never leave the random baseline cost seconds rather than minutes. Step size, hidden width, the advantage factor $k$, the wire-fitting constants and the exploration schedule are the knobs that have mattered.
2. **Combine the factors that helped on at least one seed** and run them again on the same seeds. Single-factor wins on one seed are common and mean little here.
3. **Validate the finalists on fresh seeds and on the standard 12° task**, so that a setting tuned for one regime is not silently adopted for another.
4. **Record the mode and budget with the numbers.** Because the batched and sequential replay differ, and because the frozen score is not monotone in the training budget, a result is only reproducible together with `batched_replay`, the episode count and the seeds.

For example, the wide-angle recipe below came from:

```sh
python ../hparam_sweep.py --soln 1999_qlearning_continuous --theta-limit 30 --episodes 4000 --seeds 0 1 \
    --eval-angles 12 20 25 --early-stop 1000:30 \
    --config "" --config "lr=0.005" --config "advantage_k=0.3" --config "hidden=64" --config "replay=16"

python ../hparam_sweep.py --soln 1999_qlearning_continuous --theta-limit 30 --episodes 4000 --seeds 0 1 2 3 \
    --eval-angles 12 20 25 --config "hidden=64,advantage_k=0.3" --config "hidden=128,advantage_k=0.3,lr=0.005"

python ../hparam_sweep.py --soln 1999_qlearning_continuous --theta-limit 30 --episodes 8000 --seeds 0 1 2 3 \
    --eval-angles 12 20 25 --config "hidden=64,advantage_k=0.3" --config "hidden=64,advantage_k=0.3,lr=0.005"
```