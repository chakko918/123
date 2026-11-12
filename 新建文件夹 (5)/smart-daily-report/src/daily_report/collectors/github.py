"""GitHub commit 采集器。凭证缺失或 mock 模式下降级为样例数据。"""
from __future__ import annotations

import logging
from datetime import datetime

from ..models import Activity, ActivityKind
from .base import Collector

logger = logging.getLogger(__name__)


def _parse_dt(value: str) -> datetime:
    if not value:
        return datetime.now()
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except (ValueError, AttributeError):
        return datetime.now()


class GitHubCollector(Collector):
    source = "github"

    def __init__(
        self,
        token: str = "",
        repo: str = "",
        usernames: list[str] | None = None,
        mock: bool = True,
    ) -> None:
        self.token = token
        self.repo = repo
        self.usernames = usernames or []
        self.mock = mock

    def _collect(self, since: datetime, until: datetime) -> list[Activity]:
        if self.mock or not self.token or not self.repo:
            return self._mock_data(since)
        return self._fetch_commits(since, until)

    def _fetch_commits(self, since: datetime, until: datetime) -> list[Activity]:
        import httpx  # 延迟导入：mock 模式无需该依赖

        activities: list[Activity] = []
        headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json"}
        base_params = {
            "since": since.isoformat() + "Z",
            "until": until.isoformat() + "Z",
            "per_page": 100,
        }
        with httpx.Client(timeout=10.0) as client:
            for user in self.usernames:
                url = f"https://api.github.com/repos/{self.repo}/commits"
                try:
                    resp = client.get(url, headers=headers, params={**base_params, "author": user})
                    resp.raise_for_status()
                    for c in resp.json():
                        activities.append(self._to_activity(c))
                except Exception as exc:  # noqa: BLE001 - 单用户失败不中断
                    logger.warning("github 拉取 %s 失败: %s", user, exc)
        return activities

    def _to_activity(self, commit: dict) -> Activity:
        sha = commit.get("sha", "")[:7]
        author = commit.get("author") or {}
        login = author.get("login") or "unknown"
        inner = commit.get("commit", {})
        msg = (inner.get("message") or "").splitlines()[0]
        happened = (inner.get("author") or {}).get("date") or ""
        return Activity(
            source=self.source,
            member=login,
            happened_at=_parse_dt(happened),
            summary=f"提交 {sha}: {msg}",
            kind=ActivityKind.COMMIT,
        )

    def _mock_data(self, since: datetime) -> list[Activity]:
        defaults = ["member1", "member2", "member3", "member4", "member5"]
        usernames = list(self.usernames)
        for name in defaults:  # 补齐到至少 3 个，避免越界
            if len(usernames) >= 3:
                break
            if name not in usernames:
                usernames.append(name)
        u0, u1, u2 = usernames[0], usernames[1], usernames[2]
        return [
            Activity(
                source=self.source, member=u0, happened_at=since,
                summary="提交 abc1234: 初始化 specs/ 目录与分支规范", kind=ActivityKind.COMMIT,
            ),
            Activity(
                source=self.source, member=u1, happened_at=since,
                summary="提交 def5678: 实现 GitHub 采集器", kind=ActivityKind.COMMIT,
            ),
            Activity(
                source=self.source, member=f"{u0},{u2}", happened_at=since,
                summary=f"提交 8899aab: 联调生成层接口（协作：{u0}、{u2}）", kind=ActivityKind.COMMIT,
            ),
        ]
