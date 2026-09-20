---
status: active
owner: nblane-team
last_verified: 2026-09-20
source_of_truth: src/nblane/web_api/、src/nblane/web_ui/frontend/、scripts/dev-web.sh、docs/zh/architecture/integration-audit-2026-09-20.md
---

# nblane 体验官手册：融合 + SPA 全功能走查（2026-09-20）

> 目的：逐一体验本轮全部交付（React SPA 16 页、web_api 后端、OpenClaw 融合
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

```bash
cd /home/ubuntu/nblane
scripts/dev-web.sh --isolated   # 启动三服务（若已在跑会提示；当前已经有一组在跑）
scripts/dev-web.sh status       # 确认 nblane-dev-reader-api / nblane-dev-streamlit-ui / nblane-dev-web-api 都在
```

| # | 检查 | 预期 | 结果 |
|---|------|------|------|
| 0.1 | 浏览器开 `http://127.0.0.1:18504/`（本地或 SSH 转发 18504） | 看到 SPA 登录页或档案列表（未开认证则直接进） | ☐ |
| 0.2 | `curl -s http://127.0.0.1:18504/api/v1/health` | 返回 JSON `{"ok":true,...}` | ☐ |
| 0.3 | `curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:18504/p/dev/kanban` | 输出 `200`（客户端路由回退 index.html；注意用 GET 不要用 `-I`，HEAD 目前返回 405，已记入修复批次） | ☐ |
| 0.4 | 手机体验（可选）：SSH 转发 `ssh -L 18504:127.0.0.1:18504 服务器`，手机浏览器开电脑 IP:18504 | 页面可用、导航可点 | ☐ |

> 想体验真实 `王军` 数据：告诉我一声，我用备用端口起一组默认实例
> （`scripts/dev-web.sh --reader-port 8512 --streamlit-port 8513 --web-api-port 8514`，
> 绕开生产 8502）。**不要**直接 kill 8502 上的 uvicorn，那是生产服务。

---

## 1. 认证与导航（约 10 分钟）

| # | 步骤 | 预期 | 结果 |
|---|------|------|------|
| 1.1 | 未登录直接访问 `http://127.0.0.1:18504/p/dev/kanban`（若启用了 NBLANE_AUTH_FILE） | 跳登录页；登录后**回到 kanban 页**而不是首页（修复 M-FE-3） | ☐ |
| 1.2 | 登录页输错密码 3 次 | 提示通用错误（不泄露用户是否存在）；连续错 5 次后该账号限流 60 秒 | ☐ |
| 1.3 | 登录后左侧导航 16 项逐一点一遍 | 每页都能打开；当前页高亮正确（重点看「证据」vs「证据评审」不会同时亮） | ☐ |
| 1.4 | 登出 | 回登录页；再访问内页被拦 | ☐ |
| 1.5 | 会话过期模拟：登录后删除 cookie 再刷新内页 | 自动跳回登录页，而不是困在错误页（修复 M-FE-2） | ☐ |

---

## 2. SPA 页面逐页走查（核心，约 60–90 分钟）

每页看四件事：加载态、空态（无数据时）、错误态（可拔 API 模拟）、移动端窄屏。

### 2.1 首页 Home（`/p/<name>/home`）
| # | 步骤 | 预期 | 结果 |
|---|------|------|------|
| 1 | 打开 | 北极星/主目标卡片、技能 RingProgress、看板 doing 前 5、健康分、快捷入口 | ☐ |
| 2 | 3D 星系仪表盘区域 | iframe 内嵌 sidecar dashboard；加载中有 Loader，失败有「重新加载」按钮 | ☐ |

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

### 2.4 代理活动 Agent Activity（`/p/<name>/activity`）
| # | 步骤 | 预期 | 结果 |
|---|------|------|------|
| 1 | 有 pending 项时 apply / dismiss | 状态流转；apply 后对应数据真被写入（如 kanban_move 真挪卡） | ☐ |
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
| # | 步骤 | 预期 | 结果 |
|---|------|------|------|
| 1 | 输入一段任务描述 → 分析 | 出覆盖率条、已具备/差距两栏、建议行动 | ☐ |
| 2 | 差距节点点「加入看板」 | 成功提示；看板 Queue 出现学习卡 | ☐ |
| 3 | 空描述提交 | 客户端拦截不发请求 | ☐ |
| 4 | 找「LLM 深度分析」提示 | 蓝色提示卡片说明需异步任务基建（已知降级，非故障） | ☐ |

### 2.7 周回顾 Review（`/p/<name>/review`）
| # | 步骤 | 预期 | 结果 |
|---|------|------|------|
| 1 | 默认本周窗口打开 | 四类候选（证据/下一步/公开草稿/方法笔记）+ 汇总徽章 | ☐ |
| 2 | 自定义窗口（起 > 止） | 自动交换或 422 提示 | ☐ |
| 3 | 勾选候选 → 保存到活动 → 应用写回 | 逐候选结果显示；失败单项不拖垮整单 | ☐ |
| 4 | 窄屏 | 候选表格可横向滚动 | ☐ |

### 2.8 项目看板 Project Board（`/p/<name>/project-board`）
| # | 步骤 | 预期 | 结果 |
|---|------|------|------|
| 1 | 建项目案例 → 加里程碑 → 建任务 | 全链路可用；任务出现在 kanban | ☐ |
| 2 | **草稿保护**：在「基本信息」Tab 改标题不保存，切到「任务」Tab 挪一个任务，再切回 | 未保存的标题还在（修复 M-FE-1） | ☐ |
| 3 | AI 建议引用 | 无 LLM 时显示「AI 建议不可用」降级卡片（非报错） | ☐ |
| 4 | 归档案例 | 状态流转 | ☐ |

### 2.9 输出工作室 Studio（`/p/<name>/studio`）
| # | 步骤 | 预期 | 结果 |
|---|------|------|------|
| 1 | 博客 Tab：新建文章 → 编辑 Markdown → 保存 | 保存成功；ETag 并发保护（可两标签测 412） | ☐ |
| 2 | 发布检查 → 发布 | 缺 summary 被门控拦（422 提示）；补全后可发布 | ☐ |
| 3 | 「从证据生成」Tab 选证据 → 预览 → 建草稿 | 草稿出现在博客列表 | ☐ |
| 4 | JD 匹配 Tab | 无 LLM 时黄色降级卡片（非报错） | ☐ |

### 2.10 研究台 Research（`/p/<name>/research`）
| # | 步骤 | 预期 | 结果 |
|---|------|------|------|
| 1 | 打开 | 来源统计卡片 + 最近 8 条来源 + Paper Library 入口 | ☐ |
| 2 | 点 Paper Library（iframe 或新标签） | sidecar 页面打开（需 8502 在跑）；首次自动带认证 | ☐ |

### 2.11 其余页面快速过
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

| # | 步骤 | 预期 | 结果 |
|---|------|------|------|
| 5.1 | 手机或 DevTools 375px 宽：导航 | 汉堡菜单可开合，16 项可点 | ☐ |
| 5.2 | 证据评审/周回顾/项目看板/研究台/证据 五页宽表格 | 可横向滚动，不破版 | ☐ |
| 5.3 | 看板拖拽/挪卡 | 触屏可用（下拉选择挪列） | ☐ |
| 5.4 | 收件箱快速捕获 | 手机上能单手完成 | ☐ |

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
| LLM 功能（Gap 深度分析、JD 匹配、AI 建议）统一 422 + 页面降级卡片 | 刻意，待异步任务/SSE 基建 |
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
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| … |  |  |  |  |

**体验结束后**：把问题表 + 「7. 已知不足」中你认为必须提前做的项一起发我，
我会合并修复计划统一修（目标 95 → 100），修完全量回归（pytest/vitest/e2e）。
