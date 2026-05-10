---
status: active
owner: engineering
last_verified: 2026-05-08
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

规划中的 harness 命令：

```bash
nblane sync-agent-harness --target codex
nblane sync-agent-harness --target opencode
nblane agent create --role researcher --title "..."
nblane agent handoff <agent_task_id> --target opencode
nblane agent status
```

当前 MCP 说明见 [MCP 参考](mcp.md)，规划见 [Agent Harness](agent-harness.md)。
