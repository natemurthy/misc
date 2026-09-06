# mdp-cart-pole (MPC)

TODO: study of cart pole problem solutions from the optimal control theory school of thought.


## The optimal-control lineage (for later)

Reinforcement learning and optimal control converged on the same object, the Bellman equation, from different directions, and this repository so far covers only the learning side. Threads to pick up later, in rough order:

- **Dynamic programming.** Bellman (1957) and value iteration on a discretized cart-pole model: the exact solution the 1989 Q-learning approximates from samples.
- **Linear-quadratic regulation.** Linearize the plant about the upright equilibrium and solve the Riccati equation. The resulting gain vector is a five-parameter linear controller much like the REINFORCE policy, obtained in closed form from the model instead of from data. A bang-bang version follows by taking the sign.
- **Adaptive critics as approximate DP.** Werbos (1987 onward) framed the 1983 critic as Heuristic Dynamic Programming and proposed the DHP/GDHP family, which is the control-theory community's route to the same actor-critic architecture.
- **Neuro-dynamic programming.** Bertsekas and Tsitsiklis (1996) consolidate both lineages under one theory.

