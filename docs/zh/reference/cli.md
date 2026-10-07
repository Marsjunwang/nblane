---
status: active
owner: engineering
last_verified: 2026-09-19
source_of_truth: true
---

# CLI 参考

安装后 CLI 入口为：

```bash
nblane <command> ...
```

## Profile

```bash
nblane init <profile>
nblane context <profile>
nblane context <profile> --review
nblane context <profile> --write
nblane context <profile> --plan
nblane context <profile> --no-kanban
nblane status
nblane status <profile>
nblane log <profile> "finished first manipulation demo"
```

## Skill Tree / Evidence

```bash
nblane validate
nblane validate <profile>
nblane sync <profile> --check
nblane sync <profile> --write

nblane evidence <profile> <node_id> add --type project --title "Demo"
nblane evidence <profile> pool add --type project --title "Shared milestone"
nblane evidence <profile> link <node_id> <evidence_id>
nblane evidence <profile> unlink <node_id> <evidence_id>
nblane evidence <profile> pool remove <evidence_id>
nblane evidence <profile> pool deprecate <evidence_id>
```

字段说明见 [Evidence 参考](evidence.md) 和 [Skill Tree Schema](skill-tree-schema.md)。

## Gap / Ingest / Health

```bash
nblane gap <profile> "OpenVLA robot control"
nblane gap <profile> --node ros2_basics

nblane ingest-resume <profile> --file resume.txt
nblane ingest-resume <profile> --stdin --dry-run
nblane ingest-resume <profile> --file resume.txt --allow-status-change

nblane ingest-kanban <profile>
nblane ingest-kanban <profile> --dry-run
nblane ingest-kanban <profile> --allow-status-change

nblane health <profile>
```

## Team

```bash
nblane team <team_id>
```

团队文件位于 `teams/<team_id>/team.yaml` 和 `teams/<team_id>/product-pool.yaml`。

## Public Surface

```bash
nblane public init <profile>
nblane public validate <profile>
nblane public blog new <profile> --title "My post"
nblane public build <profile> --out dist/public/<profile> --base-url https://www.example.com
```

详细说明见 [公开站点指南](../guides/public-site.md)。

## MCP / Agent

```bash
nblane-mcp
nblane sync-cursor <profile>
```

Harness / Codex 命令：

```bash
nblane sync-agent-harness --target codex
nblane sync-agent-harness --target opencode
nblane agent handoff <agent_task_id> --target codex --profile <profile>
nblane agent handoff <agent_task_id> --target opencode --profile <profile>

nblane codex status
nblane codex status --profile <profile>
nblane codex install --print-command
nblane codex install
nblane codex install --upgrade
nblane codex local run <agent_task_id> --profile <profile>
nblane codex cloud submit <agent_task_id> --profile <profile>
nblane codex cloud refresh <agent_task_id> --profile <profile>
nblane codex cloud refresh <agent_task_id> --profile <profile> --diff
```

`nblane codex local run` 是显式 CLI patch runner，不由 Kanban 页面触发；Kanban
内的 Codex 只作为可选只读 AI backend，替代原有看板 LLM 动作。

当前 MCP 说明见 [MCP 参考](mcp.md)，规划见 [Agent Harness](agent-harness.md)。

## OpenClaw

```bash
nblane openclaw doctor
nblane openclaw doctor --profile <profile>

nblane openclaw sync [--profile <profile>]
nblane openclaw sync [--profile <profile>] --check

nblane openclaw install [--profile <profile>] [--dry-run|--apply]

nblane openclaw automations sync <profile> [--apply] [--prune]   # 可选的手动工具

nblane notify <text> [--dry-run]
```

- `doctor` 把接入指南的体检项脚本化（只读）：OpenClaw CLI 版本、Node 版本
  （>=24.16 且 <25，或 >=26.1）、systemd linger、`127.0.0.1:18789` 监听、
  `mcp.servers` 含 nblane、openclaw-weixin 插件已启用、
  备份调度存在（标识含 `backup` 段且带 cron/every 调度的任务，纯文本提及
  不算）。任一 error 级检查失败时退出码为 1，warning 不影响退出码。
  **不会**调用 `openclaw doctor`（它会重启 Gateway）。
- `sync` 是日常漂移对账（§5.4）：渲染记忆语料到
  `~/.openclaw/workspace/memory/nblane/`、把 `scripts/openclaw/skills/`
  复制到 `~/.openclaw/workspace/skills/`（排除 `__pycache__`）。定时任务归 OpenClaw
  管，`sync` 不读也不改。缺省 `--profile` 时使用唯一存在的 profile。
  同步**不再只增不减**：语料侧删除带生成头标记但本次无渲染产物的旧 md
  （如源文件被删后的 `goals.md`；无标记的用户文件不动），技能侧删除
  `src` 已纳管顶层目录（如 `codex-dev/`、`kimi-dev/`、`bin/`）下
  `src` 中已不存在的文件并清理空目录（其他顶层目录视为外来技能树，
  永不触碰）。
  `--check` 不写任何文件，仅对账语料/技能漂移，任一漂移退出码为 1（对齐
  `nblane sync --check`，可进 cron 周报）；多余文件在 `--check` 下也计为漂移
  （分别以 `~` / `-` 标出）。`skills/bin/nblane_api` 是「接入 nblane」生成的包装
  脚本，不算多余文件。未安装 OpenClaw（无 `~/.openclaw`）时报错退出。
- `install` 是一键幂等安装（§5.4），默认 `--dry-run`（打印完整行动计划、
  不改任何东西），`--apply` 才执行。三步：① 技能 + 记忆语料（复用
  `sync` 的写入逻辑；dry-run 只报差异）；② 插件安装（仓库内
  `scripts/openclaw/plugins/weixin-task-bridge/` 存在时执行
  `openclaw plugins install <abs path> --force --accept-capabilities`，
  目录缺失则跳过并提示；dry-run 只打印命令）；③ 配置 overlay（profile
  有 `assistant/openclaw.overlay.json5` 时经 `openclaw config patch
  --stdin` 应用，dry-run 带官方 `--dry-run` 校验；打补丁前把
  `mcp.servers.nblane`（`build_mcp_server_entry` 生成的绝对路径
  nblane-mcp + `NBLANE_ROOT`/`NBLANE_PROFILE` env）合并进 payload——overlay
  是纯 JSON 时单补丁内存合并，非纯 JSON（JSON5 注释等）时先原样透传
  overlay、再发一个只含 MCP 注入的生成 JSON 补丁，靠 config patch 的递归
  合并组合；overlay 缺失则整步跳过）。定时任务不在安装范围内。任一步失败退出码为 1，结束提示
  运行 `nblane openclaw doctor` 体检。
- 定时任务归 OpenClaw 管，直接在 OpenClaw 里建和改。提示词只写任务本身，调用 nblane 的规则在
  nblane 技能里（见 [个人 Agent 写入策略](../guides/agent-write-policy.md)），所以 nblane 改规则
  不需要改定时任务。`automations sync` 只是可选的手动工具：想把
  `profiles/<profile>/assistant/automations.yaml` 当成定时任务的声明来维护时才用。它对账声明
  与 Gateway 实际任务（模板见 `profiles/template/assistant/`）：默认
  dry-run，只打印对账计划与将执行的命令，退出码在存在新增/更新漂移时为 1；
  `--apply` 执行 add/edit；声明中已移除的 `nblane:` 任务默认只提示，
  `--apply --prune` 才删除（`--prune` 不带 `--apply` 时 stderr 明确提醒
  其不生效，不会静默）；非 `nblane:` 前缀的任务（如
  `personal-assistant:*`）永不触碰。声明中的 `${VAR}` 从本机 `.env` /
  环境注入，未设置即报错。**纳管既有任务（adopt）**：外来 key 的条目设置
  `adopt: true` 才被 loader 接受（否则报错），被 adopt 的 key 在声明期间
  与 `nblane:` key 完全同权（add/update/keep）；声明移除后默认回到
  `skip_foreign`，调用方显式传入 `adopted_keys` 时按 `prune_candidate`
  处理（同样需 `--prune` 才删除）。
- `notify` 是 §3.4 的反向推送 MVP：经 OpenClaw 入站 webhook
  （`NBLANE_OPENCLAW_HOOK_URL`，默认 `http://127.0.0.1:18789/hooks/agent`）
  把消息推往微信通道；token 仅从 `.env` / 环境的
  `NBLANE_OPENCLAW_HOOK_TOKEN` 读取（与 `cron.webhookToken` 一致），
  未设置时报错退出码 1，成功 0；`--dry-run` 只打印 URL 与 payload 不发送。

设计细节见
[OpenClaw × nblane 深度融合总体方案](../architecture/openclaw-deep-integration.md)
§5。

`profiles/template/assistant/openclaw.overlay.json5` 是 overlay 模板
（纯 JSON，即合法 JSON5，保证 install 的单补丁合并路径可用，因此字段说明
放在这里而非文件注释）：`agents.defaults.model.primary/fallbacks`、
`agents.defaults.utilityModel`、`agents.defaults.imageModel`
（模型路由：主对话/工具调用/视觉三路，均带 fallbacks）、
`agents.defaults.heartbeat`（心跳骨架，`to` 为 `${WEIXIN_OWNER_ID}` 占位符）、
`memory.search.extraPaths`（含语料目录
`~/.openclaw/workspace/memory/nblane`）、
`channels.openclaw-weixin.replyProgressMessages`。模板**不含**
`mcp.servers`（install 自动注入）与任何密钥。
