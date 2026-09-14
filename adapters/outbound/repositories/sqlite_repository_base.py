from __future__ import annotations

from datetime import datetime, timezone

from infra.database import SQLiteDatabase


class SQLiteRepositoryBase:
    APPLICATION_FLOW = "application"
    TECHNICAL_TASK_FLOW = "technical_task"

    def __init__(self, db: SQLiteDatabase):
        self.db = db

    @staticmethod
    def parse_db_timestamp(value: str | None) -> datetime | None:
        if not value:
            return None
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
