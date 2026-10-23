"""Fact + FactStore -- vendored from the numguard project so both layers share
one definition of an allowed value (no tolerance/extractor drift)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from ._numeric import validate_fact_config, validate_tolerances


@dataclass(frozen=True)
class Fact:
    name: str
    value: Optional[float] = None
    unit: str = ""


@dataclass
class FactStore:
    facts: List[Fact] = field(default_factory=list)
    context_values: Tuple[float, ...] = ()
    abs_tol: float = 0.05
    rel_tol: float = 0.001

    def __post_init__(self) -> None:
        self.validate()

    def validate(self, required_names=()) -> None:
        validate_tolerances(self.abs_tol, self.rel_tol)
        validate_fact_config(((f.name, f.value) for f in self.facts), required_names,
                             self.context_values)

    def numeric_values(self) -> List[float]:
        vals = [f.value for f in self.facts if f.value is not None]
        vals.extend(self.context_values)
        return vals

    def _tol_for(self, v: float) -> float:
        return max(self.abs_tol, self.rel_tol * abs(v))

    def matches(self, x: float) -> Optional[float]:
        for v in self.numeric_values():
            if abs(x - v) <= self._tol_for(v):
                return v
        return None

    def by_name(self, name: str) -> Optional[Fact]:
        for f in self.facts:
            if f.name == name:
                return f
        return None
