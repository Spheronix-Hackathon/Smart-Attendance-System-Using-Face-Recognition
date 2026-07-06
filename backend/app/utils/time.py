from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


IST = ZoneInfo("Asia/Kolkata")


def now_ist() -> datetime:
    return datetime.now(IST)


def iso_ist() -> str:
    return now_ist().isoformat()


def date_key(dt: datetime | None = None) -> str:
    return (dt or now_ist()).date().isoformat()


def time_key(dt: datetime | None = None) -> str:
    return (dt or now_ist()).strftime("%H:%M:%S")
