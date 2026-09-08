# 2005: Natural Actor-Critic (Peters, Vijayakumar and Schaal)

**Lineage:** [1983 actor-critic](../1983_actor_critic/README.md) → [1986 backprop actor-critic](../1986_actor_critic_backprop/README.md) → [1988 TD(λ)](../1988_td/README.md) → [1989 Q-learning](../1989_qlearning/README.md) → [1990 Dyna](../1990_dyna/README.md) → [1992 REINFORCE](../1992_reinforce/README.md) → [1999 continuous Q-learning](../1999_qlearning_continuous/README.md) → **2005 NAC** → [2007 CACLA](../2007_cacla/README.md) → [2011 NFQCA](../2011_nfqca/README.md) → [2011 PILCO](../2011_pilco/README.md) → [2013 DQN](../2013_dqn/README.md) → [2015 DDPG](../2015_ddpg/README.md) → [2015 TRPO](../2015_trpo/README.md) → [2017 PPO](../2017_ppo/README.md) → [2018 SAC](../2018_sac/README.md)

**Previous:** [1999, wire-fitted Q-learning with a continuous force](../1999_qlearning_continuous/README.md)

**Next:** [2007, CACLA: a continuous actor-critic that updates the actor only on positive TD errors](../2007_cacla/README.md)

## References

- J. Peters, S. Vijayakumar and S. Schaal, ["Natural Actor-Critic"](https://homepages.inf.ed.ac.uk/svijayak/publications/peters-ECML2005.pdf), *Proc. 16th European Conference on Machine Learning* (ECML 2005), LNAI 3720, pp. 280-291. The conference version: Table 1 is the LSTD-Q(λ) algorithm implemented here, Table 2 the episodic variant.
- J. Peters and S. Schaal, ["Natural Actor-Critic"](https://doi.org/10.1016/j.neucom.2007.11.026), *Neurocomputing* 71(7-9):1180-1190, 2008. The journal version, with the same two algorithms, the proof that the all-action matrix is the Fisher information, and the fuller experimental section (cart-pole, motor primitives, a baseball swing on a seven-DOF arm).
- S. Amari, "Natural Gradient Works Efficiently in Learning", *Neural Computation* 10:251-276, 1998. Steepest ascent under the Fisher metric.
- S. Kakade, "A Natural Policy Gradient", *NIPS* 2001. First use of the natural gradient for policies; the "average Fisher matrix" that Peters and Schaal show is the true Fisher matrix.
- R. S. Sutton, D. McAllester, S. Singh and Y. Mansour, "Policy Gradient Methods for Reinforcement Learning with Function Approximation", *NIPS* 2000. The policy gradient theorem and compatible function approximation; V. Konda and J. Tsitsiklis, "Actor-Critic Algorithms", *NIPS* 2000, proved the same compatibility condition independently.
- J. Boyan, "Least-Squares Temporal Difference Learning", *ICML* 1999 (journal version *Machine Learning* 49, 2002). LSTD(λ), which the critic adapts.

## What changed

**From REINFORCE (1992).** REINFORCE follows the plain gradient of the return, estimated from whole episodes, and its README records the narrow band of step sizes that works. Two things are wrong with the plain gradient that have nothing to do with its variance. It depends on how the policy happens to be parameterized: the same policy written as $\mathcal N(u \mid k^\top s, \sigma^2)$ or in its information form gets a different update. And it is small exactly where the return landscape is flat, so it crawls across plateaus and races down steep directions that are often the exploration parameters, collapsing $\sigma$ before the mean has been found (the paper's Fig. 1 shows this on a one-dimensional LQR). Amari's natural gradient $\tilde\nabla J = G^{-1}\nabla J$, with $G$ the Fisher information of the policy, fixes both: it is the steepest ascent direction when distance is measured between policies rather than between parameter vectors, and it is covariant under reparameterization (Theorem 1 of the paper). Kakade (2001) had brought it to RL but had to estimate $G$ and invert it. This paper's result is that a critic of the right form yields the natural gradient with no Fisher matrix at all.

**From the actor-critics (1983, 1986).** Those learn a critic $V(s)$ by TD and push the actor along the TD error times the score function, a noisy sample of the plain gradient with a hand-picked learning rate on each side. NAC keeps the two-part architecture and changes both halves. The critic is not stepped, it is solved: LSTD accumulates second-order statistics and inverts them, so it has no learning rate and uses every sample it has seen. And the critic's parameters are not just a baseline; part of them *are* the update direction, so the actor's only free parameter is the length of the step. The paper shows in passing that the 1983 actor-critic with a Gibbs policy and a tabular value function is itself a special case: its advantage estimate is the natural gradient, which is why the old algorithm worked as well as it did.

**Forward to TRPO (2015).** [TRPO](../2015_trpo/README.md) takes exactly the natural-gradient direction and adds what NAC leaves open: a rule for the step length, a KL trust region enforced by a line search, and conjugate gradient so the direction can be computed for a network with thousands of parameters without forming $G$. NAC's LSTD critic solves a dense $(N + M)\times(N + M)$ system, which is the right tool for the six-parameter policy here and the wrong one for a deep network.

## The method

Discounted MDP with a stochastic policy $\pi_\theta(u \mid s)$, state-value basis $\phi(s)$ and objective $J(\theta) = \mathbb E\big[\sum_t \gamma^t r_t\big]$. The policy gradient theorem with a baseline $b(s)$ is

$$
\nabla_\theta J = \int d^\pi(s) \int \pi_\theta(u \mid s)\, \nabla_\theta \log \pi_\theta(u \mid s)\, \big(Q^\pi(s,u) - b(s)\big)\, du\, ds ,
$$

and Sutton et al. (2000) showed that $Q^\pi - b$ may be replaced by the *compatible* function approximation $f_w(s,u) = \nabla_\theta \log \pi_\theta(u \mid s)^\top w$ without biasing the gradient. Substituting it gives

$$
\nabla_\theta J = \Big[\int d^\pi(s) \int \pi_\theta(u \mid s)\, \nabla_\theta \log \pi_\theta\, \nabla_\theta \log \pi_\theta^\top\, du\, ds\Big]\, w = F_\theta\, w ,
$$

and Appendix A of the paper proves that the all-action matrix $F_\theta$ is the Fisher information $G(\theta)$. Hence (their Eq. 5)

$$
\tilde\nabla_\theta J = G^{-1} \nabla_\theta J = G^{-1} F_\theta\, w = w .
$$

**The compatible weights are the natural gradient.** The whole problem is to estimate $w$.

Since $f_w$ is mean-zero over actions, it is an advantage function $A^\pi(s,u) = Q^\pi(s,u) - V^\pi(s)$, and an advantage cannot be learned by TD bootstrapping on its own: the value it would bootstrap from has been subtracted out. The paper's fix is to write the Bellman equation for $Q$ in terms of the advantage and the state value, $Q^\pi(s,u) = A^\pi(s,u) + V^\pi(s) = r + \gamma\, \mathbb E[V^\pi(s')]$, give $V$ its own linear basis $V^\pi(s) \approx \phi(s)^\top v$, and read it as one set of linear equations in the joint unknown $[v;\ w]$:

$$
\phi(s_t)^\top v + \nabla_\theta \log \pi_\theta(u_t \mid s_t)^\top w \;=\; r_t + \gamma\, \phi(s_{t+1})^\top v + \epsilon_t .
$$

These are solved by LSTD-Q(λ) (Table 1 of the paper). With the stacked bases

$$
\hat\phi_t = \begin{bmatrix} \phi(s_t) \\ \nabla_\theta \log \pi_\theta(u_t \mid s_t) \end{bmatrix}, \qquad
\tilde\phi_t = \begin{bmatrix} \phi(s_{t+1}) \\ 0 \end{bmatrix},
$$

every step updates the sufficient statistics

$$
z_{t+1} = \lambda z_t + \hat\phi_t, \qquad
A_{t+1} = A_t + z_{t+1}\big(\hat\phi_t - \gamma\, \tilde\phi_t\big)^\top, \qquad
b_{t+1} = b_t + z_{t+1}\, r_t ,
$$

and the critic is $[v;\ w] = A^{-1} b$. The zero block in $\tilde\phi_t$ is the point of the "Q" in LSTD-Q(λ): the next action has not been drawn, so the regression inputs carry no noise from $u_{t+1}$. On a failure step the whole of $\tilde\phi_t$ is zero, which encodes $V(\text{terminal}) = 0$ and is the only failure signal the +1-per-step reward provides.

The actor moves when the direction has stopped changing. The paper's criterion is the angle between the current estimate and one from $\tau$ steps earlier:

$$
\angle(w_{t+1}, w_{t-\tau}) \le \varepsilon \quad\Longrightarrow\quad \theta \leftarrow \theta + \alpha\, w_{t+1}, \qquad z \leftarrow \beta z,\ A \leftarrow \beta A,\ b \leftarrow \beta b .
$$

The forgetting factor $\beta \in [0, 1]$ decides how much of the old policy's statistics the critic keeps after the policy changes: $\beta = 0$ resets it completely, which is the setting under which convergence to the true natural gradient is guaranteed; $\beta$ near 1 reuses stale but plentiful data.

**Policy.** The paper's cart-pole policy: a Gaussian whose mean is linear in the state, $\pi_\theta(u \mid s) = \mathcal N\big(u \mid k^\top \varphi(s),\ \sigma^2\big)$ with $\sigma = 1/(1 + e^{-\xi})$ and $\theta = [k;\ \xi]$. Here $\varphi(s) = (x/2.4,\ \dot x/3,\ \theta/0.21,\ \dot\theta/3.5,\ 1)$, the same five features as REINFORCE, so the policy has six parameters. With $e = (u - k^\top \varphi)/\sigma$ the score function is

$$
\nabla_k \log \pi = \frac{e}{\sigma}\, \varphi(s), \qquad
\frac{\partial \log \pi}{\partial \xi} = (e^2 - 1)(1 - \sigma) .
$$

The applied force is the sample clipped to $[-1, 1]$ (times 10 N); the score is evaluated at the unclipped sample, so the clip is part of the environment as far as the gradient is concerned. Frozen, the agent applies the mean.

**Value basis.** $\phi(s)$ is the constant, the four normalized state variables and their ten distinct products, 15 features, so $A$ is 21 × 21. A quadratic is the natural first guess for a value function around an equilibrium, and it is what LQR would give for the paper's quadratic-cost version of the task.

**The paper's cart-pole.** Section 4.1 of the paper uses a heavier pole ($l = 0.75$ m, $m = 0.15$ kg, $m_c = 1$ kg) sampled at 60 Hz with a quadratic reward $r = x^\top Q x + u^\top R u$, $Q = \mathrm{diag}(1.25, 1, 12, 0.25)$, $R = 0.01$, and the linear Gaussian policy above. It compares the episodic NAC against GPOMDP (a vanilla policy gradient) and against Kakade's projected natural gradient, and eNAC reaches the optimum in a small fraction of the episodes either of the others needs (their Fig. 2, 1.b). The cart-pole system, reward and termination here are the repository's Gymnasium-compatible task instead, so the numbers are not comparable, but the policy class is the paper's.

## Implementation notes and deviations

- Pure numpy, model-free, `continuous_actions = True`; the environment runs in continuous mode with the same cart-pole system, reward, thresholds and start distribution as every other solution. The agent reads the raw scaled state, so it accepts `--theta-limit` above 12° (see [Wider angles](../README.md#wider-angles)).
- **The critic is solved once per episode, not once per step**, and the angle test compares consecutive per-episode solutions ($\tau$ = one episode). Per step, the statistics update costs one 21-vector outer product; the 21 × 21 solve is cheap too, but a per-step angle test on a task whose episodes run from five to five hundred steps would be checking convergence at wildly different amounts of data. With $\varepsilon = 0.35$ rad (20°) and enough data the criterion fires on most episodes: in the seed-0 training run below the actor took 2,465 steps by the angle test and one forced step, about one step every two episodes.
- **Two guards the paper does not have.** A step is forced after `update_every` = 10 episodes even if the direction has not settled, so the actor cannot stall; and no step is taken while the forgetting-weighted sample count behind $A$ and $b$ is below `min_steps` = 100. The second guard came from a sweep: with a policy step forced every 2 episodes, one seed in twelve took a single ~3.4-norm step from a 21-parameter regression on about ten transitions ($\mathrm{cond}\,A \approx 10^9$) early in training, saturated the policy at ±10 N and never recovered. Refusing to trust a regression with fewer rows than columns fixed every such case.
- A ridge of $10^{-3}$ is added to the diagonal of $A$ before the solve. $A$ is not symmetric, so this is a conditioning device, not a Bayesian prior.
- **Reward scaling.** Rewards are multiplied by 0.01 so $V$ lies in $[0, 1]$ and $v$, $w$ and $\alpha$ are $O(1)$ numbers. Because $[v; w] = A^{-1} b$ is linear in the reward, this is exactly equivalent to using $\alpha = 0.01$ on the raw reward; unlike the TD critics of 1986 and 1999, nothing else depends on the scale. What the +1-per-step reward does change is where the signal lives: $V(s) \approx 1$ for every state more than ~200 steps from failure, so the advantage is nonzero only near the edges of the recoverable region, and the terminal step's zero next-state basis is the entire failure signal. No failure penalty and no value initialization trick were needed.
- $\sigma = \mathrm{sigmoid}(\xi)$ as in the paper, floored at `sigma_min` = 0.05 so the Fisher metric, which grows as $1/\sigma^2$, stays finite. In practice $\xi$ hardly moves: $\sigma$ went from 0.40 to 0.37 in 5,000 episodes. The natural gradient step on $\xi$ is $F_{\xi\xi}^{-1}\, \partial J/\partial\xi$, and with the exploration noise already far below the ±1 force range the advantage carries little information about $\sigma$ on this task. The frozen policy applies the mean, so the residual noise costs nothing at inference.
- **Defaults**: $\alpha = 1.0$, $\gamma = 0.99$, $\lambda = 0.5$, $\beta = 0.5$, $\varepsilon = 0.35$, `update_every` 10, `min_steps` 100, ridge $10^{-3}$, reward scale 0.01, $\sigma_0 = 0.4$, $\sigma_{\min} = 0.05$. What the sweeps found is tabulated under "Tuning with `hparam_sweep.py`" below: the defaults are the only setting that reaches the cap on all four seeds without giving up speed; $\alpha = 0.5$ and $\gamma = 0.98$ also reach it on all four but later, $\alpha = 2$, $\lambda = 0.9$ and $\beta = 0.7$ each lose seeds, and $\beta = 0$, the complete reset under which the paper's convergence statement holds, is fragile here because the critic restarts from nothing after every policy step and with `min_steps` it then has to wait for data every time.
- **Episodic NAC is not implemented.** eNAC (Table 2 of the paper) sums the Bellman equation along a roll-out so that each episode gives one regression row, $\sum_t \gamma^t \nabla_\theta \log \pi_\theta(u_t \mid s_t)^\top w + J = \sum_t \gamma^t r_t$, and needs only a scalar baseline $J$ instead of a basis for $V$; the paper's own experiments use it because it removes the basis functions' influence on the gradient. The LSTD-Q(λ) version is implemented here because it is the algorithm the paper derives, because a state-dependent baseline is what this lineage's 1983 and 1986 critics already provide, and because it updates from every step rather than once per episode, which matters when early episodes are ten steps long.
- `learn()` only accumulates $z$, $A$, $b$; the solve, the angle test and the actor step happen in `end_episode()`. `state_dict()` holds $\theta$ (6), $v$ (15) and $w$ (6); the statistics $A$, $b$, $z$ are rebuilt from experience and are not saved.

### Tuning with `hparam_sweep.py`

NAC has eleven hyperparameters and the paper fixes almost none of them for cart-pole, so the defaults above were chosen with [`../hparam_sweep.py`](../README.md#hyperparameter-sweeps), which trains every (configuration, seed) pair in its own process with the same loop as `main.py` and scores the frozen policy from chosen start angles. The process had three rounds. First, a schedule sweep: how often to force a policy step (`update_every` 2, 5, 10) and whether to gate it on the angle test alone. That round, run on twelve seeds because the failure it was looking for is rare, found the collapse described under "Two guards the paper does not have": one seed in twelve took a single enormous natural-gradient step from a regression with fewer rows than columns, and the `min_steps` guard came out of it. Second, one-factor-at-a-time sweeps around the defaults on four seeds and 1,500 episodes, which is enough for a working setting to reach the 500-step cap and cheap enough (about 25 s a job in numpy) that 28 jobs finish in about a minute. Third, the benchmark run in the Result section on seed 0 with the chosen defaults. Four seeds rather than two because NAC's failures are seed-dependent: a setting that reaches the cap on one seed and stalls at 250 on another is the typical outcome, not the exception.

```sh
python ../hparam_sweep.py --soln 2005_nac --episodes 1500 --seeds 0 1 2 3 --eval-angles 0 11 \
    --config "" --config "alpha=0.5" --config "alpha=2.0" --config "gamma=0.98" \
    --config "lam=0.9" --config "beta=0.7" --config "beta=0.0"
```

What the one-factor round showed (frozen policy from 0° and 11°, episode at which the 100-episode average first reached 500):

| setting | seeds at the cap from both angles | first episode at avg 500, seeds 0-3 |
|---|---|---|
| defaults | 4 of 4 | 543, 930, 781, 414 |
| $\alpha = 0.5$ | 4 of 4 | 1033, 823, 633, 611 (slower on every seed) |
| $\alpha = 2$ | 3 of 4 | 421, 280, never (best 279), 414 |
| $\gamma = 0.98$ | 4 of 4 | 742, 709, 1361, 938 (slower on every seed) |
| $\lambda = 0.9$ | 2 of 4 | never (263), 502, never (365), 501 |
| $\beta = 0.7$ | 3 of 4 | never (297), 804, 633, 395 |
| $\beta = 0$ | 2 of 4 | never (33), never (168), 1042, 485 |

The defaults are the only row that is both fast and reliable. The step size trades speed for one failed seed at $\alpha = 2$; longer traces ($\lambda = 0.9$) and slower forgetting ($\beta = 0.7$) each lose seeds by letting stale statistics from earlier policies into the critic; and $\beta = 0$, the full reset under which the paper's convergence argument holds, fails on two seeds because the critic restarts from nothing after every policy step and then waits for `min_steps` of data every time.

## Run

```sh
python ../main.py --mode train --soln 2005_nac --no-render
python ../main.py --mode infer --soln 2005_nac --theta0 -11
pytest ../tests -k nac
```

`../tests/test_2005_nac.py` runs the shared interface checks and tests the mathematics directly: the Gaussian score function against finite differences, the LSTD-Q(λ) statistics on hand-built transitions, a one-state problem where the compatible critic recovers the known advantage and $w$ equals $F^{-1} g$ computed from the same samples, and the actor step with forgetting.

## Result

Seed 0, 5000 training episodes with full-range starts, frozen policy, 20 episodes per start angle:

| start angle | 0° | −8° | +8° | −11° | +11° |
|---|---|---|---|---|---|
| mean steps (max 500) | 500 | 500 | 500 | 500 | 500 |

The 100-episode average first reached 500 at episode 543, earlier than any of the 1983-1999 solutions (the three tabular methods never reach it) and about three times sooner than REINFORCE with the same five mean features. Training took 73 s on one CPU core: 2.39 M environment steps at about 32,800 steps/s, or 30.5 µs per step. Nearly all of that per-step cost is the 21-element outer product that updates $A$; the linear solve runs once per episode. The learned policy is six numbers, $k \approx (0.29,\ 0.06,\ 0.86,\ 1.87,\ 0.00)$ on the normalized state and $\sigma = 0.375$, and once the average reached 500 it never fell below 490 in the remaining 4,450 episodes; after episode 1,000 only 0.15% of training episodes, run with the exploration noise on and starts anywhere in ±12°, ended before the cap.

## Limitations

- **The value basis shapes the gradient.** The paper says so itself: with $\lambda < 1$ the estimate of $w$ depends on how well $\phi(s)$ spans $V^\pi$, and only $\lambda = 1$ is guaranteed unbiased. A quadratic basis is enough for a linear policy on this task; a poor basis would bias the "natural gradient" in ways the angle test cannot detect, because a wrong direction can be a stable one.
- **The step length is still a hand-tuned constant.** The natural gradient fixes the direction, and it makes $\alpha$ far less sensitive than REINFORCE's, but nothing here bounds how far one step moves the policy. TRPO's contribution is precisely that bound.
- **LSTD does not scale to networks.** The statistics are $O((N+M)^2)$ per step and the solve is $O((N+M)^3)$, fine for 21 unknowns and hopeless for a 9,000-parameter network; that is why TRPO reaches the same direction through conjugate gradient and Fisher-vector products instead.
- **On-policy with a forgetting factor.** Any $\beta > 0$ mixes statistics from earlier policies into the current estimate, which biases it; $\beta = 0$ removes the bias and, as the sweep shows, most of the data. The paper leaves the trade-off to the user, and so does this implementation.
