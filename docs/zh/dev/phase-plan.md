---
status: active
owner: 王军 + kimi
last_verified: 2026-09-24
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
- Profile Health 页解散:证据风险→证据页「待补强」;数据卫生→Settings「档案维护」;体检报告→openclaw 周回顾主动推送;成长统计→首页/拓片。(SPA 页本体已删 2026-09-24,/health → /evidence?stage=strengthen,`GET /health` API 保留。)
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

### 项目页 HCI 宪法包(2026-09-23 落地,docs/zh/dev/phase2-projects-hci.md)

- 五项裁决全部前端落地:归档带就地展开(月白 40% 只读 + 恢复)、日课栏
  (一个习惯全站一行 + habit-plan 进度弧 + 90 天热力图补卡)、Queue 列顶常驻
  行内快添、时间轴历史层(kanban Done → 月白刻痕条,默认近 6 月视窗 + 脏日期
  钳制 + 最近半年/全部缩放)、抽屉删除三件套(后果预告 + 逐字确认 + 大事记默认不勾)。
- 首页左下「日课印」:`日课 锻炼○ 学习●` 印章,点名即打卡,悬停本周七点。
- 细节与取舍见 phase2-projects-hci.md「实施状态(前端)」;e2e
  `tests/e2e/spa_projects_hci.spec.ts`(隔离栈 + 王军真实数据,截图 /tmp/hci-shots/)。

### 项目页缺口闭合(2026-09-24 落地)

- **销印**:`DELETE /api/v1/profiles/{name}/checkins/{checkin_id}`(删一条打卡,
  不写 chronicle;flock + expected_snapshot + If-Match 412;未知 id 404);
  projects-board `habits[].recent_days[]` 增加 `checkin_ids` 供寻址;日课栏热力图
  实格点击 → 就地确认条 → 删当日最近一次,与补卡对称。首页 HabitSeal 已接线
  (见「工具页风格对齐 + 销印接线」节)。
- **任务编辑**:铭文详情卡编辑模式(标题/上下文/为什么/归属/标签,PATCH 只提交
  改动字段,kanban ETag 纪律);排期仍归排期行,不重复。
- 测试:pytest 1724(TestCheckinDelete 3 例新增)、vitest 229(销印/编辑 6 例新增)、
  tsc 绿;真人 QA 6 旅程全绿(vite dev 15173 → 隔离栈 18504,截图 /tmp/qa-shots/)。

### 习惯生命周期 + 技能进阶前端(2026-09-24 晚落地,跨 /projects·技能树·证据)

契约见 data-contracts.md「习惯生命周期」「技能进阶进度」「证据 breakthrough」;
本片为纯前端(后端契约同日并行落地,openapi.json + schema.d.ts 已随
gen:api 重生成,类型为 schema 别名)。

- **日课栏习惯生命周期**:纯习惯行悬停齿轮 → 归档(一键折起;「显示已归档」
  开关经 `?include_archived=true` 带回服务端归档行,弱显 + 恢复)/ 删除
  (后果预告 N 条打卡 + 逐字确认 + 记入大事记默认 OFF;422
  `habit_delete_confirm_mismatch` 行内报错)。详见 phase2-projects-hci.md 末节。
- **打卡点石刻化**:日课栏周点、时间轴习惯带、日课印浮条统一为 月白35% 空心环
  / 泥金实点 / 今日细金环;`habitGreen` 退役。
- **技能进阶进度(技能树页)**:节点铭文卡新增「进阶」块——当前阶 → 下一阶、
  score/threshold_next 泥金进度条、突破 ×N(>0 时);`progress.eligible` 时
  列表字形与境界 stepper 目标阶带柔金脉冲(`.nblane-eligible-pulse`,
  reduced-motion 关闭)并标「可进阶」。脉冲是纯提示,升阶仍走三态 PATCH。
- **证据突破标记**:详情卡 分量 旁「突破」开关(经 edit 端点
  `fields.breakthrough` "true"/"false" 字符串 round-trip),列表行显示 突破
  徽章;计分规则(突破 +1000)在 `core/skill_progression.py`。
  (注意:evidence-review 队列投影暂未携带 breakthrough——详情/条目列表
  投影有;徽章在投影补齐后即自动出现,前端已按可选字段渲染。)
- **未做**:首页星图(图态)eligible 星点脉冲——StarmapResponse 契约不含
  progress/eligible,需跨端点拼接并改 scene 逐点属性动画,超出「trivial」
  门槛且触碰冻结的场景语法;待后端把 eligible 折进 /starmap 聚合后再评。
- 测试:vitest 新增 9(日课栏 5、进阶 2、突破 2)全量 260;tsc 绿;pytest 零改动。

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

### 首页星图编辑前端(2026-09-23,设计 home-editing-starmap-design.md)

- 铭文卡重刻:帝星卡(全文/简称/可公开开关)+ 恒星卡(标题/摘要/目标日期/状态)
  卡内编辑态(`starmap/InscriptionCard.tsx`),保存走 PATCH north-star /
  goals 新端点,成功后「落印」印章微动画;失效重取 ['profiles',name,'starmap'
  /'goals'/'chronicle'],星图原位刷新。
- 虚位空星:北极星未设时图心渲染空圈+缓慢微弱脉冲,点击直接进编辑态;
  无目标时 R_GOAL 环留五个淡空圈虚位。空态判定以 GET /goals 的
  NorthStarModel 为准(`useStarmapEditingData` 合并聚合快照+目标书)。
- 刻痕星:completed 目标钉上转盘(CARVED_ANGLES 专座,随盘转),灭金光,
  月白 30%,标签转暗;暂停目标降为 55% 亮度。
- 星表面板:角落淡金「+」印章按钮唤出(斑蚀质感),帝星/进行中/暂停/已镌刻
  分节,行点击 → `scene.focusStar(id)` 定位开卡;「新增目标」行内嵌创建表单。
  focusStar 契约:冻结旋转(伸手即停)、境态先 morph 回图态、拖拽/滚轮即时
  接管(用户手势永远赢);超出 5 座上限的目标卡照开但不定位(catalog 兜底)。
- 联动卡:恒星卡跳项目泳道、行星卡跳 /projects、客星卡改跳 /evidence、
  星官卡补入座证据名录(只读,编辑留在技能树页)。
- GoalsPage 删除:nav 移除「目标」,/p/:name/goals → /home 保留 query 重定向。
- 简报行:追加大事记风味(本月新立目标 N / 新镌 M 星 / 北极星已重刻),
  取自 GET /chronicle?limit=40,基底简报保持主位。
- 场景点击守卫:React 同步重渲导致的事件目标节点脱离 DOM 时,window 级
  click 监听按 UI 点击处理(isConnected 检查)——否则重刻按钮会误触
  closeDetail。
- 测试:vitest starmap/briefing 新增 12 例(mergeGoalBook、刻痕星落位、
  chronicle 简报);e2e 新增 `spa_home_editing.spec.ts`(重刻 round-trip、
  星表定位、创建+镌刻、/goals 重定向、境态定位回归、移动底栏、虚位空星
  开通编辑态);spa_home/spa_mobile 同步更新。

### 星表交互 + 目标起始日期(2026-09-23,设计 home-starmap-enhancements-design.md §2/§3)

- **Esc = 一键回纯图,无分层**:StarmapView window keydown 兜底,任意态
  (星表/卡/重刻/组合)一次 Esc 全收;进首页永远纯图。
- **星表常驻**:行点击不再收回面板,右侧铭文卡实时更新;↑/↓(j/k)环绕移动
  高亮行,Enter 开卡;图上点星 → 星表行高亮 + 滚动到位(双向同步)。
- **快捷键提示**:行悬停才显 kbd;星表首次打开 2.4s 渐隐引导条(每会话一次)。
- **起始日期**:POST /goals 缺省 `start` 自动刻今日(显式 ISO 保留);PATCH
  接受 `start`(校验同 target,空串清除);重刻编辑态新增「起始日期」输入;
  历史空值不补刻(卡上仍显 —)。openapi.json/schema.d.ts 已重生成。
- 测试:pytest +2(test_web_api_home_editing);vitest +9(StarCatalog.test.tsx);
  e2e 新增 `spa_home_catalog_ux.spec.ts` 5 例(隔离栈 + 王军,截图
  /tmp/catalog-ux-shots/);spa_home_editing 同步去掉"行点击后重开星表"的旧断言。
- 已知后端缺口(前端已绕开/待修):/starmap 聚合仍只回 active goals 且
  north_star 为裸字符串(前端用 /goals 合并补齐);PATCH /north-star 对
  **空值铭文行**的改写会损坏 SKILL.md(_IDENTITY_BULLET_RE 的 `:\s*`
  贪婪吞掉空行尾换行,值落到裸行,解析仍为空,重复写继续追加)——虚位
  初立流程被此前端无关 bug 阻塞,e2e 中标 fixme。

### 星图增量:境态调参 + 图态命名层(2026-09-23 晚,设计 home-starmap-enhancements-design.md 实现状态节)

- **境态(deepspace)**:星等分层(逐云 deep 倍增器,北极星>目标>行星>客星>
  尘埃;底星幂律伪星等 ~5% 亮)、离散四档色温(蓝白/月白/暖金/淡橙,aColor
  按 ch2 渐变,图态色不动)、尘埃带弥散长河(径向渐变 sprite 垫层,密度随
  真实证据数)、背景视差-lite(底星 bgLayer 反旋,境态 0.3×/图态不动)、
  全面减速(目标 150s+/行星 100s+/客星 26s+ 周期,漂移 7→4;1h/圈不变,
  闪烁未动)。
- **图态命名层**:北斗七座位赐名(天枢…摇光,虚位=「名·虚位」空心,**不画
  连线、不动星位**);星官扇区=外环带竖刻古名 + 扇区内 asterisms.json 真实
  连线形(空圈蚀刻兜底,**形旁无字**);北极星图面只刻「北极星」;**显真**
  全局开关(真名泥金为主+古名月白注,localStorage `nblane.starmap.reveal`
  记忆,scene.setReveal 就地换层)。帝星→北极星重命名同步收尾(星表/重刻卡
  /详情行/fallback)。
- 偏差:翼/房/箕/轸/轩辕/虚 六官真形不在 asterisms.json(22 官),形状暂用
  模板,环带古名正确;补数据后 `SECTOR_ASTERISM` 一处即接上。
- 测试:vitest starmap +7(座位/映射/蚀刻/幂律/色板),全套 209 绿;tsc+build
  绿;pytest 1694 绿(零 .py 改动);隔离栈 18504 截图+境态帧序列
  /tmp/starmap-incr-shots/;checkpoint /tmp/starmap-incr-progress.log。

### 星图增量二轮(2026-09-23 深夜,王军裁定)

- **显真替换制**(废止主从反转):图上默认只有古名、显真只有真名,双名小注
  全撤(双名只留星表/铭文卡);外环带默认=星官名、显真=域名。
- **圆圈常显**:hover-only 提案被否(图面会秃),虚位/轨道/客星环维持常显。
- **星官名随形外移**:古名留在扇区内图形外缘之外,环带同款月白弱色小字
  (肌理级);显真态不显示。
- **形状筛选**:角宿(一线)/心宿(近共线)剔除,基础→华盖、研究→文昌;图形
  降透明度收紧尺寸(肌理层);vitest linearity 守卫(PCA 比 ≥0.18)。
- **印章家族成套**:显真方印(白文/朱文)+ 境/图竖印翻字,与星表「+」、
  日课印统一斑蚀篆刻语言(同纹理/边框/内双圈/悬停晕光,44px 模数);卜印
  未实现,归入同族待做。
- 测试:vitest 210 绿;tsc+build 绿;pytest 1694 绿;截图 r2-* 同目录。

### 星图增量三轮(2026-09-23 深夜二轮,王军规格)

- **日课印成章**:横条撤除,竖刻「日课」款 + 每习惯 44×44 单字印(文楷,
  自动取字+精选字表 炼/学/复/读/跑/坐/息),白文/朱文 = 未打卡/已打卡;
  点击打卡带钤印微动画(reduced-motion 关闭);悬停小笺(全名+连续+本周
  七点);**销印后端已到**:`DELETE /profiles/{name}/checkins/{checkin_id}`
  2026-09-24 上线(按 id 寻址,非 date?habit= 草案);日课栏热力图已接;
  HabitSeal 前端接线 2026-09-24 落地(见末节「工具页风格对齐 + 销印接线」)。
- **观瞻印组**:真印(44²「真」白/朱)+ 境/图方印(单字目标态翻印);卜印
  槽位注释在真印左(right:128px)。族规:44px 模数/斑蚀/细双圈/2px 圆角/
  悬停金晕,星表「+」对齐;移动端 ≥44px,小笺长按唤出。
- **图面**:扇区内星官小字删除(R3 撤销);星官图节点=小空圈细蚀;字级
  统一明体一梯(北极星/北斗=泥金,环带官名=月白 muted,虚位注再暗一档,
  简报行月白小字;北极星标签弃文楷)。
- 测试:vitest 213 绿(+3 sealGlyph);tsc+build 绿;pytest 1694 绿;截图
  r3-*(印章两态/小笺/打卡往返(e2e-zh 实证)/移动 390px)。

### 境态碰撞修正(2026-09-24,设计 home-starmap-enhancements-design.md 境态碰撞修正节)

- **境态=展开**:目标系径向散开车道化(58+座次×26,方位沿用盘座;刻痕星
  静道 60),车道间距 26 > 两系轨道半径和 → 任意相位不相交(vitest 不变量)。
- **行星轨道分级**:同目标行星分道(5+n×2.2≤12.6);自由行星走环极外道。
- **标签**:行星本无文字(维持);斗星名随展开外推 ×(1+0.9·ch2);碰撞按
  优先级淡出(极>斗名>虚位注,不跳不移位);**境态星名 upright**(标签反旋
  -chart·ch2,图态零影响——石刻随盘是本意)。
- **光晕收敛**:行星无独立 glow(糊块=环芯点+bloom),深态 tier 0.95→0.6,
  不透明度降 0.85 档。
- 测试:vitest 217 绿(+4 展开不变量);tsc+build 绿;pytest 绿(1721;期间
  捡了一条并行占卜线的测试欠账:test_ai_gateway 注册表断言补 divination.cast)。
  帧序列 r4-*(图态回归/morph 中段/境态 0/15/30/45s)逐帧目检无互撞。

### 星图五轮:境态第二层 + 占卜前端(2026-09-24,设计文档五轮节)

- **境态第二层**:大测绘圈 morph 早期消融(ch1);圈随星走(每行星道一条
  细暖金椭圆随目标星展开位,微光沿圈流转 46s/圈);星官点燃(图形锚定
  +z 抖动,空圈席位燃为实心小星,逐槽色温,蚀刻线 dip-and-return);
  行星时间弧实现但默认关(PLANET_TRAILS flag);尘埃带吸积盘式径向梯度。
- **占卜前端**(§5):卜印入右下印组最左;星尘聚卦仪式(canvas 尘粒聚向
  左盘区成卦,摇卦常活无死 spinner);卦辞卡左缘滑入停靠最左、卦旗居卡
  首;戏占|正占(空问不发);离线卦签;Esc 回纯图;移动端底部 sheet。
  修复:连续起卦清旧卦辞;移动端卜印 hit target 与日课印行重叠,印组上移
  一行。
- 测试:vitest 229 绿(+5 卦象渲染);tsc+build 绿;pytest 1724 绿;
  Playwright r5-* 全仪式帧 + 双模式 + Esc + 移动;规则兜底实证
  (NBLANE_DEV_ENV_FILE 死 LLM → source=rule 离线卦)。

### 星图六轮:境态残差漂移修复 + 图态归环(2026-09-24)

- **根因**:两处未按 ch3 门控的残差——goalNow 轨道旋转残差(相位出境态即
  冻结,展开车道把残差从不可见放大到数单位/轮)、planetNow 跟随项错用目标
  星 deep 基址(编组行星首载即位移,实测 t0 径向 16–78)。修复:轨道数学抽
  纯函数 `orbitPos`/`orbitPosAnchored`(残差 ×ch3,跟随项对照 morph 基址)。
- **图态归环**:行星 plan 全部正落 R_GOAL(角向偏移保留,径向 ±10 与游离
  +24 归零);deep 车道不变。
- 验证:探针实测修复前 玉衡 54→59.68/5 轮 → 修复后每轮恒 54;cycle 4 帧
  落境态读数恰为车道值(58…162/206)反证车道数学。vitest 246 绿(+6);
  tsc+build 绿;pytest 1728 绿;截图 r6-before/after-*。

### 技能树页三项升级:类目星官化 + 节点铭文卡 + 状态写端点(2026-09-24)

- **类目头星官化**:`GET /skill-tree` 新增 `categories` 卷积(zh 名取自
  `core.starmap_snapshot.CATEGORY_ZH`,lit=solid+expert);页面按类目分组,
  横幅刻星官小像(asterisms.json 真形,泥金 SVG,复用 starmap/layout.ts
  `SECTOR_ASTERISM_TABLE` + `asterismById`)+ 官名 + 三态统计 + 小传(lore
  单行);翼/房/箕/轸/轩辕/虚六个无真形域挂「拟形·模板」标记。
- **节点铭文卡 + 关联证据(G6)**:点击节点开右侧铭文卡(只读复用
  starmap `InscriptionCard` + starmap.css 铬件);`GET /evidence` 新增
  `skill_id` 过滤(evidence_usage_index 反查,与 status/q 正交),证据行
  深链 `/evidence?stage=<seated|review>&focus=<id>`(证据页新增 focus
  预选支持)。
- **技能状态写端点(G3)**:`PATCH /skill-tree/nodes/{node_id}`,三态词汇
  locked/learning/lit(lit 落 YAML `solid`;expert 评审授予不可写),
  ETag/If-Match + `update_skill_tree` 锁内快照,写后重写 SKILL.md 生成块;
  铭文卡三态步进器乐观更新 + skill-tree/projects-board/starmap 失效。
- 验证:vitest 251 绿(技能树页 9 例:横幅 2、铭文卡深链 1、步进器
  PATCH/If-Match/乐观更新 1,证据页 focus 深链 1);tsc 绿;pytest 新增
  PATCH 200/404/422/412/401 + skill_id 过滤用例;openapi.json +
  schema.d.ts 已重生成。



### 工具页风格对齐 + 日课印销印接线(2026-09-24 落地)

- **HabitSeal 销印接线**:右键/长按(coarse)朱文印 → 印行上方就地确认条
  (印章族样式:斑蚀底/细金边/明体,销印钮取朱砂色)→ `DELETE /checkins/{id}`
  删当日**最近一次**(recent_days[today].checkin_ids 末位,`todayCheckinId` 纯函数);
  成功后 projects-board 失效重取,印面回落白文。当日记录缺 id(历史遗留)时
  黄条提示不可销印,与日课栏热力图同契约;白文印右键无操作;Esc/取消收条;
  确认条打开期间悬停小笺关闭(防遮挡);长按后尾随 click 不再误打卡
  (suppressClick,顺带修了移动端长按小笺也会打卡的旧毛病)。
- **技能树页对齐星图语言**:节点四态换三态篆刻词汇——锁定=空圈、在学=实点、
  扎实/精通=点套圈(精通环取泥金,对应星图字级梯子最高档);汇总 chip 同字形;
  页面标题/正文 明体;节点列表收进铭文相邻面板(深底 `rgba(22,38,61,.55)` +
  细金边 `rgba(220,174,85,.22)` + 行间发丝金线);证据计数非零显泥金。
  纯换肤+层级整理,折叠/筛选/计数功能与 testid 全部保留。
- **证据页抛光**:五阶段导航从 Mantine Button 改为铭文相邻行(明体、active
  细金边+金底 10%、计数 tabular-nums);列表行/候选卡/风险卡/向导卡统一深底
  细金边;快评光标行从 Mantine yellow 改泥金虚线;强度徽章去绿/黄(reviewed=
  泥金 light,未评级=灰 outline);「接受」「入库」按钮 green→brand 泥金;
  详情卡沿用 InscriptionCard 不动。红色仅留语义(废弃/删除)。
- 测试:vitest 234 绿(+5:todayCheckinId 3 例、销印 round-trip/取消与右键白文
  2 例);tsc+build 绿;pytest 1724 绿(零 .py 改动);隔离栈 18504 Playwright
  实证:技能树/证据五阶段/销印往返(王军 exercise 销印后补回,数据净不变,
  id 确定性复用 act_20260924_exercise)/移动 390px 零横向溢出,截图
  /tmp/style-align-shots/。
### 生产上线 C 尾清理包(2026-09-24,production-launch-plan §2 裁决执行)

- **占卜「化为任务」桥**(§2.3 前置落地):正占卦辞卡新增「化为任务」——卦象
  锚定的 `anchors.gap.closure` 缺节点(is_gap)逐一顺序走既有
  `POST /gap/intake`(`学习 {label}` + node_id + why=所问,Queue)入看板;
  kanban/projects-board 双失效;成功后卡内小笺带 /projects 深链;失败就地
  报错可重试。`useGapIntake` 顺带补 projects-board 失效(该钩子随后随
  GapPage 本体一并移除,Divination 改为直接 `apiPost` + 内联双失效)。
- **GapPage 本体删除执行**(§2.3,2026-09-24):SPA `GapPage`(+ vitest
  测试)、`/p/:name/gap` 路由、nav「差距分析」与 `useGapAnalyze`/
  `useGapDeepAnalyze`/`useGapIntake` 钩子移除;e2e 删 `spa_gap_deep.spec.ts`、
  `spa_pages.spec.ts` 的 Gap describe 与 `spa_mobile.spec.ts` 抽屉项
  (11→10 个 profile 页入口),`audit_layout.mjs` 删 Gap 行。
  `POST /gap/analyze` 与 `POST /gap/intake` 端点保留(openclaw 与占卜
  「化为任务」在用);Streamlit `pages/2_Gap_Analysis.py` 随 8501 终态再退。
- **健康页解散执行**(§2.2):SPA `HealthPage`(+测试)与 nav「健康」删除;
  `/p/:name/health` 重定向 `/evidence?stage=strengthen`;档案列表卡片入口
  改指 `/home`;`useHealthReport` 钩子和 Health 类型导出随页移除;
  `GET /health` API 保留(openclaw/CLI 消费)。e2e:spa_mobile 抽屉项
  12→11、spa_smoke 档案卡落点改 /home、audit_layout 删 Health 行、
  spa_layout 新增重定向用例。
- **突破徽章队列投影**:`EvidenceReviewItemModel` + `_review_item_model` 补
  `breakthrough`(原始行透传);openapi.json + schema.d.ts 重生成;
  `EvidenceReviewItem` 类型去掉手工扩展;评审行「突破」徽章真正点亮
  (此前前端徽章已就位但投影缺字段)。
- **P2 打磨四条**:(a) 排期输入换 Mantine `DateInput`(valueFormat
  YYYY-MM-DD,locale=zh-cn)——原生 type=date 的显示格式跟随浏览器 UI
  locale,lang 属性实测(Chromium 探针)不影响渲染,locale attrs 路线证伪;
  (b) 标记 Done 在 mutation onSuccess 发「已标记完成」通知(卡片随 refetch
  自闭,通知须在回调里发);(c) 删除项目确认 Modal `zIndex={300}` 压过编辑
  Drawer(200 层),elementsFromPoint 实测命中顶层;(d) 未归属统计徽章对齐
  泳道口径(只计 queue/doing/someday),Done 列余量以「(含已完成 N)」明示,
  双数字不藏。
- **新增依赖**:`@mantine/dates@^8.3.18` + `dayjs@^1.11.23`(已登记
  packaging-manifest)。
- 验证:vitest 273 绿(+12:占卜面板 7、证据页突破 1、任务详情卡 2、
  项目页统计 2);tsc+build 绿;pytest 1795 绿(零新增测试文件,
  test_web_api_evidence_review 补突破投影断言);openapi 快照同步;隔离栈
  18504 Playwright 抽查 7/7(化为任务 9 缺口 9/9 入看板、health 重定向、
  突破徽章、四条 P2),截图 /tmp/c-tail-shots/,沙箱数据净不变(化为任务
  与临时卡已清、突破旗已还原)。已知边角「标题含 `/` 的看板卡无法经
  `DELETE /kanban/cards/{card_ref}` 寻址(路径参数 405)」已于当日修复:
  card_ref 改为 id 优先寻址(见 data-contracts.md「任务删除」)。



- **用户初始化链路优化**(2026-09-23 王军提出):现状是"简历 → LLM 解析 →
  robotics-engineer schema 骨架",非工程领域用户(如教师)不成立。方向:领域
  schema 模板库(工程师/教师/研究者/创作者)+ AI 按简历定制 skill-tree 草案与
  北极星候选 + 预览确认页;终点是"初始化仪式"——确认后首页星图当场亮起,用户
  点帝星亲手改定(接「重刻铭文」)。openclaw 可作对话式访谈入口(微信问答聊出
  北极星)。等工具层/IA 重设计后再排期。

## 已知风险登记

- embedding 端点是否存在待确认(无则 LLM 排序兜底)。
- openclaw 自动化已在生产运行(每日计划 08:30/每日复盘 21:30/每周整理,微信推送),声明在 openclaw workspace;nblane 侧 `assistant/automations.yaml` 从未部署——Phase 4 的核心是**把既有自动化与 nblane 数据双向接通**(MCP),而非从零创建。openclaw 本体(gateway 18789/MCP/CLI)本机可用。
- kanban.md 元数据契约脆弱,任何新写路径必须走 kanban_io。
- Streamlit 内多条写路径无快照保护(last-write-wins),迁移时以 API 纪律为准,不回移植坏习惯。
