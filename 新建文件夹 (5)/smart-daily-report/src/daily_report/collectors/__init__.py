"""采集层：把异构数据源统一适配为 Activity 列表。"""
from .base import Collector
from .github import GitHubCollector
from .feishu import FeishuTaskCollector, FeishuMessageCollector

__all__ = [
    "Collector",
    "GitHubCollector",
    "FeishuTaskCollector",
    "FeishuMessageCollector",
]
