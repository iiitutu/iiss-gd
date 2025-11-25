"""飞书推送逻辑。"""

import logging
from typing import List

import httpx

from ..models import FeedItem
from ..renderers.feishu import build_card

logger = logging.getLogger(__name__)


def push_feishu(webhook: str, items: List[FeedItem]) -> bool:
    payload = build_card(items)
    try:
        resp = httpx.post(webhook, json=payload, timeout=10)
        if resp.status_code != 200:
            logger.error("飞书推送失败 status=%s body=%s", resp.status_code, resp.text)
            return False
        data = resp.json()
        if data.get("code", 0) != 0:
            logger.error("飞书推送失败 code=%s msg=%s", data.get("code"), data.get("msg"))
            return False
        logger.info("飞书推送完成")
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("飞书推送失败: %s", exc)
        return False
