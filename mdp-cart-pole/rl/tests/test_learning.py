"""
Integration tests: each solution must actually learn to balance the pole.

Every agent is trained headlessly from scratch with a fixed seed on the
full-range start distribution (pole angle uniform in +/-12 degrees) for a
budget of episodes calibrated per method, keeping the best checkpoint. The
frozen policy is then run from Gymnasium's default near-upright start and must
survive on average at least LEARN_THRESHOLD steps, roughly five times the
random baseline (~22). These are marked `slow`; run only the quick tests with

    pytest -m fast

The budgets are deliberately small so the whole file runs in well under a
minute. They are not the recommended training lengths; main.py's default is
5000 episodes.
"""

import numpy as np
import pytest

from rl_helpers import LEARN_THRESHOLD, evaluate, load_agent_class, train

# episodes needed, with seed 0, to clear LEARN_THRESHOLD with margin
BUDGET = {
    "1983_actor_critic": 1000,
    "1986_actor_critic_backprop": 400,
    "1988_td": 600,
    "1989_qlearning": 800,
    "1990_dyna": 600,
    "1992_reinforce": 400,
    # Short on purpose: the continuous agent's greedy policy and its noisy training
    # policy only agree once the exploration noise has decayed (~2000 episodes),
    # so the frozen evaluation is not monotone in the budget at this scale.
    "1999_qlearning_continuous": 300,  # with TEST_KWARGS below (sequential replay); see note there
    "2005_nac": 500,    # reaches 500 by ~400 on seed 0; 500 leaves margin
    "2007_cacla": 800,  # learning starts abruptly around episode 450 on seed 0; 800 sits on the plateau (~180), not the cliff
    # PyTorch solutions (skipped without torch). Budgets calibrated on seed 0.
    "2011_nfqca": 300,
    "2011_pilco": 6,    # balances from its third trial; with TEST_KWARGS below the fits stop after episode 4
    "2013_dqn": 1500,  # first update at 1000 transitions; reaches the cap around episode 1500 on seed 0
    "2015_ddpg": 500,
    "2015_trpo": 600,
    "2017_ppo": 500,
    "2018_sac": 400,
}


# Constructor overrides for the learning test only. The 1999 agent's default batched
# replay is faster per second but learns later and more seed-dependently on the 12 degree
# task (500-step cap at episode ~1400-3800 depending on seed, sometimes not within 2500);
# its one-at-a-time replay mode learns within 300 episodes on seed 0, which keeps this
# suite fast. The default path is still exercised by the CLI and interface tests.
TEST_KWARGS = {
    "1999_qlearning_continuous": {"batched_replay": False},
    # PILCO refits its GP at every episode end until max_fits; the default 15 fits take ~45 s and
    # the controller is already good after two, so four fits demonstrate learning at a quarter of the cost.
    "2011_pilco": {"max_fits": 4},
}


@pytest.mark.slow
def test_solution_learns_to_balance(solution_name):
    # the raw class, not the `agent_class` fixture: that one hands PILCO a pre-fitted model for the
    # interface tests, and this test must learn from scratch
    agent = load_agent_class(solution_name)(seed=0, **TEST_KWARGS.get(solution_name, {}))
    rets = train(agent, episodes=BUDGET[solution_name], seed=0)
    # the first few episodes are at most warm-up; some methods (NFQCA) already improve within 50.
    # PILCO is exempt: it balances from its third trial, which is the point of the method.
    if solution_name != "2011_pilco":
        assert np.mean(rets[:10]) < 60, "sanity: untrained policy should not already balance"
    score = evaluate(agent, episodes=10, seed=99)
    assert score >= LEARN_THRESHOLD, (
        f"{solution_name}: frozen policy averaged {score:.1f} steps after "
        f"{BUDGET[solution_name]} episodes (threshold {LEARN_THRESHOLD})"
    )
