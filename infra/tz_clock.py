from datetime import datetime
from zoneinfo import ZoneInfo


class TZClock:
    """
    Таймзонный источник времени.
    Можно передавать в логгер, планировщик и любые функции, которым нужен datetime.
    """
    def __init__(self, tz_name: str):
        self.tz = ZoneInfo(tz_name)

    def now(self) -> datetime:
        """Текущее время в таймзоне"""
        return datetime.now(self.tz)
