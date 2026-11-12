"""从环境变量加载配置；凭证一律脱敏，绝不打印值。"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from .models import Member


def load_dotenv(path: str | Path | None = None) -> None:
    """读取 .env 并注入环境变量（已存在的变量不覆盖，避免覆盖系统配置）。"""
    candidates: list[Path]
    if path is not None:
        candidates = [Path(path)]
    else:
        candidates = [Path.cwd() / ".env", Path(__file__).resolve().parent.parent.parent / ".env"]
    for p in candidates:
        if not p.exists():
            continue
        for raw in p.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[7:].strip()
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
        break  # 只加载找到的第一个 .env


def _csv(value: str) -> list[str]:
    return [x.strip() for x in value.split(",") if x.strip()] if value else []


@dataclass
class Config:
    github_token: str = ""
    github_repo: str = ""
    github_usernames: list[str] = field(default_factory=list)
    feishu_app_id: str = ""
    feishu_app_secret: str = ""
    smtp_host: str = ""
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_to: list[str] = field(default_factory=list)
    feishu_webhook: str = ""
    mock: bool = True
    members: list[Member] = field(default_factory=list)

    @classmethod
    def from_env(cls) -> "Config":
        load_dotenv()
        return cls(
            github_token=os.getenv("GITHUB_TOKEN", ""),
            github_repo=os.getenv("GITHUB_REPO", ""),
            github_usernames=_csv(os.getenv("GITHUB_USERNAMES", "")),
            feishu_app_id=os.getenv("FEISHU_APP_ID", ""),
            feishu_app_secret=os.getenv("FEISHU_APP_SECRET", ""),
            smtp_host=os.getenv("SMTP_HOST", ""),
            smtp_port=int(os.getenv("SMTP_PORT", "465")),
            smtp_user=os.getenv("SMTP_USER", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            smtp_to=_csv(os.getenv("SMTP_TO", "")),
            feishu_webhook=os.getenv("FEISHU_WEBHOOK", ""),
            mock=os.getenv("SDR_MOCK", "1").lower() not in ("0", "false", "no"),
            members=_members_from_env(),
        )

    def __repr__(self) -> str:
        """脱敏：凭证只显示是否已配置。"""
        return (
            "Config("
            f"github_token={'***' if self.github_token else 'unset'}, "
            f"github_repo={self.github_repo!r}, "
            f"smtp_user={self.smtp_user!r}, "
            f"smtp_password={'***' if self.smtp_password else 'unset'}, "
            f"feishu_webhook={'***' if self.feishu_webhook else 'unset'}, "
            f"mock={self.mock}, members={len(self.members)})"
        )


def _members_from_env() -> list[Member]:
    # SDR_MEMBERS = "姓名:github:feishu,姓名:github:feishu,..."
    members: list[Member] = []
    for item in _csv(os.getenv("SDR_MEMBERS", "")):
        parts = item.split(":")
        name = parts[0].strip() if parts and parts[0] else ""
        if not name:
            continue
        members.append(
            Member(
                name=name,
                github=parts[1].strip() if len(parts) > 1 else "",
                feishu=parts[2].strip() if len(parts) > 2 else "",
            )
        )
    return members


DEFAULT_MEMBERS = [
    Member(name="成员1", github="member1", feishu="member1"),
    Member(name="成员2", github="member2", feishu="member2"),
    Member(name="成员3", github="member3", feishu="member3"),
    Member(name="成员4", github="member4", feishu="member4"),
    Member(name="成员5", github="member5", feishu="member5"),
]
