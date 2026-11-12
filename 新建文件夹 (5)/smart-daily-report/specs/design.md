# design.md — 智能日报生成器系统设计

- 版本：v1.0
- 状态：评审中
- 关联规范：proposal.md、tasks.md
- UML 附件：specs/uml/（usecase.puml、dataflow.puml、class.puml、er.puml）

## 1. 系统架构（分层图 + 文字说明）

```
┌─────────────────────────────────────────────────────────────┐
│                        主编排入口 main.py                     │
│        （采集 → 生成 → 推送 → 落库 的主流程与 CLI）             │
└──────────┬──────────────────────────────┬───────────────────┘
           │ 调用 collect()                │ 调用 push()
┌──────────▼──────────┐   ┌───────────────▼───────────────────┐
│        采集层         │   │             生成层                 │
│  GitHubCollector      │   │  report.generate(activities)     │
│  FeishuTaskCollector  ├──►│  · 按成员聚合                     │
│  FeishuMessageCollector│  │  · 协作成果自动归属               │
└──────────────────────┘   │  · 渲染 Markdown 日报             │
                           └───────────────┬───────────────────┘
                                           │ 推送内容
                          ┌────────────────▼──────────────────┐
                          │              推送层                │
                          │  EmailPusher(SMTP)                 │
                          │  FeishuBotPusher(Webhook)          │
                          └────────────────┬──────────────────┘
                                           │ save_report()
                          ┌────────────────▼──────────────────┐
                          │         数据层 db.py (SQLite)       │
                          │  reports(id,date,content,channels) │
                          └───────────────────────────────────┘
```

分层说明：

- **采集层**：把异构数据源（GitHub、飞书任务、飞书消息）统一适配为 `Activity` 列表，屏蔽不同平台的字段差异。
- **生成层**：纯函数式模块，无 I/O。输入 `Activity` 列表与成员名单，输出 `DailyReport` 对象与 Markdown 文本；协作成果归属规则在此实现。
- **推送层**：把日报文本推送到不同通道。每个 Pusher 独立成败，互不影响。
- **主编排入口**：CLI，负责参数解析、配置装配、按序调用各层、异常隔离与落库。
- **数据层**：SQLite 保存日报历史，与业务逻辑解耦，仅提供 `save_report` / `list_history` 两个能力。

## 2. 模块职责（每个模块一句话职责边界）

| 模块 | 职责边界 |
|------|----------|
| `main.py` | 主编排：解析 CLI 参数、装配 Config、串联采集→生成→推送→落库，捕获并隔离单源异常 |
| `config.py` | 从环境变量读取配置并构造 `Config`，负责凭证注入（不落盘、不打印值） |
| `models.py` | 领域模型：`Activity`、`Member`、`DailyReport`、`ReportEntry` 及枚举 |
| `db.py` | SQLite 初始化与日报历史读写，仅此模块持有 SQL |
| `collectors/base.py` | 定义 `Collector` 抽象基类与 `collect` 接口契约 |
| `collectors/github.py` | GitHub commit 采集，凭证缺失时降级 mock |
| `collectors/feishu.py` | 飞书任务/消息采集，本期以 mock 实现并留出真实接口位置 |
| `generator/report.py` | 聚合活动为条目、协作成果自动归属、渲染日报文本 |
| `pushers/base.py` | 定义 `Pusher` 抽象基类与 `push` 接口契约 |
| `pushers/email.py` | SMTP 邮件推送，未配置时 dry-run |
| `pushers/feishu_bot.py` | 飞书机器人 Webhook 推送，未配置时 dry-run |

## 3. 数据模型（实体、字段、约束）

### 3.1 领域模型（内存对象）

```
Activity
  - source: str          # "github" | "feishu_task" | "feishu_message"
  - member: str          # 成员标识（GitHub username / 飞书 user_id，统一映射到成员）
  - happened_at: datetime
  - summary: str         # 一句话描述
  - kind: str            # "commit" | "task" | "message"

Member
  - name: str            # 姓名（占位：成员1..成员5）
  - github: str          # GitHub 用户名
  - feishu: str          # 飞书 user_id

DailyReport
  - date: str            # "YYYY-MM-DD"
  - entries: list[ReportEntry]

ReportEntry
  - member: str          # 成员名
  - items: list[str]     # 该成员当日聚合出的事项描述
```

### 3.2 SQLite 表结构（对应 ER 图）

```sql
CREATE TABLE IF NOT EXISTS reports (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date        TEXT    NOT NULL,             -- 'YYYY-MM-DD'，唯一
    content     TEXT    NOT NULL,             -- 日报 Markdown 全文
    channels    TEXT    NOT NULL,             -- 逗号分隔：email,feishu
    created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    UNIQUE(date)
);
```

约束：`date` 唯一，同一日期重复生成走 upsert 覆盖，保证"同日期仅保留最新一份"（proposal S10）。

## 4. 接口契约（每个接口：签名、入参、出参、行为约束）

### 4.1 Collector

```python
class Collector(ABC):
    source: str
    def collect(self, since: datetime, until: datetime) -> list[Activity]: ...
```

- 入参：`since`/`until` 为左闭右开时间窗口 `[since, until)`。
- 出参：该数据源在窗口内的全部活动，无结果返回空列表 `[]`。
- 行为约束：① 任何异常必须被采集器内部捕获并记日志，返回 `[]`，不得向调用方抛出（对应 proposal S9）；② 返回的 `Activity.source` 必须与采集器 `source` 一致；③ 禁止在采集器内访问数据库或发送推送。

### 4.2 Generator

```python
def generate(activities: list[Activity], members: list[Member], date: str) -> DailyReport
def render(report: DailyReport) -> str
```

- 入参：全部采集活动、成员名单、日期。
- 出参：`DailyReport` 与 Markdown 文本。
- 行为约束：① 纯函数，不产生 I/O；② 每个成员都必须出现在结果中，无活动成员生成兜底条目（proposal G2）；③ 协作成果归属规则（见 4.4）必须可复现。

### 4.3 Pusher

```python
class Pusher(ABC):
    channel: str
    def push(self, content: str, date: str) -> bool: ...
```

- 入参：日报全文、日期。
- 出参：是否真实发送成功（dry-run 返回 `True` 并标注"未真实发送"）。
- 行为约束：① 单个 Pusher 失败不得影响其他 Pusher；② 失败时返回 `False` 并记日志，由主编排汇总。

### 4.4 协作成果归属规则（生成层核心逻辑）

- 判定协作：同一条 `Activity` 若 `member` 字段携带多个成员（以逗号分隔，如 `"alice,bob"`），则该活动同时计入 alice 与 bob 的条目。
- 来源映射：GitHub 侧通过"一个 commit 含 `Co-authored-by` 或多个作者"识别协作；mock 数据源直接提供多成员活动样例。
- 可复现性：归属结果只取决于活动数据本身，与成员遍历顺序无关（先按成员稳定排序再聚合）。

### 4.5 CLI 契约

```
python -m daily_report.main [--date YYYY-MM-DD] [--mock|--no-mock]
```

- 默认 `--date` 为当天，默认 `--mock`。
- 退出码：0 成功；2 参数错误；1 主编排异常。

## 5. 技术选型 ADR

### ADR-001：HTTP 客户端选用 httpx

- 状态：已接受
- 背景：采集层需并发调用 GitHub 与飞书多个只读接口，且需超时、重试与异常分类。
- 备选项：
  - `requests`（同步、生态大，但同步阻塞、无原生超时重试组合便利）
  - `aiohttp`（异步，但增加事件循环复杂度，CLI 场景收益低）
  - `urllib`（标准库，但 API 繁琐、无重试与超时语义）
- 决策：选 `httpx`，同步模式。
- 理由：同步 API 与 `requests` 兼容、支持连接池与超时、代码更易审查；CLI 单机场景无需引入 asyncio。

### ADR-002：存储选用 SQLite

- 状态：已接受
- 背景：仅需保存日报历史，单机运行、无并发写、数据量小。
- 备选项：
  - JSON 文件（实现简单，但无查询、无约束、并发易损坏）
  - MySQL/PostgreSQL（功能强，但引入独立服务，超出团队运维能力）
- 决策：选 SQLite（标准库 `sqlite3`）。
- 理由：零部署、支持 SQL 查询与唯一约束，与单机 CLI 形态匹配，符合提案 C2。

### ADR-003：数据源可替换（接口抽象 + mock 降级）

- 状态：已接受
- 背景：飞书应用审核、邮箱授权码申请常滞后于开发进度；若采集/推送强依赖真实凭证会阻塞主流程。
- 备选项：
  - 直接写死真实调用（阻塞风险高）
  - 各模块内部 if/else 判断凭证（判断散落、不可测）
- 决策：`Collector`/`Pusher` 定义接口，各适配器在"无凭证"时降级 mock / dry-run；`--mock` 一键强制降级。
- 理由：把"数据源可替换"写进接口契约，主流程不依赖外部服务即可走通（proposal G6），也是第 2 周集成测试的基础。

## 6. 非功能性约束

- NFR-1 采集频率限制：GitHub 采集每次窗口默认当天 00:00–24:00，单成员 commit 上限 100 条，避免打满配额。
- NFR-2 密钥管理：凭证仅从环境变量读取，`Config` 的 `__repr__` 与日志一律脱敏（不打印值）。
- NFR-3 异常重试：GitHub 只读接口超时 10s、重试 2 次（指数退避），3 次失败按空结果处理并记日志。
- NFR-4 性能：mock 全流程 ≤ 30s（proposal S5）。
- NFR-5 可维护性：分层单向依赖（采集/推送不反向依赖生成层与主编排），模块间仅通过 `Activity`/`DailyReport` 传递数据。
- NFR-6 可移植性：仅依赖标准库 + httpx，Python 3.12+，Windows/Linux 均可运行。
