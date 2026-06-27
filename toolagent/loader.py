"""Load declarative scenario files (JSON): a FactStore + banned/required lists +
a list of candidate drafts, each with its own template, scripted plan, and an
expected verdict ('pass' | 'fail' | 'miss')."""
from __future__ import annotations

import json
from typing import Any, Dict

from .facts import Fact, FactStore
from .planner import Plan


def load_scenario(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        d = json.load(fh)
    facts = [Fact(name=f["name"], value=f.get("value"), unit=f.get("unit", "")) for f in d.get("facts", [])]
    store = FactStore(facts=facts, abs_tol=d.get("abs_tol", 0.05), rel_tol=d.get("rel_tol", 0.001))
    return {
        "name": d.get("name", ""),
        "store": store,
        "banned_phrases": d.get("banned_phrases", []),
        "required_names": d.get("required_names", []),
        "candidates": d.get("candidates", []),
    }


def candidate_plan(candidate: Dict[str, Any]) -> Plan:
    p = candidate.get("plan", {})
    return Plan(tool_calls=p.get("tool_calls", []), slots=p.get("slots", {}), prose=p.get("prose", ""))
