"""Template rendering (Layer 1, structural).

A {slot} can ONLY be filled by a successful ToolResult; render injects that
result's EXACT rendered string (no re-formatting). A slot with no backing tool
result renders as «UNSOURCED» and raises a slot_unsourced ERROR, so the breach
is visible in the draft instead of hidden.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from .report import Finding
from .tools import ToolResult

_SLOT_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")
UNSOURCED = "«UNSOURCED»"


def slot_names(template_text: str) -> List[str]:
    return _SLOT_RE.findall(template_text)


def render(
    template_text: str, filled: Dict[str, Optional[ToolResult]]
) -> Tuple[str, List[Finding]]:
    findings: List[Finding] = []

    def _replace(m: "re.Match") -> str:
        slot = m.group(1)
        r = filled.get(slot)
        if r is None or not r.ok or r.value is None:
            findings.append(Finding(
                "slot_unsourced", "ERROR",
                f"slot '{slot}' was not filled from a successful tool result.",
                "layer1",
            ))
            return UNSOURCED
        return r.rendered

    text = _SLOT_RE.sub(_replace, template_text)
    return text, findings
