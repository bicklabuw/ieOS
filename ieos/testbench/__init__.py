# ieos/testbench/__init__.py
"""Autonomous UI testbench (scenario-driven synthetic input)."""

from __future__ import annotations

__all__ = ["TestbenchStartupViewController"]


def __getattr__(name: str):
    if name == "TestbenchStartupViewController":
        from ieos.testbench.startup import TestbenchStartupViewController

        return TestbenchStartupViewController
    raise AttributeError(name)
