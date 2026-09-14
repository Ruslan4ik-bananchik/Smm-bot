from __future__ import annotations

import sqlite3

from adapters.outbound.repositories.sqlite_repository_base import SQLiteRepositoryBase
from application.ports.outbound.telegram_asset_repository import TelegramAssetRepositoryPort


class SQLiteTelegramAssetRepository(SQLiteRepositoryBase, TelegramAssetRepositoryPort):
    async def save_asset_file(self, name: str, file_id: str, file_name: str | None, owner: int) -> None:
        def work(cur: sqlite3.Cursor) -> None:
            cur.execute(
                """
                INSERT INTO telegram_assets(name, file_id, file_name, owner, updated_at)
                VALUES(?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(name) DO UPDATE SET
                    file_id=excluded.file_id,
                    file_name=excluded.file_name,
                    owner=excluded.owner,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (name, file_id, file_name, owner),
            )

        await self.db.in_transaction(work)

    async def get_asset_file(self, name: str) -> tuple[str, str | None] | None:
        def work(cur: sqlite3.Cursor) -> tuple[str, str | None] | None:
            cur.execute("SELECT file_id, file_name FROM telegram_assets WHERE name = ? LIMIT 1", (name,))
            row = cur.fetchone()
            if row is None:
                return None
            return str(row[0]), str(row[1]) if row[1] else None

        return await self.db.in_transaction(work)

    async def save_asset_text(self, name: str, value: str, owner: int) -> None:
        def work(cur: sqlite3.Cursor) -> None:
            cur.execute(
                """
                INSERT INTO telegram_text_assets(name, value, owner, updated_at)
                VALUES(?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(name) DO UPDATE SET
                    value=excluded.value,
                    owner=excluded.owner,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (name, value, owner),
            )

        await self.db.in_transaction(work)

    async def get_asset_text(self, name: str) -> str | None:
        def work(cur: sqlite3.Cursor) -> str | None:
            cur.execute("SELECT value FROM telegram_text_assets WHERE name = ? LIMIT 1", (name,))
            row = cur.fetchone()
            if row is None:
                return None
            return str(row[0])

        return await self.db.in_transaction(work)
