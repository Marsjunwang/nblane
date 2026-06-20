# 项目板自研组件方案（Basics 面板 + Milestones 卡片）

## 目标
把 page 11 的「编辑基础信息」和「milestone」从 Streamlit 原生 form/expander/multiselect
换成一个自研前端组件，交互手感对齐看板（即时编辑、卡片化、chip 式引用多选），
**项目板专属视觉**（独立配色/卡片样式，不照搬看板）。任务拖拽列表本轮不做。

## 复用的现成架构（已确认）
- `kanban_board_component`：单 `index.html`（内联 CSS+JS）+ `build.mjs`（仅拷贝校验，无打包）。
- 协议三段式：`declare_component(path=static)` → 前端 `streamlit:render` 收 args / `setComponentValue` 发事件（带 `event_id`）→ Python 按 `event_id` 去重后 `action` 分发。
- 持久化全在 Python：`_sync_case_update_and_refresh` / `_sync_milestone_update_and_refresh` /
  `_sync_milestone_add_and_refresh` 已存在，直接复用，**不碰存储逻辑**。

## 改动清单

### 1. 新组件包 `src/nblane/project_board_component/`
- `__init__.py`：仿 `kanban_board_component/__init__.py`。
  - `project_board_component_available()` + `st_project_board(*, case, option_maps, labels, settings, key, height)`。
  - 入参：当前 case 字段快照 + 各引用候选 `{id: label}`（goal/task/evidence/source/experience/output）+ milestones 列表 + i18n labels。
  - 返回最近一次事件 `{action, payload, event_id}`。
- `frontend/src/index.html`：自研单文件（内联 CSS+JS），协议样板照抄看板。
  - **Basics 区**：title/status/kind/visibility/time_range/summary/notes 字段卡片；
    关联引用用 chip + 搜索下拉多选（替代 `st.multiselect`）。
  - **Milestones 区**：每个 milestone 一张卡片（标题/状态/target/summary + 完成度进度条 +
    task/evidence/source/output chip 多选）；底部「+ 新建 milestone」内联表单。
  - 视觉：项目板专属配色变量（区别看板绿色系），卡片化布局。
- `frontend/build.mjs` + `frontend/package.json`：仿看板（拷贝 src→static + 关键串校验）。
- `frontend/static/index.html`：构建产物（`npm run build` 生成）。

### 2. page 11 接入（`pages/11_Project_Board.py`）
- `_render_project_form` / `_render_milestones`：组件可用时走 `st_project_board`，
  事件交给新增 `_handle_project_event`；组件缺失则回退现有原生 form（旧函数保留为 fallback）。
- `_handle_project_event` 按 `action` 分发到已有持久化函数：
  - `save_basics` → 构造 `submitted_case` → `_sync_case_update_and_refresh`。
  - `save_milestone` → `_sync_milestone_update_and_refresh`。
  - `add_milestone` → `_sync_milestone_add_and_refresh`。
  - `archive_project` → 复用归档逻辑。
  - 引用类编辑随对应 save 一起提交（payload 带 refs 数组）。
- `event_id` 去重（新 `_state_key("pb_event_id")`）。
- 放在 `_milestones_tasks_fragment` / tab[0] 内，rerun 范围沿用现状。

### 3. i18n（`src/nblane/i18n/{zh,en}/project_board.yaml`）
- 现有字段 label 已齐全直接喂组件；仅补组件交互文案（chip「移除」「搜索…」「保存中」等少量 key）。
- 前端 `DEFAULT_LABELS` 同步加英文兜底。

## 测试
- 纯函数层：`_handle_project_event` 的 payload→`submitted_case`/`submitted_milestone` 映射用例（仿 `test_project_board.py`）。
- `build.mjs --verify`：static 与 src 一致 + 关键协议串存在。
- i18n YAML 合法性 + `py_compile`。
- 回归：`test_project_board / _sync / kanban_io` 通过；fallback 路径保留原生 form 不回归。
- 前端无单测框架 → dev(18503) 人工验证。

## 部署
- 新增组件包 + 改 page 11 + i18n 新 key（`@lru_cache`）→ **必须重启** Streamlit。
- dev(18503) 验证 → git → 生产 pull → 重启 `nblane.service`（reader 不涉及）。

## 风险
- last-write-wins：沿用既定策略（git_backup 留痕），可接受。
- 组件缺失 → 返回 None → 自动回退原生 form，不白屏。
- 体量：前端约 1000–1400 行；分阶段先 Basics 端到端，再加 Milestones。

## 实施顺序
1. 组件包骨架（`__init__.py` + build + 协议样板 html），Basics 区 + `save_basics` 端到端跑通。
2. page 11 接入 + `_handle_project_event`（Basics 分支）+ fallback，dev 验证手感。
3. 加 Milestones 卡片区 + 三个 milestone 事件分支。
4. chip 引用多选打磨 + i18n 补全 + 测试 + 构建校验。
