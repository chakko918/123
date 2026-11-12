# 智能日报生成器（Smart Daily Report Generator）

《软件工程职业技能实践》课程 · 阶段一（第 1–2 周，SDD 规范驱动）交付物。

四层结构：**采集层 → 生成层 → 推送层 → 主编排入口**，SQLite 存储日报历史。

## 目录结构

```
smart-daily-report/
├── specs/                三份核心规范（规格先行）
│   ├── proposal.md
│   ├── design.md
│   ├── tasks.md
│   └── uml/              用例图/类图/ER图/泳道图（PlantUML 工具绘制）
├── src/daily_report/     v1 源代码
│   ├── main.py           主编排入口（CLI，含 --check / --no-mock）
│   ├── config.py         配置与凭证脱敏（含 .env 加载）
│   ├── models.py         领域模型
│   ├── db.py             SQLite 存储
│   ├── collectors/       github / feishu_task / feishu_message
│   ├── generator/        日报生成与协作归属
│   └── pushers/          email / feishu_bot
├── tests/                集成测试（覆盖 proposal 成功标准，19 用例）
├── reports/              四份分析报告（.md 源 + .docx）
├── docs/                 AI 使用日志模板 + 凭证申请指南
├── scripts/md2docx.py    Markdown → Word 转换脚本
├── .env.example          凭证模板（复制为 .env 使用，.env 已被忽略）
├── .gitignore
├── requirements.txt
└── conftest.py           pytest 根配置
```

## 运行

```bash
# 依赖
pip install -r requirements.txt

# mock 模式（默认，无需任何凭证即可端到端跑通）
PYTHONPATH=src python -m daily_report.main --date 2026-11-11 --mock

# 测试
python -m pytest -q
```

真实模式需配置环境变量（凭证不落盘、不进仓库）：

```bash
export GITHUB_TOKEN=... GITHUB_REPO=owner/repo GITHUB_USERNAMES=a,b,c
export SMTP_HOST=... SMTP_PORT=465 SMTP_USER=... SMTP_PASSWORD=... SMTP_TO=...
export FEISHU_WEBHOOK=...          # 飞书自定义机器人
export SDR_MEMBERS="姓名:github:feishu,..."
python -m daily_report.main --no-mock
```

## 阶段门禁自检

- [x] 三份规范 + UML 附件齐全（proposal / design / tasks）
- [x] 全部功能按 proposal 成功标准可运行（`--mock` 端到端，19 个测试全绿）
- [x] 采集 → 生成 → 推送 全流程可演示，协作成果自动归属可核查

## 团队分工（姓名待填，替换【姓名】即可）

| 角色 | 学号 | 姓名 | 阶段一职责 |
|------|------|------|-----------|
| 需求分析师（组长） | 20233139 | 【姓名】 | proposal.md、业务调研报告、需求分析报告、隐含需求清单 |
| 架构师 | 20233134 | 【姓名】 | design.md（架构/数据模型/接口契约/ADR）、UML、系统分析报告 |
| 开发工程师 | 20233138 | 【姓名】 | 采集/生成/推送模块实现、主编排入口、v1 代码提交 |
| 测试工程师 | 20233142 | 【姓名】 | 验收标准可测性评审、集成测试、成功标准逐条核对 |
| 配置管理员 | 20233137 | 【姓名】 | 仓库与 specs/ 初始化、分支规范、AI 使用日志归档、凭证就绪登记 |

> 指导书要求每组 3–4 人；本组为 5 人，5 个角色一一对应。第 2 周起角色按周轮换，轮换记录写入项目总结报告。
