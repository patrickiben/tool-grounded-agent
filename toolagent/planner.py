"""The planner seam.

A `Planner` produces a `Plan` (which tools to call, how to bind slots, optional
free prose). MockPlanner and ReplayPlanner are DETERMINISTIC, SCRIPTED stand-ins
for a function-calling LLM -- they are NOT language models. A real model would
implement the same `Planner` protocol and the rest of the harness runs unchanged
(which is exactly why the Layer-2 backstop exists: a real model makes the planning
step LESS trustworthy, not more).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

try:
    from typing import Protocol
except ImportError:  # pragma: no cover - py<3.8
    Protocol = object  # type: ignore


@dataclass
class Task:
    instruction: str
    template: str


@dataclass
class Plan:
    # each tool call: {"id": str, "tool": str, "args": {...}}
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    # slot -> {"from": <call id>}  (legit)  or  {"literal": <value>}  (fabricated)
    slots: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    prose: str = ""


class Planner(Protocol):
    def plan(self, task: "Task", tool_specs: Any) -> "Plan": ...


class MockPlanner:
    """Returns a pre-authored Plan. Scripted stand-in for an LLM, not a model."""

    def __init__(self, plan: Plan) -> None:
        self._plan = plan

    def plan(self, task: "Task", tool_specs: Any) -> "Plan":
        return self._plan


class ReplayPlanner(MockPlanner):
    """Same contract, built from a recorded plan dict -- proves the seam is swappable."""

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ReplayPlanner":
        return cls(Plan(
            tool_calls=d.get("tool_calls", []),
            slots=d.get("slots", {}),
            prose=d.get("prose", ""),
        ))
