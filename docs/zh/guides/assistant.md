---
status: active
owner: 王军
last_verified: 2026-10-07
source_of_truth: false
---

# 助手（OpenClaw）

助手是你自己的常驻 Agent，目前适配 [OpenClaw](https://docs.openclaw.ai/)。你在微信里跟它说「打卡跑步 5 公里」「加个任务」「把那个子任务勾掉」，它直接改 nblane 里的档案。nblane 是它背后的成长档案：Agent 可以换，档案不丢。

运维细节（网关、微信插件、systemd、排障）见 [OpenClaw 运维](openclaw-ops.md)。

## 怎么接入

管理员在「设置 → 系统 → 助手与备份」（`/settings/agents`）完成，全程不用登录服务器。

| 状态 | 点哪个按钮 | 效果 |
|------|-----------|------|
| 本机没有 OpenClaw | 一键安装 OpenClaw | 安装固定版本，网关只监听本机，工作区放在 `/srv/agent-data/openclaw/workspace`，装完自动接入 |
| 已安装 | 接入 nblane | 同步 nblane 技能和 `nblane_api` 命令，生成只读档案语料供助手检索，工作区纳入 git。可重复点 |
| 工作区不在统一数据目录 | 迁移到统一数据目录 | 先整目录打包备份，再移动；微信断开约 10 秒，失败自动回滚 |
| 想在微信里用 | 安装微信渠道 | 安装腾讯的微信插件和 weixin-task-bridge，重启网关。扫码登录在「车间」终端里运行页面给出的命令 |

模型：新装时默认复用 nblane 的 AI 连接（设置 → AI 服务）。已有安装不改它的模型配置，其他服务商在 OpenClaw 控制台里加。

## 助手页

顶栏「助手」（`/assistant`）显示：

- 网关状态：是否就绪、运行时长、版本。右上角「打开控制台」在新标签页打开 OpenClaw 控制台。
- 自动化：OpenClaw 里定时任务的总数和启用数。
- 接入方式：两项各显示「已是最新 / 需更新 / 未安装」。
  - nblane 技能：助手的说明书，写明怎么调用、哪些先问你、怎么撤销。
  - HTTP 接口：唯一通道，以 `openclaw` 服务账号登录，按账号权限检查。
  - 有一项不是最新时，去「设置 → 助手与备份」点一次「接入 nblane」。
- 最近操作：助手的每一次写入，可以逐条撤销（见下文）。

本机没装 OpenClaw 时，页面只显示「本机未安装 OpenClaw」。

## 三类写入

| 类型 | 例子 | 助手怎么做 |
|------|------|-----------|
| 日常操作 | 打卡、加任务、改任务、勾子任务、移动列、排期、阶段计划、新建目标 | 直接执行，告诉你做了什么，可撤销 |
| 重要操作 | 所有删除、一次超过 3 条的批量、改目标 / 北极星 / 技能点、编辑或评审证据、结晶 apply | 先在聊天里把摘要发给你，你回「确认」才执行，可撤销 |
| 只能在页面做 | 发布公开站、简历、内容工作台、权限、系统设置 | 接口拒绝，助手会让你去页面操作 |

重要操作的确认码 10 分钟内有效，只能用一次，换了参数就失效。

规则只有一份，改规则只改这两处：

- 助手侧：[`scripts/openclaw/skills/nblane/SKILL.md`](../../../scripts/openclaw/skills/nblane/SKILL.md)，接入时同步到 OpenClaw 工作区。
- 服务端：[`src/nblane/core/agent_policy.py`](../../../src/nblane/core/agent_policy.py) 的分级表（T0 只读、T1 直写、T2 确认、T3 页面专属）。表里没登记的写操作按 T2 处理。

本机 MCP 不归助手用，见 [MCP 参考](../reference/mcp.md)。

## 撤销

- 在助手页「最近操作」里点「撤销」。也可以在聊天里说「撤销刚才那个」。
- 记录保存在 `profiles/<name>/agent-journal.yaml`，只记助手账号的写入，保留 30 天、最多 500 条。
- 撤销前会检查那条内容之后有没有被改过。改过就显示「已被改动」并拒绝撤销，不会覆盖你后来的修改。
- 编年史这类只追加的记录不回滚。

## 定时任务

定时任务（每日计划、每周巩固、每周占卜等）归 OpenClaw 管，在 OpenClaw 控制台或 `openclaw automations` 命令里建和改。nblane 不同步它们。

- 提示词只写任务本身，调用 nblane 的规则都在 nblane 技能里，所以 nblane 改规则不用动定时任务。
- 每日复盘默认关闭。
- `profiles/template/assistant/` 里有参考提示词和一份可选声明 `automations.yaml`。想用声明维护时手动跑 `nblane openclaw automations sync`，见 [CLI 参考](../reference/cli.md#openclaw)。

## 数据备份

同一张设置页的「数据备份」卡片管理两个私有 git 仓库：nblane 数据（`/srv/nblane-data`）和助手工作区。统一备份，不合并仓库。

没有远端的目标按向导走：

1. 纳入 git。
2. 在 GitHub 新建 Private 空仓库，点「生成部署密钥」，把公钥加到仓库 Deploy keys 并勾选 Allow write access。每个仓库一把密钥。
3. 测试连接：会拒绝公开仓库，并检查读写权限。
4. 保存并推送。

每天 03:30 由 `nblane-backup.timer` 自动备份：工作区整体快照后推送；nblane 数据只推送（应用每次写入已经提交）。命令行等价：`nblane backup status`、`nblane backup run [--target <id>]`。

## 账号

`users.yaml` 里给服务账号写 `agent: true`，它的写入就按上面的规则处理。历史账号 `openclaw` 不写也会被识别。服务账号密码只放在服务器环境变量里，见 [OpenClaw 运维](openclaw-ops.md#服务账号密码)。
