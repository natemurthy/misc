# rl-cart-pole

A minimal, self-contained CartPole reinforcement-learning simulator with a live
matplotlib visualization. The physics, rewards and termination rules match
Gymnasium's [CartPole-v1](https://gymnasium.farama.org/environments/classic_control/cart_pole/),
but nothing from Gymnasium is required. The agent is **tabular Q-learning** over
a discretized state space. There is no neural network in this project; see
[RL formulation](#rl-formulation) for exactly what is learned and how.

The environment is hand-written but follows the Gymnasium `Env` API, so the
same loop runs against the real library. The [`gym/`](gym/)
directory holds that version, with notes on what Gymnasium adds and when to
prefer it.

## Requirements

- Python 3.10+
- `numpy`, `matplotlib` and `tqdm`

```sh
pip install numpy matplotlib tqdm
```

## Quick start

Train a policy. Each training episode starts with the pole at a random angle
anywhere in the full ±12° range, so the agent learns to recover from large
tilts, not just to hold the pole near vertical. The best Q-table seen during
training is saved to `cartpole_q.npz`.

```sh
python main.py --mode train               # renders every 100th episode
python main.py --mode train --no-render   # headless, about 15 s for 5000 episodes
```

Run the saved policy greedily with no exploration or learning (renders every
episode):

```sh
python main.py --mode infer
python main.py --mode infer --theta0 -11  # start from a hard tilt
```

Compare against a random baseline:

```sh
python main.py --mode infer --agent random
```

In train mode a progress bar shows the latest episode's total reward, its
100-episode average, the best 100-episode average so far and the current
epsilon. Close the
plot window or press `Ctrl-C` to stop at any time; the best checkpoint is still
saved when you interrupt.

## What you'll see

The window has two panels:

- **Top:** the cart and pole on a track. Red dashed lines mark the position limit
  where the episode terminates. A text readout shows the episode, step, current
  epsilon and the four state variables.
- **Bottom:** the learning curve. The grey line is the total reward collected
  in each episode and the blue line is its moving average over the last 100
  episodes.

  CartPole pays a reward of exactly +1 for every step the pole stays within 12°
  and the cart stays on the track, so an episode's total reward is simply the
  number of steps it survived. A value of 500 means the episode hit the time
  limit while still balanced, which is the best possible outcome.

  A note on words. The per-step +1 is the *reward*. The sum of rewards over an
  episode is what reinforcement-learning texts call the *return*, and the
  [RL formulation](#rl-formulation) section below uses that term because the
  equations do. The plots and console output say "total reward" instead, since
  to a programmer "return" reads as a function returning. The plotted value is
  the plain, undiscounted sum; the agent internally optimizes the discounted
  version, but the two rank episodes the same way.

During training the per-episode total reward is noisy because every episode starts
from a different angle and exploration is still on. The moving average is the
signal to watch.

## Options

| Flag | Default | Description |
|---|---|---|
| `--mode {train,infer}` | `train` | `train` learns and saves a policy. `infer` loads a saved policy and runs it greedily. |
| `--agent {qlearning,random}` | `qlearning` | Which agent to use. The random agent does not learn. |
| `--model PATH` | `cartpole_q.npz` | Where to save (train) or load (infer) the Q-table. |
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
# Fast headless training, then watch the result
python main.py --mode train --no-render
python main.py --mode infer --episodes 5

# Keep separate policies
python main.py --mode train --model policies/run_a.npz
python main.py --mode infer --model policies/run_a.npz

# Train only on near-upright starts (the Gymnasium default), then see it fail from a tilt
python main.py --mode train --no-render --theta-range 3 --model policies/narrow.npz
python main.py --mode infer --model policies/narrow.npz --theta0 -8

# Stress-test the full-range policy
python main.py --mode infer --x0 1.5 --theta0 -8
```

### Initial state

**Training** draws the initial pole angle uniformly from ±`--theta-range`
degrees (default the full ±12°). Cart position and both velocities are drawn
from Gymnasium's default ±0.05 band. `--x0` and `--theta0` are rejected in train
mode.

**Inference** uses `--x0` and `--theta0` if given. Both are optional and
independent; anything you don't set keeps Gymnasium's default random draw.

| | `--x0` | `--theta0` |
|---|---|---|
| Meaning | Cart position along the track | Pole angle from vertical |
| Units | meters | degrees |
| Valid range | `-2.4 < x0 < 2.4` (exclusive) | `-12 < theta0 < 12` (exclusive) |
| Zero means | Center of the track | Pole perfectly upright |
| Sign | Negative = left, positive = right | Negative = tilted left, positive = tilted right |
| Default | Uniform random in `[-0.05, 0.05]` m | Uniform random in `[-0.05, 0.05]` rad (about ±2.9°) |

The limits are the same thresholds that end an episode: the cart leaving the
±2.4 m track or the pole passing ±12° from upright. Values at or beyond them are
rejected by the script, since the episode would terminate on the first step.
Initial cart velocity and pole angular velocity are always random in
`[-0.05, 0.05]` and cannot be set from the command line. The physical meaning
of these limits is discussed under [Why these ranges](#why-these-ranges).

The policy ignores cart position, so large `--x0` values are a good way to see
it drift off the track. With the default full-range training it recovers from
any `--theta0` inside the band.

## How it works

- `CartPoleEnv` re-implements the CartPole-v1 dynamics: Euler integration at
  0.02 s, +1 reward per step, termination when the pole exceeds 12° or the cart
  moves more than 2.4 m, truncation at 500 steps. It follows the Gymnasium API
  without importing it: `reset(seed=, options=)` returns `(obs, info)` and
  `step(action)` returns `(obs, reward, terminated, truncated, info)`, with
  `float32` observations. `options={"x0": ..., "theta0": ...}` overrides the
  initial position and angle.
- `QLearningAgent` discretizes the pole angle and angular velocity into an
  8 × 16 grid (cart position and velocity are ignored) and learns a Q-table with
  epsilon-greedy exploration that decays each episode. Ties between the two
  actions are broken randomly so unvisited cells carry no left/right bias.
  `save`/`load` persist the table as a `.npz` file, and `freeze` turns off
  exploration and updates for inference.
- The training loop keeps a copy of the Q-table whenever the 100-episode moving
  average reaches a new high, and saves that copy rather than the final one.
- `Renderer` draws the simulation and the learning curve with matplotlib in
  interactive mode.

## RL formulation

### The Markov decision process

The problem is the finite-horizon, discounted MDP $(\mathcal S, \mathcal A, P, R, \gamma, \rho_0)$:

- **State** $s = (x, \dot x, \theta, \dot\theta) \in \mathcal S \subset \mathbb R^4$:
  cart position and velocity, pole angle from vertical and angular velocity.
- **Action** $a \in \mathcal A = \{0, 1\}$: apply a horizontal force
  $F = -10\,\text{N}$ (push left) or $F = +10\,\text{N}$ (push right) to the cart
  for one time step $\tau = 0.02\,\text{s}$.
- **Transition** $P(s' \mid s, a)$ is deterministic, $s' = f(s, a)$, given by
  Euler integration of the cart-pole equations of motion (Barto, Sutton and
  Anderson, 1983):

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

  with $g = 9.8$, cart mass $m_c = 1.0$, pole mass $m_p = 0.1$ and pole
  half-length $l = 0.5$.
- **Reward** $R(s, a, s') = 1$ for every transition, including the one that
  terminates. Return is therefore the number of steps survived.
- **Terminal states** $\mathcal S_{\text{term}} = \{ s : |x| > 2.4 \ \text{or}\ |\theta| > 12^\circ \}$.
  Episodes are also truncated at $T = 500$ steps; truncation is a horizon, not a
  failure, and is treated differently in the update below.
- **Discount** $\gamma = 0.99$.
- **Start distribution** $\rho_0$: all four components uniform in $[-0.05, 0.05]$,
  except that in training the angle is drawn uniformly from $[-12^\circ, 12^\circ]$
  (see `--theta-range`). Changing $\rho_0$ changes which states are visited during
  learning but does not change $P$, $R$ or the optimal value function.

The objective is to find a policy $\pi : \mathcal S \to \mathcal A$ maximizing the
expected discounted return (the sum of rewards, called "total reward" in the
plots)

$$
G_t = \sum_{k=0}^{\infty} \gamma^k r_{t+k+1}.
$$

Because every reward is 1, an episode that survives $n$ more steps has
$G_t = (1 - \gamma^n)/(1 - \gamma)$, which saturates at $1/(1-\gamma) = 100$. So
the discount gives an effective planning horizon of about 100 steps (2 s), and
maximizing return is the same as surviving longer.

### Bellman optimality

The optimal action-value function $Q^*(s, a)$ is the expected return from taking
$a$ in $s$ and acting optimally thereafter. It is the unique fixed point of the
Bellman optimality equation, which for this deterministic environment reads

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

### Model-free, off-policy, tabular Q-learning

This is a **model-free** formulation. Although we wrote $f(s, a)$ above, the
agent never evaluates it, never learns an approximation of it, and never plans
by rolling it forward. It only observes sampled transitions
$(s_t, a_t, r_{t+1}, s_{t+1})$ from the simulator and updates value estimates
from them. A model-based approach would instead use $f$ (known or learned) to
look ahead, for example with value iteration on a discretized model, or a
linear-quadratic regulator around the upright equilibrium. Q-learning is also
**off-policy**: it estimates $Q^*$, the value of the greedy policy, while the
behavior policy that generates data is exploratory.

**State aggregation.** $\mathcal S$ is continuous, so the agent works with a
discretized state $\phi(s)$. Cart position and velocity are collapsed into a
single bin each; the pole angle and angular velocity are clipped and mapped onto
uniform grids:

$$
\phi(s) = \left(
\operatorname{round}\!\Big(7 \cdot \tfrac{\operatorname{clip}(\theta, -0.21, 0.21) + 0.21}{0.42}\Big),\;
\operatorname{round}\!\Big(15 \cdot \tfrac{\operatorname{clip}(\dot\theta, -3.5, 3.5) + 3.5}{7}\Big)
\right) \in \{0..7\} \times \{0..15\}.
$$

**The learned object is a table, not a network.** The action-value estimate is
an array $Q \in \mathbb R^{8 \times 16 \times 2}$, i.e. 256 numbers, one per
(angle bin, angular-velocity bin, action). Initialized to zero. This is what
`--mode train` produces and what `cartpole_q.npz` contains.

**Update rule.** After each transition the single visited entry is moved toward
the sampled Bellman target:

$$
Q\big(\phi(s_t), a_t\big) \leftarrow Q\big(\phi(s_t), a_t\big) + \alpha\Big[ y_t - Q\big(\phi(s_t), a_t\big) \Big],
\qquad
y_t =
\begin{cases}
r_{t+1}, & s_{t+1} \in \mathcal S_{\text{term}} \\
r_{t+1} + \gamma \max_{a'} Q\big(\phi(s_{t+1}), a'\big), & \text{otherwise,}
\end{cases}
$$

with learning rate $\alpha = 0.1$. The bracketed quantity is the temporal-difference
error. Note that the target bootstraps on truncated (step 500) transitions but not
on terminated ones: hitting the horizon is not a failure and should not zero out
the future value.

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

after $k$ completed episodes, so exploration decays from 1 to its floor over
roughly 4600 episodes.

**Checkpoint selection.** Tabular Q-learning with a constant step size and
aggregated states does not converge monotonically, so the training loop keeps
the Q-table from the episode with the highest 100-episode moving-average return
and saves that.

**Convergence.** Watkins' theorem guarantees $Q \to Q^*$ for a finite MDP when
every state-action pair is visited infinitely often and step sizes satisfy the
Robbins-Monro conditions. Neither holds exactly here: $\alpha$ is constant and
$\phi$ makes the aggregated process only approximately Markov. In practice the
learned table is a good approximation of $Q^*$ on the discretized problem, which
is all inference needs.

**If this were a neural network.** The formulation above is the same one a Deep
Q-Network uses; only the function class changes. A DQN replaces the table with a
parametric $Q_w(s, a)$ that reads the raw continuous state and trains $w$ by
gradient descent on the squared TD error over a replay buffer $\mathcal D$,

$$
\mathcal L(w) = \mathbb E_{(s, a, r, s') \sim \mathcal D}\Big[\big(r + \gamma \max_{a'} Q_{w^-}(s', a') - Q_w(s, a)\big)^2\Big],
$$

with a slowly updated copy $w^-$ of the weights as the bootstrap target. Nothing
in this repository does that; it is mentioned only to place the tabular method.

### Inference

`--mode infer` loads the table and runs the greedy policy with
$\varepsilon = 0$ and no updates. At each step it computes the bin index, reads
two numbers and picks the larger:

$$
a_t = \pi(s_t) = \arg\max_{a \in \{0,1\}} Q\big(\phi(s_t), a\big).
$$

That is the entire computation, a constant-time lookup. The only randomness is
the environment's start state (unless `--x0`/`--theta0` are given) and the tie
break in cells the table never visited, where both entries are still zero.

### Why these ranges

The bounds appear in three places: the termination thresholds that define the
task, the clipping ranges used by $\phi$, and the CLI validation for `--x0`,
`--theta0` and `--theta-range`. They all trace back to the physics.

**Pole angle, ±12° (0.2095 rad).** This is the failure threshold from the
original 1983 formulation and is kept by Gymnasium. Physically it marks the
region where the pole is still meaningfully "balanced":

- The upright pole is an unstable equilibrium. Within ±12°,
  $\sin\theta \approx \theta$ to better than 1%, so the dynamics are close to
  the linear inverted pendulum for which stabilizing control is well posed.
- Recoverability is a matter of torque budget. From the $\ddot\theta$ equation,
  gravity's angular acceleration at 12° is about 3.3 rad/s² while the cart's
  push can supply about 14 rad/s² in the opposite direction. The controller
  therefore has roughly a four-to-one margin at the edge of the band, which is
  why a policy trained on the full range recovers from 11° starts. Beyond the
  band the margin keeps shrinking, and past about 43° (where $\tan\theta = F/(m_c+m_p)g$) a single-force
  bang-bang controller cannot bring the pole back. The 12° threshold is a
  conservative task definition well inside the physical limit, not the limit
  itself.
- Angular velocity matters as much as angle. A pole at 11° already falling
  outward at several rad/s cannot be saved even though the angle is in range.
  That is why $\phi$ discretizes $\dot\theta$ with more bins (16) than
  $\theta$ (8), and why it clips $\dot\theta$ at ±3.5 rad/s (200°/s): at that
  rate the pole crosses the whole 24° band in six steps, and anything faster is
  effectively already lost.

**Cart position, ±2.4 m.** The cart runs on a finite 4.8 m track, again from
the 1983 setup. Leaving the track is a failure. Without a position bound the
agent could "balance" indefinitely by accelerating in one direction, so the
bound is what makes this a balancing task rather than a chasing task. The
current policy ignores $x$ and $\dot x$, so its only failures from valid starts
are drifting off the track over a long episode; adding position bins is the
natural next improvement.

**Cart velocity, ±3 m/s.** This appears only as the clipping range of $\phi$
(unused while $\dot x$ has a single bin) and is not a physical limit. The
environment never caps $\dot x$. With a 10 N force on 1.1 kg total mass the cart
accelerates at about 9.1 m/s², or 0.18 m/s per step, so reaching 3 m/s from rest
takes 16 steps of pushing in one direction, by which point the cart has already
travelled most of the track.

**Initial-state band, ±0.05.** Gymnasium's reset draws all four state variables
from $[-0.05, 0.05]$ in SI units (meters, m/s, radians, rad/s), i.e. about
±2.9° of tilt. That is small enough that a trivial policy can balance for a
while, which is why training on it alone produces an agent that cannot recover
from an 8° start. The `--theta-range` default of 12 widens the angle draw to the
whole recoverable band while leaving the velocity bands at Gymnasium's values.
`--x0` and `--theta0` must be strictly inside the termination thresholds
because a start exactly on or beyond them terminates before the agent acts.

## Notes

- Tabular Q-learning is sensitive to the discretization and the exploration
  schedule. The bin counts, clipping ranges, learning rate and epsilon decay
  live in `QLearningAgent.__init__` in `main.py` if you want to experiment.
- Results still vary somewhat with `--seed`. The best-checkpoint logic removes
  most of the variance, but if a trained policy underperforms, a different seed
  or more episodes is the first thing to try.
