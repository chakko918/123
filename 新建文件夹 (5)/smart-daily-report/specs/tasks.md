# tasks.md — 智能日报生成器任务拆解

- 版本：v1.0
- 关联规范：proposal.md、design.md
- 执行方式：SDD 代码生成（阶段一），逐任务生成 → 逐条审查 diff → 提交

## 1. 元信息

- 覆盖范围：proposal 4.1 的 F1–F8 全部功能。
- 验收口径：每个任务 = 一个可验证交付物；验收标准可执行（可用命令/断言验证）。
- 依赖图见 §3。

## 2. 任务清单

| 编号 | 标题 | 交付物 | 验收标准（可执行验证） | 依赖 | 预估 |
|------|------|--------|------------------------|------|------|
| T1 | 项目结构与配置加载 | `src/daily_report/{__init__,config}.py`、`requirements.txt` | `python -c "from daily_report.config import Config; c=Config.from_env(); assert isinstance(c.mock,bool)"` 通过 | — | 0.5h |
| T2 | 领域模型 | `src/daily_report/models.py` | `Activity`/`Member`/`DailyReport`/`ReportEntry` 可实例化，`Activity.kind` 枚举校验通过 | T1 | 0.5h |
| T3 | SQLite 存储 | `src/daily_report/db.py` | `init_db` 建表后 `save_report` 再 `list_history` 能查到记录；同日期 upsert 不产生重复行 | T1 | 1h |
| T4 | GitHub 采集器 | `src/daily_report/collectors/github.py` | mock 下返回 ≥1 条 commit；无 token 时降级 mock 且不抛异常 | T1,T2 | 2h |
| T5 | 飞书任务/消息采集器 | `src/daily_report/collectors/feishu.py` | mock 下任务、消息采集器各返回 ≥1 条，`source` 字段正确 | T1,T2 | 1.5h |
| T6 | 日报生成与协作归属 | `src/daily_report/generator/report.py` | 给定含多成员 commit 的活动，两位成员条目都含该提交；无活动成员生成兜底条目 | T2 | 2h |
| T7 | 邮件推送器 | `src/daily_report/pushers/email.py` | 未配置 SMTP 时 dry-run 输出内容并返回 True；不抛异常 | T1 | 1h |
| T8 | 飞书机器人推送器 | `src/daily_report/pushers/feishu_bot.py` | 未配置 webhook 时 dry-run 输出内容并返回 True | T1 | 0.5h |
| T9 | 主编排入口 | `src/daily_report/main.py` | `python -m daily_report.main --mock --date 2026-11-11` 端到端跑通并落库，退出码 0 | T3–T8 | 2h |
| T10 | 集成测试 | `tests/` 全部用例 | `pytest` 全绿；覆盖 proposal 成功标准 S1–S4、S7–S10 | T9 | 3h |

## 3. 依赖图与并行组

```
T1 ──┬── T2 ──┬── T4 ──┐
     │        │── T5 ──┤
     │        │── T6 ──┼── T9 ── T10
     ├── T3 ──┤        │
     ├── T7 ──┤        │
     └── T8 ──┴────────┘
```

- **并行组 A**（无共享文件）：T4 与 T5（两个采集模块，独立文件，可并行）。
- **并行组 B**：T3、T7、T8（存储、邮件、飞书推送互不共享文件，可并行）。
- **串行约束**：T6 依赖 T2；T9 依赖所有 T3–T8；T10 依赖 T9。T9（主编排）与 T10（测试）因共享主流程，必须串行。

## 4. 执行顺序（含依赖图）

1. T1 → 2. T2 → 3. 并行组 A（T4、T5）+ 并行组 B（T3、T7、T8）→ 4. T6 → 5. T9 → 6. T10
