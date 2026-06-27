import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from toolagent.facts import Fact, FactStore  # noqa: E402
from toolagent.tools import ToolRegistry  # noqa: E402


def _store():
    return FactStore(facts=[Fact("n", 24, "participants"), Fact("d", 30, "participants")])


def test_get_fact_ok():
    r = ToolRegistry(_store()).get_fact("n")
    assert r.ok and r.value == 24 and r.rendered == "24"


def test_get_fact_unknown_is_logged():
    reg = ToolRegistry(_store())
    r = reg.get_fact("missing")
    assert (not r.ok) and r.value is None
    assert reg.ledger.calls[-1].ok is False


def test_compute_rate_rounds_into_ledger():
    reg = ToolRegistry(_store())
    r = reg.compute_rate("n", "d")  # 100*24/30 = 80.0
    assert r.ok and r.value == 80.0 and r.rendered == "80.0"
    assert "80.0" in reg.ledger.sourced_strings()


def test_compute_rate_zero_denominator_fails():
    s = FactStore(facts=[Fact("n", 1), Fact("z", 0)])
    assert not ToolRegistry(s).compute_rate("n", "z").ok


def test_ledger_sourced_values_excludes_failed_calls():
    reg = ToolRegistry(_store())
    reg.get_fact("n")
    reg.get_fact("missing")
    assert reg.ledger.sourced_values() == [24]
