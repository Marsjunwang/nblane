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
| 2 | 项目-看板一体化(一页双视图) | 2–3 周期 | 后端聚合 API 已落地(2026-09-23),前端待开工 |
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

## Phase 2 进展

### 后端聚合 API(2026-09-23 落地)

概念稿(`.dev-assets/design-mockups/phase2/`,`build_data.py` 为取数规格)的后端化:

- `GET /api/v1/profiles/{name}/projects-board` — /projects 一页双视图的一次性聚合:
  目标分组泳道(项目挂在第一个有效 `goal_refs` 下,无目标进 `ungrouped_projects`)、
  每项目里程碑进度(task_refs 对照 live Done + archive)、Done 计数**含 kanban-archive.md**、
  queue/doing 列任务 + someday 徽章列表、未归属任务泳道、habit 本周 7 天打卡点 +
  streak + 总次数、north_star。全量返回,不做展示截断;ETag 覆盖
  SKILL.md/goals/project-board/kanban/kanban-archive/activity-log 六个源文件。
  聚合逻辑在 `core/projects_board.py`(纯只读)。
- 任务排期字段:`KanbanTask.planned_start` / `planned_end`(可选,ISO 日期),kanban.md
  元数据子弹 round-trip;`POST .../kanban/cards/{card_ref}/schedule` 设置/清除
  (`null` 保留、`""` 清除、start ≤ end 校验),新建卡片端点同步支持。契约见
  data-contracts.md「Kanban 任务元数据字段」。
- `POST /api/v1/profiles/{name}/checkins` — 向 activity-log.yaml 追加一条 Checkin
  (habit id/标题 或 habit 链接项目的 `project_id`;date 默认今日),agent(openclaw)
  接入面。ETag/If-Match + flock 样板与既有 mutation 一致;`add_activity_checkin`
  新增 `expected_snapshot` 支持。
- 里程碑模型保持不动(数据里全是 `planned`,「过期 planned = 空心菱形」是前端展示推导)。
- 与概念稿的偏差:habit ↔ project 链接在 mockup 里是硬编码(`保持锻炼` ↔ `exercise`);
  2026-09-23 已补显式字段:project case 新增可选 `habit_id`(case save/create API 可读写,
  空串清除),聚合时显式链接优先、名称启发式兜底;`POST .../checkins` 的 `project_id`
  入口同样先走显式链接。王军 profile 待手工挂接:project：保持锻炼 写
  `habit_id: exercise`(走 case save API)。
- 任务字段编辑(拖拽入泳道):`PATCH /api/v1/profiles/{name}/kanban/cards/{card_ref}` —
  改 title/context/why/tags,`project_id` 赋值/空串清除;改 project_id 后自动从 kanban
  元数据回写 project-board.yaml `task_refs`(任务侧为准)。If-Match/412 + 三路合并样板与
  schedule 端点一致。Someday 是 section 不是 flag,移动仍走 move 端点。
- 习惯计划模板(点击实例化):内置 3 个(30天减脂/30天康复/21天学习打卡)随包发布于
  `core/data/habit_plan_templates.yaml`(`core/plan_templates.py` 加载);
  `GET .../plan-templates` 返回内置 + profile 使用历史(新文件 plan-templates.yaml,
  按 template_id 去重、最新在前);`POST .../plan-templates/instantiate` 一次建成
  `kind=habit-plan` case(time_range/里程碑日期由 start + duration/offset 推导)+
  缺 habit 自动建 + 显式 habit_id 链接 + 历史记录——projects-board 即刻渲染为打卡泳道。
- 测试:`tests/test_web_api_projects_board.py`(30 例,含显式 habit 链接/PATCH/计划模板)
  + kanban_io 排期 round-trip。openapi.json 已随 `scripts/dump-openapi.sh` 重生成。

### 前端 /projects 一页双视图(2026-09-23 落地)

- `/p/:name/projects` 统一页(`/kanban`、`/project-board` 重定向并保留 query);
  `view=kanban|timeline` + `group=goal|activity` + `?task=<id>` 共享选中态,
  视图切换 replace 且保留 task。
- 泳道看板:目标分组泳道(Queue/Doing 列 + someday 虚线徽章卡 + Done 折叠计数含归档)、
  habit 打卡泳道(本周 7 点 + streak + 打卡按钮)、虚线金边未归属泳道、已归档项目计数
  折叠条;按活动分组按 `project.kind` 分桶。泳道内 dnd-kit 拖拽(跨列 + to_index 排序),
  跨泳道归属走详情卡 PATCH。
- 铭文详情卡:状态/日期/排期保存与清除/context/why/归属变更(PATCH project_id)/标签,
  操作行 移至 Doing/Queue、标记 Done、打卡(显式 habit 链接)、结晶为证据跳转;
  412 → ConflictAlert,422 `kanban_card_ambiguous` 专用提示。
- 时间轴:月轴 + 今日金虚线;项目 time_range 淡化底块;任务条(queue 点线/doing 实块/
  done 淡化/选中金框);里程碑菱形(过期 planned 空心);habit 绿色虚线本周带 + 打卡点;
  行尾未排期列表。拖拽改期为自定义 pointer hook(整条平移,日粒度吸附,失败回滚),
  排期 date input 为兜底。
- 项目编辑:泳道头「编辑」Drawer(基本信息/里程碑/任务三 tab,含 AI 建议引用与
  M-FE-1 草稿保护);「新建项目」与「新建计划」(内置模板 + 历史,title/start 覆盖)
  两个 modal。KanbanPage/ProjectBoardPage 已删除;Streamlit pages/3_Kanban.py 与
  11_Project_Board.py 冻结不动。
- ETag 纪律:board/kanban/activity-log/plan-templates 四源分离,mutation 一律
  postEtagMutation(412 → 刷新 ETag 重试一次);checkin 首次不带 If-Match,成功后缓存。
- 测试:vitest timelineMath/lanes/ProjectsPage 纯函数+交互 30+ 例;e2e 迁移
  spa_smoke/auth/layout/mutations/pages/mobile/llm_jobs 至 /projects,新增
  spa_projects.spec.ts(泳道 DnD/?task= 深链/排期/打卡/重定向)。

## Phase 3 进展

### home 星图进 SPA(2026-09-23 kickoff 落地)

- SPA 首页 = 成长星图:playground(`home_dashboard_component/frontend/playground/`)
  的 Three.js 场景移植为 `web_ui/frontend/src/starmap/`(layout.ts 纯数学 +
  StarmapScene.ts 场景类 + StarmapView.tsx React 壳),码分 chunk 懒加载;
  旧首页卡片与 sidecar 3D iframe 同步移除。
- 数据取数:组合既有只读 API(/goals + /skill-tree + /projects-board +
  /evidence-review?status=all + /evidence),`starmap/snapshot.ts` 纯函数对齐
  `export_snapshot.py` 语义(客星 30 天窗 + 最新 4 条密度下限、行星进度
  任务优先里程碑兜底)。后端唯一改动:`SkillTreeNodeModel` 增加 `category`
  字段(扇区环取数,additive)。
- 缺口(2026-09-23 follow-up 已全部关闭,见下节):schema 全量
  目录(locked 节点不在 overlay,星图缺空圈底星);证据列表缺 project_refs
  (入座星目前只能回退到技能扇区落位);evidence summary 需双端点合并。
- 交互保留:图态↔境态 morph(滚轮/按钮,2.4s gsap)、拖拽拨盘+惯性、
  1h/圈 恒转+伸手即停、客星呼吸 11s(仅光晕)、reduced-motion 降级、
  点击铭文卡(React 渲染,Escape/底栏滑动关闭)。
- 测试:vitest starmap 纯函数 22 例 + HomePage 3 例;e2e spa_home.spec.ts
  重写(简报计数对拍 API、morph toggle、北极星铭文卡)、spa_layout 首页
  用例换星图版式断言。
- Streamlit 首页(app.py)弃用待后续切片;星图组件回流 Streamlit 双栈共享
  亦未做(本轮仅 SPA)。

### 星图聚合端点落地(2026-09-23 follow-up)

- 新端点 `GET /api/v1/profiles/{name}/starmap`(纯读):一次返回北极星、
  active goals、**含 locked schema 节点**的技能场(三态 locked/learning/lit)
  + 服务端 zh 类目名、带 progress + goal 分组的项目行星、证据客星/入座/尘埃
  (30 天窗 + 最新 4 条密度下限,strength/summary/project_refs 齐)。语义移植
  自 playground `tools/export_snapshot.py`;核心逻辑在
  `core/starmap_snapshot.py`,响应模型 `StarmapResponse`;弱 ETag 覆盖
  SKILL.md/goals/skill-tree/schema/project-board/kanban(+archive)/
  activity-log/evidence-pool 九源(同 projects-board 模式)。
- SPA 首页换单一取数:`useStarmapData` 直连 /starmap,`snapshot.ts` 只保留
  形状声明 + `normalizeStarmapResponse`(wire 默认值填充);CATEGORY_ZH、
  客星窗口/密度下限、行星进度推导全部移到服务端。
- kickoff 三个 fidelity 缺口全部关闭:locked 空圈底星入场(类目扇区随之补全)、
  入座星按 project_refs 落行星旁、zh 类目名服务端下发。
- 测试:pytest `test_web_api_starmap.py` 12 例(客星窗口/下限、locked 包含、
  zh 类目、进度与分组、ETag、401/403/404);vitest starmap 15 例(normalize +
  layout,新增 project_refs 入座);e2e `spa_home.spec.ts` 简报计数改对拍
  /starmap counts。


## 已知风险登记

- embedding 端点是否存在待确认(无则 LLM 排序兜底)。
- openclaw 自动化已在生产运行(每日计划 08:30/每日复盘 21:30/每周整理,微信推送),声明在 openclaw workspace;nblane 侧 `assistant/automations.yaml` 从未部署——Phase 4 的核心是**把既有自动化与 nblane 数据双向接通**(MCP),而非从零创建。openclaw 本体(gateway 18789/MCP/CLI)本机可用。
- kanban.md 元数据契约脆弱,任何新写路径必须走 kanban_io。
- Streamlit 内多条写路径无快照保护(last-write-wins),迁移时以 API 纪律为准,不回移植坏习惯。
