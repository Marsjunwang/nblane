---
status: active
owner: 王军 + kimi
last_verified: 2026-09-24
source_of_truth: 生产上线与 openclaw 第一环集成计划;事实依据 src/nblane/web_api/routes_v1.py、src/nblane/web_api/auth.py、src/nblane/core/auth.py、docs/zh/guides/deployment-tencent-cloud.md、docs/zh/guides/openclaw-integration.md(CW-1..CW-5)、docs/zh/architecture/openclaw-deep-integration.md、docs/zh/dev/phase-plan.md、docs/zh/dev/home-editing-starmap-design.md §7
---

# 生产上线 + openclaw 第一数据环集成计划

> 目标:把已验收的第一数据环(首页星图 → 项目页 → Done 结晶 → 证据评审 →
> 技能树 → 星图/占卜反映成长)从隔离栈(18504)推上生产,并让 openclaw 的
> 既有自动化(晨报 08:30 / 复盘 21:30 / 每周整理)真正接入这条环。
> 验收沿用 phase-plan 总纲:第一数据 loop 全程前端/对话完成,不手改 YAML。

## 0. 现状坐标(均已核实)

- 第一环六个阶段的 API 全部存在于 `src/nblane/web_api/routes_v1.py`:
  `GET /starmap`(:5126)、`GET /projects-board`(:5013)、结晶三段
  `GET /crystallize/candidates` + `POST /crystallize/draft|apply`
  (:3229/:3270/:3338)、证据评审 `GET /evidence-review` + bulk/review/
  skill-links(:2608/:2755/:2950/:3038)、`GET /skill-tree`(:531)、
  `POST /divination`(:5181)。配套写面:`POST /checkins`(:5272)、
  `DELETE /checkins/{id}`(:5351)、`GET/POST /plan-templates[/instantiate]`
  (:5473/:5558)、`PATCH /north-star`(:1992)、goals CRUD(:2144/:2220)、
  `GET /chronicle`(:2343)。
- 习惯生命周期 + 技能进阶后端(**已落地 2026-09-24**):
  `POST /habits/{id}/archive`、`DELETE /habits/{id}`(confirm_title 逐字确认 +
  checkins 连删 + 可选 `habit.deleted`)、证据 `breakthrough` 字段(编辑白名单
  可写)、`GET /skill-tree` 节点 `progress`(规则集中在
  `core/skill_progression.py`,唯一调参处)、PATCH 升阶自动记 `skill.lit`。
  剩余缺口:仅 SPA 前端接线(习惯归档/删除入口、progress 升阶提示),
  后端无新增缺口;`eligible` 只是提示,晋升仍走人工确认的 PATCH。
- SPA(React+Mantine)在隔离栈 18504 验收通过(`docs/zh/dev/phase-plan.md`
  Phase 1–3 节);构建产物提交在 `src/nblane/web_ui/static/`,CI 有
  frontend-artifacts 新鲜度比对。生产侧:`nblane-web-api` unit(8504)写好
  但从未启用;生产 Caddy 只反代 Streamlit 8501 + workshop `/terminal/`。
- 生产数据警告:`/srv/nblane-app` 下有 4 月的过期 profile 数据;真源是
  `/srv/nblane-data`(私有 git,`NBLANE_ROOT` 应指向它)。三树规则见
  `docs/zh/architecture/openclaw-deep-integration.md` §7.1。
- openclaw 本机常驻(gateway 18789 / MCP / CLI),每日计划、每日复盘、每周
  整理三条自动化已在生产经微信运行,但声明只存在于 openclaw workspace;
  nblane 侧 `profiles/template/assistant/automations.yaml` 从未部署
  (`docs/zh/dev/phase-plan.md` 已知风险节)。CW-1..CW-5 人工变更窗口清单
  备在 `docs/zh/guides/openclaw-integration.md`:993–1300。
- Agent 写入契约(`docs/zh/dev/home-editing-starmap-design.md` §7):
  **删除 = 页面确认;其余一切写 = 对话确认;agent-activity.yaml = 留痕簿**。
- 认证现状:8504 只有 cookie 会话(`src/nblane/web_api/auth.py:227`
  `require_user`;登录 :245,TTL 12h :21,限流 :64)。**不存在任何
  service-account / API key 机制**;`NBLANE_READER_TOKEN_SECRET` 只是 HMAC
  密钥(`src/nblane/core/auth.py:98`),不是 bearer token。

---

## 1. 生产上线清单

> **执行状态(2026-09-24)**:A 全部完成(stale profiles 隔离至
> `/srv/nblane-app/deploy-backups/profiles-王军-stale-202604`;数据仓卫生快照
> `10eea35` 已推送;reader 补齐 git 备份变量;CW-1 MCP 已注册,CW-2 备份调度
> `openclaw-backup-scheduled` 已建;A.4 经核实 habit_id 挂接已存在)。
> B 已完成本机侧:8504 unit 启用、users.yaml(wang→admin、openclaw 服务账号)、
> .env 键、Caddy `spa.nblane.cloud` 站点块(含全部 8502 handle + /terminal)、
> 环回冒烟全过(登录/星图/建卡→git commit actor=openclaw→删卡)。
> **公网冒烟已于 2026-09-25 07:50 全部通过**:DNS A 记录生效后 Caddy 自动签发
> 生产证书(LE YE1);https://spa.nblane.cloud 的 health/SPA index/8502 auth
> handoff/服务账号登录+starmap 公网读取全部 200。(注意:Caddy 证书申请在
> DNS 未就位期间会指数退避,最长 6h 重试一次;DNS 生效后 `systemctl restart
> caddy` 可立即触发重试。)
> A.2 的 Git 备份闭环验收已在 B 冒烟中达成(8504 mutation → 数据仓 commit)。

### A. 数据安全(先于一切,低峰窗口)

1. **三树归位核查**:确认 `nblane.service` / `nblane-reader.service` 的
   `NBLANE_ROOT=/srv/nblane-data`(deployment 文档 :189/:240 已是此值)。
   定位 `/srv/nblane-app` 下 4 月的 stale `profiles/`:`diff -rq` 对照
   `/srv/nblane-data/profiles`,确认无独有内容后**隔离不删**
   (`mv profiles /srv/nblane-app/.deploy-backups/profiles-stale-202604`,
   该目录按 deployment 文档 :31 写进 `.git/info/exclude`)。真源以
   `/srv/nblane-data` 的 git log 为准。
2. **Git 备份闭环**:`NBLANE_DATA_GIT_AUTOCOMMIT=1` / `AUTOPUSH=1` 必须在
   全部三个 unit(8501/8502/8504)上(deployment 文档 :323–327 明确警告
   8504 漏配 = SPA 保存无备份)。机制 `src/nblane/core/git_backup.py:116`。
   验收:Web 保存一次 → `/srv/nblane-data` 出现 commit(deployment :601)。
3. **CW-1 / CW-2**(若未执行):MCP 注册 + openclaw 24h 备份调度,清单见
   openclaw-integration.md:1011/:1064。
4. **王军 profile 手工挂接**(phase-plan.md:65 待办):project「保持锻炼」
   写 `habit_id: exercise`(走 case save API,不手改 YAML)。

### B. SPA 上线(8504)

1. **代码与产物**:生产 `git pull --ff-only` + `.venv/bin/pip install -e .`
   (deployment :75–101);确认 `src/nblane/web_ui/static/` 产物是目标版本
   (产物随仓库提交,生产不跑 npm build,同组件惯例)。
2. **`/srv/nblane-data/.env` 必备键**(三 unit 共享 `EnvironmentFile`):
   - `NBLANE_READER_TOKEN_SECRET`(auth 开启后必需,`core/auth.py:110–113`;
     生成命令见 deployment :223–227);
   - `NBLANE_AUTH_COOKIE_SECURE=1`(HTTPS,deployment :469);
   - `NBLANE_WORKSHOP_URL=https://<域名>/terminal/`(对照 dev-web.sh:433);
   - `NBLANE_OPENCLAW_CONSOLE_URL`(SPA 助手页状态卡,web_api/assistant.py);
   - `NBLANE_OPENCLAW_HOOK_TOKEN`(`nblane notify` 用,`core/notify.py:31–33`);
   - 新增:`NBLANE_OPENCLAW_API_PASSWORD`(openclaw 服务账号密码,见 §3.1)。
3. **users.yaml**(`/srv/nblane-data/auth/users.yaml`):人类账号(王军,
   admin)+ **openclaw 服务账号**(member,`profiles: [王军]`,随机强密码,
   `nblane auth hash-password` 生成)。
4. **启用 unit**:`systemctl enable --now nblane-web-api`(unit 模板见
   deployment :293–321;`--workers 1` 因登录限流是单进程内存;
   `NBLANE_TRUST_PROXY_HEADERS=1` 仅在 Caddy 反代就位且 8504 不直连可达后
   开启,否则限流身份可伪造,deployment :473–482)。
5. **Caddy**:按 deployment :418–464 新增**独立子域名** `spa.<域名>`——
   复制主站全部 8502 `handle` 块(尤其 `/auth/*`,缺了 iframe handoff 404),
   catch-all → `127.0.0.1:8504`。`caddy validate` 后 reload。安全组继续只放
   80/443(:567–583)。
6. **冒烟验收**:`GET /api/v1/health`;登录 → 首页星图渲染;一次真实
   mutation(打卡)→ 数据仓出现 commit;Paper Library iframe 在同源子域名下
   不空白(handoff 链路);手机浏览器打开星图。
7. **回滚**:停 `nblane-web-api` + 删 Caddy 站点块即可,8501/8502 不受影响。

### C. Streamlit 退役时什么会断

Streamlit 已冻结(phase-plan.md:29;home-editing-starmap-design.md §10),
页面随 SPA 覆盖逐个退役,终态 8501 整体下线。退役时的真实连带项:

- **无 SPA 对应物的页面**:`pages/4_Team_View.py`(团队功能暂不做,
  phase-plan.md:22)与 `pages/12_Settings.py`(LLM/语言/Codex 设置;
  SPA 无 Settings 页,`AppLayout.tsx:29–42` nav 中无此项)。8501 须保留到
  这两者有结论;主域名 catch-all 继续 → 8501,终态再切到 8504。
- **Blog BlockNote 编辑器子切片未迁**(frontend-spa-migration.md:41
  「剩余」);SPA Studio 目前只有 Markdown 编辑器。重度 Blog 编辑留在 8501。
- **e2e 套件**:`tests/e2e/` 中 Streamlit UI 套件(evidence_editor、
  kanban_toolbar、project_board_timeline、blog_phase3、galaxy_redesign、
  startree_check 等)随页面退役删除或改写;sidecar 独立页套件
  (dashboard_canvas、paper_library*)打的是 8502,不受影响。
- **app.py 首页 3D hero**:随 8501 下线消失;SPA 首页星图为原生实现,无损失
  (phase-plan.md:149–150 已弃用 Streamlit 首页)。
- **8502 永远保留**:Reader/Paper Library/dashboard/blog-editor 路由与
  `/auth/*` handoff 是两套前端共用的基础设施。

### D. 监控与备份

- 活性探针:`/api/v1/health`(8504)、`/auth/session-ok`(8502)、
  Streamlit `_stcore/health`;Caddy 层外部探测。
- `nblane openclaw doctor` 进每周自动化,结果随周报推微信
  (deep-integration §7.4);告警通路 `nblane notify`(`core/notify.py`)。
- 备份矩阵照 deep-integration §7.2:数据仓 per-write autocommit+autopush、
  `~/.openclaw` 每日 tar、季度恢复演练。

---

## 2. 页面删除裁决

### 2.1 周回顾(SPA `ReviewPage` /p/:name/review + Streamlit `pages/8_Review.py`)

**裁决:删,但等 Phase 4 复盘推送闭环落地之后。**

它的三个角色现状:
1. 窗口聚合的**证据候选**(Done→evidence)——已被证据页「待结晶」向导取代
   (phase1 设计;结晶三段 API 已上线);
2. **周统计/体检摘要**——预定去向是 openclaw 周回顾主动推送
   (phase1-evidence-page-design.md:54),**尚未实现**;
3. **next-action 候选与 public-draft 候选**(`core/growth_review.py` +
   review 三端点 :3746/:3843/:3895)——**目前唯一载体**。

删除前置(X):openclaw 晚复盘/周报能把候选集合经对话送达并提供一键处置
(apply/dismiss 端点是通用的,与页面解耦);public-draft 候选并入 Studio
(Studio 已有 candidates/preview|create,:6281/:6303);next-action 候选由
复盘 candidate 链承接。X 达成前保留页面但可以从主导航降为深链。
Streamlit `pages/8_Review.py` 随 8501 终态一起退,不单独删。

### 2.2 健康页(SPA `HealthPage` /health + Streamlit `pages/5_Profile_Health.py`)

**裁决:已执行(2026-09-24 C 尾清理包)**——SPA `HealthPage` 与 nav
「健康」项删除,`/p/:name/health` 重定向到 `/evidence?stage=strengthen`
(五阶段词表中的实际键;本节先前提到的 `stage=risks` 为笔误),档案列表
卡片入口改指 `/home`。`GET /health` API 保留(openclaw/CLI 消费)。

~~裁决:SPA 页现在就可删(nav 移除 + /health 重定向到~~
~~/evidence?stage=risks),但保留 `GET /health` API;前提是接受 §2.2.1 的~~
~~过渡方案,否则等「Settings 档案维护」小项落地。~~

Health 解散是已定案(phase-plan.md:31;phase1-evidence-page-design.md:54),
四个去向逐一核对:
- **证据风险 → 证据页「待补强」:已落地**(`GET /evidence-stages` :3160 +
  SPA 证据页五阶段)。
- **体检报告 → openclaw 周回顾推送:未实现**,列入 §3.4 每周自动化
  (`GET /health` :620 现成,推送只是接 deliver 通道)。
- **成长统计 → 首页/拓片:首页简报行已有,拓片未建**(§4)。
- **数据卫生 → Settings「档案维护」:目标不存在**——`pages/12_Settings.py`
  只有 LLM/语言/Codex 三节,无「档案维护」;SPA 根本没有 Settings 页。
  这是删除的唯一真实损失。

2.2.1 过渡方案(单用户可接受):`analyze_profile_health` 的数据经
`GET /health` 与 `GET /home`(HomeHealthModel)双通道可得,CLI 有
`nblane health <名称>`;数据卫生由 openclaw 周报体检顺带覆盖。正式方案:
SPA 加 Settings/档案维护小节(渲染 `GET /health` 的 validate/sync 类
issue),工作量小,列入 §4 缺口 G5。

### 2.3 GapPage(SPA /gap + Streamlit `pages/2_Gap_Analysis.py`)

**裁决:删,前置一个小改动——给占卜卦辞卡接「化为任务」动作。**
**(前置与本体均已于 2026-09-24 落地:正占卦辞卡「化为任务」把卦象锚定的
gap 缺节点逐一 POST /gap/intake 入看板 Queue,双失效 + /projects 深链
小笺;GapPage 页面/nav 本体同日删除——`pages/GapPage.tsx`(+测试)、
`/p/:name/gap` 路由、nav「差距分析」与 `useGapAnalyze`/`useGapDeepAnalyze`/
`useGapIntake` 钩子移除,两个 /gap 端点保留。)**

差距分析已按定案变成首页占卜(phase-plan 星图五轮 :284–297):
`POST /divination` 正占直接跑 `core.gap` 真规则并包成卦辞,LLM 润色走
`divination.cast` 网关动作(:5181–5211)。GapPage 独有的是:LLM 深度分析
面板(jobs/SSE `gap/analyze` use_llm)和 `POST /gap/intake` 一键入看板
(:3600)。前者功能上被 `divination.cast` 的 LLM 润色覆盖;后者只需在
卦辞卡加一个动作按钮复用同一端点。**两个 /gap 端点保留**(openclaw 可调),
只删页面与 nav 项(`AppLayout.tsx:34`)。Streamlit 版随 8501 终态退。

---

## 3. openclaw × 第一数据环集成设计

### 3.1 服务账号与认证(先行小项,决定一切)

- **账号**:users.yaml 加 `openclaw`(member,`profiles: [王军]`)。权限
  面由 `require_profile_access`(routes_v1.py:407)天然收窄到王军一个
  profile,admin 面不暴露。
- **登录方式(推荐)**:`POST /api/v1/auth/login` 拿 cookie(web_api/auth.py
  :245),cookie TTL 12h(:21),自动化每次运行先登录一次——脚本化登录受
  限流保护但每天 3 次远低于阈值(5 次/60s)。无新增长效密钥。
- **备选**:用 `core.auth.mint_auth_session_token('openclaw', ttl_seconds=
  7*24*3600)`(:187)铸长效 token 直接当 cookie 值下发(`require_user`
  验 HMAC + users.yaml 存在性即放行)。只在登录链路出问题时作 fallback;
  长效密钥泄露面更大,不作首选。
- **Base URL**:`http://127.0.0.1:8504`——gateway(18789)与 8504 同机,
  agent 流量走 loopback,不经过 Caddy,不依赖公网域名。
- **客户端**:新增 `scripts/openclaw/skills/bin/nblane_api.py`(httpx;
  login → cookie jar;GET/POST;mutation 首次不带 If-Match、412 时重取
  ETag 重试一次——照抄 SPA 的 postEtagMutation 纪律;**硬编码拒绝一切
  DELETE/discard 类调用**)。prompt 里只出现 `nblane_api checkin ...`
  这样的子命令,不出现绝对路径(三树漂移免疫)。
- **为什么不用 MCP 补这些面**:MCP(`mcp_server.py`)的写面刻意更窄
  (candidate 分级),没有 starmap/checkins/divination/plan-templates/
  north-star/goals;第一环需要完整 API 面。两条路共享 core 写路径与
  flock/ETag 纪律,不冲突。MCP 继续承担读本(kanban/goals/summary)与
  candidate 提交。

### 3.2 留痕簿:agent 动作可审计(契约 §7 的硬要求)

现状缺口(**已于 2026-09-24 由 G1/G2 闭合**):~~直接 API mutation 不落
agent-activity~~——writeback 此前只有 Review/Studio 流写
(`core/review_actions.py` `record_writeback_activity`);~~8504 的 git
commit actor 是默认 "cli"~~(现由 `GitActorMiddleware` 按请求设为当前
用户 id,core/git_backup.py `start_operation`)。

建设(G1/G2,见 §4;**均已落地 2026-09-24**):
- **G1**:web_api 在 mutation 完成且 `CurrentUser.id == "openclaw"` 时追加
  writeback 条目(`kind=writeback`、`source_page="openclaw"`、
  `status="applied"`、note=动作摘要、refs、changed_paths),复用
  `record_writeback_activity`(routes_v1 `_record_agent_writeback`;
  `source_ref` 带唯一后缀保证每次 mutation 各成条目;no-op 不留痕,其他
  用户不留痕;新增非人类账号时放宽 id 判断即可扩展)。覆盖第一环写面:
  checkins POST/DELETE、kanban cards POST/DELETE + move/done/schedule/
  patch、goals POST/PATCH、PATCH north-star、plan-templates instantiate、
  结晶 apply、证据 review/skill-links/edit、skill-tree 节点 PATCH、habits
  archive/delete、project case save/archive/delete。
- **G2**:web_api 每个请求经纯 ASGI `GitActorMiddleware`
  (web_api/auth.py)以 user id 调 `git_backup.start_operation(actor=
  user.id)`——与 `require_user` 共享 `_resolve_request_user` 会话解析;
  auth 关闭时 actor 为合成账号 `local`。git 历史与留痕簿互证。
- 留痕簿消费面已有:SPA 代理活动页(ActivityPage)+
  `GET /activity`(:647)可筛选 `kind=writeback`。

### 3.3 分级授权映射(契约 §7 落到端点)

| 级别 | 端点 | openclaw 行为 |
|---|---|---|
| 页面确认(删除类) | `DELETE /checkins/{id}`、project case delete、inbox discard | **禁止调用**;客户端硬拒;对话中回「删除请到这里操作」+ SPA 深链 |
| 对话确认(其余写) | POST /checkins、kanban move/done/schedule/patch、PATCH north-star/goals、plan instantiate、crystallize draft/apply、evidence review/skill-links | 先复述动作 → 用户回「好」→ 执行 → 回执(含新 ETag/结果)→ G1 留痕 |
| 直读 | 全部 GET、`POST /divination`(不落盘,:5198 明示 single-consumption) | 免确认 |

确认规则写进 `profiles/王军/assistant/prompts/`(部署即生效,随数据仓
版本化),不靠 openclaw 侧散落记忆。

### 3.4 分阶段接线(第一环六站)

1. **晨报 08:30(daily-plan)**——展示/排期一站。
   prompt 升级:`profile://kanban`+`profile://goals`(MCP 读本,现状)
   之外,经 nblane_api 加 `GET /starmap`(counts:点亮/在学/客星数)与
   `GET /chronicle?limit=40`——直接搬首页简报行语义(本月新立目标 N /
   新镌 M 星,briefing.ts 同源数据);`GET /projects-board` 给今日排期与
   习惯待打卡清单。产出仍 ≤3 条重点,deliver 微信。
2. **微信打卡 → POST /checkins**——任务推进一站。
   「锻炼打卡」→ 复述确认 → `POST /checkins {habit:"锻炼"}`(支持标题或
   habit 链接项目,:5236–5269)→ 回执附 streak(回读 /projects-board
   habits)。销印属删除类,页面确认。
3. **晚复盘 21:30(daily-review)**——结晶与推进一站。
   对照晨报与 /projects-board;可验证进展照旧走 MCP
   `append_growth_log`+`log_interaction`;新增**一键动作**:「把 X 移到
   Done?」「给 Done 的 Y 起结晶草稿?」——确认后分别调
   `POST /kanban/cards/{ref}/done` 与 `POST /crystallize/draft`(规则版
   同步 200 无需 LLM);结晶 apply 前回显草稿全文。动作逐条 G1 留痕。
4. **证据评审**——评级/技能关联是人的仪式,不代办:复盘里把待评审计数
   (`GET /evidence-stages`)与快评深链(/evidence?stage=review,j/k/a/s
   键盘流)送达即可;用户若在微信里明确指令「接受 E1 并关联 robotics-ros」,
   走对话确认调 `POST /evidence/{id}/review|skill-links`。
5. **每周(weekly-maintenance + 新 nblane:weekly-divination)**——成长反映
   一站。周日流程:自治整理照旧;新增 `POST /divination`(戏占;用户点名
   正占需带所问之事)→ 卦辞推微信(卦象对(档案,日,模式)确定性,
   :5196–5198,推送与首页所见一致);`GET /health` 摘要随周报推送(落实
   Health 解散的「体检→openclaw 周回顾」);`nblane openclaw doctor` 结果
   附尾(deep-integration §7.4)。
6. **计划实例化**——「我想开始 30 天减脂」→ `GET /plan-templates` 列内置
   3 个 → 确认 → `POST /plan-templates/instantiate`(:5558,一次建成
   habit-plan case + habit + 历史)→ 回执附项目泳道深链。习惯与项目当即可
   在 /projects 与首页日课印出现,环闭合成环。

### 3.5 部署方式(自动化即代码收口)

> **执行进展(2026-09-24)**:`profiles/王军/assistant/automations.yaml` 与
> 4 个 prompt(daily-plan / daily-review / weekly-maintenance /
> weekly-divination)已按 §3.3/§3.4 写入数据仓(`/srv/nblane-data`),模板侧
> 已同步回灌(含新增 `nblane:weekly-divination`)。**已于 2026-09-24
> `--apply` 完成 CW-3**:4 条 `nblane:*` 全部上线并与声明一致,旧 3 条
> `personal-assistant:*` 按灰度方案 A 并存,验证一个周期后由用户手工停用。
> 配套落地:`install.sh` 现在会建 `~/.openclaw/workspace/skills/.venv`
> (httpx)并生成包装命令 `bin/nblane_api`(prompt 调用形态,无绝对路径);
> gateway 经 user unit drop-in(0600)注入 `NBLANE_OPENCLAW_API_PASSWORD`。
> 过程中修复三处 2026.9 CLI 漂移:add 需显式 `--name`、main 会话任务只收
> `--system-event` 且忽略 model/deliver、`automations list` 改为 jobs 包裹 +
> payload 嵌套字段(见 `core/openclaw_automations.py` 与
> `core/openclaw_ops.py` 及对应测试)。

- 把现有 3 条 `personal-assistant:*` 自动化纳管进
  `profiles/王军/assistant/automations.yaml`(模板:
  `profiles/template/assistant/automations.yaml`),prompt 按 §3.4 改写;
  执行 CW-3 清单(openclaw-integration.md:1108–1177):先
  `nblane openclaw automations sync --dry-run` 人工审,再 `--apply`;
  `nblane openclaw sync --check` 进 cron 周报防漂移。
- 新自动化 `nblane:weekly-divination` 直接写进声明文件一并 sync。
- 铁律:一切对生产 gateway 的变更先 dry-run、低峰窗口;脚本永不调
  `openclaw doctor --fix`(deep-integration §9.2)。

---

## 4. 剩余环缺口(按价值排序)

| # | 缺口 | 为什么排这 | 落点 |
|---|---|---|---|
| G1 | ~~**agent writeback 留痕**(mutation 落 agent-activity)~~ **已落地 2026-09-24** | 没有它,§7 契约不可审计,openclaw 上线即裸奔 | web_api mutation 层 + `record_writeback_activity` |
| G2 | ~~**git actor = 当前用户**~~ **已落地 2026-09-24** | 与 G1 互证,一行级改动 | web_api 请求生命周期 |
| G3 | ~~**技能状态写 API**(PATCH skill-tree 节点 status)~~ **已落地 2026-09-24** | 第一环唯一没有 API 写面的阶段——证据评审后点亮技能仍要手改 YAML,直接卡 phase-plan 验收标准 | `PATCH /profiles/{name}/skill-tree/nodes/{id}`(status 域 locked/learning/lit,lit 落 YAML `solid`,ETag/412 样板照抄;技能树页铭文卡三态步进器已接上) |
| G4 | **拓片**(chronicle + claims 年度叙事) | 成长统计的定案去向(首页/拓片),chronicle.yaml 数据已在累积(home-editing-starmap-design.md §8),只欠渲染 | 先只读 API + 首页入口 |
| G5 | **Settings 档案维护 / 首页健康印** | Health 页删除的正式承接(§2.2) | SPA Settings 小节渲染 `GET /health` |
| G6 | ~~**证据按技能过滤**(`GET /evidence?skill=`)~~ **已落地 2026-09-24** | 星官卡入座名录与 openclaw 查询都绕 `evidence_usage_index`;现 list 只有 status/q(:2462) | 一个 query 参数 `skill_id`(与 status/q/limit 正交;技能树铭文卡「关联证据」已消费) |
| G7 | **用户初始化仪式** | phase-plan.md:329–334 已定方向(领域 schema 模板库 + AI 草案 + openclaw 对话访谈入口);多用户才需要,单用户上线不阻塞 | Backlog,随 IA 重设计排期 |

不建议做:MCP 补齐第一环写面(与 HTTP 双写面重复维护;§3.1 已论证)。

---

## 5. 执行顺序(变更窗口串联)

1. A 数据安全(§1A 1–4)→ B SPA 上线(§1B 1–6,冒烟过)→
2. G1/G2/G3 三个小后端项( pytest + CI 五关)→
3. openclaw 服务账号 + nblane_api 客户端(§3.1/3.2)→
4. prompt 改写 + CW-3 纳管 + 新增 weekly-divination(§3.4/3.5)→
5. 页面删除:~~GapPage(卦辞卡接 intake **已落地 2026-09-24**)~~ **页面/nav
   本体已删除 2026-09-24**(/gap/analyze 与 /gap/intake API 保留)、
   周回顾(复盘推送闭环后)、
   ~~SPA HealthPage(接受 §2.2.1 过渡即可先行)~~ **已删除 2026-09-24**
   (/health → /evidence?stage=strengthen,API 保留)→
6. 观测两周:留痕簿抽查、git 历史、自动化投递、412 重试日志 →
7. Streamlit 终态评估(Settings/Team/BlockNote 三遗留有结论后切主域名)。

## 6. 风险与回滚

| 风险 | 缓解 |
|---|---|
| 8504 上线即暴露完整写面 | 服务账号仅 member+单 profile;登录限流;TRUST_PROXY_HEADERS 开启条件(deployment :473);loopback-only |
| openclaw 误执行写 | 客户端硬拒删除类;对话确认复述制;G1 留痕 + git autocommit 双审计,任何写可回滚到数据仓历史 |
| 自动化 prompt 漂移 | 声明入数据仓版本化 + `nblane openclaw sync --check` 周报 |
| /srv/nblane-app stale 数据被误读 | §1A.1 隔离 + unit NBLANE_ROOT 核查;openclaw prompt 禁绝对路径 |
| 占卜 LLM 不可用 | divination 有 rule 兜底(source="rule",:5194–5197),周报降级为规则卦,不阻塞 |
| Streamlit 退役中途 | SPA parity 未达标不退役(frontend-spa-migration 决策记录 5);8501 保留到三遗留(§1C)有结论 |
