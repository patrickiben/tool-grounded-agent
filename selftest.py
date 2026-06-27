#!/usr/bin/env python3
"""Zero-dependency self-test.

Runs every scenario through run_agent and classifies each candidate:
  OK         -- verdict matched its 'pass'/'fail' expectation
  KNOWN-GAP  -- an 'expected: miss' case that (as documented) the harness does
                NOT catch, so it passed; printed loudly so the blind spot is visible
  UNEXPECTED -- behavior changed from what's documented (fails the test)

Exits 0 iff there are zero UNEXPECTED classifications.
"""
from __future__ import annotations

import glob
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from toolagent.agent import run_agent  # noqa: E402
from toolagent.loader import candidate_plan, load_scenario  # noqa: E402
from toolagent.planner import MockPlanner, Task  # noqa: E402


def classify(expected: str, passed: bool) -> str:
    if expected == "pass":
        return "OK" if passed else "UNEXPECTED"
    if expected == "fail":
        return "OK" if not passed else "UNEXPECTED"
    if expected == "miss":
        return "KNOWN-GAP" if passed else "UNEXPECTED"
    return "UNEXPECTED"


def main() -> int:
    files = sorted(glob.glob(os.path.join(BASE, "scenarios", "*.json")))
    all_ok = True
    counts = {"OK": 0, "KNOWN-GAP": 0, "UNEXPECTED": 0}

    for path in files:
        sc = load_scenario(path)
        print("#" * 72)
        print(f"SCENARIO: {sc['name']}  ({os.path.basename(path)})")
        for cand in sc["candidates"]:
            task = Task(instruction=cand.get("instruction", ""), template=cand["template"])
            planner = MockPlanner(candidate_plan(cand))
            run = run_agent(task, sc["store"], planner, sc["banned_phrases"], sc["required_names"])
            status = classify(cand["expected"], run.passed)
            counts[status] += 1
            if status == "UNEXPECTED":
                all_ok = False
            print("=" * 72)
            print(f"[{status}] {cand['label']}  expected={cand['expected']}  passed={run.passed}")
            if cand.get("note"):
                print(f"  note: {cand['note']}")
            print(f"  draft: {run.text}")
            print(run.scorecard())

    print("#" * 72)
    print(f"summary: {counts['OK']} OK, {counts['KNOWN-GAP']} KNOWN-GAP, {counts['UNEXPECTED']} UNEXPECTED")
    print("SELFTEST PASSED" if all_ok else "SELFTEST FAILED")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
