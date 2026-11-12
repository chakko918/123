from datetime import datetime

from daily_report.collectors import (
    FeishuMessageCollector,
    FeishuTaskCollector,
    GitHubCollector,
)
from daily_report.models import Activity, ActivityKind


def _window():
    since = datetime(2026, 11, 11, 0, 0, 0)
    until = datetime(2026, 11, 12, 0, 0, 0)
    return since, until


def test_github_mock_returns_commits():
    since, until = _window()
    acts = GitHubCollector(mock=True).collect(since, until)
    assert len(acts) >= 1
    assert all(a.kind == ActivityKind.COMMIT for a in acts)


def test_github_no_token_degrades_to_mock():
    since, until = _window()
    acts = GitHubCollector(token="", repo="", mock=False).collect(since, until)
    assert len(acts) >= 1  # 无凭证自动降级，不抛异常


def test_feishu_collectors_source_correct():
    since, until = _window()
    tasks = FeishuTaskCollector(mock=True).collect(since, until)
    msgs = FeishuMessageCollector(mock=True).collect(since, until)
    assert all(a.source == "feishu_task" for a in tasks)
    assert all(a.source == "feishu_message" for a in msgs)


def test_collector_exception_isolated():
    class Broken(GitHubCollector):
        def _collect(self, since, until):
            raise RuntimeError("boom")

    since, until = _window()
    # 不抛异常，返回空列表
    assert Broken(mock=True).collect(since, until) == []
