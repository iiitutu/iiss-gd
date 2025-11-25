import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

import feedparser
import httpx
import praw
from pydantic import BaseModel, Field


class Settings(BaseModel):
    """运行时配置，来源于环境变量。"""

    feishu_webhook: Optional[str] = None
    youtube_channels: List[str] = Field(default_factory=list)
    reddit_subreddits: List[str] = Field(default_factory=list)
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    reddit_user_agent: str = "iiss-gd-bot/0.1"
    max_items: int = 5


@dataclass
class FeedItem:
    title: str
    url: str
    source: str
    published_at: datetime
    summary: str = ""


logger = logging.getLogger("iiss_gd")


def init_logger() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


def parse_env_list(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def load_settings() -> Settings:
    return Settings(
        feishu_webhook=os.getenv("FEISHU_WEBHOOK"),
        youtube_channels=parse_env_list(os.getenv("YOUTUBE_CHANNEL_IDS")),
        reddit_subreddits=parse_env_list(os.getenv("REDDIT_SUBREDDITS")),
        reddit_client_id=os.getenv("REDDIT_CLIENT_ID"),
        reddit_client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        reddit_user_agent=os.getenv("REDDIT_USER_AGENT", "iiss-gd-bot/0.1"),
        max_items=int(os.getenv("MAX_ITEMS", "5")),
    )


def to_datetime(parsed_time) -> datetime:
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


def fetch_youtube(channel_id: str, limit: int) -> List[FeedItem]:
    # 使用官方RSS避免额外依赖，频道ID可在YouTube后台或链接中获取
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    feed = feedparser.parse(url)
    items: List[FeedItem] = []
    for entry in feed.entries[:limit]:
        published_at = to_datetime(getattr(entry, "published_parsed", None))
        items.append(
            FeedItem(
                title=entry.title, # type: ignore
                url=entry.link, # type: ignore
                source=f"YouTube:{channel_id}",
                published_at=published_at,
                summary=getattr(entry, "summary", ""),
            )
        )
    logger.info("YouTube频道%s抓取%d条", channel_id, len(items))
    return items


def build_reddit_client(settings: Settings) -> Optional[praw.Reddit]:
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


def render_card(items: List[FeedItem]) -> dict:
    # 构造简单的飞书交互卡片，突出来源与标题
    elements = []
    for item in items[:10]:
        elements.append(
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**{item.source}** · [{item.title}]({item.url})\n{item.summary or '暂无摘要'}",
                },
            }
        )
    return {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": "IISS-GD 信息流"},
                "template": "turquoise",
            },
            "elements": elements,
        },
    }


def push_feishu(webhook: str, items: List[FeedItem]) -> None:
    payload = render_card(items)
    try:
        resp = httpx.post(webhook, json=payload, timeout=10)
        resp.raise_for_status()
        logger.info("飞书推送完成")
    except Exception as exc:  # noqa: BLE001
        logger.error("飞书推送失败: %s", exc)


def main() -> None:
    init_logger()
    settings = load_settings()
    all_items: List[FeedItem] = []

    for channel in settings.youtube_channels:
        all_items.extend(fetch_youtube(channel, settings.max_items))

    reddit_client = build_reddit_client(settings)
    if reddit_client:
        for subreddit in settings.reddit_subreddits:
            all_items.extend(fetch_reddit(subreddit, reddit_client, settings.max_items))

    if not all_items:
        logger.warning("没有可用的抓取结果，请检查数据源配置")
        return

    all_items.sort(key=lambda item: item.published_at, reverse=True)

    if settings.feishu_webhook:
        push_feishu(settings.feishu_webhook, all_items)
    else:
        logger.warning("未配置FEISHU_WEBHOOK，打印预览代替推送")
        for item in all_items:
            print(f"[{item.source}] {item.title} -> {item.url}")


if __name__ == "__main__":
    main()
