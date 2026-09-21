---
status: active
owner: nblane-team
last_verified: 2026-09-21
source_of_truth: src/nblane/web_api/、src/nblane/web_ui/frontend/、scripts/dev-web.sh、docs/zh/architecture/integration-audit-2026-09-20.md
---

# nblane 体验官手册：融合 + SPA 全功能走查（2026-09-20）

> 目的：逐一体验本轮全部交付（React SPA 17 页、web_api 后端、OpenClaw 融合
> CLI、打包），记录不足，最后集中修复（95 → 100）。
> 使用方法：按章节顺序走，每步对照「预期」，✅/❌ 勾选；发现问题记到文末
> 「问题记录表」（不用管格式，写清现象+复现步骤即可）。
>
> **红线（全程有效）**：不要执行任何会改动生产 OpenClaw 的命令——
> `openclaw config set/patch`、`openclaw gateway restart`、`openclaw automations add/run`、
> 插件 install/uninstall、`openclaw doctor` 都不行。本文列的命令全部是只读
> 或 `--dry-run`，已逐条核对过。

---

## 0. 启动环境（5 分钟）

> **本机（VM-0-5）注意**：默认模式的 8502 被**生产** Reader API 占用（不能杀），
> 所以 `scripts/dev-web.sh` 默认模式在这台机器上起不来。**请用隔离模式**——
> 端口 18502/18503/18504，数据在 `.dev-data/`（沙箱，随便折腾不污染真实数据）。

> **认证已启用（2026-09-21 起）**：隔离实例的 SPA 后端（18504）已开启应用层登录
> （检测到 `.dev-data/auth/users.yaml` 自动启用，文件里只有沙箱测试口令）。
> **测试账号：`admin` / `test1234`**（管理员，全部 profile 可见）；
> **`member` / `test1234`**（成员，仅见 dev profile，用于 §1.7 授权过滤验证）。
> Streamlit（18503）与 Reader sidecar（18502）仍保持免登录，日常走查与老 e2e
> 不受影响。若发现 18504 不再拦登录，多半是 `.dev-data/auth/users.yaml` 被挪走
> ——`scripts/dev-web.sh` 只在检测到该文件（或显式 `--auth-file`）时开认证。

```bash
cd /home/ubuntu/nblane
scripts/dev-web.sh --isolated   # 启动三服务（若已在跑会提示；当前已经有一组在跑）
scripts/dev-web.sh status       # 确认 nblane-dev-reader-api / nblane-dev-streamlit-ui / nblane-dev-web-api 都在
```

| # | 检查 | 预期 | 结果 |
|---|------|------|------|
| 0.1 | 浏览器开 `http://127.0.0.1:18504/`（本地或 SSH 转发 18504） | 看到「nblane 登录」页（认证已启用）；用 admin/test1234 登录后进入档案列表 | ☐ |
| 0.2 | `curl -s http://127.0.0.1:18504/api/v1/health` | 返回 JSON `{"ok":true,...}` | ☐ |
| 0.3 | `curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:18504/p/dev/kanban` | 输出 `200`（客户端路由回退 index.html；注意用 GET 不要用 `-I`，HEAD 目前返回 405，已记入修复批次） | ☐ |
| 0.4 | `curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:18504/api/v1/auth/me` | 未带 cookie 输出 `401`（认证确已开启；不是 200） | ☐ |
| 0.5 | 手机体验（可选）：SSH 转发 `ssh -L 18504:127.0.0.1:18504 服务器`，手机浏览器开电脑 IP:18504 | 登录页可用、登录后导航可点 | ☐ |

> 想体验真实 `王军` 数据：告诉我一声，我用备用端口起一组默认实例
> （`scripts/dev-web.sh --reader-port 8512 --streamlit-port 8513 --web-api-port 8514`，
> 绕开生产 8502）。**不要**直接 kill 8502 上的 uvicorn，那是生产服务。

---

## 1. 认证与导航（约 10 分钟）

> 账号：`admin` / `test1234`（管理员）、`member` / `test1234`（仅 dev profile）。
> 以下 a–f 旅程已被真实浏览器 e2e 覆盖（`tests/e2e/spa_auth.spec.ts`，6 条），
> 本表是人工复核口径；发现问题先对照 e2e 是否也红。

| # | 步骤 | 预期 | 结果 |
|---|------|------|------|
| 1.1 | **无痕窗口**访问 `http://127.0.0.1:18504/p/dev/kanban`（确保无旧 cookie） | 自动跳到 `/login`（标题「nblane 登录」）；用 admin/test1234 登录后**回到 `/p/dev/kanban` 看板页**而不是档案列表首页（修复 M-FE-3） | ☐ |
| 1.2 | 登录页：用户名 admin + 任意错误密码提交；再换一个**不存在的用户名**（如 `nosuchuser`）+ 任意密码提交 | 两次红条提示逐字相同：`Invalid username or password`（通用文案，不泄露账号是否存在）；仍停留在 `/login` | ☐ |
| 1.3 | 限流：用**独立测试名**（如 `locktest1`，⚠️ 不要用 admin/member，免得锁住后面步骤）连续错密码 5 次，第 6 次提交 | 前 5 次都是通用 401 提示；第 6 次提示 `Too many failed login attempts; try again later`（该用户名限流 60 秒，按 IP+用户名计桶，不影响其他账号） | ☐ |
| 1.4 | admin 登录后，左侧导航 17 项逐一点一遍 | 每页都能打开；当前页高亮正确（重点看「证据」vs「证据评审」不会同时亮） | ☐ |
| 1.5 | 点页面右上角「退出登录」 | 回 `/login`；再直接访问 `http://127.0.0.1:18504/p/dev/kanban` 被拦回 `/login` | ☐ |
| 1.6 | 会话过期模拟：重新登录后，DevTools → Application → Cookies → 删除 `nblane_auth_session`，再刷新内页 | 自动跳回登录页，而不是困在错误页（修复 M-FE-2） | ☐ |
| 1.7 | 登出后改用 `member` / `test1234` 登录，打开档案列表 `/`；再直接访问 `http://127.0.0.1:18504/p/王军/kanban` | 档案列表**只显示 dev** 一张卡（admin 登录可见 dev/e2e-local/王军 等全部）；直接深链未授权 profile 拿不到数据（后端 403，范围校验先于 404，连 profile 是否存在都探不到）（修复 M-API-1） | ☐ |

---

## 2. SPA 页面逐页走查（核心，约 60–90 分钟）

每页看四件事：加载态、空态（无数据时）、错误态（可拔 API 模拟）、移动端窄屏。

### 2.1 首页 Home（`/p/<name>/home`）
| # | 步骤 | 预期 | 结果 |
|---|------|------|------|
| 1 | 打开 | iOS 式三段：焦点卡（北极星+主目标进度/目标日期/stalled 提示）→ 成长星系 hero → 今日待办聚合带（待审批/待评审/Doing 前 3，点击跳对应页）；无快捷入口条、无平铺卡片阵 | ☐ |
| 2 | 3D 星系区域（sidecar 可达） | 全宽内嵌 iframe 直接展示（不再是折叠卡片）；指标 chip 悬浮于星系上可点击入潜；iframe 指向本栈 reader 端口（隔离实例=18502，不再是 8502 拒绝连接页） | ☐ |
| 3 | 3D 星系区域（sidecar 不可达） | 优雅降级为静态指标带（点亮率/进行中/待评审 + 重试按钮），不出现浏览器「refused to connect」灰框 | ☐ |

### 2.2 收件箱 Inbox（`/p/<name>/inbox`）
| # | 步骤 | 预期 | 结果 |
|---|------|------|------|
| 1 | 捕获一条想法 | 列表即时出现新条目 | ☐ |
| 2 | 点条目 → clarify → 发到看板 Queue | 成功提示；去看板页能看到卡 | ☐ |
| 3 | archive / discard 各试一条 | 状态流转，筛选 Tab 计数变 | ☐ |
| 4 | 打开详情模态框后切换筛选 Tab | 条目消失时模态框自动关闭（不再空壳） | ☐ |

### 2.3 看板 Kanban（`/p/<name>/kanban`）
| # | 步骤 | 预期 | 结果 |
|---|------|------|------|
| 1 | 建卡（标题留空提交一次） | 留空被拦（422 提示）；正常建卡成功 | ☐ |
| 2 | 挪卡到 Doing → 完成 | 列间移动、日期自动记录 | ☐ |
| 3 | **双人并发测试**：开两个浏览器标签都打开看板，A 挪一张卡，B 再挪另一张 | B 看到黄色「数据已被他人修改」提示 + 刷新按钮（412 闭环） | ☐ |
| 4 | 建两张同名卡，尝试移动其中一张 | 橙色提示说明重名需先去 kanban.md 消歧（已知限制，非崩溃） | ☐ |
| 5 | 同列拖拽：Queue 里把一张卡拖到另一张上 | 列内拖拽排序可落库——松手调 move（带 to_index），顺序变化且刷新后保持；跨列拖到某张卡上则插到该卡位置（不再总是列尾） | ☐ |

### 2.4 代理活动 Agent Activity（`/p/<name>/activity`）
| # | 步骤 | 预期 | 结果 |
|---|------|------|------|
| 1 | 有 pending 项时 apply / dismiss | 仅 Review 来源的 pending 项显示「应用」；其他来源（如 AI Gateway）只显示「驳回」+ 来源说明（P0-2 修复后行为，与 Streamlit 一致）。可 apply 项 apply 后数据真被写入（如 kanban_move 真挪卡） | ☐ |
| 2 | 另一标签改动数据后再 apply | 412 黄色提示（修复后不再静默覆盖） | ☐ |

### 2.5 证据 Evidence + 证据评审 Evidence Review（两页）
| # | 步骤 | 预期 | 结果 |
|---|------|------|------|
| 1 | Evidence 页浏览/搜索/详情 | 列表+详情正常；页面上「编辑开发中」提示符合预期（已知只读） | ☐ |
| 2 | Review 页：勾选多条 → 批量接受 | 全选/选待审核好用；成功后列表刷新、横幅随后消失 | ☐ |
| 3 | 批量打标（强度/置信度/公开就绪） | 菜单二级项可点，值写回 | ☐ |
| 4 | 拒绝（deprecated）→ 切到 deprecated 视图恢复 | 往返正常 | ☐ |
| 5 | 窄屏（手机或拖窄窗口） | 表格可横向滚动不破版（修复项） | ☐ |

### 2.6 差距分析 Gap（`/p/<name>/gap`）

> 本表 1–3 已被真实浏览器 e2e 覆盖（`tests/e2e/spa_pages.spec.ts`「SPA Gap」，
> 2 条，2026-09-21）；4–5 由 `tests/e2e/spa_gap_deep.spec.ts` 覆盖（stub 快
> 路径 + 沙箱真实 LLM 慢路径，2026-09-21），本表是人工复核口径。

| # | 步骤 | 预期 | 结果 |
|---|------|------|------|
| 1 | 输入一段任务描述 → 分析 | 出覆盖率条、已具备/差距两栏、建议行动 | ☐ |
| 2 | 差距节点点「加入看板」 | 成功提示；看板 Queue 出现学习卡（标题为「学习 <节点名>」） | ☐ |
| 3 | 空描述提交 | 客户端拦截不发请求（纯空格同样被拦） | ☐ |
| 4 | 点「深度分析(LLM)」 | 进度卡出现（排队中→路由中→合并中），约 1 分钟内出结果（jobs + SSE 基建，2026-09-21 接入） | ☐ |
| 5 | 深度分析结果 | 同版型渲染，紫色「LLM 深度分析」徽章 + 根因来源行（规则/LLM 各几项）；LLM 不可用时黄色降级提示并回退规则结果 | ☐ |

### 2.7 周回顾 Review（`/p/<name>/review`）
| # | 步骤 | 预期 | 结果 |
|---|------|------|------|
| 1 | 默认本周窗口打开 | 四类候选（证据/下一步/公开草稿/方法笔记）+ 汇总徽章 | ☐ |
| 2 | 自定义窗口（起 > 止） | 自动交换或 422 提示 | ☐ |
| 3 | 勾选候选 → 保存到活动 → 应用写回 | 逐候选结果显示；失败单项不拖垮整单 | ☐ |
| 4 | 窄屏 | 候选表格可横向滚动 | ☐ |

### 2.8 项目看板 Project Board（`/p/<name>/project-board`）

> 本表 1–4 已被真实浏览器 e2e 覆盖（`tests/e2e/spa_pages.spec.ts`
> 「SPA Project Board」，2 条，2026-09-21）；第 3 行的 jobs/SSE 链路由
> `tests/e2e/spa_llm_jobs.spec.ts` 覆盖（stub 快路径 + 沙箱真实 LLM 慢
> 路径，2026-09-21），本表是人工复核口径。
> **注意（2026-09-21 实测）**：隔离实例的 web-api 会 source 仓库 `.env`，
> 即沙箱**有活 LLM**——第 3 行的真实行为是真跑 AI job（见行内）；
> 「无 LLM 降级卡」只在未配 LLM 的栈上出现，e2e 用 stub 的 job-error
> 契约覆盖。

| # | 步骤 | 预期 | 结果 |
|---|------|------|------|
| 1 | 建项目案例 → 加里程碑 → 建任务 | 全链路可用；任务出现在 kanban | ☐ |
| 2 | **草稿保护**：在「基本信息」Tab 改标题不保存，切到「任务」Tab 挪一个任务，再切回 | 未保存的标题还在（修复 M-FE-1） | ☐ |
| 3 | AI 建议引用 | 先出进度卡（排队中→收集候选→生成建议，jobs + SSE 基建，2026-09-21 接入）；沙箱（有 LLM）：job 完成出蓝色「AI 引用建议」卡（可合并到表单）；provider 结构化输出校验失败时出黄色「AI 建议不可用」卡。未配 LLM 的栈：稳定出黄色降级卡（非报错） | ☐ |
| 4 | 归档案例 | 状态流转：详情徽标变「已归档」、归档按钮消失、案例卡移入「已归档」状态 Tab | ☐ |

### 2.9 输出工作室 Studio（`/p/<name>/studio`）

> 本表 1–4 已被真实浏览器 e2e 覆盖（`tests/e2e/spa_pages.spec.ts`
> 「SPA Studio」，3 条，2026-09-21）；第 4 行的 jobs/SSE 链路由
> `tests/e2e/spa_llm_jobs.spec.ts` 覆盖（stub 快路径 + 沙箱真实 LLM 慢
> 路径，2026-09-21），本表是人工复核口径。
> LLM 注意事项同 §2.8（沙箱有活 LLM：JD 匹配真实分析约 55 秒，期间
> 进度卡实时显示；「无 LLM 降级卡」只在未配 LLM 的栈出现，e2e 用
> stub 的 job-error 契约覆盖）。

| # | 步骤 | 预期 | 结果 |
|---|------|------|------|
| 1 | 博客 Tab：新建文章 → 编辑 Markdown → 保存 | 保存成功；ETag 并发保护（可两标签测 412） | ☐ |
| 2 | 发布检查 → 发布 | 缺 summary 被门控拦（检查红卡列出缺项；发布 422 `blog_publish_blocked` 红条提示）；补全后可发布，状态徽标变「已发布」 | ☐ |
| 3 | 「从证据生成」Tab 选证据 → 预览 → 建草稿 | 草稿出现在博客列表（沙箱有 LLM 时预览/建稿各有一次真实 LLM 调用，约十几秒） | ☐ |
| 4 | JD 匹配 Tab | 先出进度卡（排队中→分析中→生成中，jobs + SSE 基建，2026-09-21 接入）；沙箱（有 LLM）：约 55 秒后 job 完成出真实匹配分析卡；未配 LLM 的栈：黄色「AI 分析不可用」降级卡片（非报错） | ☐ |

### 2.10 研究台 Research（`/p/<name>/research`）

> 本表 1–2 已被真实浏览器 e2e 覆盖（`tests/e2e/spa_pages.spec.ts`
> 「SPA Research」，2 条，2026-09-21），本表是人工复核口径。

| # | 步骤 | 预期 | 结果 |
|---|------|------|------|
| 1 | 打开 | 来源统计卡片（总数/进行中/断言/引用 + 状态与类型分布）+ 最近 8 条来源表 + Paper Library 入口卡 | ☐ |
| 2 | 点 Paper Library（「嵌入显示」iframe 或「新标签打开」） | sidecar 页面打开（需本栈 reader 端口在跑：默认实例 8502、隔离实例 18502，页面坐标随栈走）；认证开启时首次自动经隐藏表单 POST `/auth/session` 带认证，iframe 文档真实 200 | ☐ |

### 2.11 公开构建 Public Build（`/p/<name>/public-build`）

> 本表 1–3 已被真实浏览器 e2e 覆盖（`tests/e2e/spa_public_build.spec.ts`，
> 2 条，2026-09-21），本表是人工复核口径。沙箱 dev 档案为
> `visibility: private`，生产模式构建会被可见性门禁拦（预期行为，见第 3 行）。

| # | 步骤 | 预期 | 结果 |
|---|------|------|------|
| 1 | 打开 | 状态总览卡（校验通过/错误徽标、最近构建时间、产物计数、输出目录 `.dev-data/dist/public/dev`）+ 待发布草稿列表 + 说明卡（同步构建、目录固定、部署在外部） | ☐ |
| 2 | 开「包含草稿」→ 构建静态站 | 绿色「已构建」反馈；产物表出现 index.html 等文件，点击新标签打开真实 HTML；整站预览 iframe 渲染站点首页 | ☐ |
| 3 | 关「包含草稿」（private 档案）直接构建 | 422 红条提示 visibility 门禁（与 Streamlit 一致，非故障） | ☐ |
| 4 | 勾选草稿 → 发布并构建 | 草稿状态翻 published 并立即重建；首篇失败时 422 命名该 slug、已发布的不回滚（与 Streamlit 同语义） | ☐ |
| 5 | 窄屏 | 产物表可横向滚动不破版；预览 iframe 整宽 | ☐ |

### 2.12 其余页面快速过
| # | 页面 | 预期 | 结果 |
|---|------|------|------|
| 1 | 技能树 `/p/<name>/skill-tree` | schema 层级展示、状态徽标 | ☐ |
| 2 | 目标 `/p/<name>/goals` | 北极星 + 目标列表（编辑按钮提示开发中属已知） | ☐ |
| 3 | 健康 `/p/<name>/health` | 健康报告渲染 | ☐ |
| 4 | 助手 `/p/<name>/assistant` | OpenClaw 状态探针卡片（Gateway/自动化/MCP 状态；MCP 未接通显示未配置属预期） | ☐ |
| 5 | 档案列表 `/` | 只显示你有权限的 profile（修复 M-API-1） | ☐ |

---

## 3. OpenClaw 融合 CLI 体验（只读/dry-run，约 15 分钟）

```bash
cd /home/ubuntu/nblane
nblane validate                                    # 全量校验
nblane status                                      # 技能树摘要
nblane openclaw doctor --profile 王军               # 8 项检查（只读）
nblane openclaw sync --check                       # 语料漂移检查（只读）
nblane openclaw automations sync 王军               # 自动化对账（默认 dry-run）
nblane openclaw install --dry-run                  # 安装预演（会向 live 发 dry-run patch，安全）
nblane notify --dry-run "测试消息"                  # webhook 干跑
nblane sync-agent-harness --target openclaw --profile 王军   # 看 MCP 注册 snippet
```

| # | 检查 | 预期 | 结果 |
|---|------|------|------|
| 3.1 | doctor | 8 项检查逐项输出 pass/warn/fail；不会改任何东西 | ☐ |
| 3.2 | sync --check | 有漂移时列出文件并退出 1；无漂移安静退出 0 | ☐ |
| 3.3 | automations sync | 打印计划（add/edit/skip）；不写生产 | ☐ |
| 3.4 | install --dry-run | 打印四步计划 + patch 全文；零落盘 | ☐ |
| 3.5 | 删除 `~/.openclaw/workspace/memory/nblane/` 里某个生成文件（先备份），再跑 `nblane openclaw sync` | 能重新生成；反向：手动放个旧文件跑 sync 会被清理（M-BE-2 修复验证） | ☐ |

---

## 4. 并发与冲突专项（验证审查修复，约 10 分钟）

| # | 步骤 | 预期 | 结果 |
|---|------|------|------|
| 4.1 | 两标签开同一博客文章编辑，A 保存后 B 保存 | B 收到 412 冲突提示 + 刷新按钮，内容不丢（可恢复） | ☐ |
| 4.2 | 两标签开证据评审，A 批量接受后 B 批量打标 | B 412 提示 | ☐ |
| 4.3 | Streamlit 看板（18503）和 SPA 看板（18504）同时操作同一 profile | 不再互相静默覆盖（file_lock + 锁内快照复核） | ☐ |

---

## 5. 移动端专项（约 10 分钟）

> 本表 5.1–5.4 已被真实浏览器 e2e 自动化覆盖（`tests/e2e/spa_mobile.spec.ts`，
> 9 条，viewport 375×812 + 触屏模拟，2026-09-21，两轮单跑全绿），
> 本表是人工复核口径；发现问题先对照 e2e 是否也红。e2e 与人工的剩余差异
> 见表下「人工复核项」。

| # | 步骤 | 预期 | 结果 | e2e 覆盖 |
|---|------|------|------|------|
| 5.1 | 手机或 DevTools 375px 宽：导航 | 汉堡菜单可开合，17 项可点（抽屉 15 个 profile 页项 + 档案列表 + 头部助手）；点「看板」正确跳转并收合 | ☐ | ✅ 自动化（开合状态读 navbar 离屏 transform 断言，逐项点击 + 收合断言） |
| 5.2 | 证据评审/周回顾/项目看板/研究台/证据 五页宽表格 | 可横向滚动，不破版（Table.ScrollContainer 滚动 + 文档无横向溢出双重断言） | ☐ | ✅ 自动化（评审页队列耗尽时走空态分支，同样断言不溢出） |
| 5.3 | 看板拖拽/挪卡 | 触屏可用：真 CDP 长按拖拽 Queue→Doing（TouchSensor 250ms 长按 + auto-scroll）实测落库；「…」菜单挪列 tap 回退亦覆盖 | ☐ | ✅ 自动化 |
| 5.4 | 收件箱快速捕获 | 手机上能单手完成（375px 下标题框整宽可见——2026-09-21 已修 26px 挤压 bug）；提交成功且无横向溢出 | ☐ | ✅ 自动化（输入框宽度下限断言锁定回归） |

**人工复核项**（e2e 无法代答，仍建议真机过一遍）：横滑表格时的手感与
滚动惯性；长按拖拽与页面滚动在真机浏览器（尤其 iOS Safari）上的手势
竞争；通知 toast 在窄屏下的遮挡可接受度；字体/点击目标大小的主观舒适度。

---

## 5A. 宽屏专项（约 10 分钟）

> 本表 5A.1–5A.4 已被真实浏览器 e2e 自动化覆盖（`tests/e2e/spa_layout.spec.ts`，
> 8 条，1280×800 与 1920×1080 双视口，2026-09-21），本表是人工复核口径。
> 宽屏口径：内容列限宽 **1400px** 居中（`AppLayout` 的
> `data-testid="page-container"`，`data-layout="capped"`）；**看板是唯一
> 全宽豁免页**（`data-layout="wide"`，列天然横向平铺）；任何视口下文档
> 不得横向溢出。首页星系 embed 走 `?compact=1`（dashboard 组件的紧凑
> 模式：检查器改为点选节点才弹出的抽屉，无固定右栏），iframe 高度
> `clamp(640px, calc(100vh - 180px), 900px)`。

| # | 步骤 | 预期 | 结果 | e2e 覆盖 |
|---|------|------|------|------|
| 5A.1 | 1920×1080 逐页过（首页/证据/证据评审/周回顾/项目看板/输出工作室/研究台/差距/目标/健康/活动/公开构建/技能树/收件箱/助手/档案列表） | 内容列 ≤1400px 居中，表格行不再拉成超长行，卡片/表单右侧无大片空白；无横向溢出 | ☐ | ✅ 自动化（代表页断言 + 全页审计脚本 `tests/e2e/audit_layout.mjs`） |
| 5A.2 | 看板在 1920×1080 | 全宽豁免生效：列用满视口宽，文档仍无横向溢出 | ☐ | ✅ 自动化（`data-layout="wide"` + 容器宽 >1400 断言） |
| 5A.3 | 首页星系 hero（1280×800 / 1440×900 / 1920×1080 / 2560×1440） | iframe 与卡片内容同宽；高度落在 clamp 区间（约 640–900px），星系完整可见、iframe 内无高内部滚动；embed 内无固定右栏（点节点才弹检查器抽屉），3D 舞台占 iframe 宽 ≥55% | ☐ | ✅ 自动化（1280/1920 双视口断言 src 含 `compact=1`、宽高、内部滚动 ≤80px） |
| 5A.4 | 2560×1440 超宽屏抽查首页/证据评审/看板 | 限宽与豁免规则同 5A.1/5A.2，布局不失衡 | ☐ | 人工（审计脚本可跑任意视口） |

**人工复核项**：星系在 21:9 带鱼屏上的观感（是否需要更宽的豁免档）；
看板豁免是否还应扩到项目时间轴等未来画布页；1400px 上限在大字体
（125%/150% 缩放）下的实际可读宽度。

---

## 6. 打包与安装态（可选，约 10 分钟）

```bash
cd /home/ubuntu/nblane
.venv/bin/pip wheel --no-deps -w /tmp/nblane-wheel .
unzip -l /tmp/nblane-wheel/nblane-*.whl | grep web_ui/static   # 应看到 index.html + assets
```

| # | 检查 | 预期 | 结果 |
|---|------|------|------|
| 6.1 | wheel 内容 | 含 `nblane/web_ui/static/index.html` 和哈希 assets | ☐ |
| 6.2 | 前端产物新鲜度 | `cd src/nblane/web_ui/frontend && npm run build` 后 `git status` 对 static/ 无 diff | ☐ |

---

## 7. 已知不足（体验前请知悉，这些不算新发现）

| 项 | 状态 |
|---|---|
| Evidence/Goals 页的编辑按钮 | 只读，页面有「开发中」提示 |
| BlockNote 富文本编辑器 | 未接入（Markdown 源码编辑代替） |
| Home 的 trends/每日简报、目标编辑器 | 未做 |
| 项目时间轴画布 | 未做 |
| 看板重名卡按 id 寻址 | 后端后续项，当前提示消歧 |
| OpenClaw Dashboard 内嵌 iframe | 上游否决（issue #47565），方案为 Caddy 反代 + 新标签（CW-4，待人工窗口） |
| MCP 生产接通、备份调度、自动化切换、SecretRef | CW-1/2/3/5，待人工变更窗口执行 |
| `--agent main` 硬编码 | 上游 schema 限制 |
| sidecar handoff 一次性 POST 换票 | 已知残余风险（TTL 已降至 60s） |

---

## 8. 问题记录表（体验后把这一节发给我）

| # | 页面/命令 | 现象 | 复现步骤 | 严重度（阻塞/难受/别扭/建议） |
|---|-----------|------|----------|------|
| 1 | 全部写操作（收件箱捕获/看板建卡/证据评审批量接受等） | **已修复（2026-09-20，P0-1）**。现象：浏览器内所有携带 If-Match 的 mutation 全部 422 `request: Input should be a valid dictionary or object...`，curl 直打后端却正常。根因：`frontend/src/api/client.ts` `requestWithHeaders()` 先写 headers 再展开 `...init`，`ifMatch(etag)` 把合并好的 headers 整体覆盖，Content-Type 丢失，fetch 默认 text/plain，FastAPI 不按 JSON 解析。修复：调整展开顺序一行改动（覆盖全部 28 处 ifMatch 调用点）；回归 `client.test.ts` 新用例 + `tests/e2e/spa_mutations.spec.ts` 断言每条 mutation 出站为 application/json。 | 浏览器开收件箱填一条点「记录」即报红 | 阻塞 |
| 2 | 活动页（Activity） | **已修复（2026-09-20，P0-2）**。现象：pending 项点「应用」报「Only Review-origin items can be applied from Activity」。根因：SPA 对所有 pending 项都显示「应用」，但后端只允许 Review 来源候选（沙箱里大量 AI Gateway 来源项本不可 apply）；Streamlit 版本就禁用该按钮并附说明。修复：`ActivityPage.tsx` 新增 `canApplyActivityItem`（与 `pages/9_Agent_Activity.py` `_can_apply_here` 同口径），不可 apply 的项隐藏「应用」并显示来源说明；后端判定未动。回归：ActivityPage 单测 + e2e 双向用例（非 Review 项无按钮 / 看板 Done 卡→周回顾保存→活动 apply 全链路）。 | 活动页选 AI Gateway 来源 pending 项点「应用」 | 阻塞 |
| 3 | 首页 Home | **已修复（2026-09-20，P1-1+P1-3）**。现象：顶部快捷入口条（看板/技能树/目标/证据评审/周回顾/研究台/输出工作室）与左侧导航完全重复；8+ 卡片平铺信息密度过高，3D 星系只是底部一张需手点「嵌入显示」的折叠卡。修复：iOS 式减法——删快捷入口条与七张平铺卡，改为焦点卡（北极星+主目标）→ 成长星系全宽 hero（指标 chip 悬浮、可点击入潜）→ 今日待办聚合带（待审批/待评审/Doing 前 3）。数据层零改动（复用 home 端点现有字段）。回归：`spa_home.spec.ts` + `HomePage.test.tsx`。 | 打开 `/p/dev/home` 即见 | 难受 |
| 4 | 首页/研究台 3D 星系 iframe | **已修复（2026-09-20，P1-2）**。现象：iframe 内「127.0.0.1 refused to connect」。根因：`scripts/dev-web.sh` 给 streamlit 会话注入了 `NBLANE_READER_API_BASE` 却漏了 web-api 会话，隔离实例里 home/research 端点的 `sidecar.base` 落到默认值 8502（沙箱无服务）。修复：web-api tmux 会话补注 `NBLANE_READER_API_BASE='$reader_base'`；另加前端探活（no-cors fetch `/auth/session-ok`），sidecar 不可达时降级为静态指标带而非浏览器错误灰框。生产 8502 未动。回归：`spa_home.spec.ts`（base=18502 断言 + iframe 真实 200 + 拦截模拟不可达）。 | 隔离实例打开 `/p/dev/home` 看星系 iframe | 阻塞 |
| 5 | 全站 17 页（1920+ 宽屏） | **已修复（2026-09-21，宽屏布局批次）**。现象：所有页面主体在 1920×1080 下无限拉宽（内容列 1668px）——表格行过长、卡片右半大片空白、差距分析表单拉满；首页星系 iframe 写死 560px 高，embed 实际内容 816–1026px，星系被腰斩，且 embed 内固定右栏（Graph nodes 列表 280px + 检查器 ~35% 宽）随 iframe 越宽越失衡，3D 舞台只占 hero 宽 ~42%。修复：① `AppLayout` 主体列统一限宽 1400px 居中（`page-container`，看板 `data-layout="wide"` 豁免）；② dashboard 组件新增 `?compact=1`（仅 embed 生效：检查器改点选抽屉、隐藏与 SPA 重复的 Attention 条、3D 画布高度下限 560→480），后端 `dashboard_url` 统一带 `compact=1`；③ 星系 iframe 高改 `clamp(640px, calc(100vh - 180px), 900px)`（`SidecarFrame` 支持 CSS 高度）。向后兼容：无参 embed / Streamlit / standalone 行为不变。回归：`tests/e2e/spa_layout.spec.ts`（8 条双视口）+ `spa_mobile.spec.ts` 375px 不回归 + `audit_layout.mjs` 17 页×3 视口审计。 | 1920 宽屏打开任一页；首页看星系被截断 | 难受 |
| 6 |  |  |  |  |
| … |  |  |  |  |

**体验结束后**：把问题表 + 「7. 已知不足」中你认为必须提前做的项一起发我，
我会合并修复计划统一修（目标 95 → 100），修完全量回归（pytest/vitest/e2e）。
