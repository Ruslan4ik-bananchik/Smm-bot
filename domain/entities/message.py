from dataclasses import dataclass
from typing import Sequence

@dataclass
class Message:
    sender_id: int
    text: str
    history: Sequence[str]
    flow: str = "application"
    
