"""时间转换工具。"""

from datetime import datetime, timezone
from time import struct_time
from typing import Optional


def to_datetime(parsed_time: Optional[struct_time]) -> datetime:
    """将feedparser返回的时间结构转换为UTC datetime。"""
    if not parsed_time:
        return datetime.now(timezone.utc)
    return datetime(
        parsed_time.tm_year,
        parsed_time.tm_mon,
        parsed_time.tm_mday,
        parsed_time.tm_hour,
        parsed_time.tm_min,
        parsed_time.tm_sec,
        tzinfo=timezone.utc,
    )
