---
status: active
owner: 王军 + kimi
last_verified: 2026-09-23
source_of_truth: 首页星图编辑与导航设计(重刻铭文/星表/大事记);实现见 src/nblane/web_ui/frontend/src/starmap/ 与 web_api/routes_v1.py
---

# 首页星图编辑设计:重刻铭文 · 星表 · 大事记

2026-09-23 与王军逐条对齐定案。哲学:首页是居所(观赏+仪式),编辑是重刻(稀有、
庄重),管理是星表(完备、可靠)。第一眼是图,第二眼是卡,第三层是表。

## 1. 可见性:二元,只管公开产物

- 字段简化为「可公开 / 仅本地」一键开关,**只影响公开产物**(公开构建/拓片/分享)。
- openclaw 与本地永远看全文——agent 看不到真实北极星就不可能给出真实计划。
  已知并接受:agent prompt 会进云端 LLM(dashscope),北极星全文随之出本机
  (王军 2026-09-23 确认接受该暴露面)。
- 迁移:旧 `discreet` 档映射为「仅本地」;`brief` 字段保留(展示简称,非隐私机制)。
- 图面只写古星名(帝星/北极星/勾陈…),真实文字只在铭文卡——图面天然公开安全,
  未来公开构建直接放星图无需打码。

## 2. 重刻铭文:帝星与恒星的编辑

- 入口:点星 → 铭文卡(阅读态)→ 卡上「重刻」图标翻成编辑态。无独立编辑页。
- 帝星字段:全文 / 简称 brief / 可公开开关。恒星字段:标题 / 摘要 / 目标日期 /
  状态(进行中/暂停/完成)。
- 保存后星图原位刷新(ETag 失效),简报行联动。确认时"落印"动画收尾。
- **空态 = 虚位空星**:帝星未设时图心是空圈+微弱脉冲(虚位以待,环境化,无弹窗),
  点击直接进编辑态;初始化与日常修改是同一个动作。

## 3. 双通道选择

- 图上点选:稀疏时的优雅路径。
- **星表面板**(角落淡金「+」唤出,印章式设计):帝星 + 全部恒星分节列出
  (进行中/暂停/已镌刻),点条目 → 图盘定位该星并开卡。手机端主路径。
- **定位契约**(防 morph/旋转 bug):定位先冻结旋转(伸手即停);境态下先 morph
  回图态再定位;定位动画期间用户拖拽立即接管(用户手势永远赢)。
- Playwright 回归:旋转中定位 / morph 中定位 / 境态定位。

## 4. 已完成目标 = 刻痕星

- 完成的恒星**钉在转盘上**(石刻随盘转,相对盘面位置固定——数学上不可能与同盘
  星碰撞),熄灭金光与呼吸,月白 30% 亮度。「不动」指无动画,非脱离盘。
- 星表归入「已镌刻」节。
- backlog:年度级沉积后迁入外盘碑座名录(刻碑),现在不做。

## 5. 星图 = 全站导航枢纽

| 元素 | 铭文卡 | 动作 |
|---|---|---|
| 帝星 | north star 全文 | 重刻 |
| 恒星 | 目标详情+关联项目 | 重刻;跳项目泳道 |
| 星官 | 三态统计/在学技能/入座证据 | 去技能树(只读卡,编辑留在技能树页) |
| 行星 | 项目摘要+进度 | 去 /projects |
| 客星 | 证据铭文 | 去证据页 |

## 6. GoalsPage 删除

只读页,批量管理由星表吸收;导航少一项,删除不冷藏。

## 7. openclaw 分级授权(修正原"审批队列唯一入口")

- **删除**:仍需页面确认(收件箱/GUI)。
- **其他一切写**(改目标/调日期/打卡/重刻):对话中确认即可执行——微信里说
  "好"就是确认,形式不该比语义重。
- `agent-activity.yaml` 从审批队列退化为**留痕簿**:记录谁提议、哪句对话确认、
  执行结果。审计能力保留,交互不死。

## 8. 大事记(chronicle.yaml)

git 留的是噪音,拓片要叙事级事件。新增 `profiles/<name>/chronicle.yaml`
(append-only),由写端点自己落笔:重刻北极星、新增/完成/重命名目标、里程碑
达成、项目完成。每条 `{date, kind, ref, note}`。
消费者:拓片(年度叙事)、首页简报行("本月新增目标 1")、openclaw 复盘素材。

## 9. 后端契约

- `PATCH /profiles/{name}/north-star`:**外科手术式**写 SKILL.md identity 区
  (只碰 identity 行,不整文件覆盖;sync.py 生成块不受影响)。
- goals CRUD:`POST /profiles/{name}/goals`、`PATCH .../goals/{id}`(走
  save_goal_book + ETag/412 纪律)。
- 上述写端点同步追加 chronicle。
- 全部 mutation 幂等、可校验,人与 agent 共用同一写路径(§7)。

实现状态(2026-09-23 落地,与本节一致,两处细化):

- 北极星写入落在 `core/north_star.py::update_north_star`(SKILL.md flock +
  expected_snapshot + 412);可见性只接受 `public`/`private`,旧值读取时映射
  (§1),写只写 canonical 新值。no-op patch 不写文件、不记 chronicle。
- chronicle kind 当前实现 `north_star.rewritten` / `goal.added` /
  `goal.completed` / `goal.renamed`(rename 仅当 title 真变);里程碑达成、
  项目完成随各页写路径后续接入。`GET /profiles/{name}/chronicle?limit=`
  提供简报行读取(最新在前,带 ETag)。
- goals PATCH 的 status 只接受 `active`/`paused`/`completed`(archived 不入
  星表编辑面);goal id 为标题 slug(`goal-<slug>`),冲突追加数字后缀。

前端落地(2026-09-23 同日,`web_ui/frontend/src/starmap/`):

- §2 铭文卡重刻(`InscriptionCard.tsx`,帝星+恒星,卡内编辑态,落印动画)、
  虚位空星(空圈+慢脉冲,点击直进编辑态)、无目标时 R_GOAL 淡空圈虚位;
  §3 星表面板(`StarCatalog.tsx`,淡金「+」印章按钮,帝星/进行中/暂停/已镌刻
  分节,新增目标表单)+ `StarmapScene.focusStar` 定位契约(冻旋转/境态先回
  图态/拖拽接管);§4 刻痕星(CARVED_ANGLES 专座,灭金光,月白 30%);
  §5 联动卡(恒星→项目泳道,行星→/projects,客星→/evidence,星官补入座
  证据名录);§6 GoalsPage 删除(/goals → /home 重定向);§8 简报行大事记
  风味(`briefing.ts`,本月新立目标 N / 新镌 M 星)。
- 数据缺口绕法:/starmap 只回 active goals + 裸 north_star 字符串,前端
  用 GET /goals 合并(`mergeGoalBook`)拿全状态目标与权威 NorthStarModel。
- 已知后端 bug(待修,非前端):`profile_context.update_identity_fields_in_body`
  对空值铭文行的改写会损坏 SKILL.md(`:\s*` 吞换行,值落裸行)——虚位
  空星的首次落印被其阻塞,e2e `spa_home_editing.spec.ts` 标 fixme。

## 10. 明确不做

技能星官/行星/客星的编辑(各归其页)、刻碑名录(backlog)、修改日志 UI、
⌘K(随 IA 重设计)、Streamlit 侧任何改动(冻结)。
