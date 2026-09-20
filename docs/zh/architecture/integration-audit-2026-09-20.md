---
status: active
owner: nblane-team
last_verified: 2026-09-20
source_of_truth: 四个只读审查代理的分域报告（融合后端 / web_api 后端 / SPA 前端 / 文档与打包），每条问题均落实到文件:行号并经代码核实；测试基线 pytest 1470 / vitest 81 / spa_smoke e2e 4/4 全绿
---

# 融合开发全面审查报告（2026-09-20）

> **修复后状态（2026-09-20 晚）**：本报告列出的问题已按「六、修复优先级建议」
> 的第 1–4 档全部修复（详见文末「七、修复记录」），最终回归：
> pytest **1535 passed**、vitest **106 passed**、`tsc` 零错误、CI 关全绿。
> **修复后总体完成度：95 / 100**（各域均 ~95）。原始 82 分基线与问题清单
> 保留作为台账。残余项：M-BE-3 对外契约实证（待人工变更窗口）、
> `--agent main` 硬编码（上游 schema 限制）、看板按 id 寻址、OpenAPI 422
> 契约标注统一、sidecar 一次性 POST 换票——均已在修复记录中注明去向。

对 nblane×OpenClaw 深度融合全部改动（L0–L3 融合仓库侧 + L4 助手页 + L5 SPA
M0–M4 + 打包 + 变更窗口清单）的四域只读审查汇总。审查时代码基线：
pytest **1470 passed**、vitest **81 passed**、`tsc` 零错误、CI 四关（validate /
status / import smoke / pytest）全绿、构建产物与源码同步。

**总体完成度：82 / 100** —— 架构与工程纪律扎实（契约驱动、乐观并发设计、
dry-run 默认、测试非摆设且全绿），无 blocker 级功能缺陷；扣分集中在并发
写防护的覆盖缺口、两处未验证的对外契约、若干安全打磨项和文档漂移。

| 域 | 评分 | 主要扣分点 |
|---|---|---|
| 融合后端（L0–L3） | 82 | 锁未包「读-改-写」全链路；语料/技能同步只增不减；notify/automations 外部契约未验证 |
| web_api 后端 | 82 | `/profiles` 跨用户泄露；登录限流在反代拓扑下失效；If-Match TOCTOU |
| SPA 前端 | 82 | 草稿静默丢失；401 无统一跳转；412 处理三档不一；移动端表格破版 |
| 文档与打包 | 82 | 产物「已入库」表述不成立（未 git add）；cli.md 键层级矛盾；进度表数字失真 |

---

## 一、Blocker（必须先处理）

### B1. 全部新代码尚未 `git add`，「产物提交入库」不成立，按现状推送 CI 必红
- 位置：`docs/zh/architecture/frontend-spa-migration.md:20`、`docs/zh/guides/web-ui.md:82-87`、`AGENTS.md`（均声称 static/ 已提交入库）
- 证据：`git status --porcelain` 显示 44 个 `??`（含 `src/nblane/web_ui/`、
  `src/nblane/web_api/`、`commands/openclaw.py`、`core/openclaw_*.py`、40+ 测试
  文件），`git ls-files src/nblane/web_ui/` 为空。
- 连带风险：`.github/workflows/ci.yml:96` 的 frontend-artifacts job 用
  `git status --porcelain` 判新鲜度，untracked 文件会以 `??` 出现 → 漏 add
  必报 stale。
- 修复：`git add src/nblane/web_ui src/nblane/web_api`（及本轮全部新文件），
  注意 `web_ui/frontend/package-lock.json` 是 ci.yml `cache-dependency-path`
  必需的，不能漏。

> 这是唯一 blocker，且本质是「用户尚未提交」而非代码缺陷——按约定本轮
> 开发未执行任何 git commit。

---

## 二、Major 问题清单

### 融合后端（agent-43 审查）

**M-BE-1. 锁只包了写，没包「读-改-写」——kanban/tree/pool 仍有丢失更新窗口**
`profile_io.py:139-140,189-190`、`kanban_io.py:854-855` 只在写入外套
`locked_profile_write`，load 在锁外。受害最重的是本轮新增的 kanban_move
applier：`review_actions.py:629` parse → `apply_kanban_reorder` → `:647`
save_kanban 全程无锁；MCP apply 与看板编辑并发时后写者静默覆盖，而
Activity 已标 `applied`——状态与事实失真。对比：inbox/agent_activity 有
完整 `update_*` 包装（`agent_activity.py:212-231`）。
修复：为 kanban/tree/pool 增加同构 `update_kanban(profile, fn)` 入口。

**M-BE-2. 语料与技能同步「只增不减」，过期内容永久滞留 agent 记忆**
`openclaw_corpus.py:285-313` 只写当前能渲染的文件，源删除后旧 md 永远留
在 `~/.openclaw/workspace/memory/nblane/`；`check_corpus_drift`（:334-337）
对 skipped 源直接 continue。`_sync_skills`（`commands/openclaw.py:217-249`）
同样不清理 dst 多余文件。
修复：渲染时删除「自有产物但本次无 body」的文件（header 标记识别），
drift 检查计入多余文件。

**M-BE-3. 两处外部契约未验证，且都是生产写路径**
- `notify.py:14-16,91-93`：webhook payload `{"text","source"}` 未对真实
  gateway 验证（代码注释自认）；
- `openclaw_automations.py:33-37`：只有 `add` 端到端验证过，`edit`/`rm` 的
  `--declaration-key` 选择器是假设，dry-run 看不出错误。
修复：变更窗口补一次真实 `edit` 验证并回填注释；或 apply 前对首个 edit
做「先 list 验证 key 命中」预检。

### web_api 后端（agent-44 审查）

**M-API-1. `GET /api/v1/profiles` 跨用户泄露全部 profile（`routes_v1.py:353`）**
只用 `require_user`，不按 `user.profiles` 过滤。member 能看到所有 profile
的名字/schema/current_goal_title，与 `require_profile_access`「403 先于 404
防探测」的设计（:320-321）自相矛盾。
修复：`list_profiles` 按 `can_access_profile` 过滤。

**M-API-2. 登录限流在反代拓扑下失效且可自我 DoS（`auth.py:166-167,227-232`）**
`_client_key` 用 `request.client.host`；生产走 Caddy 反代且无
`--proxy-headers`（全仓库 grep 确认），所有客户端共享 `127.0.0.1` 失败桶：
任何人失败 5 次，全体 60 秒无法登录。
修复：读 `X-Forwarded-For`（uvicorn `--proxy-headers` + 可信代理清单），
限流键改 `ip + username`；至少在部署文档声明该限制。

**M-API-3. If-Match 检查与落盘之间 TOCTOU，412 契约在 kanban 之外名存实亡**
统一模式：请求开始算 ETag → 校验 → 重读 → flock 内写，**锁内不复核快照**。
受影响：activity apply（:707→727）、inbox archive/discard（:1367→1383）、
evidence-review（:1792→1810）、review（:2178→2213+）、project-board
（:2621+）、studio（:3597→3613,3678→3690）。只有 kanban 走
`save_kanban_with_merge(expected_snapshot=...)`（:962-968）真正闭环。
修复：core saver 增加 `expected_snapshot` 参数（仿 kanban_merge），锁内
比对不符抛冲突 → 412。

**M-API-4. inbox clarify 的 ETag 覆盖缺口 + kanban 写不合并（`routes_v1.py:1328-1348` + `core/inbox.py:592-608`）**
clarify 的 `to_kanban_queue` 分支 core 里裸 `save_kanban`（无 merge），路由
If-Match 只覆盖 inbox.yaml：看板上的并发编辑被整体覆盖，客户端也无法感知
kanban 已变。
修复：kanban 分支改 `save_kanban_with_merge`；clarify ETag 纳入 kanban.md。

**M-API-5. review mutation 的 ETag 覆盖不全（`routes_v1.py:2028-2048`）**
`_review_etag` 覆盖五文件，但 public_draft applier 写 public layer（blog 草稿）、
save 写 `agent-activity.yaml`，均不在指纹里。
修复：并入 agent-activity.yaml 与 public layer 指纹，或文档明确降级声明。

### SPA 前端（agent-45 审查）

**M-FE-1. 项目看板编辑草稿被静默清空（`ProjectBoardPage.tsx:1027` + `:289`）**
`CaseDetail` 以 `key={selected.id:data.updated}` 挂载，`BasicsTab` 草稿是
本地 useState。任何板级 mutation（挪任务/加里程碑）→ refetch →
`data.updated` 变 → 整体 remount → **未保存编辑无提示丢失**。在「任务」
Tab 挪一个任务就会清掉「基本信息」Tab 的未保存内容。
修复：key 只用 `selected.id`；服务端数据变化走受控同步 + dirty 检查提示。
（`StudioPage.tsx:209` 同模式但仅外部改文章时触发，风险低。）

**M-FE-2. 会话过期后 401 无统一处理（`client.ts:44-66`、`RequireAuth.tsx:24`）**
401 跳登录只在首次 `useMe` 生效；`staleTime:60s` + `refetchOnWindowFocus:false`
使过期会话的 `me` 缓存仍「新鲜」，守卫放行，用户困在各页英文错误。
修复：QueryClient 全局 onError 或 client.ts 内对 401 统一跳 `/login`。

**M-FE-3. 登录后丢失原始目标页（`LoginPage.tsx:34`）**
`RequireAuth` 带了 `state.from`，但登录成功的 `onSuccess` 写死
`navigate('/')`。深链 `/p/alice/studio` → 登录 → 落到档案列表。
修复：`navigate(from ?? '/', { replace: true })`。

### 文档与打包（agent-46 审查）

**M-DOC-1. cli.md 对 overlay 键层级的描述与真实文件矛盾（`docs/zh/reference/cli.md` 末尾新增段）**
写 `model.primary` / `heartbeat.main`，实际是
`agents.defaults.model.primary` / `agents.defaults.heartbeat`（还漏了
imageModel），与 openclaw-integration.md:1144-1147（CW-3 注 b）自相矛盾。
修复：改为 `agents.defaults.*` 全路径并补 imageModel。

**M-DOC-2. SPA 进度表把已完成的 Inbox 页列为「剩余」（`frontend-spa-migration.md:22`）**
Inbox 页已完整落地（`InboxPage.tsx` 423 行 + 4 mutation + 测试）。
另：同表 M2 行把规则版 Gap 页整体放入「剩余」，应为「已实现（规则版），
剩余 LLM 异步任务」。

**M-DOC-3. 测试基线数字失真（`openclaw-deep-integration.md:32`）**
写 1357/39，实测 1470/81。建议改为「≥」弱表述或更新为当前值。

---

## 三、Minor 问题（按域归并，完整版见各域审查记录）

**融合后端**
- `mcp_server.py:1062-1063` 工具文档串列名误导（"Someday" vs 真实
  "Someday / Maybe"），且提交时不预检 target_section
- `agent_activity.py:138` normalize 使 apply 时 `created` 时间戳总被重置
- `--prune` 不带 `--apply` 时静默无效（`commands/openclaw.py:139-145`）
- `_install_automations` 失败 `sys.exit(1)` 与其他步骤的 `return False` 不一致
- MCP 工具错误契约漏 catch `yaml.YAMLError`（文件损坏时客户端收协议级异常）
- `growth_log.py` 原子化但 SKILL.md 读-改-写仍无锁（与 M-BE-1 同源）
- doctor 备份检查是子串启发式（`openclaw_ops.py:392-401`）
- `cmd_sync` 写入模式遇漂移也退出 1，cron 日常 sync 会持续报失败（需文档说明或降级）
- `--agent main` 硬编码（`openclaw_automations.py:676-677`）

**web_api**
- handoff token 可重放、走 URL query（进日志/历史/Referer）；每次 GET
  /home、/research 都铸新 token（`routes_v1.py:3951`）
- 无服务端会话吊销（12h stateless token，logout 只删 cookie）——可接受但文档未声明
- `Secure` cookie 默认关；部署文档完全没覆盖 SPA 后端（8504 如何挂 Caddy）
- 422 错误体双格式：handler 抛 `ErrorResponse`，pydantic 校验失败返回 FastAPI
  默认 `{"detail":[...]}`（需加 RequestValidationError handler 统一）
- `routes_v1.py:95-110` 重复 import 块（合并残留）；单文件已 4160 行，建议拆分
- project task 的 `milestone_id` 不校验存在性（`:3019-3024`）
- gap intake 响应回显原始 section 而非实际落盘值（`:2018-2022`）
- `KanbanCardCreateRequest.title` 无 schema 级 min/max 约束（`schemas.py:238-244`）
- token 过期边界 `exp < now` 应为 `<=`（`core/auth.py:232`）
- 每请求全文件哈希/解析的性能注意（`_studio_etag` rglob、users.yaml 每请求重读）

**SPA 前端**
- 空 ETag 退化为必然 412：hooks 层 `?? ''` 回退后后端恒 412，误导性报错
  （hooks.ts 8 处 + `routes_v1.py:625-632`）——etag 为空应省略 If-Match
- 412 冲突处理三档不一致：Kanban/Inbox/Activity 有黄提示+refetch；Studio
  有提示无刷新按钮；EvidenceReview/Review/ProjectBoard 完全无 412 识别
- 看板按标题寻址，重名卡 422 `kanban_card_ambiguous` 且 UI 无消解手段
  （需后端支持按 id 寻址）
- Inbox 模态框在筛选切换/refetch 后可能变空壳（`InboxPage.tsx:106-107`）
- SidecarFrame cookie 引导靠固定 800ms 猜测延时，无重试
- 移动端表格无横向滚动容器：EvidenceReview/Review/ProjectBoard/Research/
  Evidence 五页 9 列表格在手机上破版（手机访问是明确需求）
- 导航路径拼接 profile 名未 `encodeURIComponent`（`AppLayout.tsx:119`）
- 成功提示永不消散（EvidenceReview/Review 的 isSuccess 横幅）
- 死代码：`useGapAnalyze` 写入的缓存 key 无 reader（`hooks.ts:469-471`）

**文档**
- `notify` 是顶层命令，`openclaw-deep-integration.md:27` 与 `status.md` 误写进
  openclaw 命令组
- MCP 工具数验收口径未更新（现为 13 个，文档写 7 个，:158 与 :684）
- `frontend-spa-migration.md:113-149` 策 C 表格被评估记录隔断（渲染断裂）
- e2e spec 计数 14→15（:44）；front matter `status: proposed` 宜升 active；
  `source_of_truth` 未列 web_api/web_ui
- `web-ui.md:200-206` 手动停止清单漏第三服务；`web-ui.md` 与 `docs/zh/README.md`
  的 last_verified 未随本轮改动更新
- 「CI 四关」表述未覆盖第五个 frontend-artifacts job
- `src/nblane/web_ui/README.md:80-81`「kanban、inbox、goals 等前端尚未实现」
  已过时

---

## 四、未完成部分（刻意推迟项，非缺陷）

| 项 | 状态 | 备注 |
|---|---|---|
| LLM 异步任务/SSE 基建 | 未开始 | Gap `use_llm`、jd-match 等统一 422 降级 + 页面提示卡片 |
| BlockNote 富文本编辑器 | 未接入 | 博客 Markdown 含自定义指令/公式，往返会丢结构；sidecar blocks 已保留，可无损接入 |
| Home trends/daily_brief | 未纳入 | 依赖 dashboard_payload 的快照写副作用，GET 需保持纯读 |
| Home 目标编辑器/命令条 | 未做 | 3D dashboard 内交互 |
| 项目时间轴画布 | 未做 | Streamlit 版 timeline 视图 + web_preferences 持久化 |
| 新页面 e2e spec | 未新增 | 仅既有 spa_smoke 4 例；随 M5 移植 |
| SPA 后端生产部署（8504 systemd + Caddy） | 未做 | 部署文档未覆盖；CW-2 备份检查也需含第三 unit |
| 变更窗口 CW-1~CW-5 | 命令清单已备 | 待人工在生产窗口执行 |
| EvidencePage/GoalsPage 编辑 | 页面自述「开发中」 | 当前只读 |

---

## 五、审查确认无问题的关键面（正向核查）

- **路径安全**：profile 名 `validate_profile_name` 拒绝分隔符/控制字符；
  blog slug 逐段 slug 化（`..` 变 `draft`）；SPA 静态 resolve + `is_relative_to`；
  item/task id 仅 dict 查找不拼路径。无命令注入（subprocess 全 argv 列表），
  无密钥泄露面（token 只进 header，错误信息截断）。
- **认证覆盖**：除 /health、/profiles、/auth/* 外全部 40+ 端点走
  PROFILE_DEPENDENCY；scope 检查先于 404。
- **测试质量**：非摆设——双进程×50 并发写锁测试、注入 runner 断言
  dry-run 不落盘、前端测试断言 If-Match header 与 412 行为、OpenAPI 快照
  守护无绕过。
- **打包**：wheel 解包模拟安装态全链路实测通过（SPA 回退、/api 隔离、
  immutable 缓存）；pyproject package-data 声明有测试锁定。
- **CW 清单**：全部 nblane 侧命令与真实 `--help` 逐条核对一致，引用路径全部存在。
- **LLM 降级清单**：与代码逐一核对，无静默降级，页面均有明示。

---

## 六、修复优先级建议

1. **立即（提交前）**：B1 `git add` 全部新文件；M-DOC-1/2/3 三处文档事实更新
   （cli.md 键层级、进度表 Inbox/Gap 行、测试数字）。
2. **下一轮开发（并发写防护专题）**：M-API-3/4/5 + M-BE-1——为 core saver
   增加 `expected_snapshot` 参数统一闭环 412；kanban/tree/pool 补 `update_*`
   包装；applier 改走锁内读-改-写。**（已于 2026-09-20 完成，见七·二）**
3. **安全打磨**：M-API-1（/profiles 过滤）、M-API-2（限流键 + 部署文档）、
   handoff token 改 POST 一次性、Secure cookie 部署指引。
4. **UX 修复**：M-FE-1/2/3（草稿丢失、401 跳转、登录回跳）+ 移动端表格
   ScrollContainer + 412 处理统一组件。
5. **验证债**：变更窗口补 notify payload 与 automations edit 的真实验证并
   回填注释（M-BE-3）。

---

## 七、修复记录

### 2026-09-20 前端 UX 批次（vitest 81 → 93，tsc+vite build 干净）

- **M-FE-1 草稿静默丢失**：`ProjectBoardPage.tsx` 的 `CaseDetail` 改按
  `selected.id` 键控（不再含 `data.updated`）；`BasicsTab` 增加 dirty 跟踪
  + `lastSynced` ref——draft 未脏时跟随 refetch 后的服务端数据，已脏时
  保留本地编辑，保存成功后复位 dirty。`StudioPage.tsx` 同模式消除
  `key={slug:etag}`（key 只用 slug，`PostEditorForm` 同样 dirty 同步）。
  回归测试：板级 mutation（挪任务）refetch 后脏草稿保留 / 净表单跟随
  服务端；studio 创建文章触发 refetch 后脏草稿保留。
- **M-FE-2 401 统一处理**：`client.ts` 请求层对 401 触发回调，
  `installUnauthorizedHandler(queryClient)`（main.tsx 注册）在
  `['auth','me']` 处于 success 态时 `resetQueries` 使其失效，由
  RequireAuth 守卫 refetch 后自行跳转 /login；以 success 态为守卫条件，
  登录页自身的 401（守卫 refetch 或密码错误）不会死循环。
- **M-FE-3 登录回跳**：`LoginPage.tsx` `onSuccess` 改为
  `navigate(from ?? '/', { replace: true })`；`from` 只接受以 `/` 开头且
  非 `//` 的站内路径，防开放重定向。
- **移动端表格破版**：EvidenceReview / Review / ProjectBoard / Research /
  Evidence 五页表格外包 `Table.ScrollContainer`（minWidth 420–1000，
  按列数设定）。
- **空 ETag 必然 412**：新增 `client.ts` 的 `ifMatch(etag)`——etag 为空
  串时整体省略 If-Match header；`hooks.ts` 全部 26 处 mutation 请求构造
  改走该辅助函数。
- **成功横幅不消散**：EvidenceReviewPage 在选择变更 / 搜索 / 状态筛选时
  `mutation.reset()`；ReviewPage CandidateTab 在新选择与窗口切换时
  reset save/apply mutation。
- **导航路径编码**：`AppLayout.tsx` 导航 basePath 对 profile 名补
  `encodeURIComponent`（与 ProfilesPage 一致），新增 AppLayout 测试锁定。

---

## 七、修复记录（2026-09-20）

以下条目已于 2026-09-20 修复（仅文档改动，未改代码）；原始条目保留在上文
作为审查当时的事实快照。

- **M-DOC-1 已修复**：`docs/zh/reference/cli.md` 末尾 overlay 键改为真实路径
  `agents.defaults.model.primary/fallbacks`、`agents.defaults.utilityModel`、
  `agents.defaults.imageModel`、`agents.defaults.heartbeat`
  （以 `profiles/template/assistant/openclaw.overlay.json5` 实际内容为准）。
- **M-DOC-2 已修复**：`frontend-spa-migration.md` 进度表 M3–M5 行「剩余」
  删除「新 Inbox 页」；M2 行 Gap Analysis 改为「已实现（规则版），剩余 LLM
  异步任务」。
- **M-DOC-3 已修复**：`openclaw-deep-integration.md:32` 测试基线改为弱表述
  「≥1470 pytest / ≥81 vitest（随开发递增）」。
- **文档 Minor 已修复**（对应第三节「文档」整组）：
  - `openclaw-deep-integration.md:27` 与 `status.md`：`notify` 移出 openclaw
    命令组，改为「`nblane openclaw doctor|sync|install|automations sync`
    CLI + 顶层 `nblane notify`」；
  - `openclaw-deep-integration.md:158` 与 `:684`：MCP 工具数 7 → 13
    （7 旧 + 6 新）；
  - `frontend-spa-migration.md` 策 C 表格行恢复连续（策 B 复用评估记录移至
    表格之后）；`:44`（及 §7 测试策略表同口径处）e2e spec 计数 14 → 15；
    front matter `status` 升 `active`、`source_of_truth` 补
    `src/nblane/web_api/`、`src/nblane/web_ui/`；
  - `web-ui.md:200-206` 手动停止清单补第三服务（nblane-web-api
    8504/18504）；`web-ui.md` 与 `docs/zh/README.md` 的 `last_verified`
    更新为 2026-09-20；
  - `openclaw-deep-integration.md:676-677`「CI 四关」改为「CI 五关（含
    frontend-artifacts）」；
  - `src/nblane/web_ui/README.md:80-81` 删除「kanban、inbox、goals 等前端
    尚未实现」过时表述，改为反映 16 页已实现的现状。

## 七·二、修复记录（并发写防护专题，2026-09-20）

以下条目为本节 Major 并发写防护问题的代码修复（M-API-3/4/5 + M-BE-1，
另含 Minor 第 9 条 growth_log 同源问题）；原始条目保留在上文作为审查
当时的事实快照。统一设计：**复用 `core/file_state.py` 的
`FileConflictError` + `assert_unchanged`**（不另造异常），各 core saver
新增可选 `expected_snapshot` 参数，在 `locked_profile_write` 锁内复核
请求开始时的文件指纹，不符即抛 `FileConflictError`；web_api 路由将其
映射为与 If-Match 预检一致的 `412 etag_mismatch` + 响应头带新 ETag。
无 If-Match/无快照的旧调用方行为不变（参数默认 None）。

- **M-API-3 已修复（If-Match 与落盘间 TOCTOU）**：
  - `save_kanban_with_merge`（`core/kanban_merge.py`）的快照复核、重读与
    写入全部移入 kanban.md 锁内，kanban 闭环消除残余竞态；
  - 以下 saver 获得锁内快照复核能力：`save_evidence_pool` /
    `save_skill_tree`（`core/profile_io.py`）、`save_kanban`（
    `core/kanban_io.py`）、`save_inbox` / `update_inbox`（`core/inbox.py`）、
    `save_agent_activity` / `update_agent_activity` /
    `append_activity_item` / `update_activity_status`
    （`core/agent_activity.py`）、`save_learning_log` /
    `add_learning_resource`（`core/learning_log.py`，补 flock）、
    `activity_log.save` / `add_habit`（`core/activity_log.py`，补 flock）、
    `save_project_board`（`core/project_board.py`，补 flock）、
    `save_research_sources`（`core/research_sources.py`，补 flock）、
    `save_blog_post` / `publish_blog_text`（`core/public_site.py`，新增
    profile 级 blog 锁，复核 Markdown + BlockNote sidecar 双指纹）；
  - 路由层 412 映射覆盖：activity apply/dismiss、inbox
    capture/clarify/archive/discard、evidence-review bulk/deprecate（改走
    `update_evidence_pool` 锁内读-改-写）、review save/apply（按文件
    线程化 activity/pool/kanban 快照，同一请求内首次写入后消费）、
    project-board 全部 mutation（`_check_board_mutation` 下发
    board/kanban/pool/sources 四路快照，经 `sync_project_case_workspace`
    / `sync_project_board_from_kanban` 锁内复核）、studio blog
    save/publish。
- **M-API-4 已修复**：`_inbox_etag` 改为覆盖 inbox.yaml + kanban.md +
  learning-log.yaml + activity-log.yaml 的复合指纹（GET 与全部 mutation
  一致使用，SPA 无感）；clarify 的 `to_kanban_queue` 分支改走
  `save_kanban_with_merge`（以请求开始快照做锁内复核 + 三方合并），
  learning/activity 分支线程化对应快照，inbox.yaml 落盘前锁内复核。
- **M-API-5 已修复**：`_review_etag` 并入 agent-activity.yaml 与 public
  layer 指纹（public layer 文件组 + blog 目录指纹，提取为
  `_public_layer_fingerprints` 与 `_studio_etag` 共用）。
- **M-BE-1 已修复**：新增与 `update_inbox` 同构的锁内读-改-写入口
  `update_kanban`（`core/kanban_io.py`）、`update_skill_tree` /
  `update_evidence_pool`（`core/profile_io.py`）、`update_project_board`
  （`core/project_board.py`）；`review_actions.py` 的 kanban_move applier
  改走 `update_kanban`（parse → reorder → save 全程锁内），evidence
  applier 的 mark_crystallized 与 next_action applier 的 Queue 追加同改；
  各 applier 的 `except Exception` 前补 `except FileConflictError: raise`，
  冲突不再被吞成 failed 项而是冒泡为 412。已核查锁嵌套：无同文件锁
  重入路径（file_lock 非可重入约束保持不变）。
- **growth_log 同源 Minor 已修复**：`append_growth_log_row` 的 SKILL.md
  读-改-写全程包 SKILL.md 锁（调用方 mcp_server / commands/profile 均无
  锁嵌套）。
- **测试**：新增 `tests/test_write_conflict.py`（23 例，core 级锁内复核 /
  update_* 入口 / merge 锁内闭环 / blog 双指纹 / growth_log 并发追加 /
  kanban_move applier 加锁与冲突冒泡）与
  `tests/test_web_api_write_conflict.py`（12 例，包装目标模块
  `locked_profile_write` 在锁内注入外部写，验证各端点 412 + 新 ETag、
  clarify kanban 分支合并不 412、inbox/review ETag 覆盖范围）；测试基线
  1470 → **1505 passed**。API 行为兼容：无 If-Match 旧客户端仍放行，
  OpenAPI 快照无变化（未动 schemas）。
- **已知残留**（不阻塞，后续专题再议）：learning/activity log 的
  `add_*` 读-改-写中 id 分配仍在锁外（写入已入锁复核，冲突会 412 而非
  静默覆盖）；review apply 批处理中途遇冲突时已应用候选保持已应用并
  整体 412（语义与逐项 apply 一致，客户端按提示 reload）；blog 锁目前
  仅覆盖 save/publish（create/media 写入未入锁）。

## 七·三、修复记录（安全打磨专题，2026-09-20）

以下条目为本节安全类 Major/Minor 的修复（M-API-1、M-API-2、handoff
token 卫生前三条、部署文档缺口）；原始条目保留在上文作为审查当时的事实
快照。

- **M-API-1 已修复（/profiles 跨用户泄露）**：`list_profiles`
  （`routes_v1.py`）改用 `Depends(require_user)` 取当前用户并按
  `core.auth.can_access_profile` 过滤——admin（及 auth-off 合成
  admin）看全部，member 只看其 user 记录授权的 profile，不可访问的
  条目整体省略而非 403。提取 `_core_user` 辅助函数供
  `require_profile_access` 与本端点共用（同源规则）；`AUTH_DEPENDENCY`
  常量随之删除（已无引用）。
- **M-API-2 已修复（登录限流反代失效 + 自我 DoS）**：
  - 限流键改为「客户端 IP + 用户名」组合
    （`_client_key(request, username)`，`web_api/auth.py`）——用户名
    维度防止单一来源把共享 IP 桶打满、锁死其他账号；
  - 新增 `NBLANE_TRUST_PROXY_HEADERS=1` 开关：开启后取
    `X-Forwarded-For` 首跳作为客户端 IP（Caddy `reverse_proxy` 默认
    重写该头）；默认关闭，直连部署不受伪造头影响。未采用 uvicorn
    `--proxy-headers` 方案——该开关在应用层显式控制，语义单一、可按
    服务独立配置，且不改变 `request.client` 对其他逻辑的含义。
    `.env.example` 与部署文档已同步说明开启前提（仅当应用端口不直接
    可达且反代覆盖该头部）。
- **handoff token 卫生（Minor web_api 第 1 条）部分收紧**：
  - 确认 `GET /home`、`GET /research` 只在 sidecar auth 开启时铸
    token（auth-off 本地模式恒为空串，既有逻辑不变）；
  - TTL 120s → **60s**（`core.auth.mint_auth_handoff_token` 默认值，
    Streamlit 侧 `web_auth.sidecar_auth_handoff_token` 同步受益）；
  - 残余风险在 `_sidecar_info` 与两端点 docstring 注明：token 在
    TTL 内可重放，sidecar 仍兼容 URL query 换票（进代理日志/浏览器
    历史）。SPA `SidecarFrame` 与 Streamlit `_render_authenticated_iframe`
    **本就走隐藏表单 POST** `/auth/session`，query 路径仅为 sidecar
    兼容残留；一次性 POST-only 换票属 sidecar（web_reader_api）改动，
    按任务边界留给后续专题。
- **Minor web_api 第 2 条（无服务端会话吊销）**：确认为可接受设计
  （12h stateless HMAC token，logout 只删 cookie），已在部署文档
  限流段落与上文残留声明中显式记录，不改代码。
- **部署文档缺口已补（Minor web_api 第 3 条 + 第四节未完成项）**：
  `docs/zh/guides/deployment-tencent-cloud.md` 新增「SPA 后端（8504，
  nblane.web_api）」小节——systemd unit 示例（含
  `NBLANE_DATA_GIT_AUTOCOMMIT/AUTOPUSH`，CW-2 备份检查需覆盖第三
  unit、`--workers 1` 限流约束）、Caddy 子域名反代配置（复制全部
  8502 `handle` 块、catch-all 指 8504）、`NBLANE_AUTH_COOKIE_SECURE=1`
  与 `NBLANE_TRUST_PROXY_HEADERS`/XFF 的关系；同步修订「应用层不实
  现登录限流」过时段落（8504 已内置 ip+username 限流，8501/8502 登录
  面仍建议反代层兜底）与 handoff 120s 表述；端口职责清单补 8504；
  front matter `last_verified` 更新为 2026-09-20。
- **测试**：`tests/test_web_api_auth.py` 新增 6 例——member 只见
  授权 profile / admin 见全部 / 未登录 401；限流键含用户名（同 IP
  不同账号不互锁）、XFF 关闭时伪造头不换桶、XFF 开启时按首跳分桶。
  端点 docstring 变化触发 OpenAPI 快照更新，已走
  `scripts/dump-openapi.sh` + `npm run gen:api` 流程（仅 description
  文本变化，无 API 结构变化）。测试基线 1505 → **1511 passed**。
- **已知残留**（不阻塞）：handoff token 一次性化与 sidecar 移除
  query 换票路径（web_reader_api 侧）；`core/auth.py:232` token 过期
  边界 `exp < now` 应为 `<=`（Minor，本轮未动）；8501 Streamlit 与
  8502 sidecar 登录面仍无应用层限流（部署文档已声明反代层兜底）。

## 七·四、修复记录（M-BE-2 + 融合后端/web_api Minor 批次，2026-09-20）

以下条目为本批修复：Major M-BE-2（语料/技能同步只增不减）+ 融合后端
Minor 7 项 + web_api Minor 6 项；原始条目保留在上文作为审查当时的事实
快照。测试基线 1511 → **1535 passed**（+24）；OpenAPI 快照经
`scripts/dump-openapi.sh` + `npm run gen:api` 重生成（仅
`KanbanCardCreateRequest.title` 增加 min/maxLength 约束，另同步了七·三
批次遗留的两处 docstring 漂移，无 API 结构变化）。

- **M-BE-2 已修复（语料/技能同步「只增不减」）**：
  - 语料（`core/openclaw_corpus.py`）：新增 `_is_own_artifact`（首行匹配
    生成头 `<!-- source: nblane | ... | do-not-edit -->`）与
    `_stale_artifacts`；`render_profile_corpus` 渲染后删除「自有产物但
    本次无 body」的 md（含非 `CORPUS_FILES` 名的遗留产物），记入
    `CorpusResult.removed`；无标记的用户文件一律不动。
    `check_corpus_drift` 不再对 skipped 源视而不见——盘上仍存生成产物
    即计漂移，任何带生成头的多余文件同样计入。
  - 技能（`commands/openclaw.py` `_sync_skills`）：新增
    `_stale_skill_files` + `_remove_empty_skill_dirs`；归属判定限定
    `src` 顶层条目（`codex-dev/`、`kimi-dev/`、`bin/`），其下 `src` 已
    不存在的文件写入模式删除、`--check` 以 `-` 计漂移并清空空目录；
    其他顶层目录视为外来技能树永不触碰（`src` 为空时全部不清理，防
    误删）。`_sync_corpus` 输出补 `[删除]` 行。
- **融合后端 Minor**：
  1. `mcp_server.py` `submit_kanban_candidate`：docstring 改为列举
     `KANBAN_SECTIONS` 真实四列（明示 `Someday / Maybe` 是含斜杠的
     单个列名）；非空 `target_section` 经 `resolve_kanban_section`
     预检，非法值返回错误负载（大小写不敏感命中时归一化为规范名），
     空值仍允许。
  2. `core/agent_activity.py` `append_activity_item`：merge 时按
     「显式传入 > 已存值 > 当前时间」保留 `created`（此前
     normalize 总填当前时间，重 apply 必重置）。
  3. `commands/openclaw.py` `cmd_automations_sync`：`--prune` 不带
     `--apply` 时 stderr 明确提醒其不生效（原静默无效）。
  4. `_install_automations` 加载/拉取失败改 `return False`（原
     `sys.exit(1)`），与其他步骤一致经 `cmd_install` 汇总退出码。
  5. MCP 工具错误契约：新增 `_TOOL_STORE_ERRORS = (OSError,
     ValueError, yaml.YAMLError)` 统一替换全部 9 处 store 层 catch
     （含 `log_skill_evidence` 原仅 catch ValueError 处）——文件
     损坏时客户端收到结构化错误负载而非协议级异常。未选 yaml_io 层
     包装方案（`fast_safe_load` 另有 8 处直接 catch `yaml.YAMLError`
     的调用方，包装会改变其语义，侵入更大）。
  6. `core/openclaw_ops.py` `check_backup_schedule`：子串启发式收紧为
     「标识（declarationKey/name）在段边界含 `backup`（如
     `system:backup-daily`）且带 cron/every 调度」——纯文本提及或无
     调度的同名任务不再误判。
  7. `cmd_sync` 写入模式遇 automations 漂移退出 1：维持行为不变
     （向后兼容优先），已在 `docs/zh/reference/cli.md` 补文档说明
     （含 cron 场景的处置建议），同节补充本批清理行为与 `--prune`
     提醒、doctor 备份检查口径。
- **web_api Minor**：
  8. 422 双格式统一：`create_app` 注册 `RequestValidationError` handler
     （`web_api/__init__.py` + `routes_v1.py` 新增
     `validation_error_handler`），pydantic 校验失败与 ApiError 同为
     `ErrorResponse{code, message}`，code 固定 `validation_error`，
     message 取前 5 条 `loc: msg`；HTTPException 路径（`{"detail"}`
     登录/reader 等既有断言）不受影响。
  9. `routes_v1.py` 合并残留的重复 import 块（experience/goals/
     kanban_archive/kanban_io/kanban_merge/llm/models/growth_review
     共 18 行）已删除。
  10. project task 创建（`add_profile_project_task`）：非空
      `milestone_id` 必须存在于 `case.milestones`，否则 422
      `unknown_milestone`；空值仍允许。
  11. gap intake 响应 section 改为落盘后回读（`parse_kanban` 定位新建
      卡片所在列），不再回显请求原值。
  12. `schemas.py` `KanbanCardCreateRequest.title` 补
      `min_length=1, max_length=200`（与其他 create 模型一致）；
      空白标题仍走路由侧 `invalid_kanban_card` 422，既有断言兼容。
  13. `core/auth.py` `verify_auth_session_token` 过期边界 `exp < now`
      改 `<=`（exp 当即失效）；新增边界测试锁定 exp-1/exp/exp+1 三态。
- **测试**（+24）：`test_openclaw_corpus.py` +5（源删除后渲染清理 +
  drift 报多余文件 + 用户文件豁免）、`test_openclaw_sync.py` +3（技能
  清理/外来树豁免/check 只报不删）、`test_openclaw_ops.py` +3（备份
  检查误报三例）、`test_mcp_surface.py` +3（列名预检/规范化 + 两处
  YAML 损坏错误负载）、`test_agent_activity.py` +1（created 保留）、
  `test_openclaw_automations.py` +1（--prune 提醒）、
  `test_openclaw_install.py` +3（步骤失败 return False 契约）、
  `test_web_api_kanban.py` +1（422 统一形态 + title 约束三例）、
  `test_web_api_project_board.py` +2（milestone 422/空值放行）、
  `test_web_api_gap.py` +1（回读落盘 section）、`test_auth.py` +1
  （exp 边界）。
- **刻意保留未修**：`openclaw_automations.py:676-677` `--agent main`
  硬编码——automations schema 无 agent 字段，CLI `add/edit` 必须以
  `--agent` 指定目标 agent，属上游 OpenClaw 限制；待上游支持声明式
  agent 字段后再移除。
- **已知残留**（不阻塞）：`core/auth.py:310` reader token 同款
  `exp < now` 边界（本批按任务边界只修 session token 一处，建议下次
  一并改 `<=`）；OpenAPI 文档中 422 仍声明 FastAPI 默认
  `HTTPValidationError` 模型（运行时形态已统一，契约标注统一需逐路由
  `responses=` 覆盖，留待后续）；`src` 为空的极端情况下技能清理不
  生效（防误删的有意设计，已测试锁定）。

## 七·四、修复记录（SPA 前端 Minor 批次，2026-09-20）

以下条目为第三节「SPA 前端」Minor 组剩余五项的修复；原始条目保留在上文
作为审查当时的事实快照。vitest 基线 93 → **106 passed**（21 个文件），
`npm run build`（tsc + vite）干净。至此第三节 SPA 前端 Minor 组全部
清零（其余各条已在前端 UX 批次修复）。

- **412 冲突处理三档不统一 已修复**：新增共享组件
  `src/nblane/web_ui/frontend/src/components/ConflictAlert.tsx`——
  `isConflictError`（ApiError 412 识别）、`ConflictAlert`（黄色提示 +
  统一文案「数据已被他人修改，请刷新后重试」+「刷新」按钮）、
  `MutationErrorAlert`（412 升级为冲突提示，其余错误保持红色 fallback）。
  四页接入：
  - **Studio**（原先有提示无刷新按钮）：删除本地 `isConflictError` /
    `MutationError`，全部 mutation 错误位（创建/保存/发布/预览/建草稿/
    初始化）改走共享组件，刷新经 `useRefreshStudio` invalidate
    `['profiles', name, 'studio']`（总览与文章详情同前缀一并刷新）；
  - **EvidenceReview**（原先红色泛化错误）：错误块改共享组件，刷新走
    `list.refetch()`；
  - **Review**：错误块改共享组件，刷新 invalidate
    `['profiles', profile, 'review']`；
  - **ProjectBoard**：5 处错误位（创建 case / 保存基本信息 / 里程碑编辑
    与添加 / 任务添加与移动）改共享组件，刷新经 `useRefreshBoard`
    invalidate board 查询。
  Kanban/Inbox/Activity 既有「黄提示 + 自动 refetch」通知模式为参照实现，
  保持不变。测试：新增 `ConflictAlert.test.tsx` 7 例（识别/统一文案/刷新
  按钮/空态/红色 fallback）；四页既有 412 测试升级为「冲突提示 + 原始
  错误文案不再展示 + 点击刷新触发 GET refetch」。
- **Inbox 模态框空壳 已修复**：`InboxPage.tsx` 新增 effect——`selectedId`
  对应条目在已加载列表中消失（筛选切换或 refetch 后不再返回）时自动关闭
  模态框；以 `list.data !== undefined` 为守卫，新查询加载途中不误关。
  测试：筛选切到「已归档」后模态框自动关闭并显示空态。
- **SidecarFrame 800ms 猜测延时 已改善**：内容 iframe 上方新增常驻
  「重新加载」按钮（重跑完整 bootstrap——隐藏表单 POST + keyed 重挂载
  强制真实刷新，handoff 过期场景同样适用）；iframe `onLoad` 前显示加载
  遮盖层（Loader + 提示文案），onLoad 后撤去——慢网络下不再是白屏无
  出路。cookie 引导的 800ms head start 保留（跨域隐藏 iframe 无可靠
  load 信号，与 Streamlit 侧同一模式）。测试：新增
  `SidecarFrame.test.tsx` 3 例（onLoad 撤遮盖 / 重新加载重挂载 /
  handoff bootstrap 重跑）。
- **useGapAnalyze 死缓存 key 已修复**：删除向
  `['profiles', profile, 'gap', 'last']` 的 `setQueryData`（全仓库无
  reader）；页面本就渲染 `mutation.data`，行为不变。测试：新增
  `api/hooks.test.tsx` 1 例，断言结果经 mutation state 暴露且 query
  cache 无任何写入。
- **看板重名卡 422 已改善（前端侧）**：`KanbanPage.tsx` mutation 错误
  处理新增 422 `kanban_card_ambiguous` 专门分支——橙色通知说明存在
  重名卡片、请先在数据层（kanban.md）重命名消歧后再试；不自动消解、
  不重试。按 id 寻址需后端支持，维持原条目的后续项。测试：新增 1 例
  断言专门文案 + 无泛化红错 + 无重试。
