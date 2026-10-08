---
status: active
owner: engineering
last_verified: 2026-10-08
source_of_truth: true
---

# 当前状态

nblane 是单人加自己的 Agent 的成长系统。唯一界面是 React SPA（8504，同进程提供 `/api/v1`），论文库和阅读器由 Reader API（8502）提供并嵌入 SPA。数据仍是 `profiles/<name>/` 下的文件。

## 各区现状

| 区 | 现状 |
|----|------|
| 首页 | 全屏星图（图态 / 境态），铭文卡重刻北极星与目标，星表管理目标，日课印打卡与销印，占卜（戏占 / 正占，正占可「化为任务」） |
| 项目 | 看板 / 时间轴 / 编年史三视图，按目标或活动分组；看板与项目板合并；习惯与阶段计划住日课栏；Someday 可直接列入 Queue；手机与键盘可用 |
| 技能树 | 按类目星官分组，节点铭文卡显示关联证据和进阶进度，三态写入（locked / learning / lit） |
| 证据 | 五阶段单页：待结晶、待评审（审阅队列）、已入座、待补强（原档案体检）、已废弃；Done 任务结晶为证据，突破标记 |
| 研究台 | 论文库（嵌入 8502）、论文概览、阅读器（嵌入 8502）、研究来源；本地翻译模型与 GROBID 可在设置页安装和启停；Claim / Evidence 暂不进 SPA |
| 内容工作台 | 文章库 + 全屏 BlockNote 编辑器，AI 封面、改写、元信息建议 |
| 求职工作台 | 结构化简历、目标岗位、导入简历、按 JD 定制 |
| 公开站点 | 自我介绍开关、作品、写作、构建与上线 |
| 车间 | 网页终端（xterm + ttyd，设置页托管），手机快捷键栏；生产待部署 |
| 助手 | OpenClaw 状态、「接入方式」卡（nblane 技能 / HTTP 接口是否最新）、撤销日志 |
| 设置 | 系统级：AI 服务、本地服务、车间终端、助手与备份；档案级：通用、研究与阅读、AI 路由 |
| AI 异常 | 顶栏抽屉，可逐条或批量忽略 |
| Agent 写入 | 直写可撤销，重要操作聊天确认，页面专属操作 403；助手只走 HTTP |

## 已移除

- Streamlit 多页应用（2026-10-06 退出主界面，旧 URL 重定向到 SPA；代码待删）。
- Team View 与团队产品池（`teams/`、`core/team*.py`、`nblane team` 已删）。
- Gap Analysis 页、`nblane gap` 命令、`POST .../gap/analyze` 与 MCP `profile://gap`（缺口计算 `core/gap.py` 保留，供首页占卜使用；化为任务走 `POST .../divination/intake`）。
- Agent Activity 审批页与待审候选：`GET/POST .../activity*`、`.../activity/profile-model`、MCP `submit_evidence_candidate` / `submit_profile_model_candidate` / `submit_kanban_candidate` 与 `agent://activity`、助手 `nblane_api propose` / `activity` 已删；Agent 写入改为直写可撤销。
- 收件箱：Inbox 页、`.../inbox*` 端点、`core/inbox.py`、MCP `capture_inbox` 与 `profile://inbox` 已删（已有的 `inbox.yaml` 不再读写，可自行删除）。
- Output Studio 页与 `.../studio`、`.../studio/blog*`、`.../studio/candidates/*`、`.../studio/jd-match` 端点（由内容工作台、求职工作台、公开站点承接；只保留 `POST .../studio/init` 初始化公开层）。
- 独立的目标页、档案体检页（分别并入首页星表、证据页「待补强」）。

## 当前技术边界

- 主存储是文件，不是数据库；Git 做备份。
- 生产：systemd（`nblane-web-api.service`、`nblane-reader.service`）+ Caddy，端口只绑 127.0.0.1。
- LLM 走 OpenAI-compatible API，经 `core/ai/` 路由；本地翻译用 llama.cpp。
- `nblane-mcp` 只给本机 Cursor / Claude Code，无登录无权限控制。
- 公开站构建不读取 private 文件。

## 缺口与优先级

1. 删除 Streamlit 遗留代码（`app.py`、`pages/`、`*_component/`、`web_*.py`），先确认 SPA 与 Reader 无引用。
2. 车间上生产：8504 WS 代理 + nblane 会话认证已完成，待部署并改 Caddy、撤 basic_auth。
3. 文档按 SPA 现状收束（本轮进行中）。
4. 首页星图尚未显示技能「可进阶」脉冲（`/starmap` 不含 progress）。
5. MCP 暂停扩展；Agent 写入策略阶段 5 暂停。
6. 新用户初始化可选领域（内置机器人、自动驾驶，管理员可往数据目录 `schemas/` 加）；非工程领域的 schema 待做。
