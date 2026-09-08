"""
2011: PILCO, probabilistic inference for learning control (Deisenroth and Rasmussen).

Reference
    M. P. Deisenroth, C. E. Rasmussen, "PILCO: A Model-Based and Data-Efficient
    Approach to Policy Search", ICML 2011.
    https://mlg.eng.cam.ac.uk/pub/pdf/DeiRas11.pdf
    M. P. Deisenroth, D. Fox, C. E. Rasmussen, "Gaussian Processes for
    Data-Efficient Learning in Robotics and Control", IEEE TPAMI 37(2), 2015
    (the long version, with the cart-pole settings used here).
    J. Quinonero-Candela, A. Girard, C. E. Rasmussen, "Prediction at an
    uncertain input for Gaussian processes and relevance vector machines",
    ICASSP 2003 (moment matching through a GP).

What changed from Dyna (1990) and NFQCA (2011)
    Dyna learned a sample model and used it to run more Q-learning updates.
    PILCO learns a model too, but a *probabilistic* one, a Gaussian process
    per state dimension over (state, action) -> state change with a squared
    exponential ARD kernel, and uses it not for more value updates but to
    evaluate a policy directly: the Gaussian state distribution is pushed
    through the GP and the controller for T steps with exact moment matching,
    every step's expected saturating cost is summed, and that expected
    long-term cost J(theta) is minimized by gradient descent on the policy
    parameters. Model uncertainty is part of the prediction, so a policy that
    drives the system where the model is ignorant is penalized by the spread
    it creates rather than trusted (model bias). No value function is learned.
    Where NFQCA fits a critic on every transition ever seen, PILCO's whole
    point is that a handful of trials suffice: the paper's real cart-pole
    swing-up needed 17.5 s of interaction.

Algorithm (Deisenroth & Rasmussen 2011, Alg. 1)
    trial 1: apply random controls (held for 0.1 s), record (x, u) -> x'
    repeat for each subsequent trial:
        fit the GP dynamics model: one SE-ARD GP per state dimension on the
            differences x' - x, hyperparameters by marginal likelihood
        policy search: from x0 ~ N(mu0, S0), for t = 1..T
            u_t = squash(w . x_t + b) with the Gaussian moments of (x_t, u_t)
            (x_t, u_t) -> Delta_t through the GP by moment matching
            x_{t+1} = x_t + Delta_t, accumulate E[c(x_{t+1})],
            c(x) = 1 - exp(-d(x)^2 / (2 sigma_c^2)),  d^2 = x^2 + (L theta)^2
        minimize J = sum_t E[c(x_t)] over (w, b) with L-BFGS on autograd
        apply the new policy for one trial and record the data
    stop after `max_fits` trials; the controller is then fixed.
"""

import math
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common.deep import TorchAgent  # noqa: E402
from common.features import STATE_SCALE  # noqa: E402

DT = torch.float64
POLE_LENGTH = 1.0   # full pole length in meters (the environment's `length` is the half length)
JITTER = 1e-6


class _Policy(nn.Module):
    """Linear preliminary controller v = w . x + b on the normalized state, squashed to [-1, 1]."""

    def __init__(self, gen):
        super().__init__()
        self.w = nn.Parameter(0.3 * torch.randn(4, generator=gen, dtype=DT))
        self.b = nn.Parameter(torch.zeros((), dtype=DT))

    @staticmethod
    def squash(v):
        """PILCO's saturating function (9 sin v + sin 3v) / 8, bounded in [-1, 1] and flat at +/-pi/2."""
        return (9.0 * torch.sin(v) + torch.sin(3.0 * v)) / 8.0

    def forward(self, x):
        v = torch.clamp(self.w @ x + self.b, -math.pi / 2, math.pi / 2)
        return self.squash(v)


class _GP(nn.Module):
    """
    Four independent GPs (one per state dimension) with zero mean and SE-ARD kernels on the
    5-d input (normalized state, action), predicting the normalized state difference.
    The training set is stored as buffers so it is saved with the model.
    """

    def __init__(self, n_out=4, n_in=5):
        super().__init__()
        self.log_ell = nn.Parameter(torch.zeros(n_out, n_in, dtype=DT))            # length-scales, per GP
        self.log_sf = nn.Parameter(torch.zeros(n_out, dtype=DT))                   # signal std
        self.log_sn = nn.Parameter(torch.full((n_out,), math.log(0.05), dtype=DT))  # noise std
        self.register_buffer("X", torch.zeros(0, n_in, dtype=DT))
        self.register_buffer("Y", torch.zeros(0, n_out, dtype=DT))

    def set_data(self, X, Y):
        self.X, self.Y = X.to(DT), Y.to(DT)

    def kernel(self, A, B):
        """(n_out, |A|, |B|) SE-ARD kernel matrices."""
        iL = torch.exp(-self.log_ell)                              # (D, E) inverse length-scales
        a = A[None] * iL[:, None, :]
        b = B[None] * iL[:, None, :]
        d2 = (a * a).sum(-1)[:, :, None] + (b * b).sum(-1)[:, None, :] - 2.0 * a @ b.transpose(1, 2)
        return torch.exp(2.0 * self.log_sf)[:, None, None] * torch.exp(-0.5 * d2.clamp_min(0.0))

    def chol(self):
        n = self.X.shape[0]
        K = self.kernel(self.X, self.X) + (torch.exp(2.0 * self.log_sn) + JITTER)[:, None, None] * torch.eye(n, dtype=DT)
        return torch.linalg.cholesky(K)

    def nlml(self):
        """Negative log marginal likelihood summed over the GPs, plus PILCO's soft bounds on the
        hyperparameters (length-scales within 100x of unit scale, signal-to-noise below 1000)."""
        L = self.chol()
        y = self.Y.T[:, :, None]
        alpha = torch.cholesky_solve(y, L)
        nll = 0.5 * (y * alpha).sum() + torch.log(torch.diagonal(L, dim1=1, dim2=2)).sum()
        curb = ((self.log_ell / math.log(100.0)) ** 30).sum() + (((self.log_sf - self.log_sn) / math.log(1000.0)) ** 30).sum()
        return nll + curb

    def posterior(self):
        """beta = (K + sn^2 I)^-1 y  (D, n)  and  iK = (K + sn^2 I)^-1  (D, n, n), for prediction."""
        L = self.chol()
        n = L.shape[-1]
        iK = torch.cholesky_solve(torch.eye(n, dtype=DT).expand(L.shape[0], n, n), L)
        beta = (iK @ self.Y.T[:, :, None]).squeeze(-1)
        return beta, iK

    def predict_gaussian(self, mu, S, beta, iK):
        """
        Moment matching (Deisenroth & Rasmussen 2011, Sec. 2.2; Quinonero-Candela et al. 2003):
        for a Gaussian input N(mu, S) return the exact mean M (D,), covariance V (D, D) of the
        GP prediction and C = S^-1 cov[input, output] (E, D).
        """
        D, E = self.log_ell.shape
        eyeE = torch.eye(E, dtype=DT)
        nu = self.X - mu                                              # (n, E)   x_i - mu
        Lam = torch.exp(2.0 * self.log_ell)                           # (D, E)   squared length-scales
        iL = torch.exp(-2.0 * self.log_ell)                           # (D, E)   Lambda^-1
        # mean, Eqs. (13)-(16): q_i = sf^2 |S Lambda^-1 + I|^-1/2 exp(-1/2 nu_i (S + Lambda)^-1 nu_i)
        SL = S[None] + torch.diag_embed(Lam)                          # (D, E, E)  S + Lambda
        t = torch.linalg.solve(SL, nu.T[None]).transpose(1, 2)       # (D, n, E)  nu_i (S + Lambda)^-1
        logc = 2.0 * self.log_sf + self.log_ell.sum(1) - 0.5 * torch.linalg.slogdet(SL)[1]
        q = torch.exp(logc[:, None] - 0.5 * (t * nu[None]).sum(-1))  # (D, n)
        bq = beta * q
        M = bq.sum(1)                                                 # (D,)
        C = (bq[:, :, None] * t).sum(1).T                             # (E, D)   S^-1 cov[x~, Delta]
        # covariance, Eqs. (17)-(23): Q_ij = k_a(x_i, mu) k_b(x_j, mu) |R|^-1/2 exp(1/2 z_ij^T R^-1 S z_ij)
        inp = nu[None] * iL[:, None, :]                              # (D, n, E)  nu_i Lambda_a^-1
        logk = 2.0 * self.log_sf[:, None] - 0.5 * (inp * nu[None]).sum(-1)   # (D, n)  log k_a(x_i, mu)
        R = S[None, None] * (iL[:, None, None, :] + iL[None, :, None, :]) + eyeE   # (D, D, E, E)
        Qm = 0.5 * torch.linalg.solve(R, S.expand(D, D, E, E))       # (D, D, E, E)  R^-1 S / 2, symmetric
        P = torch.einsum("ane,abef->abnf", inp, Qm)                   # z_a,i^T Qm
        diag_a = torch.einsum("abnf,anf->abn", P, inp)                # (D, D, n)
        diag_b = diag_a.transpose(0, 1)                               # z_b,j^T Qm z_b,j
        cross = torch.einsum("abif,bjf->abij", P, inp)                # (D, D, n, n)
        logQ = (logk[:, None, :, None] + logk[None, :, None, :]
                + diag_a[:, :, :, None] + diag_b[:, :, None, :] + 2.0 * cross)
        Q = torch.exp(logQ - 0.5 * torch.linalg.slogdet(R)[1][:, :, None, None])
        V = torch.einsum("ai,abij,bj->ab", beta, Q, beta) - M[:, None] * M[None, :]
        extra = torch.exp(2.0 * self.log_sf) - torch.einsum("aij,aaij->a", iK, Q)   # E[var_f], Eq. (23)
        V = V + torch.diag_embed(extra)
        return M, 0.5 * (V + V.T), C


class PILCOAgent(TorchAgent):
    name = "2011_pilco"
    continuous_actions = True
    supports_wide_angles = True

    def __init__(self, hold=5, horizon=30, max_fits=15, random_trials=1, n_max=200, sigma_c=0.25,
                 theta0_std_deg=10.0, gp_iters=40, policy_iters=40, seed=None):
        super().__init__(seed)
        self.hold, self.horizon, self.max_fits, self.random_trials = hold, horizon, max_fits, random_trials
        self.n_max, self.sigma_c, self.theta0_std_deg = n_max, sigma_c, theta0_std_deg
        self.gp_iters, self.policy_iters = gp_iters, policy_iters
        self.policy = _Policy(self.gen)
        self.gp = _GP()
        self.register(policy=self.policy, gp=self.gp)
        self.scale = torch.as_tensor(STATE_SCALE, dtype=DT)
        # saturating cost on the pole-tip-like distance d^2 = x^2 + (L theta)^2, in normalized coordinates
        w = torch.tensor([STATE_SCALE[0] ** 2, 0.0, (POLE_LENGTH * STATE_SCALE[2]) ** 2, 0.0], dtype=DT) / sigma_c ** 2
        self.W = torch.diag(w)
        # initial state distribution for planning: Gymnasium's +/-0.05 box, pole angle wide
        s0 = np.array([0.03, 0.03, math.radians(theta0_std_deg), 0.03]) / STATE_SCALE
        self.S0 = torch.diag(torch.as_tensor(s0 ** 2, dtype=DT))
        self.data_x, self.data_u, self.data_y = [], [], []   # all recorded 0.1 s transitions (raw units)
        self.episodes, self.fits = 0, 0
        self._u, self._left, self._x_hold, self._steps_in_hold = 0.0, 0, None, 0
        self._J, self._nlml = 0.0, 0.0

    # ---- acting: one command per `hold` environment steps while learning ----- #
    def _policy_action(self, obs):
        with torch.no_grad():
            x = torch.as_tensor(np.asarray(obs, dtype=np.float64), dtype=DT) / self.scale
            return float(self.policy(x))

    def act(self, obs):
        if self.frozen or self.episodes >= self.max_fits:
            # deployed controller: state feedback applied at every 20 ms step. The hold below
            # exists so that recorded transitions match the model's 0.1 s time step.
            return self._policy_action(obs)
        if self._left == 0:
            if self.episodes < self.random_trials:
                self._u = float(self.rng.uniform(-1.0, 1.0))
            else:
                self._u = self._policy_action(obs)
            self._left = self.hold
            self._x_hold, self._steps_in_hold = np.asarray(obs, dtype=np.float64), 0
        self._left -= 1
        return self._u

    # ---- data: (state at the start of a hold, command) -> state after the hold -- #
    def _learn(self, obs, action, reward, next_obs, terminated):
        if self.episodes >= self.max_fits or self._x_hold is None:
            return
        self._steps_in_hold += 1
        if self._steps_in_hold == self.hold:
            self.data_x.append(self._x_hold)
            self.data_u.append(float(action))
            self.data_y.append(np.asarray(next_obs, dtype=np.float64) - self._x_hold)
            self._x_hold = None

    def _end_episode(self):
        self.episodes += 1
        self._left, self._x_hold = 0, None
        if self.episodes <= self.max_fits and len(self.data_x) >= 2:
            self.fit()

    # ---- the PILCO loop body: refit the GP, then optimize the policy on it ------- #
    def _select_data(self):
        """Farthest-point subsample of the recorded transitions to at most n_max, deterministic."""
        Z = np.concatenate([np.array(self.data_x) / STATE_SCALE, np.array(self.data_u)[:, None]], axis=1)
        Y = np.array(self.data_y) / STATE_SCALE
        if len(Z) > self.n_max:
            chosen = [0]
            dist = np.sum((Z - Z[0]) ** 2, axis=1)
            for _ in range(self.n_max - 1):
                i = int(np.argmax(dist))
                chosen.append(i)
                dist = np.minimum(dist, np.sum((Z - Z[i]) ** 2, axis=1))
            Z, Y = Z[chosen], Y[chosen]
        self.gp.set_data(torch.as_tensor(Z, dtype=DT), torch.as_tensor(Y, dtype=DT))

    def fit(self):
        self._select_data()
        self._nlml = self._optimize(self.gp.parameters(), self.gp.nlml, self.gp_iters)
        with torch.no_grad():
            beta, iK = self.gp.posterior()
        self._J = self._optimize(self.policy.parameters(), lambda: self.expected_cost(beta, iK), self.policy_iters)
        self.fits += 1

    @staticmethod
    def _optimize(params, objective, iters):
        """L-BFGS with a strong-Wolfe line search (PILCO used CG/L-BFGS); keeps the old parameters
        if the fit produced a non-finite objective."""
        params = list(params)
        backup = [p.detach().clone() for p in params]
        opt = torch.optim.LBFGS(params, lr=1.0, max_iter=iters, line_search_fn="strong_wolfe",
                                tolerance_grad=1e-9, tolerance_change=1e-12)

        def closure():
            opt.zero_grad()
            loss = objective()
            if not torch.isfinite(loss):
                return loss.detach()
            loss.backward()
            return loss

        opt.step(closure)
        with torch.no_grad():
            value = objective()
            if not torch.isfinite(value) or not all(torch.isfinite(p).all() for p in params):
                for p, b in zip(params, backup):
                    p.copy_(b)
                value = objective()
        return float(value)

    # ---- policy evaluation by moment matching ---------------------------------- #
    def control_moments(self, mu, S):
        """Gaussian moments of u = squash(v), v = w . x + b ~ N(m, s2), with cov[x, u] by Stein's lemma."""
        w, b = self.policy.w, self.policy.b
        m = w @ mu + b
        s2 = (w @ S @ w).clamp_min(1e-12)
        cxv = S @ w
        e = lambda k: torch.exp(-0.5 * k * k * s2)  # noqa: E731  E[cos(k v)] / cos(k m)
        mu_u = (9.0 * torch.sin(m) * e(1) + torch.sin(3.0 * m) * e(3)) / 8.0
        # E[u^2] from products of sines: sin(a) sin(b) = (cos(a-b) - cos(a+b)) / 2
        e_u2 = (81.0 * 0.5 * (1.0 - torch.cos(2.0 * m) * e(2))
                + 18.0 * 0.5 * (torch.cos(2.0 * m) * e(2) - torch.cos(4.0 * m) * e(4))
                + 0.5 * (1.0 - torch.cos(6.0 * m) * e(6))) / 64.0
        var_u = (e_u2 - mu_u * mu_u).clamp_min(1e-12)
        dg = (9.0 * torch.cos(m) * e(1) + 3.0 * torch.cos(3.0 * m) * e(3)) / 8.0   # E[squash'(v)]
        return mu_u, var_u, cxv * dg

    def step_moments(self, mu, S, beta, iK):
        """One 0.1 s step of the Gaussian state distribution through policy and GP (Eqs. 10-12)."""
        mu_u, var_u, cxu = self.control_moments(mu, S)
        mu_t = torch.cat([mu, mu_u[None]])
        S_t = torch.cat([torch.cat([S, cxu[:, None]], 1), torch.cat([cxu, var_u[None]])[None]], 0)
        S_t = S_t + JITTER * torch.eye(5, dtype=DT)
        M, V, C = self.gp.predict_gaussian(mu_t, S_t, beta, iK)
        cov_xd = (S_t @ C)[:4]                                       # cov[x_t, Delta_t]
        S_next = S + V + cov_xd + cov_xd.T
        return mu + M, 0.5 * (S_next + S_next.T)

    def expected_saturating_cost(self, mu, S):
        """E[1 - exp(-1/2 x^T W x)] for x ~ N(mu, S), in closed form."""
        A = torch.eye(4, dtype=DT) + S @ self.W
        quad = mu @ self.W @ torch.linalg.solve(A, mu)
        return 1.0 - torch.exp(-0.5 * quad) / torch.sqrt(torch.linalg.det(A))

    def expected_cost(self, beta, iK):
        mu, S = torch.zeros(4, dtype=DT), self.S0.clone()
        J = torch.zeros((), dtype=DT)
        for _ in range(self.horizon):
            mu, S = self.step_moments(mu, S, beta, iK)
            J = J + self.expected_saturating_cost(mu, S)
        return J

    # ---- bookkeeping ------------------------------------------------------------ #
    def load_state_dict(self, d):
        self.gp.set_data(torch.as_tensor(np.array(d["gp.X"])), torch.as_tensor(np.array(d["gp.Y"])))
        super().load_state_dict(d)

    def stats(self):
        return {"J": self._J / max(1, self.horizon), "nlml": self._nlml, "data": float(len(self.data_x)),
                "fits": float(self.fits)}

    def hparams(self):
        return dict(hold=self.hold, horizon=self.horizon, max_fits=self.max_fits, random_trials=self.random_trials,
                    n_max=self.n_max, sigma_c=self.sigma_c, theta0_std_deg=self.theta0_std_deg,
                    gp_iters=self.gp_iters, policy_iters=self.policy_iters)


Agent = PILCOAgent
