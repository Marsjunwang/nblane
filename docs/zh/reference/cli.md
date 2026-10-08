---
status: active
owner: engineering
last_verified: 2026-10-08
source_of_truth: true
---

# CLI 参考

安装后入口为 `nblane <command> ...`。子命令以 `src/nblane/cli.py` 为准，`nblane <command> --help` 看完整参数。

## 档案

```bash
nblane init <profile> [--schema NAME]   # 选领域技能树，默认 robotics-engineer
nblane context <profile> [--chat|--review|--write|--plan] [--no-kanban]
nblane status [profile]
nblane log <profile> "finished first manipulation demo"
nblane health [profile]                 # 档案体检（SPA 证据页「待补强」的同一份报告）
nblane sync-cursor <profile>            # 写 .cursor/rules/nblane-context.mdc
```

`init --schema` 可选内置的 `robotics-engineer`、`autonomous-driving`，或数据目录 `schemas/` 里管理员加的领域；名字不存在时报错并列出可选项，见 [技能树 Schema](skill-tree-schema.md#选择与更换领域)。

`context` 输出 Agent system prompt，格式见 [SKILL.md 格式](skill-md-format.md)。

## 技能树与证据

```bash
nblane validate [profile]
nblane sync <profile> --check           # 有漂移退出码 1
nblane sync <profile> --write

nblane evidence <profile> <node_id> add --type project --title "Demo"
nblane evidence <profile> pool add --type project --title "Shared milestone"
nblane evidence <profile> link <node_id> <evidence_id>
nblane evidence <profile> unlink <node_id> <evidence_id>
nblane evidence <profile> pool remove <evidence_id> [--prune-refs]
nblane evidence <profile> pool deprecate <evidence_id> [--replaced-by ID]

nblane crystallize <profile> <project> [--file PATH|--stdin]   # 写方法草稿到 methods/
```

写入顺序是证据池 → 技能树 → validate → sync。字段见 [证据参考](evidence.md) 和 [技能树 Schema](skill-tree-schema.md)。

## 导入（LLM）

```bash
nblane ingest-resume <profile> --file resume.txt [--dry-run] [--allow-status-change] [--no-bump-locked]
nblane ingest-resume <profile> --stdin --dry-run
nblane ingest-kanban <profile> [--dry-run] [--allow-status-change]
```

流程是解析 → 合并 → 预览 → 应用。需要配置 `LLM_API_KEY`，见 [本机安装](../guides/setup.md#ai-配置)。

## 公开站

```bash
nblane public init <profile>
nblane public validate <profile> [--include-drafts]
nblane public build <profile> [--out dist/public/<profile>] [--base-url https://www.example.com] [--include-drafts]
nblane public resume <profile> [--out DIR] [--target ROLE]
nblane public blog list|new|media|publish <profile> ...
nblane public library tree|reconcile|trash|restore|purge <profile> ...
nblane public draft-blog <profile> (--from-evidence ID | --from-kanban-done)
nblane public draft-resume <profile> --target ROLE
nblane public draft-project-update <profile> --project ID
nblane public suggest-groups <profile> --dry-run
nblane public group <profile> --id ID --title T --evidence ID [--evidence ID ...]
nblane public hydrate <profile> --dry-run|--write-drafts
```

说明见 [公开站点](../guides/public-site.md)。

## 研究台

```bash
nblane research connector sync <profile> --all [--provider arxiv|semantic_scholar|github|...] [--dry-run]
nblane research connector sync <profile> --id <connector_id>
```

## Codex 与外部 Agent

```bash
nblane codex status [--profile <profile>]
nblane codex install [--print-command] [--upgrade]
nblane codex local run <agent_task_id> --profile <profile>
nblane codex cloud submit <agent_task_id> --profile <profile>
nblane codex cloud refresh <agent_task_id> --profile <profile> [--diff]

nblane agent handoff <agent_task_id> --target codex|opencode [--profile <profile>]
nblane sync-agent-harness --target codex|opencode [--out PATH]
```

见 [Agent Harness](agent-harness.md)。`sync-agent-harness --target openclaw` 仍能打印 MCP 片段，但助手不走 MCP，不要用它接 OpenClaw。

## MCP

```bash
nblane-mcp            # stdio，给本机 Cursor / Claude Code
```

见 [MCP 参考](mcp.md)。

## OpenClaw

```bash
nblane openclaw doctor [--profile <profile>]
nblane openclaw sync [--profile <profile>] [--check]
nblane openclaw install [--profile <profile>] [--dry-run|--apply]
nblane openclaw automations sync <profile> [--apply] [--prune]   # 可选的手动工具
nblane notify <text> [--dry-run]
```

- `doctor`：只读体检。OpenClaw 版本、Node 版本（>=24.16 且 <25，或 >=26.1）、systemd linger、`127.0.0.1:18789` 监听、openclaw-weixin 插件已启用、存在备份调度。任一 error 级失败退出码 1。不调用 `openclaw doctor`（它会重启网关）。
- `sync`：渲染只读档案语料到 `~/.openclaw/workspace/memory/nblane/`，把 `scripts/openclaw/skills/` 同步到工作区 `skills/`。会删除纳管目录里仓库已不存在的文件，其他技能树不碰；`skills/bin/nblane_api` 是生成物，不算多余。`--check` 不写文件，有漂移退出码 1。缺省 `--profile` 时用唯一存在的档案。
- `install`：一键幂等安装，默认 dry-run。三步：技能与语料；安装 `weixin-task-bridge` 插件；profile 有 `assistant/openclaw.overlay.json5` 时经 `openclaw config patch --stdin` 应用（`${VAR}` 从环境替换，未设置即报错）。不注册 MCP，不碰定时任务。
- `automations sync`：可选手动工具。定时任务归 OpenClaw 管，平时直接在 OpenClaw 里建和改。只有想把 `profiles/<profile>/assistant/automations.yaml` 当声明维护时才用：默认 dry-run 打印计划和命令，有新增或更新时退出码 1；`--apply` 执行 add / edit；`--apply --prune` 才删除声明里已移除的任务。只处理 `nblane:` 前缀的任务（或声明里标了 `adopt: true` 的），其他任务不碰。
- `notify`：经 OpenClaw 入站 webhook 推消息到微信。地址 `NBLANE_OPENCLAW_HOOK_URL`（默认 `http://127.0.0.1:18789/hooks/agent`），token 只读 `NBLANE_OPENCLAW_HOOK_TOKEN`。`--dry-run` 只打印 URL 和 payload。

运维背景见 [OpenClaw 运维](../guides/openclaw-ops.md)。

## 备份与账号

```bash
nblane backup status
nblane backup run [--target <id>]        # 任一目标失败退出码 1
nblane auth hash-password [password]     # 省略时交互输入；日常加人改密在设置页做
```

备份目标在「设置 → 助手与备份」配置，见 [助手 · 数据备份](../guides/assistant.md#数据备份)。
