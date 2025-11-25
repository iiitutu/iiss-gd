"""通用数据模型。"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class FeedItem:
    title: str
    url: str
    source: str
    published_at: datetime
    thumbnail: str = ""
    summary: str = ""
