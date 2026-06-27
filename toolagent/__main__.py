"""CLI: python -m toolagent <scenario.json> [--json out] [--junit out] [--quiet].

Runs every candidate in a scenario through the harness and (optionally) writes
JSON/JUnit for CI. Exit code = number of candidates whose verdict did not match
expectation (0 = all behaved as documented, including known gaps).
"""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from .agent import run_agent
from .export import record_ok, reports_to_json, reports_to_junit
from .loader import candidate_plan, load_scenario
from .planner import MockPlanner, Task


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="toolagent")
    parser.add_argument("scenario", help="path to a scenario JSON file")
    parser.add_argument("--json", dest="json_out")
    parser.add_argument("--junit", dest="junit_out")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    sc = load_scenario(args.scenario)
    records = []
    for cand in sc["candidates"]:
        task = Task(cand.get("instruction", ""), cand["template"])
        run = run_agent(task, sc["store"], MockPlanner(candidate_plan(cand)),
                        sc["banned_phrases"], sc["required_names"])
        records.append({"label": cand["label"], "expected": cand.get("expected"), "run": run})
        if not args.quiet:
            print(f"[{cand['label']}] expected={cand.get('expected')} passed={run.passed}")
            print(run.scorecard())
            print("-" * 60)

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            fh.write(reports_to_json(records))
        print(f"wrote {args.json_out}")
    if args.junit_out:
        with open(args.junit_out, "w", encoding="utf-8") as fh:
            fh.write(reports_to_junit(records))
        print(f"wrote {args.junit_out}")

    not_ok = sum(0 if record_ok(r["run"], r.get("expected")) else 1 for r in records)
    if not_ok:
        print(f"{not_ok} candidate(s) did not match expectation.", file=sys.stderr)
    return 1 if not_ok else 0


if __name__ == "__main__":
    raise SystemExit(main())
