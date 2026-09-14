from __future__ import annotations

from dataclasses import dataclass

from application.dtos.application_form import ApplicationFormDTO


@dataclass(frozen=True)
class AnwserDTO:
    text: str
    should_auto_close: bool = False
    application_form: ApplicationFormDTO | None = None
    should_issue_product_key: bool = False
    should_activate_technical_task: bool = False
    should_complete_technical_task: bool = False
    should_decline_technical_task: bool = False
    should_block_as_troll: bool = False
