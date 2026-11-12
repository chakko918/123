"""Pusher 抽象基类：定义 push 接口契约，单通道失败返回 False 不抛出。"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class Pusher(ABC):
    channel: str = ""

    @abstractmethod
    def _push(self, content: str, date: str) -> bool:
        """真实推送逻辑，子类实现。"""

    def push(self, content: str, date: str) -> bool:
        try:
            return self._push(content, date)
        except Exception as exc:  # noqa: BLE001 - 单通道失败隔离
            logger.exception("%s 推送失败: %s", self.channel, exc)
            return False
