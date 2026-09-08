# mdp-cart-pole (RL)

Study of the `mpd-cart-pole` problem within the reinforcement learning (RL) school of thought.

The cart-pole benchmark framed as an RL problem first appeared in [Barto, Sutton, and Anderson (1983)][barto1983] (the [1983_actor_critic/](1983_actor_critic/) subfolder locally implements this method). The following explores prominent methods in the RL literature since this seminal problem formulation appeared for solving the cart-pole problem. 

Sample runs below of the 1983 actor-critic solution, training on the left (every 100th episode rendered) and inference on the right (phase portraits not shown):

<p align="center">
  <img src="2026-09-06%2000.48.21.gif" width="49%" alt="1983 actor-critic: training run, learning curve rising to 500" />
  <img src="2026-09-06%2000.47.08.gif" width="49%" alt="1983 actor-critic: inference run with the frozen policy" />
</p>

[barto1983]: https://github.com/david78k/pendulum/blob/master/c/anderson/Neuronlike%20Adaptive%20Elements%20That%20Can%20Solve%20Difficult%20Learning%20Control%20Problems%20Barto1983.pdf

## Gymnasium API

Each method implements the environment interface provided by the widely standard Gymnasium [CartPole-v1](https://gymnasium.farama.org/environments/classic_control/cart_pole/) SDK that follows the Gymnasium `Env` API without requiring the library. The shared environment this codebase subtly departs from 1983 paper in two ways inherited from Gymnasium:

1. The friction terms are dropped (their effect is negligible, a 0.0005 N cart friction against a 10 N push amounts to less than a rounding error on learning table),
2. The reward is +1 per step rather than −1 at failure. Each solution's README notes what that reward change required.

The environment class here follows Gymnasium's `Env` API: `reset(seed=, options=)` returns `(obs, info)` and `step(action)` returns `(obs, reward, terminated, truncated, info)` with `float32` observations. The [`gym/`](gym/README.md) directory runs the same problem and the same Q-learning agent on the real library, with notes on what Gymnasium adds and when to prefer it.

## Layout

Each annually prefixed directory (`<year>_<method>/`) implements a notable RL method dating back to techniques from the year in which it appeared in the field, in the order the ideas appeared in the academic literary history. The base `main.py` trains or runs inference across each of the methods with a live matplotlib view of the cart, the pole and the learning curve. 

```bash
main.py                     CLI driver: --soln picks a solution, one train/infer loop for all
hparam_sweep.py             parallel hyperparameter sweeps: configs x seeds in a process pool
complexity.py               implementation-complexity table (SLOC, branches, parameters, hyperparameters)
common/
  env.py                    the CartPole MDP (Gymnasium API, no Gymnasium dependency; optional continuous force)
  features.py               state representations: grid discretizer, BOXES decoder, normalizer
  agent.py                  BaseAgent interface + RandomAgent; save/load/freeze/snapshot
  render.py                 matplotlib visualization
  deep.py                   PyTorch helpers for the 2011-2018 solutions (CPU by default; CARTPOLE_TORCH_DEVICE to change)
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
pytest                    # everything in rl/tests; run from the repository root to include ../oc/tests as well
pytest -m fast            # every test that finishes in under 0.1 s: the unit tests, a few seconds in total
pytest -m slow            # everything else: learning runs and the subprocess CLI checks; several minutes
pytest -k 1983            # tests for just one major solution for the given year
```

- `test_<solution>.py`, one file per solution directory, holds everything about that solution. Each subclasses `AgentInterfaceTests` from `interface_checks.py`, which runs the shared interface checks: valid actions, save/load round trip, frozen policies are deterministic and stop learning, snapshots restore, and identical seeds give identical training. Seven of the files also hold method-specific tests, for the solutions whose mathematics is written out by hand and worth checking against finite differences, Monte Carlo or a known closed form: 1988, 1990, 1992, 1999, 2005, 2007 and 2011 PILCO. Each of those solutions' READMEs lists its tests under Run. One suite-level detail: PILCO fits its Gaussian process once per file, in a module fixture, and every PILCO test reuses that fit, so the file is all `fast` at a one-time cost of a few seconds.
- `test_suite_layout.py` checks that every solution in `main.SOLUTIONS` has such a file.
- `test_env.py` checks the MDP: reset options, the five-tuple step API, one Euler step against a hand computation, termination and truncation, the ~22-step random baseline, and, if `gymnasium` is installed, a trajectory match against the reference `CartPole-v1`.
- `test_features.py` checks the discretizers, including that the BOXES decoder produces all 162 regions with the paper's boundaries.
- `test_complexity.py` checks `complexity.py`: docstrings and comments are excluded from line counts, a known solution measures as expected, and the table has one row per solution.
- `test_learning.py` (marked `slow`) trains every solution from scratch with a small per-method episode budget and requires the frozen policy to survive at least 100 steps from the default start, about five times the random baseline. PILCO is exempt from the accompanying "not yet balancing in the first ten episodes" sanity check, because it is.
- `test_cli.py` (marked `slow`, every case spawns a Python subprocess) exercises `main.py`: train-then-infer for every solution, argument validation, the legacy Q-table format, and that the untouched `gym/main.py` still imports this module's agents.


## Hyperparameter sweeps

`hparam_sweep.py` trains many (configuration, seed) pairs in parallel processes, headless, with the same loop and best-checkpoint rule as `main.py`, then scores each frozen policy from a few start angles and prints a table. It exists because the 1999 solution's tuning runs took minutes each; on a 12-core machine eight jobs finish in the time of the slowest one.

```sh
python hparam_sweep.py --soln 1999_qlearning_continuous --theta-limit 30 --episodes 4000 --seeds 0 1 --eval-angles 12 20 25 \
    --config "hidden=64,advantage_k=0.3" --config "hidden=128,advantage_k=0.3,lr=0.005" --config "" \
    --early-stop 1000:30 --json results.json
```

`--config` is repeatable and takes the same `KEY=VALUE` items as `main.py --hparam`, comma-separated; the empty string means the solution's defaults. `--early-stop EPISODE:AVG` aborts a job whose best 100-episode average is still below `AVG` at `EPISODE`, which prunes hopeless settings early (a random policy averages about 22). `--workers` defaults to one fewer than the machine's cores. Results can be written as JSON for later comparison.

**What one job does.** Each job is exactly one `main.py --mode train --no-render` run: a fresh agent with the given constructor overrides and seed, full-range start angles, the best 100-episode checkpoint kept, then the frozen policy run from each `--eval-angles` value in both directions. The table reports, per job, the best 100-episode average and the episode it was reached at, the mean steps survived from each start angle, and the wall time. Two seeds is the usual minimum, because a setting that works on seed 0 alone is the most common way to fool yourself on this problem.

**When to reach for it.** It works for any solution, since every agent exposes its constructor arguments through `hparams()`, but it earns its keep in four situations:

- A solution does not learn at its first defaults on the standard task and a serial trial-and-error loop would take hours.
- The task is changed, as with `--theta-limit 30`, and the defaults tuned for 12° no longer apply.
- A design choice needs checking across seeds before it becomes a default: a flag, a guard, a schedule.
- A 5000-episode run takes minutes (the PyTorch solutions, the 1999 network), so any comparison of more than two or three settings should run in parallel.

**Where it was used.** The solution READMEs record the sweeps behind their defaults:

- [1999 continuous Q-learning](1999_qlearning_continuous/README.md#tuning-with-hparam_sweeppy): the tool's origin. Eight configurations at two seeds each found the wire-fitting constants, then the wider-angle recipe (`hidden=64`, `advantage_k=0.3`, `lr=0.005`, 8000 episodes) that recovers from 25° on three of four seeds; the choice between batched and one-at-a-time replay came out of the same runs.
- [2013 DQN](2013_dqn/README.md): eight settings on two seeds. The first defaults, 64 units at a step size of 1e-3, learned and then collapsed, the instability DQN is known for. 128 units at 5e-4 reached the cap from both 0° and 11° on both seeds and became the default.
- [2005 NAC](2005_nac/README.md): a twelve-seed sweep over the update schedule exposed the one failure mode, a single huge natural-gradient step taken from a regression with fewer rows than columns early in training, and produced the `min_steps` guard that fixed it. The same sweeps showed what the forgetting factor $\beta$ trades: bias against data.
- [2007 CACLA](2007_cacla/README.md): the paper's own settings (12 hidden units, TD(0), $\sigma = 0.1$) did not learn with the +1-per-step reward; the defaults are the result of comparing widths, traces and exploration noise, and CACLA+Var stays off because a three-seed comparison found plain CACLA as good or better.

The other solutions were tuned by hand on seed 0, lightly, to make each method demonstrably work; the results table is not a fair benchmark of the methods against each other, and each README notes where its settings depart from its paper.

## Literary history

Read the READMEs in order; each explains what it improves on the one before. The 1983 to 1992 solutions and DQN, TRPO and PPO use Gymnasium's two-action version of the problem. The 1999, 2005, 2007, both 2011, 2015 DDPG and 2018 SAC solutions control a continuous force anywhere in ±10 N, which the environment supports through a `continuous=True` flag with the cart-pole system, reward, thresholds and start distribution unchanged. The 1983 to 2007 solutions are numpy only; from 2011 on the methods need automatic differentiation and use PyTorch on the CPU (see `common/deep.py`), which is an optional dependency: without it those PyTorch solutions and their tests are skipped.

| Directory | Year | Method | Learns | Discrete/Continuous | model-based? |
|---|---|---|---|---|---|
| [`1983_actor_critic/`](1983_actor_critic/README.md) | 1983 | Barto, Sutton, Anderson: ASE/ACE actor-critic on the BOXES decoder | actor weights + critic values, 162 boxes each | discrete | no |
| [`1986_actor_critic_backprop/`](1986_actor_critic_backprop/README.md) | 1986-89 | Anderson: the same actor-critic with two-layer backprop networks | two small neural nets | discrete | no |
| [`1988_td/`](1988_td/README.md) | 1988 | Sutton: TD(λ) value prediction, controlled by one-step lookahead | state-value table $V$ | discrete | yes, the true dynamics, to act |
| [`1989_qlearning/`](1989_qlearning/README.md) | 1989 | Watkins: tabular Q-learning **(default)** | action-value table $Q$ | discrete | no |
| [`1990_dyna/`](1990_dyna/README.md) | 1990 | Sutton: Dyna-Q, Q-learning plus planning on a learned model | $Q$ and a sample model | discrete | yes, learned, to plan |
| [`1992_reinforce/`](1992_reinforce/README.md) | 1992 | Williams: REINFORCE policy gradient with a baseline | 5 policy parameters | discrete | no |
| [`1999_qlearning_continuous/`](1999_qlearning_continuous/README.md) | 1999 | Gaskett, Wettergreen, Zelinsky: wire-fitted neural-network Q-learning with advantage learning, **continuous force** | one small neural net producing 5 (action, value) wires | continuous | no |
| [`2005_nac/`](2005_nac/README.md) | 2005-08 | Peters, Vijayakumar, Schaal: natural actor-critic, LSTD-Q(λ) critic whose compatible weights are the natural gradient, **continuous force** | 6 policy parameters (linear Gaussian mean + σ) and a 21-weight linear critic | continuous | no |
| [`2007_cacla/`](2007_cacla/README.md) | 2007 | Van Hasselt, Wiering: CACLA, actor regressed toward the taken action only on a positive TD error, Gaussian exploration, **continuous force** | two small neural nets: state-value critic + deterministic actor | continuous | no |
| [`2011_nfqca/`](2011_nfqca/README.md) | 2011 | Hafner, Riedmiller: neural fitted Q iteration with continuous actions, batch regression with Rprop | actor + critic nets (PyTorch) | continuous | no |
| [`2011_pilco/`](2011_pilco/README.md) | 2011 | Deisenroth, Rasmussen: PILCO, Gaussian-process dynamics model, analytic moment matching, gradient-based policy search, **continuous force** | GP dynamics model (4 SE-ARD GPs) + 5-parameter squashed linear controller (PyTorch) | continuous | yes, a learned GP, to evaluate and optimize the policy by inference |
| [`2013_dqn/`](2013_dqn/README.md) | 2013 | Mnih et al.: deep Q-network, replay + target network | Q net (PyTorch) | discrete | no |
| [`2015_ddpg/`](2015_ddpg/README.md) | 2015 | Lillicrap et al.: deep deterministic policy gradient, **continuous force** | actor + critic nets with targets (PyTorch) | continuous | no |
| [`2015_trpo/`](2015_trpo/README.md) | 2015 | Schulman et al.: trust region policy optimization, natural gradient with a KL constraint | policy + value nets (PyTorch) | discrete | no |
| [`2017_ppo/`](2017_ppo/README.md) | 2017 | Schulman et al.: proximal policy optimization, clipped surrogate | policy + value nets (PyTorch) | discrete | no |
| [`2018_sac/`](2018_sac/README.md) | 2018 | Haarnoja et al.: soft actor-critic, maximum entropy, **continuous force** | actor + twin critics + temperature (PyTorch) | continuous | no |


# Results

Seed `[0, 5000]` training episodes with the pole started anywhere in ±12°, then the frozen policy run 20 times from each of five start angles. Mean steps survived, out of a possible 500:

| Solution | 0° | −8° | +8° | −11° | +11° | first episode at avg 500 | 5000-episode train time | episodes/s | steps/s | µs per step |
|---|---|---|---|---|---|---|---|---|---|---|
| [`1983_actor_critic/`](1983_actor_critic/README.md) | 500 | 500 | 500 | 500 | 492 | 1602 | 17.6 s | 294 | 123 k | 8.1 |
| [`1986_actor_critic_backprop/`](1986_actor_critic_backprop/README.md) | 500 | 500 | 500 | 500 | 500 | 1242 | 57.4 s | 88 | 37 k | 26.9 |
| [`1988_td/`](1988_td/README.md) | 486 | 457 | 467 | 479 | 447 | never (best 474) | 46.6 s | 108 | 33 k | 30.4 |
| [`1989_qlearning/`](1989_qlearning/README.md) | 492 | 500 | 500 | 495 | 487 | never (best 479) | 14.9 s | 346 | 54 k | 18.5 |
| [`1990_dyna/`](1990_dyna/README.md) | 495 | 488 | 307 | 425 | 257 | never (best 247) | 30.0 s | 170 | 25 k | 40.6 |
| [`1992_reinforce/`](1992_reinforce/README.md) | 500 | 500 | 500 | 500 | 500 | 1582 | 19.5 s | 262 | 109 k | 9.2 |
| [`1999_qlearning_continuous/`](1999_qlearning_continuous/README.md) | 500 | 500 | 500 | 500 | 500 | 3753 | 148 s † | 33.8 | 7.8 k | 128 |
| [`2005_nac/`](2005_nac/README.md) | 500 | 500 | 500 | 500 | 500 | 543 | 73 s † | 68.4 | 32.8 k | 30.5 |
| [`2007_cacla/`](2007_cacla/README.md) | 500 | 500 | 500 | 500 | 500 | 3642 | 43.2 s † | 116 | 34.2 k | 29.2 |
| [`2011_nfqca/`](2011_nfqca/README.md) | 500 | 500 | 500 | 500 | 491 | 2050 | 1595 s † | 3.1 | 1.2 k | 831 |
| [`2011_pilco/`](2011_pilco/README.md) | 500 | 500 | 500 | 500 | 500 | 102 | 76.6 s † | 65.2 | 32.6 k | 30.7 |
| [`2013_dqn/`](2013_dqn/README.md) | 500 | 500 | 500 | 500 | 500 | never (best 385) | 246 s † | 20.3 | 3.1 k | 320 |
| [`2015_ddpg/`](2015_ddpg/README.md) | 500 | 500 | 500 | 500 | 500 | never (best 476) | 618 s † | 8.1 | 1.6 k | 645 |
| [`2015_trpo/`](2015_trpo/README.md) | 500 | 500 | 500 | 500 | 500 | 2530 | 182 s † | 27.5 | 12.2 k | 82 |
| [`2017_ppo/`](2017_ppo/README.md) | 500 | 500 | 500 | 500 | 500 | 512 | 363 s † | 13.8 | 6.4 k | 156 |
| [`2018_sac/`](2018_sac/README.md) | 500 | 500 | 500 | 500 | 500 | 351 | 4290 s † | 1.2 | 0.5 k | 1941 |
| random baseline (tests)| ~22 | | | | | | | | | |

† The 1999 and 2005-2018 rows were timed on a different machine from the first six (an M3 Pro, one core, PyTorch on the CPU for 2011-2018), so their wall-clock figures are indicative only; the steps-per-second and per-step figures are comparable in proportion, not in absolute value. The 2005, 2007 and 2011 PILCO rows were also timed while other jobs shared the machine.

PILCO's row hides the number that matters for it. Its 100-episode average reached 500 at episode 102 only because the first two trials failed and the window is 100 wide: the policy fitted after trial 2, to a Gaussian-process model of 8 transitions (0.8 s of experience), already ran the full 500 steps, and so did every trial after it. Learning stopped after 15 trials (131 s of experience), and the remaining 4985 episodes only exercised the fixed controller. No model-free method in the table is within two orders of magnitude of that data efficiency; see its [README](2011_pilco/README.md).

# Complexity

Two different questions hide under "how complex is this solution": how much code you have to read and tune, and how much mathematics you have to understand to trust it. They are measured differently and they do not agree, which is the interesting part.

## Implementation complexity

`complexity.py` measures the code. Run `python complexity.py` to regenerate the table (`--json` for machine-readable output).

The solutions which appeared from 1983 to 2007 do not involve any deep learning architectures in the modern sense: no GPU, and only shallow networks written by hand in numpy (the 1986, 1999 and 2007 solutions each train networks with a single hidden layer). The other early solutions are linear units over fixed features (1983, 1992, 2005) or plain tables (1988, 1989, 1990); the largest learned object among them is a 4608-entry table. From 2011 on the solutions need automatic differentiation and use PyTorch on the CPU: the deep-RL methods with small two-hidden-layer networks of 32 to 64 units, because that is all this four-dimensional problem needs, and PILCO, whose Gaussian-process model and moment-matching rollout are differentiated by autograd rather than by hand.

| Solution | Own SLOC | Branches | Shared SLOC | Total SLOC | Network architecture | Learned params | Hyperparams | Library |
|---|---|---|---|---|---|---|---|---|
| [`1983_actor_critic/`](1983_actor_critic/README.md) | 57 | 12 | 205 | 262 | - | 324 | 6 | numpy |
| [`1986_actor_critic_backprop/`](1986_actor_critic_backprop/README.md) | 93 | 4 | 205 | 298 | MLP (tanh): critic/actor 4 × 16 × 1 | 194 | 6 | numpy |
| [`1988_td/`](1988_td/README.md) | 50 | 8 | 205 | 255 | - | 4,609 | 6 | numpy |
| [`1989_qlearning/`](1989_qlearning/README.md) | 59 | 8 | 205 | 264 | - | 257 | 5 | numpy |
| [`1990_dyna/`](1990_dyna/README.md) | 68 | 10 | 205 | 273 | - | 257 | 6 | numpy |
| [`1992_reinforce/`](1992_reinforce/README.md) | 53 | 7 | 205 | 258 | - | 6 | 3 | numpy |
| [`1999_qlearning_continuous/`](1999_qlearning_continuous/README.md) | 157 | 12 | 205 | 362 | MLP (tanh): net 4 × 32 × 10 | 491 | 14 | numpy |
| [`2005_nac/`](2005_nac/README.md) | 102 | 11 | 205 | 307 | - | 27 | 11 | numpy |
| [`2007_cacla/`](2007_cacla/README.md) | 116 | 10 | 205 | 321 | MLP (tanh): critic/actor 4 × 64 × 1 | 772 | 12 | numpy |
| [`2011_nfqca/`](2011_nfqca/README.md) | 66 | 8 | 281 | 347 | MLP (tanh): actor 4 × 32 × 32 × 1, critic 5 × 32 × 32 × 1 | 2,530 | 10 | PyTorch |
| [`2011_pilco/`](2011_pilco/README.md) | 220 | 19 | 281 | 501 | GP dynamics model + 5-parameter linear controller | 33 | 9 | PyTorch |
| [`2013_dqn/`](2013_dqn/README.md) | 61 | 6 | 281 | 342 | MLP (relu): q (+ target) 4 × 128 × 128 × 2 | 34,820 | 9 | PyTorch |
| [`2015_ddpg/`](2015_ddpg/README.md) | 73 | 4 | 281 | 354 | MLP (relu): actor (+ target) 4 × 64 × 64 × 1, critic (+ target) 5 × 64 × 64 × 1 | 18,308 | 13 | PyTorch |
| [`2015_trpo/`](2015_trpo/README.md) | 153 | 15 | 281 | 434 | MLP (tanh): pi 4 × 64 × 64 × 2, vf 4 × 64 × 64 × 1 | 9,155 | 11 | PyTorch |
| [`2017_ppo/`](2017_ppo/README.md) | 119 | 9 | 281 | 400 | MLP (tanh): pi 4 × 64 × 64 × 2, vf 4 × 64 × 64 × 1 | 9,155 | 11 | PyTorch |
| [`2018_sac/`](2018_sac/README.md) | 100 | 3 | 281 | 381 | MLP (relu): actor 4 × 64 × 64 × 2, q1/q2 (+ target) 5 × 64 × 64 × 1 | 23,047 | 10 | PyTorch |

Column definitions:

- **own SLOC**: source lines in the solution's `soln.py`, excluding blank lines, comments and docstrings. Raw line counts would mislead here because every `soln.py` opens with a long docstring.
- **branches**: a cyclomatic-style count of decision points in `soln.py` (one plus every `if`, loop, ternary, boolean operator, exception handler and comprehension).
- **shared SLOC**: source lines of the `common/` modules the solution depends on. Every solution uses `env.py`, `agent.py` and `features.py`; the PyTorch solutions also use `deep.py`.
- **network architecture**: the neural networks the agent trains, read off the constructed agent as layer widths, input × hidden × ... × output. Every network here is a fully connected multilayer perceptron (MLP) with the activation in parentheses; "(+ target)" marks a slowly updated copy with the same shape. "-" means no neural network: a table or a linear unit on fixed features. PILCO is the one solution that uses PyTorch without a network, for automatic differentiation through its Gaussian process, so its cell names what it does learn instead.
- **learned params**: total size of the arrays the agent saves, at default settings. For the tabular methods this is the table; for the networks it includes target copies. PILCO's 33 are its controller and GP hyperparameters as measured on a fresh agent; a trained model also saves the GP's 200 stored transitions, which are its data, not parameters.
- **hyperparams**: number of constructor arguments exposed through `hparams()`, a proxy for tuning burden.

Three caveats on reading it:

- **SLOC understates the framework solutions.** DQN is about sixty lines because autograd, Adam and the tensor library do the differentiation and optimization. The 1986 agent is longer partly because it writes its own backpropagation. The number measures what you have to read, not what runs.
- **Branch count tracks algorithmic bookkeeping, not difficulty.** TRPO's branches come from conjugate gradient and the backtracking line search; SAC's straight-line update has almost none. Yet SAC's equations are the harder ones to derive.
- **Hyperparameter count correlates with the tuning stories in the READMEs.** The two solutions that needed sweeps to work at all, 1999 and DQN, are among the most heavily parameterized.
- **PILCO is the longest solution and the smallest policy.** Its 220 lines are the Gaussian-process posterior and the closed-form moment matching, written out because no library does them; the controller they optimize has five numbers in it.

For a standard toolchain, `radon` gives cyclomatic complexity and a maintainability index per function and `cloc` gives language-aware line counts; `complexity.py` exists so that the numbers here are reproducible without either.

## Mathematical complexity

There is no accepted scalar for this. The rubric below scores each solution on five dimensions that determine how hard the method is to derive, analyse and trust. Each is an ordinal judgement, maintained by hand.

1. **Derivative order.** The highest derivative the update needs. Zero for tables and for the 1983 BOXES elements, whose "gradient" is the one-hot input. First for every gradient method, including NAC, which never differentiates the Fisher matrix because the compatible critic hands it the natural gradient directly. Second for TRPO alone, whose Fisher-vector products differentiate the gradient of the KL divergence.
2. **Coupled learning problems.** How many estimates are fit simultaneously and depend on one another. One for Q-learning, TD(λ) and REINFORCE. Two for the actor-critics and for TRPO and PPO (policy and value). Three for DQN and Dyna, counting the target network or the learned model as a separate estimation problem. Four for SAC: actor, two critics and the temperature, all coupled through the soft Bellman target.
3. **Convergence theory.** Whether the update is known to converge to what it estimates. Tabular Q-learning and TD(λ) have proofs (Watkins and Dayan 1992; Sutton 1988, Tsitsiklis and Van Roy 1997 for linear on-policy). Function approximation with bootstrapping does not, off-policy least of all (the "deadly triad"). TRPO's monotonic-improvement bound is the one guarantee on the policy side.
4. **Inner optimization.** What has to be solved to act or to update. Nothing for a lookup or an argmax over two actions. A closed-form argmax over a continuum for wire fitting. A learned maximizer, the actor, for NFQCA, DDPG and SAC. An iterative solve, conjugate gradient plus a line search under a constraint, for TRPO.
5. **Objective structure.** How many derivation steps stand between the textbook objective and the loss in the code. A squared TD error is the baseline. Wire fitting's hand-written interpolator gradients, PPO's clipped surrogate, TRPO's constrained problem, and SAC's entropy-regularized objective with a reparameterized expectation and the tanh change-of-variables Jacobian each add one or more.

| Solution | Derivative order | Coupled problems | Convergence theory | Inner optimization | Objective structure | Overall |
|---|---|---|---|---|---|---|
| [`1983_actor_critic/`](1983_actor_critic/README.md) | 0 | 2 | none for the pair | none | TD error with traces | low |
| [`1986_actor_critic_backprop/`](1986_actor_critic_backprop/README.md) | 1 | 2 | none | none | TD error with traces, hand-written backprop | low-mid |
| [`1988_td/`](1988_td/README.md) | 0 | 1 | yes (tabular) | one-step lookahead with the true model | TD error with traces | low |
| [`1989_qlearning/`](1989_qlearning/README.md) | 0 | 1 | yes (tabular) | argmax over 2 actions | TD error | low |
| [`1990_dyna/`](1990_dyna/README.md) | 0 | 3 (Q, model, planner) | yes for the Q part | argmax over 2 actions | TD error, sampled model | low |
| [`1992_reinforce/`](1992_reinforce/README.md) | 1 | 1 | unbiased gradient; no rate | none | Monte Carlo score function with baseline | low-mid |
| [`1999_qlearning_continuous/`](1999_qlearning_continuous/README.md) | 1 | 1 | none | closed-form argmax over a continuum | wire-fitting gradients, advantage target | mid-high |
| [`2005_nac/`](2005_nac/README.md) | 1 | 2 (policy, joint LSTD critic [v; w]) | natural gradient equals the compatible-critic weights (exact for β = 0, λ = 1); local convergence as for gradient ascent; biased basis for λ < 1 | linear solve of the 21 × 21 LSTD system plus an angle test | Bellman equation split into advantage + value, compatible features, Fisher = all-action matrix, natural gradient | mid-high |
| [`2007_cacla/`](2007_cacla/README.md) | 1 | 2 | none | none | TD error with traces; sign-gated regression of the actor toward the taken action | low-mid |
| [`2011_nfqca/`](2011_nfqca/README.md) | 1 | 2 | none (fitted iteration is stable per fit) | learned maximizer | squared TD error, batch fit | mid |
| [`2011_pilco/`](2011_pilco/README.md) | 1 | 2 (GP model, policy) | none (local optimum of an approximate objective) | L-BFGS on the moment-matched expected cost, nested inside marginal-likelihood fitting | GP posterior, closed-form moment matching through kernel and squashing, expected saturating cost, chain rule over the horizon | high |
| [`2013_dqn/`](2013_dqn/README.md) | 1 | 3 (online, target, replay) | none | argmax over 2 actions | Huber TD error | low-mid |
| [`2015_ddpg/`](2015_ddpg/README.md) | 1 | 2 (+ targets) | none | learned maximizer | deterministic policy gradient through the critic | mid |
| [`2015_trpo/`](2015_trpo/README.md) | 2 | 2 | monotonic-improvement bound | conjugate gradient + line search under a KL constraint | constrained surrogate, natural gradient, GAE | high |
| [`2017_ppo/`](2017_ppo/README.md) | 1 | 2 | none (heuristic trust region) | none | clipped surrogate, GAE | mid |
| [`2018_sac/`](2018_sac/README.md) | 1 | 4 | none | learned maximizer | entropy-regularized soft Bellman, reparameterization, tanh Jacobian, temperature dual | high |

Read against the implementation table, the two measures disagree in instructive ways. TRPO and PILCO are the two longest solutions and the two most mathematically demanding, so both agree there; PILCO gets there with the fewest learned parameters of any solution but REINFORCE, because its complexity is in the inference, not the model. NAC is the other way round: a short numpy file whose 21-by-21 linear solve rests on the compatible-function-approximation argument that TRPO later builds on. SAC has the fewest branches of any solution and the second-highest mathematical load. DQN has the most learned parameters and one of the simplest derivations. The 1999 agent is the longest numpy solution because it does by hand what the framework solutions get for free, and its derivation load is high for the same reason. The tabular methods are cheap on every axis, which is why they are the right place to start.


Train times are wall-clock for `python main.py --mode train --soln <name> --no-render` on one CPU core at 98-99% utilization, so they are also CPU time. Episodes per second is tqdm's overall rate for the same run. Both depend on how long episodes last as well as on per-step cost: a method that balances early runs 500-step episodes for most of training, so the fastest learners by wall clock are not the cheapest per step. The last two columns correct for that. Steps per second is the run's total environment steps (mean episode reward × 5000) divided by wall time, and microseconds per step is its reciprocal. By that measure the 1983 agent and REINFORCE are cheapest, at under 10 µs per step, because each step is a handful of Python operations on tiny arrays (REINFORCE only records the step and updates once per episode). Q-learning pays about twice that for several small numpy calls per step. The 1986 networks (two forward and two backward passes), the 1988 lookahead (two extra dynamics evaluations) and Dyna (five planning updates) are the most expensive. At this scale interpreter overhead dominates arithmetic, so these numbers reflect Python call counts far more than floating-point work.

Hyperparameters were tuned lightly, on seed 0 only, to make each method demonstrably work; the table is not a fair benchmark of the methods against each other. Each directory's README notes where its settings depart from the original paper and why.

## Requirements

- Python 3.10+
- `numpy`, `matplotlib`, `tqdm`; `pytest` to run the tests
- `torch` (PyTorch, CPU build is enough) for the 2011 to 2018 solutions; optional, everything else runs without it

```sh
pip install numpy matplotlib tqdm pytest
pip install torch          # only for the 2011-2018 solutions
```

## Quick start

Train a policy. Each training episode starts with the pole at a random angle anywhere in the full ±12° range, so the agent learns to recover from large tilts, not just to hold the pole near vertical. The best checkpoint seen during training is saved to `cartpole_<soln>.npz`.

The training runs can be executed in headless mode without the visualization when the `--no-render` flag is set  (which is faster if it is desirable to go straight to the learned model policy).

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

## Visualizations

The visualization window displays three panels/subplots for both training and inference runs:

- **Top left:** the cart and pole on a track. Red dashed lines mark the position limit where the episode terminates. A text readout shows the episode, step, the solution's diagnostics and the four state variables.
- **Bottom left:** the learning curve. The grey line is the total reward collected in each episode and the blue line is its moving average over the last 100 episodes.

  CartPole pays a reward of exactly +1 for every step the pole stays within 12° and the cart stays on the track, so an episode's total reward is simply the number of steps it survived. A value of 500 means the episode hit the time limit while still balanced, which is the best possible outcome.

  A note on words. The per-step +1 is the *reward*. The sum of rewards over an episode is what reinforcement-learning texts call the *return*, and the formulation in the 1989 README uses that term because the equations do. The plots and console output say "total reward" instead, since to a programmer "return" reads as a function returning.

- **Right, full height:** a phase portrait of the pole angle θ on the horizontal axis and angular velocity θ̇ on the vertical, traced step by step for each rendered episode. The cart-pole system plus the policy form a closed-loop dynamical system, and this is its state-space picture. A good policy spirals in toward the origin (upright, at rest) and then chatters in a small cycle around it, which is what bang-bang control does. A failing episode spirals out through one of the red ±12° lines. The orange dot is the current state; earlier episodes fade so that a multi-episode inference run accumulates into one picture. Different solutions have visibly different portraits: the 1983 BOXES policy, with only six angle regions, rocks the pole in a wide cycle of about ±8°, while finer-grained policies hold a much tighter one.

During training the per-episode total reward is noisy because every episode starts from a different angle and exploration is still on. The moving average is the signal to watch.

## Options

| Flag | Default | Description |
|---|---|---|
| `--mode {train,infer}` | `train` | `train` learns and saves a policy. `infer` loads a saved policy and runs it deterministically. |
| `--soln NAME` | `1989_qlearning` | Which solution directory's `soln.py` to use. See the lineage table. |
| `--agent {soln,qlearning,random}` | `soln` | `soln` uses `--soln`. `qlearning` is a backward-compatible alias that forces `--soln 1989_qlearning`. `random` is the uniform baseline and does not learn. |
| `--model PATH` | `cartpole_<soln>.npz` | Where to save (train) or load (infer) the learned parameters. |
| `--hparam KEY=VALUE` | none | Train only, repeatable. Override a constructor argument of the selected solution's agent, e.g. `--hparam hidden=64`. Values are parsed as Python literals and saved with the model, so inference needs no repeat. |
| `--episodes N` | 5000 train / 10 infer | Number of episodes to run. |
| `--render-every N` | 100 train / 1 infer | Animate every Nth episode. Lower is slower but shows more. |
| `--theta-limit DEGREES` | 12 | Absolute pole angle at which an episode terminates, in both modes. Above 12 only for the solutions that read the raw state (1986, 1992, 1999 and later, except DQN); the BOXES decoder and the grids are built for 12 and the driver refuses. See [Wider angles](#wider-angles). |
| `--theta-range DEGREES` | = `--theta-limit` | Train only. Each episode starts with the pole at a uniform random angle in ±DEGREES. Valid range 0 to `--theta-limit` inclusive. Use about 3 to mimic Gymnasium's narrow start. |
| `--fps F` | 50 | Animation speed in frames per second. |
| `--no-render` | off | Run headless. Useful for fast training. |
| `--seed N` | 0 | Random seed for the environment, agent and start states. |
| `--x0 METERS` | random | Infer only. Initial cart position. See [Initial state](#initial-state). |
| `--theta0 DEGREES` | random | Infer only. Initial pole angle; must be strictly inside ±`--theta-limit`. See [Initial state](#initial-state). |

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
| Valid range | `-2.4 < x0 < 2.4` (exclusive) | `-12 < theta0 < 12` (exclusive; ±`--theta-limit` if widened) |
| Zero means | Center of the track | Pole perfectly upright |
| Sign | Negative = left, positive = right | Negative = tilted left, positive = tilted right |
| Default | Uniform random in `[-0.05, 0.05]` m | Uniform random in `[-0.05, 0.05]` rad (about ±2.9°) |

The limits are the same thresholds that end an episode: the cart leaving the ±2.4 m track or the pole passing ±12° from upright. Values at or beyond them are rejected by the script, since the episode would terminate on the first step. Initial cart velocity and pole angular velocity are always random in `[-0.05, 0.05]` and cannot be set from the command line. The physical meaning of these limits is derived in [the 1989 README](#why-these-ranges).

### Wider angles

`--theta-limit` raises the failure angle above the standard 12°. It applies to both modes: training episodes then start anywhere in ±`--theta-range`, which defaults to the new limit, and `--theta0` may be set anywhere inside it. Only solutions that read the raw scaled state accept it: `1986_actor_critic_backprop`, `1992_reinforce`, `1999_qlearning_continuous`, and every later solution except DQN (2005, 2007, both 2011, DDPG, TRPO, PPO, SAC). The 1983 BOXES decoder marks any angle past 12° as failed and the 1988, 1989, 1990 and 2013 grids clip there, so the driver refuses values above 12 for those.

The useful range is bounded by the track, not the motor. The push out-accelerates gravity up to about 43°, but recovering from a wide angle means a long hard push, and the cart runs out of its ±2.4 m before the pole is upright. A hand-tuned bang-bang linear controller (see [`../oc/`](../oc/README.md)) recovers from at most about 34° starting at rest in the center, 37° with 1.5 m of track behind it, and 22° with 1.5 m in front. In a short experiment training on ±40° starts, REINFORCE recovered from 20° every time and from 30° three times in ten, failing by running out of track; the 1986 networks recovered from 20° most of the time; the 1999 agent did not learn with its 12° defaults but does with `--episodes 8000 --hparam hidden=64 --hparam advantage_k=0.3 --hparam lr=0.005`, recovering from 25° at the 500-step cap on three of four seeds (see its [README](1999_qlearning_continuous/README.md#wider-angles)). Beyond about 43° no push can recover the pole and the task becomes swing-up, which needs a different reward.

```sh
python main.py --mode train --soln 1992_reinforce --no-render --theta-limit 30
python main.py --mode infer --soln 1992_reinforce --theta-limit 30 --theta0 25
```

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
