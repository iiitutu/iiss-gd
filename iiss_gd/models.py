"""通用数据模型。"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class FeedItem:
    """
    用于飞书卡片的信息类
    """
    title: str
    url: str
    source: str
    published_at: datetime
    thumbnail: str = ""
    summary: str = ""
