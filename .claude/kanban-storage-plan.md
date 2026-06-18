# 看板存储与原生编辑修复方案

## 根因总结
1. **focus mode 不记忆**：`3_Kanban.py:2267` 硬编码 `value=False`，仅存 session_state，无持久层。
2. **每次 save / 加 subtask 都弹 reload + 编辑丢失**：`assert_files_current`（为「手动保存的单文件编辑器」设计）被用在「每次交互自动保存」的 React 看板上。快照跨页共享（page 3/11 同守 `kanban.md`+`project-board.yaml`），任何外部写入（另一页、AI agent）都让快照过期 → 每次保存判冲突 `st.stop()`。`project-board.yaml` 被纳入守卫属误伤（sync 本就重新读盘、只更 task_refs）。
3. **原生新建不完善**：`quick_add` 只接受 title，无法建时填背景/备注。编辑面板字段其实已齐全。

## 决策（已确认）
- 冲突策略：**看板自动保存、不再硬拦截（last-write-wins，保留 git_backup 留痕）**
- 偏好记忆：**持久化到 `web-preferences.yaml`**
- 编辑：**新建可填背景/备注 + 自动填时间 + 编辑面板补全（面板已齐，重点补 quick-add 与时间可见性）**

## 改动清单

### A. 看板自动保存不再硬拦截（根治 reload 反复弹 + 编辑丢失）
**`pages/3_Kanban.py::_auto_save`（L152-168）**
- 删除 `assert_files_current([path, project_path])`（L159）这一硬停。
- 保留 `save_kanban` + `sync_project_board_from_kanban` + `refresh_file_snapshots` + git_backup。
- 即：看板写盘走 last-write-wins，git_backup 仍逐次提交可回溯。

**`_auto_save_subtask_toggle`（L244-304）**
- 去掉冲突重试/`st.warning(kb_drag_stale)` 分支里因 `assert_unchanged` 抛错导致的「放弃保存」路径，
  改为：仍以「读最新盘→合并这一次勾选→写回」的方式（已有 merge 逻辑），但冲突时**不再丢弃**，
  而是合并后直接保存。保留 2 次尝试的乐观循环作为并发兜底。

**工具栏「Reload」按钮（L2285）**
- 保留，但补一句 help/确认语义，避免和「自动保存」混淆（它是「丢弃本地、拉磁盘最新」）。
  仅文案 + help，不改行为。

### B. focus mode / auto_dates 持久化到 web-preferences.yaml
**`src/nblane/core/web_preferences.py::normalize_web_preferences`（L144-147 kanban 段）**
- 在 `kanban` 段白名单加两个布尔：`focus_mode`、`auto_dates`（默认 auto_dates=True、focus_mode=False）。
- 需要一个布尔清洗 helper（仿 `_clean_text`），缺省回退默认值。

**`pages/3_Kanban.py`（checkbox L2261-2272）**
- 读：初值从 `load_web_preferences(selected)["kanban"]` 取，喂给 checkbox 的 `value=`。
  注意 Streamlit checkbox 有 `key` 时 `value` 仅作首帧默认；用「session 无此 key 时以 prefs 初始化 session_state」的写法。
- 写：checkbox 变化时 `update_web_preferences(selected, {"kanban": {...}})`（其内置 changed 比较，无变化不写盘）。
  用 `on_change` 回调或比对后调用，避免每帧写盘。

### C. quick-add 支持背景/备注 + 时间自动填可见
**前端 `kanban_board_component/frontend/src/index.html`**
- quick-add 表单（L1388-1394）：在 title 输入旁增加一个「展开更多」切换，展开后显示 `context`(背景) 与 `notes`(备注) 两个 textarea。
- 提交事件（L1500）：`emit("quick_add", { section, title, context, notes })`。
- 新增 label：`quick_add_more`(更多)、复用已有 `context`/`details` label。

**`pages/3_Kanban.py::_handle_board_event` quick_add 分支（L1740-1757）**
- 读取 `payload.get("context")`、`payload.get("notes")`，建任务时 `replace(task, context=..., details=split_kanban_details(notes))`。
- 时间自动填：现有逻辑已对 Doing→started_on、Done→completed_on 生效（L1749-1754），确认 auto_dates 默认 True 后体验即到位。

### D. i18n
- `common.yaml`（zh/en）补 quick-add 的 `kb_quick_add_more` / 背景/备注占位文案；Reload 按钮 help 文案。
- 前端 DEFAULT_LABELS 同步加默认英文。

## 测试
- `tests/test_kanban_ai.py` / 新增用例：`apply_kanban_card_update` 已覆盖 title/dates/notes，不动。
- 新增 `tests/` 用例：
  - web_preferences 归一化保留 `kanban.focus_mode/auto_dates` 布尔，缺省回退。
  - quick_add 事件携带 context/notes 时任务字段正确落地（在 `_handle_board_event` 可测的纯函数层，或抽一个 helper）。
- 回归：`test_personal_workspace.py`（含 file_state 守卫）——确认删除看板硬守卫后该测试仍针对其它编辑器、不回归。
- 前端 `index.html` 无单测框架则人工验证。

## 部署
- 改了 `web_shared.py`？本方案 **不改** web_shared，只改 page/前端/core，Streamlit 仍需重启 18503（page 文件改动通常 rerun 即可，但 import 的 core 模块改动要重启）。dev 先验证，再 git → 生产 pull → 重启 `nblane.service` + `nblane-reader.service`。
- 前端 index.html 改动：确认组件是否需要构建（此组件是单 html，无构建步骤，直接生效）。

## 风险
- last-write-wins：多端同时编辑同一 profile 看板时后写覆盖先写。可接受（git_backup 留每步提交可回溯），且看板本是单人高频编辑场景。
- 其它页面（如 page 11）仍保留冲突守卫，不受影响。

---

# 项目驱动建任务（Project Board, page 11）

## 需求与根因
建完项目后以「项目驱动」连续建任务是核心动线，但当前不顺：
1. **入口深**：选项目 → 切 `Milestones & tasks` tab → 展开折叠的 `Create task` → 填 → 提交（`11_Project_Board.py:926-927`）。
2. **建完看不见**：page 11 不显示项目任务列表，只显示 milestone 完成度计数（`:816`）。任务实体在 Kanban(page 3)，闭环断裂——本页建完看不到，须跳页。
3. **milestone 无就地建**：`Create task` 有 milestone 下拉，但每个 milestone 卡片自身无「+建任务」。
4. **整页 rerun + 冲突守卫**：建任务 `st.rerun()` 且带 `assert_files_current`（`:978`），易弹 reload、丢滚动。

## 决策（已确认）
- 优先级：**先把建任务入口提到显眼处**（最小最快），其余分期。
- 冲突策略：**建任务跟看板一致，放开守卫（last-write-wins，保留 git_backup 留痕）**。

## 改动清单

> 进度（2026-06-18）：**P0 / P1 / P3 已完成并在 dev(18503) 验证**；P2 待做。

### P0（已完成）入口提显眼 + 放开守卫
**`pages/11_Project_Board.py::_render_create_task`**
- 入口：表单提到 `Milestones & tasks` tab 顶部，`expanded=not has_tasks`（无任务时默认展开，建完自动收起）。
- 放开守卫：删除 `assert_files_current([_kanban_path])`；保留「读最新盘→`_case_by_id` 校验项目仍在→append→save」。
- 保留 `save_kanban` + `sync_project_board_from_kanban` + `stash_git_backup_results` + `clear_web_cache` + `refresh_file_snapshots`。

### P1（已完成）建完能看见：项目任务列表内联
- 新增 `_render_project_tasks`：按 `KANBAN_SECTIONS` 顺序列出该项目任务（owner=project_id 或 case.task_refs），每行显示标题 + milestone 标签，右侧 selectbox 改 section 即时保存。
- 新增 helper：`_case_task_ids` / `_case_tasks_by_section` / `_move_task_section_and_refresh`（移动时 Doing→started_on、Done→completed_on/done，last-write-wins）。

### P2（可选，待做）milestone 上就地建任务
- 每个 milestone expander 内加「+建任务」，预填该 milestone_id，复用 P0 表单逻辑。

### P3（已完成）fragment 化
- 新增 `@st.fragment _milestones_tasks_fragment(case_id)`：内部重新 `load_project_board`/`_case_by_id` 取最新数据，包住 create-task + 项目任务列表 + milestones。
- 建任务 / 移动任务 / 存 milestone / 加 milestone 的 `st.rerun()` 改为 `st.rerun(scope="fragment")`；成功提示由 `st.success` 改 `st.toast`（fragment 重跑后仍可见）。
- tab[0]（项目表单 / 归档）保持整页 rerun 不动。

## 测试
- `test_project_board / _sync / kanban_io` 28 项通过；`py_compile` + i18n YAML 校验通过。
- 待补：建任务/移动任务的纯函数层用例（`_move_task_section_and_refresh` 的 section 移动 + 日期落地）。

## 部署
- 改了 page 11 + i18n YAML。i18n 是 `@lru_cache`，新 key 需**重启** Streamlit 才生效（已在 dev 重启验证）。
- 上生产：git → 生产 pull → 重启 `nblane.service`（+ reader 若涉及，本次未涉及）。
