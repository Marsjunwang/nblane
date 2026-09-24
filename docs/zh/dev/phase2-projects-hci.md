---
status: active
owner: 王军 + kimi
last_verified: 2026-09-24
source_of_truth: /projects 页人机交互设计;实现见 src/nblane/web_ui/frontend/src/components/projects/
---

# Phase 2 补篇 · 项目页人机交互宪法(2026-09-23 与王军逐条对齐)

## 总纲:三级触达法则

每个对象只有三级触达:
- **L1 板上直操作**:拖拽、点打卡、行内快添——高频动作,零跳转零弹窗
- **L2 卡片与抽屉**:铭文卡(任务)/编辑抽屉(项目)——全字段;破坏性动作只住这层
- **L3 索引与历史**:时间轴历史层、归档带——完备但视觉降级,可触达不打扰

军规:任何创建动作 ≤1 次点击;历史永远可见但静弱化(动=未竟之事,静=已定之史)。

## 视觉降级规范

- 泳道看板:归档带一行灰条,点击就地展开(月白 40%、只读、可开抽屉、带恢复);
  Done 维持折叠计数,展开后卡淡化;someday 虚线徽章卡;未归属虚线框沉底。
- 时间轴:Done/归档任务 = 月白细刻痕条(半高、无填充、选中提亮),「历史」开关
  默认开;过期里程碑空心菱形;**默认视窗 = 近 6 个月**(可缩放平移),脏日期钳制。
- 一句话:活跃 = 泥金实心+可拖;已定 = 月白线刻+只读。

## 五项裁决

1. **归档项目**:带内就地展开,内容全可查,可恢复。
2. **习惯(日课)**:双重居所——
   - 首页左下「日课印」:一行 `日课 锻炼○ 学习●`(空圈=未打卡,金点=已打卡),
     点名字直接打卡,悬停浮现本周七点;构图上补左下空缺,与简报行、境态按钮
     同为裱边层。(后续增强 backlog:锻炼/学习升格为帝星旁伴星,打卡即点亮)
   - 项目页顶部「日课栏」独立区(目标组之上,裱边纹理分隔):一个习惯全站只有
     一行(杜绝分身);habit-plan 也住这里(进度弧 第N/30天 + 打卡点),
     **不再渲染 Queue/Doing 空列**;行展开 = 月历热力图(GitHub 式,月白→泥金),
     点任意格子补卡/消卡。
3. **删除项目**:用户全权。抽屉内「删除」→ 确认弹窗三件套:后果预告("N 个任务
   回未归属 · M 条证据保留引用")+ 输入项目名 + 勾选「记入大事记」(**默认不勾**——
   大事记是叙事,家务删除不混入)。非空项目数据不丢:任务回未归属,证据引用走
   墓碑机制。需后端 `DELETE /project-board/cases/{id}`。
4. **新建任务**:每条泳道 Queue 列顶部常驻「＋ 快速添加」行内输入(点→打字→回车);
   抽屉完整表单保留给全字段场景。
5. **时间轴契约修复**(实测根因):computeScale 原先只遍历 queue/doing/someday,
   Done/归档不进渲染源;域被脏日期拖到 2022→一切压扁。修复:历史层进数据源 +
   默认近 6 月视窗 + 脏日期钳制。

## 功能边界

项目页管:任务、项目、习惯打卡、计划模板。不管:目标(首页重刻)、证据评审
(证据页)、技能编辑(技能树页)。跨域一律跳转不内嵌。

## 后端补件清单

- `DELETE /profiles/{name}/project-board/cases/{case_id}`:chronicle 可选(请求体
  `record_chronicle: bool`,默认 false);任务 project_id 清空回未归属;证据引用
  不动(墓碑机制兜底);ETag/412 纪律。
- 习惯热力图数据:projects-board 的 habits[] 增加近 90 天打卡日期列表(现在只有
  本周七点,热力图无数据)。或独立 `GET /checkins?habit=&days=90`。取舍由实施者定,
  倾向并入 projects-board(单端点原则)。

## 实施状态(2026-09-23 后端落地)

- 删除端点已上线:`DELETE /api/v1/profiles/{name}/project-board/cases/{case_id}`,
  请求体 `{confirm_title, record_chronicle=false}`;confirm_title 逐字不匹配 →
  422 `project_delete_confirm_mismatch`。写入顺序 kanban.md → project-board.yaml,
  双文件锁内复核请求起始快照;勾选时追加 chronicle `project.deleted`(note=标题)。
  响应 `{ok, deleted_id, tasks_unassigned, evidence_refs_kept}`。
- 后果预告**不需要**独立预览端点:projects-board 聚合的每项目 `column_counts`
  (任务数)已够,本次另补 `evidence_ref_count`(case.evidence_refs 计数)——
  前端用已有板数据即可拼「N 个任务回未归属 · M 条证据保留引用」。
- 热力图数据按「单端点原则」并入 projects-board:`habits[].recent_days` =
  近 90 天 `{date, count}`(同日打卡求和、升序);week/streak/total 口径不变。
- 不变量详见 docs/zh/architecture/data-contracts.md「Internal Project」节;
  无新增依赖(见 docs/zh/guides/packaging-manifest.md 登记日志)。

## 实施状态(2026-09-23 前端落地,web_ui SPA)

- **归档带展开**:`components/projects/ArchivedStrip.tsx` — 灰条点击就地展开为
  月白 40% 只读列(无拖拽、无快添、卡片可点开铭文卡);恢复走既有
  `POST /cases/{id}/save {status:'active'}`(archive 端点是单向的,无独立恢复路由)。
- **日课栏**:`HabitBand.tsx` + `habitHeatmap.ts` — 目标组之上、裱边金发丝分隔;
  一个习惯全站一行(`lanes.ts collectHabitRows/collectHabitPlanIds`:`habit.project_id`
  优先、`project.habit_id` 兜底;kind ∈ {habit, habit-plan} 且有解析链接的项目
  不再渲染泳道,孤儿 habit-plan 项目仍保留泳道兜底);habit-plan 行带 第N/总天
  进度弧(time_range vs board.today);行展开 = 近 90 天 GitHub 式热力图
  (月白→泥金),空格点击补卡(POST /checkins 带 date);**实格点击销印**
  (2026-09-24 起:格子带 checkin_ids 时点击 → 就地确认条 →
  DELETE /checkins/{id} 删当日最近一次;无 id 的历史行 tooltip 明示不可销印)。
- **行内快添**:`QuickAddInput.tsx` 常驻每条泳道 Queue 列顶;项目泳道走
  `POST /cases/{id}/tasks`(project-board ETag;`/kanban/cards` 无 project_id 字段),
  未归属泳道走 `POST /kanban/cards`(kanban ETag)。
- **时间轴修复**:`computeScale({dayWidth, history, zoom})` — 历史层(kanban.md
  Done 区)进数据源;默认视窗 = 近 6 个月(`zoom:'recent'`),「最近半年/全部」切换;
  脏日期(<2015 或 >today+2y)钳制 + console.warn;条带一律 `clampRangeToScale`
  裁剪进视窗;初始滚动定位到今日线(约 75% 视口处);刻痕条 = 月白半高无填充、
  选中提亮、只读不可拖;「历史」开关默认开。
- **删除项目 UI**:抽屉基本信息 tab 底部危险区 → 确认弹窗:后果预告
  (column_counts 活列合计 + evidence_ref_count,注明 done-archive 高估口径)+
  逐字项目名输入 +「记入大事记」(默认不勾)→ DELETE → 失效刷新 + 关抽屉。
- **首页日课印**:`starmap/HabitSeal.tsx` + starmap.css 印章样式 — 左下裱边层
  (星表「+」旁,与右下 →境态 对位);`日课 名字○/●`(空圈/金点按今日打卡态),
  点名字 POST /checkins(今日),悬停浮本周七点。数据走 projects-board
  (单端点原则,react-query 与 /projects 共享缓存;无更轻的 habits 端点)。
- 测试:vitest 26 文件 189 例(新增 lanes 去重 3、timelineMath 5、habitHeatmap 4、
  ProjectsPage 5、HomePage 1);e2e `tests/e2e/spa_projects_hci.spec.ts` 8 例
  (隔离栈 18504 + 王军数据,截图 /tmp/hci-shots/)。

## 实施状态(2026-09-24 缺口闭合:销印 + 任务编辑)

- **销印端点**:`DELETE /api/v1/profiles/{name}/checkins/{checkin_id}` — 从
  activity-log.yaml 删除一条打卡(纯家务,**不写 chronicle**);flock +
  expected_snapshot 锁内复核,If-Match 412 纪律与 POST 相同;未知 id → 404
  `checkin_not_found`;响应 `{ok, checkin_id}` + 新 ETag。无 id 的历史行
  不可寻址(404)。
- **热力图数据**:`habits[].recent_days[]` 增加 `checkin_ids`(当日打卡行 id,
  升序;无 id 行省略)——销印寻址所需,单端点原则不变。
- **日课栏销印 UI**:实格(有 checkin_ids)点击 → 网格下方就地确认条
  「销印 <date> 最近一次打卡?」→ 确认删当日**最近一次**记录 → 失效刷新;
  caption 改为「空格点击补卡,实格点击销印(删最近一次)」,补卡/销印对称。
  首页 starmap HabitSeal 暂未接销印(待接线,见 HabitBand.tsx 头注)。
- **任务编辑**:铭文详情卡 `TaskDetailCard.tsx` 新增编辑模式(头部「编辑」
  切换)——标题/上下文/为什么/归属/标签五字段,保存走既有
  `PATCH /kanban/cards/{ref}`(kanban.md ETag + If-Match,只提交改动字段,
  标题不可空);排期仍归既有排期行,不重复造。归属 Select 在编辑模式并入表单,
  阅读模式保持即选即改。
- 测试:pytest `tests/test_web_api_projects_board.py` 新增 TestCheckinDelete 3 例
  (删除回写 + 聚合更新 + 无 chronicle、404、412;auth 401 覆盖面同步扩展);
  vitest 新增 habitHeatmap checkin_ids 1 例、ProjectsPage 销印往返 1 例、
  TaskDetailCard 编辑模式 4 例。全量:pytest 1724、vitest 229、tsc 绿。
- 真人 QA(vite dev 15173 → 隔离栈 18504,王军数据,Playwright 6 旅程全绿):
  任务 create→edit→schedule→move→done 闭环、热力图补卡→销印往返、
  空项目 归档→恢复→删除、时间轴交互;截图 /tmp/qa-shots/。
