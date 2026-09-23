---
status: active
owner: 王军 + kimi
last_verified: 2026-09-23
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

## 2. 系统配置(仓库外文件,模板应收进 deploy/)

- [ ] Caddyfile 模板(/etc/caddy/Caddyfile 的生产形态,含 basic_auth 段)
- [ ] systemd units:nblane.service(8501)、nblane-reader.service(8502)、nblane-web-api(8504,未上生产)、nblane-workshop.service(ttyd,用户级)
- [ ] .env(.env.example 已是模板)

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
