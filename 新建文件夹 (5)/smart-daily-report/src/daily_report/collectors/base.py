"""Collector 抽象基类：定义 collect 接口契约，统一异常隔离。"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime

from ..models import Activity

logger = logging.getLogger(__name__)


class Collector(ABC):
    source: str = ""

    @abstractmethod
    def _collect(self, since: datetime, until: datetime) -> list[Activity]:
        """真实采集逻辑，子类实现。"""

    def collect(self, since: datetime, until: datetime) -> list[Activity]:
        """接口契约：任何异常 → 空列表 + 日志，不向调用方抛出（proposal S9）。"""
        try:
            return self._collect(since, until)
        except Exception as exc:  # noqa: BLE001 - 数据源故障必须隔离
            logger.exception("%s 采集失败，返回空列表: %s", self.source, exc)
            return []
