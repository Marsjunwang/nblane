---
status: active
owner: 王军
last_verified: 2026-09-20
source_of_truth: src/nblane/mcp_server.py、src/nblane/core/agent_tasks.py、src/nblane/core/inbox.py、scripts/openclaw/skills/、docs/zh/guides/openclaw-integration.md、本机 OpenClaw 2026.9.4 实测（2026-09-17/18）
---

# OpenClaw × nblane 深度融合总体方案

> 本文是 nblane 与 OpenClaw 深度融合的**分层开发计划**，含优先级、代码级任务、
> 前置测试与验收标准。配套文档：[前端 SPA 迁移方案](frontend-spa-migration.md)
> （L5 层的完整展开）。现状运维手册见
> [OpenClaw 接入指南](../guides/openclaw-integration.md)。

## 实施进度（2026-09-20）

| 层 | 状态 | 落地内容 |
|----|------|----------|
| L0.1 插件入库 | ✅ 已实现 | `scripts/openclaw/plugins/weixin-task-bridge/` + `scripts/openclaw/install.sh`（幂等，含 --dry-run） |
| L0.3 写入加固 | ✅ 已实现 | `core/file_lock.py`（flock 边车锁）；growth_log/team_io 原子化；interaction/crystallize 补 git 备份；六个 save 路径加锁 |
| L0.2 接通 MCP | ⏳ 命令清单已备，待人工窗口执行 | 涉及生产 Gateway 配置变更；清单见接入指南「变更窗口」CW-1 |
| L0.4 备份闭环 | ⏳ 命令清单已备，待人工窗口执行 | `openclaw backup enable` 属生产操作；清单见接入指南 CW-2 |
| L1 MCP 补全 | ✅ 已实现 | 新资源 5（goals/evidence/inbox/learning/activity）+ 新工具 6（capture_inbox、3 个 candidate、validate/sync 只读检查），带 ToolAnnotations + 结构化返回；kanban_move applier 入 `review_actions` |
| L1.4 反向推送 | ✅ 已实现（MVP） | `nblane notify`（webhook 方式；payload 契约待对 live 验证） |
| L2 灌注流 | ✅ 渲染器已实现 | `core/openclaw_corpus.py` + `nblane openclaw sync [--check]`（语料+技能+自动化对账）；`memory.search.extraPaths` 配置待人工（随 CW-3 的 overlay 一并应用） |
| L2 巩固流 | ⏳ 命令清单已备，待人工窗口执行 | `profiles/template/assistant/prompts/` 三个 prompt 已改为 MCP 资源式；生产自动化切换清单见接入指南 CW-3 |
| L3 自动化即代码 | ✅ 已实现 | `core/openclaw_automations.py`（声明/对账/应用，含 adopt 纳管外 key）+ `core/openclaw_ops.py`（doctor 8 项检查）+ `nblane openclaw doctor|sync|install|automations sync` CLI + 顶层 `nblane notify` |
| L4 入口统一 | 🔨 Step 2 已落地（仓库侧） | 助手状态 API `web_api/assistant.py` + SPA 页 `/assistant`（状态卡+深链，无 iframe 无写操作）；Caddy `/openclaw` 反代（Step 1）命令清单已备，待人工窗口执行（接入指南 CW-4） |
| L5 SPA 迁移 | 🔨 M0–M1 进行中 | `src/nblane/web_api/` 已落地：cookie 认证（复用 core/auth HMAC）、profile 作用域 403、只读端点（profiles/summary/health/activity/kanban/inbox/agent-tasks/goals）、activity apply/dismiss（ETag+If-Match 冲突保护）；前端脚手架待建 |
| L6 生产布局 | ⏳ 部分命令清单已备，待人工窗口执行 | 密钥 SecretRef 迁移清单见接入指南 CW-5；三树归一的文档增补仍待办 |

测试基线：≥1470 pytest passed（融合开工前为 1102）+ SPA vitest ≥81 + `spa_smoke` e2e 4/4（随开发递增，2026-09-20 实测 1470 / 81）。

## 0. 背景与目标

### 0.1 现状：三处真实割裂（2026-09-18 实测）

| # | 割裂点 | 证据 |
|---|--------|------|
| 1 | **MCP 根本没有接通** | 本机 `openclaw mcp list` → "No OpenClaw-managed MCP servers configured"。每日计划自动化靠 prompt 里写死绝对路径直接读 `/srv/nblane-data/profiles/王军/kanban.md`，完全绕过了 nblane 的上下文组装与审批闭环 |
| 2 | **双记忆系统平行生长** | OpenClaw workspace 有 `AGENTS.md / MEMORY.md / USER.md / SOUL.md / memory/（20 余篇 daily notes）`，与 nblane 的 `SKILL.md / agent-profile.yaml` / Growth Log 互不感知；复盘产出沉淀在 `~/.openclaw` 而非 `profiles/` |
| 3 | **三棵目录树** | `/home/ubuntu/nblane`（开发）、`/srv/nblane-app/nblane`（生产代码）、`/srv/nblane-data`（生产数据，profile 真源）。自动化 prompt 里手工标注"前两个是过期副本"，换机器/换路径即漂移 |

外围佐证（同属"割裂"症状）：weixin-task-bridge 插件源码只在
`~/.openclaw/workspace/plugins/`、不在仓库；`scripts/openclaw/skills/` 到
`~/.openclaw/workspace/skills/` 靠手抄，文档明示"运行时与仓库不同步"
（2026-09-18 实测当前恰好同步，但没有任何机制保证）；6 条自动化只存在
OpenClaw 的 SQLite 里，仓库无声明。

### 0.2 目标分工

| 职责 | 归属 | 说明 |
|------|------|------|
| 人交互前端、结构化数据存储、特色功能定义 | **nblane** | `profiles/` 是唯一事实源；Web UI 是唯一审批处置面 |
| 成长性自更新、语言交互、自动化管理、对外接口（微信）、调用 agent | **OpenClaw** | 自主维护自己的情景记忆与渠道；通过 MCP 读写 nblane |

### 0.3 核心架构原则：双记忆系统 + 两条流

第一版方案"一切写回 nblane、OpenClaw 文件全是投影"是**错误**的——它会废掉
OpenClaw 的记忆检索能力（`memory/` 混合索引、daily notes、自我维护的
USER.md），把微信助手变成一个只会查库的前台。修正后的模型借自人脑与
Letta 的 sleep-time 设计（§8.1）：

- **情景记忆（OpenClaw 自治）**：会话、daily notes、USER.md 日常维护。
  高频、杂乱、免审批。这是助手"越用越懂你"的来源，**必须保留并增强**。
- **成长档案（nblane 权威）**：技能树、证据池、目标、看板、Growth Log。
  低频、准确、经审批。这是唯一事实源。
- **巩固流（OpenClaw → nblane，相当于"睡眠"）**：每日/每周自动化从情景记忆
  提炼可验证的沉淀，经 MCP 写入（低风险直写）或提交 candidate（人审批）。
- **灌注流（nblane → OpenClaw，相当于"教育背景"）**：结构化档案渲染为只读
  语料喂给 OpenClaw 的记忆索引（官方机制 `memory.search.extraPaths`），
  system prompt 走 `profile://context`。

裁决规则（两处都有同一事实时）：

| 事实类型 | 权威 | 冲突处理 |
|----------|------|----------|
| 结构化事实（技能状态、目标、证据） | nblane | 每周维护对照纠正 OpenClaw 记忆，漂移报告进 Agent Activity |
| 情境与偏好（当日状态、对话风格、临时承诺） | OpenClaw | nblane 不抢；稳定偏好经审批归档进 `agent-profile.yaml` |
| 运行时事实（模型路由、渠道状态） | OpenClaw | 不进 nblane |

### 0.4 非目标（红线）

- 不把 OpenClaw 嵌为 nblane 的库/子进程（`docs/zh/reference/agent-harness.md`
  既定边界：harness 可替换，换掉不丢记忆）。
- 不让 agent 绕过 Agent Activity 直接改 skill-tree 状态、发布公开内容。
- 不把密钥/Owner ID 提交进仓库或 `profiles/`；OpenClaw 密钥走 SecretRef。
- 不用剥离 `X-Frame-Options` 的反代手段内嵌 Control UI（上游明确拒绝，
  见 §6.1/§6.3，该手段削弱点击劫持防护且随时被升级打破）。
- 不引入数据库；维持文件优先（`docs/zh/architecture/storage.md` 边界）。

---

## 1. 优先级总览

排序依据三个维度：**数据丢失风险**（不修会不会丢东西）、**融合核心价值**
（不修融合是否名存实亡）、**依赖关系**（后面的事是否都建立在它之上）。
工作量标注为粗估（1 人全栈，含测试）。

| 层 | 名称 | 优先级 | 工作量 | 排序理由 |
|----|------|--------|--------|----------|
| L0 | 止血与数据安全 | **P0（第 1 周）** | 3–5 天 | 插件源码不入库=迁移即丢；MCP 未接通=融合名存实亡；写入非原子=并发即可能损坏 profile。全是小改动 |
| L1 | MCP 接口补全与闭环接通 | **P0–P1（第 1–3 周）** | 8–12 天 | 融合的承重墙；L2/L4 的功能都建立在新 MCP 面上 |
| L2 | 双记忆流转（巩固+灌注） | **P1（第 2–4 周）** | 6–8 天 | "成长性自更新"的实际载体；依赖 L0 的 MCP 接通与 L1 的新工具 |
| L3 | 自动化即代码与安装统一 | **P1（第 3–4 周）** | 6–8 天 | 解决迁移/漂移；依赖 L0（插件入库），与 L2 并行 |
| L4 | 入口统一与手机访问 | **P2（第 2 月）** | 5–8 天 | 体验整合；只读状态卡依赖 L1，内嵌面板依赖 L5 的 SPA 壳 |
| L5 | 前端重构：Streamlit → SPA | **P2–P3（第 2–4 月，并行轨）** | 40–60 天 | 独立价值最大但工作量最大；与 L0–L4 无代码冲突，见[配套文档](frontend-spa-migration.md) |
| L6 | 生产环境数据布局与运维硬化 | **P2（第 2 月）** | 3–5 天 | 三树归一、备份矩阵、密钥 SecretRef 化；依赖 L3 的安装命令 |

**并行策略**：L0→L1→L2/L3 为主线（串行依赖）；L5 从第 2 周起并行启动
（先做 API 底座，见配套文档）；L4/L6 在主线完成后收口。

**为什么 L5 排最后但不压轴启动**：SPA 迁移不阻塞任何 OpenClaw 融合工作
（融合全部发生在 CLI/MCP/文件层），反过来 L4 的内嵌助手面板需要 SPA 壳。
因此 L5 以"API 底座先行"的方式早早开工、最后交付。

---

## 2. L0 止血与数据安全（P0）

目标：消除"今天就会丢数据/已经名存实亡"的四个点。全部小步快跑、当天可回滚。

### L0.1 weixin-task-bridge 插件源码入库

- 任务：将 `~/.openclaw/workspace/plugins/weixin-task-bridge/`（`package.json`、
  `openclaw.plugin.json`、`dist/index.js`）复制为
  `scripts/openclaw/plugins/weixin-task-bridge/`；剔除配置中的真实 Owner ID
  （插件 config 在 `openclaw.json` 里，源码本不含，复制后 grep 确认：
  `grep -rE '@im\.wechat' scripts/openclaw/` 应为空）。
- 在 `scripts/openclaw/` 加 `install.sh`：`rsync` skills + `openclaw plugins
  install <repo 路径> --force --accept-capabilities`（幂等，重跑即更新）。
- 验收：`rm -rf ~/.openclaw/extensions/weixin-task-bridge` 后能从仓库重装并
  `openclaw plugins inspect weixin-task-bridge --runtime --json` 显示 loaded。
- 前置测试：先在测试副本验证插件包完整性 `cd scripts/openclaw/plugins/
  weixin-task-bridge && npm pack --dry-run`（不发布，只看文件清单）。

### L0.2 接通 nblane MCP（融合的实际起点）

现状：生产 Gateway 零 MCP 配置，自动化直接读文件。任务：

1. 生成配置（已有工具）：`nblane sync-agent-harness --target openclaw
   --profile 王军`，确认 `command` 为 `/srv/nblane-app/nblane/.venv/bin/
   nblane-mcp` 绝对路径、`env` 含 `NBLANE_ROOT=/srv/nblane-data` 与
   `NBLANE_PROFILE=王军`（生成逻辑：`src/nblane/core/mcp_client_config.py:63`
   `build_openclaw_mcp_snippet`；命令解析 `:18` 已含 which/回退逻辑）。
2. 写入 Gateway：**用 `openclaw config patch`（JSON5 递归合并，自带
   `--dry-run`）** 而非手改 JSON：

   ```bash
   openclaw config patch --stdin --dry-run <<'JSON5'
   { mcp: { servers: { nblane: {
     command: "/srv/nblane-app/nblane/.venv/bin/nblane-mcp",
     env: { NBLANE_ROOT: "/srv/nblane-data", NBLANE_PROFILE: "王军" }
   } } } }
   JSON5
   ```

3. 验收四板斧：`openclaw mcp list` 出现 nblane；`openclaw mcp probe nblane`
   列出 13 个工具（7 旧 + 6 新；注意：`openclaw mcp tools` 是设置工具过滤器的命令，
   不能列工具）；在主会话里让 agent 读 `profile://summary` 成功；微信里问
   "我当前看板有什么" 能得到真实数据。
4. 回滚：`openclaw config unset mcp.servers.nblane`（config 有 `.bak` 环）。

### L0.3 写入路径加固（消除非原子写与无备份写）

代码事实（已核实）：

| 写入方 | 现状 | 问题 |
|--------|------|------|
| `core/growth_log.py:48` | `skill_md.write_text(...)` | **非原子**（崩溃可截断 SKILL.md），有 git backup |
| `core/interaction.py:31` | `open(path,"a")` | 原子性尚可（追加单行）但**无 git backup** |
| `core/crystallize.py:18` | `atomic_write_text` ✓ | **无 git backup** |
| `core/team_io.py:50,67` | 裸 `write_text` | **非原子**，有 backup |
| 全部 `save_*` | 无锁、无版本号 | 两个进程并发 read-modify-write 会丢更新（MCP 多工具并发时真实存在） |

任务：

1. `growth_log` / `team_io` 改走 `core/file_write.atomic_write_text`；
   `interaction` / `crystallize` 补 `git_backup.record_change`。
2. 新增 `core/file_lock.py`：基于 stdlib `fcntl.flock` 的
   `locked_profile_write(profile_dir, filename)` 上下文管理器
   （`scripts/openclaw/skills/bin/dev_delegate.py` 已用 fcntl，证明运行环境
   可用；不加第三方依赖）。先覆盖 L1 要经 MCP 暴露的写路径：
   `save_inbox`、`save_agent_tasks`、`save_agent_activity`、`save_skill_tree`、
   `save_evidence_pool`、`save_kanban`。
3. 测试（沿用既有模式）：`tests/test_file_lock.py` 起两个进程并发写
   inbox.yaml 100 次断言零丢失；`test_growth_log.py`/`test_team_io.py` 断言
   走 atomic 路径（mock `atomic_write_text` 被调用）；`test_interaction.py`
   断言 `git_backup.record_change` 被调用（patch 模式见
   `tests/test_inbox.py:188-191`）。

### L0.4 备份闭环

- OpenClaw 侧：`openclaw backup create` 手动验证一次 → `openclaw backup
  enable --every 24h`（官方：重复执行是更新而非重复创建）；归档落盘到
  `~/.openclaw` 之外的私有加密位置。
- nblane 侧：确认生产数据仓 `/srv/nblane-data` 的
  `NBLANE_DATA_GIT_AUTOCOMMIT=1` + `AUTOPUSH` 指向私有远端
  （机制：`core/git_backup.py:116` `record_change`）。
- 文档化恢复演练：从 backup 恢复到一个临时目录 + `nblane validate` 通过。

---

## 3. L1 MCP 接口补全与闭环接通（P0–P1）

目标：把 MCP 从"6 资源 7 工具、纯文本"补全为融合所需的完整读写面。
现状基线（`src/nblane/mcp_server.py`）：资源 `profile://summary|kanban|
context|gap/{task}`、`agent://tasks|task/{task_id}`；工具 `append_growth_log`、
`log_skill_evidence`、`log_interaction`、`suggest_skill_upgrade`（纯建议）、
`crystallize_method_draft`、`submit_agent_task_candidate`、
`update_agent_task_status`。

### 3.1 新增资源（只读，低风险）

| URI | 内容 | 数据来源 |
|-----|------|----------|
| `profile://goals` | goals.yaml 摘要 + North Star 全文（2026-09-23 起二元可见性,只门控公开产物,agent 上下文不再脱敏;private 目标仍不出现) | `core/goals.py` |
| `profile://evidence` | 证据池摘要（count by status + 最近 N 条） | `core/profile_io.load_evidence_pool` |
| `profile://inbox` | inbox.yaml 未处置条目 | `core/inbox.load_inbox:310` |
| `profile://learning` | learning-log 摘要 | `core/learning_log.py` |
| `agent://activity` | 待审批队列摘要（kind/status 计数 + 前 N 条标题） | `core/agent_activity.activity_summary:259` |

### 3.2 新增工具（写面；审批分级）

设计规则：**直写只给"追加型、低解释成本"的操作；一切改变既有事实的操作
一律走 candidate → Agent Activity 人审**。

| 工具 | 写路径 | 级别 | 说明 |
|------|--------|------|------|
| `capture_inbox(title, raw_text, source, tags)` | `core/inbox.add_inbox_item:360` + `save_inbox:660`（原子+备份✓） | **直写** | 微信随手记入口；`captured_by="openclaw"`；inbox 状态机已完备（`INBOX_STATUSES`，`core/inbox.py:18`），目前**无任何 UI/MCP 暴露**，此工具是接通微信捕获的关键 |
| `submit_evidence_candidate(skill_id, title, evidence_type, date, url, summary)` | `agent_activity.append_activity_item`（`candidate_type="evidence"`，`target_owner="evidence_pool"`） | candidate | 复用已有审批链：`core/review_actions.py:316` `apply_review_evidence_candidate` 已能处置 |
| `submit_kanban_candidate(action, card_ref, payload)` | 同上（`target_owner="kanban"`） | candidate | **需扩展** `review_actions` 新增 kanban 处置器（现仅支持 evidence/next_action/public_draft 三类，`:316/407/448`） |
| `submit_profile_model_candidate(field, proposed_value, rationale)` | 同上（`target_owner="profile_context"`） | candidate | USER.md 稳定偏好 → `agent-profile.yaml` 的审批入口（L2 巩固流的落点） |
| `run_validate()` | `core/validate.validate_one:22` | 只读 | agent 自检查数据健康 |
| `run_sync_check()` | `core/sync.get_drifted_blocks:196` | 只读 | 报 SKILL.md 漂移，不写 |

### 3.3 结构化输出与工具注解

- 现状痛点：所有工具返回 `ERROR:`/`OK:` 前缀的字符串，agent 只能靠正则解析。
- 方案：新工具返回 dict（FastMCP 自动生成 structuredContent + outputSchema）；
  存量工具保留字符串以兼容已部署的 prompt，文档标记 soft-deprecated。
- 工具注解（Basic Memory 的成熟实践，§8.6）：为每个工具声明
  `readOnlyHint / destructiveHint / idempotentHint`，让 OpenClaw 不误用写工具。
- 已核实（2026-09-18 本机实测）：`mcp==1.26.0` 的 `@mcp.tool` 签名已含
  `annotations` 与 `structured_output` 参数；`ToolAnnotations` 字段为
  `title / readOnlyHint / destructiveHint / idempotentHint / openWorldHint`。
- 同步更新 `core/mcp_client_config.py:63` 的 snippet 生成器（现在资源/工具
  清单是硬编码的，改为从注册表自省生成，防止文档漂移）；顺带修正 snippet
  里错误的验证命令 `openclaw mcp tools` → `openclaw mcp probe`
  （`core/mcp_client_config.py:98` 现有 bug：`mcp tools` 实为设置工具
  过滤器的命令，不能列工具）。

### 3.4 反向通道：nblane → 微信推送

OpenClaw 侧两种现成机制（均已核实存在）：

1. **Webhook 自动化**（推荐 MVP）：`POST /hooks/agent` / `/hooks/<name>`
   入站钩子 → nblane 新增 `nblane notify <text>` CLI（httpx POST，token 从
   `.env` 读）。用途：看板逾期提醒、周报告推送。
2. **`openclaw mcp serve`**（备选）：把 OpenClaw 渠道会话暴露为 MCP server
   （`messages_send` 等工具），nblane 以 MCP client 消费。能力更强（能读会话）
   但引入 client 生命周期管理，MVP 不用。

### 3.5 测试与验收

- 每个新工具/资源配 pytest：`tests/test_mcp_<x>.py`，沿用
  `tests/test_mcp_agent_tasks.py:59-63` 模式（tmp profile + patch
  `resolve_active_profile` + 直接调工具函数）。
- `review_actions` 的 kanban 处置器配应用/回滚测试。
- 端到端验收（真实 Gateway）：微信发"记一下：xxx" → `profile://inbox`
  出现条目 → Web UI 处置；微信问"我有什么待审批" → 读到
  `agent://activity` 摘要。

---

## 4. L2 双记忆流转：巩固与灌注（P1）

目标：让"成长性自更新"真实发生——OpenClaw 的记忆系统**保留并增强**，
同时成长沉淀进入 nblane 档案。对应 Letta 的 sleep-time 模式（§8.1）：
主会话不打断（微信体验），后台任务做巩固。

### 4.1 灌注流：nblane → OpenClaw 记忆语料

官方机制（已核实）：`memory.search.extraPaths` 可把额外 Markdown 目录纳入
OpenClaw 的混合检索（BM25+向量），正是跨 agent 共享语料的文档化方式。

任务：

1. 新增 `core/openclaw_corpus.py`：从 profile 渲染只读语料到
   `~/.openclaw/workspace/memory/nblane/`：
   - `skill-tree.md`（`skill-tree.yaml` 渲染，复用 `core/sync.py:182`
     `build_generated_blocks` 的渲染器抽取复用）
   - `goals.md`(private 目标不出现;North Star 全文——二元可见性只门控
     公开产物,见 home-editing-starmap-design.md §1)
   - `kanban.md`（直接复制，本来就是 Markdown）
   - `profile-summary.md`（`mcp_server.build_summary_text:96` 复用）
   每个文件头部加 frontmatter 式注释：`source: nblane / generated:
   <ts> / do-not-edit`。
2. `nblane openclaw sync`（L3 的命令）顺带执行语料渲染 + `openclaw config
   patch` 确保 `memory.search.extraPaths` 包含该目录 + 触发
   `openclaw memory status --index` 让索引刷新。
3. 漂移检测：`nblane openclaw sync --check` 对语料做 diff（同
   `nblane sync --check` 体验）。
4. 效果：微信里问"我 robotics 技能树下一步是什么"→ OpenClaw 自己的
   `memory_search` 直接命中，无需 MCP 往返；记忆系统能力**变强**而非被取代。

注意边界：语料是**派生物**，OpenClaw 可自由读；它的 daily notes/MEMORY.md
仍由它自己写。两边井水不犯河水。

### 4.2 巩固流：改造三个既有自动化

现状（实测）：`personal-assistant-daily-plan`（08:30）、`-daily-review`
（21:30）、`-weekly-maintenance`（周日 20:00），prompt 内嵌绝对路径、
直接读写 OpenClaw 自己的记忆文件。

改造（改 prompt + 换工具面，不动调度）：

| 自动化 | 现状 | 目标行为 |
|--------|------|----------|
| daily-plan | 读 `/srv/nblane-data/profiles/王军/kanban.md` 等文件 | 改读 MCP 资源 `profile://kanban`、`profile://goals`（路径无关，解决三树漂移） |
| daily-review | 写 OpenClaw daily memory | daily memory 照写（自治）；**另**将可验证进展调 `append_growth_log` + `log_interaction` 写回 nblane |
| weekly-maintenance | 整理 MEMORY.md/USER.md | 保留自治整理；**另**把稳定偏好/新认识打包为 `submit_profile_model_candidate` → Agent Activity 人审；把与 skill-tree 矛盾的 MEMORY.md 条目标记并生成漂移报告 |

prompt 模板入库：`profiles/<name>/assistant/prompts/{daily-plan,
daily-review,weekly-maintenance}.md`（L3 的 automations.yaml 引用它们），
提示词从"读死路径"改为"优先 MCP，资源列表见 `profile://summary`"。

### 4.3 微信随手记 → inbox 闭环

Blinko 双层笔记模式（§8.5）：闪记（闪念）→ 周回顾时晋升（整理）。
落法：

1. L1 的 `capture_inbox` 工具 + 微信侧 prompt 规则：用户转发链接/想法/
   截图描述 → agent 分类打 tag → `capture_inbox`。
2. 人侧处置面：inbox 目前**没有 UI 页面**（实测确认），短期由
   `pages/8_Review.py` 的周回顾流程承载（它已读 inbox 计数，
   `core/growth_review.py:143/303`）；中期在 SPA 里做专门的 Inbox 页
   （见配套文档 L5 页面规划）。
3. 验收：微信发"记一下：https://… 这篇讲的技能图谱方法不错" →
   `profiles/王军/inbox.yaml` 新增 `captured_by: openclaw` 条目 →
   周回顾页可见可处置（to_kanban_queue / to_evidence_draft 等已有动作，
   `core/inbox.py:26`）。

### 4.4 测试与验收

- `tests/test_openclaw_corpus.py`：渲染输出的快照测试 + 隐私测试
  （private 目标不外泄;North Star 对 agent 永远可见）。
- 端到端：手动跑一次 daily-review 自动化（`openclaw automations run <id>
  --wait`），断言 SKILL.md Growth Log 增行、OpenClaw daily memory 也写。
- 漂移报告：人为在 MEMORY.md 写一条与 skill-tree 矛盾的事实，跑
  weekly-maintenance，断言 agent-activity 出现 review 项。

---

## 5. L3 自动化即代码与安装统一（P1）

目标：把 989 行人工运维指南收敛为**声明式文件 + 幂等命令**。借鉴
Home Assistant 的 YAML 分区模式与 Windmill 的 git 同步模式（§8.3/8.4）。

### 5.1 目录约定：profile 内的 `assistant/`

```
profiles/<name>/assistant/
├── automations.yaml          # 自动化声明（本层核心）
├── openclaw.overlay.json5    # 非密钥 Gateway 配置 overlay
└── prompts/                  # 自动化 prompt 模板（§4.2 引用）
    ├── daily-plan.md
    ├── daily-review.md
    └── weekly-maintenance.md
```

`profiles/` 在生产数据仓 `/srv/nblane-data`（私有 git）内，故声明文件天然
随数据仓版本化、迁移；模板进 `profiles/template/assistant/` 入库。

### 5.2 automations.yaml 声明式模型

借鉴 HA 教训（§8.3）：**按来源分区**。nblane 只管理
`declarationKey` 前缀为 `nblane:` 的任务；OpenClaw 系统任务
（`heartbeat:main`、`memory-core:*`）与手工任务一律不碰。YAML 只由人手
和 CLI 写，不做 UI 回写（规避 pyyaml 丢注释问题；若未来 UI 化再评估
ruamel.yaml）。

```yaml
# profiles/<name>/assistant/automations.yaml
version: 1
defaults:
  tz: Asia/Shanghai
  model: qwen/qwen3.7-flash
  fallbacks: [rightcode/gpt-6-astra]
  session: isolated
  timeout_seconds: 300
  deliver:
    channel: openclaw-weixin
    to: ${WEIXIN_OWNER_ID}        # 从本机 .env / 环境注入，永不入库
automations:
  - key: nblane:daily-plan        # → declarationKey，幂等锚点
    name: 每日计划
    cron: "30 8 * * *"
    prompt: prompts/daily-plan.md  # 相对本文件
  - key: nblane:daily-review
    name: 每日复盘
    cron: "30 21 * * *"
    prompt: prompts/daily-review.md
  - key: nblane:weekly-maintenance
    name: 每周巩固
    cron: "0 20 * * 0"
    session: main                  # 覆盖 defaults
    model: qwen/qwen3.8-flash      # 主会话可能很长，保持 3.8
    prompt: prompts/weekly-maintenance.md
```

同步实现 `core/openclaw_automations.py` + `nblane openclaw automations
sync [--dry-run]`：

1. `openclaw automations list --all --json` 拉全量；
2. 按 `declarationKey` 对账：声明有而运行时无 → add；两边都有但字段漂移
   → edit；运行时有 `nblane:` 前缀而声明无 → 提示（默认不删，`--prune`
   才删）；
3. `automations add` 支持 `--declaration-key`（已实测存在），官方文档说明
   reconcile 语义（常规声明保留 stopped/failure 状态），正好满足幂等；
4. 前置验证：先在生产用 `--dry-run` 对账现有 3 条 `personal-assistant:*`
   任务，确认能无损纳管（迁移 = 改 key 或声明里 adopt 现有 key）。

### 5.3 配置 overlay：`openclaw.overlay.json5`

- 内容：模型路由、fallbacks、utilityModel、心跳、渠道开关、`memory.search.
  extraPaths`、`mcp.servers.nblane`——**全部非密钥**。
- 应用：`openclaw config patch --stdin --dry-run < profiles/<name>/assistant/
  openclaw.overlay.json5`，人确认后去掉 `--dry-run` 正式 patch（官方 JSON5
  递归合并，strict 校验，`.bak` 环兜底）。
- 密钥一律不入 overlay：现有明文 key 的治理走 L6 的 SecretRef 迁移。

### 5.4 一键命令与体检

新命令组 `nblane openclaw …`（落 `src/nblane/commands/openclaw.py` +
`core/openclaw_ops.py`）：

| 命令 | 行为 |
|------|------|
| `nblane openclaw doctor` | 把接入指南的 A–E 分层条件脚本化：Node 版本（24.16+/26.1+）、linger、18789 监听、`nblane-mcp` 在 Gateway PATH、`openclaw mcp list` 含 nblane、微信插件版本 ≥、automations 对账、备份调度存在。只读，exit code 反映健康 |
| `nblane openclaw install [--dry-run]` | 幂等全装：skills rsync → `~/.openclaw/workspace/skills/`；插件 install（L0.1）；config patch overlay；MCP 注入；语料首渲染；automations sync |
| `nblane openclaw sync [--check]` | 日常漂移对账：skills diff、语料 diff、overlay diff、automations diff，一项不合即非零退出（进 cron 周报） |

实现要点：所有对 OpenClaw 的调用走 subprocess 包 `openclaw … --json`；
解析失败即报错退出，不静默吞。**禁止**在命令里调 `openclaw doctor`
（它会重启 Gateway——生产微信通道会断）。

### 5.5 测试与验收

- `tests/test_openclaw_automations.py`：用录制好的 `automations list --json`
  fixture 测对账逻辑（add/edit/keep/prune 四分支 + 不碰非 `nblane:` key）。
- `tests/test_openclaw_ops.py`：doctor 各检查项用 mock subprocess 输出驱动。
- 真实验收：在一台干净 VM/容器跑 `nblane openclaw install` → doctor 全绿
  → 微信收到 daily-plan。这就是新机器迁移的验收标准。

---

## 6. L4 入口统一与手机访问（P2）

目标：手机一个域名访问一切——nblane Web、OpenClaw 控制台、以后的 SPA 助手
面板。**先纠正一个直觉方案**：把 Control UI 用 iframe 嵌进 nblane 页面
**不可行**，这不是配置问题而是上游的明确决策（§6.1）。

### 6.1 关键事实（2026-09-18 实测 + 官方文档）

| 事实 | 证据 |
|------|------|
| Control UI 与 Gateway 同端口（18789），Vite+Lit SPA，走 WebSocket | `HEAD http://127.0.0.1:18789/` → 200 text/html；docs.openclaw.ai/web |
| **iframe 硬封禁**：响应头 `X-Frame-Options: DENY` + CSP `frame-ancestors 'none'`，无配置开关 | 本机响应头实测；官方 issue #47565 于 2026-08-22 closed as not-planned |
| **官方支持子路径反代**：`gateway.controlUi.basePath` + `gateway.publicOrigin`，改动需重启 Gateway | docs.openclaw.ai/web/urls |
| 认证在 **WebSocket 握手**（`connect.params.auth.token`），token 只存 sessionStorage，不出现在 URL | docs.openclaw.ai/web/control-ui/security-model |
| 无 REST 外 API（`/api/v1/health` 404）；程序化面是 WS 协议 v4 + 官方 `@openclaw/gateway-client` + 默认关闭的 `admin-http-rpc` 插件 | 本机实测 404；docs.openclaw.ai/gateway/protocol、/plugins/admin-http-rpc |

### 6.2 三步走

**Step 1：子路径反代（1 天，手机立即可用）**

Caddyfile 在现有站点内追加（现有路由表见 deployment 文档，本次实测确认
18789 未入 Caddy、全站 loopback-only）：

```caddy
handle /openclaw/* {
    reverse_proxy 127.0.0.1:18789   # WebSocket upgrade Caddy 自动处理
}
```

Gateway 侧（走 L3 的 overlay，不手改）：

```json5
{ gateway: { controlUi: { basePath: "/openclaw" },
             publicOrigin: "https://<域名>/openclaw" } }
```

- 前置测试：`caddy validate`；`curl -sI https://<域名>/openclaw/` 期望 200；
  桌面浏览器 WS 握手正常（Control UI 能登录）后再上手机。
- 手机体验：Safari/微信浏览器打开 `https://<域名>/openclaw/` → 粘贴一次
  token（sessionStorage 保存）→ 可加到主屏当 PWA 用。token 永不进 URL、
  不进 nblane、不进 Caddy access log 明文（无 query 参数承载）。
- 回滚：删 Caddy `handle` 块 + `config unset` 两个键，重启 Gateway。

**Step 2：nblane「助手」页 v1（Streamlit 期，2–3 天）**

不做 iframe，做**状态卡 + 深链**：

> 实现注记（2026-09-19）：Step 2 直接落在 SPA/API 侧而非 Streamlit 页——
> 后端 `GET /api/v1/system/assistant`（`src/nblane/web_api/assistant.py`，
> `require_user`、非 profile 作用域，各 probe 独立兜底 5s 超时、app.state
> 60s 缓存，`console_url` 取自 `NBLANE_OPENCLAW_CONSOLE_URL`），前端
> `/assistant` 页（状态卡网格 +「打开控制台」新标签 + 未安装空态），
> 顶栏右侧新增「助手」入口。Streamlit 版 `pages/13_Assistant.py` 不再
> 单独建设。

- 新页 `pages/13_Assistant.py`：展示 Gateway 健康（版本、渠道状态、
  automations 列表、MCP 连接状态、备份新鲜度）+「打开控制台」新标签按钮。
- 数据获取：后端 shell 调 `openclaw gateway call status --json` /
  `automations list --all --json` / `mcp list`（subprocess + 10s 超时 +
  60s 缓存），**零 token 需求**（CLI 本机认证）。这与 nblane 既有
  `codex_adapter.py` 的 subprocess 模式一致。
- 价值：人不用记两个入口；状态巡检从 SSH 命令变成页面一瞥。

**Step 3：SPA 内嵌实时面板（L5 壳就绪后，spike 先行）**

- 目标：SPA 内直接看会话/发消息/审批 exec——一个原生「助手」页，而非
  套壳 Dashboard。
- 架构：浏览器 ⇄ FastAPI WebSocket 代理（nblane 会话认证）⇄ Gateway WS
  协议 v4（device identity + token 存服务端 `.env`，浏览器永不可见）。
- **Spike 任务（0.5 天，Go/No-Go）**：Python `websockets` 实现 protocol
  v4 最小子集——pairing、`sessions.list`、`chat.history`、
  `sessions.messages.subscribe`。官方客户端是 TS 包
  （`@openclaw/gateway-client`），Python 侧需自证协议兼容；schema 可从
  npm 包 `@openclaw/gateway-protocol` 的 `protocol.schema.json` 机械生成。
- No-Go 回退：启用 `admin-http-rpc` 插件（本机已装未启用），HTTP 轮询
  `cron.list / tasks.* / channels.* / health`（allowlist 只读方法）做
  只读面板；发消息能力留在新标签控制台。
- 微信对话本身不需要这个面板——它永远是第一公民渠道；面板服务的是
  "在电脑前时的一体化体验"。

### 6.3 明确否决项

- **否决**：反代剥离 `X-Frame-Options` / 改写 `frame-ancestors` 实现 iframe
  内嵌。理由：上游 closed not-planned（升级随时打破）；削弱全站点击劫持
  防护；认证在 WS 握手层，iframe 里照样要处理。
- **否决**：把 18789 直接绑 `0.0.0.0`「方便手机」。一切入口走 Caddy+TLS。

---

## 7. L6 生产环境数据布局与运维硬化（P2）

### 7.1 三树归一

| 树 | 角色 | 规则 |
|----|------|------|
| `/srv/nblane-data` | **唯一数据根**（profiles/schemas/teams/auth/.env，私有 git） | 一切读写只发生在这；`NBLANE_ROOT=/srv/nblane-data` |
| `/srv/nblane-app/nblane` | 生产代码 | 只读部署；`.venv` 内 `nblane-mcp` |
| `/home/ubuntu/nblane` | 开发 | 只跑 `dev-web.sh --isolated`（18502/18503 + `.dev-data/`）；**禁止**用真 profile 写操作 |

动作：MCP env、automations prompt、doctor 检查项全部以 `NBLANE_ROOT`
为准（L0.2/§4.2 落地后，prompt 里不再出现任何绝对路径，三树漂移问题
自然消解）；`docs/zh/guides/deployment-tencent-cloud.md` 增补一节
"OpenClaw 与三树"。

### 7.2 备份矩阵

| 数据 | 机制 | 频率 | 异地 |
|------|------|------|------|
| `/srv/nblane-data` | `NBLANE_DATA_GIT_AUTOCOMMIT=1` + AUTOPUSH 私有远端（`core/git_backup.py:116`） | 每次写入 | 私有 git 远端 |
| `~/.openclaw`（配置+会话+记忆） | `openclaw backup create` → tar.gz（L0.4 已启用 24h 调度） | 每日 | 加密副本出机 |
| OpenClaw 状态库 | `openclaw backup sqlite`（随 tar 调度） | 每日 | 同上 |
| 微信登录态 | 不可备份即重建（扫码成本低），文档化即可 | — | — |

每季度一次恢复演练：tar 解到临时目录 + `openclaw backup verify` +
nblane `validate` 通过。

### 7.3 密钥与日志卫生

- `openclaw.json` 明文 token/key → `openclaw secrets configure/apply` 迁
  SecretRef（env provider 起步）；`secrets audit --check` 纳入
  `nblane openclaw doctor`。
- Caddy access log 脱敏：nblane 的 auth handoff token 走 query 参数
  （既有设计），为 `/auth/*` 路径配置日志 redact（deployment 文档已有
  警示，本层落成配置）。
- systemd：nblane 两个 system unit + openclaw user unit 共存，文档化
  linger 依赖（`loginctl enable-linger`，接入指南 A 层已述）。

### 7.4 监控

- `nblane openclaw doctor` 进每周自动化（周五随周报推送结果到微信）。
- Caddy 层外部探测：`/readyz`（18789 经反代后）+ nblane 8501/8502 健康点。
- 告警通路复用 §3.4 的 `nblane notify` webhook → 微信。

---

## 8. 开源借鉴清单（每项均有出处）

### 8.1 Letta（原 MemGPT）→ 双记忆 + sleep-time 巩固

记忆分层：core（常驻上下文、带 description 的命名块）/ recall（会话检索）/
archival（向量归档）；agent 用显式工具自编辑记忆；0.7+ 的 **sleep-time
agent** 在空闲时异步巩固主 agent 记忆（主循环不带记忆工具，降延迟）。
**借**：nblane 的 L2 巩固流就是 sleep-time 模式——微信主会话不打断，
daily-review/weekly-maintenance 做异步巩固。docs.letta.com/guides/agents/memory、
letta.com/blog/sleep-time-compute

### 8.2 Khoj → 内容索引与自动化投递

Django+FastAPI 混合、pgvector、按内容类型注册 processor；自然语言描述
自动化 → 调度 → 邮件摘要投递。**借**：NL 自动化 → 推送的体验范式
（我们把邮件换成微信）；processor registry 思想可用于未来 research 源。
docs.khoj.dev/features/automations

### 8.3 Home Assistant → 声明式 YAML 与 UI 共存的分区法

UI 建的自动化存 `automations.yaml`（UI 专属），手写走 `configuration.yaml`
的带标签块，两边共存；`id` 字段是 UI 可编辑性的桥；reload 服务免重启；
著名痛点：UI 回写摧毁 YAML 注释。**借**：L3 按 `declarationKey` 前缀分区
（`nblane:` vs 系统/手工），YAML 不做 UI 回写以规避注释问题。
home-assistant.io/docs/automation/yaml

### 8.4 Windmill（对照 n8n）→ git 即自动化事实源

Windmill Git Sync：单文件 `wmill.yaml` + UI 与 git 双向同步、显式
push/pull；n8n 同类能力在付费版。**借**：L3 的 automations.yaml = nblane
的 `wmill.yaml`；采用显式 `sync` 命令而非隐式 watch。
windmill.dev/docs/advanced/git_sync

### 8.5 Blinko / Memos → 闪记双层模型

Blinko："Blinkos（闪记流）vs Notes（晋升整理）"双层，周回顾时晋升；
Memos：零字段快速捕获。**借**：L2.3 微信随手记 = 闪记，`inbox.yaml` 状态机
（inbox→captured→clarified…，已有）= 晋升管道。github.com/blinkospace/blinko

### 8.6 Basic Memory / zettelkasten-mcp → 文件即事实源 + MCP 工具形态

Basic Memory：Markdown+frontmatter 为事实源，SQLite 索引可随时重建；
MCP 工具带 `readOnlyHint/destructiveHint/idempotentHint` 注解；**且已有官方
OpenClaw 插件**（`@basicmemory/openclaw-basic-memory`）——OpenClaw 插件化
分发的直接先例。zettelkasten-mcp：fleeting→permanent 笔记生命周期、
双向语义链接、显式 `zk_rebuild_index`。**借**：L1 工具注解；插件分发的
打包参考；"索引可重建"思想强化 nblane 文件优先原则。
github.com/basicmachines-co/basic-memory、github.com/entanglr/zettelkasten-mcp

### 8.7 Immich / Docmost → SPA 迁移蓝图

Immich：OpenAPI 驱动生成全部 client、cookie 会话 + scoped API key 双认证。
Docmost：React 18 + Vite + **Mantine 8** + TanStack Query + Tiptap——与
nblane 现有组件栈（BlockNote/Mantine，见 `public_blog_editor_component`）
天然一致。**借**：见[前端 SPA 迁移方案](frontend-spa-migration.md)。
docs.immich.app/developer/architecture、docmost.com/docs/self-hosting/development

### 8.8 Open WebUI → 反例确认

FastAPI + SvelteKit、in-process Functions 插件（Filter/Action/Pipe +
Valves 配置）。**确认无"内嵌外部 dashboard"先例**——它自己是被嵌方。
佐证 §6.3 的否决项。docs.openwebui.com

---

## 9. 测试总纲

### 9.1 分层测试矩阵

| 测试层 | 载体 | 覆盖 |
|--------|------|------|
| 单元 | pytest（`tests/`，CI 必跑） | 每个新 core 模块 + 每个新 MCP 工具；沿用 tmp profile + patch `profile_dir`/`resolve_active_profile` 模式（`tests/test_mcp_agent_tasks.py:59-63`） |
| 对账逻辑 | pytest + 录制 fixture | automations/doctor 的 reconcile 与检查逻辑（mock subprocess 输出） |
| 并发 | pytest 多进程用例 | L0.3 文件锁：双进程并发写零丢失 |
| 端到端 | Playwright（`tests/e2e/`，手动触发） | L4 反代后页面可达；SPA 迁移期 parity（见配套文档） |
| 真实环境验收 | 手动清单 | 每层末尾的"端到端验收"条目（微信收发、自动化实跑、`--dry-run` 对账） |

### 9.2 铁律

- 对生产 Gateway 的一切变更：**先 `--dry-run`，先备份（L0.4），低峰窗口
  操作**。Gateway 承载着活的微信通道。
- 永不调用 `openclaw doctor --fix` 于自动化脚本（会重启 Gateway）。
- 新代码一律走 `core/file_write.atomic_write_text` + `git_backup.
  record_change` + L0.3 文件锁。
- CI 五关保持绿（含 frontend-artifacts 前端产物重建比对）：`pip install -e .`、
  `pytest -q`、`nblane validate`、`status` + import smoke、
  frontend-artifacts（.github/workflows/ci.yml）。

### 9.3 各层前置测试清单（开工前必做）

| 层 | 前置验证 |
|----|----------|
| L0.1 | `npm pack --dry-run` 确认插件包完整；`grep` 确认无 Owner ID |
| L0.2 | `config patch --stdin --dry-run` 校验通过；`openclaw mcp probe nblane` 列出 13 工具（7 旧 + 6 新） |
| L0.3 | 并发写测试 100 次零丢失；CI 全绿 |
| L1 | 确认 mcp 1.26 的 `annotations` 参数与结构化返回 API 形态 |
| L2 | `memory.search.extraPaths` 在小目录上验证索引生效后再灌全量 |
| L3 | 生产 `--dry-run` 对账现有 3 条 `personal-assistant:*`，确认无损纳管 |
| L4 | `caddy validate`；桌面 WS 握手通过后上手机 |
| L4 Step 3 | WS 协议 spike（Go/No-Go 判定） |
| L5 | 见配套文档的 API 底座 spike 与 parity checklist |

---

## 10. 风险与回滚

| 风险 | 影响 | 缓解 |
|------|------|------|
| OpenClaw 升级改协议/配置 schema | L4 面板、L3 命令失效 | 版本钉在 stable 通道；升级前跑 `nblane openclaw doctor` 对比；overlay 只覆盖文档化键 |
| MCP 工具面扩大后被误用 | 数据污染 | 分级纪律（§3.2）+ 工具注解 + 评审：任何"改变既有事实"的工具必须走 candidate |
| 双记忆长期漂移 | 助手回答与档案矛盾 | L2 weekly 漂移报告进 Agent Activity，人裁决 |
| SPA 迁移烂尾 | 双前端维护地狱 | 配套文档的 strangler 策略 + 每页 parity 验收，未达标不退役 Streamlit |
| `admin-http-rpc` / WS 协议属半公开面 | L4 Step 3 不稳定 | spike 闸门 + 新标签回退方案常备 |

### 决策记录（本方案内置）

1. **iframe 内嵌 Control UI：否决**（§6.1 事实 + §6.3），采用子路径反代 +
   原生面板路线。
2. **OpenClaw 记忆系统：保留并增强**，不投影替换（§0.3 的双记忆模型）。
3. **automations.yaml 不做 UI 回写**（HA 注释教训），UI 化时机留给 SPA 期
   再评估（届时用 ruamel.yaml）。
4. **反向推送用 webhook 而非 `openclaw mcp serve`**（MVP 简单性）。
5. **Streamlit 全量退役是终态**，迁移期双轨，parity 达标才切（配套文档）。
