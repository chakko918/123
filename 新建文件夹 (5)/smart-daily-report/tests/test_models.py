from datetime import datetime

from daily_report.models import Activity, ActivityKind, Member


def test_activity_members_single():
    a = Activity("github", "alice", datetime.now(), "x", ActivityKind.COMMIT)
    assert a.members() == ["alice"]


def test_activity_members_collaboration():
    a = Activity("github", "alice, bob", datetime.now(), "x", ActivityKind.COMMIT)
    assert a.members() == ["alice", "bob"]


def test_member_defaults():
    m = Member(name="成员1")
    assert m.github == "" and m.feishu == ""
