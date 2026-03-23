# 大佬之路 中文文档

与 [上级英文索引](../README.md) 对应，便于中文读者阅读。

| 文档 | 说明 |
|------|------|
| [安装与 LLM 配置](setup.md) | 安装方式、依赖说明、`.env` 配置、非 OpenAI 服务商 |
| [产品设计 (v0.2)](product.md) | Human + Agent + Team 共进化、四层结构、路线图与仓库映射 |
| [Web 体验设计（Streamlit）](web-ui-product.md) | 信息架构、首屏与品牌、动线、与产品分层对齐；backlog |
| [Web 使用手册（Streamlit）](web-ui.md) | 如何运行、侧栏档案、分页面操作、与 CLI 对照 |
| [看板使用手册](kanban.md) | 四列用法、结构化字段、子任务、移动列、Done 整理、AI 摄入步骤 |
| [看板归档 kanban-archive.md](kanban-archive.md) | 主看板与归档文件分工、Web 归档操作、与 AI 摄入的关系 |
| [初步设计闭环](initial-loop.md) | 把产品、设计、架构串成一条可执行的最小闭环 |
| [设计手册与里程碑](design.md) | 如何实现、里程碑、数据契约、命令与验收 |
| [架构与设计原则](architecture.md) | 目录结构、工程规则、与产品愿景的关系 |
| [SKILL.md 格式说明](profile-format.md) | 各章节含义与更新节奏 |
| [技能树 Schema 指南](skill-tree-schema.md) | `schemas/` 与个人 `skill-tree.yaml` |
| [技能证据 Skill evidence](evidence.md) | 字段说明、CLI、Web、`context` / `gap` / `validate` |
| [Demo 1 · Profile 文档关系与闭环](../profile-documents-relationship.md) | 各文件职责、简历与看板闭环、更新顺序与 LLM 契约；**`ingest-resume` / `ingest-kanban` 与 Web 摄入**已对齐 |
| [MCP 服务器（Cursor）](mcp.md) | stdio 资源、环境变量、**在非 nblane 工程窗口**通过用户级 MCP 连接本机同一仓库 |

## 推荐阅读顺序

1. 先读 [产品设计](product.md)，理解 nblane 的目标、对象与四层结构。
2. 再读 [初步设计闭环](initial-loop.md)，看当前版本如何把任务、协作、回写与复用串起来。
3. 然后读 [设计手册与里程碑](design.md)，确认每个阶段的交付、命令与验收。
4. 最后读 [架构与设计原则](architecture.md)，理解仓库今天真正实现到哪里。
