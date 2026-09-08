# mdp-cart-pole (OC)

TODO: study of cart pole problem solutions from the optimal control theory school of thought.


## Linear state feedback, hand-tuned (`linear_controller/`)

The first controller here is the simplest one in the optimal-control lineage and doubles as the reference the `../rl` READMEs quote: full-state linear feedback through a bang-bang actuator,

$$
u = \mathrm{sign}\big(k_\theta\,\theta + k_{\dot\theta}\,\dot\theta + k_x\,x + k_{\dot x}\,\dot x\big), \qquad (k_\theta, k_{\dot\theta}, k_x, k_{\dot x}) = (1,\ 0.35,\ 0.02,\ 0.2),
$$

with $u = +1$ a full push right and $u = -1$ a full push left. Nothing is learned. The gains were found by a grid search (`tune()` in `linear_controller/soln.py`) that maximizes the widest pole angle the controller can recover from, starting at rest, without leaving the ±2.4 m track. Only the ratios matter to a sign function, so $k_\theta$ is fixed at 1.


This is not model-predictive control and it is not yet optimal control. It is the form an LQR produces once its continuous output is saturated to a sign, with the gains chosen by trial instead of by solving the Riccati equation for a stated cost. It is also, deliberately, the same form as the `1992_reinforce` policy in `../rl`, a linear-logistic unit over the same four state variables: the two differ only in how the gains were obtained, by search here and by policy gradient there.

**Recovery envelope.** Largest start angle recovered from at rest (episode survives 500 steps with the angle limit widened so that only the track can end it), by cart start position, with the pole leaning toward positive $x$:

| cart start | −1.5 m | −1.0 m | 0 m | +1.0 m | +1.5 m |
|---|---|---|---|---|---|
| max recoverable angle | 37° | 37° | 34° | 27° | 22° |

The bound is the track, not the motor. The push out-accelerates gravity up to about 43°, but recovering from a wide angle takes a long hard push and the cart reaches the end of the track first. Every failure inside the envelope is by track, none by angle.

**Run** (from this directory):

```sh
python main.py --mode run                                   # standard 12 degree task, live view
python main.py --mode run --theta-limit 45 --theta0 30 --x0 -1.0
python main.py --mode run --gains 1 0.5 0.05 0.2 --no-render --episodes 20
python main.py --mode envelope                              # the table above
python main.py --mode tune                                  # redo the gain search
pytest                                                      # tests for the controller and the driver
```

The environment and the three-panel visualization, including the phase portrait, are shared with `../rl/common`; the portrait's diagnostic readout shows the feedback value $u$ before the sign.

**Next in this directory:** derive the gains instead of searching for them. Linearize the cart-pole system about the upright equilibrium, state a quadratic cost, solve the Riccati equation for the LQR gain vector, and compare it with the tuned vector above and with the REINFORCE policy.

## The optimal-control lineage (for later)

Reinforcement learning and optimal control converged on the same object, the Bellman equation, from different directions, and this repository so far covers only the learning side. Threads to pick up later, in rough order:

- **Dynamic programming.** Bellman (1957) and value iteration on a discretized cart-pole model: the exact solution the 1989 Q-learning approximates from samples.
- **Linear-quadratic regulation.** Linearize the cart-pole system about the upright equilibrium and solve the Riccati equation. The resulting gain vector is a five-parameter linear controller much like the REINFORCE policy, obtained in closed form from the model instead of from data. A bang-bang version follows by taking the sign.
- **Adaptive critics as approximate DP.** Werbos (1987 onward) framed the 1983 critic as Heuristic Dynamic Programming and proposed the DHP/GDHP family, which is the control-theory community's route to the same actor-critic architecture.
- **SARSA, Rummery and Niranjan (1994).** The on-policy sibling of Q-learning: bootstrap from the action actually taken. Safer with function approximation and with exploration, which is why Sutton's 1996 results used it.
- **Convergence proofs.** Jaakkola, Jordan and Singh (1994) and Tsitsiklis (1994) gave a stochastic-approximation framework that proves Q-learning and TD(λ) convergence in one stroke; Singh, Jaakkola, Littman and Szepesvári (circulated 1998) did the same for SARSA under decaying exploration.
- **Q(λ) and prioritized sweeping.** Peng and Williams (1994 to 1996) put eligibility traces under Q-learning; Moore and Atkeson (1993) replaced Dyna's uniform planning sample with a priority queue ordered by TD error, which fixes the weakness our Dyna README describes.
- **Neuro-dynamic programming.** Bertsekas and Tsitsiklis (1996) consolidate both lineages under one theory.
- **Policy gradient with function approximation.** Sutton, McAllester, Singh and Mansour (1999) proved the policy gradient theorem and showed which critic is compatible with a given actor; Konda and Tsitsiklis (1999) gave convergent actor-critic algorithms. This is where the 1983 actor-critic and the 1992 REINFORCE lines formally rejoin. Ng, Harada and Russell (1999) showed which reward shapings leave the optimal policy unchanged.


- **Model-based data efficiency with PILCO.** Deisenroth and Rasmussen (2011) learned a Gaussian-process model of the cart-pole system and swung up a real cart-pole in about ten trials, the most sample-efficient result of the period and the strongest argument for learning a model when data is expensive (question of whether this is MPC or model-based RL)
