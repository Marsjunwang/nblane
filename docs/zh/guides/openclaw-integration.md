---
status: active
owner: 王军
last_verified: 2026-09-17
source_of_truth: src/nblane/mcp_server.py、src/nblane/core/mcp_client_config.py、src/nblane/core/agent_tasks.py
---

# OpenClaw 接入指南

本文说明如何把 OpenClaw(常驻 AI agent gateway)接入 nblane,让外部
agent 在你的个人成长系统里"干活",同时保证上下文与审批闭环的主权留在
nblane。

## 定位:各层干什么

| 层 | 谁担当 | 说明 |
| --- | --- | --- |
| 模型(大脑) | 千问 API / ChatGPT / Kimi / Claude | 可替换,按成本与质量路由 |
| Agent runtime(手+嘴) | OpenClaw、Codex CLI、OpenCode | 可替换的执行与消息渠道层 |
| 上下文+记忆+闭环(神经) | **nblane** | `profiles/` 文件是唯一事实源,不自建 coding agent |

OpenClaw 装上来的第一天并不"懂你":它不知道你的技能树、primary goal、
未关联证据。接入的本质是让 OpenClaw 通过 MCP 读取 nblane 的上下文,
并把产出送回 nblane 的审批队列——换任何 runtime,记忆和闭环都不丢。

## 模型与订阅怎么选(2026-09 核实)

- **ChatGPT Plus**:可用。OpenClaw 支持 OpenAI 的 Codex 订阅 OAuth
  登录(Plus $20/月封顶),适合个人交互式使用;长期在线 gateway 官方
  建议 API key 更稳定。
- **千问(DashScope)**:可用。OpenClaw 支持任意 OpenAI 兼容端点,
  直接复用 nblane `.env` 里的 `LLM_BASE_URL` / `LLM_API_KEY` 配置思路即可。
- **Kimi**:充 Kimi Pro 网页会员**不能**给 agent 用。要用 Kimi,需
  Moonshot 开放平台 API key(按量)或 Kimi Coding 编程套餐(独立订阅,
  key 与端点均不通用)。
- 注意:Claude Pro/Max 订阅 OAuth 接第三方工具违反 Anthropic 服务条款,
  请勿使用。

## 实际部署:模型路由(2026-09-17 实测)

服务器(VM-0-5-ubuntu)上微信机器人当前的模型路由:**GPT 中转站为默认、
千问 flash 兜底**,两条路径均已实测可用:

```bash
openclaw config set agents.defaults.model.primary "rightcode/gpt-6-astra"
openclaw config set agents.defaults.model.fallbacks '["qwen/qwen3.8-flash"]'
systemctl --user restart openclaw-gateway    # 已有会话里 /new 生效
```

- `rightcode/gpt-6-astra`:rightcode 中转站,OpenAI 兼容接口,普通 provider。
- `qwen/qwen3.8-flash`:百炼 DashScope,OpenAI 兼容接口。
- 会话级临时切换(微信里直接发):`/model rightcode/gpt-6-astra`、
  `/model qwen/qwen3.5-plus`、`/model default`;`/status` 查看当前模型。

### API key 配置方法

- **百炼(qwen)**:`openclaw models auth login --provider qwen` 交互录入;
  `openclaw models auth list --provider qwen` 查看已有 profile。
  provider 端点 `https://dashscope.aliyuncs.com/compatible-mode/v1`,
  `api: "openai-completions"`。
- **rightcode 中转**:静态 API key,与 codex CLI 共用同一把
  (`~/.codex/auth.json` 的 `OPENAI_API_KEY`):

  ```bash
  openclaw config set models.providers.rightcode '{
    "baseUrl": "https://rightapi.ai/codex/v1",
    "api": "openai-completions",
    "apiKey": "<取自 ~/.codex/auth.json 的 OPENAI_API_KEY>",
    "models": [{"id":"gpt-6-astra","name":"gpt-6-astra","api":"openai-completions",
                "contextWindow":200000,"maxTokens":128000}]
  }'
  ```

  注意:baseUrl 必须带渠道前缀 `/codex/v1`(旧版 key 不认裸 `/v1`);
  自定义 provider 必须显式声明 `models` 数组,否则配置校验不过。

### 踩坑:中转站模型不能走 Codex harness

曾尝试让 OpenClaw 通过 Codex app-server harness 跑中转站模型
(模型引用 `openai/gpt-6-astra`),症状是微信/Dashboard 全部无回复、报
`codex app-server execution budget timed out`,但 `/codex status` 正常、
`codex exec` 也正常,极具迷惑性。根因链:

1. codex harness **只接受 `openai/*` 模型引用**(自定义 provider 报
   `provider is not one of: codex, openai`);
2. `openai/*` 会强制使用 codex **内置的 openai 提供商**(线程 rollout 文件
   `~/.codex/sessions/**/rollout-*.jsonl` 的 `session_meta.model_provider`
   可实锤),无视 `~/.codex/config.toml` 的 `model_provider`;
3. 新版 codex 内置提供商走 **WebSocket 直连 `api.openai.com`**,国内服务器
   无代理必挂;且本机 codex 登录是 rightcode 的 key,真 OpenAI 也不认。

弯路(不要再试):在 `config.toml` 重定义 `[model_providers.openai]` 会被
codex 拒绝(`reserved built-in provider IDs`,还会搞挂系统 codex CLI);
`OPENAI_BASE_URL` 只影响 HTTPS、不影响 WebSocket 硬编码域名。

**结论:中转站场景一律用普通 provider(上面的 rightcode 配置),
不要用 `openai/*` 引用。** codex harness 仅适合真实 ChatGPT 订阅 +
可直连/可代理 api.openai.com 的环境。

### 踩坑:root 残留旧实例抢端口

若 `openclaw gateway status` 报 `protocol mismatch` / `token mismatch` /
服务 exit 78:检查是否有 root 下的旧版 OpenClaw 占着 18789
(`ps aux | grep -i openclaw`)。本机曾残留 pnpm 装的 2026.3.8,由
**root 的 systemd 用户服务**守护(系统级 `systemctl` 看不到,需
`sudo env XDG_RUNTIME_DIR=/run/user/0 ... systemctl --user stop/disable`),
已于 2026-09-17 清理完毕,旧配置归档 `/root/.openclaw.bak-20260917`。

更多运维细节(验证三板斧、日志位置、杂项坑)见服务器上的
`~/.openclaw/config-notes.md`。

## 通过 OpenClaw 调本机 codex 做开发(2026-09-17 实测可行)

中转站场景下 codex harness 不可用(见上文坑),但可以让 OpenClaw 的 agent
**通过 exec 工具直接调用本机 codex CLI** 完成编码任务——codex 自带读写文件/
跑命令能力,OpenClaw 只管派活和回收结果:

```text
微信里发:用 codex 在 nblane 仓库写一个 xxx 脚本
agent 实际执行:cd /home/ubuntu/nblane && codex exec --sandbox workspace-write "<任务>" </dev/null
```

实测:agent 调 codex 创建文件并成功读回内容。注意点:

- 调用时带 `</dev/null`,避免 codex 从 stdin 阻塞等待输入;
- 工作目录要在 codex 信任的项目内(`~/nblane`、`~/.openclaw/workspace`
  已在 `~/.codex/config.toml` 的 `[projects.*]` 里配为 trusted),其他目录
  需加 `--skip-git-repo-check`;
- 长任务建议让 agent 用 `timeout 300 codex exec ...` 包住,防止挂死。

已固化为两个 workspace skill(用户说"用 codex/kimi 做 xx"时 agent 自动
加载并按规范调用):`~/.openclaw/workspace/skills/codex-dev/SKILL.md` 和
`.../kimi-dev/SKILL.md`(kimi 用 `~/.kimi-code/bin/kimi -p`,勿加 `--auto`,
与 `-p` 互斥;追问用 `kimi -r session_<id> -p`)。均已实测端到端跑通。

**前置修复(本机已做)**:codex 沙箱依赖 bubblewrap,腾讯云 Ubuntu 上
bwrap 起报 `loopback: Failed RTM_NEWADDR: Operation not permitted`(系统
AppArmor 限制非特权用户命名空间)。修复:

```bash
sudo apt-get install -y bubblewrap
sudo chmod u+s /usr/bin/bwrap    # setuid 是 bwrap 的设计运行模式
```

## 接入步骤

1. 安装并初始化 OpenClaw(参考其官方文档,`openclaw onboard`)。
2. 生成 nblane 的 MCP 配置片段:

   ```bash
   nblane sync-agent-harness --target openclaw --profile 王军
   # 或写入文件:--out ~/.openclaw/nblane-mcp.json
   ```

   输出是一段可合并进 `~/.openclaw/openclaw.json` 的 `mcp.servers` 配置
   (command 自动解析本机 `nblane-mcp`,env 带 `NBLANE_ROOT` 与
   `NBLANE_PROFILE`)。也可以用 `openclaw mcp add` 交互式添加。
3. 验证:

   ```bash
   openclaw mcp list            # 能看到 nblane
   openclaw mcp tools nblane    # 能列出 submit_agent_task_candidate 等工具
   ```

4. 在 OpenClaw 里让 agent 先读 `profile://context`(完整 system prompt)
   或 `profile://summary`(摘要),再开始工作。

## 闭环工作流(重要)

OpenClaw 是执行层,**产出必须进审批队列,由人处置**:

1. agent 读 `agent://tasks` / `agent://task/{task_id}` 领取派单;
2. 执行(调研、写草稿、跑代码……);
3. 完成时调用 `submit_agent_task_candidate`(summary / changed_paths /
   warnings / result_payload);失败或阻塞调 `update_agent_task_status`;
4. 人在 Web UI 的 **Agent Activity** 页审批候选写回;看板任务完成后由人
   触发 crystallize,沉淀为证据。

安全边界(nblane-mcp 的设计保证):MCP 走 stdio 本地进程;工具只写
growth log、inline evidence、interaction 记录、方法草稿与审批队列,
**不能**直接改技能树状态、不能发布公开内容。OpenClaw 本身权限很大,
请只在本地运行,不要把 gateway 暴露到公网,`NBLANE_ROOT` 指向你的
nblane 仓库即可。

## 相关文档

- Agent Activity 审批页:`docs/zh/guides/agent-activity.md`
- 看板:`docs/zh/guides/kanban.md`
- MCP server 实现:`src/nblane/mcp_server.py`(资源与工具清单以源码为准)
