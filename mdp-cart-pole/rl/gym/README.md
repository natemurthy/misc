# rl-cart-pole, Gymnasium edition

The same CartPole problem, agent and command line as [`../main.py`](../main.py), re-implemented on top of Farama's [Gymnasium](https://gymnasium.farama.org/). The parent project owns its physics (`../common/env.py`) and rendering; this one gets them from the library and keeps only two small files of its own.

| File | Role |
|---|---|
| `cartpole_env.py` | Subclasses Gymnasium's `CartPoleEnv` to add the wide-angle start distribution and exact start overrides, and registers it as `CartPoleFullRange-v0`. |
| `main.py` | Training and inference loop. Imports the Q-learning agent unchanged from `../main.py`, builds the environment with `gym.make` plus wrappers, and shows Gymnasium's rendered frames next to the learning curve. |

## Requirements

```sh
pip install "gymnasium[classic-control]" numpy matplotlib tqdm
pip install moviepy      # only for --record-video
```

`gymnasium[classic-control]` pulls in pygame, which Gymnasium's CartPole uses to draw frames.

## Quick start

Run from this directory.

```sh
python main.py --mode train                          # renders every 100th episode
python main.py --mode train --no-render              # headless, saves cartpole_q_gym.npz
python main.py --mode infer                          # greedy policy, renders every episode
python main.py --mode infer --theta0 -11 --x0 1.0    # exact start state
python main.py --mode infer --record-video videos    # MP4 per episode, no window needed
python main.py --mode infer --agent random
```

All flags from the parent script work the same way: `--mode`, `--agent`, `--model`, `--episodes`, `--render-every`, `--theta-range`, `--fps`, `--no-render`, `--seed`, `--x0`, `--theta0`. See `python main.py --help` and the [parent README](../README.md) for their meaning and valid ranges. The one addition is `--record-video DIR`.

Trained Q-tables are interchangeable between the two scripts. A table saved by either can be loaded by the other with `--model`, since the agent, the discretization and the underlying physics are identical.

## What Gymnasium adds

Concretely, mapped to what changed between `../main.py` and this directory.

**A reference environment.** The equations of motion, reset logic and termination checks in the parent `common/env.py` are replaced by `gymnasium.envs.classic_control.CartPoleEnv`, maintained upstream. That class implements the cart-pole dynamics and ±12° / ±2.4 m failure thresholds of [Barto, Sutton and Anderson (1983)][barto1983], minus the paper's friction terms and with Gymnasium's +1-per-step reward in place of the paper's failure signal. See the parent README for how this project relates to that paper. The parent script was already written against Gymnasium's `reset` and `step` signatures, so the loop body did not change at all.

**Wrappers.** Behavior the parent script codes by hand is composed from library pieces instead:

| Parent script | Here |
|---|---|
| `steps >= 500` check inside `step` | `TimeLimit`, applied automatically by `gym.make` from the registered `max_episode_steps` |
| Summing `reward` in the loop | `RecordEpisodeStatistics`, which puts the episode's total reward in `info["episode"]["r"]` on the last step |
| Not available | `RecordVideo`, which writes an MP4 of any episode you choose via `--record-video` |

Other wrappers you could add with one line each: `TransformObservation` to move the discretization out of the agent, `NormalizeObservation`, `ClipAction`, or `FrameStackObservation` if you later swap in an agent that needs history.

**A registry.** `CartPoleFullRange-v0` is a name. `gym.make("CartPoleFullRange-v0", theta_range=...)` reproduces the experiment from a string plus kwargs, and the registration carries the step limit and reward threshold with it. That is the natural home for the full-range start distribution the parent script exposes through `--theta-range`.

**Rendering.** `render_mode="rgb_array"` returns a 400 × 600 RGB frame drawn with pygame. This script shows those frames in the top-left matplotlib panel and keeps the parent's learning-curve panel below and its phase portrait on the right, so the window looks the same but the cart-pole drawing is Gymnasium's. The same frames feed `RecordVideo`. Passing `render_mode="human"` instead would open Gymnasium's own pygame window and skip matplotlib entirely.

The bottom panel plots the **total reward per episode**. Because CartPole's reward is +1 per step, this equals the number of steps the episode survived, capped at 500 by the time limit. Reinforcement-learning texts and Gymnasium's own docs call this sum the episode *return*; the plots say "total reward" to avoid the programming sense of the word. Here the value is read from `info["episode"]["r"]`, which the `RecordEpisodeStatistics` wrapper fills in on the final step of each episode, instead of being summed by hand as in the parent script.

**A standard interface.** Anything that speaks the Gymnasium API can now drive this environment: Stable-Baselines3, CleanRL, RLlib, or your own DQN. The tabular agent here does not need that, but comparing it against a library PPO or DQN is now a few lines rather than an adapter.

**Vectorization.** `gym.make_vec("CartPoleFullRange-v0", num_envs=8)` runs eight copies in lockstep for agents that learn from batches. Tabular Q-learning updates one cell per step and would not benefit, so it is not used here.

## What Gymnasium does not add

- **Anything on the agent side.** Gymnasium is environments only. The Q-learning update, epsilon schedule, best-checkpoint logic and inference math are imported from the parent file verbatim.
- **Exact start states.** Gymnasium's `reset(options=...)` for CartPole only accepts `low`/`high` bounds for the uniform draw. Setting an exact `x0` or `theta0`, or widening only the angle, still needs the subclass in `cartpole_env.py`. It is 30 lines, most of them docstring.
- **The learning-curve panel.** Gymnasium renders the simulation, not training progress. That stays in matplotlib.

## Should the parent script be replaced by this one?

Not for its current purpose. The parent is a readable, dependency-light demonstration where the physics, the MDP and the learner are all visible in one file, and its README's formulation section leans on that transparency. This directory is the better starting point when you want any of:

- a second agent from an off-the-shelf RL library to compare against,
- video output instead of a live window,
- many environments in parallel,
- an environment someone else can `gym.make` without reading your code.

Because the parent already conforms to the Gymnasium API, moving between the two is a matter of swapping the environment constructor. Nothing else in the loop changes.

## Differences worth knowing

- **Observation dtype** is `float32` in both. The parent converts on the way out to match Gymnasium.
- **Reset seeding.** Gymnasium seeds the environment's RNG on the first `reset(seed=...)` and ignores `seed=None` afterwards. This script passes the seed on episode 1 only. The parent seeds in the constructor and also accepts `reset(seed=...)`.
- **Truncation source.** In the parent, `truncated` is set by the environment itself. Here it comes from the `TimeLimit` wrapper, and the base `CartPoleEnv` never sets it. Both report `terminated` identically.
- **Random-number streams differ** between the two implementations even for the same `--seed`, because Gymnasium seeds through `gymnasium.utils.seeding`. Runs are reproducible within each script, not across them.
- **`RecordVideo` episode indexing** is zero-based, so with `--render-every N` the recorded episodes are 1, N, 2N, ... in the script's one-based numbering, matching the live-render schedule.

[barto1983]: https://github.com/david78k/pendulum/blob/master/c/anderson/Neuronlike%20Adaptive%20Elements%20That%20Can%20Solve%20Difficult%20Learning%20Control%20Problems%20Barto1983.pdf
