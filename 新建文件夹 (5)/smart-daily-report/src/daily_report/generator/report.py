"""日报生成：按成员聚合、协作成果自动归属、渲染 Markdown 文本。纯函数，无 I/O。"""
from __future__ import annotations

from collections import defaultdict

from ..models import Activity, DailyReport, Member, ReportEntry


def _build_id_maps(members: list[Member]) -> dict[str, str]:
    """建立 标识(github/feishu/姓名) → 姓名 的映射。"""
    id_to_name: dict[str, str] = {}
    for m in members:
        if m.github:
            id_to_name[m.github] = m.name
        if m.feishu:
            id_to_name[m.feishu] = m.name
        id_to_name[m.name] = m.name
    return id_to_name


def generate(
    activities: list[Activity],
    members: list[Member],
    date: str,
) -> DailyReport:
    id_to_name = _build_id_maps(members)
    grouped: dict[str, set[str]] = defaultdict(set)

    for activity in activities:
        for ident in activity.members():
            name = id_to_name.get(ident, ident)
            grouped[name].add(activity.summary)

    ordered = [m.name for m in members]
    entries: list[ReportEntry] = []
    for name in ordered:
        items = sorted(grouped.get(name, []))
        if not items:
            items = [f"今日无提交/无任务（{name}）"]
        entries.append(ReportEntry(member=name, items=items))

    # 活动里出现、但不在成员名单中的标识，附在末尾，保证不丢失
    known = set(ordered)
    for name in sorted(grouped):
        if name not in known:
            entries.append(ReportEntry(member=name, items=sorted(grouped[name])))

    return DailyReport(date=date, entries=entries)


def render(report: DailyReport) -> str:
    lines = [f"# 团队日报 {report.date}", ""]
    total = 0
    for entry in report.entries:
        lines.append(f"## {entry.member}")
        for item in entry.items:
            lines.append(f"- {item}")
            total += 1
        lines.append("")
    lines.append("## 汇总")
    lines.append(f"- 全组当日事项 {total} 条，涉及成员 {len(report.entries)} 人")
    return "\n".join(lines)
