# 凭证申请与配置指南

> 对应 proposal C4：凭证仅经环境变量（或 `.env`）注入，严禁写入代码或提交到仓库。

## 快速上手

1. 复制模板：`cp .env.example .env`
2. 按下面各节填入真实值
3. 自检：`PYTHONPATH=src python -m daily_report.main --check`
4. 走真实接口：`PYTHONPATH=src python -m daily_report.main --no-mock --date 2026-11-11`

## 1. GitHub Token（采集提交）

1. 打开 GitHub → Settings → Developer settings → Personal access tokens → **Tokens (classic)** → Generate new token。
2. **权限只勾选只读**：`repo` 下仅 `public_repo`（公开仓库）或按需 `repo`；以及 `read:user`。其余一律不勾。
3. 生成后复制（只显示一次），填入 `.env` 的 `GITHUB_TOKEN`。
4. `GITHUB_REPO` 填 `owner/repo` 格式；`GITHUB_USERNAMES` 填成员 GitHub 用户名（逗号分隔）。

> 注意：令牌值只在生成时显示一次。泄露立即到 GitHub 撤销重建。

## 2. 飞书开放平台（任务/消息采集，本期预留）

1. 飞书开放平台 → 创建企业自建应用，得到 `app_id` / `app_secret`。
2. 本期任务与消息采集为 mock，凭证先填好备用，v1.1 再接入真实接口。
3. 真实接口接入需申请权限：任务 `task:task` 读、消息 `im:message` 读。

## 3. SMTP 邮件推送

以 QQ 邮箱为例：

1. 登录 QQ 邮箱 → 设置 → 账户 → 开启 SMTP 服务。
2. 生成**授权码**（不是登录密码）。
3. 填入 `.env`：`SMTP_HOST=smtp.qq.com`、`SMTP_PORT=465`、`SMTP_USER=你的邮箱`、`SMTP_PASSWORD=授权码`、`SMTP_TO=收件人`。
4. 其它邮箱对应：163 → `smtp.163.com`；Outlook → `smtp.office365.com`（端口 587，需把 pushers/email.py 的 `SMTP_SSL` 改 `SMTP` + `starttls`）。

## 4. 飞书自定义机器人（推送 webhook）

1. 飞书群 → 群设置 → 群机器人 → 添加自定义机器人。
2. 复制 Webhook 地址填入 `FEISHU_WEBHOOK`。
3. 该地址即推送凭证，勿提交到仓库。

## 5. 成员清单 SDR_MEMBERS

格式：`姓名:github用户名:飞书user_id`，多人逗号分隔。用于把 GitHub/飞书标识映射回成员姓名（日报按姓名输出）。

## 自检结果解读

`--check` 会逐项列出 `[OK]`/`[MISSING]`，并对 GitHub 只读接口做一次真实调用：

- `HTTP 200`：Token 与仓库名正确，可 `--no-mock`。
- `HTTP 401`：Token 无效或过期，重新生成。
- `HTTP 404`：仓库名不对或 Token 无该仓库权限。

> 主流程永远可降级：任何凭证缺失时，对应采集器/推送器自动 mock/dry-run，不阻塞其它通道（proposal S7–S9）。
