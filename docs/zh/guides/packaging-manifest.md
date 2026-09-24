---
status: active
owner: 王军 + kimi
last_verified: 2026-09-24
source_of_truth: nblane 打包/迁移时的一切外部依赖与系统配置的登记处
---

# 打包与迁移清单(Dependency & Deploy Manifest)

nblane 本体是 `pip install -e .`(Python 依赖见 pyproject.toml/uv.lock);本清单登记**本体之外**的一切——换机器/打包分发时按此复现。

## 1. 系统级依赖(本体之外,需另行安装)

| 依赖 | 用途 | 安装方式 | 记录位置 |
|---|---|---|---|
| Node.js ≥ 18 | 组件前端构建、e2e | 系统包/nvm | package.json |
| tmux | 远程车间会话 | apt | deploy/units/ |
| ttyd(静态二进制) | 远程车间网页终端 | GitHub releases → ~/.local/bin | docs/zh/dev/phase0.5-remote-terminal.md |
| GROBID(可选) | PDF 结构提取 | docker,端口 8070 | deployment-tencent-cloud.md |
| mihomo(可选,本机网络工具) | 代理 | 见 mihomo-deployment.md | 非 nblane 配置 |
| openclaw(可选) | 常驻 agent 运行时 | npm 全局 | scripts/openclaw/install.sh |
| 思源宋体/文楷/一点明体/IM Fell | 星图标签字体 | GitHub releases,子集化后入库 | home_dashboard_component/frontend/playground/tools/ |
| three / troika-three-text / gsap / postprocessing / culori(SPA 前端 npm 依赖) | 星图三维渲染/SDF 文字/动画/后处理/OKLCH 色彩 | npm(web_ui/frontend package.json,2026-09-23 Phase 3 引入) | src/nblane/web_ui/frontend/package.json |
| 星官数据资产 asterisms.json(已入库,无需重装) | 首页星图技能域映射/北斗目标几何的星官形状(坐标+连线+小传) | 星官拓扑取自 Stellarium skycultures/chinese(CC BY-SA 4.0),星位/星等取自 Hipparcos 主星表(CDS I/239,J2000);已按星官质心归一化 | src/nblane/web_ui/frontend/src/starmap/data/(含 README.md 与 asterisms.test.ts) |

## 2. 系统配置(仓库外文件,模板应收进 deploy/)

- [ ] Caddyfile 模板(/etc/caddy/Caddyfile 的生产形态,含 basic_auth 段)
- [ ] systemd units:nblane.service(8501)、nblane-reader.service(8502)、nblane-web-api(8504,未上生产)、nblane-workshop.service(ttyd,用户级)
- [ ] .env(.env.example 已是模板)
- [ ] 数据拓扑(2026-09-23 查明):真实 profile 数据在 `/srv/nblane-data/profiles/`;仓库 `profiles/王军` 是指向它的符号链接(2026-09-17 起);`/srv/nblane-app/nblane/profiles/王军` 是 4 月旧副本(疑似生产 8501 在用,待王军确认是否需同步)。注意:沙箱 `.dev-data` 复制数据必须用 `cp -aL` 解引用——符号链接会被 `safe_profile_dir`  containment 拦截(表现为 profile_not_found)

## 3. 数据迁移单元

- `profiles/<name>/`(全部用户数据,YAML/MD,git 即可迁移)
- `teams/`、`schemas/.learned/`(本地学习产物)
- `auth/users.yaml`(认证开启时)

## 4. 打包纪律

- 新增任何系统级依赖/端口/服务,必须同步登记本文件 + 对应 phase 文档。
- 安装动作优先写成幂等脚本(参照 scripts/openclaw/install.sh)。
- 个人数据(profiles/ 非 template、.env、密钥)永不进包。

## 5. 依赖登记日志

- 2026-09-23 Phase 2 后端(projects-board 聚合 API、任务排期字段、check-in 写入):**无新增依赖**——纯 Python 逻辑落在 `core/projects_board.py` 与既有 kanban_io/activity_log,Web API 复用现有 FastAPI 栈;无新端口、无新服务。
- 2026-09-23 Phase 2 后端续片(habit_id 显式链接、kanban PATCH、习惯计划模板):**无新增依赖**——内置模板是纯 YAML 包数据(`core/data/habit_plan_templates.yaml`,已登记进 pyproject package-data),无新端口/服务;profile 侧新增小文件 `plan-templates.yaml`(随 profiles/ 一并 git 迁移)。
- 2026-09-23 首页星图编辑后端(north-star 外科写入、goals CRUD、chronicle.yaml):**无新增依赖**——纯 Python(`core/north_star.py` / `core/chronicle.py` / `core/goals.py` 加锁与快照)复用既有 file_lock/file_state/file_write 与 FastAPI 栈;无新端口/服务;profile 侧新增 append-only 小文件 `chronicle.yaml`(随 profiles/ 一并 git 迁移)。
- 2026-09-23 项目页 HCI 后端补件(项目删除端点、habits[] 90 天热力图 recent_days):**无新增依赖**——删除走既有 kanban_io/project_board/chronicle 锁与快照纪律,热力图只是 `core/projects_board.py` 聚合口径扩展;无新端口/服务/包。
- 2026-09-23 星官数据资产(22 星官:紫微垣核心+太微/天市垣墙+角亢心斗奎毕参柳):**无新增运行时依赖**——纯静态 JSON 入库(`src/nblane/web_ui/frontend/src/starmap/data/asterisms.json`),一次性抓取 Stellarium chinese 星空文化 + Hipparcos I/239 生成,生成脚本不入库(再生步骤见同目录 README.md);无新端口/服务/包。
- 2026-09-24 占卜后端(§5,`POST /profiles/{name}/divination`):**无新增依赖**——纯 Python(`core/divination.py` 卦表/锚点/确定性起卦)复用既有 starmap_snapshot/projects_board/gap 读路径与 AI gateway(`divination.cast`,60s 超时,失败回落规则解卦);卦表为代码内精选 34 卦文本(易经原文,公有领域),无新数据资产、无新端口/服务/包;结果一次性消费,profile 侧无新文件。
- 2026-09-24 项目页缺口闭合(checkin 销印端点 + recent_days checkin_ids + 任务编辑前端):**无新增依赖**——删除走既有 activity_log 锁与快照纪律,前端复用 Mantine/react-query 存量;无新端口/服务/包。
- 2026-09-24 项目页收尾片(日课项目删除入口、快添自动打开详情卡、任务 TODO 清单 todos meta 子弹 + PATCH 全量替换):**无新增依赖**——纯 Python(`core/models.py` KanbanTodo、`core/kanban_io.py` todo: 子弹 parse/render、`core/projects_board.py` 聚合携带)复用既有 kanban PATCH 端点与锁/快照纪律,前端复用 Mantine/react-query 存量;无新端口/服务/包。
- 2026-09-24 技能树页三项升级(类目星官化横幅 + 节点铭文卡 + `PATCH /skill-tree/nodes/{id}` 状态写端点 + `GET /evidence?skill_id=`):**无新增依赖**——纯 Python(routes_v1/schemas 复用 `update_skill_tree` 锁内快照、`evidence_usage_index` 反查、`write_generated_blocks` 同步),前端复用 starmap `InscriptionCard`/asterisms.json/Mantine/react-query 存量;无新数据资产、无新端口/服务/包。
