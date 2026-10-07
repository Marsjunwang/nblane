---
status: active
owner: product
last_verified: 2026-10-07
source_of_truth: true
---

# 决策记录

## D1 · 中文文档为事实源

结论：`docs/zh/` 是主维护目录。英文只保留入口和关键摘要。

理由：

- 当前中文文档更完整。
- 项目主要讨论和产品规划使用中文。
- 中英完整镜像维护成本过高。

## D2 · 旧过程文档合并后删除

结论：`initial-loop.md`、`public-site-workplan.md`、`public-site-blog-editor-design.md` 等过程文档被吸收到新事实源后删除，不长期归档。

理由：

- 过程文档继续存在会制造过期入口。
- 项目管理信息应集中在 `project/`。
- 历史仍可通过 Git 找回。

## D3 · 文件优先，不立刻上数据库

结论：YAML/Markdown 继续作为事实源。SQLite/Postgres 只作为后续索引缓存或 SaaS 规模化选项。

理由：

- 当前产品价值来自可读、可 diff、可人工编辑的文件。
- 现有 CLI/Web/MCP 已围绕文件工作。
- Obsidian-like 体验可以先通过属性、索引、视图实现。

## D4 · AI Gateway 先于 Harness 集成

结论：先把内部模型调用从 `llm.chat()` 升级为任务化 AI Gateway，再接 OpenCode/Codex。

理由：

- UI 内短任务需要低延迟、结构化输出和可控错误。
- OpenCode/Codex 更适合复杂多步任务，不适合替代所有按钮级模型调用。
- AI Gateway 是未来模型路由、审计、prompt registry 的基础。

## D5 · 助手只走 HTTP，MCP 仅本机

日期：2026-10-07（`83f0ca8`）。

结论：助手（OpenClaw）只通过 HTTP `/api/v1` 访问 nblane（`scripts/openclaw/skills/bin/nblane_api.py`，服务账号 + profile 权限）。`nblane-mcp`（stdio）只给本机 Cursor / Claude Code，暂停扩展。ACP 不进入架构。

理由：

- stdio MCP 绕过登录和 profile 权限。
- OpenClaw 每个会话常驻一个 `nblane-mcp` 进程，心跳会话导致进程堆积。
- HTTP 一处实现写入策略与撤销日志，所有客户端共用。

取代了：「MCP-first，ACP 后评估」。

## D6 · Harness 不内嵌为业务库

结论：OpenClaw、Codex、Cursor、Claude Code 是外部执行器，通过 HTTP 接口、生成的指令和 CLI 集成。

理由：

- 避免绑定某个 harness 的内部 API。
- 保持 nblane 数据模型独立。
- 关掉 OpenClaw，全站照常工作，只是没有主动推送。

## D7 · Public Site 与 Research Workspace 分离

结论：Public Site 继续负责公开发布；Research Workspace 负责 source、chunk、claim、citation、synthesis draft。

理由：

- Public Site 页面已经很重。
- 研究资料默认私有，公开发布必须显式导出。
- 博客需要 source-aware，但不应把私有研究层直接变成公开层。

## D8 · Streamlit 退役

日期：2026-10-06（`ad87958`）。

结论：React SPA（8504）是唯一界面。旧 Streamlit URL 重定向到 SPA 路由，`scripts/dev-web.sh` 默认不再启动 Streamlit。遗留代码待删，不再修改。

理由：

- 双栈维护让每个功能做两遍，Streamlit 写路径缺快照保护。
- SPA 已覆盖全部保留的页面。

取代了：「SPA 为新前端、Streamlit 冻结、按页逐个退役」的过渡安排。

## D9 · Agent 写入直写可撤销，重要操作聊天确认

日期：2026-10-07（`915323f`、`2946ac5`、`83f0ca8`）。

结论：一张策略表（`core/agent_policy.py`）给每个 Agent 写入定级：

- T0 只读。
- T1 日常操作直接写入，记入 `agent-journal.yaml`（保留 30 天 / 500 条），可撤销。
- T2 重要操作（删除、超过 3 条的批量、改目标 / 北极星 / 技能点、证据编辑与评审、结晶 apply 等）先返回 428 和确认码，用户在聊天里同意后带 `X-Nblane-Confirm` 重试；确认码 10 分钟、一次性、绑定调用方和请求。
- T3 发布、权限、系统设置等页面专属操作，对 Agent 返回 403 `agent_forbidden`。

调用规则只写在 `scripts/openclaw/skills/nblane/SKILL.md`，服务端由 `web_api/agent_guard.py` 和 `core/agent_ops.py` 执行。

理由：

- 网页审批让日常打卡、加任务也要人来回点，助手形同虚设。
- 撤销日志让错误写入的代价可控；真正不可逆或影响身份的操作仍需人确认。

取代了：「Agent 写回先进草稿 / 候选，在 Agent Activity 页审批」。

## D10 · 定时任务归 OpenClaw

日期：2026-10-07（`65754db`）。

结论：定时任务由 OpenClaw 自己管理（`openclaw automations`）。nblane 的 `openclaw sync` / `install` / `doctor` 不再列出或对齐定时任务；`nblane openclaw automations sync` 只是可选的手动工具。每日复盘默认关闭。

理由：调用规则已集中在 nblane 技能，提示词只描述任务本身，nblane 没有需要同步的内容。

取代了：「自动化即代码，由 nblane 声明并同步到 OpenClaw」。

## D11 · 单人加自己的 Agent

日期：2026-10-07。

结论：nblane 定位为一个人加自己的 Agent。移除 Team View、团队产品池、Gap Analysis 页、Agent Activity 审批页、Inbox 页、Output Studio 页；路线图不保留远期团队功能。账号只区分本人、助手服务账号（`agent: true`）和管理员。

理由：

- 团队层从未有真实用户，却在数据模型、文档和导航里持续占位。
- 差距分析并入首页占卜，Output Studio 由内容、求职、公开站点三个工作台承接。

取代了：「Private / Agent / Team / Public 四层」和「多个成长单元 + 共享产品池 = 长期复利团队」。

## D12 · 前端只经 API 写，聚合端点单源

日期：2026-09-22 起（Phase 1–3）。

结论：

- 前端从不直接读写 YAML；所有写入走 API，带 ETag / If-Match 和 flock，412 由前端刷新重试或点名冲突。
- `kanban.md` 只经 `core/kanban_io.py` 读写。
- 一页一个聚合端点（`/projects-board`、`/starmap`），ETag 覆盖它读取的全部源文件。

理由：kanban 元数据契约脆弱，多写路径曾导致静默覆盖；单一聚合端点避免前端拼接和缓存不一致。
