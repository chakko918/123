"""主编排入口：解析参数 → 装配配置 → 采集 → 生成 → 推送 → 落库。"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timedelta

from . import db
from .config import DEFAULT_MEMBERS, Config
from .collectors import FeishuMessageCollector, FeishuTaskCollector, GitHubCollector
from .generator import generate, render
from .pushers import EmailPusher, FeishuBotPusher


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="daily-report", description="智能日报生成器")
    parser.add_argument("--date", default=None, help="日报日期 YYYY-MM-DD，默认当天")
    parser.add_argument(
        "--mock", dest="mock", action="store_true", default=None,
        help="强制使用 mock 数据源与 dry-run 推送（默认）",
    )
    parser.add_argument(
        "--no-mock", dest="mock", action="store_false",
        help="使用真实凭证（需配置环境变量）",
    )
    parser.add_argument("--db", default=None, help="SQLite 文件路径")
    parser.add_argument(
        "--check", action="store_true",
        help="凭证就绪检查：列出各凭证配置状态并对 GitHub 做只读冒烟测试",
    )
    return parser


def check_credentials(cfg: Config) -> int:
    """检查各凭证是否就绪，并对 GitHub 只读接口做一次真实调用。"""
    print("== 凭证就绪检查 ==")
    items = [
        ("GITHUB_TOKEN", cfg.github_token),
        ("GITHUB_REPO", cfg.github_repo),
        ("GITHUB_USERNAMES", ",".join(cfg.github_usernames)),
        ("SMTP_HOST", cfg.smtp_host),
        ("SMTP_USER", cfg.smtp_user),
        ("SMTP_PASSWORD", cfg.smtp_password),
        ("SMTP_TO", ",".join(cfg.smtp_to)),
        ("FEISHU_WEBHOOK", cfg.feishu_webhook),
        ("FEISHU_APP_ID", cfg.feishu_app_id),
        ("SDR_MEMBERS", ",".join(m.name for m in cfg.members)),
    ]
    for name, value in items:
        print(f"[{'OK' if value else 'MISSING'}] {name}")

    if not (cfg.github_token and cfg.github_repo):
        print("GitHub 冒烟测试：跳过（缺少 GITHUB_TOKEN 或 GITHUB_REPO）")
        return 0
    try:
        import httpx

        resp = httpx.get(
            f"https://api.github.com/repos/{cfg.github_repo}",
            headers={"Authorization": f"Bearer {cfg.github_token}"},
            timeout=10.0,
        )
        print(f"GitHub 只读冒烟测试：HTTP {resp.status_code} {resp.reason_phrase}")
    except Exception as exc:  # noqa: BLE001
        print(f"GitHub 只读冒烟测试失败：{exc}")
    return 0


def run(argv: list[str] | None = None) -> int:
    args = build_argparser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

    cfg = Config.from_env()
    if args.mock is not None:
        cfg.mock = args.mock
    if args.check:
        return check_credentials(cfg)
    members = cfg.members or DEFAULT_MEMBERS

    if args.date:
        day = datetime.strptime(args.date, "%Y-%m-%d")
    else:
        now = datetime.now()
        day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    date_str = day.strftime("%Y-%m-%d")
    since = day
    until = day + timedelta(days=1)

    db.init_db(args.db)

    collectors = [
        GitHubCollector(token=cfg.github_token, repo=cfg.github_repo,
                        usernames=cfg.github_usernames, mock=cfg.mock),
        FeishuTaskCollector(app_id=cfg.feishu_app_id, app_secret=cfg.feishu_app_secret, mock=cfg.mock),
        FeishuMessageCollector(app_id=cfg.feishu_app_id, app_secret=cfg.feishu_app_secret, mock=cfg.mock),
    ]
    activities = []
    for collector in collectors:
        acts = collector.collect(since, until)
        logging.info("采集器 %s 返回 %d 条", collector.source, len(acts))
        activities.extend(acts)

    report = generate(activities, members, date_str)
    content = render(report)
    print(content)
    print()

    pushers = [
        EmailPusher(host=cfg.smtp_host, port=cfg.smtp_port, user=cfg.smtp_user,
                    password=cfg.smtp_password, to=cfg.smtp_to, mock=cfg.mock),
        FeishuBotPusher(webhook=cfg.feishu_webhook, mock=cfg.mock),
    ]
    channels: list[str] = []
    for pusher in pushers:
        ok = pusher.push(content, date_str)
        logging.info("推送器 %s -> %s", pusher.channel, "成功" if ok else "失败")
        if ok:
            channels.append(pusher.channel)

    db.save_report(date_str, content, channels, db_path=args.db)
    logging.info("日报已落库: date=%s channels=%s", date_str, ",".join(channels) or "无")
    return 0


if __name__ == "__main__":
    sys.exit(run())
