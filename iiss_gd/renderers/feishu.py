"""飞书交互卡片渲染。"""

from typing import List

from ..models import FeedItem


def _format_item_md(item: FeedItem) -> str:
    parts: List[str] = [f"**{item.source}** · [{item.title}]({item.url})"]
    if item.thumbnail:
        parts.append(f"![thumbnail]({item.thumbnail})")
    if item.summary:
        parts.append(item.summary)
    return "\n".join(parts)


def build_card(items: List[FeedItem]) -> dict:
    # 构造简单的飞书交互卡片，突出来源与标题
    elements = []
    for item in items[:10]:
        elements.extend(
            [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": _format_item_md(item),
                    },
                },
                {"tag": "hr"},
            ]
        )

    if elements:
        elements.pop()

    return {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": "Designer 信息流"},
                "template": "turquoise",
            },
            "elements": elements,
        },
    }
