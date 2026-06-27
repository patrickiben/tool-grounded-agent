"""extract_numbers -- vendored VERBATIM from numguard so 'a number' means the
identical thing in every layer of this harness."""
from __future__ import annotations

import re
from typing import List, Tuple

_NUM_RE = re.compile(r"(?<![\w.])(\d+(?:,\d{3})*(?:\.\d+)?)")


def extract_numbers(text: str) -> List[Tuple[float, str, int]]:
    out: List[Tuple[float, str, int]] = []
    for m in _NUM_RE.finditer(text):
        raw = m.group(1)
        try:
            out.append((float(raw.replace(",", "")), raw, m.start()))
        except ValueError:  # pragma: no cover
            continue
    return out
