"""YouTube RSS 抓取。"""

import logging
from typing import List

import feedparser

from ..models import FeedItem
from ..utils.time_utils import to_datetime

logger = logging.getLogger(__name__)


def fetch_youtube(channel_id: str, limit: int) -> List[FeedItem]:
    # 使用官方RSS避免额外依赖，频道ID可在YouTube后台或链接中获取
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    feed = feedparser.parse(url)    # 见temp_files/youtube_feed_template
    items: List[FeedItem] = []
    for entry in feed.entries[:limit]:
        published_at = to_datetime(getattr(entry, "published_parsed", None))
        thumb = ""
        thumbnails = getattr(entry, "media_thumbnail", None)
        if thumbnails and isinstance(thumbnails, list):
            thumb = thumbnails[0].get("url", "")
        items.append(
            FeedItem(
                title=getattr(entry, "title", ""),
                url=getattr(entry, "link", ""),
                source=f"YouTube:{channel_id}",
                published_at=published_at,
                thumbnail=thumb,
                summary=getattr(entry, "summary", ""),
            )
        )
    logger.info("YouTube频道%s抓取%d条", channel_id, len(items))
    return items
