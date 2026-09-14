from __future__ import annotations

import sqlite3

from adapters.outbound.repositories.sqlite_repository_base import SQLiteRepositoryBase
from application.dtos.technical_task_key_log_notification import TechnicalTaskKeyLogNotificationDTO
from application.dtos.technical_task_key_state import TechnicalTaskKeyStateDTO
from application.dtos.technical_task_timeout_notification import TechnicalTaskTimeoutNotificationDTO
from application.dtos.technical_task_review_resolution import TechnicalTaskReviewResolutionDTO
from application.ports.outbound.technical_task_repository import TechnicalTaskRepositoryPort
from domain.entities.product_key import ProductKey


class SQLiteTechnicalTaskRepository(SQLiteRepositoryBase, TechnicalTaskRepositoryPort):
    REJECT_COOLDOWN_SQL = "+4 days"

    async def create_technical_task_review(
        self,
        token: str,
        manager_user_id: int,
        applicant_user_id: int,
        applicant_chat_id: int,
        applicant_username: str | None,
        submission_text: str,
        business_connection_id: str | None,
    ) -> None:
        def work(cur: sqlite3.Cursor) -> None:
            cur.execute(
                """
                INSERT INTO technical_task_reviews(
                    token,
                    manager_user_id,
                    applicant_user_id,
                    applicant_chat_id,
                    applicant_username,
                    submission_text,
                    business_connection_id,
                    status,
                    updated_at
                ) VALUES(?, ?, ?, ?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP)
                """,
                (
                    token,
                    manager_user_id,
                    applicant_user_id,
                    applicant_chat_id,
                    applicant_username,
                    submission_text,
                    business_connection_id,
                ),
            )

        await self.db.in_transaction(work)

    async def resolve_technical_task_review(self, token: str, approved: bool) -> TechnicalTaskReviewResolutionDTO | None:
        next_status = "approved" if approved else "rejected"
        next_step = "approved_by_manager" if approved else "rejected_by_manager"

        def work(cur: sqlite3.Cursor) -> TechnicalTaskReviewResolutionDTO | None:
            cur.execute(
                """
                SELECT applicant_chat_id, applicant_user_id, business_connection_id, status
                FROM technical_task_reviews
                WHERE token = ?
                """,
                (token,),
            )
            row = cur.fetchone()
            if row is None:
                return None

            applicant_chat_id, applicant_user_id, business_connection_id, status = row
            current_status = str(status)
            if current_status != "pending":
                return TechnicalTaskReviewResolutionDTO(
                    applicant_chat_id=int(applicant_chat_id),
                    applicant_user_id=int(applicant_user_id),
                    business_connection_id=str(business_connection_id) if business_connection_id else None,
                    status=current_status,
                    was_updated=False,
                )

            cur.execute(
                """
                UPDATE technical_task_reviews
                SET status = ?, resolved_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE token = ?
                """,
                (next_status, token),
            )
            cur.execute(
                """
                UPDATE technical_task_stage
                SET status = ?,
                    current_step = ?,
                    completed_at = CASE
                        WHEN completed_at IS NULL THEN CURRENT_TIMESTAMP
                        ELSE completed_at
                    END,
                    last_activity_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE applicant_chat_id = ?
                """,
                (next_status, next_step, int(applicant_chat_id)),
            )
            cur.execute(
                """
                INSERT INTO technical_task_stage_log(applicant_chat_id, event_type, event_data)
                VALUES(?, ?, ?)
                """,
                (
                    int(applicant_chat_id),
                    "task_approved" if approved else "task_rejected",
                    token,
                ),
            )
            if not approved:
                cur.execute(
                    f"""
                    INSERT INTO dialog_blocks(dialog_id, reason, expires_at, created_at, updated_at)
                    VALUES(?, 'reject_cooldown', datetime(CURRENT_TIMESTAMP, '{self.REJECT_COOLDOWN_SQL}'), CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT(dialog_id) DO UPDATE SET
                        reason='reject_cooldown',
                        expires_at=datetime(CURRENT_TIMESTAMP, '{self.REJECT_COOLDOWN_SQL}'),
                        updated_at=CURRENT_TIMESTAMP
                    """,
                    (int(applicant_chat_id),),
                )
                cur.execute(
                    f"""
                    INSERT INTO dialog_state(dialog_id, human_takeover, auto_closed, troll_blocked, reject_cooldown_until, updated_at)
                    VALUES(?, 0, 1, 0, datetime(CURRENT_TIMESTAMP, '{self.REJECT_COOLDOWN_SQL}'), CURRENT_TIMESTAMP)
                    ON CONFLICT(dialog_id) DO UPDATE SET
                        human_takeover=0,
                        auto_closed=1,
                        troll_blocked=0,
                        reject_cooldown_until=datetime(CURRENT_TIMESTAMP, '{self.REJECT_COOLDOWN_SQL}'),
                        updated_at=CURRENT_TIMESTAMP
                    """,
                    (int(applicant_chat_id),),
                )
                cur.execute("DELETE FROM dialog_messages WHERE dialog_id = ?", (int(applicant_chat_id),))
                cur.execute("DELETE FROM dialog_guard WHERE dialog_id = ?", (int(applicant_chat_id),))
            return TechnicalTaskReviewResolutionDTO(
                applicant_chat_id=int(applicant_chat_id),
                applicant_user_id=int(applicant_user_id),
                business_connection_id=str(business_connection_id) if business_connection_id else None,
                status=next_status,
                was_updated=True,
            )

        return await self.db.in_transaction(work)

    async def start_technical_task_stage(self, applicant_chat_id: int, task_type: str, max_key_count: int) -> None:
        await self.start_technical_task_stage_with_connection(
            applicant_chat_id=applicant_chat_id,
            task_type=task_type,
            max_key_count=max_key_count,
            business_connection_id=None,
        )

    async def start_technical_task_stage_with_connection(
        self,
        applicant_chat_id: int,
        task_type: str,
        max_key_count: int,
        business_connection_id: str | None,
    ) -> None:
        def work(cur: sqlite3.Cursor) -> None:
            cur.execute(
                """
                UPDATE technical_task_stage
                SET status='awaiting_consent',
                    task_type=?,
                    business_connection_id=?,
                    current_step='task_sent',
                    product_key=NULL,
                    key_count=0,
                    max_key_count=?,
                    task_sent_at=CURRENT_TIMESTAMP,
                    started_at=NULL,
                    first_key_time=NULL,
                    last_key_time=NULL,
                    completed_at=NULL,
                    last_activity_at=CURRENT_TIMESTAMP,
                    updated_at=CURRENT_TIMESTAMP
                WHERE applicant_chat_id = ?
                """,
                (task_type, business_connection_id, max_key_count, applicant_chat_id),
            )
            if cur.rowcount == 0:
                cur.execute(
                    """
                    INSERT INTO technical_task_stage(
                        applicant_chat_id,
                        status,
                        task_type,
                        business_connection_id,
                        current_step,
                        product_key,
                        max_key_count,
                        task_sent_at,
                        started_at,
                        last_activity_at,
                        updated_at
                    ) VALUES(?, 'awaiting_consent', ?, ?, 'task_sent', NULL, ?, CURRENT_TIMESTAMP, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                    (applicant_chat_id, task_type, business_connection_id, max_key_count),
                )
            cur.execute(
                """
                INSERT INTO technical_task_stage_log(applicant_chat_id, event_type, event_data)
                VALUES(?, 'task_sent', ?)
                """,
                (applicant_chat_id, "technical task activated"),
            )

        await self.db.in_transaction(work)

    async def mark_technical_task_started(self, applicant_chat_id: int) -> None:
        def work(cur: sqlite3.Cursor) -> None:
            cur.execute(
                """
                UPDATE technical_task_stage
                SET status='task_started',
                    current_step='awaiting_key_request',
                    started_at=CASE
                        WHEN started_at IS NULL THEN CURRENT_TIMESTAMP
                        ELSE started_at
                    END,
                    last_activity_at=CURRENT_TIMESTAMP,
                    updated_at=CURRENT_TIMESTAMP
                WHERE applicant_chat_id = ?
                """,
                (applicant_chat_id,),
            )
            if cur.rowcount == 0:
                return
            cur.execute(
                """
                INSERT INTO technical_task_stage_log(applicant_chat_id, event_type, event_data)
                VALUES(?, 'task_started', ?)
                """,
                (applicant_chat_id, "technical task started by applicant"),
            )

        await self.db.in_transaction(work)

    async def mark_technical_task_submitted(self, applicant_chat_id: int, submission_text: str) -> None:
        def work(cur: sqlite3.Cursor) -> None:
            cur.execute(
                """
                UPDATE technical_task_stage
                SET status='submitted',
                    current_step='awaiting_manager_review',
                    completed_at=CURRENT_TIMESTAMP,
                    last_activity_at=CURRENT_TIMESTAMP,
                    updated_at=CURRENT_TIMESTAMP
                WHERE applicant_chat_id = ?
                """,
                (applicant_chat_id,),
            )
            if cur.rowcount == 0:
                return
            cur.execute(
                """
                INSERT INTO technical_task_stage_log(applicant_chat_id, event_type, event_data)
                VALUES(?, 'task_submitted', ?)
                """,
                (applicant_chat_id, submission_text),
            )

        await self.db.in_transaction(work)

    async def mark_technical_task_declined(self, applicant_chat_id: int, decline_text: str) -> None:
        def work(cur: sqlite3.Cursor) -> None:
            cur.execute(
                """
                UPDATE technical_task_stage
                SET status='declined',
                    current_step='declined_by_applicant',
                    completed_at=CURRENT_TIMESTAMP,
                    last_activity_at=CURRENT_TIMESTAMP,
                    updated_at=CURRENT_TIMESTAMP
                WHERE applicant_chat_id = ?
                """,
                (applicant_chat_id,),
            )
            if cur.rowcount == 0:
                return
            cur.execute(
                """
                INSERT INTO technical_task_stage_log(applicant_chat_id, event_type, event_data)
                VALUES(?, 'task_declined', ?)
                """,
                (applicant_chat_id, decline_text),
            )

        await self.db.in_transaction(work)

    async def apply_reject_cooldown(self, applicant_chat_id: int) -> None:
        def work(cur: sqlite3.Cursor) -> None:
            cur.execute(
                f"""
                INSERT INTO dialog_blocks(dialog_id, reason, expires_at, created_at, updated_at)
                VALUES(?, 'reject_cooldown', datetime(CURRENT_TIMESTAMP, '{self.REJECT_COOLDOWN_SQL}'), CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(dialog_id) DO UPDATE SET
                    reason='reject_cooldown',
                    expires_at=datetime(CURRENT_TIMESTAMP, '{self.REJECT_COOLDOWN_SQL}'),
                    updated_at=CURRENT_TIMESTAMP
                """,
                (applicant_chat_id,),
            )
            cur.execute(
                f"""
                INSERT INTO dialog_state(dialog_id, human_takeover, auto_closed, troll_blocked, reject_cooldown_until, updated_at)
                VALUES(?, 0, 1, 0, datetime(CURRENT_TIMESTAMP, '{self.REJECT_COOLDOWN_SQL}'), CURRENT_TIMESTAMP)
                ON CONFLICT(dialog_id) DO UPDATE SET
                    human_takeover=0,
                    auto_closed=1,
                    troll_blocked=0,
                    reject_cooldown_until=datetime(CURRENT_TIMESTAMP, '{self.REJECT_COOLDOWN_SQL}'),
                    updated_at=CURRENT_TIMESTAMP
                """,
                (applicant_chat_id,),
            )
            cur.execute("DELETE FROM dialog_messages WHERE dialog_id = ?", (applicant_chat_id,))
            cur.execute("DELETE FROM dialog_guard WHERE dialog_id = ?", (applicant_chat_id,))

        await self.db.in_transaction(work)

    async def get_technical_task_key_state(self, applicant_chat_id: int) -> TechnicalTaskKeyStateDTO | None:
        def work(cur: sqlite3.Cursor) -> TechnicalTaskKeyStateDTO | None:
            cur.execute(
                """
                SELECT status, task_type, product_key, key_count, max_key_count, first_key_time, last_key_time
                FROM technical_task_stage
                WHERE applicant_chat_id = ?
                LIMIT 1
                """,
                (applicant_chat_id,),
            )
            row = cur.fetchone()
            if row is None:
                return None

            status, task_type, product_key, key_count, max_key_count, first_key_time, last_key_time = row
            return TechnicalTaskKeyStateDTO(
                status=str(status or "pending"),
                task_type=str(task_type or "shorts"),
                product_key=ProductKey(str(product_key)) if product_key else None,
                key_count=int(key_count or 0),
                max_key_count=int(max_key_count or 6),
                first_key_time=self.parse_db_timestamp(str(first_key_time) if first_key_time else None),
                last_key_time=self.parse_db_timestamp(str(last_key_time) if last_key_time else None),
            )

        return await self.db.in_transaction(work)

    async def has_started_technical_task(self, applicant_chat_id: int) -> bool:
        def work(cur: sqlite3.Cursor) -> bool:
            cur.execute(
                """
                SELECT 1
                FROM technical_task_stage
                WHERE applicant_chat_id = ?
                  AND status IN ('awaiting_consent', 'task_started', 'key_issued', 'submitted', 'approved')
                LIMIT 1
                """,
                (applicant_chat_id,),
            )
            return cur.fetchone() is not None

        return await self.db.in_transaction(work)

    async def mark_technical_task_key_issued(self, applicant_chat_id: int) -> None:
        def work(cur: sqlite3.Cursor) -> None:
            cur.execute(
                """
                SELECT product_key, key_count
                FROM technical_task_stage
                WHERE applicant_chat_id = ?
                LIMIT 1
                """,
                (applicant_chat_id,),
            )
            row = cur.fetchone()
            if row is None:
                return

            product_key, key_count = row
            cur.execute(
                """
                UPDATE technical_task_stage
                SET status='key_issued',
                    current_step='key_sent',
                    key_count=?,
                    first_key_time=CASE
                        WHEN first_key_time IS NULL THEN CURRENT_TIMESTAMP
                        ELSE first_key_time
                    END,
                    last_key_time=CURRENT_TIMESTAMP,
                    last_activity_at=CURRENT_TIMESTAMP,
                    updated_at=CURRENT_TIMESTAMP
                WHERE applicant_chat_id = ?
                """,
                (int(key_count or 0) + 1, applicant_chat_id),
            )
            cur.execute(
                """
                INSERT INTO technical_task_stage_log(applicant_chat_id, event_type, event_data)
                VALUES(?, 'key_issued', ?)
                """,
                (applicant_chat_id, str(product_key) if product_key else "missing_product_key"),
            )

        await self.db.in_transaction(work)

    async def claim_available_product_key(self, applicant_chat_id: int) -> ProductKey | None:
        def work(cur: sqlite3.Cursor) -> ProductKey | None:
            cur.execute(
                """
                SELECT product_key
                FROM technical_task_stage
                WHERE applicant_chat_id = ?
                LIMIT 1
                """,
                (applicant_chat_id,),
            )
            row = cur.fetchone()
            if row is not None and row[0]:
                return ProductKey(str(row[0]))

            cur.execute(
                """
                SELECT name
                FROM product_keys
                WHERE owner IS NULL
                ORDER BY rowid ASC
                LIMIT 1
                """
            )
            free_row = cur.fetchone()
            if free_row is None:
                return None

            key_name = str(free_row[0])
            cur.execute(
                """
                UPDATE product_keys
                SET owner = ?, issued_time = CURRENT_TIMESTAMP
                WHERE name = ? AND owner IS NULL
                """,
                (applicant_chat_id, key_name),
            )
            if cur.rowcount == 0:
                return None

            cur.execute(
                """
                UPDATE technical_task_stage
                SET product_key = ?, last_activity_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE applicant_chat_id = ?
                """,
                (key_name, applicant_chat_id),
            )
            cur.execute(
                """
                INSERT INTO technical_task_stage_log(applicant_chat_id, event_type, event_data)
                VALUES(?, 'key_reserved', ?)
                """,
                (applicant_chat_id, key_name),
            )
            return ProductKey(key_name)

        return await self.db.in_transaction(work)

    async def add_product_keys(self, keys: list[ProductKey]) -> int:
        def work(cur: sqlite3.Cursor) -> int:
            inserted = 0
            for key in keys:
                cur.execute(
                    """
                    INSERT OR IGNORE INTO product_keys(name, owner, issued_time)
                    VALUES(?, NULL, NULL)
                    """,
                    (str(key),),
                )
                inserted += cur.rowcount
            return inserted

        return await self.db.in_transaction(work)

    async def collect_expired_technical_tasks(self) -> int:
        def work(cur: sqlite3.Cursor) -> int:
            cur.execute(
                """
                SELECT applicant_chat_id, business_connection_id, task_type
                FROM technical_task_stage
                WHERE status IN ('awaiting_consent', 'task_started', 'key_issued')
                  AND task_sent_at IS NOT NULL
                  AND (
                    (task_type = 'longform' AND datetime(task_sent_at, '+9 days', '+12 hours') <= CURRENT_TIMESTAMP)
                    OR
                    (task_type != 'longform' AND datetime(task_sent_at, '+7 days', '+12 hours') <= CURRENT_TIMESTAMP)
                  )
                  AND applicant_chat_id NOT IN (
                    SELECT applicant_chat_id FROM technical_task_timeouts
                  )
                """
            )
            rows = cur.fetchall()
            inserted = 0
            for applicant_chat_id, business_connection_id, task_type in rows:
                cur.execute(
                    """
                    INSERT INTO technical_task_timeouts(
                        applicant_chat_id,
                        business_connection_id,
                        task_type,
                        timed_out_at
                    ) VALUES(?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (
                        int(applicant_chat_id),
                        str(business_connection_id) if business_connection_id else None,
                        str(task_type),
                    ),
                )
                cur.execute(
                    """
                    UPDATE technical_task_stage
                    SET status='expired',
                        current_step='timed_out',
                        completed_at=CURRENT_TIMESTAMP,
                        last_activity_at=CURRENT_TIMESTAMP,
                        updated_at=CURRENT_TIMESTAMP
                    WHERE applicant_chat_id = ?
                    """,
                    (int(applicant_chat_id),),
                )
                cur.execute(
                    """
                    INSERT INTO technical_task_stage_log(applicant_chat_id, event_type, event_data)
                    VALUES(?, 'task_timed_out', ?)
                    """,
                    (int(applicant_chat_id), str(task_type)),
                )
                cur.execute(
                    f"""
                    INSERT INTO dialog_blocks(dialog_id, reason, expires_at, created_at, updated_at)
                    VALUES(?, 'reject_cooldown', datetime(CURRENT_TIMESTAMP, '{self.REJECT_COOLDOWN_SQL}'), CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT(dialog_id) DO UPDATE SET
                        reason='reject_cooldown',
                        expires_at=datetime(CURRENT_TIMESTAMP, '{self.REJECT_COOLDOWN_SQL}'),
                        updated_at=CURRENT_TIMESTAMP
                    """,
                    (int(applicant_chat_id),),
                )
                cur.execute(
                    f"""
                    INSERT INTO dialog_state(dialog_id, human_takeover, auto_closed, troll_blocked, reject_cooldown_until, updated_at)
                    VALUES(?, 0, 1, 0, datetime(CURRENT_TIMESTAMP, '{self.REJECT_COOLDOWN_SQL}'), CURRENT_TIMESTAMP)
                    ON CONFLICT(dialog_id) DO UPDATE SET
                        human_takeover=0,
                        auto_closed=1,
                        troll_blocked=0,
                        reject_cooldown_until=datetime(CURRENT_TIMESTAMP, '{self.REJECT_COOLDOWN_SQL}'),
                        updated_at=CURRENT_TIMESTAMP
                    """,
                    (int(applicant_chat_id),),
                )
                inserted += 1
            return inserted

        return await self.db.in_transaction(work)

    async def get_pending_technical_task_timeout_notifications(self) -> list[TechnicalTaskTimeoutNotificationDTO]:
        def work(cur: sqlite3.Cursor) -> list[TechnicalTaskTimeoutNotificationDTO]:
            cur.execute(
                """
                SELECT
                    t.applicant_chat_id,
                    ar.applicant_user_id,
                    ar.applicant_username,
                    t.business_connection_id,
                    t.task_type,
                    t.timed_out_at,
                    s.product_key,
                    s.key_count,
                    t.notified_at
                FROM technical_task_timeouts t
                LEFT JOIN technical_task_stage s
                    ON s.applicant_chat_id = t.applicant_chat_id
                LEFT JOIN (
                    SELECT applicant_chat_id, MAX(created_at) AS latest_created_at
                    FROM application_reviews
                    GROUP BY applicant_chat_id
                ) latest_ar
                    ON latest_ar.applicant_chat_id = t.applicant_chat_id
                LEFT JOIN application_reviews ar
                    ON ar.applicant_chat_id = latest_ar.applicant_chat_id
                   AND ar.created_at = latest_ar.latest_created_at
                WHERE notified_at IS NULL
                ORDER BY timed_out_at ASC
                """
            )
            rows = cur.fetchall()
            return [
                TechnicalTaskTimeoutNotificationDTO(
                    applicant_chat_id=int(applicant_chat_id),
                    applicant_user_id=int(applicant_user_id) if applicant_user_id is not None else None,
                    applicant_username=str(applicant_username) if applicant_username else None,
                    business_connection_id=str(business_connection_id) if business_connection_id else None,
                    task_type=str(task_type),
                    timed_out_at=str(timed_out_at),
                    product_key=str(product_key) if product_key else None,
                    key_count=int(key_count or 0),
                    notified_at=str(notified_at) if notified_at else None,
                )
                for applicant_chat_id, applicant_user_id, applicant_username, business_connection_id, task_type, timed_out_at, product_key, key_count, notified_at in rows
            ]

        return await self.db.in_transaction(work)

    async def mark_technical_task_timeout_notified(self, applicant_chat_id: int) -> None:
        def work(cur: sqlite3.Cursor) -> None:
            cur.execute(
                """
                UPDATE technical_task_timeouts
                SET notified_at=CURRENT_TIMESTAMP
                WHERE applicant_chat_id = ?
                """,
                (applicant_chat_id,),
            )

        await self.db.in_transaction(work)

    async def get_pending_technical_task_key_logs(self) -> list[TechnicalTaskKeyLogNotificationDTO]:
        def work(cur: sqlite3.Cursor) -> list[TechnicalTaskKeyLogNotificationDTO]:
            cur.execute(
                """
                SELECT
                    l.id,
                    l.applicant_chat_id,
                    ar.applicant_user_id,
                    ar.applicant_username,
                    l.event_type,
                    l.event_data,
                    l.created_at
                FROM technical_task_stage_log l
                LEFT JOIN (
                    SELECT applicant_chat_id, MAX(created_at) AS latest_created_at
                    FROM application_reviews
                    GROUP BY applicant_chat_id
                ) latest_ar
                    ON latest_ar.applicant_chat_id = l.applicant_chat_id
                LEFT JOIN application_reviews ar
                    ON ar.applicant_chat_id = latest_ar.applicant_chat_id
                   AND ar.created_at = latest_ar.latest_created_at
                WHERE notified_at IS NULL
                  AND event_type IN ('key_reserved', 'key_issued')
                ORDER BY l.id ASC
                """
            )
            rows = cur.fetchall()
            return [
                TechnicalTaskKeyLogNotificationDTO(
                    log_id=int(log_id),
                    applicant_chat_id=int(applicant_chat_id),
                    applicant_user_id=int(applicant_user_id) if applicant_user_id is not None else None,
                    applicant_username=str(applicant_username) if applicant_username else None,
                    event_type=str(event_type),
                    event_data=str(event_data) if event_data else None,
                    created_at=str(created_at),
                )
                for log_id, applicant_chat_id, applicant_user_id, applicant_username, event_type, event_data, created_at in rows
            ]

        return await self.db.in_transaction(work)

    async def mark_technical_task_key_log_notified(self, log_id: int) -> None:
        def work(cur: sqlite3.Cursor) -> None:
            cur.execute(
                """
                UPDATE technical_task_stage_log
                SET notified_at=CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (log_id,),
            )

        await self.db.in_transaction(work)

    async def get_low_product_key_alert(self, threshold: int) -> int | None:
        state_key = "low_product_key_alert_count"

        def work(cur: sqlite3.Cursor) -> int | None:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM product_keys
                WHERE owner IS NULL
                """
            )
            remaining_count = int(cur.fetchone()[0] or 0)

            if remaining_count >= threshold:
                cur.execute(
                    """
                    DELETE FROM system_state
                    WHERE key = ?
                    """,
                    (state_key,),
                )
                return None

            cur.execute(
                """
                SELECT value
                FROM system_state
                WHERE key = ?
                LIMIT 1
                """,
                (state_key,),
            )
            row = cur.fetchone()
            last_alert_count = int(str(row[0])) if row is not None and row[0] is not None else None
            if last_alert_count is not None and remaining_count >= last_alert_count:
                return None

            return remaining_count

        return await self.db.in_transaction(work)

    async def mark_low_product_key_alert_sent(self, remaining_count: int) -> None:
        state_key = "low_product_key_alert_count"

        def work(cur: sqlite3.Cursor) -> None:
            cur.execute(
                """
                INSERT INTO system_state(key, value, updated_at)
                VALUES(?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET
                    value=excluded.value,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (state_key, str(remaining_count)),
            )

        await self.db.in_transaction(work)

    async def add_pending_chat_acceptance(self, applicant_chat_id: int, applicant_user_id: int, target_chat_id: int) -> None:
        def work(cur: sqlite3.Cursor) -> None:
            cur.execute(
                """
                INSERT INTO pending_chat_acceptances(applicant_chat_id, applicant_user_id, target_chat_id, created_at)
                VALUES(?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(applicant_chat_id) DO UPDATE SET
                    applicant_user_id=excluded.applicant_user_id,
                    target_chat_id=excluded.target_chat_id,
                    created_at=CURRENT_TIMESTAMP
                """,
                (applicant_chat_id, applicant_user_id, target_chat_id),
            )

        await self.db.in_transaction(work)

    async def remove_pending_chat_acceptance(self, applicant_user_id: int, target_chat_id: int) -> bool:
        def work(cur: sqlite3.Cursor) -> bool:
            cur.execute(
                "DELETE FROM pending_chat_acceptances WHERE applicant_user_id = ? AND target_chat_id = ?",
                (applicant_user_id, target_chat_id),
            )
            return cur.rowcount > 0

        return await self.db.in_transaction(work)
