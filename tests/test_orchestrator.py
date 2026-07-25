import pytest

from src.orchestrator.orchestrator import Orchestrator


def test_orchestrator_initializes():
    orch = Orchestrator()
    assert orch is not None
