"""
2005: Peters, Vijayakumar & Schaal's Natural Actor-Critic (NAC).

Reference
    J. Peters, S. Vijayakumar, S. Schaal, "Natural Actor-Critic", Proc. 16th
    European Conference on Machine Learning (ECML 2005), LNAI 3720, pp. 280-291.
    https://homepages.inf.ed.ac.uk/svijayak/publications/peters-ECML2005.pdf
    J. Peters, S. Schaal, "Natural Actor-Critic", Neurocomputing 71(7-9):
    1180-1190, 2008 (the journal version, same algorithm, more experiments).
    Background: S. Amari, "Natural gradient works efficiently in learning",
    Neural Computation 1998; S. Kakade, "A natural policy gradient", NIPS 2001;
    R. Sutton, D. McAllester, S. Singh, Y. Mansour, "Policy gradient methods
    for RL with function approximation", NIPS 2000 (compatible function
    approximation); J. Boyan, "Least-squares temporal difference learning",
    ICML 1999 / Machine Learning 2002 (LSTD).

What changed from REINFORCE (1992) and the actor-critics (1983, 1986)
    REINFORCE follows the plain gradient of the return, estimated from whole
    episodes with high variance. The 1983/1986 actor-critics use a critic's TD
    error as the reinforcement but also step along the plain gradient. NAC
    changes the direction, not just the estimator: it follows Amari's natural
    gradient G^-1 grad J, the steepest ascent under the Fisher metric of the
    policy, which is invariant to how the policy is parameterized and does not
    stall on the plateaus that flatten the plain gradient.

    The paper's central observation is that the natural gradient comes for
    free from the critic. If the critic approximates the advantage with the
    *compatible* features of Sutton et al. (2000),

        A(s, a) ~= grad_theta log pi(a | s) . w,

    then the policy gradient is grad J = F w with F the Fisher matrix, and so
    the natural gradient is simply F^-1 F w = w. No Fisher matrix is ever
    formed or inverted. The critic's weights ARE the update direction.

    The compatible approximator is mean-zero over actions, so it cannot be
    learned by ordinary TD bootstrapping on its own. Writing the Bellman
    equation as Q(s,a) = A(s,a) + V(s) = r + gamma V(s') and giving V its own
    linear basis phi(s) turns it into one linear regression in [w; v], which
    the paper solves with LSTD-Q(lambda): accumulate sufficient statistics
    (A, b) with an eligibility trace z and solve once, instead of stepping
    a TD critic with a learning rate.

Algorithm (Table 1 of the ECML paper, "Natural Actor-Critic with LSTD-Q(lambda)")
    for each step t, with action u_t ~ pi(. | x_t), reward r_t, next state x_t+1:
        phi_hat   = [phi(x_t);   grad_theta log pi(u_t | x_t)]      (critic basis)
        phi_tilde = [phi(x_t+1); 0]                                (next-state basis)
        z <- lambda z + phi_hat
        A <- A + z (phi_hat - gamma phi_tilde)^T
        b <- b + z r_t
        [v; w] = A^-1 b                                            (critic)
        if angle(w_t+1, w_t-tau) <= epsilon:                       (converged?)
            theta <- theta + alpha w                               (actor)
            z <- beta z,  A <- beta A,  b <- beta b                (forget)
    phi_tilde has a zero block in the policy part because the next action is
    not yet drawn; that is what makes it LSTD-Q(lambda) rather than SARSA-like
    LSTD on state-action features, and it is why the regression inputs are not
    contaminated by the noise of u_t+1.

Policy used here (the paper's own cart-pole choice)
    Gaussian with a mean linear in the normalized state plus a bias and a
    learned standard deviation, pi(u | s) = N(u | theta_mu . phi(s), sigma^2),
    sigma = sigmoid(xi) as in the paper's theta = [k; xi]. The force is the
    sample clipped to [-1, 1]; the score function uses the unclipped sample,
    so the clip is part of the environment as far as the gradient is
    concerned. Frozen, the agent applies the mean.

Deviations
    * The critic is solved once per episode rather than after every step, and
      the angle test compares consecutive per-episode solutions. A policy step
      is also forced after `update_every` episodes so a noisy direction cannot
      stall the actor forever, and no step is taken while the (forgetting-
      weighted) sample count behind A and b is below `min_steps`: a 21-
      parameter regression on ten transitions is not a gradient estimate.
    * A small ridge term is added to A before the solve; the paper inverts A.
    * Rewards are scaled by reward_scale so that the value function's targets
      are O(1) with the +1-per-step reward; the natural gradient scales with
      the reward, so alpha is tuned jointly with it.
    * sigma is floored at sigma_min so that the Fisher metric, which grows as
      1/sigma^2, stays finite and the actor keeps exploring.
    The episodic variant (eNAC, Table 2) fits one regression per batch of
    roll-outs with a single scalar baseline J; the per-step LSTD-Q(lambda)
    variant is the one implemented because it is the one the paper derives
    the algorithm from, and the state-dependent baseline V(s) is what the
    1983/1986 critics in this lineage already provide.
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import BaseAgent, normalize_obs  # noqa: E402

_IU = np.triu_indices(4)  # the 10 distinct quadratic monomials of the 4 state variables


def _sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


class NaturalActorCriticAgent(BaseAgent):
    name = "2005_nac"
    continuous_actions = True    # act() returns a force fraction in [-1, 1]
    supports_wide_angles = True  # reads the raw scaled state; no 12-degree decoder or grid

    def __init__(self, alpha=1.0, gamma=0.99, lam=0.5, beta=0.5, epsilon=0.35, update_every=10, min_steps=100,
                 ridge=1e-3, reward_scale=0.01, sigma0=0.4, sigma_min=0.05, seed=None):
        super().__init__(seed)
        self.alpha, self.gamma, self.lam, self.beta = alpha, gamma, lam, beta
        self.epsilon, self.update_every, self.min_steps, self.ridge = epsilon, update_every, min_steps, ridge
        self.reward_scale, self.sigma0, self.sigma_min = reward_scale, sigma0, sigma_min
        self.n_pol = 6                              # 5 mean weights + xi
        self.n_val = 1 + 4 + len(_IU[0])            # 1, s, s_i s_j  (15)
        n = self.n_pol + self.n_val
        # actor: theta = [mean weights (5), xi] with sigma = sigmoid(xi)
        self.theta = np.zeros(self.n_pol)
        self.theta[-1] = np.log(sigma0 / (1.0 - sigma0))
        # critic: LSTD-Q(lambda) sufficient statistics and its last solution [v; w]
        self.A = np.zeros((n, n))
        self.b = np.zeros(n)
        self.z = np.zeros(n)
        self.v = np.zeros(self.n_val)
        self.w = np.zeros(self.n_pol)
        self.n = 0.0                                # forgetting-weighted sample count behind A, b
        self._w_prev = None
        self._since_update = 0
        self._last_angle = 0.0
        self._raw = None                            # unclipped sample behind the last act()

    # ---- features and policy --------------------------------------------- #
    @staticmethod
    def _policy_features(obs):
        return np.append(normalize_obs(obs), 1.0)

    @staticmethod
    def _value_features(obs):
        s = normalize_obs(obs)
        return np.concatenate(([1.0], s, np.outer(s, s)[_IU]))

    @property
    def sigma(self):
        return max(float(_sigmoid(self.theta[-1])), self.sigma_min)

    def mean(self, obs):
        return float(self.theta[:-1] @ self._policy_features(obs))

    def score(self, obs, u):
        """grad_theta log pi(u | s) for the Gaussian with sigma = sigmoid(xi)."""
        phi = self._policy_features(obs)
        sigma = self.sigma
        eps = (u - self.theta[:-1] @ phi) / sigma
        # d log N / d sigma = (eps^2 - 1) / sigma ;  d sigma / d xi = sigma (1 - sigma)
        return np.append(eps / sigma * phi, (eps * eps - 1.0) * (1.0 - sigma))

    def act(self, obs):
        mu = self.mean(obs)
        if self.frozen:
            return float(np.clip(mu, -1.0, 1.0))
        self._raw = mu + self.sigma * self.rng.standard_normal()
        return float(np.clip(self._raw, -1.0, 1.0))

    # ---- critic: LSTD-Q(lambda) statistics, one step ------------------------ #
    def _learn(self, obs, action, reward, next_obs, terminated):
        # use the unclipped sample when learn() follows the act() that produced it
        u = self._raw if self._raw is not None and float(np.clip(self._raw, -1, 1)) == action else action
        phi_hat = np.concatenate((self._value_features(obs), self.score(obs, u)))
        phi_tilde = np.zeros_like(phi_hat)
        if not terminated:
            phi_tilde[:self.n_val] = self._value_features(next_obs)
        self.z = self.lam * self.z + phi_hat
        self.A += np.outer(self.z, phi_hat - self.gamma * phi_tilde)
        self.b += self.z * (reward * self.reward_scale)
        self.n += 1.0

    def solve(self):
        """Critic parameters [v; w] = (A + ridge I)^-1 b; w is the natural gradient estimate."""
        n = self.A.shape[0]
        sol = np.linalg.solve(self.A + self.ridge * np.eye(n), self.b)
        self.v, self.w = sol[:self.n_val], sol[self.n_val:]
        return self.w

    # ---- actor: natural gradient step when the direction has settled -------- #
    def _end_episode(self):
        self.z[:] = 0.0                              # traces do not cross episode boundaries
        w = self.solve()
        self._since_update += 1
        if self._w_prev is not None:
            denom = np.linalg.norm(w) * np.linalg.norm(self._w_prev)
            cos = (w @ self._w_prev) / denom if denom > 0 else 1.0
            self._last_angle = float(np.arccos(np.clip(cos, -1.0, 1.0)))
        converged = self._w_prev is not None and self._last_angle <= self.epsilon
        if (converged or self._since_update >= self.update_every) and self.n >= self.min_steps:
            self.theta += self.alpha * w
            self.A *= self.beta
            self.b *= self.beta
            self.n *= self.beta
            self._since_update = 0
            self._w_prev = None
        else:
            self._w_prev = w.copy()

    # ---- bookkeeping ------------------------------------------------------ #
    def stats(self):
        return {"sigma": self.sigma, "|w|": float(np.linalg.norm(self.w)), "angle": self._last_angle}

    def hparams(self):
        return dict(alpha=self.alpha, gamma=self.gamma, lam=self.lam, beta=self.beta, epsilon=self.epsilon,
                    update_every=self.update_every, min_steps=self.min_steps, ridge=self.ridge,
                    reward_scale=self.reward_scale, sigma0=self.sigma0, sigma_min=self.sigma_min)

    def state_dict(self):
        return {"theta": self.theta, "v": self.v, "w": self.w}

    def load_state_dict(self, d):
        self.theta = np.array(d["theta"], dtype=np.float64)
        self.v = np.array(d["v"], dtype=np.float64)
        self.w = np.array(d["w"], dtype=np.float64)


Agent = NaturalActorCriticAgent
