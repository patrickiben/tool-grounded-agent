import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from toolagent.render import UNSOURCED, render, slot_names  # noqa: E402
from toolagent.tools import ToolResult  # noqa: E402


def test_slot_injects_exact_string():
    text, findings = render("the rate was {x}.", {"x": ToolResult(value=79.2, rendered="79.2", ok=True)})
    assert text == "the rate was 79.2."
    assert findings == []


def test_missing_binding_is_unsourced():
    text, findings = render("the rate was {x}.", {"x": None})
    assert UNSOURCED in text
    assert any(f.check == "slot_unsourced" and f.layer == "layer1" for f in findings)


def test_failed_tool_result_is_unsourced():
    text, findings = render("the rate was {x}.", {"x": ToolResult(ok=False)})
    assert UNSOURCED in text
    assert any(f.check == "slot_unsourced" for f in findings)


def test_slot_names_parsed():
    assert slot_names("a {x} b {y_2} c") == ["x", "y_2"]
