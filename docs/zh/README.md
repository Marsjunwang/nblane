---
status: active
owner: docs
last_verified: 2026-10-07
source_of_truth: true
---

# nblane 中文文档

中文文档是 nblane 的事实源。英文文档只保留入口。产品定义、项目状态、架构边界以本目录为准。

## 阅读路径

| 读者 | 阅读顺序 |
|------|----------|
| 新用户 | [产品总览](product/overview.md) → [安装与配置](guides/setup.md) → [Web 总览](guides/web-ui.md) → [首页](guides/home.md) → [项目](guides/projects.md) → [证据](guides/evidence.md) |
| 开发者 | [架构总览](architecture/overview.md) → [数据契约](architecture/data-contracts.md) → [模块地图](architecture/module-map.md) → [SPA 现状总账](architecture/frontend-spa-migration.md) → [设计语言](product/design-language.md) → [CLI 参考](reference/cli.md) |
| Agent 接入 | [AI 架构](architecture/ai-architecture.md) → [个人助手](guides/assistant.md) → [OpenClaw 运维](guides/openclaw-ops.md) → [Agent Harness](reference/agent-harness.md) → [MCP 参考](reference/mcp.md)（仅本机 Cursor / Claude Code） |
| 部署 / 运维 | [腾讯云部署](guides/deployment-tencent-cloud.md) → [整机迁移](guides/migration.md) → [Mihomo 代理](guides/mihomo-deployment.md) → [OpenClaw 运维](guides/openclaw-ops.md) → [存储边界](architecture/storage.md) |
| 产品 / 项目管理 | [路线图](product/roadmap.md) → [当前状态](project/status.md) → [里程碑](project/milestones.md) → [决策记录](project/decisions.md) → [问题与风险](project/issues.md) |

## 文档地图

### product/

| 文档 | 作用 |
|------|------|
| [overview.md](product/overview.md) | 定位、用户、核心对象、三层结构、非目标 |
| [roadmap.md](product/roadmap.md) | 往后方向、暂不做、升级判断标准 |
| [design-language.md](product/design-language.md) | 主题 token、身份语法、交互约定、设计流程 |
| [growth-graph.md](product/growth-graph.md) | 成长图谱：evidence 支撑 skill，skill 构成北极星的地基 |
| [paper_reading.md](product/paper_reading.md) | 论文阅读工作台：检索、导入、阅读、翻译、深读、GROBID |

### project/

| 文档 | 作用 |
|------|------|
| [status.md](project/status.md) | 各功能区现状、已移除项、缺口与优先级 |
| [milestones.md](project/milestones.md) | Phase 0–4 里程碑账本 |
| [decisions.md](project/decisions.md) | 关键产品 / 架构决策 |
| [issues.md](project/issues.md) | 当前问题与风险 |

### architecture/

| 文档 | 作用 |
|------|------|
| [overview.md](architecture/overview.md) | 进程与端口、请求链路、鉴权、Agent 写入守卫、生产布局 |
| [ai-architecture.md](architecture/ai-architecture.md) | AI Gateway、外部 harness、Agent 接入与写入策略 |
| [data-contracts.md](architecture/data-contracts.md) | profile 文件真源、写入顺序、不变量 |
| [module-map.md](architecture/module-map.md) | `src/nblane` 模块地图 |
| [storage.md](architecture/storage.md) | 文件优先、Git 备份、公开层、数据库演进边界 |
| [frontend-spa-migration.md](architecture/frontend-spa-migration.md) | SPA 技术栈、打包、契约与现状总账 |

### guides/

| 文档 | 作用 |
|------|------|
| [web-ui.md](guides/web-ui.md) | SPA 总览、导航、通用设置 |
| [home.md](guides/home.md) | 首页星图、星表与目标、占卜、习惯印 |
| [projects.md](guides/projects.md) | 项目：看板 / 时间轴 / 编年史、习惯阶段计划 |
| [skill-tree.md](guides/skill-tree.md) | 技能树 |
| [evidence.md](guides/evidence.md) | 证据六阶段、审阅、待补强、结晶 |
| [research.md](guides/research.md) | 研究台：论文库、概览、阅读器、来源 |
| [content.md](guides/content.md) | 内容工作台 |
| [career.md](guides/career.md) | 求职工作台：简历、目标岗位、JD 定制 |
| [public-site.md](guides/public-site.md) | 公开站点：公开层、构建、发布 |
| [assistant.md](guides/assistant.md) | 个人助手：接入、写入策略、确认与撤销 |
| [workshop.md](guides/workshop.md) | 车间网页终端 |
| [openclaw-ops.md](guides/openclaw-ops.md) | OpenClaw 安装、接入、定时任务、备份 |
| [setup.md](guides/setup.md) | 安装、依赖、LLM 配置 |
| [deployment-tencent-cloud.md](guides/deployment-tencent-cloud.md) | 生产部署：systemd + Caddy |
| [migration.md](guides/migration.md) | 整机迁移 runbook |
| [mihomo-deployment.md](guides/mihomo-deployment.md) | Mihomo 代理部署与运维 |

### reference/

| 文档 | 作用 |
|------|------|
| [cli.md](reference/cli.md) | CLI 命令总览 |
| [mcp.md](reference/mcp.md) | 本机 MCP resources / tools |
| [evidence.md](reference/evidence.md) | Evidence 字段与解析 |
| [skill-md-format.md](reference/skill-md-format.md) | `SKILL.md` 人写区与生成区 |
| [skill-tree-schema.md](reference/skill-tree-schema.md) | `schemas/` 与 `skill-tree.yaml` |
| [agent-harness.md](reference/agent-harness.md) | Codex / OpenCode 等外部 harness 集成 |

### dev/

| 文档 | 作用 |
|------|------|
| [phase0.5-remote-terminal.md](dev/phase0.5-remote-terminal.md) | 远程终端（车间）设计与待部署项 |
| [public-output-workspaces-design.md](dev/public-output-workspaces-design.md) | 内容 / 求职工作台与公开站点的边界和契约 |

英文入口：[../README.md](../README.md)；英文项目板指南：[../en/guides/project-board.md](../en/guides/project-board.md)。

## 文档纪律

- Active 文档必须保留 front matter 四项：`status`、`owner`、`last_verified`、`source_of_truth`。
- 产品状态只写在 [status.md](project/status.md) 和 [milestones.md](project/milestones.md)，使用手册不重复维护路线图。
- 过程性计划合并进正式文档后删除，不新增长期 `*-workplan.md`。
- 规则只写一处，其他地方链接。Agent 写入规则以 [个人助手](guides/assistant.md) 和服务端 `core/agent_policy.py` 为准；公开发布与研究引用以 [数据契约](architecture/data-contracts.md) 为准。
- 事实以代码为准；改了文档描述的行为，同步改文档。
