from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ApplicationFormDTO:
    montage: str
    experience: str
    game: str
    channel: str
    video_format: str
    video_format_code: str
