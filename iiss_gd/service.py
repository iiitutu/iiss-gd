"""主流程服务：聚合各数据源后返回列表。"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from .config import Settings
from .fetchers.reddit import build_client as build_reddit_client
from .fetchers.reddit import fetch_reddit
from .fetchers.youtube import fetch_youtube
from .models import FeedItem

logger = logging.getLogger(__name__)


def _load_incremental_state(path: Path) -> Dict[str, datetime]:
    """读取增量抓取的时间戳状态。"""
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text())
    except Exception as exc:  # noqa: BLE001
        logger.warning("增量状态文件解析失败，忽略: %s", exc)
        return {}
    state: Dict[str, datetime] = {}
    for source, ts in raw.items():
        try:
            state[source] = datetime.fromisoformat(ts)
        except Exception:  # noqa: BLE001
            logger.debug("增量状态中的时间戳非法，跳过 source=%s ts=%s", source, ts)
    return state


def _save_incremental_state(path: Path, state: Dict[str, datetime]) -> None:
    """写回增量抓取状态。"""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {key: value.isoformat() for key, value in state.items()}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    except Exception as exc:  # noqa: BLE001
        logger.warning("增量状态写入失败: %s", exc)


def _filter_new_items(
    items: List[FeedItem], state: Dict[str, datetime]
) -> Tuple[List[FeedItem], Dict[str, datetime]]:
    """根据状态过滤出新增内容，并返回更新后的状态。"""
    if not state:
        latest = {}
    else:
        latest = dict(state)
    filtered: List[FeedItem] = []
    for item in items:
        last_seen = state.get(item.source)
        if last_seen and item.published_at <= last_seen:
            continue
        filtered.append(item)
        prev_latest = latest.get(item.source)
        if not prev_latest or item.published_at > prev_latest:
            latest[item.source] = item.published_at
    return filtered, latest


def collect_items(settings: Settings) -> List[FeedItem]:
    items: List[FeedItem] = []
    state_path: Path | None = None
    incremental_state: Dict[str, datetime] = {}
    if settings.incremental_state_file:
        logger.info('增量更新模式启动')
        state_path = Path(settings.incremental_state_file).expanduser()
        incremental_state = _load_incremental_state(state_path)
    else:
        logger.info('全量更新模式启动')

    for channel in settings.youtube_channels:
        items.extend(fetch_youtube(channel, settings.max_items))

    # reddit_client = build_reddit_client(settings)
    # if reddit_client:
    #     for subreddit in settings.reddit_subreddits:
    #         items.extend(fetch_reddit(subreddit, reddit_client, settings.max_items))

    items.sort(key=lambda item: item.published_at, reverse=True)

    if state_path:
        items, incremental_state = _filter_new_items(items, incremental_state)
        if not items:
            logger.info("无增量内容")
        _save_incremental_state(state_path, incremental_state)

    logger.info("聚合完成，合计%d条", len(items))
    return items
