# MCP 服务器（Cursor 等客户端）

nblane 提供 **只读** MCP 服务：`python -m nblane.mcp_server`，通过 **stdio** 与 Cursor 通信，暴露 `profile://…` 等资源，供 Agent 拉取当前 profile 的上下文。

## 当前实现范围（给集成方 / 其他 Agent）

### 已提供的能力

| 类别 | 说明 |
|------|------|
| 传输 | **stdio**（由 Cursor 等客户端拉起子进程） |
| MCP 原语 | 仅 **Resources（只读）**；**未**注册 Tools、Prompts |
| 数据方向 | 全部 **读**：从本机 `profiles/` 等文件生成文本；**不**修改仓库 |

### 已实现的具体功能（与 CLI / Web 的对应关系）

| 能力 | MCP | 说明 |
|------|-----|------|
| 技能树摘要 + agent-profile 焦点/偏好 + Doing 看板 | `profile://summary` | 近似 `nblane status` 的摘要信息 + YAML 与看板解析，**不是** `status` 的逐行打印格式 |
| 完整 system prompt | `profile://context` | 对齐 **`nblane context`**（含 kanban；模式由 `NBLANE_CONTEXT_MODE` 控制） |
| 看板原文 | `profile://kanban` | 直接读 `kanban.md` |
| **Gap 分析** | `profile://gap/{task}` | 对齐 **`nblane gap <profile> "<task>"`** 的**自然语言任务**路径：规则匹配开启；可选 LLM 路由由 `NBLANE_GAP_USE_LLM` 控制（见下） |

### Gap：能不能调用？与 CLI 的差异

- **可以。** 通过资源 **`profile://gap/{task}`** 读取一次，即对该 **task** 跑一遍与 CLI 相同的 `gap.analyze`（输出为 `format_text` 的纯文本）。
- **与 CLI 的差异（MCP 当前未暴露的参数）：**
  - **没有** `nblane gap ... --node <id>`：MCP 侧 **固定为自然语言任务**，不能单独指定 schema 节点 id。需要 `--node` 时请用 **CLI**。
  - **没有** `--no-rule`：MCP 侧 **固定** `use_rule_match=True`。
  - Gap 的 LLM 路由在 MCP 里由环境变量 **`NBLANE_GAP_USE_LLM`** 开关；为免污染本机学习词表，MCP 调用时 **`persist_router_keywords=False`**（不向 `learned_keywords` 持久化），与 CLI 默认持久化行为不同。
- **仍需要：** 本机已有 `skill-tree.yaml`、schema 可加载；任务非空。错误时响应正文以 `ERROR [profile://gap]: ...` 开头。

### 明确未实现（勿在文档中误传）

- 写入：`SKILL.md`、`skill-tree.yaml`、`evidence-pool.yaml`、`kanban.md` 等 **均不能** 通过本 MCP 修改。
- 无 **`nblane ingest-resume` / `ingest-kanban`**、无 **`nblane evidence`**、无 **`nblane team`**、无 **`nblane sync` / `validate`** 的 MCP 封装。
- `nblane context --no-kanban`：MCP 的 `profile://context` **固定带 kanban**；若不要看板请用 CLI 或本地文件。

---

## 接口说明（给其他 Agent：如何调用每个 URI）

约定：客户端使用 MCP 的 **ReadResource**，URI 如下。除 `gap` 外均为**固定 URI**，无路径参数。

| URI | 参数 | 返回 | 说明 |
|-----|------|------|------|
| `profile://summary` | 无 | Markdown 文本 | 依赖当前解析到的 profile（见环境变量）。 |
| `profile://kanban` | 无 | Markdown 文本 | 无文件时返回一行英文提示。 |
| `profile://context` | 无 | 纯文本 | 长度可能较大；模式由 `NBLANE_CONTEXT_MODE` 决定。 |
| `profile://gap/{task}` | **路径段 `task`** | 纯文本 | **必须**把自然语言任务放进 URI 的最后一级；**先做 URL 编码**（如空格→`%20`，中文通常 UTF-8 百分号编码）。服务端会对该段做 `urllib.parse.unquote` 后再分析。 |

**Profile 如何选定（所有资源共用）**

1. 若设置 `NBLANE_PROFILE` 或 `NBLANE_MCP_PROFILE`，且对应目录存在 → 使用该 profile。  
2. 否则若 `profiles/` 下**恰好一个**非 template profile → 自动用它。  
3. 否则 → 读资源失败，正文为 `ERROR [profile://…]: …`（提示需设置 `NBLANE_PROFILE`）。

**Gap 资源示例（编码）**

- 任务原文：`OpenVLA robot control`  
- URI：`profile://gap/OpenVLA%20robot%20control`  
- 任务原文含中文时：对每个字节做百分号编码，或由 MCP 客户端按 RFC 3986 处理路径段。

---

## 前置条件

在用于启动 MCP 的 Python 环境里安装本仓库，例如：

```bash
cd /home/narwal/workspace/nblane
pip install -e .
```

（若你的克隆不在此路径，请改成自己的目录。）

这样会安装 `mcp` 依赖并注册 `nblane` 包。

若 `profiles/` 下 **不止一个** profile，请设置 **`NBLANE_PROFILE`**（见下文）。

## 在 Cursor 里怎么用、能帮你什么

**它是什么：** MCP 把 nblane 里的 **profile 数据**暴露成一组 **只读资源**（URI）。Cursor 连上后，**Agent 可以按需读取**这些资源，相当于在对话里「附带一份你的 SKILL / 看板 / 技能树摘要」，而不必每次手动粘贴 `nblane context` 的输出。

**你怎么做（操作顺序）：**

1. 按下文「用法 A 或 B」配好 MCP，重启 Cursor 或刷新 MCP 列表。
2. 打开 **Cursor → Settings → MCP**，确认 **nblane** 显示为已连接（无红色错误）。
3. 打开 **MCP Inspector**（或设置里与 MCP 相关的面板），应能看到 `profile://summary`、`profile://context` 等；点一次 **Read** 做自检。
4. 在 **Agent / Chat** 里开发时：
   - **直接说明意图**：例如「先通过 MCP 读 `profile://context`，再帮我改这段代码」「结合 `profile://summary` 看我当前技能重点，给重构建议」。
   - Cursor 是否**自动**把资源塞进上下文，取决于当前 Agent 与规则；**最稳妥**的方式是在任务开头显式让模型去 **fetch 对应 MCP resource**（不同版本界面文案可能略有差异，意思相同）。

**对日常开发的帮助（典型场景）：**

| 场景 | 可读的 URI | 作用 |
|------|------------|------|
| 新开对话、不想重复自我介绍 | `profile://context` | 对齐「你是谁、证据、看板」的长期 system prompt 级上下文 |
| 快速扫一眼进度与焦点 | `profile://summary` | 技能树 lit、agent-profile 里的 focus、Doing 看板 |
| 对齐本周事项 | `profile://kanban` | 原始 `kanban.md` |
| 准备做一件大活（选型 / 攻坚） | `profile://gap/任务描述`（注意 URL 编码） | 与 CLI **`nblane gap <profile> "<task>"`** 的自然语言模式基本一致（见上文与 CLI 的差异） |

**注意：** MCP 这里是 **读路径**，不会替你改仓库文件；改 `SKILL.md`、看板、技能树仍用你平时的编辑方式或 nblane CLI / Web。

## 环境变量

| 变量 | 作用 |
|------|------|
| `NBLANE_PROFILE` 或 `NBLANE_MCP_PROFILE` | 默认 profile 名；存在多个 profile 时**必须**设置。 |
| `NBLANE_ROOT` | 指定仓库根目录（含 `profiles/`）。在任意工作区使用时建议显式设置。 |
| `NBLANE_CONTEXT_MODE` | `chat` · `review` · `write` · `plan`，仅影响 `profile://context`。默认 `chat`。 |
| `NBLANE_GAP_USE_LLM` | 设为 `1` / `true` 时对 gap 启用 LLM 路由（需 API key）。默认关闭。 |

## 用法 A：只在「当前工程就是 nblane 仓库」时启用

仓库内已有 **`.cursor/mcp.json`**，使用：

- `command`: `${workspaceFolder}/.venv/bin/python`
- `cwd`: `${workspaceFolder}`

因此 **`${workspaceFolder}` 必须是 nblane 仓库根目录**（在 Cursor 里直接打开 nblane 项目时成立）。

可按需增加 `env`，例如：

```json
"env": {
  "PYTHONPATH": "src",
  "NBLANE_PROFILE": "你的名字"
}
```

若已 `pip install -e .`，多数情况下可去掉 `PYTHONPATH`。

## 用法 B：在**另一窗口 / 别的项目**里也能连上（同一台电脑）

当 Cursor 当前打开的是**别的目录**时，`${workspaceFolder}` **不是** nblane 路径，仅靠仓库里的 `.cursor/mcp.json` **不会**自动在其他工程生效，除非那个工程自己也配了 MCP。

要在**任意工作区**使用同一套 nblane 数据，请用下面方式之一。

### 1. 用户级 MCP 配置（推荐）

在 **Cursor → Settings → MCP** 里添加服务器，或编辑本机用户级 MCP JSON（路径因系统而异，常见在 `~/.cursor/` 下）。关键是使用 **绝对路径**，指向你的 nblane 克隆与解释器。

本机克隆在 `/home/narwal/workspace/nblane` 时，可直接复制（把 `NBLANE_PROFILE` 改成你的 profile 名）：

```json
{
  "mcpServers": {
    "nblane": {
      "command": "/home/narwal/workspace/nblane/.venv/bin/python",
      "args": ["-m", "nblane.mcp_server"],
      "env": {
        "NBLANE_PROFILE": "你的名字",
        "NBLANE_ROOT": "/home/narwal/workspace/nblane"
      }
    }
  }
}
```

说明：

- **`command`**：装有 `nblane` 的 Python 可执行文件**完整路径**（在该环境中执行过 `pip install -e .`）。
- **`NBLANE_ROOT`**：可选，但**建议**在「工作区不是 nblane 仓库」时写上；必须是包含 `profiles/`、`schemas/` 的**仓库根目录**。
- 若已 `pip install -e .`，一般**不需要**再设 `PYTHONPATH`。
- **`cwd`** 常可省略；未设置时客户端可能用当前工作区目录，数据路径仍以 `NBLANE_ROOT` / 包内解析为准。

这样无论你打开的是前端项目还是别的仓库，只要 Cursor 加载了用户级 MCP，都会启动**同一套** nblane 进程配置（数据仍来自 `NBLANE_ROOT` 下的 `profiles/`）。

### 2. 在其他仓库里单独放 `.cursor/mcp.json`

在**每个**需要用到 nblane MCP 的项目里，复制一份配置，同样使用**绝对路径**的 `command` 和 `NBLANE_ROOT`。维护成本较高，适合少数固定项目。

### 避免重名

若同时启用了「nblane 仓库内的项目级 MCP」和「用户级 nblane」，可能重复注册同名服务。请只保留一处，或把其中一条改名为例如 `nblane-global`。

## 自检

- 在 Cursor 的 MCP / Inspector 中能看到 `profile://summary`、`profile://context` 等资源。
- 读取 `profile://context` 应出现基于 `SKILL.md` 的 system prompt。

## 另见

- 设计：[设计手册与里程碑](design.md) 中 Demo 1 Phase 2（MCP 读路径）
- 命令行对照：`nblane context`、`nblane gap`
