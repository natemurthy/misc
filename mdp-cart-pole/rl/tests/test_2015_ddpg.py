"""Tests for the 2015 deep deterministic policy gradient (Lillicrap et al.): the shared agent interface."""

import pytest

from interface_checks import AgentInterfaceTests

pytest.importorskip("torch")


class TestInterface(AgentInterfaceTests):
    solution = "2015_ddpg"
