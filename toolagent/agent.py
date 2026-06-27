"""run_agent -- orchestration: execute the plan's tool calls (recording a
ledger), resolve slots, render (Layer 1), then guard the final text (Layer 2).

Overall verdict = (no Layer-1 ERRORs) AND (Layer-2 report passes). A Layer-1
failure alone forces overall failure.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from .facts import FactStore
from .guard import evaluate
from .planner import Plan, Planner, Task
from .render import render, slot_names
from .report import Finding, Report
from .tools import ToolLedger, ToolRegistry, ToolResult


@dataclass
class AgentRun:
    plan: Plan
    ledger: ToolLedger
    text: str
    layer1_findings: List[Finding]
    layer2_report: Report

    @property
    def layer1_passed(self) -> bool:
        return not any(f.severity == "ERROR" for f in self.layer1_findings)

    @property
    def passed(self) -> bool:
        return self.layer1_passed and self.layer2_report.passed

    def all_findings(self) -> List[Finding]:
        return list(self.layer1_findings) + list(self.layer2_report.findings)

    def scorecard(self) -> str:
        head = "PASS" if self.passed else "FAIL"
        l1e = sum(1 for f in self.layer1_findings if f.severity == "ERROR")
        lines = [f"  verdict: {head}  (layer1 errors={l1e}, "
                 f"layer2 errors={len(self.layer2_report.errors)})"]
        findings = self.all_findings()
        if not findings:
            lines.append("   - no findings.")
        for f in findings:
            lay = f" {{{f.layer}}}" if f.layer else ""
            lines.append(f"   - [{f.severity}]{lay} {f.check}: {f.message}")
        return "\n".join(lines)

    def ledger_table(self) -> str:
        return self.ledger.table()


def run_agent(
    task: Task,
    store: FactStore,
    planner: Planner,
    banned_phrases: Iterable[str] = (),
    required_names: Iterable[str] = (),
) -> AgentRun:
    plan = planner.plan(task, None)
    registry = ToolRegistry(store)

    results_by_id = {}
    for call in plan.tool_calls:
        res = registry.call(call["tool"], call.get("args", {}))
        cid = call.get("id")
        if cid is not None:
            results_by_id[cid] = res

    filled = {}
    for slot in slot_names(task.template):
        binding = plan.slots.get(slot)
        if binding and "from" in binding:
            r = results_by_id.get(binding["from"])
            filled[slot] = r if (r is not None and r.ok and r.value is not None) else None
        else:
            # missing binding OR a fabricated literal -> not tool-backed
            filled[slot] = None

    text, layer1 = render(task.template, filled)
    if plan.prose:
        text = (text + " " + plan.prose).strip()

    layer2 = evaluate(text, store, banned_phrases, required_names, ledger=registry.ledger)
    return AgentRun(plan=plan, ledger=registry.ledger, text=text,
                    layer1_findings=layer1, layer2_report=layer2)
