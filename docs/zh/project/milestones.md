---
status: active
owner: engineering
last_verified: 2026-10-07
source_of_truth: true
---

# 里程碑

本页是阶段账本。总纲（2026-09-22）：融合 OpenClaw、优化前端交互、统合后端功能，不改数据存储。验收标准：第一条数据闭环（北极星 → 目标 → 项目 → 看板 → 证据结晶）全程在前端完成，不手改 YAML。往后方向见 [路线图](../product/roadmap.md)。

## Phase 0 · 基线：文件层、AI Gateway、SPA 骨架

状态：完成（2026-09-20）。

目标：在文件事实源上建好后续阶段要用的底座。

- 文档事实源收束到 `docs/zh/`，项目管理集中到 `project/`。
- AI Gateway：`core/ai/`（gateway / router / backends / 结构化输出），`llm.py` 兼容旧调用。
- 项目一等实体：`project-board.yaml`，kanban 任务带 `project_id`。
- 研究层：`research/` 下来源、分块、阅读笔记，研究默认私有。
- 博客 front matter 支持 `related_sources` / `related_claims`。
- `nblane sync-agent-harness --target codex|opencode|openclaw` 生成外部执行器配置。
- React SPA 骨架（8504）与 OpenClaw 初步接入。

关键提交：`0e7431b`（OpenClaw 接入 + SPA M0–M4）。

旧计划中的独立 Workspace Index 与 Obsidian 式多视图不再单列：只读聚合改由各页的聚合端点承担（`/starmap`、`/projects-board`），多视图落在项目页三视图。

## Phase 0.5 · 远程车间

状态：代码完成，生产待部署。

目标：手机也能进入 nblane 的运行环境，调用任意已装工具。

- ttyd + tmux 网页终端，设置页托管，手机快捷键栏，nblane 会话认证。
- 生产剩余：8504 WS 代理上线、改 Caddy、撤 basic_auth。

关键提交：`57a82b8`。方案见 [远程车间](../dev/phase0.5-remote-terminal.md)。

## Phase 1 · 证据域单页化

状态：完成。

目标：证据的采集、评审、结晶、入座、补强在一页内完成。

- 证据页五阶段：待结晶、待评审、已入座、待补强、已废弃。
- 结晶状态机收口在 `core/crystallize.py`；Done 任务按任务结晶，一任务一证据。
- 档案体检页解散：证据风险进「待补强」。
- 通用件：mutation API 样板（ETag / If-Match + flock）、铭文卡共享组件与设计 token。

关键提交：`0ec6f2c`（证据单页 + 结晶管线）、`46fb878`（结晶上线）、`28f5768`。

## Phase 2 · 项目与看板一体化

状态：完成。

目标：项目、任务、习惯在一个页面里规划和执行。

- `/projects` 一页三视图：看板（目标分组泳道）、时间轴（排期拖拽、里程碑、历史层）、编年史（只读回放）。
- 日课栏：一个习惯全站一行，阶段计划、90 天热力图补卡与销印，习惯归档与删除。
- 行内快添、任务编辑与删除、TODO 清单、Someday 直接列入 Queue。
- 删除三件套，计划模板。
- 打磨：不静默丢数据、真实数据规模下保持紧凑、手机与键盘可用。

关键提交：`7adfa7e`（后端聚合）、`775b2c8`（统一 /projects）、`3c119e8`（交互宪法）、`88f7717`、`8516112`、`ad86485`（阶段计划）、`0e5bb15`、`d77597f`、`29c8f46`、`1521f65`。

## Phase 3 · 目标 / 北极星编辑 + 首页星图

状态：完成。

目标：首页成为全站导航枢纽，目标和北极星在星图上直接改。

- `/starmap` 聚合端点，Three.js 星图（图态 / 境态）。
- 铭文卡重刻北极星和目标，虚位空星，刻痕星，星表管理目标，目标页删除。
- 命名层与显真，印章家族，日课印，占卜（替代差距分析页）。
- 技能树页：类目星官化、节点铭文卡、三态写端点、进阶进度。
- Streamlit 退出主界面（`ad87958`），设置页分区（`32ff066`）。

关键提交：`794d55f`（星图原型）、`775b2c8`、`b377c6b`（北极星 / 目标 CRUD、大事记）、`3c119e8`、`8383c59`、`ad87958`。

未完成：星图上的技能「可进阶」脉冲（`/starmap` 尚不含 progress）。

## Phase 4 · 助手（OpenClaw）主动推进

状态：完成。

目标：助手每天用 nblane 的数据做计划、提醒和记录，且写入安全可撤销。

- `nblane_api` HTTP 客户端，助手服务账号（`agent: true`）+ profile 权限。
- 写入策略 T0–T3：日常直写进撤销日志，重要操作 428 + 聊天确认，页面专属 403。
- 调用规则只在 nblane 技能一处；助手只走 HTTP，MCP 仅本机。
- 定时任务由 OpenClaw 自己管理，nblane 不同步；每日复盘默认关闭。
- 助手页：状态、接入方式卡、撤销日志。

关键提交：`3a96ffe`（nblane_api）、`5fd4ad1`（自动化声明，后被 `65754db` 收回）、`915323f`、`2946ac5`、`65754db`、`83f0ca8`。

## 工具层（Phase 5 起，按需）

已落地：研究台与阅读器（`ad64e16`、`f07a975`、`957ae24`、`f64ceff`、`0fbf9fe`）、本地翻译模型（`ca61dbf`）、内容工作台（`667a28c`、`bf56f14`、`09b97dd`）、求职工作台（`a897cbc`）、公开站点控制台（`b19a0d2`）、AI 异常（`0a34fa0`、`4ef0ee0`、`32a1d8c`）。

团队功能不做。
