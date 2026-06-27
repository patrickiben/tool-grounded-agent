"""Executable contract for the documented blind spots.

Each of these has a real problem the harness does NOT catch. The tests assert it
PASSES -- so if the guard's behavior ever silently changes, these fail and force
the README's "What this does NOT catch" section to be updated honestly.
"""
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from toolagent.agent import run_agent  # noqa: E402
from toolagent.loader import candidate_plan, load_scenario  # noqa: E402
from toolagent.planner import MockPlanner, Task  # noqa: E402


def _run(scenario_file, label):
    sc = load_scenario(os.path.join(BASE, "scenarios", scenario_file))
    cand = next(c for c in sc["candidates"] if c["label"] == label)
    return sc, run_agent(Task("", cand["template"]), sc["store"],
                         MockPlanner(candidate_plan(cand)),
                         sc["banned_phrases"], sc["required_names"])


def test_garbage_in_fact_passes_both_layers():
    # neither layer validates upstream truth
    _, run = _run("lab_summary.json", "garbage_in_fact")
    assert run.passed


def test_spelled_out_number_not_caught():
    _, run = _run("misleading_but_grounded.json", "spelled_out_number_and_paraphrased_claim")
    assert run.passed


def test_unit_swap_not_caught():
    _, run = _run("misleading_but_grounded.json", "unit_swap")
    assert run.passed


def test_whitespace_evaded_claim_not_caught():
    _, run = _run("misleading_but_grounded.json", "whitespace_evaded_banned_claim")
    assert run.passed


def test_correct_number_wrong_sentence_not_caught():
    _, run = _run("misleading_but_grounded.json", "correct_number_wrong_sentence")
    assert run.passed


def test_wrong_denominator_layers_disagree():
    # provenance (ledger) passes; correctness (grounded) fails -> they cover each other
    _, run = _run("lab_summary.json", "wrong_denominator_disagree")
    errs = [f.check for f in run.all_findings() if f.severity == "ERROR"]
    assert errs == ["numbers_grounded"]
    assert not run.passed
