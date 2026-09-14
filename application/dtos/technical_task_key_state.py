from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from domain.entities.product_key import ProductKey


@dataclass(frozen=True)
class TechnicalTaskKeyStateDTO:
    status: str
    task_type: str
    product_key: ProductKey | None
    key_count: int
    max_key_count: int
    first_key_time: datetime | None
    last_key_time: datetime | None
