"""Tests for the 2013 deep Q-network (Mnih et al.): the shared agent interface."""

import pytest

from interface_checks import AgentInterfaceTests

pytest.importorskip("torch")


class TestInterface(AgentInterfaceTests):
    solution = "2013_dqn"
