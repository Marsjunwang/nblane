---
status: complete
owner: 王军 + AI agent
last_verified: 2026-09-16
source_of_truth: AI native 改造的计划、决策、进度与中断恢复;改造已于 2026-09-16 收官,最终行为以 docs/zh/guides/ 为准
---

# AI Native 改造开发日志

> 本文件是中断恢复的**唯一权威记录**。每次阶段推进后必须更新
> "进度日志"与"范围状态";恢复时先读本文件,再继续下一个未完成项。
> 注意遵守 docs 纪律:本文件是开发日志,不是长期 workplan;改造完成后
> 结论应沉淀回 `docs/zh/guides/` 与 `docs/zh/architecture/`,本文件可归档。

## 背景(2026-09-16 讨论结论)

- 目标:让首页(Daily Dashboard)和看板(Kanban)成为 AI native 工作台。
- 智能公式:**智能 = 模型能力 × 上下文质量 × 闭环设计 × 记忆积累**。
  模型/agent CLI 可买(千问 API、Codex CLI、Kimi CLI、OpenClaw),
  上下文 + 闭环 + 记忆必须自建——nblane 的文件制 profile 是地基。
- OpenClaw 定位:**常驻 agent runtime / 消息渠道层**(手+嘴),
  通过 `nblane-mcp`(MCP stdio server)读 nblane 上下文,
  通过 `agent-tasks.yaml` / `agent-activity.yaml` 走派单-审批闭环。
  nblane 不做自己的 coding agent,做自己的上下文编译与编排。
- 现状痛点(代码证据):
  1. 首页是只读展板:galaxy 节点点击不回传 Streamlit
     (`home_dashboard_component/frontend/src/main.jsx` `handleSelectNode`),
     右栏统计卡不可操作;`dashboard.graph_insights` 在 `app.py` 的
     `_DASHBOARD_AI_ACTIONS` 注册但无事件无处理(空壳)。
  2. 看板每个事件 → `_auto_save` → `st.rerun()`(约 15 处),
     AI 提案要 spinner → 整页重跑 → 重注入 ai_state。
  3. ~~任务 ID 是内容哈希~~(**P1 已修**:随机 UUID + materialize 固化)。
  4. ~~保存是 deliberate last-write-wins~~(**P1 已修**:
     `core/kanban_merge.py` 快照检测 + diff/replay 合并)。
  5. Human+Agent 闭环零件齐(`core/agent_tasks.py` 派单、
     `pages/9_Agent_Activity.py` 审批、crystallize → evidence),
     但看板卡片无派单入口、首页无待审批队列。

## 范围与落地顺序

- [x] P1 看板:任务稳定 UUID + 保存冲突检测(2026-09-16 完成,子代理 A):
      `kanban_io` 改随机 UUID(`kb_`+uuid4[:12],板内查重,编辑后 id 不变)+
      `materialize_kanban_task_ids` 固化存量;新模块 `core/kanban_merge.py`
      (diff/replay 字段级合并,快照比对,丢弃语义明确);页面维护
      `kanban_base_{profile}`,合并提示 i18n;修复 evidence 链路 3 处
      哈希依赖;12 个 merge 新测试;全量 1015 passed。
- [x] P2 看板:AI 流程异步化(2026-09-16 完成,子代理 A):
      `core/kanban_ai_tasks.py` 注册表(同 ai_stream_tasks idioms;
      超时后迟到结果被丢弃,修正了旧模式缺陷)+ `kanban_ai_jobs.py`
      Streamlit 胶水(sections 冻结快照、backend 后缀 key、搬运后
      refresh_file_snapshots);三 AI 分支去 spinner;`st.fragment(run_every=1)`
      仅在有任务时挂载;卡片 pending 呼吸 pill + 菜单禁用;
      discard 可取消;18 个新测试;另修复 P1 遗留 en/kanban.yaml
      引号 bug。全量 1047 passed。
- [x] P3 看板:卡片"派给 agent"闭环(2026-09-16 完成,子代理 A):
      `KanbanTask.agent_task_id` 新字段(round-trip 无损)+
      `agent_tasks.dispatch_agent_task_for_kanban`(每次新 id,
      related.kanban_task_id 关联,同步建 Activity 跟踪项)+ 组件卡片
      内联派单区(harness/role/instruction)+ 状态徽标(candidate_ready
      可点,复用 open_activity_item 跳审批页)+ `agent-tasks.yaml` 纳入
      快照清单;NL quick-add 复用 `command_bar.kanban_task_from_intent`
      字段映射(evidence.capture 在看板侧只引导不写入,保持单一通道);
      闭环集成测试 `tests/test_kanban_agent_loop.py` 五步链每步断言文件;
      另修 `review_actions._mark_done_crystallized` 用 dataclasses.replace
      (原逐字段重建会丢新字段)。全量 1076 passed。
- [x] P4 首页(2026-09-16 完成,子代理 B):Daily Brief(启发式
      `core/daily_brief.py` + LLM 增强,模块级缓存含失败缓存,
      privacy-safe)+ "待你决策"队列(agent-activity pending / health /
      evidence 均可跳转);`dashboard.graph_insights` 空壳 →
      `dashboard.daily_brief` 真接线;React banner + native fallback;
      9 个新测试;docs dashboard/web-ui 已同步。
      P5 接线建议已留(ContextHeader 加 command bar,事件
      `command_bar_submit`,见下方"P5 设计要点")。
- [x] P5 NL 意图入口(2026-09-16 完成):`core/intent.py`(主线,启发式
      离线解析,20 测试)+ 首页 command bar(子代理 B:
      `core/command_bar.py` 承载逻辑,写类意图确认卡确认后落盘,
      kanban 写入走 `save_kanban_with_merge` union 合并,due 进 details、
      started_on 仅 Doing;`command_bar_submit/confirm/discard` 事件;
      前端 CommandBar 组件已重建;15 测试)+ intent.py 四条覆盖修复
      (英文 add X to Doing 残留 to / by Friday·next Monday 英文日期 /
      「加到看板」页面名词漏标题 / 上周总结·周报触发但「写周报」不误捕;
      下周X 改为"下周一为锚"的正确算法)
- [x] P6 OpenClaw 接入(2026-09-16 完成):`core/mcp_client_config.py`
      (新建,解析 nblane-mcp 命令/env,单 profile 自动预填)+
      `nblane sync-agent-harness --target openclaw [--profile]` +
      `tests/test_mcp_client_config.py`(7 个测试)+
      `docs/zh/guides/openclaw-integration.md`(定位/订阅建议/接入步骤/
      闭环工作流/安全边界)
- [x] 终验(2026-09-16 完成):全量 **1076 passed / 11 subtests**;
      `test_kanban_component_read_mode` 2 passed;两个组件前端均已重建;
      validate OK(11 个存量数据 warning);status / import smoke OK;
      **CLI 闭环演示**:临时 NBLANE_ROOT(/tmp/nblane-loop-*)上
      建卡(kb_7e135472d02e)→ 派单(agenttask_…,status ready +
      Activity 跟踪项)→ submit_agent_task_candidate(candidate_ready)
      → update_activity_status(applied)→ Done+crystallized →
      evidence proposal(kind=new, kanban_refs 指回原卡)逐步走通,
      kanban.md / agent-tasks.yaml / agent-activity.yaml 文件级证据齐全。

## 决策记录

- D1 不靠换模型/换 CLI 求智能;投资上下文编译、闭环、记忆(2026-09-16)。
- D2 OpenClaw 作 runtime/渠道层接入,nblane 保留上下文与闭环主权;
  Kimi Pro 网页会员不接入(API/Coding 套餐才行),ChatGPT Plus 可经
  Codex OAuth 接入 OpenClaw。
- D3 Daily Brief 启发式模板优先(离线可用、可测试),LLM 只做增强;
  按 payload 指纹 + 日期缓存,避免 Streamlit 频繁 rerun 重复调 LLM。
- D4 闭环保持 human-in-the-loop:agent 回写必须经 Agent Activity 审批,
  crystallize 由人触发;不做自动改看板 Done。
- D5 看板任务 ID 从内容哈希改为创建即写随机 UUID(**P1 已实施**:
  `kb_`+uuid4[:12] 板内查重;存量经 `materialize_kanban_task_ids` 固化;
  evidence `kanban_refs` 等引用点已逐一排查,3 处修复、其余只读无需改)。

## 基线(2026-09-16)

- git: `main` @ 947e605,工作区干净。
- 环境:Python 3.12.3(.venv)、pytest 9.0.3、node v18.19.1、npm 9.2.0。
- 组件构建:看板 `src/nblane/kanban_board_component/frontend/build.mjs`
  (拷贝 src/index.html → static/);首页 `home_dashboard_component/frontend`
  为 Vite+React(`npm run build`)。改前端后**必须重建**,
  `tests/test_kanban_component_read_mode.py` 会校验 static 与 src 一致。
- pytest 基线结果:**982 passed, 11 subtests passed, 19.89s**(全绿)。

## 进度日志

### 2026-09-16

- 创建目标与 TodoList;基线检查通过(git 干净、工具链正常);
  全量 pytest 后台运行中。
- 建立本日志。
- 启动子代理 A(看板 P1)与子代理 B(首页 P4),后台并行。
- P6 完成:`core/mcp_client_config.py` + `sync-agent-harness --target openclaw`
  + `docs/zh/guides/openclaw-integration.md`;新增 7 个测试,
  全量 989 passed / 11 subtests;`--target codex` 回归正常。
  设计要点:OpenClaw 官方托管 `mcp.servers` 配置键(clawdhub.mintlify.app/zh-CN/cli/mcp),
  故片段直接产出该结构;`nblane-mcp` 不在 PATH 时回退 `python -m nblane.mcp_server`。
- P4 完成(子代理 B):`core/daily_brief.py` 新建(启发式+AI 增强+
  失败也缓存)、`dashboard.daily_brief` 替换 graph_insights 空壳、
  DailyBriefBanner + 待你决策队列(agent_activity/health 条目)、
  前端 vite 重建、9 个新测试;全量 **1015 passed**。
  详见 git 工作区与上方范围清单。看板线(A)仍在 P1 收尾。
- P1 完成(子代理 A):稳定 UUID + `core/kanban_merge.py`(diff/replay
  字段级合并;无 base 时退化 union;丢弃=外部删除赢,warning 列出);
  `materialize_kanban_task_ids` 修复 evidence 链路 3 处 id 不稳定依赖;
  12 个 merge 测试;全量 1015 passed。`.claude/kanban-storage-plan.md`
  仍有"id 内容哈希"旧描述(计划文档,暂不动)。
- P2 启动(resume 子代理 A)。A 交接的 P2 实施要点(恢复时照此核对):
  事件 handler 三分支(request_gap/request_subtasks/confirm_subtask_alignment)
  改启动后台任务;注册表模式参照 `core/ai_stream_tasks.py`;后台线程
  禁碰 session_state;结果由前台 fragment 搬运进既有
  `_subtask_alignments_key/_subtask_proposals_key/_gap_results_key/_subtask_errors_key`
  (下游零改动);后台写 ai-runs/agent-activity 后前台必须
  refresh_file_snapshots;key 带 backend 后缀,任务亦按 backend 区分。
- P5 核心完成(主线):`core/intent.py` 启发式解析器(kanban.add /
  evidence.capture / review.weekly_summary / navigate / unknown;
  中文日期:明天/周五前/下周三/10月1日/ISO;#tag;Doing/Queue/Someday
  列识别),`tests/test_intent.py` 14 个用例全绿。
  接线拆分:首页 command bar → 子代理 B(resume);看板 quick-add →
  子代理 A 完成 P2/P3 后顺带做。
- P2 完成(子代理 A):见范围清单。关键事实(恢复时用):
  `core/kanban_ai_tasks.py`(注册表,start_job/snapshot/cancel_job/
  cancel_jobs_for_kanban_task/drop_job/cleanup;env
  NBLANE_KANBAN_AI_TIMEOUT_SECONDS 默认 600)+ `kanban_ai_jobs.py`
  (页面胶水);卡片 pending 经 `_board_ai_state.pending_by_task` 透出。
- P3 启动(resume 子代理 A):派单闭环(dispatch_agent_task_for_kanban
  → KanbanTask.agent_task_id → 徽标回流 → open_activity_item)+
  闭环集成测试(tests/test_kanban_agent_loop.py 五步链)+
  看板 NL quick-add(接 core/intent.py)。
- P5 首页侧完成(子代理 B):`core/command_bar.py`(resolve_command_text
  纯路由不写盘 / pending_intent_payload / apply_kanban_add_intent 唯一写路径
  → save_kanban_with_merge(base=None))、app.py 三事件分支、前端
  CommandBar(ContextHeader 内,canEditGoals 门控)、i18n 14 键、
  15 测试;全量 1062 passed。evidence.capture 复用
  `_capture_home_research_source`(capture_event="command_bar" 标记来源)。
- P5 补丁(主线):intent.py 修 B 交接的 4 条观察 + `_weekday_date`
  「下周X=下周一锚定」算法修正;20 个 intent 测试全绿,全量 1068 passed。
- (用户支线)评估了 /home/ubuntu/kimi-goal-runner:机制可行(dev log 即
  恢复源),但 run.sh 缺 `--auto`(headless 会卡审批)且 rg 不在 PATH
  (quota 检测失效);已建议修复与启用时机,待用户决定。
- P3 完成(子代理 A):见范围清单。闭环五步链集成测试
  `tests/test_kanban_agent_loop.py`;全量 1076 passed。
- **终验完成(主线)**:全部验收标准达成,详见范围清单"终验"条。
  改造收官。后续可选:galaxy 节点点击事件/折叠(P1 时定为 stretch,
  未做);OpenClaw 实体安装与订阅是用户侧动作;kimi-goal-runner 补丁
  (--auto、rg→grep)待用户确认后打。全部改动未提交 git(按规则),
  由用户决定提交时机。

## 中断恢复指南

### P5 设计要点(来自子代理 B 的交接,实施时照此接线)

- command bar 放 `main.jsx` `ContextHeader`:次目标 rail 之下、
  `hd-context-actions` 之上,单列全宽 input;用 `canEditGoals` 门控
  只读模式;事件 `command_bar_submit {text}`,确认/撤销配
  `command_bar_confirm/discard {intent_id}`;payload 增加
  `payload.command_bar = {enabled, placeholder_key, pending_intent}`。
- `core/intent.py` 产出 kind 枚举(`kanban.add_doing` /
  `evidence.capture` / `review.weekly_summary` …),写类意图一律经确认,
  建议落成 agent-activity candidate 接入"待你决策"闭环;LLM 消歧可复用
  `dashboard.daily_brief` 的 gateway 注册+缓存+静默回退路径。

## 中断恢复指南

1. 读本文件的"范围与落地顺序"找到第一个未完成项;
2. 每条线的关键文件:
   - 看板线:`pages/3_Kanban.py`、`src/nblane/core/kanban_io.py`、
     `src/nblane/core/kanban_ai.py`、`src/nblane/core/agent_tasks.py`、
     `src/nblane/kanban_board_component/frontend/src/index.html`、
     `tests/test_kanban_*.py`
   - 首页线:`app.py`、`src/nblane/core/home_dashboard.py`、
     `src/nblane/home_dashboard_component/frontend/src/main.jsx`、
     `src/nblane/i18n/{en,zh}/home.yaml`、`tests/test_*dashboard*.py`
   - 意图线(P5):`src/nblane/core/intent.py`(新建)
   - OpenClaw 线(P6):`src/nblane/mcp_server.py`、
     `src/nblane/commands/agent.py`、`docs/zh/guides/openclaw-integration.md`(新建)
3. 验收命令:`.venv/bin/pytest -q`、
   `python -m nblane.cli validate`、`status`、
   `python -c "import nblane.kanban_ui, nblane.core.profile_ingest"`。
4. 铁律:不得读写真实 profile(`profiles/alice`、`profiles/王军`);
   测试用 `tmp_path` 隔离;新 UI 文案进 i18n(en+zh 双份);
   改组件前端后必须重建 static。
