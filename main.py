import logging

from iiss_gd.config import load_settings
from iiss_gd.pushers.feishu import push_feishu
from iiss_gd.service import collect_items

logger = logging.getLogger("iiss_gd")


def init_logger() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


def main() -> None:
    init_logger()
    settings = load_settings()
    items = collect_items(settings)

    if not items:
        logger.warning("没有可用的抓取结果，请检查数据源配置")
        return

    if settings.feishu_webhook:
        push_feishu(settings.feishu_webhook, items)
    else:
        logger.warning("未配置FEISHU_WEBHOOK，打印预览代替推送")
        for item in items:
            print(f"[{item.source}] {item.title} -> {item.url}")


if __name__ == "__main__":
    main()
