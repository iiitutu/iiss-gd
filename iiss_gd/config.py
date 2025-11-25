"""配置与环境变量解析。"""

import os
from typing import List, Optional

from dotenv import load_dotenv
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
    incremental_state_file: Optional[str] = None


def _parse_env_list(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def load_settings() -> Settings:
    """加载.env与环境变量，生成配置对象。"""
    load_dotenv()
    return Settings(
        feishu_webhook=os.getenv("FEISHU_WEBHOOK"),
        youtube_channels=_parse_env_list(os.getenv("YOUTUBE_CHANNEL_IDS")),
        reddit_subreddits=_parse_env_list(os.getenv("REDDIT_SUBREDDITS")),
        reddit_client_id=os.getenv("REDDIT_CLIENT_ID"),
        reddit_client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        reddit_user_agent=os.getenv("REDDIT_USER_AGENT", "iiss-gd-bot/0.1"),
        max_items=int(os.getenv("MAX_ITEMS", "5")),
        incremental_state_file=os.getenv("INCREMENTAL_STATE_FILE"),
    )
