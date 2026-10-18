"""Tests for the 2018 soft actor-critic (Haarnoja et al.): the shared agent interface."""

import pytest

from interface_checks import AgentInterfaceTests

pytest.importorskip("torch")


class TestInterface(AgentInterfaceTests):
    solution = "2018_sac"
