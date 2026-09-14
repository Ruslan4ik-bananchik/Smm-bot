from __future__ import annotations


class AntiTrollCode:
    PREFIX = "SYSTEM_ANTI_TROLL:"
    BLOCK_VALUE = "SMM_ANTI_TROLL_BLOCK_176C4A"

    @classmethod
    def should_block(cls, text: str) -> bool:
        return cls.BLOCK_VALUE in text

    @classmethod
    def strip_all_codes(cls, text: str) -> str:
        cleaned = text.replace(cls.BLOCK_VALUE, "")
        lines = [line.strip() for line in cleaned.splitlines()]
        filtered = [line for line in lines if not line.startswith(cls.PREFIX)]
        return "\n".join(line for line in filtered if line)
