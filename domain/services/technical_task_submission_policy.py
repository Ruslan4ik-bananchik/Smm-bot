from __future__ import annotations

import re

from domain.exceptions.errors import (
    TechnicalTaskSubmissionInvalidLinkCountError,
    TechnicalTaskSubmissionInvalidPlatformError,
)


class TechnicalTaskSubmissionPolicy:
    SHORTS_REQUIRED_LINKS = 3
    LONGFORM_REQUIRED_LINKS = 2
    URL_PATTERN = re.compile(r"(https?://\S+|(?:www\.)?\S+\.\w{2,}\S*)", re.IGNORECASE)
    SHORTS_ALLOWED_DOMAINS = ("youtube.com", "youtu.be", "tiktok.com", "vt.tiktok.com", "vm.tiktok.com")
    LONGFORM_ALLOWED_DOMAINS = ("youtube.com", "youtu.be")

    @classmethod
    def required_link_count(cls, task_type: str | None) -> int:
        if (task_type or "").strip().lower() == "longform":
            return cls.LONGFORM_REQUIRED_LINKS
        return cls.SHORTS_REQUIRED_LINKS

    @classmethod
    def extract_links(cls, text: str) -> list[str]:
        return [match.group(0).rstrip(".,);]") for match in cls.URL_PATTERN.finditer(text)]

    @classmethod
    def _allowed_domains(cls, task_type: str | None) -> tuple[str, ...]:
        if (task_type or "").strip().lower() == "longform":
            return cls.LONGFORM_ALLOWED_DOMAINS
        return cls.SHORTS_ALLOWED_DOMAINS

    @classmethod
    def _matches_allowed_platform(cls, link: str, task_type: str | None) -> bool:
        normalized = link.lower()
        return any(domain in normalized for domain in cls._allowed_domains(task_type))

    @classmethod
    def ensure_valid_submission(cls, text: str, task_type: str | None) -> None:
        links = cls.extract_links(text)
        required_count = cls.required_link_count(task_type)
        if len(links) != required_count:
            raise TechnicalTaskSubmissionInvalidLinkCountError()
        if not all(cls._matches_allowed_platform(link, task_type) for link in links):
            raise TechnicalTaskSubmissionInvalidPlatformError()
