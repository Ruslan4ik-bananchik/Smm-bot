from __future__ import annotations

import sqlite3

from adapters.outbound.repositories.sqlite_repository_base import SQLiteRepositoryBase
from application.ports.outbound.blocklist_repository import BlocklistRepositoryPort


class SQLiteBlocklistRepository(SQLiteRepositoryBase, BlocklistRepositoryPort):
    async def add_user(self, user_id: int, reason: str | None = None) -> None:
        def work(cur: sqlite3.Cursor) -> None:
            cur.execute(
                """
                INSERT INTO blocked_users(user_id, reason, created_at, updated_at)
                VALUES(?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    reason=excluded.reason,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (user_id, reason),
            )

        await self.db.in_transaction(work)

    async def remove_user(self, user_id: int) -> bool:
        def work(cur: sqlite3.Cursor) -> bool:
            cur.execute(
                """
                DELETE FROM blocked_users
                WHERE user_id = ?
                """,
                (user_id,),
            )
            return cur.rowcount > 0

        return await self.db.in_transaction(work)

    async def contains_user(self, user_id: int) -> bool:
        def work(cur: sqlite3.Cursor) -> bool:
            cur.execute(
                """
                SELECT 1
                FROM blocked_users
                WHERE user_id = ?
                LIMIT 1
                """,
                (user_id,),
            )
            return cur.fetchone() is not None

        return await self.db.in_transaction(work)
