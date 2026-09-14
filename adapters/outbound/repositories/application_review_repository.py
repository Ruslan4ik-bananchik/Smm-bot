from __future__ import annotations

import sqlite3

from adapters.outbound.repositories.sqlite_repository_base import SQLiteRepositoryBase
from application.dtos.application_review_resolution import ApplicationReviewResolutionDTO
from application.ports.outbound.application_review_repository import ApplicationReviewRepositoryPort
from domain.exceptions.errors import ApplicationRetakeLimitReachedError


class SQLiteApplicationReviewRepository(SQLiteRepositoryBase, ApplicationReviewRepositoryPort):
    REJECT_COOLDOWN_SQL = "+4 days"
    RETAKE_RESET_TECHNICAL_TASK_STATUSES = {"declined", "rejected", "expired"}

    async def create_application_review(
        self,
        token: str,
        manager_user_id: int,
        applicant_user_id: int,
        applicant_chat_id: int,
        applicant_username: str | None,
        application_text: str,
        video_format: str | None,
        video_format_code: str | None,
        business_connection_id: str | None,
    ) -> None:
        def work(cur: sqlite3.Cursor) -> None:
            cur.execute(
                """
                SELECT status
                FROM technical_task_stage
                WHERE applicant_chat_id = ?
                LIMIT 1
                """,
                (applicant_chat_id,),
            )
            stage_row = cur.fetchone()
            technical_task_status = str(stage_row[0]) if stage_row is not None and stage_row[0] else None

            cur.execute(
                """
                INSERT INTO dialog_state(
                    dialog_id,
                    human_takeover,
                    auto_closed,
                    troll_blocked,
                    reject_cooldown_until,
                    application_retake_count,
                    updated_at
                )
                VALUES(?, 0, 0, 0, NULL, 0, CURRENT_TIMESTAMP)
                ON CONFLICT(dialog_id) DO UPDATE SET
                    human_takeover=0,
                    auto_closed=0,
                    troll_blocked=0,
                    reject_cooldown_until=NULL,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (applicant_chat_id,),
            )
            cur.execute("DELETE FROM dialog_blocks WHERE dialog_id = ?", (applicant_chat_id,))

            if technical_task_status in self.RETAKE_RESET_TECHNICAL_TASK_STATUSES:
                cur.execute(
                    """
                    UPDATE dialog_state
                    SET application_retake_count = 0,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE dialog_id = ?
                    """,
                    (applicant_chat_id,),
                )
                cur.execute(
                    """
                    UPDATE application_reviews
                    SET status = 'superseded',
                        resolved_at = COALESCE(resolved_at, CURRENT_TIMESTAMP),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE applicant_chat_id = ?
                      AND status != 'superseded'
                    """,
                    (applicant_chat_id,),
                )

            cur.execute(
                "SELECT application_retake_count FROM dialog_state WHERE dialog_id = ? LIMIT 1",
                (applicant_chat_id,),
            )
            state_row = cur.fetchone()
            retake_count = int(state_row[0] or 0) if state_row is not None else 0

            cur.execute(
                """
                SELECT COUNT(*)
                FROM application_reviews
                WHERE applicant_chat_id = ?
                  AND status != 'superseded'
                """,
                (applicant_chat_id,),
            )
            existing_count = int(cur.fetchone()[0] or 0)

            cur.execute(
                """
                SELECT COUNT(*)
                FROM application_reviews
                WHERE applicant_chat_id = ?
                  AND status = 'pending'
                """,
                (applicant_chat_id,),
            )
            pending_count = int(cur.fetchone()[0] or 0)
            if existing_count > 0:
                if retake_count >= 1:
                    raise ApplicationRetakeLimitReachedError()
                cur.execute(
                    """
                    UPDATE dialog_state
                    SET application_retake_count = application_retake_count + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE dialog_id = ?
                    """,
                    (applicant_chat_id,),
                )
                if pending_count > 0:
                    cur.execute(
                        """
                        UPDATE application_reviews
                        SET status = 'superseded',
                            resolved_at = CURRENT_TIMESTAMP,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE applicant_chat_id = ?
                          AND status = 'pending'
                        """,
                        (applicant_chat_id,),
                    )

            cur.execute(
                """
                INSERT INTO application_reviews(
                    token,
                    manager_user_id,
                    applicant_user_id,
                    applicant_chat_id,
                    applicant_username,
                    application_text,
                    video_format,
                    video_format_code,
                    business_connection_id,
                    status,
                    updated_at
                ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP)
                """,
                (
                    token,
                    manager_user_id,
                    applicant_user_id,
                    applicant_chat_id,
                    applicant_username,
                    application_text,
                    video_format,
                    video_format_code,
                    business_connection_id,
                ),
            )

        await self.db.in_transaction(work)

    async def resolve_application_review(self, token: str, approved: bool) -> ApplicationReviewResolutionDTO | None:
        next_status = "approved" if approved else "rejected"

        def work(cur: sqlite3.Cursor) -> ApplicationReviewResolutionDTO | None:
            cur.execute(
                """
                SELECT applicant_chat_id, applicant_user_id, business_connection_id, video_format, video_format_code, status
                FROM application_reviews
                WHERE token = ?
                """,
                (token,),
            )
            row = cur.fetchone()
            if row is None:
                return None

            applicant_chat_id, applicant_user_id, business_connection_id, video_format, video_format_code, status = row
            current_status = str(status)
            if current_status != "pending":
                return ApplicationReviewResolutionDTO(
                    applicant_chat_id=int(applicant_chat_id),
                    applicant_user_id=int(applicant_user_id),
                    business_connection_id=str(business_connection_id) if business_connection_id else None,
                    video_format=str(video_format) if video_format else None,
                    video_format_code=str(video_format_code) if video_format_code else None,
                    status=current_status,
                    was_updated=False,
                )

            cur.execute(
                """
                UPDATE application_reviews
                SET status = ?, resolved_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE token = ?
                """,
                (next_status, token),
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
            return ApplicationReviewResolutionDTO(
                applicant_chat_id=int(applicant_chat_id),
                applicant_user_id=int(applicant_user_id),
                business_connection_id=str(business_connection_id) if business_connection_id else None,
                video_format=str(video_format) if video_format else None,
                video_format_code=str(video_format_code) if video_format_code else None,
                status=next_status,
                was_updated=True,
            )

        return await self.db.in_transaction(work)
