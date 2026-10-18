# What to explore next: cart-pole in the RL literature, 2018 to present

This file merges two AI-generated literature surveys of cart-pole work since 2018 (one from Gemini, one from Claude), de-duplicated and reorganized, and turns them into a rough plan for which methods to add to this directory next. The [lineage table](README.md#literary-history) currently ends at [2018 SAC](2018_sac/README.md); everything below is a candidate for what comes after it.

Provenance is marked per entry: **[G]** appeared only in the Gemini survey, **[C]** only in the Claude survey, **[G,C]** in both. A **✓** means the citation was checked against the primary source while assembling this file; entries without it are carried over from the surveys as written and should be verified before being relied on.

Contents:

1. [Benchmark and comparison papers](#1-benchmark-and-comparison-papers)
2. [Research threads, 2018 to present](#2-research-threads-2018-to-present)
3. [Suggested plan](#3-suggested-plan)
4. [What the two surveys disagreed on or got wrong](#4-what-the-two-surveys-disagreed-on-or-got-wrong)
5. [References](#5-references)

## 1. Benchmark and comparison papers

Papers whose main contribution is a protocol or a side-by-side comparison on cart-pole, rather than a new method. These are the ones to read first, because they define what "solved" and "better" mean and because this directory's own [results table](README.md#results) should eventually be comparable to at least one of them.

| Paper | Year | What it benchmarks | Why it matters here |
|---|---|---|---|
| Duan, Chen, Houthooft, Schulman, Abbeel, [*Benchmarking Deep Reinforcement Learning for Continuous Control*](https://arxiv.org/abs/1604.06778v2), ICML ✓ | 2016 | The `rllab` suite: REINFORCE, TNPG, RWR, REPS, TRPO, CEM, CMA-ES, DDPG on cart-pole balance, **cart-pole swing-up**, mountain car, acrobot, double inverted pendulum, plus locomotion and partially observed variants. | The reference protocol for continuous-force cart-pole and the first standard **swing-up** definition. Its finding that TRPO and TNPG beat DDPG on stability, and that gradient-free CEM and CMA-ES are competitive on the low-dimensional tasks, is the baseline any new entry here should be checked against. Predates 2018 but is the benchmark the later work cites. |
| Henderson, Islam, Bachman, Pineau, Precup, Meger, [*Deep Reinforcement Learning that Matters*](https://arxiv.org/abs/1709.06560), AAAI **[C]** | 2018 | PPO, TRPO, DDPG, ACKTR under different seeds, network widths, activations, reward scales and codebases. | Showed reported gains are often seed noise. The reason the results table in this directory needs multi-seed runs with confidence intervals before any two rows are compared. |
| Tassa et al., [*DeepMind Control Suite*](https://arxiv.org/abs/1801.00690) **[C]** | 2018 | Cart-pole `balance`, `balance_sparse`, `swingup`, `swingup_sparse` from state or pixels, with a fixed 1000-step, 0-to-1 reward. | The standard pixel-based cart-pole; every DrQ, Dreamer and CURL result uses it. |
| Nagendra, Podila, Ugarakhod, George, [*Comparison of Reinforcement Learning algorithms applied to the Cart Pole problem*](https://arxiv.org/abs/1810.01940) **[G]** | 2017 | Q-learning variants and Deep Q-learning on the Gym cart-pole. | An early plain comparison, cited by the 2024 study below. |
| [*Empirical study of deep reinforcement learning algorithms for CartPole problem*](https://ieeexplore.ieee.org/document/10512107), IEEE conference **[G,C]** ✓ | 2024 | **DQN, PPO, QR-DQN and A2C** on Gym `CartPole`, scored on training time, timesteps to threshold, best 100-episode mean and frames per second. | The closest published analogue of this directory's results table (episodes to 500, wall time, steps per second). Also the paper the Gemini survey cited for QR-DQN on cart-pole. |
| [*Reinforcement Learning Control Strategies: Q-learning, SARSA, and Double Q-learning Performance for the Cart-Pole Problem*](https://ieeexplore.ieee.org/document/11099239), IEEE conference **[G]** | 2025 | Three tabular methods. | Directly comparable to [`1989_qlearning/`](1989_qlearning/README.md); a cheap SARSA and Double-Q addition would reproduce it. |
| [*Implementation of Reinforcement Learning on Cart-Pole System Using Deep Q-Network, REINFORCE a Policy-Based, and Advanced Actor-Critic Methods*](https://ieeexplore.ieee.org/document/11350702/), IEEE conference | 2025 | DQN, REINFORCE, A2C. | Same three families as [`2013_dqn/`](2013_dqn/README.md), [`1992_reinforce/`](1992_reinforce/README.md) and the actor-critics here. |
| [*Review on Reinforcement Learning in CartPole Game*](https://ieeexplore.ieee.org/document/9990767/), IEEE conference **[G]** | 2022 | A survey of methods applied to the Gym task. | Secondary source; useful as a citation index. |
| Lange, Hafner, Riedmiller, [*NFQ2.0: The CartPole Benchmark Revisited*](https://arxiv.org/abs/2511.12644) **[G]** ✓ | 2025 | Neural fitted Q iteration, modernized (batch size 2048 or more, full-dataset replay, strict reward shaping), on a **physical** cart-pole built from industrial components. Swing-up and balance in roughly 70 to 120 real episodes, with ablations on repeatability. | The same authors as [`2011_nfqca/`](2011_nfqca/README.md), revisiting their own benchmark on real hardware. The natural "what happened to NFQ" follow-up for this lineage. |
| Araújo, Figueiredo, Botto, [*Control with adaptive Q-learning: A comparison for two classical control problems*](https://www.sciencedirect.com/science/article/abs/pii/S0952197622000732), Eng. Appl. of AI ([arXiv 2011.02141](https://arxiv.org/abs/2011.02141)) **[G]** ✓ | 2022 | AQL, SPAQL and SPAQL-TS against TRPO on Pendulum and CartPole. | Adaptive state-action partitioning that is more sample-efficient than TRPO and yields interpretable, time-invariant policies. Bridges the tabular and deep halves of this directory. |
| Farama, [Gymnasium `CartPole-v1` documentation](https://gymnasium.farama.org/environments/classic_control/cart_pole/) **[G,C]** | ongoing | The 500-step cap that replaced `v0`'s 200, the reward and termination conventions this directory follows. | Already the reference for [`common/env.py`](common/env.py); listed for completeness. |
| Freeman et al., [*Brax*](https://arxiv.org/abs/2106.13281) and Lange, [*gymnax*](https://github.com/RobertTLange/gymnax) **[C]** | 2021-22 | JAX-vectorized environments. | Make thousand-seed sweeps cheap; relevant if the Henderson-style protocol turns out too slow in numpy. |

## 2. Research threads, 2018 to present

Cart-pole was solved long before 2018. Both surveys agree that the literature since then treats it as a fast, cheap testbed for a *property* of an algorithm (sample efficiency, robustness, interpretability, safety, transfer) rather than as a target. The threads below merge the two surveys' section lists; where both covered a thread the entries are combined.

### 2.1 Model-based RL and sample efficiency **[G,C]**

- **PILCO** (Deisenroth and Rasmussen, 2011) already reached swing-up in a handful of trials with Gaussian-process dynamics; implemented here as [`2011_pilco/`](2011_pilco/README.md), and its data efficiency is two orders of magnitude beyond anything model-free in the results table. **[C]**
- **PETS** (Chua, Calandra, McAllister, Levine, [arXiv 1805.12114](https://arxiv.org/abs/1805.12114), NeurIPS 2018): probabilistic ensemble dynamics model with trajectory-sampling MPC. Near-optimal cart-pole in a few thousand steps. **[C]**
- **MBPO** (Janner, Fu, Zhang, Levine, [arXiv 1906.08253](https://arxiv.org/abs/1906.08253), NeurIPS 2019): short model rollouts branched from real states, feeding SAC. **[C]**
- **Dreamer / DreamerV3** (Hafner et al., 2019 to 2023, [arXiv 2301.04104](https://arxiv.org/abs/2301.04104)): latent world model learned from pixels; V3 uses one fixed hyperparameter set across every domain. **[C]**
- **JEPA for RL** (T. Kenneweg, P. Kenneweg, Hammer, [arXiv 2504.16591](https://arxiv.org/abs/2504.16591), ESANN 2025) ✓: the non-generative counterpart to Dreamer. A joint-embedding predictive architecture, in the LeCun sense, learns a latent from three stacked pixel frames with a vision-transformer encoder, and an action-conditioned predictor forecasts the *embedding* of the next frame rather than reconstructing pixels. PPO is trained on the 64-dimensional embedding. Collapse is prevented by an EMA target encoder, batch-wise variance regularization, and backpropagating the actor-critic loss through the encoder. Evaluated only on pixel cart-pole over the first 100k steps, with four ablations of its own and no external baselines; the authors call the results exemplary and the task simple. Where Dreamer spends capacity on a decoder, JEPA spends none, which is the design question this line of work is testing. Added to the surveys' lists by request.
- **SPAQL-TS** (2022, above): adaptive partitioning of the continuous state-action space during training, time-invariant policies, more sample-efficient than TRPO on Gym CartPole. **[G]**

### 2.2 Value-function improvements: distributional and de-biased Q-learning **[G]**

- **QR-DQN** (Dabney, Rowland, Bellemare, Munos, [arXiv 1710.10044](https://arxiv.org/abs/1710.10044), AAAI 2018) models the full return distribution with quantile regression rather than its mean. Applied to cart-pole in the 2024 IEEE study above.
- **Dueling Double DQN (D3QN)** and Double Q-learning address the maximization bias of standard Q-learning; the 2025 IEEE tabular comparison covers Double Q-learning. Cited by the Gemini survey via a [comparative review on the inverted pendulum](https://www.academia.edu/72820412/A_Review_of_Deep_Reinforcement_Learning_Algorithms_and_Comparative_Results_on_Inverted_Pendulum_System).
- Related and not in either survey, but the obvious 2018 companion to SAC: **TD3** (Fujimoto, van Hoof, Meger, [arXiv 1802.09477](https://arxiv.org/abs/1802.09477), ICML 2018), already cited in the [SAC README](2018_sac/README.md) for the twin-critic minimum.

### 2.3 Pixel-based learning and data augmentation **[C]**

- The **DeepMind Control Suite** (2018) made image-based cart-pole a standard benchmark.
- **CURL** (Laskin et al., 2020), **RAD** (Laskin et al., 2020), **DrQ** (Kostrikov et al., 2020) and **DrQ-v2** (Yarats et al., 2021) showed that random crop or shift augmentation plus a contrastive or plain SAC objective closes most of the gap between pixel and state observations.
- **JEPA for RL** (2025, see 2.1) is the newest entry in this thread: a predictive rather than contrastive or augmentation-based auxiliary loss, with PPO on frozen or fine-tuned embeddings. It is the one pixel-based paper in this file whose only benchmark is cart-pole.

### 2.4 Offline RL and sequence modeling **[G]**

- **Decision Transformer** (Chen et al., [arXiv 2106.01345](https://arxiv.org/abs/2106.01345), NeurIPS 2021) treats control as return-conditioned sequence modeling. The Gemini survey cites a [Weights & Biases report](https://wandb.ai/evansnyanney-ohio-university/rl_algorithm_zoo/reports/Comparison-of-Four-Reinforcement-Learning-Methods-on-CartPole-v1--VmlldzoxMjEwMzE3MQ) that runs it on offline CartPole-v1 datasets against online methods.

### 2.5 Evolutionary and minimal-policy approaches **[C]**

- OpenAI's **evolution strategies** work (Salimans et al., 2017) and **Weight Agnostic Neural Networks** (Gaier and Ha, [arXiv 1906.04358](https://arxiv.org/abs/1906.04358), NeurIPS 2019), which solves cart-pole swing-up by architecture search with a single shared weight and no weight training.
- Duan et al. (2016) already found CEM and CMA-ES competitive on the low-dimensional tasks.

### 2.6 Interpretable and symbolic policies **[G,C]**

Cart-pole is the canonical example for interpretable RL. Both surveys covered this; the Gemini survey framed it as post-hoc explanation, the Claude survey as inherently interpretable policies.

- **Symbolic regression of policies** by genetic programming: Hein, Udluft, Runkler, [*Interpretable Policies for Reinforcement Learning by Genetic Programming*](https://arxiv.org/abs/1712.04170), 2018. One-line closed-form controllers matching deep policies. **[C]**
- **VIPER** (Bastani, Pu, Solar-Lezama, [arXiv 1805.08328](https://arxiv.org/abs/1805.08328), NeurIPS 2018): distill a deep policy into a verifiable decision tree; cart-pole is a worked example. **[C]**
- **Policy distillation into equations** that can be checked against a known control law such as LQR, enabling formal verification before deployment. **[G]** Overlaps with the two entries above and with [`../oc/`](../oc/README.md).
- **SPAQL-TS** (2022) also produces interpretable partition-based policies. **[G]**
- Post-hoc attribution on cart-pole agents: **SHAP** and **LIME** feature attributions showing the network weights pole angular velocity heavily and ignores cart position until near the track edge; **Jacobian saliency** and **Integrated Gradients** for pixel agents, which exposed agents tracking a score counter or a flickering pixel instead of the pole. **[G]**
- **Concept whitening** (Chen, Bei, Rudin, 2020) to align layers with named physical quantities. **[G]**

### 2.7 Safety and constrained RL **[G,C]**

- **Lyapunov-based safe RL** (Chow et al., [arXiv 1805.07708](https://arxiv.org/abs/1805.07708), NeurIPS 2018) and **control-barrier-function shielding** (Cheng, Orosz, Murray, Burdick, [arXiv 1903.08792](https://arxiv.org/abs/1903.08792), AAAI 2019), both using cart-pole with position constraints as the illustrative case. **[C]**
- **Logarithmic barrier function with DDPG** for swing-up: a pseudo-energy reward plus a barrier term to limit violent motions before hardware deployment. The Gemini survey cites a [2026 World Scientific paper](https://www.worldscientific.com/doi/10.1142/S2301385026410074); not verified. **[G]**
- Safety Gym-style constrained variants of cart-pole. **[C]**
- Not in either survey but on-topic: [*Reachability Guarantees for Cart-Pole Swing-Up and Stabilization*](https://arxiv.org/html/2606.28627), arXiv 2026.

### 2.8 Hybrid classical control and RL **[G]**

- **LQR for stabilization, RL for swing-up**, switched at a threshold. Cited via Nagendra et al. and the 2026 World Scientific paper.
- The hand-off already exists in this repository between [`2018_sac/`](2018_sac/README.md) and [`../oc/linear_controller/`](../oc/README.md); the missing piece is the swing-up phase, which needs a different reward.

### 2.9 Sim-to-real and hardware **[G,C]**

- **NFQ2.0** (2025, above): real cart-pole from industrial components, ablations on repeatability and latency. **[G]** ✓
- **DDPG parametric study** of swing-up ([ResearchGate](https://www.researchgate.net/publication/347683580_A_Parametric_Study_of_a_Deep_Reinforcement_Learning_Control_System_Applied_to_the_Swing-Up_Problem_of_the_Cart-Pole), 2020) reporting tolerance to large mass variation and dry friction, and hardware adaptation in a few dozen episodes; and a [2023 Springer chapter](https://link.springer.com/chapter/10.1007/978-981-99-1549-1_33) on DDPG swing-up and balance. The "90% mass variation" and "fewer than 40 episodes" figures are the Gemini survey's; not verified. **[G]**
- **Zero-shot transfer** of separately trained swing-up and stabilization policies to a physical rig ([arXiv 2606.22145](https://arxiv.org/abs/2606.22145), June 2026): Simulink switching logic, first-order action smoothing, sensitivity-guided domain randomization, linear curriculum. **[C]** ✓
- **MuJoCo Playground** (2025) as tooling for fast sim-to-hardware pipelines. **[C]**
- **Representation learning as a transfer route.** The pixel-based latent methods in 2.1 and 2.3 (DreamerV3, DrQ-v2, JEPA for RL) are the usual argument for how a policy trained on rendered frames could survive a camera on a physical rig: a latent that predicts the next embedding, not the next pixel, should be less sensitive to lighting and texture shifts. None of the cart-pole papers above tests that claim on hardware, so it is an open experiment, not a result.

### 2.10 Reproducibility and benchmark critique **[C]**

- Henderson et al. (2018) and follow-ups on seeds, hyperparameter sensitivity and "solving" thresholds.
- `CartPole-v1`'s 500-step cap replacing `v0`'s 200.
- JAX-vectorized environments for million-episode sweeps.

### 2.11 Quantum cart-pole **[G]**

- Wang, Ashida, Ueda, [*Deep reinforcement learning control of quantum cartpoles*](https://arxiv.org/abs/1910.09200), PRL 2020: quantum analogues built from inverted harmonic and quartic potentials, controlled by deep RL under continuous measurement, matching or beating physics-based feedback cooling. A novel domain rather than a method improvement.

### 2.12 Adjacent: interpretability of deep networks in general **[G,C]**

Both surveys appended a section on explainable AI and mechanistic interpretability that is mostly not about cart-pole. Condensed here because it motivates thread 2.6:

- **Attribution era (2016 to 2020):** LIME, Integrated Gradients, SHAP, Grad-CAM, TCAV; the critiques *Sanity Checks for Saliency Maps* (Adebayo et al., 2018) and *Stop Explaining Black Box Models* (Rudin, 2019); inherently interpretable architectures such as ProtoPNet and Concept Bottleneck Models. **[C]**, partially **[G]**
- **Circuits era (2020 to present):** the Distill Circuits thread, Transformer Circuits, induction heads, superposition and polysemanticity, sparse autoencoders (2023 to 2024), circuit tracing and attribution graphs (2025), the refusal direction (Arditi et al., 2024), chain-of-thought monitoring. **[C]**; the Gemini survey mentions polysemanticity and superposition applied to phase-space boundaries in cart-pole networks without a citation. **[G]**
- **Status:** *Open Problems in Mechanistic Interpretability* (2025) lists many intractable queries; the Claude survey notes that mechanistic interpretability has barely touched RL policy networks, which leaves an open gap between the two threads. **[C]**

## 3. Suggested plan

Ranked by expected applied-research return for *this* repository: how much a method teaches about the lineage, how directly it plugs into the existing `Agent` interface, environment and test suite, and how much it costs to build. Directory names follow the `<year>_<method>` convention. Each phase is roughly independent of the next, so they can be reordered, but within a phase the order is the suggested one.

### Phase 1: close out 2018 and fix the measurement (cheap, high return)

| Proposed directory | Year | Why first | Cost |
|---|---|---|---|
| `2018_td3/` | 2018 | The deterministic twin of SAC; clipped double-Q, delayed actor updates, target-policy smoothing. Isolates *which* of SAC's four changes over DDPG matter, since the [DDPG row](README.md#results) never reached 500 and SAC did. Reuses `deep.py` and the DDPG code almost line for line. | Low |
| `2018_qrdqn/` | 2017-18 | First distributional method; replaces DQN's Huber loss on a scalar with quantile regression over N atoms. Directly comparable to the 2024 IEEE benchmark, which ran QR-DQN against DQN, PPO and A2C on the same task. Discrete actions, so it slots next to [`2013_dqn/`](2013_dqn/README.md). | Low |
| Benchmark protocol (no new directory; extend `hparam_sweep.py`) | 2018 | Henderson et al.: run every solution on 5 to 10 seeds, report mean and bootstrap CI for episodes-to-500 and eval survival, and note the sensitivity to the two or three hyperparameters each README already discusses. Turns the results table from "each method demonstrably works" into something citable against Duan et al. and the 2024 IEEE study. | Low to medium (compute only) |
| Robustness evaluation (extend `main.py --mode infer`) | 2020-26 | Evaluate frozen policies under perturbed dynamics: pole mass, pole length, cart friction, action delay, observation noise. This is the cheapest possible sim-to-real proxy and the axis on which the sim-to-real papers (2.9) actually differ. Requires exposing `CartPoleEnv` parameters, which is a small change. | Low |

### Phase 2: model-based RL, the repository's stated thesis (high return, medium cost)

The top-level README argues that model-based RL and model-predictive control converged. PILCO is the only learned-model entry after 1990. These two make the argument concrete and set up the hand-off to [`../oc/`](../oc/README.md).

| Proposed directory | Year | Why | Cost |
|---|---|---|---|
| `2018_pets/` | 2018 | Probabilistic ensemble of neural dynamics models plus cross-entropy-method MPC over sampled trajectories. It *is* MPC with a learned model, so it is the clearest bridge to the optimal-control side. Continuous force. Compare data efficiency against PILCO's 15 trials and SAC's thousands of episodes. | Medium |
| `2019_mbpo/` | 2019 | Same ensemble model, but used to generate short branched rollouts that feed SAC. Shows the other way to spend a model: data augmentation for a model-free learner rather than planning. Reuses `2018_sac/` and the PETS model. | Medium |
| (optional) `2022_tdmpc/` | 2022 | TD-MPC (Hansen, Wang, Su): latent model plus terminal value plus MPC. The modern synthesis of the two above; defer unless PETS and MBPO both land cleanly. | Medium to high |

### Phase 3: interpretability and safety (high conceptual return, low to medium cost)

Cart-pole is the canonical example in both literatures, and this repository already has the two things they need: trained deep policies to distill, and a hand-tuned linear controller in `oc/` to compare against.

| Proposed directory | Year | Why | Cost |
|---|---|---|---|
| `2018_viper/` | 2018 | Distill any trained policy here (PPO or SAC) into a decision tree by DAgger-style imitation weighted by Q-value gaps. Then verify the tree: count leaves, read off the switching surface, compare with the `oc/` linear controller's gain vector. This is the Gemini survey's "policy distillation" entry made concrete. | Low to medium |
| `2018_gp_symbolic/` | 2018 | Hein et al. genetic-programming symbolic regression of a closed-form policy from the same trajectories. Compare the recovered expression with LQR gains. Pure numpy. | Medium |
| `2019_cbf_shield/` | 2019 | Cheng et al.: wrap an RL actor (SAC) in a control-barrier-function safety filter that keeps the cart inside a position bound stricter than ±2.4 m during *training*. Counts constraint violations per episode against unshielded SAC. Track limits make this the most natural constrained problem the environment already has. | Medium |
| `2022_spaql_ts/` | 2022 | Adaptive partitioning Q-learning with terminal states. Ties the 1989 tabular lineage to the deep half, reproduces a published cart-pole result that claims better sample efficiency than TRPO, and gives an interpretable partition to visualize on the phase portrait. | Medium |
| Attribution diagnostics (a script, not a solution) | 2017-20 | SHAP or Integrated Gradients over the four state inputs of each trained network, plotted on the phase portrait. Cheap, and it tests the Gemini survey's claim that networks ignore cart position until near the track edge. | Low |

### Phase 4: change the task (higher cost, opens new comparisons)

| Proposed work | Year | Why | Cost |
|---|---|---|---|
| Swing-up variant of `CartPoleEnv` | 2016-26 | Add `swingup=True`: pole starts hanging down, no angle termination, cosine-of-angle reward as in Duan et al. and the DeepMind Control Suite. Unlocks comparison with `rllab`, DMC, NFQ2.0, the DDPG swing-up papers and the 2026 zero-shot paper, and makes the LQR-plus-RL hybrid (2.8) a real experiment. Most later papers benchmark swing-up, not balance. | Medium |
| `2017_es/` or `2019_wann/` | 2017-19 | Gradient-free baselines. ES is a few dozen numpy lines and, per Duan et al., competitive here. WANN is a good teaching example of how little cart-pole needs. | Low (ES), medium (WANN) |
| `2021_decision_transformer/` | 2021 | Offline RL from trajectories logged by the existing agents (a mixed-quality dataset is free: log the 1989, 2013 and 2017 agents during training). Return-conditioned inference reproduces the W&B report cited by the Gemini survey. First sequence model in the lineage. | Medium |
| Pixel observations plus `2021_drqv2/`, `2023_dreamerv3/` or `2025_jepa/` | 2020-25 | Render the cart to a small image and learn from it. Expensive on CPU, needs a renderer decoupled from matplotlib, and most of the interesting result (augmentation closes the pixel-state gap) is about vision rather than control. Of the three, JEPA is the cheapest to try first: its policy is the existing [`2017_ppo/`](2017_ppo/README.md) agent on a 64-dimensional embedding, the encoder can be a small CNN instead of the paper's vision transformer at this image size, and its 100k-step budget is within reach on a CPU. The comparison worth running is JEPA against DreamerV3 on the same frames: predict the embedding or reconstruct the pixels. Defer the other two unless there is a GPU. | High (medium for JEPA alone) |
| Domain randomization plus hardware | 2025-26 | Only worth doing with a physical rig. The Phase 1 robustness evaluation captures the simulation half. | High |

### Deferred

- **Quantum cart-pole** (2.11): a different physical system, not an RL method; interesting reading, no repository work.
- **Mechanistic interpretability of policy networks** (2.12): the Claude survey identifies this as an open gap, and the networks here are tiny (32 to 128 units), which makes them an unusually tractable target. Worth a small exploratory notebook after Phase 3, not a lineage entry.
- **LBF+DDPG** and the other unverified **[G]** citations: check the primary sources before reproducing.

### Order of operations, condensed

1. `2018_td3/`, `2018_qrdqn/`, multi-seed protocol, robustness evaluation.
2. `2018_pets/`, `2019_mbpo/`; write the hand-off to `oc/` MPC.
3. `2018_viper/`, `2019_cbf_shield/`, attribution script; then `2022_spaql_ts/` and symbolic regression.
4. Swing-up environment, then whichever of ES, Decision Transformer or the hybrid LQR+RL swing-up is most useful at that point. If pixels are ever added, start with `2025_jepa/` on top of the PPO agent and compare with DreamerV3.

## 4. What the two surveys disagreed on or got wrong

- **Framing.** The Gemini survey organized by application concern (sim-to-real, hybrid control, distributional, sample efficiency, quantum) and leaned on 2022 to 2026 applied papers, several from ResearchGate or paywalled venues. The Claude survey organized by algorithmic thread (model-based, pixels, evolutionary, interpretable, safety, sim-to-real, reproducibility) and leaned on 2018 to 2021 arXiv papers. Neither is wrong; the merged section 2 uses the Claude structure and folds the Gemini entries into it.
- **Interpretability.** Both appended a general XAI section; the Gemini version made cart-pole-specific claims (SHAP shows angular velocity dominates; visual agents track the score counter; concept whitening pins single neurons to pole velocity) without primary citations. They are plausible and testable but are treated here as hypotheses for the Phase 3 attribution script, not as findings.
- **Overlap.** Both cited the IEEE 2024 empirical study and the Gymnasium docs. Both mentioned sim-to-real, but with disjoint citations (NFQ2.0 and the DDPG parametric study versus the 2026 zero-shot paper), which are complementary rather than duplicates.
- **Gemini's "NFQ2.0" and Claude's "arXiv 2026 zero-shot transfer"** were both verified against arXiv (2511.12644 and 2606.22145). **Gemini's "LBF with DDPG, World Scientific 2026"** could not be retrieved and its exact claims are unverified. **Gemini's DDPG figures** ("90% mass variation", "fewer than 40 episodes") come from a ResearchGate listing and are unverified.
- The Gemini file's original "would you like me to..." trailers and the Claude file's summary table were dropped; the summary table's content is in section 2 and the plan in section 3.

## 5. References

Verified primary sources are listed first, then the survey-supplied links carried over as given.

**Benchmarks and protocols**

- Y. Duan, X. Chen, R. Houthooft, J. Schulman, P. Abbeel. "Benchmarking Deep Reinforcement Learning for Continuous Control." *ICML*, 2016. https://arxiv.org/abs/1604.06778v2
- P. Henderson, R. Islam, P. Bachman, J. Pineau, D. Precup, D. Meger. "Deep Reinforcement Learning that Matters." *AAAI*, 2018. https://arxiv.org/abs/1709.06560
- Y. Tassa et al. "DeepMind Control Suite." 2018. https://arxiv.org/abs/1801.00690
- "Empirical study of deep reinforcement learning algorithms for CartPole problem." *IEEE conference*, 2024. https://ieeexplore.ieee.org/document/10512107
- "Reinforcement Learning Control Strategies: Q-learning, SARSA, and Double Q-learning Performance for the Cart-Pole Problem." *IEEE conference*, 2025. https://ieeexplore.ieee.org/document/11099239
- "Implementation of Reinforcement Learning on Cart-Pole System Using Deep Q-Network, REINFORCE a Policy-Based, and Advanced Actor-Critic Methods." *IEEE conference*, 2025. https://ieeexplore.ieee.org/document/11350702
- "Review on Reinforcement Learning in CartPole Game." *IEEE conference*, 2022. https://ieeexplore.ieee.org/document/9990767
- S. Nagendra, N. Podila, R. Ugarakhod, K. George. "Comparison of Reinforcement Learning algorithms applied to the Cart Pole problem." 2017. https://arxiv.org/abs/1810.01940
- S. Lange, R. Hafner, M. Riedmiller. "NFQ2.0: The CartPole Benchmark Revisited." 2025. https://arxiv.org/abs/2511.12644
- J. P. Araújo, M. A. T. Figueiredo, M. A. Botto. "Control with adaptive Q-learning: A comparison for two classical control problems." *Engineering Applications of Artificial Intelligence*, 2022. https://www.sciencedirect.com/science/article/abs/pii/S0952197622000732 (preprint https://arxiv.org/abs/2011.02141)
- Farama Foundation. Gymnasium `CartPole-v1`. https://gymnasium.farama.org/environments/classic_control/cart_pole/

**Methods, 2018 to present**

- K. Chua, R. Calandra, R. McAllister, S. Levine. "Deep Reinforcement Learning in a Handful of Trials using Probabilistic Dynamics Models" (PETS). *NeurIPS*, 2018. https://arxiv.org/abs/1805.12114
- M. Janner, J. Fu, M. Zhang, S. Levine. "When to Trust Your Model: Model-Based Policy Optimization" (MBPO). *NeurIPS*, 2019. https://arxiv.org/abs/1906.08253
- D. Hafner, J. Pasukonis, J. Ba, T. Lillicrap. "Mastering Diverse Domains through World Models" (DreamerV3). 2023. https://arxiv.org/abs/2301.04104
- T. Kenneweg, P. Kenneweg, B. Hammer. "JEPA for RL: Investigating Joint-Embedding Predictive Architectures for Reinforcement Learning." *ESANN*, 2025. https://arxiv.org/abs/2504.16591
- W. Dabney, M. Rowland, M. Bellemare, R. Munos. "Distributional Reinforcement Learning with Quantile Regression" (QR-DQN). *AAAI*, 2018. https://arxiv.org/abs/1710.10044
- S. Fujimoto, H. van Hoof, D. Meger. "Addressing Function Approximation Error in Actor-Critic Methods" (TD3). *ICML*, 2018. https://arxiv.org/abs/1802.09477
- L. Chen et al. "Decision Transformer: Reinforcement Learning via Sequence Modeling." *NeurIPS*, 2021. https://arxiv.org/abs/2106.01345
- A. Gaier, D. Ha. "Weight Agnostic Neural Networks." *NeurIPS*, 2019. https://arxiv.org/abs/1906.04358
- D. Hein, S. Udluft, T. Runkler. "Interpretable Policies for Reinforcement Learning by Genetic Programming." 2018. https://arxiv.org/abs/1712.04170
- O. Bastani, Y. Pu, A. Solar-Lezama. "Verifiable Reinforcement Learning via Policy Extraction" (VIPER). *NeurIPS*, 2018. https://arxiv.org/abs/1805.08328
- Y. Chow, O. Nachum, E. Duenez-Guzman, M. Ghavamzadeh. "A Lyapunov-based Approach to Safe Reinforcement Learning." *NeurIPS*, 2018. https://arxiv.org/abs/1805.07708
- R. Cheng, G. Orosz, R. M. Murray, J. W. Burdick. "End-to-End Safe Reinforcement Learning through Barrier Functions for Safety-Critical Continuous Control Tasks." *AAAI*, 2019. https://arxiv.org/abs/1903.08792
- "Zero-shot Transfer of Reinforcement Learning Control Policies for the Swing-Up and Stabilization of a Cart-Pole System." 2026. https://arxiv.org/abs/2606.22145
- "Reachability Guarantees for Cart-Pole Swing-Up and Stabilization." 2026. https://arxiv.org/html/2606.28627
- Z. T. Wang, Y. Ashida, M. Ueda. "Deep reinforcement learning control of quantum cartpoles." *Phys. Rev. Lett.*, 2020. https://arxiv.org/abs/1910.09200
- C. D. Freeman et al. "Brax: A Differentiable Physics Engine for Large Scale Rigid Body Simulation." 2021. https://arxiv.org/abs/2106.13281
- R. T. Lange. gymnax. https://github.com/RobertTLange/gymnax

**Carried over from the surveys, not verified**

- Logarithmic barrier function with DDPG for cart-pole swing-up, *Unmanned Systems* (World Scientific), 2026. https://www.worldscientific.com/doi/10.1142/S2301385026410074
- "A Parametric Study of a Deep Reinforcement Learning Control System Applied to the Swing-Up Problem of the Cart-Pole." 2020. https://www.researchgate.net/publication/347683580
- "Swing-Up and Balance Control of Cart-Pole Based on Reinforcement Learning DDPG." Springer, 2023. https://link.springer.com/chapter/10.1007/978-981-99-1549-1_33
- "A Review of Deep Reinforcement Learning Algorithms and Comparative Results on Inverted Pendulum System." https://www.academia.edu/72820412
- Weights & Biases, "Comparison of Four Reinforcement Learning Methods on CartPole-v1." https://wandb.ai/evansnyanney-ohio-university/rl_algorithm_zoo/reports/Comparison-of-Four-Reinforcement-Learning-Methods-on-CartPole-v1--VmlldzoxMjEwMzE3MQ
- "Mastering CartPole: a complete journey through 6 reinforcement learning algorithms." Medium. https://medium.com/@sachith.icc/mastering-cartpole-a-complete-journey-through-6-reinforcement-learning-algorithms-06d92fa6d601
- Concept whitening explainer. https://bdtechtalks.com/2021/01/11/concept-whitening-interpretable-neural-networks/
- Mechanistic interpretability survey cited by the Gemini survey. https://arxiv.org/abs/2511.19265
