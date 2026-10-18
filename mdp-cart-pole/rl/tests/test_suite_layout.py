"""Every solution has its own tests/test_<solution>.py that runs the shared interface checks."""

import importlib

import pytest

from interface_checks import AgentInterfaceTests
from rl_helpers import SOLUTIONS


@pytest.mark.parametrize("soln", SOLUTIONS)
def test_every_solution_has_a_test_module_with_the_interface_checks(soln):
    mod = importlib.import_module(f"test_{soln}")
    classes = [c for c in vars(mod).values()
               if isinstance(c, type) and issubclass(c, AgentInterfaceTests) and c is not AgentInterfaceTests]
    assert classes, f"tests/test_{soln}.py has no AgentInterfaceTests subclass"
    assert {c.solution for c in classes} == {soln}
