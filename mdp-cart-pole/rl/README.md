# mdp-cart-pole (RL)

Study of the "Cart Pole" problem within the reinforcement learning (RL) school of thought.

Each annually prefixed directory implements a notable reinforcement learning method dating back to techniques from the decade in which the field took shape, in the order the ideas appeared in the academic literary history. The base `main.py` trains or runs inference across each of the methods with a live matplotlib view of the cart, the pole and the learning curve. The training runs can be executed in headlines mode without the visualization (which is faster if it is desirable to go straight to the learned model policy. Each of the techniques in this subfolder are "model-free" RL methods.

Each methods implements the environment interface provided by Gymnasium's [CartPole-v1](https://gymnasium.farama.org/environments/classic_control/cart_pole/) that follows the Gymnasium `Env` API without requiring the library.

The cart-pole benchmark framed as an RL problem first appeared [Burto, Sutton, and Anderson (1983)][barto1983]; the [1983_actor_critic/](1983_actor_critic/README.md) subdir re-implements its learning method.The shared environment departs from the paper in two ways inherited from Gymnasium: the friction terms are dropped (their effect is negligible, a 0.0005 N cart friction against a 10 N push), and the reward is +1 per step rather than −1 at failure. Each solution's README notes what that reward change required.

[barto1983]: https://github.com/david78k/pendulum/blob/master/c/anderson/Neuronlike%20Adaptive%20Elements%20That%20Can%20Solve%20Difficult%20Learning%20Control%20Problems%20Barto1983.pdf

There is no deep learning here in the modern sense: no framework, no GPU, and only a shallow neural network (the 1986 solution trains a small network with a single hidden layer of 16 units and are written by hand in numpy). The other solutions are linear units over fixed features (1983, 1992) or plain tables (1988, 1989, 1990). The largest learned object in the repository is a 4608-entry table.

## Gymnasium API

The environment class here follows Gymnasium's `Env` API: `reset(seed=, options=)` returns `(obs, info)` and `step(action)` returns `(obs, reward, terminated, truncated, info)` with `float32` observations. The [`gym/`](gym/README.md) directory runs the same problem and the same Q-learning agent on the real library, with notes on what Gymnasium adds and when to prefer it.

## Layout

```bash
main.py                     CLI driver: --soln picks a solution, one train/infer loop for all
common/
  env.py                    the CartPole MDP (Gymnasium API, no Gymnasium dependency)
  features.py               state representations: grid discretizer, BOXES decoder, normalizer
  agent.py                  BaseAgent interface + RandomAgent; save/load/freeze/snapshot
  render.py                 matplotlib visualization
<year>_<method>/soln.py     one solution each; exposes `Agent`
<year>_<method>/README.md   the paper, the method, what it improved, results
tests/                      pytest suite (see below)
gym/                        the same problem on the real Gymnasium library (see gym/README.md)
```

Every solution's agent implements the same interface, so `main.py` treats them identically:

```python
agent = Agent(seed=0)
a = agent.act(obs)                                    # 0 = left, 1 = right
agent.learn(obs, a, reward, next_obs, terminated)     # per step
agent.end_episode()                                   # per episode
agent.save(path); Agent.load(path); agent.freeze()    # persistence and inference
```

## Tests

```sh
pytest                    # everything, about 15 s
pytest -m fast            # unit and CLI tests only (majority of the cases) a few seconds
pytest -m slow            # only the learning tests which are annoted with @pytest.mark.slow
pytest -k 1983            # one solution
```

- `test_env.py` checks the MDP: reset options, the five-tuple step API, one Euler step against a hand computation, termination and truncation, the ~22-step random baseline, and, if `gymnasium` is installed, a trajectory match against the reference `CartPole-v1`.
- `test_features.py` checks the discretizers, including that the BOXES decoder produces all 162 regions with the paper's boundaries.
- `test_agents.py` runs every solution through the shared interface: valid actions, save/load round trip, frozen policies are deterministic and stop learning, snapshots restore, and identical seeds give identical training.
- `test_learning.py` (marked `slow`) trains every solution from scratch with a small per-method episode budget and requires the frozen policy to survive at least 100 steps from the default start, about five times the random baseline. It also checks that Dyna with zero planning steps reproduces Q-learning exactly and that the 1988 agent never touches the model while learning.
- `test_cli.py` exercises `main.py` as a subprocess: train-then-infer for every solution, argument validation, the legacy Q-table format, and that the untouched `gym/main.py` still imports this module's agents.


## Literary history

Read the READMEs in order; each explains what it improves on the one before.

| Directory | Year | Method | Learns | Uses a model? |
|---|---|---|---|---|
| [`1983_actor_critic/`](1983_actor_critic/README.md) | 1983 | Barto, Sutton, Anderson: ASE/ACE actor-critic on the BOXES decoder | actor weights + critic values, 162 boxes each | no |
| [`1986_actor_critic_backprop/`](1986_actor_critic_backprop/README.md) | 1986-89 | Anderson: the same actor-critic with two-layer backprop networks | two small neural nets | no |
| [`1988_td/`](1988_td/README.md) | 1988 | Sutton: TD(λ) value prediction, controlled by one-step lookahead | state-value table $V$ | yes, the true dynamics, to act |
| [`1989_qlearning/`](1989_qlearning/README.md) | 1989 | Watkins: tabular Q-learning **(default)** | action-value table $Q$ | no |
| [`1990_dyna/`](1990_dyna/README.md) | 1990 | Sutton: Dyna-Q, Q-learning plus planning on a learned model | $Q$ and a sample model | yes, learned, to plan |
| [`1992_reinforce/`](1992_reinforce/README.md) | 1992 | Williams: REINFORCE policy gradient with a baseline | 5 policy parameters | no |

The full definition of the shared MDP, the Bellman equation all six are solving, and the physical reasons behind the ±12° and ±2.4 m bounds live in [`1989_qlearning/README.md`](1989_qlearning/README.md#rl-formulation).

# Results

Seed `[0, 5000]` training episodes with the pole started anywhere in ±12°, then the frozen policy run 20 times from each of five start angles. Mean steps survived, out of a possible 500:

| Solution | 0° | −8° | +8° | −11° | +11° | first episode at avg 500 | 5000-episode train time | episodes/s | steps/s | µs per step |
|---|---|---|---|---|---|---|---|---|---|---|
| 1983 actor-critic | 500 | 500 | 500 | 500 | 492 | 1602 | 17.6 s | 294 | 123 k | 8.1 |
| 1986 backprop actor-critic | 500 | 500 | 500 | 500 | 500 | 1242 | 57.4 s | 88 | 37 k | 26.9 |
| 1988 TD(λ) + lookahead | 486 | 457 | 467 | 479 | 447 | never (best 474) | 46.6 s | 108 | 33 k | 30.4 |
| 1989 Q-learning | 492 | 500 | 500 | 495 | 487 | never (best 479) | 14.9 s | 346 | 54 k | 18.5 |
| 1990 Dyna-Q | 495 | 488 | 307 | 425 | 257 | never (best 247) | 30.0 s | 170 | 25 k | 40.6 |
| 1992 REINFORCE | 500 | 500 | 500 | 500 | 500 | 1582 | 19.5 s | 262 | 109 k | 9.2 |
| random baseline | ~22 | | | | | | | | | |

Train times are wall-clock for `python main.py --mode train --soln <name> --no-render` on one CPU core at 98-99% utilization, so they are also CPU time. Episodes per second is tqdm's overall rate for the same run. Both depend on how long episodes last as well as on per-step cost: a method that balances early runs 500-step episodes for most of training, so the fastest learners by wall clock are not the cheapest per step. The last two columns correct for that. Steps per second is the run's total environment steps (mean episode reward × 5000) divided by wall time, and microseconds per step is its reciprocal. By that measure the 1983 agent and REINFORCE are cheapest, at under 10 µs per step, because each step is a handful of Python operations on tiny arrays (REINFORCE only records the step and updates once per episode). Q-learning pays about twice that for several small numpy calls per step. The 1986 networks (two forward and two backward passes), the 1988 lookahead (two extra dynamics evaluations) and Dyna (five planning updates) are the most expensive. At this scale interpreter overhead dominates arithmetic, so these numbers reflect Python call counts far more than floating-point work.

Hyperparameters were tuned lightly, on seed 0 only, to make each method demonstrably work; the table is not a fair benchmark of the methods against each other. Each directory's README notes where its settings depart from the original paper and why.

## Requirements

- Python 3.10+
- `numpy`, `matplotlib`, `tqdm`; `pytest` to run the tests

```sh
pip install numpy matplotlib tqdm pytest
```

## Quick start

Train a policy. Each training episode starts with the pole at a random angle anywhere in the full ±12° range, so the agent learns to recover from large tilts, not just to hold the pole near vertical. The best checkpoint seen during training is saved to `cartpole_<soln>.npz`.

```sh
python main.py --mode train                                  # Q-learning, renders every 100th episode
python main.py --mode train --soln 1983_actor_critic         # any other solution
python main.py --mode train --no-render                      # headless, fastest
```

Run the saved policy deterministically with no exploration or learning (renders every episode):

```sh
python main.py --mode infer
python main.py --mode infer --soln 1992_reinforce --theta0 -11   # start from a hard tilt
```

Compare against a random baseline:

```sh
python main.py --mode infer --agent random
```

In train mode a progress bar shows the latest episode's total reward, its 100-episode average, the best 100-episode average so far and each solution's own diagnostics (epsilon, noise level, TD error, ...). Close the plot window or press `Ctrl-C` to stop at any time; the best checkpoint is still saved when you interrupt.

## What you'll see

Sample runs of the 1983 actor-critic solution, training on the left (every 100th episode rendered) and inference on the right:

<p align="center">
  <img src="2026-09-06%2000.48.21.gif" width="49%" alt="1983 actor-critic: training run, learning curve rising to 500" />
  <img src="2026-09-06%2000.47.08.gif" width="49%" alt="1983 actor-critic: inference run with the frozen policy" />
</p>

The window has three panels:

- **Top left:** the cart and pole on a track. Red dashed lines mark the position limit where the episode terminates. A text readout shows the episode, step, the solution's diagnostics and the four state variables.
- **Bottom left:** the learning curve. The grey line is the total reward collected in each episode and the blue line is its moving average over the last 100 episodes.

  CartPole pays a reward of exactly +1 for every step the pole stays within 12° and the cart stays on the track, so an episode's total reward is simply the number of steps it survived. A value of 500 means the episode hit the time limit while still balanced, which is the best possible outcome.

  A note on words. The per-step +1 is the *reward*. The sum of rewards over an episode is what reinforcement-learning texts call the *return*, and the formulation in the 1989 README uses that term because the equations do. The plots and console output say "total reward" instead, since to a programmer "return" reads as a function returning.

- **Right, full height:** a phase portrait of the pole, angle θ on the horizontal axis and angular velocity θ̇ on the vertical, traced step by step for each rendered episode. The plant plus the policy form a closed-loop dynamical system, and this is its state-space picture. A good policy spirals in toward the origin (upright, at rest) and then chatters in a small cycle around it, which is what bang-bang control does. A failing episode spirals out through one of the red ±12° lines. The orange dot is the current state; earlier episodes fade so that a multi-episode inference run accumulates into one picture. Different solutions have visibly different portraits: the 1983 BOXES policy, with only six angle regions, rocks the pole in a wide cycle of about ±8°, while finer-grained policies hold a much tighter one.

During training the per-episode total reward is noisy because every episode starts from a different angle and exploration is still on. The moving average is the signal to watch.

## Options

| Flag | Default | Description |
|---|---|---|
| `--mode {train,infer}` | `train` | `train` learns and saves a policy. `infer` loads a saved policy and runs it deterministically. |
| `--soln NAME` | `1989_qlearning` | Which solution directory's `soln.py` to use. See the lineage table. |
| `--agent {soln,qlearning,random}` | `soln` | `soln` uses `--soln`. `qlearning` is a backward-compatible alias that forces `--soln 1989_qlearning`. `random` is the uniform baseline and does not learn. |
| `--model PATH` | `cartpole_<soln>.npz` | Where to save (train) or load (infer) the learned parameters. |
| `--episodes N` | 5000 train / 10 infer | Number of episodes to run. |
| `--render-every N` | 100 train / 1 infer | Animate every Nth episode. Lower is slower but shows more. |
| `--theta-range DEGREES` | 12 | Train only. Each episode starts with the pole at a uniform random angle in ±DEGREES. Valid range 0 to 12 inclusive. Use about 3 to mimic Gymnasium's narrow start. |
| `--fps F` | 50 | Animation speed in frames per second. |
| `--no-render` | off | Run headless. Useful for fast training. |
| `--seed N` | 0 | Random seed for the environment, agent and start states. |
| `--x0 METERS` | random | Infer only. Initial cart position. See [Initial state](#initial-state). |
| `--theta0 DEGREES` | random | Infer only. Initial pole angle. See [Initial state](#initial-state). |

Examples:

```sh
# Training: every run is headless (no visual rendering)
# Running all the training scripts without matplotlib rendering completes in ~3 mins
for s in 1983_actor_critic 1986_actor_critic_backprop 1988_td 1989_qlearning 1990_dyna 1992_reinforce; do
  python main.py --mode train --soln $s --no-render
done

# Inference: with no render finishes in ~4 sec
for s in 1983_actor_critic 1986_actor_critic_backprop 1988_td 1989_qlearning 1990_dyna 1992_reinforce; do
  python main.py --mode infer --soln $s --no-render --episodes 20 --theta0 -11 | tail -1
done

# Keep separate policies
python main.py --mode train --model policies/run_a.npz
python main.py --mode infer --model policies/run_a.npz

# Train only on near-upright starts (the Gymnasium default), then see it fail from a tilt
python main.py --mode train --no-render --theta-range 3 --model policies/narrow.npz
python main.py --mode infer --model policies/narrow.npz --theta0 -8
```

### Initial state

**Training** draws the initial pole angle uniformly from ±`--theta-range` degrees (default the full ±12°). Cart position and both velocities are drawn from Gymnasium's default ±0.05 band. `--x0` and `--theta0` are rejected in train mode.

**Inference** uses `--x0` and `--theta0` if given. Both are optional and independent; anything you don't set keeps Gymnasium's default random draw.

| | `--x0` | `--theta0` |
|---|---|---|
| Meaning | Cart position along the track | Pole angle from vertical |
| Units | meters | degrees |
| Valid range | `-2.4 < x0 < 2.4` (exclusive) | `-12 < theta0 < 12` (exclusive) |
| Zero means | Center of the track | Pole perfectly upright |
| Sign | Negative = left, positive = right | Negative = tilted left, positive = tilted right |
| Default | Uniform random in `[-0.05, 0.05]` m | Uniform random in `[-0.05, 0.05]` rad (about ±2.9°) |

The limits are the same thresholds that end an episode: the cart leaving the ±2.4 m track or the pole passing ±12° from upright. Values at or beyond them are rejected by the script, since the episode would terminate on the first step. Initial cart velocity and pole angular velocity are always random in `[-0.05, 0.05]` and cannot be set from the command line. The physical meaning of these limits is derived in [the 1989 README](1989_qlearning/README.md#why-these-ranges).

### Why these ranges?

The bounds appear in three places: the termination thresholds that define the task, the clipping ranges used by $\phi$, and the CLI validation for `--x0`, `--theta0` and `--theta-range`. They all trace back to the physics.

**Pole angle, ±12° (0.2095 rad).** This is the failure threshold from [Barto, Sutton and Anderson (1983)][barto1983] and is kept by Gymnasium. Physically it marks the region where the pole is still meaningfully "balanced":

- The upright pole is an unstable equilibrium. Within ±12°, $\sin\theta \approx \theta$ to better than 1%, so the dynamics are close to the linear inverted pendulum for which stabilizing control is well posed.
- Recoverability is a matter of torque budget. From the $\ddot\theta$ equation, gravity's angular acceleration at 12° is about 3.3 rad/s² while the cart's push can supply about 14 rad/s² in the opposite direction. The controller therefore has roughly a four-to-one margin at the edge of the band, which is why a policy trained on the full range recovers from 11° starts. Beyond the band the margin keeps shrinking, and past about 43° (where $\tan\theta = F/(m_c+m_p)g$) a single-force bang-bang controller cannot bring the pole back. The 12° threshold is a conservative task definition well inside the physical limit, not the limit itself.
- Angular velocity matters as much as angle. A pole at 11° already falling outward at several rad/s cannot be saved even though the angle is in range. That is why $\phi$ discretizes $\dot\theta$ with more bins (16) than $\theta$ (8), and why it clips $\dot\theta$ at ±3.5 rad/s (200°/s): at that rate the pole crosses the whole 24° band in six steps, and anything faster is effectively already lost.

**Cart position, ±2.4 m.** The cart runs on a finite 4.8 m track, again from the [1983 setup][barto1983]. Leaving the track is a failure. Without a position bound the agent could "balance" indefinitely by accelerating in one direction, so the bound is what makes this a balancing task rather than a chasing task. This solution's policy ignores $x$ and $\dot x$, so its only failures from valid starts are drifting off the track over a long episode. The 1983 and 1988 solutions include cart bins and do not have this failure mode.

**Cart velocity, ±3 m/s.** This appears only as the clipping range of $\phi$ (unused while $\dot x$ has a single bin) and is not a physical limit. The environment never caps $\dot x$. With a 10 N force on 1.1 kg total mass the cart accelerates at about 9.1 m/s², or 0.18 m/s per step, so reaching 3 m/s from rest takes 16 steps of pushing in one direction, by which point the cart has already travelled most of the track.

**Initial-state band, ±0.05.** Gymnasium's reset draws all four state variables from $[-0.05, 0.05]$ in SI units (meters, m/s, radians, rad/s), i.e. about ±2.9° of tilt. That is small enough that a trivial policy can balance for a while, which is why training on it alone produces an agent that cannot recover from an 8° start. The `--theta-range` default of 12 widens the angle draw to the whole recoverable band while leaving the velocity bands at Gymnasium's values. `--x0` and `--theta0` must be strictly inside the termination thresholds because a start exactly on or beyond them terminates before the agent acts.


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

The optimal action-value function $Q^{\ast}(s, a)$ is the expected return from taking $a$ in $s$ and acting optimally thereafter. It is the unique fixed point of the Bellman optimality equation, which for this deterministic environment reads

$$
Q^{\ast}(s, a) =
\begin{cases}
1, & f(s, a) \in \mathcal S_{\text{term}} \\
1 + \gamma \max_{a'} Q^{\ast}\big(f(s, a), a'\big), & \text{otherwise.}
\end{cases}
$$

The optimal policy is greedy with respect to $Q^{\ast}$:

$$
\pi^{\ast}(s) = \arg\max_{a \in \{0, 1\}} Q^{\ast}(s, a).
$$

Every solution in this repository is trying to find $\pi^{\ast}$ for this one equation. They differ in what they estimate (a state value, an action value, or the policy directly) and in whether they use $f$.

## The optimal-control lineage (for later)

Reinforcement learning and optimal control converged on the same object, the Bellman equation, from different directions, and this repository so far covers only the learning side. Threads to pick up later, in rough order:

- **Dynamic programming.** Bellman (1957) and value iteration on a discretized cart-pole model: the exact solution the 1989 Q-learning approximates from samples.
- **Linear-quadratic regulation.** Linearize the plant about the upright equilibrium and solve the Riccati equation. The resulting gain vector is a five-parameter linear controller much like the REINFORCE policy, obtained in closed form from the model instead of from data. A bang-bang version follows by taking the sign.
- **Adaptive critics as approximate DP.** Werbos (1987 onward) framed the 1983 critic as Heuristic Dynamic Programming and proposed the DHP/GDHP family, which is the control-theory community's route to the same actor-critic architecture.
- **Neuro-dynamic programming.** Bertsekas and Tsitsiklis (1996) consolidate both lineages under one theory.

