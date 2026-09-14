from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AutoCloseCode:
    value: str

    CLOSE_VALUE = "SMM_CLOSE_TICKET_9F3A72"
    KEEP_OPEN_VALUE = "SMM_KEEP_OPEN_B41C20"
    SYSTEM_PREFIX = "SYSTEM_CODE:"

    @classmethod
    def default(cls) -> AutoCloseCode:
        return cls(cls.CLOSE_VALUE)

    @classmethod
    def has_close_code(cls, text: str) -> bool:
        return cls.CLOSE_VALUE in text

    @classmethod
    def strip_all_codes(cls, text: str) -> str:
        cleaned = text.replace(cls.CLOSE_VALUE, "")
        cleaned = cleaned.replace(cls.KEEP_OPEN_VALUE, "")
        lines = [line.strip() for line in cleaned.splitlines()]
        filtered = [line for line in lines if not line.startswith(cls.SYSTEM_PREFIX)]
        return "\n".join(line for line in filtered if line)
