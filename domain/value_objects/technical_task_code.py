from __future__ import annotations


class TechnicalTaskCode:
    PREFIX = "SYSTEM_TECHNICAL_TASK:"
    ISSUE_KEY_VALUE = "SMM_TECH_ISSUE_KEY_29AC41"
    ACTIVATE_VALUE = "SMM_TECH_ACTIVATE_54D91B"
    COMPLETE_VALUE = "SMM_TECH_COMPLETE_1E6A20"
    DECLINE_VALUE = "SMM_TECH_DECLINE_6B74D3"
    KEEP_VALUE = "SMM_TECH_KEEP_7D18E2"

    @classmethod
    def should_issue_key(cls, text: str) -> bool:
        return cls.ISSUE_KEY_VALUE in text

    @classmethod
    def looks_like_key_request(cls, text: str) -> bool:
        return "ключ" in (text or "").lower()

    @classmethod
    def should_activate_task(cls, text: str) -> bool:
        return cls.ACTIVATE_VALUE in text

    @classmethod
    def should_complete_task(cls, text: str) -> bool:
        return cls.COMPLETE_VALUE in text

    @classmethod
    def should_decline_task(cls, text: str) -> bool:
        return cls.DECLINE_VALUE in text

    @classmethod
    def strip_all_codes(cls, text: str) -> str:
        cleaned = text.replace(cls.ISSUE_KEY_VALUE, "")
        cleaned = cleaned.replace(cls.ACTIVATE_VALUE, "")
        cleaned = cleaned.replace(cls.COMPLETE_VALUE, "")
        cleaned = cleaned.replace(cls.DECLINE_VALUE, "")
        cleaned = cleaned.replace(cls.KEEP_VALUE, "")
        lines = [line.strip() for line in cleaned.splitlines()]
        filtered = [line for line in lines if not line.startswith(cls.PREFIX)]
        return "\n".join(line for line in filtered if line)
