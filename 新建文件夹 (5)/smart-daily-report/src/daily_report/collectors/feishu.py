"""飞书任务 / 飞书群消息采集器。

本期以 mock 实现并预留真实接口位置（app_id/app_secret 经环境变量注入）。
真实实现需调用飞书开放平台：任务 task/v1、消息 im/v1，凭证缺失时保持降级。
"""
from __future__ import annotations

from datetime import datetime

from ..models import Activity, ActivityKind
from .base import Collector


class FeishuTaskCollector(Collector):
    source = "feishu_task"

    def __init__(self, app_id: str = "", app_secret: str = "", mock: bool = True) -> None:
        self.app_id = app_id
        self.app_secret = app_secret
        self.mock = mock

    def _collect(self, since: datetime, until: datetime) -> list[Activity]:
        if not self.mock and self.app_id and self.app_secret:
            return self._fetch_tasks(since, until)
        return [
            Activity(
                source=self.source, member="member3", happened_at=since,
                summary="完成任务: 撰写 tasks.md 任务拆解与依赖图", kind=ActivityKind.TASK,
            ),
            Activity(
                source=self.source, member="member4", happened_at=since,
                summary="完成任务: 编写集成测试用例与验收核对表", kind=ActivityKind.TASK,
            ),
        ]

    def _fetch_tasks(self, since: datetime, until: datetime) -> list[Activity]:
        # TODO(v1.1): 接入飞书任务 open api，返回统一 Activity
        return []


class FeishuMessageCollector(Collector):
    source = "feishu_message"

    def __init__(self, app_id: str = "", app_secret: str = "", mock: bool = True) -> None:
        self.app_id = app_id
        self.app_secret = app_secret
        self.mock = mock

    def _collect(self, since: datetime, until: datetime) -> list[Activity]:
        if not self.mock and self.app_id and self.app_secret:
            return self._fetch_messages(since, until)
        return [
            Activity(
                source=self.source, member="member5", happened_at=since,
                summary="群消息: 确认日报统一推送时间为每日 18:00", kind=ActivityKind.MESSAGE,
            ),
        ]

    def _fetch_messages(self, since: datetime, until: datetime) -> list[Activity]:
        # TODO(v1.1): 接入飞书消息 im/v1，返回统一 Activity
        return []
