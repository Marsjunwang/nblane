---
status: active
owner: product
last_verified: 2026-10-07
source_of_truth: true
---

# 路线图

本页只写往后方向。已完成的阶段见 [里程碑](../project/milestones.md)，各区现状见 [项目状态](../project/status.md)。

## 往后方向

| 方向 | 要解决的问题 | 前提 |
|------|--------------|------|
| 清理 Streamlit 遗留代码 | `app.py`、`pages/`、`*_component/`、`web_*.py` 仍在仓库里，增加误改和依赖负担 | 先确认 SPA 与 Reader 不再引用其中任何模块 |
| 车间上生产 | 网页终端代码已完成（8504 WS 代理 + nblane 会话认证），生产仍待部署和改 Caddy | 见 [远程车间方案](../dev/phase0.5-remote-terminal.md) |
| 输出层重建 | 证据到简历 bullet、公开站铭文、写作之间缺少一层可复用的断言（Claim 目前封存） | 内容工作台、求职工作台、公开站稳定后再定形状 |
| 初始化链路 | 新用户只能从简历解析出工程类技能树，非工程领域不成立 | 领域 schema 模板库 + AI 按简历定制技能树草案与北极星候选 + 预览确认 |
| 研究台打磨 | 阅读器仍是 8502 iframe；多篇论文综述、研究来源到证据的连接后置 | 见 [论文阅读](paper_reading.md) |
| 助手能力 | 助手通过 HTTP 能做的日常操作还可扩充（按需加端点并在策略表登记等级） | 每个新写端点都要在 `core/agent_policy.py` 显式登记，未登记默认需确认 |

## 暂不做

- 迁移到 SQLite / Postgres 主存储。
- 团队功能。nblane 只服务单人加自己的 Agent。
- 扩展 MCP。`nblane-mcp` 只给本机 Cursor / Claude Code 用，暂停加新工具。
- 把 OpenClaw、Codex 等内嵌为 nblane 的业务库。
- 让 AI / Agent 发布公开内容、改权限或系统设置。
- 把研究资料放进公开站。
- 托管型社交网络。
- 首页星图倾斜相机（2026-09-24 已讨论搁置，见 [设计语言](design-language.md)）。

## 升级判断标准

每个方向落地都必须满足：

- 旧 profile 能继续读取，文件仍可人工编辑。
- 写入有校验，遵守 pool → tree → validate → sync 顺序。
- Agent 写入可撤销；重要操作先在聊天里确认，页面专属操作对 Agent 返回 403。
- 公开层不读取 private 文件。
- 改动说明它解决哪个已感到的痛点（见 [设计语言](design-language.md)）。
