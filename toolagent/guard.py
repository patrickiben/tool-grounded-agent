"""Layer 2 -- the text guard.

Three checks vendored from numguard plus a NEW provenance check:
  numbers_grounded     -- every number is an allowed fact (set membership).
  unsupported_claims   -- no banned qualitative phrase.
  required_facts       -- required fact values appear in the text.
  numbers_from_ledger  -- every number was actually produced by a tool THIS RUN
                          (strictly stronger than set membership).

evaluate(..., ledger=None) reproduces numguard exactly; pass a ledger to add the
provenance check. The non-redundancy proof: a real fact recited but never fetched
passes numbers_grounded yet fails numbers_from_ledger.
"""
from __future__ import annotations

from typing import Iterable, List, Optional

from .extract import extract_numbers
from .facts import FactStore
from .report import Finding, Report
from .tools import ToolLedger


def check_numbers_grounded(text: str, store: FactStore) -> List[Finding]:
    out: List[Finding] = []
    for val, raw, _ in extract_numbers(text):
        if store.matches(val) is None:
            out.append(Finding("numbers_grounded", "ERROR",
                               f"Untraceable number '{raw}' is not an allowed fact.",
                               "layer2", {"value": val}))
    return out


def check_no_unsupported_claims(text: str, banned_phrases: Iterable[str]) -> List[Finding]:
    out: List[Finding] = []
    low = text.lower()
    for phrase in banned_phrases:
        if phrase.lower() in low:
            out.append(Finding("unsupported_claims", "ERROR",
                               f"Unsupported qualitative claim: '{phrase}'.", "layer2"))
    return out


def check_required_facts(text: str, store: FactStore, required_names: Iterable[str]) -> List[Finding]:
    out: List[Finding] = []
    nums = [v for v, _, _ in extract_numbers(text)]
    for name in required_names:
        f = store.by_name(name)
        if f is None or f.value is None:
            raise ValueError(f"Invalid required fact: {name!r}")
        tol = store._tol_for(f.value)
        if not any(abs(n - f.value) <= tol for n in nums):
            unit = f" {f.unit}" if f.unit else ""
            out.append(Finding("required_facts", "ERROR",
                               f"Required fact '{name}' ({f.value}{unit}) is missing.", "layer2"))
    return out


def check_numbers_from_ledger(text: str, store: FactStore, ledger: ToolLedger) -> List[Finding]:
    out: List[Finding] = []
    allowed = ledger.sourced_values()
    for val, raw, _ in extract_numbers(text):
        if not any(abs(val - lv) <= store._tol_for(lv) for lv in allowed):
            out.append(Finding("numbers_from_ledger", "ERROR",
                               f"Number '{raw}' was not produced by any tool call this run.",
                               "layer2", {"value": val}))
    return out


def evaluate(
    text: str,
    store: FactStore,
    banned_phrases: Iterable[str] = (),
    required_names: Iterable[str] = (),
    ledger: Optional[ToolLedger] = None,
) -> Report:
    required_names = tuple(required_names)
    store.validate(required_names)
    try:
        return _evaluate(text, store, banned_phrases, required_names, ledger)
    except ValueError as error:
        return Report([Finding("numeric_format", "ERROR", str(error), "layer2")])


def _evaluate(text, store, banned_phrases, required_names, ledger):
    findings: List[Finding] = []
    findings += check_numbers_grounded(text, store)
    findings += check_no_unsupported_claims(text, banned_phrases)
    findings += check_required_facts(text, store, required_names)
    if ledger is not None:
        findings += check_numbers_from_ledger(text, store, ledger)
    return Report(findings)
