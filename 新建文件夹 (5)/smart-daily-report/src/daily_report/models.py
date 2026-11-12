"""领域模型：Activity、Member、DailyReport、ReportEntry。"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ActivityKind(str, Enum):
    COMMIT = "commit"
    TASK = "task"
    MESSAGE = "message"


@dataclass
class Activity:
    """一次可归属到成员的工作痕迹。协作成果的 member 以逗号分隔多个标识。"""

    source: str
    member: str
    happened_at: datetime
    summary: str
    kind: ActivityKind

    def members(self) -> list[str]:
        """返回涉及的全部成员标识（协作成果 → 多个）。"""
        return [m.strip() for m in self.member.split(",") if m.strip()]


@dataclass
class Member:
    name: str
    github: str = ""
    feishu: str = ""


@dataclass
class ReportEntry:
    member: str
    items: list[str] = field(default_factory=list)


@dataclass
class DailyReport:
    date: str
    entries: list[ReportEntry] = field(default_factory=list)
