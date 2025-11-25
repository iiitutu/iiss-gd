"""Reddit 抓取模块。"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

import praw

from ..config import Settings
from ..models import FeedItem

logger = logging.getLogger(__name__)


def build_client(settings: Settings) -> Optional[praw.Reddit]:
    if not settings.reddit_client_id or not settings.reddit_client_secret:
        logger.warning("未配置Reddit凭据，跳过Reddit抓取")
        return None
    return praw.Reddit(
        client_id=settings.reddit_client_id,
        client_secret=settings.reddit_client_secret,
        user_agent=settings.reddit_user_agent,
    )


def fetch_reddit(subreddit: str, client: praw.Reddit, limit: int) -> List[FeedItem]:
    # 仅抓取hot列表，后续可按需扩展到keyword/flair过滤
    items: List[FeedItem] = []
    for submission in client.subreddit(subreddit).hot(limit=limit):
        published_at = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc)
        items.append(
            FeedItem(
                title=submission.title,
                url=f"https://www.reddit.com{submission.permalink}",
                source=f"Reddit:{subreddit}",
                published_at=published_at,
                summary=submission.selftext[:240],
            )
        )
    logger.info("Reddit子版块%s抓取%d条", subreddit, len(items))
    return items
