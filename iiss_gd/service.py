"""主流程服务：聚合各数据源后返回列表。"""

import logging
from typing import List

from .config import Settings
from .fetchers.reddit import build_client as build_reddit_client
from .fetchers.reddit import fetch_reddit
from .fetchers.youtube import fetch_youtube
from .models import FeedItem

logger = logging.getLogger(__name__)


def collect_items(settings: Settings) -> List[FeedItem]:
    items: List[FeedItem] = []

    for channel in settings.youtube_channels:
        items.extend(fetch_youtube(channel, settings.max_items))

    # reddit_client = build_reddit_client(settings)
    # if reddit_client:
    #     for subreddit in settings.reddit_subreddits:
    #         items.extend(fetch_reddit(subreddit, reddit_client, settings.max_items))

    items.sort(key=lambda item: item.published_at, reverse=True)
    logger.info("聚合完成，合计%d条", len(items))
    return items
