from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TelegramAssetFileViewDTO:
    file_id: str
    file_name: str | None
