import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from toolagent.facts import Fact, FactStore  # noqa: E402
from toolagent.guard import evaluate  # noqa: E402
from toolagent.tools import ToolRegistry  # noqa: E402


def test_identifier_digits_not_flagged():
    s = FactStore(facts=[Fact("n", 5)])
    assert evaluate("Study CP101 enrolled 5 participants.", s).passed


def test_required_fact_missing_flagged():
    s = FactStore(facts=[Fact("k", 42)])
    rep = evaluate("no relevant numbers", s, required_names=["k"])
    assert not rep.passed
    assert any(f.check == "required_facts" for f in rep.findings)


def test_tolerance_boundary():
    s = FactStore(facts=[Fact("k", 10.0)])  # tol = max(0.05, 0.001*10) = 0.05
    # use values clearly inside / outside the 0.05 window (exactly-on-boundary is
    # subject to float noise: 10.05 - 10.0 == 0.0500000000000007)
    assert evaluate("value 10.03 here", s).passed
    assert not evaluate("value 10.09 here", s).passed


def test_thousands_separator_grounds():
    s = FactStore(facts=[Fact("k", 1200.0)])
    assert evaluate("a count of 1,200 events", s).passed


def test_numbers_from_ledger_is_stronger_than_grounded():
    s = FactStore(facts=[Fact("p", 79.2)])
    empty_ledger = ToolRegistry(s).ledger  # nothing fetched
    assert evaluate("the rate was 79.2%", s, ledger=None).passed          # numguard: 79.2 is a fact
    rep = evaluate("the rate was 79.2%", s, ledger=empty_ledger)
    assert not rep.passed
    assert any(f.check == "numbers_from_ledger" for f in rep.findings)
