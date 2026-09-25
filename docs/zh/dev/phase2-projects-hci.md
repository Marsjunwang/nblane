---
status: active
owner: 王军 + kimi
last_verified: 2026-09-25
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

## 实施状态(2026-09-24 收尾片:日课项目可删除 + 快添即入详情 + 任务 TODO 清单)

- **日课项目可删除**:habit-plan 行(日课栏)新增悬停浮现的 设置 钮
  (`habit-plan-settings-<caseId>`,键盘 focus 同样浮现)→ 打开该 case 的
  ProjectEditDrawer(基本信息/里程碑/任务 + 危险区删除,复用裁决3 全套确认)。
  **纯习惯行不给入口**:habit 不是 project case,项目侧无可删对象
  (习惯生命周期归 activity-log/设置页),不做 archive-only 半吊子入口。
  (2026-09-24 晚更新:习惯生命周期端点落地后,纯习惯行已获同款齿轮菜单,
  见文末「习惯生命周期 + 打卡点石刻化」节。)
- **快添即入详情**:≤1-click 规则不变(快添仍只产标题卡),但项目泳道
  (`POST /cases/{id}/tasks`)与未归属泳道(`POST /kanban/cards`)快添成功后
  立即 `?task=<newId>` 打开铭文详情卡——要补上下文的直接落在编辑语境,
  只要标题的 Esc/点即走,零成本。
- **任务 TODO 清单(常用功能)**:kanban 任务新增可选 `todos: [{text, done}]`,
  存为 `- todo: [x]/[ ] text` meta 子弹(契约见
  docs/zh/architecture/data-contracts.md「Kanban 任务元数据字段」;
  旧式 `- todo: 自由文本` 按 detail 兼容,3-way merge 按 list 字段整体 carry)。
  `PATCH /kanban/cards/{ref}` 新增 `todos` 全量替换(`[]` 清空)。
  详情卡新增 TODO 区:勾选/回车加项/删除,本地乐观更新 + 400ms 防抖批量 PATCH;
  看板卡显示 清单 d/t 进度(projects-board 聚合携带 todos)。
- 测试:pytest 新增 4(test_kanban_io todos round-trip + legacy detail 兼容、
  test_kanban_merge todos carry、test_web_api_projects_board PATCH 全量替换/
  清空/聚合携带)全量 1728;vitest 新增 7(TaskDetailCard 清单 4、
  ProjectsPage 快添自动打开 2 + 日课设置钮 1 + 卡片进度 1)全量 246;tsc 绿;
  openapi.json + schema.d.ts 已重生成。无新增依赖(packaging-manifest 已登记)。

## 实施状态(2026-09-24 晚:习惯生命周期 + 打卡点石刻化)

- **习惯生命周期 UI(纯习惯行)**:日课栏纯习惯行获得与 habit-plan 行同款
  悬停浮现齿轮(`habit-menu-<id>`),开菜单两项——
  - **归档**:一键 `POST .../habits/{id}/archive {archived:true}`,行即刻折起
    (本地 archivedIds,服务端归档行默认退出 board 载荷);顶栏「显示已归档」
    开关拉取 `?include_archived=true`(`useArchivedBoardHabits`,与主 board
    共享 query-key 前缀,生命周期 mutation 一并失效),归档行弱显并带 已归档
    徽标,菜单换成「恢复」(`archived:false`)。
  - **删除**:确认弹窗复用项目删除裁决——后果预告「将移除 N 条打卡记录」
    (N 取 `total_checkins`)+ 逐字输入习惯名 + 记入大事记(默认 OFF)→
    `DELETE .../habits/{id} {confirm_title, record_chronicle}` →
    `{ok, deleted_id, checkins_removed}`;422 `habit_delete_confirm_mismatch`
    落为行内字段错误,行保留。
- **打卡点石刻化**:日课栏周点与时间轴习惯带、首页日课印悬停浮条统一
  词汇——未打卡 = 月白 35% 细空心环,已打卡 = 泥金实点,今日格外套细金环
  (box-shadow,不扰填充/描边语义);`boardPalette.habitGreen` 全站退役,
  打卡按钮 green → brand 泥金,无 Mantine 绿。
- 测试:本片 vitest 新增 5(石刻样式 1、归档折起/开关/恢复 1、服务端归档行 1、
  删除预告+逐字确认+DELETE body 1、422 mismatch 1);同日前端另有技能进阶进度
  与证据突破标记(见 phase-plan.md 末节),全量 260、tsc 绿。

## 实施状态(2026-09-24 晚:任务可删除)

- **删除任务端点**:`DELETE /api/v1/profiles/{name}/kanban/cards/{card_ref}`
  — 永久删除一张看板卡。`card_ref` 语义同 move/done/patch(id 优先,
  标题精确/唯一子串为回落;歧义 422、未知 404);kanban.md ETag/If-Match 412 + 锁内快照复核 +
  3-way merge 纪律与其他卡片写端点一致。请求体 `{record_chronicle=false}`:
  勾选才追加 `task.deleted`(ref = 任务 id,note = 标题,默认不记——
  家务删除不混入叙事)。响应 `{ok, deleted_ref, deleted_title}`。
  任务的 todos/subtasks/meta 随卡片消失;evidence-pool `kanban_refs`
  不动(墓碑机制)。
- **删除任务 UI**:铭文详情卡行动行尾(与主操作分开,`ml-auto` 弱红
  subtle 钮)「删除任务」→ 就地确认条「将删除任务「title」,不可恢复」+
  记入大事记勾选(默认 OFF)→ 确认删除 → 失效 board/kanban → 关详情卡;
  412 由 hook 取新 ETag 自动重试一次。
- 测试:pytest `tests/test_web_api_kanban.py` 新增 TestKanbanCardDelete 8 例
  (happy path 文件/看板双验证、子串、歧义 422、未知 404、 stale If-Match
  412、无 body、chronicle on/off、证据 kanban_refs 不动;auth 401/403 覆盖
  同步扩展)全量 1781;vitest 新增 4(确认条显隐/取消、DELETE body+If-Match+
  关卡、记入大事记 on、412 重试)全量 264;tsc 绿;openapi.json +
  schema.d.ts 已重生成。无新增依赖(packaging-manifest 已登记)。

## 实施状态(2026-09-25:someday 进入日常流程)

- **痛点**:Someday 停在 Queue 列里当虚线徽章,不能拖。移入日常只藏在铭文详情卡,
  看板上没有出口,卡片看起来像死胡同。
- **板上直操作**:徽章卡底部「列入 Queue」(走既有 `POST .../cards/{ref}/move`
  `{target_section: Queue}`,落到 Queue 列尾)与「标记 Done」(走既有
  `POST .../done`)。点击不打开详情卡;点卡片其余区域仍开详情(那里还有
  移至 Doing)。徽章仍不是列,仍不进拖拽排序。
- 测试:vitest ProjectsPage 新增 1 例(Queue/Done 请求体 + If-Match + 不改
  `?task=`)。无新增依赖。

## 大事记(编年视图)边界契约(2026-09-25 定稿)

视图切换第三档 `?view=story`,实现见
`src/nblane/web_ui/frontend/src/components/projects/ChronicleView.tsx` +
`chronicleMath.ts`(纯函数:行划分 / 双向 x 映射 / 断轴压缩 / 事件收集 /
标签碰撞 / URL 状态)。

**与时间轴的分工:时间轴是规划(可拖拽改排期、泳道分项目、里程碑与撞期
预警),大事记是回放(全状态同轴、只读)。** 两者数据全量相同(queue /
doing / done / someday / 归档任务与归档项目),只是读法不同;大事记不做
任何编辑,点击事件只出铭文卡(任务名 / 项目 / 起止 / 状态),卡内
「去编辑」跳 `?view=kanban&task=<id>`。

形态规则清单:

- **S 形牛耕式**:按行排布,最新在上(第 1 行含今天),行序越往下越久远;
  方向交替——偶数行(0/2/…)镜像、最新日期在左(右→左读),奇数行左→右读。
- **每行一条横轴,五种笔法**:done=月白竖刻点(完成日,刻点顶部带**项目图形**
  glyph——确定性 hash project_id → ●◆■▲★✦◈✚ 之一,月白同色系只用形状区分,
  归档淡色,未归属无图形,与文字徽章双通道);doing=描金短条
  (started_on→today,淡金填充);queue=虚框短条(planned 区间,dim 虚线);
  someday=金色虚线圆点(期望激活日,planned_start<=today 过期转朱砂);
  **断轴**=**任何** >21 天无事件区间都压缩为 34px 的 `///` 块——事件之间、
  窗口前导/尾随空区都算;整行全空塌缩成 ~20px 的「/// N天」断行,合法全空
  窗口呈现为断行/断块链而非空白带。hover 显示区间与天数,点击展开(会话态,
  不记忆);断轴可跨行,每行各自截断渲染。
- **行间弯头**:细线 SVG path 连接上一行最老端与下一行最新端(同侧),
  竖直段中央一个朝下小箭头(dim 金),左右留 ≥10px 安全边距不裁切。
- **日期锚点**:行两端各一个(YY-MM-DD,dim),内移避免裁切。
- **标签**:每个事件两行(任务名+日期),地图标注式碰撞布局,**上 2 层 +
  下 2 层**四条标签带(层距 ~24px,行高随之涨到 148px)——降级链:同层 →
  对侧同层 → 上/下第二层 → 标题截断(≥6 字保首) → 缩字号(地板 8.5px) →
  仍挤不下聚成「+N」chip(hover 列出全部名字,不静默消失;chip 自身也做
  碰撞+外移扫描);标题前
  项目徽章 `[VLA]`(≤4 字,金色;归档淡一档),徽章可点击=只看该项目(单选,
  再点取消)。**同日完成的多个 done 按 started_on 先后扇排**:最早开始的
  坐在完成点上,其余按序向两侧外推(±10px 步进,无 started_on 排最后,
  翻转行镜像),保证每个都可点。
- **今天**:所在行内朱砂三角 + 「今天 MM-DD」标签(作为固定上方参与者
  进入碰撞布局,其他标签避让)。
- **无**里程碑、**无**斑马纹、**无**行内地色块(回放不搞规划语义)。
- **行数自适应**:行数 = 可用高度 ÷ (行高 120px + 弯头 36px),最少 1 行。
- **滚轮**:垂直滚轮 = 时间平移(向下滚=向过去,行整体上移,更早的行从
  底部长出;大事记独占纵向滚轮,不链给页面);Ctrl+滚轮 = 缩放,改变每行
  跨度天数(默认 90,范围 7~365),锚定鼠标所在日期(保持其行号与行内
  时间比例)。
- **URL 状态**:`view=story` + `cspan`(每行跨度)+ `ctop`(顶行最新日期)
  + `cproj`(筛选,仅收窄时写),replace 写入,刷新/分享可还原。
- **筛选**:工具栏 MultiSelect 与时间轴共用 localStorage key
  (`nblane.timeline.projects`),两视图筛选一致;归档项目与时间轴一样免疫
  MultiSelect;「重置视图」恢复 90 天/行 + 锚定今天 + 全项目并清除存储。
- **键盘导航(2026-09-26)**:焦点序 = 蛇形阅读顺序(最新→最久:行序 +
  行内 newest-first,+N chip 成员是独立节点;跨行长条按最新行去重)。
  ←/↑/k = 向现在,→/↓/j = 向过去(沿阅读路径,与首页星图同义),首尾钳制;
  无选中按任意方向键选中第一个(最新);选中态描金高亮 + 自动滚动到可见;
  Enter 开铭文卡,Esc 取消;键盘挂在画布容器(tabIndex),点空白处选中
  最近事件并接管焦点。
- **上下文小窗(inspector,2026-09-26)**:选中时出现、固定右下浮层(石刻风
  ground 底 + 细金边,半透不挡轴),无选中自动收起;内容 = 当前事件迷你
  铭文卡 + 阅读顺序前 3 / 后 3 邻居行(图形+任务名+日期,当前行高亮),
  点邻居行跳选;顶部一行键位提示。
