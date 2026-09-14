from __future__ import annotations

import sqlite3

from adapters.outbound.repositories.sqlite_repository_base import SQLiteRepositoryBase
from application.ports.outbound.conversation_repository import ConversationRepositoryPort
from domain.entities.dialog_policy_state import DialogPolicyState


class SQLiteConversationRepository(SQLiteRepositoryBase, ConversationRepositoryPort):
    REJECT_COOLDOWN_SQL = "+4 days"
    BLOCK_REASON_CLOSED = "closed"
    BLOCK_REASON_REJECT_COOLDOWN = "reject_cooldown"
    BLOCK_REASON_TROLL_COOLDOWN = "troll_cooldown"

    @classmethod
    def _sync_state_from_block(
        cls,
        cur: sqlite3.Cursor,
        dialog_id: int,
        *,
        reason: str | None,
        expires_at_sql: str | None = None,
    ) -> None:
        troll_blocked = 1 if reason == cls.BLOCK_REASON_TROLL_COOLDOWN else 0
        auto_closed = 1 if reason is not None else 0
        reject_cooldown_expr = expires_at_sql if expires_at_sql is not None else "NULL"
        cur.execute(
            f"""
            INSERT INTO dialog_state(
                dialog_id,
                human_takeover,
                auto_closed,
                troll_blocked,
                reject_cooldown_until,
                updated_at
            )
            VALUES(?, 0, ?, ?, {reject_cooldown_expr}, CURRENT_TIMESTAMP)
            ON CONFLICT(dialog_id) DO UPDATE SET
                human_takeover=0,
                auto_closed=excluded.auto_closed,
                troll_blocked=excluded.troll_blocked,
                reject_cooldown_until={reject_cooldown_expr},
                updated_at=CURRENT_TIMESTAMP
            """,
            (dialog_id, auto_closed, troll_blocked),
        )

    @classmethod
    def _upsert_dialog_block(
        cls,
        cur: sqlite3.Cursor,
        dialog_id: int,
        *,
        reason: str,
        expires_at_sql: str | None = None,
    ) -> None:
        expires_value_expr = expires_at_sql if expires_at_sql is not None else "NULL"
        cur.execute(
            f"""
            INSERT INTO dialog_blocks(dialog_id, reason, expires_at, created_at, updated_at)
            VALUES(?, ?, {expires_value_expr}, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(dialog_id) DO UPDATE SET
                reason=excluded.reason,
                expires_at={expires_value_expr},
                updated_at=CURRENT_TIMESTAMP
            """,
            (dialog_id, reason),
        )
        cls._sync_state_from_block(
            cur,
            dialog_id,
            reason=reason,
            expires_at_sql=expires_at_sql,
        )

    async def get_dialog_policy_state(self, dialog_id: int) -> DialogPolicyState:
        def work(cur: sqlite3.Cursor) -> DialogPolicyState:
            cur.execute(
                """
                SELECT
                    COALESCE(ds.human_takeover, 0),
                    db.reason,
                    db.expires_at,
                    tts.status,
                    dg.last_user_text,
                    dg.last_user_at
                FROM dialog_state ds
                LEFT JOIN dialog_blocks db
                    ON db.dialog_id = ds.dialog_id
                LEFT JOIN technical_task_stage tts
                    ON tts.applicant_chat_id = ds.dialog_id
                LEFT JOIN dialog_guard dg
                    ON dg.dialog_id = ds.dialog_id
                WHERE ds.dialog_id = ?
                LIMIT 1
                """,
                (dialog_id,),
            )
            row = cur.fetchone()
            if row is None:
                cur.execute(
                    """
                    SELECT
                        db.reason,
                        db.expires_at,
                        tts.status,
                        dg.last_user_text,
                        dg.last_user_at
                    FROM dialog_blocks db
                    LEFT JOIN technical_task_stage tts
                        ON tts.applicant_chat_id = db.dialog_id
                    LEFT JOIN dialog_guard dg
                        ON dg.dialog_id = db.dialog_id
                    WHERE db.dialog_id = ?
                    LIMIT 1
                    """,
                    (dialog_id,),
                )
                block_row = cur.fetchone()
                if block_row is None:
                    cur.execute(
                        """
                        SELECT status
                        FROM technical_task_stage
                        WHERE applicant_chat_id = ?
                        LIMIT 1
                        """,
                        (dialog_id,),
                    )
                    stage_row = cur.fetchone()
                    return DialogPolicyState(
                        human_takeover=False,
                        block_reason=None,
                        block_expires_at=None,
                        technical_task_status=str(stage_row[0]) if stage_row is not None and stage_row[0] else None,
                        last_user_text=None,
                        last_user_at=None,
                    )

                return DialogPolicyState(
                    human_takeover=False,
                    block_reason=str(block_row[0]) if block_row[0] else None,
                    block_expires_at=str(block_row[1]) if block_row[1] else None,
                    technical_task_status=str(block_row[2]) if block_row[2] else None,
                    last_user_text=str(block_row[3]) if block_row[3] else None,
                    last_user_at=int(block_row[4]) if block_row[4] is not None else None,
                )

            return DialogPolicyState(
                human_takeover=bool(int(row[0] or 0)),
                block_reason=str(row[1]) if row[1] else None,
                block_expires_at=str(row[2]) if row[2] else None,
                technical_task_status=str(row[3]) if row[3] else None,
                last_user_text=str(row[4]) if row[4] else None,
                last_user_at=int(row[5]) if row[5] is not None else None,
            )

        return await self.db.in_transaction(work)

    async def get_dialog_history(self, dialog_id: int, history_limit: int) -> list[str]:
        def work(cur: sqlite3.Cursor) -> list[str]:
            cur.execute(
                "SELECT text FROM dialog_messages WHERE dialog_id = ? ORDER BY id DESC LIMIT ?",
                (dialog_id, history_limit),
            )
            return [str(row[0]) for row in reversed(cur.fetchall())]

        return await self.db.in_transaction(work)

    async def store_user_message(self, dialog_id: int, text: str, created_at: int) -> None:
        def work(cur: sqlite3.Cursor) -> None:
            cur.execute("INSERT INTO dialog_messages(dialog_id, text) VALUES(?, ?)", (dialog_id, text))
            cur.execute(
                """
                INSERT INTO dialog_guard(dialog_id, last_user_text, last_user_at)
                VALUES(?, ?, ?)
                ON CONFLICT(dialog_id) DO UPDATE SET
                    last_user_text=excluded.last_user_text,
                    last_user_at=excluded.last_user_at
                """,
                (dialog_id, text, created_at),
            )

        await self.db.in_transaction(work)

    async def mark_human_takeover(self, dialog_id: int) -> None:
        def work(cur: sqlite3.Cursor) -> None:
            cur.execute(
                """
                INSERT INTO dialog_state(dialog_id, human_takeover, auto_closed, updated_at)
                VALUES(?, 1, 0, CURRENT_TIMESTAMP)
                ON CONFLICT(dialog_id) DO UPDATE SET
                    human_takeover=1,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (dialog_id,),
            )

        await self.db.in_transaction(work)

    async def clear_dialog_block(self, dialog_id: int) -> None:
        def work(cur: sqlite3.Cursor) -> None:
            cur.execute("DELETE FROM dialog_blocks WHERE dialog_id = ?", (dialog_id,))
            self._sync_state_from_block(cur, dialog_id, reason=None)

        await self.db.in_transaction(work)

    async def append_message(
        self,
        dialog_id: int,
        text: str,
        auto_close_eligible: bool = False,
        force_auto_close: bool = False,
    ) -> None:
        if not text:
            return

        def work(cur: sqlite3.Cursor) -> None:
            cur.execute("INSERT INTO dialog_messages(dialog_id, text) VALUES(?, ?)", (dialog_id, text))
            if auto_close_eligible and force_auto_close:
                self._upsert_dialog_block(cur, dialog_id, reason=self.BLOCK_REASON_CLOSED)

        await self.db.in_transaction(work)

    async def close_dialog(self, dialog_id: int) -> None:
        def work(cur: sqlite3.Cursor) -> None:
            self._upsert_dialog_block(cur, dialog_id, reason=self.BLOCK_REASON_CLOSED)

        await self.db.in_transaction(work)

    async def close_dialog_with_reject_cooldown(self, dialog_id: int) -> None:
        def work(cur: sqlite3.Cursor) -> None:
            self._upsert_dialog_block(
                cur,
                dialog_id,
                reason=self.BLOCK_REASON_REJECT_COOLDOWN,
                expires_at_sql=f"datetime(CURRENT_TIMESTAMP, '{self.REJECT_COOLDOWN_SQL}')",
            )
            cur.execute("DELETE FROM dialog_messages WHERE dialog_id = ?", (dialog_id,))
            cur.execute("DELETE FROM dialog_guard WHERE dialog_id = ?", (dialog_id,))

        await self.db.in_transaction(work)

    async def mark_dialog_as_troll(
        self,
        *,
        dialog_id: int,
        user_id: int,
        username: str | None,
        text: str,
        source_message_link: str | None,
        business_connection_id: str | None,
    ) -> None:
        def work(cur: sqlite3.Cursor) -> None:
            self._upsert_dialog_block(
                cur,
                dialog_id,
                reason=self.BLOCK_REASON_TROLL_COOLDOWN,
                expires_at_sql=f"datetime(CURRENT_TIMESTAMP, '{self.REJECT_COOLDOWN_SQL}')",
            )
            cur.execute("DELETE FROM dialog_messages WHERE dialog_id = ?", (dialog_id,))
            cur.execute("DELETE FROM dialog_guard WHERE dialog_id = ?", (dialog_id,))
            cur.execute(
                """
                INSERT INTO troll_reports(
                    applicant_chat_id,
                    applicant_user_id,
                    applicant_username,
                    troll_text,
                    source_message_link,
                    business_connection_id,
                    created_at,
                    updated_at
                ) VALUES(?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(applicant_chat_id) DO UPDATE SET
                    applicant_user_id=excluded.applicant_user_id,
                    applicant_username=excluded.applicant_username,
                    troll_text=excluded.troll_text,
                    source_message_link=excluded.source_message_link,
                    business_connection_id=excluded.business_connection_id,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (dialog_id, user_id, username, text, source_message_link, business_connection_id),
            )

        await self.db.in_transaction(work)

    async def upsert_business_connection(self, connection_id: str, owner_user_id: int, is_enabled: bool) -> None:
        def work(cur: sqlite3.Cursor) -> None:
            cur.execute(
                """
                INSERT INTO business_connections(connection_id, owner_user_id, is_enabled, updated_at)
                VALUES(?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(connection_id) DO UPDATE SET
                    owner_user_id=excluded.owner_user_id,
                    is_enabled=excluded.is_enabled,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (connection_id, owner_user_id, 1 if is_enabled else 0),
            )

        await self.db.in_transaction(work)

    async def get_business_connection_owner(self, connection_id: str) -> int | None:
        def work(cur: sqlite3.Cursor) -> int | None:
            cur.execute(
                """
                SELECT owner_user_id
                FROM business_connections
                WHERE connection_id = ?
                  AND is_enabled = 1
                LIMIT 1
                """,
                (connection_id,),
            )
            row = cur.fetchone()
            if row is None:
                return None
            return int(row[0])

        return await self.db.in_transaction(work)
