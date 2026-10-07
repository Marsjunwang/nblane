---
status: active
owner: engineering
last_verified: 2026-10-07
source_of_truth: true
---

# AI 架构

nblane 内的 AI 分两类：页面里的短任务走 AI Gateway 直接调模型；复杂多步工作交给外部 Agent（个人助手 OpenClaw、Codex 等），它们通过 HTTP 读写 nblane，不嵌进 nblane。

```text
SPA / CLI / Reader 短任务
  → core/ai/ AI Gateway（action → backend → 结构化输出 → run 日志）
  → OpenAI-compatible API / 本地翻译模型 / 本地 Codex 只读 / 规则兜底

个人助手 OpenClaw（微信等渠道）
  → nblane_api.py（HTTP，服务账号）
  → /api/v1 + agent_write_guard（分级、确认、撤销日志）
  → core/ → profile 文件

本机 Cursor / Claude Code
  → nblane-mcp（stdio，无登录无 ACL，暂停扩展）
```

## AI Gateway

模块：`src/nblane/core/ai/`

| 文件 | 职责 |
|------|------|
| `gateway.py` | `run_ai_action` 统一入口：选 backend、调用、修复一次、记录 run |
| `router.py` | `ACTION_SPECS` 动作注册表：owner、默认 / 兜底 backend、输出模式、schema |
| `actions.py` | 请求 / 结果 / 规格数据结构 |
| `backends.py` | `direct_llm`、`local_translation`、`rule_fallback`、`workflow_agent`、`external_agent`、`local_codex_readonly` |
| `structured.py` | JSON 提取与轻量 schema 校验 |
| `prompts.py` | prompt 注册 |
| `runs.py` | `ai-runs/YYYY-MM-DD.jsonl` 运行记录 |
| `exceptions.py` | AI 异常汇总（顶栏「AI 异常」抽屉），支持忽略 |
| `skill_suggest.py` | 技能关联建议：embedding → LLM → 规则三级 |
| `local_models.py` / `local_translation.py` | 可安装的本地翻译模型（llama.cpp，懒启动） |

已注册的动作覆盖：论文翻译 / 解释 / 问答 / 深读 / 速读卡 / 断言提取、来源推荐、简历要点与 JD 定制、博客候选与行内改写、看板任务对齐与子任务、证据结晶、项目引用建议、简历 / 看板摄入、视觉配图说明、每日简报、占卜。完整列表以 `router.py` 为准。

约定：

- 新 AI 流程必须注册为 action 走 Gateway，路由和页面不直接调 provider SDK。
- 路由按 profile 的 AI 路由设置（`web-preferences.yaml`）选 backend；未配置时回退 `LLM_MODEL`。
- 失败要显式：降级到规则兜底时结果带标记，页面显示；失败进 AI 异常抽屉。
- 长任务走 web_api jobs + SSE，不做前端轮询。
- run 日志默认不保存完整私密 prompt。
- `llm.py` 保留旧薄封装供兼容。

## 外部 Agent 与 harness

- 外部 harness（OpenClaw、Codex、OpenCode）负责多步任务、长对话、渠道和定时任务；nblane 不把它们嵌为库或子进程。harness 可替换，换掉不丢档案。
- Codex：页面可用本地 Codex 作为只读 AI backend；改代码类 handoff 由 `external_agent` 创建 `agent-tasks.yaml` 任务，结果由人处理。集成细节见 [Agent Harness](../reference/agent-harness.md)。

## 个人助手接入

助手只走 HTTP：`scripts/openclaw/skills/bin/nblane_api.py` 用 `agent: true` 的服务账号调用 `/api/v1`，受 profile ACL 约束。调用规则只有一份：`scripts/openclaw/skills/nblane/SKILL.md`（技能）+ 服务端策略。

服务端策略：

| 组件 | 作用 |
|------|------|
| `core/agent_policy.py` | 动作分级表 T0–T3、批量阈值 3、确认码（10 分钟、一次性、请求指纹） |
| `web_api/agent_guard.py` | 路由 → 动作映射，应用级依赖统一拦截 |
| `core/agent_ops.py` | begin / finish / abort 共享流程（HTTP 与 MCP 共用） |
| `core/agent_journal.py` | 实体级 before / after 撤销日志 `agent-journal.yaml` |

- T1 日常操作（打卡、加任务、勾子任务、习惯计划等）直写、记日志、可撤销。
- T2 重要操作（删除、超过 3 条的批量、改目标 / 北极星 / 技能点、证据编辑与评审、结晶 apply 等）先 428，助手在聊天里请用户确认后带 `X-Nblane-Confirm` 重发。
- T3 页面专属（发布、权限、系统设置）对 Agent 返回 403 `agent_forbidden`。
- 定时任务归 OpenClaw 管（`openclaw automations`），nblane 不同步；`nblane openclaw automations sync` 只是可选的手动工具。

用户侧说明（接入、确认、撤销、助手页）见 [个人助手](../guides/assistant.md)，运维见 [OpenClaw 运维](../guides/openclaw-ops.md)。

## 双记忆模型

nblane 与助手各管一种记忆，不互相投影替换：

| 记忆 | 归属 | 内容 | 特点 |
|------|------|------|------|
| 成长档案 | nblane（权威） | 目标、技能树、证据、项目、Growth Log | 低频、准确、可审查 |
| 情景记忆 | 助手自治 | 会话、daily notes、USER.md | 高频、杂乱，助手自己维护 |

- 巩固：助手把可验证的沉淀经 HTTP 写回 nblane（T1 直写或 T2 确认）。
- 灌注：nblane 的上下文（`core/context.py`、`SKILL.md`）和档案摘要供助手读取。
- 冲突裁决：结构化事实（技能状态、目标、证据）以 nblane 为准；情境与偏好（当日状态、对话风格）以助手为准；运行时事实（模型路由、渠道状态）不进 nblane。

## 安全

- 密钥不进仓库、不进 `profiles/`。OpenClaw 自身的 token / key 用其 SecretRef 机制管理，不写明文配置。
- Agent 写入复用路径安全、文件锁、原子写、Git 备份；撤销遇到后续人工修改时拒绝，不覆盖新内容。
- 服务端无法证明确认是人敲的，这是助手技能的契约；公开发布始终只能在 Web 端由人触发。
- 对生产 Gateway 的变更先 dry-run、先备份、低峰操作。
