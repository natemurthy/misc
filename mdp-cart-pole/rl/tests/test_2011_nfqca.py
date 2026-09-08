"""Tests for the 2011 neural fitted Q iteration with continuous actions (Hafner and Riedmiller): the shared agent interface."""

import pytest

from interface_checks import AgentInterfaceTests

pytest.importorskip("torch")


class TestInterface(AgentInterfaceTests):
    solution = "2011_nfqca"

    # these two refit both networks on 20-episode trainings (0.1-0.2 s), over the fast threshold
    @pytest.mark.slow
    def test_snapshot_restore_round_trip(self):
        super().test_snapshot_restore_round_trip()

    @pytest.mark.slow
    def test_same_seed_same_training_trajectory(self):
        super().test_same_seed_same_training_trajectory()
