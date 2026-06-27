"""Suite-level exports for CI: JSON and JUnit XML.

A record is {"label", "expected", "run": AgentRun}. record_ok():
  expected 'pass' -> ok iff the run passed
  expected 'fail' -> ok iff the run failed
  expected 'miss' -> ok iff the run passed (a documented known-gap the harness
                     is NOT expected to catch)
Each exported case carries the tool ledger and which layer caught each finding.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List
from xml.dom import minidom
from xml.etree import ElementTree as ET

from .agent import AgentRun


def record_ok(run: AgentRun, expected: Any) -> bool:
    if expected == "pass":
        return run.passed
    if expected == "fail":
        return not run.passed
    if expected == "miss":
        return run.passed
    return run.passed


def _findings(run: AgentRun) -> List[Dict[str, Any]]:
    return [{"check": f.check, "severity": f.severity, "layer": f.layer, "message": f.message}
            for f in run.all_findings()]


def _ledger(run: AgentRun) -> List[Dict[str, Any]]:
    return [{"tool": c.tool, "args": c.args, "ok": c.ok, "rendered": c.rendered, "value": c.value}
            for c in run.ledger.calls]


def _case(rec: Dict[str, Any]) -> Dict[str, Any]:
    run = rec["run"]
    return {
        "label": rec["label"],
        "expected": rec.get("expected"),
        "verdict": "pass" if run.passed else "fail",
        "passed": run.passed,
        "ok": record_ok(run, rec.get("expected")),
        "text": run.text,
        "findings": _findings(run),
        "ledger": _ledger(run),
    }


def reports_to_dict(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    cases = [_case(r) for r in records]
    not_ok = sum(0 if c["ok"] else 1 for c in cases)
    return {"total": len(cases), "not_ok": not_ok, "all_ok": not_ok == 0, "cases": cases}


def reports_to_json(records: List[Dict[str, Any]], indent: int = 2) -> str:
    return json.dumps(reports_to_dict(records), indent=indent)


def reports_to_junit(records: List[Dict[str, Any]], suite_name: str = "tool-grounded-agent") -> str:
    not_ok = sum(0 if record_ok(r["run"], r.get("expected")) else 1 for r in records)
    suites = ET.Element("testsuites", name=suite_name, tests=str(len(records)), failures=str(not_ok))
    suite = ET.SubElement(suites, "testsuite", name=suite_name, tests=str(len(records)), failures=str(not_ok))
    for r in records:
        run = r["run"]
        tc = ET.SubElement(suite, "testcase", name=str(r["label"]), classname=suite_name)
        if not record_ok(run, r.get("expected")):
            verdict = "pass" if run.passed else "fail"
            msg = f"expected {r.get('expected')}, got {verdict}"
            failure = ET.SubElement(tc, "failure", message=msg, type="HarnessUnexpected")
            failure.text = "\n".join(
                f"[{f.severity}] {{{f.layer}}} {f.check}: {f.message}" for f in run.all_findings()
            ) or msg
    raw = ET.tostring(suites, encoding="unicode")
    return minidom.parseString(raw).toprettyxml(indent="  ")
