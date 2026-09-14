from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TechnicalTaskKeyViewDTO:
    value: str
    is_repeat: bool = False
