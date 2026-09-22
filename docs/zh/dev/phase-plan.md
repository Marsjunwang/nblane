---
status: active
owner: 王军 + kimi
last_verified: 2026-09-22
source_of_truth: 全局路线图与各 Phase 边界;Phase 1 细节见 phase1-evidence-page-design.md
---

# nblane 蜕变计划 · 全局路线图(粗版)

总纲(王军 2026-09-22 设计文档):聚焦深入融合 openclaw,优化前端交互,统合后端功能,**不改变数据存储**。
验收标准:第一数据 loop(北极星→目标→项目→看板→证据结晶)全程前端完成,不手改 YAML。

## 路线图

| Phase | 内容 | 预估 | 状态 |
|---|---|---|---|
| 1 | 证据域单页化 | 1–1.5 周期 | 已定案,开工 |
| 2 | 项目-看板一体化(一页双视图) | 2–3 周期 | 形态讨论中 |
| 3 | 目标/北极星编辑 + home 星图生产化 | 1.5–2 周期 | 待 Phase 1 |
| 4 | openclaw 日报/主动提醒 | 1–2 周期 | 待 Phase 3 |
| 5+ | 工具层:论文阅读/写作减法/静态网页/简历/gap 占卜按钮 | 各 0.5–2 周期 | 按喜好挑选 |
| — | 团队功能 | — | 暂不做 |

总预估 6–9 个额度周期(墙钟约 1–1.5 周)打通 loop;工具层随后按需。

## 已定案的全局决策

- **Agent 后端可切换**:`NBLANE_AGENT_BACKEND=openclaw|none`;openclaw 提供"主动性"(调度+触达),能力永远在 nblane core;关掉 openclaw 全站照常工作,只是没有晨报和主动推送。集成面只有两处:MCP server + automations 声明,禁止深度私有集成。agent 动作的唯一入口是 `agent-activity.yaml` 审批队列。
- **SPA 是唯一新前端;Streamlit 冻结**,页面随 SPA 覆盖逐个分层退役;**Streamlit 首页(app.py)在 Phase 3 完全弃用**,随星图组件替换一起换。
- 所有写操作只走 API(ETag/If-Match + flock 样板);kanban.md 只经 `core/kanban_io.py`;前端永不直碰 YAML。
- Profile Health 页解散:证据风险→证据页「待补强」;数据卫生→Settings「档案维护」;体检报告→openclaw 周回顾主动推送;成长统计→首页/拓片。
- Claims 封存,Phase 5 输出层重建时复活(消费者:拓片铭文/简历 bullet)。
- home 星图组件为双栈共享组件,替换时两栈同时生效。

## 跨阶段契约(防返工)

Phase 1 建成通用件:mutation API 样板、embedding 建议能力(core/ai/)、铭文卡共享组件+设计 token、结晶状态机(core 收口)。分别被 Phase 2/3/4 消费。

## 已知风险登记

- embedding 端点是否存在待确认(无则 LLM 排序兜底)。
- openclaw 自动化已在生产运行(每日计划 08:30/每日复盘 21:30/每周整理,微信推送),声明在 openclaw workspace;nblane 侧 `assistant/automations.yaml` 从未部署——Phase 4 的核心是**把既有自动化与 nblane 数据双向接通**(MCP),而非从零创建。openclaw 本体(gateway 18789/MCP/CLI)本机可用。
- kanban.md 元数据契约脆弱,任何新写路径必须走 kanban_io。
- Streamlit 内多条写路径无快照保护(last-write-wins),迁移时以 API 纪律为准,不回移植坏习惯。
