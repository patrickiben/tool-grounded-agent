"""Tools, tool-call ledger, and tool registry.

The registry is the agent's ONLY legitimate channel to numbers. Every call is
recorded in a ToolLedger -- the audit trail and the basis for the Layer-2
provenance check. compute_rate takes fact NAMES, not raw numbers, so the agent
cannot mint an arbitrary value; it can only derive rates from existing facts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .facts import FactStore


def fmt_value(v: Any) -> str:
    """Render a fact value as it should appear in text (24 -> '24', 25.0 -> '25.0')."""
    return str(v)


@dataclass
class ToolResult:
    value: Optional[float] = None
    rendered: str = ""
    unit: str = ""
    provenance: str = ""
    ok: bool = True
    error: str = ""
    payload: Any = None


@dataclass
class ToolCall:
    tool: str
    args: Dict[str, Any]
    value: Optional[float]
    rendered: str
    unit: str
    ok: bool
    provenance: str


class ToolLedger:
    def __init__(self) -> None:
        self.calls: List[ToolCall] = []

    def record(self, call: ToolCall) -> None:
        self.calls.append(call)

    def sourced_values(self) -> List[float]:
        return [c.value for c in self.calls if c.ok and c.value is not None]

    def sourced_strings(self) -> set:
        return {c.rendered for c in self.calls if c.ok and c.value is not None}

    def table(self) -> str:
        rows = [
            "   # | tool          | args                              | ok    | return",
            "   --+---------------+-----------------------------------+-------+--------",
        ]
        for i, c in enumerate(self.calls):
            args = ", ".join(f"{k}={v}" for k, v in c.args.items())
            ret = c.rendered if (c.ok and c.value is not None) else (c.error or "-")
            rows.append(f"   {i} | {c.tool:<13} | {args:<33} | {str(c.ok):<5} | {ret}")
        return "\n".join(rows)


class ToolRegistry:
    def __init__(self, store: FactStore) -> None:
        self.store = store
        self.ledger = ToolLedger()

    def list_facts(self) -> ToolResult:
        payload = [{"name": f.name, "unit": f.unit} for f in self.store.facts]
        self.ledger.record(ToolCall("list_facts", {}, None, "", "", True, "list_facts"))
        return ToolResult(value=None, rendered="", provenance="list_facts", ok=True, payload=payload)

    def get_fact(self, name: str) -> ToolResult:
        f = self.store.by_name(name)
        prov = f"fact:{name}"
        if f is None or f.value is None:
            res = ToolResult(value=None, rendered="", ok=False, error=f"unknown fact '{name}'", provenance=prov)
        else:
            res = ToolResult(value=f.value, rendered=fmt_value(f.value), unit=f.unit, ok=True, provenance=prov)
        self.ledger.record(ToolCall("get_fact", {"name": name}, res.value, res.rendered, res.unit, res.ok, prov))
        return res

    def compute_rate(self, numerator_name: str, denominator_name: str, ndigits: int = 1) -> ToolResult:
        n = self.store.by_name(numerator_name)
        d = self.store.by_name(denominator_name)
        prov = f"compute_rate({numerator_name},{denominator_name})"
        if n is None or d is None or n.value is None or d.value in (None, 0):
            res = ToolResult(value=None, rendered="", ok=False, error="invalid rate inputs", provenance=prov)
        else:
            val = round(100.0 * n.value / d.value, ndigits)
            res = ToolResult(value=val, rendered=f"{val:.{ndigits}f}", unit="%", ok=True, provenance=prov)
        self.ledger.record(ToolCall(
            "compute_rate",
            {"numerator_name": numerator_name, "denominator_name": denominator_name},
            res.value, res.rendered, res.unit, res.ok, prov,
        ))
        return res

    def call(self, tool: str, args: Dict[str, Any]) -> ToolResult:
        if tool == "list_facts":
            return self.list_facts()
        if tool == "get_fact":
            return self.get_fact(args["name"])
        if tool == "compute_rate":
            return self.compute_rate(args.get("numerator_name"), args.get("denominator_name"), args.get("ndigits", 1))
        raise ValueError(f"unknown tool '{tool}'")


# Machine-readable tool schema -- the seam a real function-calling LLM receives.
BUILTIN_TOOLS: List[Dict[str, Any]] = [
    {"name": "list_facts", "description": "List available fact names and units (no values).", "parameters": {}},
    {"name": "get_fact", "description": "Return the value of a named fact.",
     "parameters": {"name": {"type": "string", "required": True}}},
    {"name": "compute_rate", "description": "Compute 100*numerator/denominator from two named facts.",
     "parameters": {"numerator_name": {"type": "string", "required": True},
                    "denominator_name": {"type": "string", "required": True},
                    "ndigits": {"type": "integer", "required": False}}},
]
