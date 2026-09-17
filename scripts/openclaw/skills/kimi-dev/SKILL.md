---
name: kimi-dev
description: 把编程、修复、重构或代码分析任务委派给本机 Kimi Code CLI。仅当用户明确要求“用 kimi”或“让 kimi 做”时使用；没有指定执行者时不要主动调用。
metadata:
  openclaw:
    os: [linux]
    requires:
      bins: [bash, python3, git, kimi]
---

# kimi-dev：委派给 Kimi Code CLI

仅在用户明确指定 kimi 时执行。使用共用入口 `{baseDir}/../bin/dev-delegate.sh`；
完整运行规则见 [共用委派说明](../bin/delegation.md)，首次执行前阅读。

## 启动与追问

先告知将委派的任务。通过文件写入工具把完整任务保存为 UTF-8 prompt 文件，写清目标、
允许修改的范围和验收方式；禁止覆盖或撤销无关修改。不要把任务原文拼进 shell 命令，
也不要用拼接的 `echo` 或未引用的 heredoc 创建 prompt。

以下命令中的工作目录、文件路径和会话 ID 是示意参数，替换时使用安全的 shell 引用；
优先通过执行工具的 argv 接口传递动态参数。

```bash
"{baseDir}/../bin/dev-delegate.sh" start kimi /absolute/workdir /absolute/prompt.txt
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
"{baseDir}/../bin/dev-delegate.sh" start kimi /previous/cwd /absolute/followup.txt SESSION_ID
```

恢复时保持原工作目录；若上次执行已留下修改，先检查后再按共用说明使用 `--allow-dirty`。
不要猜测 ID，不要使用“最近一次会话”代替明确 ID。

## Kimi 约束

wrapper 使用 `--output-format stream-json --prompt`，任务作为单个 argv 参数传递；
恢复使用 `--session`，不使用过时的 `-r`。不额外添加 `--auto` 或 `-y`。
`~/.local/bin/kimi` 是本机 CLI 的稳定符号链接，目标为 `~/.kimi-code/bin/kimi`；
Gateway 的 PATH 必须包含该入口所在目录，wrapper 启动时也会检查 CLI 是否存在。

wrapper 从结构化事件中读取明确的 `session_id` / `sessionId` 字段。
若当前版本未输出这些字段，状态保留空 ID：检查原始事件或 `kimi session list --help`
后通过官方会话列表确认，不从自然语言尾注猜测、不自动拼接 `session_` 前缀。
认证错误时报告 stderr 中的相关错误，并提示用户通过 `kimi login` 续期。
