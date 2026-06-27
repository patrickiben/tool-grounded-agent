"""Finding + Report -- vendored from numguard, plus a `layer` tag so findings
can say which guard layer caught them."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Finding:
    check: str
    severity: str
    message: str
    layer: str = ""
    detail: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Report:
    findings: List[Finding] = field(default_factory=list)

    @property
    def errors(self) -> List[Finding]:
        return [f for f in self.findings if f.severity == "ERROR"]

    @property
    def warnings(self) -> List[Finding]:
        return [f for f in self.findings if f.severity == "WARN"]

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0

    def scorecard(self) -> str:
        head = "PASS" if self.passed else "FAIL"
        lines = [f"  {head}  ({len(self.errors)} error(s))"]
        if not self.findings:
            lines.append("   - no findings.")
        for f in self.findings:
            lay = f" {{{f.layer}}}" if f.layer else ""
            lines.append(f"   - [{f.severity}]{lay} {f.check}: {f.message}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "n_errors": len(self.errors),
            "findings": [
                {"check": f.check, "severity": f.severity, "message": f.message, "layer": f.layer}
                for f in self.findings
            ],
        }
