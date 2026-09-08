# 2011: PILCO, Probabilistic Inference for Learning Control (Deisenroth and Rasmussen)

**Lineage:** [1983 actor-critic](../1983_actor_critic/README.md) → [1986 backprop actor-critic](../1986_actor_critic_backprop/README.md) → [1988 TD(λ)](../1988_td/README.md) → [1989 Q-learning](../1989_qlearning/README.md) → [1990 Dyna](../1990_dyna/README.md) → [1992 REINFORCE](../1992_reinforce/README.md) → [1999 continuous Q-learning](../1999_qlearning_continuous/README.md) → [2005 NAC](../2005_nac/README.md) → [2007 CACLA](../2007_cacla/README.md) → [2011 NFQCA](../2011_nfqca/README.md) → **2011 PILCO** → [2013 DQN](../2013_dqn/README.md) → [2015 DDPG](../2015_ddpg/README.md) → [2015 TRPO](../2015_trpo/README.md) → [2017 PPO](../2017_ppo/README.md) → [2018 SAC](../2018_sac/README.md)

**Previous:** [2011 NFQCA, batch-fitted actor and critic](../2011_nfqca/README.md)

**Next:** [2013 DQN, replay and target networks](../2013_dqn/README.md)

## References

- M. P. Deisenroth and C. E. Rasmussen, ["PILCO: A Model-Based and Data-Efficient Approach to Policy Search"](https://mlg.eng.cam.ac.uk/pub/pdf/DeiRas11.pdf), *ICML* 2011. The method, the analytic gradients, and the real cart-pole swing-up learned from 17.5 s of interaction. [Talk slides](https://www.deisenroth.cc/talks/2011-07-01-icml.pdf) from the same conference: 10 Hz control, fewer than 10 trials, about 20 s of interaction, θ ∈ ℝ³⁰⁰.
- M. P. Deisenroth, D. Fox and C. E. Rasmussen, ["Gaussian Processes for Data-Efficient Learning in Robotics and Control"](https://doi.org/10.1109/TPAMI.2013.218), *IEEE TPAMI* 37(2), 2015. The long version, with the cart-pole settings: Δt = 0.1 s, a 2.5 s prediction horizon, u ∈ [−10, 10] N, cost on the pole-tip distance.
- C. E. Rasmussen and C. K. I. Williams, *Gaussian Processes for Machine Learning*, MIT Press, 2006. The GP prior, posterior and marginal-likelihood training used here.
- J. Quiñonero-Candela, A. Girard, J. Larsen and C. E. Rasmussen, "Propagation of Uncertainty in Bayesian Kernel Models: Application to Multiple-Step Ahead Forecasting", *ICASSP* 2003. Moment matching for a GP prediction at a Gaussian input, which PILCO extends to multiple outputs and controls.

## What changed

**From Dyna (1990), the other learned-model method here.** Dyna learned a tabular sample model and used it to run more Q-learning updates between real steps: the model was a source of extra transitions, and the value function did the work. PILCO learns a model too, but a *probabilistic* one, a Gaussian process per state dimension over (state, action) → state change, and it never learns a value function at all. The model is used for *inference*: the distribution of the state is pushed forward through the GP and through the controller for the whole horizon, the expected cost along the way is computed in closed form, and the policy parameters are moved down its gradient. Model uncertainty is carried along on purpose. A deterministic learned model claims to know what happens where it has no data, and a policy optimized against it exploits those claims (the paper calls this model bias and shows that PILCO with the GP's posterior mean alone fails on the same task). The GP's posterior variance grows away from the data, the predicted state distribution widens, the saturating cost's expectation rises toward 1, and the optimizer is pushed back toward states the model knows. That is why PILCO learns from so little data: the paper's real cart-pole swing-up took 17.5 s of interaction, the slides say fewer than 10 trials, and Fig. 5 of the paper puts that an order of magnitude below every method that had solved the task from scratch before, NFQ (2005) and CACLA (2010) included.

**From NFQCA (2011).** Both are batch methods that refit on all data between episodes, and both output a continuous force. NFQCA is model-free: it fits a critic to the reward signal by fitted Q iteration and a maximizing actor on top, and it needs hundreds of episodes because every bit of information about the dynamics has to arrive through the scalar Bellman residual. PILCO goes the other way: it learns the dynamics directly from the 4-dimensional state differences, which is a far richer supervised signal per step, and it evaluates the policy by simulation on that model. The cost of the trade is that the model, not the data, determines what the policy can learn, and that all the inference must be done by hand: moment matching through a nonlinear model is only tractable for a few model and controller families, which is why the SE kernel, the linear or RBF controller and the saturating cost are chosen as they are.

**Model-based versus model-free.** In the lineage table PILCO and Dyna are the two solutions that learn a model, and TD(λ) with lookahead is the one that is given the true model. Everything else is model-free. PILCO is the first method here whose data requirement is measured in seconds rather than in hundreds of episodes.

## The method

State $\mathbf x_t \in \mathbb R^4$, control $u_t \in [-1, 1]$ (the force fraction), unknown dynamics $\mathbf x_{t+1} = f(\mathbf x_t, u_t)$. The policy $\pi_\theta$ is deterministic, and the objective is the expected long-term cost of following it for $T$ steps from a Gaussian start,

$$
J(\theta) = \sum_{t=1}^{T} \mathbb E_{\mathbf x_t}\!\big[c(\mathbf x_t)\big], \qquad \mathbf x_0 \sim \mathcal N(\boldsymbol\mu_0, \boldsymbol\Sigma_0),
$$

with the saturating cost on the distance $d$ of the pole tip from its target,

$$
c(\mathbf x) = 1 - \exp\!\left(-\frac{d(\mathbf x)^2}{2\sigma_c^2}\right) \in [0, 1], \qquad d^2 = x^2 + (L\theta)^2,
$$

$L = 1$ m the pole length and $\sigma_c = 0.25$ m the cost width, as in the paper. The three components are the model, the inference, and the gradient step.

**Dynamics model.** One GP per state dimension $a$, with training inputs $\tilde{\mathbf x} = (\mathbf x, u) \in \mathbb R^5$ and targets the differences $\Delta^a = x'_a - x_a$, zero prior mean and a squared exponential kernel with automatic relevance determination,

$$
k_a(\tilde{\mathbf x}, \tilde{\mathbf x}') = \alpha_a^2 \exp\!\Big(-\tfrac12 (\tilde{\mathbf x} - \tilde{\mathbf x}')^\top \boldsymbol\Lambda_a^{-1} (\tilde{\mathbf x} - \tilde{\mathbf x}')\Big), \qquad \boldsymbol\Lambda_a = \operatorname{diag}(\ell_{a1}^2, \dots, \ell_{a5}^2).
$$

Given $n$ inputs $\tilde{\mathbf X}$ and targets $\mathbf y_a$, the hyperparameters $(\ell_a, \alpha_a, \sigma_{\varepsilon a})$ maximize the marginal likelihood,

$$
\log p(\mathbf y_a \mid \tilde{\mathbf X}) = -\tfrac12 \mathbf y_a^\top (\mathbf K_a + \sigma_{\varepsilon a}^2 \mathbf I)^{-1} \mathbf y_a - \tfrac12 \log|\mathbf K_a + \sigma_{\varepsilon a}^2 \mathbf I| - \tfrac n2 \log 2\pi,
$$

and the posterior at a known input $\tilde{\mathbf x}_*$ is Gaussian with mean $\mathbf k_*^\top \boldsymbol\beta_a$ and variance $k_{**} - \mathbf k_*^\top (\mathbf K_a + \sigma_{\varepsilon a}^2 \mathbf I)^{-1} \mathbf k_*$, where $\boldsymbol\beta_a = (\mathbf K_a + \sigma_{\varepsilon a}^2 \mathbf I)^{-1} \mathbf y_a$.

**Policy evaluation by moment matching.** The state at time $t-1$ is approximated by $\mathcal N(\boldsymbol\mu, \boldsymbol\Sigma)$. The controller is a linear law through a saturating function, $u = g(v)$, $v = \mathbf w^\top \mathbf x + b$, $g(v) = \tfrac18 (9 \sin v + \sin 3v)$, which is bounded in $[-1, 1]$ and whose moments under a Gaussian $v \sim \mathcal N(m, s^2)$ are elementary: $\mathbb E[\sin kv] = \sin(km)\, e^{-k^2 s^2/2}$, products of sines reduce to cosines, and $\operatorname{cov}[\mathbf x, u] = \boldsymbol\Sigma \mathbf w\, \mathbb E[g'(v)]$ by Stein's lemma. That gives the joint Gaussian of $(\mathbf x, u)$, with mean $\tilde{\boldsymbol\mu}$ and covariance $\tilde{\boldsymbol\Sigma}$. Pushing it through GP $a$ exactly is intractable, but the first two moments of the output are available in closed form (paper Eqs. 13-23):

$$
\mu_\Delta^a = \boldsymbol\beta_a^\top \mathbf q_a, \qquad
q_{ai} = \alpha_a^2\, |\tilde{\boldsymbol\Sigma} \boldsymbol\Lambda_a^{-1} + \mathbf I|^{-1/2} \exp\!\Big(-\tfrac12 \boldsymbol\nu_i^\top (\tilde{\boldsymbol\Sigma} + \boldsymbol\Lambda_a)^{-1} \boldsymbol\nu_i\Big), \qquad \boldsymbol\nu_i = \tilde{\mathbf x}_i - \tilde{\boldsymbol\mu},
$$

$$
\sigma^2_{ab} = \boldsymbol\beta_a^\top \mathbf Q_{ab} \boldsymbol\beta_b - \mu^a_\Delta \mu^b_\Delta + \delta_{ab}\Big(\alpha_a^2 - \operatorname{tr}\big((\mathbf K_a + \sigma_{\varepsilon a}^2 \mathbf I)^{-1} \mathbf Q_{aa}\big)\Big),
\qquad
Q_{ab,ij} = \frac{k_a(\tilde{\mathbf x}_i, \tilde{\boldsymbol\mu})\, k_b(\tilde{\mathbf x}_j, \tilde{\boldsymbol\mu})}{\sqrt{|\mathbf R|}} \exp\!\Big(\tfrac12 \mathbf z_{ij}^\top \mathbf R^{-1} \tilde{\boldsymbol\Sigma} \mathbf z_{ij}\Big),
$$

with $\mathbf R = \tilde{\boldsymbol\Sigma}(\boldsymbol\Lambda_a^{-1} + \boldsymbol\Lambda_b^{-1}) + \mathbf I$ and $\mathbf z_{ij} = \boldsymbol\Lambda_a^{-1}\boldsymbol\nu_i + \boldsymbol\Lambda_b^{-1}\boldsymbol\nu_j$. The last term is the expected model variance: it is what makes the prediction widen where the data are sparse. The input-output covariance is $\operatorname{cov}[\tilde{\mathbf x}, \Delta^a] = \sum_i \beta_{ai} q_{ai}\, \tilde{\boldsymbol\Sigma} (\tilde{\boldsymbol\Sigma} + \boldsymbol\Lambda_a)^{-1} \boldsymbol\nu_i$, and the next state distribution is

$$
\boldsymbol\mu_t = \boldsymbol\mu_{t-1} + \boldsymbol\mu_\Delta, \qquad
\boldsymbol\Sigma_t = \boldsymbol\Sigma_{t-1} + \boldsymbol\Sigma_\Delta + \operatorname{cov}[\mathbf x_{t-1}, \boldsymbol\Delta_t] + \operatorname{cov}[\boldsymbol\Delta_t, \mathbf x_{t-1}].
$$

Repeating this $T$ times gives $\mathcal N(\boldsymbol\mu_t, \boldsymbol\Sigma_t)$ for $t = 1..T$, and the expected saturating cost of each is also closed form,

$$
\mathbb E\big[c(\mathbf x_t)\big] = 1 - |\mathbf I + \boldsymbol\Sigma_t \mathbf W|^{-1/2} \exp\!\Big(-\tfrac12 \boldsymbol\mu_t^\top \mathbf W (\mathbf I + \boldsymbol\Sigma_t \mathbf W)^{-1} \boldsymbol\mu_t\Big), \qquad \mathbf W = \operatorname{diag}(1, 0, L^2, 0)/\sigma_c^2 .
$$

**Policy improvement.** Everything above is a differentiable function of $\theta = (\mathbf w, b)$, so $\mathrm dJ/\mathrm d\theta$ exists in closed form; the paper obtains it by repeated application of the chain rule through Eqs. 10-23 and hands it to a gradient-based optimizer (CG or L-BFGS). The outer loop, Algorithm 1 of the paper, is: apply random controls for one trial; then repeat {fit the GP on all data, minimize $J(\theta)$ on the model, apply $\pi_{\theta^*}$ for one trial and record it}.

## Implementation notes and deviations

- **Autograd instead of hand-derived gradients.** The paper's contribution includes the analytic derivatives of the moment-matching equations. Here the forward computation, GP posterior, control moments, moment matching, cost, is written in PyTorch (float64) and `torch.autograd` supplies $\mathrm dJ/\mathrm d\theta$ and the marginal-likelihood gradients; `torch.optim.LBFGS` with a strong-Wolfe line search does both optimizations, capped at 40 iterations each. The moment-matching formulas themselves are the closed-form ones above, checked against Monte Carlo sampling through the GP in `tests/test_pilco.py`.
- **10 Hz control while collecting data.** The paper controlled its cart-pole at 10 Hz. The environment steps every 20 ms, so while learning the agent holds each command for `hold = 5` steps and records one transition per hold: state at the start, command, state at the end. That keeps the GP's time step at 0.1 s and the planning horizon at `horizon = 30` model steps (3 s), against the paper's 2.5 s. Transitions cut short by a failure inside a hold are not recorded. Once learning has stopped, and whenever the agent is frozen, the controller is a state-feedback law $u = g(\mathbf w^\top \mathbf x + b)$ and is applied at every 20 ms step, which is strictly more stable than holding it: the held version is marginal from starts within a degree of the 12° limit, the per-step version is not.
- **Balancing, not swing-up.** The environment terminates at 12°, so the task is the balancing regulator, and a linear controller with the paper's squashing function is enough (PILCO used a linear controller for the unicycle and a 50-unit RBF network, $\theta \in \mathbb R^{305}$, for the swing-up, which a linear law cannot do). The preliminary control is clamped to $[-\pi/2, \pi/2]$ before squashing at act time so the periodic $g$ cannot wrap around; in planning $v$ is Gaussian and unclamped, exactly as in the paper.
- **Fixed fit schedule.** The GP is refit and the policy reoptimized at the end of each of the first `max_fits = 15` episodes ("trials"), then learning stops and the controller is fixed for the rest of the run. The paper stops "until task learned"; a fixed count keeps a 5000-episode run tractable and makes the point that all the learning is over in the first dozen trials. The first trial applies uniformly random held commands, as in Algorithm 1.
- **Capped training set.** The paper uses all data. Here the GP keeps at most `n_max = 200` transitions, chosen by farthest-point sampling in input space from everything recorded so far, so the set covers the visited region rather than piling up near the equilibrium; a fit then costs 1-6 s on one core. With a good policy every trial adds 100 transitions, so the cap is hit at trial 4.
- **Hyperparameter priors.** As in Deisenroth's reference code, the marginal likelihood is penalized with a soft barrier on the length-scales (within 100× the unit scale) and on the signal-to-noise ratio (below 1000), which keeps the tiny first fits (4-8 transitions) from running off.
- **Cost and start distribution.** The cost is quadratic in $(x, L\theta)$, the small-angle form of the paper's pole-tip distance, with the paper's $\sigma_c = 0.25$ m; velocities carry no cost. Planning starts from $\boldsymbol\mu_0 = 0$ and $\boldsymbol\Sigma_0 = \operatorname{diag}(0.03^2, 0.03^2, (10°)^2, 0.03^2)$, wide in the angle so the policy is optimized for the full ±12° range of starts; with 7° the held controller failed from 11°.
- **What the +1 reward change required.** Nothing in the algorithm. PILCO never sees the environment's reward: it minimizes its own saturating state cost, as in the paper, and the +1 per step is used only to compute the episode return that the training loop and the tests report. The saved model contains the policy $(\mathbf w, b)$, the GP hyperparameters and the GP training set; only the policy is needed to act.
- The agent reads the raw state, so `--theta-limit` above 12° is accepted, but the cost width and the planning distribution were chosen for the 12° task.

## Run

```sh
python ../main.py --mode train --soln 2011_pilco --no-render
python ../main.py --mode infer --soln 2011_pilco --theta0 -11
pytest ../tests -k pilco
```

With rendering on, the first 18 training episodes are animated regardless of `--render-every` (the agent sets `render_first_episodes = max_fits + 3`): the 15 learning trials are the whole story of a PILCO run and would otherwise never be shown, and the phase portrait makes the jump from the second trial's fall to the third trial's 500 steps visible. Each of those episodes ends with a fit of a few seconds, during which the window pauses.

`../tests/test_2011_pilco.py` runs the shared interface checks and tests the model directly: the GP mean interpolates its training targets, moment matching agrees with Monte Carlo sampling through the GP, the saturating cost is 0 at the target, and the action is held for the model's 0.1 s time step. Because a fit costs seconds, the file fits the GP once in a module fixture; the interface checks run on that pre-fitted agent with its fit budget spent, and the remaining tests read the fit record: no call to `CartPoleEnv.dynamics` while learning, fitting stopped at the budget, two fits already clear the learning threshold, and the saved model carries the GP data and the controller.

## Result

Seed 0, 5000 training episodes with full-range starts, frozen policy, 20 episodes per start angle:

| start angle | 0° | −8° | +8° | −11° | +11° |
|---|---|---|---|---|---|
| mean steps (max 500) | 500 | 500 | 500 | 500 | 500 |

The first two trials (random commands, then a controller fitted to 4 transitions) lasted 20 and 21 steps. The third trial, with a policy optimized on a GP fitted to 8 transitions, 0.8 s of experience, ran the full 500 steps, and so did every trial after it. The 100-episode average first reached 500 at episode 102, the earliest the two warm-up trials allow. Learning stopped after trial 15 with 1308 recorded transitions (130.8 s of experience, 200 of them kept in the GP); the controller it left, $u = g(2.62\,\bar x + 3.22\,\bar{\dot x} + 1.12\,\bar\theta + 4.73\,\bar{\dot\theta})$ on the normalized state, is a plain linear stabilizer. Over the remaining 4985 episodes only six fell short of 500, all one-step episodes started within 0.03° of the 12° limit with an adverse initial angular velocity, which no controller can recover. Training took 76.6 s on one CPU core with PyTorch: 2.50 M environment steps at about 32,600 steps/s, or 30.7 µs per step; the 15 fits account for about 45 s of that and the rest is the fixed controller running 500-step episodes. For comparison, the paper's real cart-pole swing-up took 17.5 s of interaction; the balancing task here is easier, and PILCO's data efficiency shows accordingly.

## Limitations

- Moment matching is exact only for the first two moments, and the true state distribution after a nonlinear step is not Gaussian; the paper notes the approximation tends to be conservative rather than overconfident, which is the safe direction, but a multimodal outcome (fall left or fall right) is represented as one wide Gaussian. Model uncertainty is also treated as independent across time steps, which underestimates the correlated error of a consistently wrong model.
- Everything is closed form only for the SE kernel, the saturating (or polynomial) cost and controllers whose Gaussian moments are available. Changing any of them means rederiving the inference. The cost is $O(T n^2 D^2)$ per gradient evaluation for $n$ training points and $D$ state dimensions, so the training set must stay small (hundreds of points); that is why the paper's data efficiency and its computational cost are the same fact.
- The policy is only as good as the model in the region the trials visited. From starts the model has not seen, the GP's uncertainty saturates the cost and the gradient vanishes (the paper's Section 4 discusses this); on this task the random first trial and the wide start distribution are enough, on harder tasks PILCO needs several random trials.
- It is deterministic and noise-free in its exploration: after the first trial there is no exploration beyond what model uncertainty induces in the optimizer. When that is not enough the method stalls quietly with a confident, wrong model.
