---
status: draft
owner: 王军 + kimi
last_verified: 2026-09-23
source_of_truth: Phase 2 前端(/projects 一页双视图)实施计划;后端契约见 routes_v1.py / core/projects_board.py;视觉概念稿见 .dev-assets/design-mockups/phase2/
---

# Phase 2 前端实施计划 · /projects 一页双视图

## 0. 现状与关键事实(侦察结论)

- 后端聚合已落地:`GET /api/v1/profiles/{name}/projects-board`(ETag 覆盖 6 个源文件)、
  `POST kanban/cards/{ref}/move`(含 `to_index`)、`/done`、`/schedule`、`POST /checkins`。
- **ETag 不可混用**:projects-board 的 ETag 是 6 文件联合摘要,kanban mutation 校验的是
  kanban.md 单文件 ETag(`_kanban_etag`,routes_v1.py:899),checkins 校验 activity-log.yaml
  单文件 ETag。把 board ETag 当 If-Match 发会稳定 412。
- **card_ref 按标题寻址**(精确标题或唯一子串,不是 task id);重名 → 422
  `kanban_card_ambiguous`。`?task=` 选中态与 dnd id 用 task.id(kb_xxx),mutation 传 title。
- checkins 没有任何 GET 端点返回 activity-log ETag;首次打卡只能不带 If-Match
  (服务端 flock + expected_snapshot 仍兜底),成功后缓存响应 ETag 供连续打卡使用,
  412 时降级为无 If-Match 重试一次。
- `openapi.json` 已含新端点,但 `src/api/schema.d.ts` 未重生成 —— 第 0 步先跑
  `npm run gen:api`。
- DnD 库已在依赖中:`@dnd-kit/core@^6.3.1` + `sortable@^10` + `utilities@^3.2.2`,
  KanbanPage 已有完整多容器拖拽 + jsdom 测试 mock 样板,直接复用,**不新增依赖**。
- habit 泳道数据:顶层 `habits[]`(本周 7 天 dots + streak + total_checkins +
  last_checkin);`habit↔project` 的名称启发式链不上王军的 `保持锻炼`↔`exercise`,
  前端 habit 泳道**从顶层 habits[] 渲染**;后端补件落地后 project.habit_id 作显式关联。
- **时间轴 habit 打卡带的历史数据缺口**:API 只给本周 dots + 计数,概念稿的 38 个
  历史打卡点无数据源。本期打卡带只画本周 dots,完整历史带列为后端待办(可选 follow-up)。
- 概念稿「按活动」分组 toggle 在 mockup.js 中是无行为的占位 div,语义未定 —
  本计划按 `project.kind`(内部/研究/工作/副业/学习,KIND_LABELS 已存在)实现。
- 铭文卡 token(theme.ts)与概念稿 v2 提亮值(#eeddab/#e2dcc9/#b0a78c/#eac57e)
  有偏差,实施时同步更新 theme.ts 的 inscription token。

## 1. 执行步骤(按序)

### 步骤 0 · 类型与 API 层(无 UI)
1. `cd src/nblane/web_ui/frontend && npm run gen:api` 重生成 `schema.d.ts`。
2. `src/api/types.ts`:新增别名
   `ProjectsBoardResponse`/`ProjectsBoardGoal`/`ProjectsBoardProject`/
   `ProjectsBoardTask`/`ProjectsBoardMilestone`/`ProjectsBoardHabit`/
   `ProjectsBoardHabitDay`/`KanbanCardScheduleRequest`/`CheckinCreateRequest`/
   `CheckinMutationResponse`,以及 `ProjectsBoardResult { board, etag }`。
3. `src/api/hooks.ts`:
   - `useProjectsBoard(profile)` — queryKey `['profiles', name, 'projects-board']`,
     `apiGetWithHeaders` 抓 ETag(同 useKanbanBoard 样板)。
   - `useKanbanEtag(profile)` — 轻量 GET /kanban 只取 ETag(`select` 收窄),
     queryKey `['profiles', name, 'kanban-etag']`;供 move/done/schedule/add 的
     If-Match 使用。
   - `useScheduleKanbanCard(profile)` — POST `.../schedule`,body
     `{planned_start?, planned_end?}`(null 省略 / "" 清除)。
   - `useAddCheckin(profile)` — POST `/checkins`;首次无 If-Match,成功后把响应
     ETag 写入 cache;412 → 无 If-Match 重试一次。
   - move/done/add 复用既有 hooks,但改用 `postEtagMutation` + `refreshKanbanEtag`
     (GET /kanban headers)+ `writeKanbanEtag`(仿 writePoolEtag),成功后同步失效
     `projects-board` + `kanban` + `kanban-etag` 三个 query。
   - `useInvalidateProjectsBoard(profile)` — 失效 projects-board;checkin 只需它。

### 步骤 1 · 路由与导航合并
- `src/App.tsx`:新增 `/p/:name/projects` → `ProjectsPage`;`/p/:name/kanban` 与
  `/p/:name/project-board` 改为 redirect(`<Navigate ... replace />`,保留 query
  串;仿 EvidenceReviewRedirect 写法,放在 ProjectsPage.tsx 内导出)。
- `src/components/AppLayout.tsx`:NAV_ITEMS 删「看板」「项目看板」两项,加
  `{ label: '项目', path: 'projects', icon: IconTimeline }`(排在首页之后);
  `FULL_BLEED_SEGMENTS` 把 `'/kanban'` 换成 `'/projects'`。

### 步骤 2 · 页面骨架 + URL 状态
- 新建 `src/pages/ProjectsPage.tsx`:
  - `useSearchParams`:`view=kanban|timeline`(默认 kanban)、`group=goal|activity`
    (默认 goal)、`task=<task.id>`。非法值回退默认。切换 view/group 时
    `setSearchParams(..., { replace: true })` **保留 task**(共享选中态);
    关闭详情卡时只删 task 参数。
  - 顶栏(sticky,仿 EvidencePage):标题 `{name} · 项目`、视图
    `SegmentedControl`(泳道看板/时间轴)、分组 SegmentedControl(按目标/按活动)。
  - 数据:`useProjectsBoard(name)`;pending/error 态同既有页面。
  - `useMemo` 派生泳道列表:`group=goal` → goals[].projects + ungrouped_projects
    追加为「未分组」组;`group=activity` → 全部项目按 kind 分桶。**两种分组产出
    同构的 LaneGroup[] 数组**,BoardView 与 TimelineView 共用同一份。
  - 选中任务查找:跨 goals/ungrouped/unassigned_tasks 按 id 找 BoardTask。

### 步骤 3 · 看板视图(BoardView)
新建 `src/components/projects/` 目录:
- `BoardView.tsx` — 渲染 LaneGroup[];每组:目标行(徽标 + title + target 日期 +
  summary);其下项目泳道;组尾「未归属任务」泳道(虚线金边);底部「已归档项目 ·
  N ▸」折叠条(本期仅计数折叠)。
- `ProjectLane.tsx` — 一条泳道:头部(项目名、kind/status 徽标、里程碑进度、
  `Done · N ▸` 折叠计数含 archived_done_count、last_activity);Queue / Doing 列;
  someday 渲染为 Queue 列内虚线半透明卡 + 金边徽章(不占列、不参与拖拽排序)。
- `LaneColumn.tsx` + `TaskCard.tsx` — 从 KanbanPage 移植 dnd-kit 样板,**DnD 范围
  收敛到单条泳道内**(每条泳道一个 DndContext):跨列 Queue↔Doing + 列内排序 →
  move(to_index);跨泳道归属走详情卡 PATCH。卡片点击(非拖动)→ 设 `?task=<id>`。
- `HabitLane.tsx` — 从顶层 habits[] 渲染:标题 + 徽标 + 本周 7 个打卡点 +
  `连续 N 天 · 上次 MM-DD` + 「打卡」按钮(useAddCheckin)。
- 视觉:深色内容底 alpha 0.85–0.92、月白 `#f2ede0` 正文、小字金 `#eac57e`、
  选中卡金框(概念稿 v2 提亮值;石刻纹理底层本期可选,先纯色)。

### 步骤 4 · 铭文详情卡(TaskDetailCard)
- `src/components/projects/TaskDetailCard.tsx`:复用 `InscriptionCard` +
  `InscriptionRow`;`?task=` 有值且找到任务时打开。
- 内容:状态行、started_on/completed_on、planned 排期、context/why、归属项目、tags。
- 操作行:移至 Doing/Queue/Done;排期 date input + 保存/清除(时间轴拖拽的兜底,
  先上);打卡;结晶为证据 → 跳转 `/p/:name/evidence?stage=crystallize`;
  归属变更 → PATCH `/kanban/cards/{ref}` 改 project_id(后端补件)。
- 412/422:ConflictAlert + `kanban_card_ambiguous` 专用提示。

### 步骤 5 · 时间轴视图(TimelineView,静态先上)
- `timelineMath.ts` — 纯函数:`dateToX` / `xToDate`(日粒度吸附)/ `monthTicks` /
  `taskBarRange(task, today)`:`planned_start ?? started_on` →
  `planned_end ?? completed_on ?? today`;无日期 → null(行尾「未排期」)。单测优先。
- `TimelineView.tsx` — 同一份 LaneGroup[]:月轴 + 今日线(金色虚线,board.today);
  项目 time_range 淡化底块;任务条(queue/doing 点线细块、done 淡化块、选中金框);
  里程碑菱形(planned 且过期 → 空心);habit 行绿色虚线带 + 本周 dots;行尾 Done
  计数 + 未排期列表。横滚 ScrollArea,行标签列 sticky 左侧。
- 点击任务条 → 同一 `?task=` 详情卡。

### 步骤 6 · 时间轴拖拽改期(风险最高,放静态视图之后)
- `useTimelineDrag` 自定义 hook(**不引入新库**):pointerdown 记起点与 bar 区间,
  pointermove 换算日偏移(吸附整天),本地预览,pointerup 提交 schedule(整体平移;
  左右边缘拖拽分别改 start/end 为增强项)。
- 失败(412/422)→ 回滚预览 + ConflictAlert。
- 项目编辑能力(原 ProjectBoardPage BasicsTab/MilestonesTab)迁为泳道头「编辑」
  Drawer,复用 useSaveProjectCase 等 hooks;完成后删除旧页面。

### 步骤 7 · 测试
- vitest:timelineMath 纯函数全覆盖;ProjectsPage(分组/someday/未归属/habit dots/
  Done 折叠/view 切换保留 ?task/redirect 带 query);BoardView 拖拽(仿 KanbanPage
  mock 样板);TaskDetailCard 操作行;AppLayout 导航断言更新。
- e2e:spa_smoke/auth/kanban_dnd/mutations/pages/mobile/layout 中 /kanban、
  /project-board 引用全部迁到 /projects;新增 spa_projects.spec.ts(视图切换选中态、
  ?task= 深链、排期提交、打卡)。
- 回归:`npm run build` + 全量 pytest;CI 四件套绿。

### 步骤 8 · 清理
- 删除 KanbanPage/ProjectBoardPage 及其测试(能力迁出后);孤儿 hooks 一并删。
- 更新 phase-plan.md「Phase 2 进展」;本文件 last_verified 刷新。
- Streamlit 的 pages/3_Kanban.py / 11_Project_Board.py 冻结不动,退役归全局路线图。

## 2. 风险登记

1. **时间轴拖拽改期(最高)**:pointer 数学、日吸附、横滚与手势冲突、touch 设备。
   缓解:静态视图 + date input 兜底先交付,拖拽作增量;失败一律回滚 + 412 刷新。
2. **ETag 三源不一致**(board / kanban / activity-log):误用即稳定 412。所有
   mutation 集中走 postEtagMutation + 各自 refresh/write 对。
3. **标题寻址**:重名卡 422;选中用 id、mutation 用 title。
4. habit 数据缺口:时间轴打卡带只有本周 dots。
5. 旧路由深链:redirect 保留 query 串并 replace,e2e 全量过。
6. 设计 token 漂移:inscription token 按概念稿 v2 提亮值更新 theme.ts。
7. 全量聚合无截断:数据量大时观察首屏性能,暂不做虚拟化。
