from datetime import datetime

from daily_report.generator import generate, render
from daily_report.models import Activity, ActivityKind, Member


MEMBERS = [
    Member(name="成员1", github="member1"),
    Member(name="成员2", github="member2"),
    Member(name="成员3", github="member3"),
    Member(name="成员4", github="member4"),
    Member(name="成员5", github="member5"),
]


def test_collaboration_attributed_to_both():
    t = datetime(2026, 11, 11, 9, 0, 0)
    acts = [
        Activity("github", "member1,member2", t, "提交 x: 联调接口", ActivityKind.COMMIT),
    ]
    report = generate(acts, MEMBERS, "2026-11-11")
    e1 = next(e for e in report.entries if e.member == "成员1")
    e2 = next(e for e in report.entries if e.member == "成员2")
    assert "提交 x: 联调接口" in e1.items
    assert "提交 x: 联调接口" in e2.items


def test_member_without_activity_gets_fallback():
    report = generate([], MEMBERS, "2026-11-11")
    e = next(e for e in report.entries if e.member == "成员5")
    assert len(e.items) == 1
    assert "今日无提交/无任务" in e.items[0]


def test_all_members_present():
    report = generate([], MEMBERS, "2026-11-11")
    assert [e.member for e in report.entries] == ["成员1", "成员2", "成员3", "成员4", "成员5"]


def test_render_contains_header_and_summary():
    report = generate([], MEMBERS, "2026-11-11")
    text = render(report)
    assert text.startswith("# 团队日报 2026-11-11")
    assert "## 汇总" in text
