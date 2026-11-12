"""飞书自定义机器人推送器。未配置 webhook 或 mock 模式下降级 dry-run。"""
from __future__ import annotations

import logging

from .base import Pusher

logger = logging.getLogger(__name__)


class FeishuBotPusher(Pusher):
    channel = "feishu"

    def __init__(self, webhook: str = "", mock: bool = True) -> None:
        self.webhook = webhook
        self.mock = mock

    def _push(self, content: str, date: str) -> bool:
        if self.mock or not self.webhook:
            logger.info("[feishu][dry-run] 未真实发送。日期=%s 正文=%d 字", date, len(content))
            return True

        import httpx  # 延迟导入：dry-run 无需该依赖

        payload = {"msg_type": "text", "content": {"text": f"团队日报 {date}\n{content}"}}
        resp = httpx.post(self.webhook, json=payload, timeout=10.0)
        resp.raise_for_status()
        logger.info("[feishu] 已推送")
        return True
