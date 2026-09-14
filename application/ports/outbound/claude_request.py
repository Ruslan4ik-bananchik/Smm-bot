from abc import ABC, abstractmethod
from domain.entities.message import Message
from application.dtos.anwser import AnwserDTO
from typing import Optional

class ClaudeRequestPort(ABC):
    @abstractmethod
    async def request_anwser(self, message_entity: Message) -> Optional[AnwserDTO]: ...

    @abstractmethod
    async def generate_technical_task_offer(self, video_format_code: str | None, reference_text: str) -> str | None: ...
