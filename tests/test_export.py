import json
import os
import sys
from xml.etree import ElementTree as ET

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from toolagent.agent import run_agent  # noqa: E402
from toolagent.export import record_ok, reports_to_junit, reports_to_dict  # noqa: E402
from toolagent.loader import candidate_plan, load_scenario  # noqa: E402
from toolagent.planner import MockPlanner, Task  # noqa: E402


def _records(scenario_file="ae_overview.json"):
    sc = load_scenario(os.path.join(BASE, "scenarios", scenario_file))
    recs = []
    for c in sc["candidates"]:
        run = run_agent(Task("", c["template"]), sc["store"],
                        MockPlanner(candidate_plan(c)), sc["banned_phrases"], sc["required_names"])
        recs.append({"label": c["label"], "expected": c["expected"], "run": run})
    return recs


def test_json_carries_ledger_and_layer():
    d = reports_to_dict(_records())
    assert d["total"] == 7 and d["all_ok"] is True
    behaved = next(c for c in d["cases"] if c["label"] == "well_behaved")
    assert behaved["ledger"]  # audit trail present
    centerpiece = next(c for c in d["cases"] if c["label"] == "rogue_unqueried_real_fact")
    assert any(f["layer"] == "layer2" and f["check"] == "numbers_from_ledger"
               for f in centerpiece["findings"])
    # round-trips through JSON
    json.loads(json.dumps(d))


def test_junit_is_valid_xml_no_failures_when_expected():
    root = ET.fromstring(reports_to_junit(_records()))
    suite = root.find("testsuite")
    assert len(suite.findall("testcase")) == 7
    assert suite.findall(".//failure") == []  # all behaved as documented


def test_junit_flags_an_unexpected_verdict():
    recs = _records()
    behaved = next(r for r in recs if r["label"] == "well_behaved")
    behaved["expected"] = "fail"  # force a mismatch
    root = ET.fromstring(reports_to_junit([behaved]))
    failure = root.find(".//testcase/failure")
    assert failure is not None and "expected fail" in failure.get("message")


def test_record_ok_semantics():
    sc = load_scenario(os.path.join(BASE, "scenarios", "ae_overview.json"))
    cand = next(c for c in sc["candidates"] if c["label"] == "well_behaved")
    run = run_agent(Task("", cand["template"]), sc["store"],
                    MockPlanner(candidate_plan(cand)), sc["banned_phrases"], sc["required_names"])
    assert record_ok(run, "pass") and not record_ok(run, "fail")
