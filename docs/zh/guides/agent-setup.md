---
status: active
owner: 王军
last_verified: 2026-10-06
source_of_truth: src/nblane/core/backup_targets.py、src/nblane/core/openclaw_setup.py、src/nblane/web_api/agents_setup.py、src/nblane/web_ui/frontend/src/components/settings/AgentSetupSections.tsx
---

# 个人 Agent 接入与数据备份（设置 → 助手与备份）

管理员在 SPA「设置 → 系统 → 助手与备份」里完成两件事：把个人 agent（目前适配
OpenClaw）装上并接入 nblane，以及给 nblane 数据和 agent 工作区配置私有远端与每日备份。
命令行等价物见 [OpenClaw 接入指南](openclaw-integration.md)。

## 定位

- nblane 是 agent 背后的**成长档案**：agent 通过 MCP 读写，改变既有事实的操作走
  Agent Activity 审批。agent 可替换，换掉不丢档案。
- **统一备份，不统一仓库**：nblane 数据（`NBLANE_ROOT`）和每个 agent 的工作区各是一个
  私有 git 仓库，由同一个面板和同一个每日定时器负责提交推送。agent 的情景记忆仍归 agent
  自己维护。
- 生产布局：

  ```
  /srv/nblane-data/                    nblane 数据（应用每次写入自动提交）
  /srv/agent-data/openclaw/workspace   OpenClaw 工作区（独立 git，每日快照）
  /srv/backups/agents/                 迁移前的整目录 tar 包（含 sqlite/会话/凭据，权限 600）
  ```

## 个人 Agent

| 场景 | 操作 | 做了什么 |
|------|------|----------|
| 未安装 | 一键安装 OpenClaw | `npm install -g openclaw@<固定版本>`（用户目录，无 sudo）→ `openclaw onboard --non-interactive`（网关只绑 loopback、装 systemd user unit、工作区直接放 `/srv/agent-data/openclaw/workspace`）→ 自动执行「接入」 |
| 已安装 | 接入 nblane | 工作区 `git init` + `.gitignore`；同步仓库技能并生成 `skills/bin/nblane_api`（复用 nblane 自己的 Python，不再建技能 venv）；`openclaw mcp set nblane`；渲染只读语料到 `memory/nblane/` 并加入 `memory.search.extraPaths`。幂等，可重复点 |
| 工作区不在 `/srv/agent-data` | 迁移到统一数据目录 | 先 tar 整个状态目录 → 停网关（微信断开约 10 秒）→ 移动 → 旧路径留软链接 → 改配置 → 起网关；中途失败自动回滚 |
| 需要微信 | 安装微信渠道 | 安装腾讯维护的 `@tencent-weixin/openclaw-weixin`（`--pin`）与 weixin-task-bridge，重启网关。扫码登录在「车间」终端运行页面给出的命令，或在 OpenClaw 控制台扫码 |

模型凭据：

- 新装时默认**复用 nblane 的 AI 连接**（以 OpenAI 兼容自定义 provider `nblane` 写入）。
  Key 通过子进程环境变量 `CUSTOM_API_KEY` 交给 onboarding，不出现在命令行、日志或页面。
- 已有安装**不改模型路由**。其它服务商（如 Kimi Code 订阅）在 OpenClaw 控制台添加——
  nblane 不接管各家 agent 的模型配置格式，这是保持可替换的边界。

其它支持 MCP 的 agent（Claude Code、Cursor、nanobot 等）用卡片底部的 MCP 配置片段接入。

## 数据备份

每个备份目标一行，显示远端、未推送提交数、未提交改动数和上次备份结果。没有远端的目标
按向导添加：

1. **纳入 git**（工作区默认已是 git 仓库时跳过）。
2. **新建私有仓库 + 部署密钥**：在 GitHub 新建 Private 空仓库（不勾 README）；点「生成
   部署密钥」，服务器生成 `~/.ssh/nblane_backup_<目标>_ed25519`（每个仓库一把，GitHub 部署
   密钥不能跨仓库复用），把公钥加到仓库 Settings → Deploy keys 并勾选 Allow write access。
3. **测试连接**：只读检查，依次校验 SSH 地址格式、匿名 API 能否看到仓库（看得到即公开，
   拒绝）、`git ls-remote`（读）与 `git push --dry-run`（写、历史是否冲突）。
4. **保存并推送**：写入 `origin` 与 `core.sshCommand`，`git push -u`。非 GitHub 平台无法
   自动确认私有性，需要勾选人工确认。

每日自动备份：systemd user timer `nblane-backup.timer`，每天 03:30（OpenClaw 记忆整理
03:00 之后）执行 `nblane backup run`。工作区整体快照（`git add -A`）后推送；nblane 数据
只推送（应用已逐次提交，残留的未跟踪文件留给人看，不自动收进仓库）。

命令行：`nblane backup status`、`nblane backup run [--target <id>]`（任一目标失败退出码 1）。

## 隔离开发

`scripts/dev-web.sh --isolated` 为这两张卡设置独立的 OpenClaw profile
（`NBLANE_OPENCLAW_PROFILE=nblane-dev`，状态在 `~/.openclaw-nblane-dev`，网关 19789、unit
`openclaw-gateway-nblane-dev.service`）、`.dev-data/agent-data`、`.dev-data/backup` 与
`nblane-backup-dev` 定时器，不会碰生产网关、密钥和定时器。

## 已知限制

- `openclaw backup create` 在旧安装残留的 `skills/.venv` 存在时失败（venv 里有绝对路径
  软链接），迁移前的安全备份因此改用 tar。新的接入不再创建该 venv。
- 若 OpenClaw 的 nblane MCP 指向另一个 `NBLANE_ROOT`（例如开发环境误连生产网关），卡片
  只读，接入/迁移/网关操作一律拒绝。
- 安装/迁移任务在 SPA 后端进程内的后台线程运行，服务重启会中断任务（迁移的回滚依赖
  任务本身，中断后按 `/srv/backups/agents/` 的 tar 包手工恢复）。
- 云端 agent（Muse、Kimi Claw 等）需要远程 MCP 端点，本页暂不覆盖。
