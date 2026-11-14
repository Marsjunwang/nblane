---
status: active
owner: engineering
last_verified: 2026-11-15
source_of_truth: true
---

# 当前状态

nblane 是单人加自己的 Agent 的成长系统。唯一界面是 React SPA（8504，同进程提供 `/api/v1`），论文库和阅读器由 Reader API（8502）提供并嵌入 SPA。数据仍是 `profiles/<name>/` 下的文件。

## 各区现状

| 区 | 现状 |
|----|------|
| 档案初始化 | 本人管理员可在档案列表创建私有档案，选择领域并填写北极星、首个目标、项目和任务；临时目录校验后整体落盘，失败不留下半成品 |
| 首页 | 全屏星图（图态 / 境态），铭文卡重刻北极星与目标，星表管理目标，日课印打卡与销印，占卜（戏占 / 正占，正占可「化为任务」） |
| 项目 | 看板 / 时间轴 / 编年史三视图，按目标或活动分组；看板与项目板合并；习惯与阶段计划住日课栏；Someday 可直接列入 Queue；手机与键盘可用 |
| 技能树 | 按类目星官分组，节点铭文卡显示关联证据和进阶进度，三态写入（locked / learning / lit） |
| 证据 | 六阶段单页：待结晶、待评审（审阅队列）、待关联、已入座、待补强（原档案体检）、已废弃；Done 任务结晶为证据，突破标记 |
| 研究台 | 论文库（嵌入 8502）、论文概览、阅读器（嵌入 8502）、研究来源；本地翻译模型与 GROBID 可在设置页安装和启停；Claim / Evidence 暂不进 SPA |
| 内容工作台 | 文章库 + 全屏 BlockNote 编辑器，AI 封面、改写、元信息建议 |
| 求职工作台 | 结构化简历、目标岗位、导入简历、按 JD 定制；保存失败保留本地草稿，并阻止返回与导出；正文和元信息使用同一版本基线 |
| 公开站点 | 自我介绍开关、作品、写作、构建与上线 |
| 车间 | 网页终端（xterm + ttyd，设置页托管），手机快捷键栏；生产待部署 |
| 助手 | OpenClaw 状态、「接入方式」卡（nblane 技能 / HTTP 接口是否最新）、撤销日志 |
| 设置 | 系统级：AI 服务、本地服务、车间终端、助手与备份；档案级：通用、研究与阅读、AI 路由 |
| AI 异常 | 顶栏抽屉，可逐条或批量忽略 |
| Agent 写入 | SPA 与 Reader 统一分级；直写可撤销，重要操作聊天确认，页面专属操作 403；后台任务按真实提交段记账，取消 / 超时明确部分写入；助手只走 HTTP |

## 已移除

- Streamlit 多页应用（2026-10-06 退出主界面，旧 URL 重定向到 SPA；旧入口与页面代码已删）。论文库继续服务 Reader API，已去除 Streamlit 通信分支与依赖；`pandas` 无运行时引用，已移除。
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
- 跨文件修改与撤销在相关文件锁内复核快照，普通异常回滚；仍不是进程崩溃时的数据库事务，详见 [数据契约](../architecture/data-contracts.md)。
- SPA 按页面懒加载，路由错误边界保留导航，支持重试和显式刷新应用。前端单测、API 类型一致性、构建产物与隔离浏览器烟测纳入 CI；E2E 每轮创建临时档案和独立服务，拒绝复用外部实例。

## 手机 App

截至 2026-10-26，PWA 已在正式域名上线，签名 TWA `0.1.0` 内测 APK/AAB 已产出；两者共用现有 SPA，不另做移动业务页面或服务器监控页。构建、签名和静态配置已验证，但真实安卓设备尚未验收，下一里程碑是安装并检查域名信任、登录保持、全部网页、车间输入与重连、论文阅读和后台恢复。

后续待交付：业务数据离线、推送与后台提醒、设备授权与桌面小组件、受限远程维护、发布自动化与应用商店、Kotlin 原生重写。完成状态、构建入口和真机清单见 [安卓 PWA 与 TWA](../guides/android-twa.md)。

## 缺口与优先级

1. 首页保留现有星盘与字体；新增行动入口（待结晶、待评审、待关联、可进阶）的预览方案已决定不实施。星图仍未显示技能进阶进度，`/starmap` 不含 progress。
2. 已有档案的领域迁移与影响预览、非工程领域 schema 待做；创建时已支持内置机器人、自动驾驶及管理员放入数据目录 `schemas/` 的模板。
3. 车间上生产：8504 WS 代理 + nblane 会话认证已完成，待部署并改 Caddy、撤 basic_auth。
4. 按业务域持续拆分路由与 hooks；新档案初始化已独立成模块，旧的巨型路由与数据层仍需逐步收束。
5. MCP 暂停扩展；Agent 写入策略阶段 5 暂停。
