"""Tests for the 2017 proximal policy optimization (Schulman et al.): the shared agent interface."""

import pytest

from interface_checks import AgentInterfaceTests

pytest.importorskip("torch")


class TestInterface(AgentInterfaceTests):
    solution = "2017_ppo"
