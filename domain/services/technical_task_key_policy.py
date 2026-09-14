from __future__ import annotations

from datetime import datetime, timedelta

from domain.exceptions.errors import (
    TechnicalTaskKeyLimitReachedError,
    TechnicalTaskKeyNotAssignedError,
    TechnicalTaskKeyReissueTooEarlyError,
)


class TechnicalTaskKeyPolicy:
    MAX_ISSUES = 6
    REISSUE_DELAY = timedelta(days=1)

    @classmethod
    def check_can_issue(
        cls,
        *,
        has_product_key: bool,
        key_count: int,
        max_issues: int,
        last_key_time: datetime | None,
        now: datetime,
    ) -> bool:
        if not has_product_key:
            raise TechnicalTaskKeyNotAssignedError()
        if key_count >= max_issues:
            raise TechnicalTaskKeyLimitReachedError()
        if last_key_time is not None and (now - last_key_time) < cls.REISSUE_DELAY:
            raise TechnicalTaskKeyReissueTooEarlyError()
        return key_count > 0
