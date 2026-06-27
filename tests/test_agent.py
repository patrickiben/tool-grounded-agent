import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from toolagent.agent import run_agent  # noqa: E402
from toolagent.extract import extract_numbers  # noqa: E402
from toolagent.guard import evaluate  # noqa: E402
from toolagent.loader import candidate_plan, load_scenario  # noqa: E402
from toolagent.planner import MockPlanner, ReplayPlanner, Task  # noqa: E402
from toolagent.render import UNSOURCED  # noqa: E402


def run_candidate(scenario_file, label):
    sc = load_scenario(os.path.join(BASE, "scenarios", scenario_file))
    cand = next(c for c in sc["candidates"] if c["label"] == label)
    task = Task("", cand["template"])
    run = run_agent(task, sc["store"], MockPlanner(candidate_plan(cand)),
                    sc["banned_phrases"], sc["required_names"])
    return sc, cand, run


def test_behaved_passes():
    _, _, run = run_candidate("ae_overview.json", "well_behaved")
    assert run.passed
    assert "24" in run.text and "79.2" in run.text


def test_behaved_every_number_traces_to_ledger():
    sc, _, run = run_candidate("ae_overview.json", "well_behaved")
    allowed = run.ledger.sourced_values()
    for val, raw, _ in extract_numbers(run.text):
        assert any(abs(val - lv) <= sc["store"]._tol_for(lv) for lv in allowed), raw


def test_rogue_hallucinated_caught_by_both_number_checks():
    _, _, run = run_candidate("ae_overview.json", "rogue_hallucinated_number")
    assert not run.passed
    checks = {f.check for f in run.all_findings()}
    assert "numbers_grounded" in checks and "numbers_from_ledger" in checks
    assert any("81.5" in f.message for f in run.all_findings())


def test_centerpiece_ledger_only_and_numguard_passes():
    sc, _, run = run_candidate("ae_overview.json", "rogue_unqueried_real_fact")
    errs = [f.check for f in run.all_findings() if f.severity == "ERROR"]
    assert errs == ["numbers_from_ledger"], errs  # ONLY the provenance check fires
    # the SAME text, without a ledger, passes plain numguard -> layers are non-redundant
    rep = evaluate(run.text, sc["store"], sc["banned_phrases"], sc["required_names"], ledger=None)
    assert rep.passed, rep.scorecard()


def test_fabricated_slot_marks_unsourced():
    _, _, run = run_candidate("ae_overview.json", "rogue_fabricated_slot")
    assert not run.passed
    assert any(f.check == "slot_unsourced" for f in run.layer1_findings)
    assert UNSOURCED in run.text


def test_banned_claim_caught_layer2_only():
    _, _, run = run_candidate("ae_overview.json", "rogue_banned_claim")
    assert not run.passed
    assert run.layer1_passed  # zero Layer-1 errors -> defense in depth, not redundancy
    assert any(f.check == "unsupported_claims" for f in run.layer2_report.findings)


def test_unknown_fact_logged_with_no_value():
    _, _, run = run_candidate("ae_overview.json", "rogue_unknown_fact")
    assert any((not c.ok) and c.value is None and c.args.get("name") == "pct_cure"
               for c in run.ledger.calls)
    assert not run.passed


def test_layer1_failure_forces_overall_fail():
    _, _, run = run_candidate("ae_overview.json", "rogue_fabricated_slot")
    assert run.layer1_passed is False
    assert run.passed is False


def test_planner_protocol_swappable():
    sc = load_scenario(os.path.join(BASE, "scenarios", "ae_overview.json"))
    cand = next(c for c in sc["candidates"] if c["label"] == "well_behaved")
    replay = ReplayPlanner.from_dict(cand["plan"])
    run = run_agent(Task("", cand["template"]), sc["store"], replay,
                    sc["banned_phrases"], sc["required_names"])
    assert run.passed  # a different Planner implementation, identical verdict
