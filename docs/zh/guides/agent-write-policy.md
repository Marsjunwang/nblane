---
status: active
owner: 王军
last_verified: 2026-10-07
source_of_truth: src/nblane/core/agent_policy.py、src/nblane/core/agent_ops.py、src/nblane/core/agent_journal.py、src/nblane/web_api/agent_guard.py、src/nblane/mcp_server.py、scripts/openclaw/skills/nblane/SKILL.md
---

# 个人 Agent 写入策略

在微信等聊天渠道里让 agent 打卡、加任务、勾子任务，这些操作应该直接生效，不用再回
nblane 页面点确认。安全感来自两点：**都能撤销**，**重要操作先在聊天里确认**。

## 分级

一张表（`core/agent_policy.py` 的 `ACTION_TIERS`）同时约束 HTTP 和 MCP。OpenClaw 助手只走 HTTP；
MCP 留给 Cursor 这类本机客户端：

| 级别 | 处理方式 | 例子 |
|------|----------|------|
| T0 | 只读，不记录 | 读取、占卜 |
| T1 | 直接执行，写入撤销日志 | 打卡、新建/修改/移动/排期任务、勾 todo、阶段计划增改、习惯归档、项目案例保存/归档、新建目标 |
| T2 | 聊天确认后执行，写入撤销日志 | 所有删除、一次超过 3 条的批量操作、套用计划模板、技能节点/北极星/目标修改、证据编辑、结晶 |
| T3 | 只能在页面操作 | 公开站发布、简历、内容工作台、权限、系统设置、审批队列的通过/驳回 |

表里没有的写操作默认按 T2 处理：新接口要明确登记，才能让 agent 直接写。

## 聊天确认（T2）

1. agent 第一次请求时，服务端返回 `428 confirmation_required`，带 `confirmation.summary`
   和 `confirm_id`，此时什么都没有改。
2. agent 把 summary 发给用户。用户同意后，agent 在同一请求上加
   `X-Nblane-Confirm: <confirm_id>` 重发。
3. 确认码 10 分钟有效，只能用一次，并绑定账号和「方法 + 路径 + 请求体」。拿删除 A 的确认码
   去删 B，会被拒绝。

限制：服务端无法证明确认真的是用户本人在聊天里打出来的，这一点靠 agent 遵守
`skills/nblane/SKILL.md` 的约定。待办是由 weixin-task-bridge 转发用户原话，让确认不能伪造。
HTTP 的确认码存在进程内存里，服务重启后 agent 需要重新发起确认。MCP 每个 agent 会话一个进程，
确认码改存 `~/.local/share/nblane/agent/mcp-confirmations.json`，兄弟进程也能兑现。

## 撤销日志

- 文件：`profiles/<name>/agent-journal.yaml`。它和 `agent-activity.yaml` 分开，只记 agent
  账号的写入，人在页面上的修改不会进来。保留 30 天，最多 500 条。
- 每条日志按实体保存 before/after 快照。快照来自写入前后对相关实体的两次读取和比对，所以
  不用改各个写入函数。撤销时把 before
  写回，但前提是该实体当前仍等于 after。如果之后有人改过，就拒绝撤销
  （`409 journal_undo_conflict`），不覆盖新的修改。
- 接口：`GET /api/v1/profiles/{name}/agent/journal` 和
  `POST /api/v1/profiles/{name}/agent/journal/{id}/undo`。
- 入口：HTTP agent 用 `nblane_api recent` / `undo <id>`，MCP agent 用 `recent_actions` /
  `undo_action`；用户在 SPA「助手」页的「最近操作」卡片里点撤销。
- 编年史（chronicle.yaml）、计划模板使用记录这类只追加的叙事记录不回滚。

## 规则只有一份

- 服务端：`core/agent_policy.py` 的分级表，HTTP 和 MCP 都按它执行。HTTP 还要求账号登录、按账号
  授权的档案检查；本机 MCP 不登录，所以助手不用它。
- Agent 侧：`scripts/openclaw/skills/nblane/SKILL.md`，写明怎么调用、哪些直接做、哪些要确认、
  怎么撤销。「接入 nblane」时同步到 OpenClaw 工作区。
- 定时任务提示词（`profiles/<name>/assistant/prompts/*.md`）只写任务本身要做什么，
  调用规则一律引用 nblane 技能，不在提示词里重复。改规则只需改上面两处。

## Agent 账号

在 `users.yaml` 里给账号写 `agent: true` 即按本策略处理。历史账号 `openclaw` 即使没有这一项，
也会被识别为 agent。

## 覆盖范围（2026-10-07）

HTTP（OpenClaw 助手的唯一通道）：所有 `/api/v1` 写请求都经过一道应用级检查（`web_api/agent_guard.py`），按路由对照分级表。
可撤销的实体：任务卡、打卡、习惯、阶段计划、目标、北极星、技能点、证据、项目（含里程碑）、
收件箱、资料、学习记录。未登记的路由按 T2 处理。

MCP（给 Cursor 等本机客户端）：写工具走同一流程（`core/agent_ops.py`）。看板增/移/删、打卡、收件箱、成长日志、方法草稿
可撤销；`submit_kanban_candidate` 改为直接移动（不再进审批队列）。工具清单见
[MCP 参考](../reference/mcp.md)。

已知代价：快照比对按时间窗归属。人在页面上的修改如果和 agent 的写入落在同一个几毫秒里，
会被一起记进 agent 那条日志。
