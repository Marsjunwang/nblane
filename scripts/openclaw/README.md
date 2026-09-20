# scripts/openclaw — OpenClaw 侧资源与安装脚本

本目录存放需要部署到 OpenClaw workspace（`~/.openclaw/workspace/`）的源码，
随 nblane 仓库版本管理；OpenClaw 侧的运行副本**不会**与仓库自动同步。

## 目录结构

```text
scripts/openclaw/
├── skills/                    # 同步到 ~/.openclaw/workspace/skills/
│   ├── codex-dev/SKILL.md     # Codex 委派 Skill
│   ├── kimi-dev/SKILL.md      # Kimi 委派 Skill
│   └── bin/                   # 两个 Skill 共用的 wrapper（dev-delegate.sh、
│                              #   dev_delegate.py、delegation.md、tests/）
├── plugins/
│   └── weixin-task-bridge/    # 微信任务桥插件源码（package.json、
│                              #   openclaw.plugin.json、dist/index.js），
│                              #   提供 /taskctl 命令与 [后台任务] 进度镜像
└── install.sh                 # 幂等安装脚本（见下）
```

## install.sh

在目标机器上执行一次即可完成两件事：

1. `rsync` 把 `skills/` 同步到 `~/.openclaw/workspace/skills/`（保持
   `codex-dev/`、`kimi-dev/`、`bin/` 结构，可用 `OPENCLAW_WORKSPACE`
   环境变量覆盖目标 workspace）；
2. `openclaw plugins install <repo>/plugins/weixin-task-bridge --force
   --accept-capabilities` 安装/覆盖安装微信任务桥插件。

脚本是幂等的，可重复运行。用法：

```bash
scripts/openclaw/install.sh            # 实际安装
scripts/openclaw/install.sh --dry-run  # 只打印将执行的命令
```

完成后按脚本末尾提示验证：

```bash
openclaw plugins inspect weixin-task-bridge --runtime --json
```

## 安全说明

- 本脚本**必须在目标主机上人工运行**，不属于任何自动化流程；执行前请先用
  `--dry-run` 确认动作。
- 仓库内的插件源码不含 Owner ID、密钥或任何凭据；`ownerId` 等配置项在
  安装后写入 `openclaw.json`（见 `docs/zh/guides/openclaw-integration.md`
  「Weixin Task Bridge 插件」一节），不要提交真实值到仓库。
- 详细配置与验收步骤见 `docs/zh/guides/openclaw-integration.md`。
