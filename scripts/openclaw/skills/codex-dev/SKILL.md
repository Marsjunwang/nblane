---
name: codex-dev
description: 把编程、修复、重构或代码分析任务委派给本机 Codex CLI。仅当用户明确要求“用 codex”或“让 codex 做”时使用；没有指定执行者时不要主动调用。
metadata:
  openclaw:
    os: [linux]
    requires:
      bins: [bash, python3, git, codex]
---

# codex-dev：委派给 Codex CLI

仅在用户明确指定 codex 时执行。使用共用入口 `{baseDir}/../bin/dev-delegate.sh`；
完整运行规则见 [共用委派说明](../bin/delegation.md)，首次执行前阅读。

## 启动与追问

先告知将委派的任务。通过文件写入工具把完整任务保存为 UTF-8 prompt 文件，写清目标、
允许修改的范围和验收方式；禁止覆盖或撤销无关修改。不要把任务原文拼进 shell 命令，
也不要用拼接的 `echo` 或未引用的 heredoc 创建 prompt。

以下命令中的工作目录、文件路径和会话 ID 是示意参数，替换时使用安全的 shell 引用；
优先通过执行工具的 argv 接口传递动态参数。

```bash
"{baseDir}/../bin/dev-delegate.sh" start codex /absolute/workdir /absolute/prompt.txt
```

wrapper 自行后台运行，返回 JSON，其中 `task_dir` 是后续操作的唯一入口。
不需要额外 `nohup`、`&`、`timeout` 或 stdin 重定向。启动成功后再报告已委派。

```bash
"{baseDir}/../bin/dev-delegate.sh" poll /absolute/task_dir
"{baseDir}/../bin/dev-delegate.sh" cancel /absolute/task_dir
```

约每 20–30 秒检查状态及日志，有实质进展时简短汇报。没有日志变化不代表卡死。
完成后检查产物、变更范围与验证证据，再报告结果和实际 `session_id`。
不要把 `SUCCEEDED` 或文件存在本身当成任务验收通过。

追问时，把新任务写到另一个 prompt 文件，用上次状态中的实际 `cwd` 和 `session_id`：

```bash
"{baseDir}/../bin/dev-delegate.sh" start codex /previous/cwd /absolute/followup.txt SESSION_ID
```

恢复时保持原工作目录；若上次执行已留下修改，先检查后再按共用说明使用 `--allow-dirty`。
不要猜测 ID，不要使用“最近一次会话”代替明确 ID。

## Codex 约束

wrapper 使用 `codex exec --sandbox workspace-write --json`，任务从 stdin 读取；
恢复使用 `exec ... resume --json`，同样显式设置 workspace-write。
会话 ID 从 `thread.started.thread_id` 获取。

沙箱的实际可写范围还受配置及受保护路径影响，不应保证“只能写工作目录和 /tmp”。
遇到 bwrap 或沙箱故障，检查 `stderr.log` 的具体错误与本机环境；不要自动修改 setuid、
关闭沙箱或提升系统权限。`--skip-git-repo-check` 仅用于明确允许的非 Git 目录，
不能修复项目信任或沙箱错误。
