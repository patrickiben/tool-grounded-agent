"""Regressions for previously passing unsupported numbers and invalid contracts."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from toolagent.facts import Fact, FactStore
from toolagent.guard import evaluate


@pytest.mark.parametrize("text", ["Change -2.3 mg.", "Rate .5%.", "Count 1e9 participants."])
def test_unsupported_numeric_meanings_fail(text):
    assert not evaluate(text, FactStore([Fact("change", 2.3), Fact("n", 1)])).passed


def test_signed_and_scientific_supported_values_pass():
    store = FactStore([Fact("change", -2.3), Fact("rate", .5), Fact("n", 1e9)])
    assert evaluate("Change −2.3, rate +.5, count 1e9.", store).passed


@pytest.mark.parametrize("text", ["Rate 79,2%.", "Count 1e999."])
def test_malformed_or_nonfinite_draft_gets_a_failing_report(text):
    report = evaluate(text, FactStore([Fact("n", 1)]))
    assert not report.passed
    assert report.errors[0].check == "numeric_format"


@pytest.mark.parametrize("required", [["mortailty"], ["qualitative"]])
def test_unknown_or_nonnumeric_required_fact_is_a_configuration_error(required):
    store = FactStore([Fact("mortality", 0), Fact("qualitative")])
    with pytest.raises(ValueError):
        evaluate("No outcome reported.", store, required_names=required)


@pytest.mark.parametrize("kwargs", [
    {"abs_tol": float("inf")}, {"rel_tol": float("nan")},
    {"abs_tol": -1}, {"rel_tol": True},
    {"context_values": (float("inf"),)},
])
def test_invalid_tolerances_and_context_values_rejected(kwargs):
    with pytest.raises(ValueError):
        FactStore([Fact("n", 1)], **kwargs)


@pytest.mark.parametrize("facts", [
    [Fact("n", 1), Fact("n", 2)], [Fact("", 1)],
    [Fact("n", float("inf"))], [Fact("n", float("nan"))], [Fact("n", True)],
])
def test_ambiguous_or_nonfinite_facts_rejected(facts):
    with pytest.raises(ValueError):
        FactStore(facts)


def test_mutating_a_store_cannot_bypass_configuration_validation():
    store = FactStore([Fact("n", 1)])
    store.facts.append(Fact("n", 2))
    with pytest.raises(ValueError):
        evaluate("Count 1.", store)


def test_empty_candidate_file_cannot_report_a_successful_run(tmp_path):
    import json
    from toolagent.loader import load_scenario
    path = tmp_path / "empty.json"
    path.write_text(json.dumps({"facts": [], "candidates": []}))
    with pytest.raises(ValueError, match="candidate"):
        load_scenario(str(path))
