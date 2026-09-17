# 共用委派运行规则

入口：`dev-delegate.sh`（与本文件同目录），实现为 `dev_delegate.py`。
需要 Linux、Python 3、Git、Bash 和对应 CLI；不调用 shell 解析任务内容，不依赖 timeout 程序。

## 工作区

- 启动前检查 `git status --short`，说明任务范围及允许修改的文件。
- 默认拒绝已有修改（包括未跟踪文件）。若现有修改是任务上下文，确认任务授权范围后加
  `--allow-dirty`，保留现有修改，禁止自动 stash/reset/clean。
- 高风险或需隔离的任务加 `--worktree`：从干净源仓库 HEAD 创建 detached worktree，
  路径记录在状态 `cwd` 中。脏源仓库不自动复制修改，也不隐式忽略修改。
  结果保留供审阅，不自动合并或删除 worktree；恢复会话使用记录的 cwd，不再加该选项。
- 两种 CLI 共用按 Git 工作树根目录定位的 advisory lock，涵盖仓库子目录及符号链接别名。
  锁贯穿任务执行和退出检查。它不能阻止编辑器或未使用 wrapper 的进程写入。
- 非 Git 目录必须显式加 `--allow-non-git`；该模式只有目录锁，没有 Git 变更快照或 worktree。
- 普通目录和 worktree 都不是对所有工具生效的安全隔离。Kimi 的权限行为仍由其 CLI 决定。

## 状态、日志与取消

每个任务使用 `~/.local/state/dev-delegate/` 下的唯一私有目录（0700，文件默认 0600）：

- `prompt.txt`：任务输入副本，启动后修改原文件不会影响任务。
- `events.jsonl`：stdout 结构化事件；`stderr.log`：CLI 诊断；`worker.log`：wrapper 诊断。
- `status.json`：状态、工作目录、PID、会话 ID、退出码及时间，原子更新。
- `before.json` / `after.json`：Git 状态和相对 HEAD 的 tracked diff；不是文件备份，
  不包含未跟踪文件内容，也不能检测所有对原本已脏文件的再次修改，必要时直接核对文件。

`poll TASK_DIR` 返回 JSON。状态可能是 QUEUED、STARTING、RUNNING、SUCCEEDED、FAILED、
TIMEOUT、CANCELLED、EXITED_UNKNOWN。worker 意外消失时不把进程退出误报为成功。
`cancel TASK_DIR` 写入取消请求；继续 poll 直到终态，不直接 kill 返回的 PID。

CLI 运行默认最多 600 秒，超时或取消先向 CLI 进程组发送 TERM，最多等待 15 秒再 KILL。
可用 `--timeout SECONDS --grace SECONDS` 调整。超时记录 exit_code=124，取消=130；
其他失败保留 CLI 退出码，信号退出转换为 128+signal。`child_returncode` 保留 Python 原始返回值。
状态文件明确区分超时与 CLI 自己返回 124。子进程另建 session/逃离进程组不在清理保证内。

不要因短暂无日志而杀任务。worker 被 SIGKILL、机器重启等会导致收尾无法执行；
EXITED_UNKNOWN 时检查 child_pid 和实际进程，不直接重试或假定已全部停止。
任务目录包含 prompt 和日志，不自动删除未审阅结果，不向无关人员发送。

## 收尾

核对前后变更、允许修改的范围、产物内容及测试命令/结果。有可靠测试证据时不必重复跑；
缺乏证据时补足与任务风险相称的检查。CLI 返回 0 只表示程序正常退出。
发现无关改动时先报告，不自动回滚可能属于用户的修改。
结构化事件没有会话 ID 时如实报告；保留日志便于定位，禁止猜测。

OpenClaw 的 requires 检查只表示 PATH 中存在依赖，不表示认证或版本兼容性已经验证。
修改技能后，新会话或技能快照刷新才会使用新指令；无需为此自动重启 Gateway。
