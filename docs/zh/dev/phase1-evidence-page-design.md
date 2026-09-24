---
status: active
owner: 王军 + kimi
last_verified: 2026-09-24
source_of_truth: 本文档是 Phase 1(证据域)的设计定案;全局计划见同目录 phase-plan.md
---

# Phase 1 · 证据域单页化 — 设计定案(交接文档)

## 背景与约束

- 目标:第一数据 loop(北极星→目标→项目→看板任务→证据结晶)全程可在前端完成,不手改 YAML。
- 约束:**不改变数据存储格式**;SPA 为唯一新前端,Streamlit 冻结为 legacy;所有写操作走 API(ETag/If-Match + flock + 锁内快照复检,样板见 `web_api/routes_v1.py` 的 `_mutate_evidence_pool`);kanban.md 写操作只允许经 `core/kanban_io.py`。
- 现状侦察结论(2026-09-22 四路侦察):
  - SPA 证据池页纯只读;评审页只有 4 个白名单字段批量改;结晶(Done→证据)只在 Streamlit。
  - `crystallized` 状态机在 `pages/3_Kanban.py:406` 和 `pages/2_Evidence_Review.py:382` 双写,**先收口进 core 再接 API**。
  - 生产数据(`/srv/nblane-data/profiles/王军`):55 条证据,`original_content` 填充 47/55,`kanban_refs` 31 条中 8 条死链,`source_refs`/`experience_refs` 0 使用。
  - Profile Health 页解散(诊断应该来找人,不是人去找诊断;首页星图即健康展示)。

## 页面设计:单页「证据」,五阶段工序

证据生命周期 = 流水线 = 星图语言里的"客星入座"。

```
待结晶 → 待评审 → 已入座 → 已废弃
                ↘ 待补强(风险)
```

- 左栏:五个阶段,数字常驻(与首页简报行/脉动客星同源)。
- 中栏:证据列表(标题/类型/强度/日期/所属项目)。
- 右栏:详情铭文卡(视觉语言与 home 详情卡一致,工具页效率优先,风格点到为止)。
- 顶部唯一主按钮:「从已完成任务结晶」→ 三步向导:选 Done 任务 → AI 生成草稿(走既有 job+SSE)→ 人工评级勾选 → 入库;无 LLM 时规则版兜底生成毛坯。

> 风格对齐(2026-09-24):左栏阶段导航与中栏列表行/候选卡/风险卡/向导卡统一
> 铭文相邻质感(深底 + 细金边 `rgba(220,174,85,.22)` + 明体);active 阶段=
> 细金框 + 金底 10%;快评光标行 = 泥金虚线;强度徽章与「接受」「入库」按钮
> 去 Mantine 绿/黄,统一泥金 brand;红色仅留语义(废弃/删除)。详情铭文卡本体
> 不动。右栏占位卡同款细金边。

## 已定案的设计规则

1. **快速评审模式**:键盘 `j/k` 导航、`a` 接受、`s` 跳过、`1/2/3` 定强度。清空队列像清收件箱。
2. **原文规则(数据投票:original_content 85% 填充、kanban_refs 26% 死链)**:
   - 结晶即快照:任务原文(title+context+why)写入 `original_content`+hash,证据自足;
   - `kanban_refs` 保留为溯源通道,死链显示"已归档"墓碑,不 404;
   - UI 统一渲染为「出处」列表(类型图标区分);数据层字段不动。
   - UI 字段瘦身:`source_refs`/`experience_refs`/`url` 收进「更多」。
3. **证据↔技能关联**(降低粒度 + 检索建议 + 单一真相):
   - 默认挂**类别级**(14 选 1),叶级仅在证据专属时;
   - embedding top-5 建议(技能名称+描述离线嵌入缓存,证据实时余弦);无 embedding 端点时 LLM 排序兜底;
   - 结晶向导的 LLM patch 顺手生成技能建议,确认即关联;
   - 写入只有一侧(技能节点的 `evidence_refs`),反向现算(`evidence_usage_index`),UI 双向展示。
4. **Claims 封存**:消费者(简历/公开页/拓片铭文)未建成前不迁移;Phase 5 输出层重建时复活(可更名"成就")。
5. **Risks 并入证据页「待补强」阶段**(expert 技能+陈旧/薄弱证据);Profile Health 解散:数据卫生→Settings「档案维护」;体检报告→openclaw 周回顾主动推送。

## 与后续 Phase 的契约(防止返工)

| Phase 1 要建成通用件 | 后续消费者 |
|---|---|
| mutation API 样板(ETag 模式) | Phase 2 看板卡片编辑、Phase 3 目标 CRUD |
| embedding 建议能力(`core/ai/` 下,技能描述嵌入缓存) | Phase 2 任务→项目建议、Phase 4 openclaw 语料 |
| 铭文卡组件(设计 token:深底/金边/文楷标题/明体正文) | Phase 3 home 详情卡同款、全局统一 |
| 结晶状态机(core 收口) | Phase 2 看板 Done 流、Phase 4 agent 自动结晶 |

不做的事(本期):Claims studio、时间轴、团队、公开输出。

## 验收标准

- 王军真实使用:录证据/评审/结晶/关联技能全程不出 SPA,不手改 YAML。
- `pytest -q` 全绿;既有 e2e 不破坏;CI 四项通过。
