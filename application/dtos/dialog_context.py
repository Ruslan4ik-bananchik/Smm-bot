from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DialogContextDTO:
    should_process: bool
    history: list[str]
    response_flow: str = "application"
