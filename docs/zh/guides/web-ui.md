---
status: active
owner: docs
last_verified: 2026-05-24
source_of_truth: true
---

# Web 使用手册（Streamlit）

本文说明如何**运行与操作**本地 Streamlit 界面。信息架构、首屏原则与 backlog 见
[Web 体验设计](../product/web-experience.md)；页面清单与文件映射见
[当前状态](../project/status.md)。

| 项目 | 说明 |
|------|------|
| 入口 | 在仓库根目录启动 Streamlit；Research PDF Reader 和 Paper Library standalone 默认还需要 FastAPI sidecar |
| 范围 | `app.py` + `pages/*.py`；这是文件驱动的私有工作台。Public Site 页面会构建静态公开产物，但 Streamlit 应用本身**不是**托管公开站点 |

---

## 1. 前置条件

1. 安装：`pip install -e .`（见 [安装与 LLM 配置](setup.md)）。
2. 至少一个 `profiles/` 下的档案（`nblane init <名称>`）。
3. 可选 **LLM**：在 `.env` 配置 `LLM_API_KEY` 等，以使用差距页 AI 教练、首页简历摄入、看板「已完成→证据」。看板页也可选择本地 **Codex** 作为只读 AI backend，替代看板内的 LLM 动作。未配置时仍可使用规则差距分析与全部非 AI 编辑。

如果要运行 `tests/e2e` 的浏览器回归，需额外在仓库根目录执行：

```bash
npm install
npm run test:e2e:install
```

国内网络环境可使用镜像：

```bash
npm_config_registry=https://registry.npmmirror.com npm install
npm run test:e2e:install:cn
```

### 1.1 开发启动 Research PDF Reader 和 Paper Library

Research 的 PDF Reader 和 Paper Library standalone 是 **Streamlit 主应用 + FastAPI sidecar** 两个进程。
开发环境不要使用生产的 systemd service；用 tmux 跑独立进程即可。生产通常占用
`8501/8502/8070`，所以开发分两种模式：

- **普通本机开发**：没有生产服务同机运行时，可继续使用 `8502/8503`。
- **与生产同机并行调试**：使用 `18502/18503` 和 `.dev-data/.dev-assets`，避免写入
  `/srv/nblane-data`、`/srv/nblane-assets` 或抢占生产 `8502`。

推荐用脚本启动：

```bash
# 普通本机开发：Reader API 8502 + Streamlit 8503。
scripts/dev-web.sh

# 调试短任务时可启用 uvicorn reload；跑 Codex 搜索、translation/extraction 等长任务前关掉 reload。
scripts/dev-web.sh --reload

# 与生产服务同机并行开发：Reader API 18502 + Streamlit 18503，数据写入 .dev-data/.dev-assets。
scripts/dev-web.sh --isolated

# 同机并行开发 + reload。
scripts/dev-web.sh --isolated --reload
```

脚本会创建/重启 tmux session：

```text
普通本机开发：nblane-reader-api / nblane-streamlit-ui
同机隔离开发：nblane-dev-reader-api / nblane-dev-streamlit-ui
```

查看状态和停止：

```bash
scripts/dev-web.sh status
scripts/dev-web.sh stop

scripts/dev-web.sh --isolated status
scripts/dev-web.sh --isolated stop
```

同机隔离开发第一次启动时，脚本会从 `profiles/template` 创建 `.dev-data/profiles/dev`，并复制
`schemas/`、`teams/` 作为开发数据底座。之后所有 Web 保存、论文产物和 PDF asset 都写入：

```text
.dev-data/
.dev-assets/research/
```

这两个目录已被 `.gitignore` 忽略。不要把生产的 `/srv/nblane-data` 直接作为开发
`NBLANE_ROOT` 使用；需要复现生产问题时，先做快照，再同步到独立开发目录。

如果需要在开发环境调试 GROBID，不要复用生产 `8070`。启动一个本机开发容器，把 host
`18070` 映射到容器内 `8070`：

```bash
sudo docker rm -f nblane-dev-grobid 2>/dev/null || true
sudo docker run -d --name nblane-dev-grobid --restart unless-stopped \
  -p 127.0.0.1:18070:8070 \
  grobid/grobid:0.9.0-crf

curl http://127.0.0.1:18070/api/isalive
scripts/dev-web.sh --isolated --grobid
```

不加 `--grobid` 时，开发脚本默认使用 PyMuPDF fallback，避免误连生产 GROBID。

如果需要手动启动而不是用脚本，本地开发没有 Caddy 反向代理时，需要先启动 sidecar，并让
Streamlit iframe 指向浏览器能访问的 sidecar 地址：

```bash
# 在仓库根目录启动两个 tmux session。
# 如果是重启，先清掉旧 session；不存在时会安全忽略。
tmux kill-session -t nblane-reader-api 2>/dev/null || true
tmux kill-session -t nblane-streamlit-ui 2>/dev/null || true

# Research sidecar: http://127.0.0.1:8502
tmux new-session -d -s nblane-reader-api -c "$PWD" \
  'PYTHONPATH=src .venv/bin/uvicorn nblane.web_reader_api:app \
    --host 127.0.0.1 --port 8502'

# Streamlit UI: http://127.0.0.1:8503
tmux new-session -d -s nblane-streamlit-ui -c "$PWD" \
  'NBLANE_READER_API_BASE=http://127.0.0.1:8502 \
   PYTHONPATH=src .venv/bin/streamlit run app.py \
    --server.address=127.0.0.1 --server.port=8503 --server.headless=true'
```

如果要手动启动同机隔离开发，把端口和数据目录一起换掉：

```bash
mkdir -p .dev-data/profiles .dev-data/schemas .dev-data/teams .dev-assets/research
cp -a profiles/template .dev-data/profiles/template 2>/dev/null || true
cp -a schemas/. .dev-data/schemas/
cp -a teams/. .dev-data/teams/
NBLANE_ROOT="$PWD/.dev-data" PYTHONPATH=src .venv/bin/nblane init dev 2>/dev/null || true

tmux kill-session -t nblane-dev-reader-api 2>/dev/null || true
tmux kill-session -t nblane-dev-streamlit-ui 2>/dev/null || true

# Dev Research sidecar: http://127.0.0.1:18502
tmux new-session -d -s nblane-dev-reader-api -c "$PWD" \
  'NBLANE_ROOT=.dev-data \
   NBLANE_RESEARCH_ASSET_ROOT=.dev-assets/research \
   NBLANE_RESEARCH_STRUCTURE_BACKEND=pymupdf \
   PYTHONPATH=src .venv/bin/uvicorn nblane.web_reader_api:app \
    --host 127.0.0.1 --port 18502'

# Dev Streamlit UI: http://127.0.0.1:18503
tmux new-session -d -s nblane-dev-streamlit-ui -c "$PWD" \
  'NBLANE_ROOT=.dev-data \
   NBLANE_READER_API_BASE=http://127.0.0.1:18502 \
   NBLANE_DASHBOARD_CANVAS_BASE=http://127.0.0.1:18502 \
   NBLANE_STREAMLIT_BASE_URL=http://127.0.0.1:18503 \
   NBLANE_RESEARCH_ASSET_ROOT=.dev-assets/research \
   NBLANE_RESEARCH_STRUCTURE_BACKEND=pymupdf \
   PYTHONPATH=src .venv/bin/streamlit run app.py \
    --server.address=127.0.0.1 --server.port=18503 --server.headless=true'
```

Paper Library 的 Codex 搜索和 Reader 长任务会在 sidecar 进程内保存 job 状态。默认启动不要加
`--reload`；否则代码或产物变动触发 uvicorn reload 后，前端继续查询旧 job 可能得到
`search job not found`。如果只是短时间调试代码，可临时加
`--reload --reload-dir src`；跑长搜索、translation/extraction 前建议重启回无 reload 模式。

查看日志/进入进程：

```bash
tmux attach -t nblane-reader-api
tmux attach -t nblane-streamlit-ui

tmux attach -t nblane-dev-reader-api
tmux attach -t nblane-dev-streamlit-ui
```

在 tmux 中按 `Ctrl-b` 然后按 `d` 可 detach，服务会继续运行。停止服务：

```bash
tmux kill-session -t nblane-reader-api
tmux kill-session -t nblane-streamlit-ui

tmux kill-session -t nblane-dev-reader-api
tmux kill-session -t nblane-dev-streamlit-ui
```

如果通过 SSH / IDE port forwarding 在浏览器访问，请同时转发 Streamlit 和 sidecar 两个端口：
普通本机开发转发 `8503` 和 `8502`；同机隔离开发转发 `18503` 和 `18502`。同时把
`NBLANE_READER_API_BASE` 设成浏览器能打开的 sidecar URL。

启动后常用入口：

- Streamlit Research：`http://127.0.0.1:8503`
- Paper Library standalone：`http://127.0.0.1:8502/paper-library?profile=<profile>`
- PDF Reader：从 Paper Library 的 `Open Reader` 打开，或访问 `/reader/view/{source_id}`。
- 同机隔离开发 Streamlit：`http://127.0.0.1:18503`
- 同机隔离开发 Paper Library：`http://127.0.0.1:18502/paper-library?profile=dev`

端口级自测可以先确认两个进程都活着：

```bash
curl -i http://127.0.0.1:8503/_stcore/health
curl -i 'http://127.0.0.1:8502/paper-library?profile=<profile>'

curl -i http://127.0.0.1:18503/_stcore/health
curl -i 'http://127.0.0.1:18502/paper-library?profile=dev'
```

`Find and import papers` 的 Codex 搜索运行在 sidecar search job 上；普通本机开发是 `8502`，
同机隔离开发是 `18502`。前端不再固定提交
`120s / 180s` 搜索时长；默认只提交 `Fast / Deep` 搜索深度，后端按 depth、limit 和环境变量计算
adaptive budget。`Fast + limit=10` 默认会给 Codex 约 `180s`，避免正常 web search 因插件同步或
网络抖动被 `75s` 误杀；如需更长或更短，可在 `Advanced` 手动填 `Codex max s`。页面优先通过
SSE 订阅 `/search/jobs/<job_id>/stream`，不可用时自动回落到 status polling。搜索过程会在页面中显示
job events，例如 Codex 启动、web search、organizing、timeout / idle timeout、provider fallback
和最终候选数量。搜索中可点击 `Cancel`，后端会标记
job 为 cancelling/cancelled，并终止正在运行的 Codex 子进程。
Codex CLI 的 live web-search 进度有时会从 stderr 输出；这不等于错误。Paper Library 会把这些原始输出归类成
`web search`、`organizing`、`codex setup` 等用户可读事件；只有最终 trace 里的
`local_codex_readonly · failed` 或 `command_timeout` 才表示 Codex 路径失败。
Paper Library 的 Codex 论文搜索默认使用终端/插件同款 `CODEX_HOME`（通常是 `~/.codex`），
以复用相同的登录、模型、web search、项目 trust 和插件缓存；这也是建议的日常模式。只有需要复现
Web profile 隔离环境时，才在请求体或环境变量中设置 `codex_home_policy=profile` /
`NBLANE_PAPER_SEARCH_CODEX_HOME_POLICY=profile`；若要让所有 Codex 动作都进入旧隔离模式，可设置
`NBLANE_CODEX_HOME_POLICY=profile`。

`Find and import papers` 顶部也提供手动入口：`URL` 可粘贴论文页、DOI URL、arXiv URL 或直接 PDF URL，
并按所选 collection/status/visibility 导入；如果打开 `Download PDF`，后端会在 URL 可推导到
open-access PDF 时尝试下载。`Upload` 可直接选择本地 `.pdf`，创建新的 paper source、保存外部 PDF asset，
并在导入后打开对应论文详情。已有论文详情页里的 `Upload PDF` 仍用于给当前 paper 补传/替换 PDF。

如需用 API 直接验证 search job 与取消链路，可从同源端口发起请求：
同机隔离开发时，把下面 URL 和 `Origin` 里的 `8502` 换成 `18502`。

```bash
curl -X POST "http://127.0.0.1:8502/api/research/<profile>/paper-library/search/jobs" \
  -H "Origin: http://127.0.0.1:8502" \
  -H "Content-Type: application/json" \
  -d '{"mode":"codex","query":"OpenVLA robot manipulation","limit":1,"codex_search_depth":"quick"}'

curl -X POST "http://127.0.0.1:8502/api/research/<profile>/paper-library/search/jobs/<job_id>/cancel" \
  -H "Origin: http://127.0.0.1:8502" \
  -H "Content-Type: application/json" \
  -d '{}'
```

高级调参可在页面的 `Advanced` 区域填写，也仍可走请求体或环境变量：
`codex_timeout_seconds` 可手动指定硬上限；`codex_idle_timeout_seconds` 控制长时间无输出时提前
fallback；`provider_budget_seconds` 和 `provider_timeout_seconds` 控制 provider fallback 的预算。

如果远程 PDF 下载很慢或失败，但你能在本地浏览器更快下载 PDF，可以在 Paper Library 详情页点击
`Upload PDF`，直接选择本地 `.pdf` 文件上传到 sidecar。上传会复用同一套外部 PDF asset 存储，
成功后立即写入 `pdf_asset_ref`、标记 `pdf_download_status=downloaded`，并启用 `Open Reader`。
这适合 arXiv 等站点在服务器侧下载很慢、但浏览器侧访问正常的情况；后续 `Retry PDF` 仍可继续用于
让服务器按远程 `open_access_pdf_url` 重试下载。

Paper Library 的 `Retry translation` 也是后台 job。页面轮询 job 状态时，偶发的 status 请求超时不代表
LLM 翻译已经失败；前端会继续等待后台 job。论文翻译 batch 的 LLM 调用默认使用更长的
`NBLANE_PAPER_TRANSLATION_MODEL_TIMEOUT_SECONDS=180` 秒预算，避免大段结构化翻译被普通短请求超时误杀。
Direct LLM 的 `research.paper_translate` 默认启用流式请求（`NBLANE_STREAM_PAPER_TRANSLATION=1`），
用于规避 SOCKS 代理或供应商网关在长非流式 JSON 响应上一直不返回的问题；如需回退旧行为，可设为 `0`。
大论文的全文翻译可能持续十几分钟以上，生产 sidecar 建议把 `NBLANE_READER_TASK_TIMEOUT_SECONDS`
设为不低于 `3600`，让 Reader 任务状态和已落库进度保持可见。
详情页 `Retry translation` 旁可选择翻译模式：

- `Fast body`：默认值。使用带 PDF 定位的 structure 单元，只翻正文、标题和图表 caption，跳过参考文献。
- `Full paper`：仍使用 structure 单元，但包含 `References / Bibliography`。
- `GROBID paragraphs`：使用 GROBID 段落/section 文本翻译，通常更快，但 Reader 定位会弱于 structure 单元。

结构化翻译默认会把 batch 调小并逐批落盘：`structure/layout` 默认最多每批 12 个单元、`segment`
默认最多 12 个、`page` 默认最多 4 页；同时按字符预算自动切批，避免少数长段落把单次 LLM 请求撑得过大。
结构化翻译默认跳过 `References / Bibliography` 段落，只翻译正文、标题和图表 caption；如确实需要翻参考文献，
可设置 `NBLANE_PAPER_TRANSLATION_INCLUDE_REFERENCES=1`。可用 `NBLANE_PAPER_TRANSLATION_STRUCTURE_BATCH_SIZE`、
`NBLANE_PAPER_TRANSLATION_LAYOUT_BATCH_SIZE`、`NBLANE_PAPER_TRANSLATION_SEGMENT_BATCH_SIZE`、
`NBLANE_PAPER_TRANSLATION_PAGE_BATCH_SIZE` 或通用 `NBLANE_PAPER_TRANSLATION_BATCH_SIZE` 覆盖数量上限；也可用
`NBLANE_PAPER_TRANSLATION_STRUCTURE_BATCH_CHARS`、`NBLANE_PAPER_TRANSLATION_LAYOUT_BATCH_CHARS`、
`NBLANE_PAPER_TRANSLATION_SEGMENT_BATCH_CHARS`、`NBLANE_PAPER_TRANSLATION_PAGE_BATCH_CHARS` 或通用
`NBLANE_PAPER_TRANSLATION_BATCH_CHARS` 覆盖字符预算。
如果 sidecar 在长翻译中短暂断开，页面会显示重连倒计时并保留当前进度；如果 sidecar 重启导致内存 job
丢失，页面会刷新最新已保存产物，并提示再次点击 `Retry translation` 继续剩余单元。

Paper Library 在 Streamlit Research 页中的入口由 `NBLANE_PAPER_LIBRARY_RUNTIME` 控制：

- `fastapi_iframe`：默认值。把 sidecar `/paper-library` 直接嵌入 Research 页，并保留新窗口打开入口。
- `fastapi_link`：只显示 sidecar 工作台入口，旧 Streamlit 组件作为手动 fallback。
- `streamlit_component`：继续把旧 Streamlit component 作为主路径；适合 sidecar 不稳定时调试。

启用 `NBLANE_AUTH_FILE` 的部署中，8502 standalone 页面使用共享登录态：

- Streamlit 登录成功后会 mint 一个短期 handoff token，并通过隐藏 POST 提交到 sidecar
  `/auth/session`；sidecar 校验后设置 HttpOnly `nblane_auth_session` cookie。
- `/paper-library`、`/dashboard`、`/api/research/*` 和 `/api/dashboard/*` 会读取该 cookie，
  并继续按 `auth/users.yaml` 的 profile 权限做校验。没有 cookie 时会返回 `401 auth session required`。
- 生产 Caddy 需要把 `/auth/*`、`/reader/*`、`/paper-library*`、`/dashboard*`、
  `/api/research/*` 和 `/api/dashboard/*` 都反代到 `127.0.0.1:8502`。
- 生产同源部署建议保持 `NBLANE_READER_API_BASE=0`，并使用
  `NBLANE_PAPER_LIBRARY_RUNTIME=fastapi_iframe`；页面会把 `0` 解析成浏览器可访问的 sidecar：
  正式域名访问时使用当前 origin（例如 `https://www.nblane.cloud`），通过 Caddy 命中 8502；
  直连/端口转发 `localhost:8501` 时自动推导 `localhost:8502`。不要把 sidecar 暴露成另一个公网域名。

如果设置了绝对 `NBLANE_READER_API_BASE` 且 sidecar 不可达，Research 页会提示、暂时禁用 Reader / Paper Library 跳转，并显示 Streamlit fallback。

Reader 或 Paper Library 白屏的常见原因是只启动了 Streamlit，或者没有设置 `NBLANE_READER_API_BASE`。这时 iframe
会请求相对路径 `/reader/view/...`；没有 Caddy 时这个路径会被 Streamlit 自己接住，
iframe 里加载的是另一个 Streamlit shell，而不是 Reader API，所以看起来是空白。

另一个本地开发白屏原因是 sidecar 使用 `--reload` 监控了整个仓库。Reader 的 extract pages /
extract segments 会写入 `profiles/` 下的论文产物；如果 uvicorn reload 监听整个仓库，提取时可能触发
sidecar reload 或高 CPU 轮询，导致 sidecar 短暂无响应，iframe 看起来空白。调试短任务时可以使用
`--reload --reload-dir src`，让 sidecar 只监听代码目录；跑 Codex 搜索、translation/extraction
等长任务时建议去掉 `--reload`，避免内存 job 在 reload 后丢失。

旧的单进程组件启动路径已停用。PDF Reader 的主入口始终是
`/reader/view/{source_id}` 对应的 FastAPI sidecar；Paper Library 的主工作台入口是
`/paper-library?profile=<profile>`。

生产部署如果已经用 Caddy 将 `/auth/*`、`/reader/*`、`/paper-library*` 和 `/api/research/*`
反代到 `127.0.0.1:8502`，可设置 `NBLANE_READER_API_BASE=0` 进入同源模式。若通过 SSH/IDE
直连 `localhost:8501` 查看生产 Streamlit，也要同时转发 `8502`；否则页面会把 sidecar
健康检查标为不可用，而不会再把 Streamlit 登录页误嵌进 Paper Library。

普通阅读默认使用译文 flow 视图，不把译文贴回 PDF rect。当前页/可见页翻译会优先使用
`paper-structure` 结构单元，并保留合并后的段落 rect，
用于点击译文块时跳转和高亮 PDF 原文块。只有调试 legacy overlay 时才设置
`NBLANE_READER_DEBUG_OVERLAY=1`。

Reader 左侧 `Pages` 会列出 PDF 的全部页码；缩略图按视口懒加载，滚动到对应页附近时再请求
sidecar 的 page preview。翻译当前页时 Reader 会优先使用 `structure -> layout -> page -> segment`
自动策略；structure 由 PDF layout 几何、标题/caption/front matter 规则和 GROBID section 弱对齐生成，
缓存到 `profiles/<profile>/research/paper-structure/`。在翻译页点击译文块会跳回 PDF 对应页和段落位置，
并高亮对应区域。若某篇旧论文只有语义段落译文、没有 structure/layout rect，可在 Reader 内重新执行
当前页翻译来生成可跳转的结构化译文。

Reader 右侧 `Review` 会显示当前上下文页的图表提取结果。图表提取优先使用 PDF 内嵌图片和
PyMuPDF 表格检测；如果论文使用矢量图导致没有独立图片对象，则会根据 `Figure/Table` caption
裁剪附近区域。点击图表卡片会跳转并高亮 PDF 中的对应区域，便于对照阅读。

页面级 AI 设置遵守一个统一原则：**当前页面的 AI 设置只覆盖当前页面自己的 AI 动作**。侧栏
**LLM 设置** 和 **Codex 状态与配置** 是默认运行时；Dashboard、Research、Kanban 等页面可以在自己的
入口里覆盖本页动作使用的 backend / model，但不会顺手改其他页面的行为。

Research 页右上角有 **Research AI 配置**。这里保存的是当前 profile 的非密钥偏好，只影响 Research 内的
论文搜索、翻译、Reader 和 DeepRead：

- **当前页翻译模型**：用于 Reader 当前页/可见页翻译，以及文本模式 Reader 的翻译动作。
- **DeepRead 模型**：用于 Reader 的 Deep read/Codex deep read，也用于 Analyze Paper 的深读评审模型覆盖。

留空或选择默认时沿用侧边栏/环境变量里的全局模型。配置会写入
`profiles/<profile>/web-preferences.yaml`，不会保存 API key，也不会覆盖 Dashboard 的 goal-skill
匹配、图谱洞察或 Kanban 的任务类 AI 设置。

---

## 2. 语言与显示

- **`.env` 中的 `UI_LANG`**：`en`（默认）或 `zh`。控制 `web_i18n.py`
  提供的 **Streamlit 界面文案**，不受 `LLM_REPLY_LANG` 影响。
- **`.env` 中的 `LLM_REPLY_LANG`**：`en`（默认）或 `zh`。控制模型回复语言，
  以及差距分析、摄入等 AI 路径使用的 **LLM 系统提示语言**。它可以和
  `UI_LANG` 不同，例如中文界面配英文模型输出。
- **`NBLANE_UI_EMOJI`**：设为 `0`、`false`、`no` 或 `off` 时，关闭首页指标、
  技能状态行、看板列标题、团队池 tab 等处的 emoji 前缀（见
  [架构总览](../architecture/overview.md)）。
- **`NBLANE_ROOT`**：若自动解析到的仓库不对，设为包含 `profiles/` 的目录。

---

## 3. 侧栏：当前档案

- **当前档案** — 决定加载哪一份 `profiles/<名称>/` 数据。
- **新建档案** — 展开区效果同 `nblane init`。
- 在页面间切换时，选择会通过会话状态保持。

在 **团队视图** 中，读写始终针对 **`teams/`**。页面说明侧栏档案用于首页、
技能树、差距、看板；**团队数据不按档案过滤**。

### 3.1 侧栏 AI / LLM

- **页面级 AI 设置原则** — 侧栏提供默认运行时和 profile 级 Codex 配置；页面右上角的
  AI 设置只覆盖本页动作。例如 Dashboard 的 **本页 AI 设置** 只影响
  `dashboard.goal_skill_match` / `dashboard.graph_insights`，Research 的
  **Research AI 配置** 只影响论文搜索、翻译、Reader 和 DeepRead。Dashboard 与
  Research 的页面级 AI 面板都提供 backend、LLM model、Codex model 和逐动作
  **Test model**；测试只验证当前行配置，不会写文件。
- **看板 AI 引擎** — 按当前档案选择看板 AI 动作使用普通 LLM 还是本地只读
  Codex。选择会写入当前 profile 的 `web-preferences.yaml`，影响看板的 gap、
  拆子任务、任务理解和 Done -> evidence。
- **LLM 设置** — provider、base URL、模型、界面语言和模型回复语言会按当前
  profile 写入 `web-preferences.yaml`；API key 仍只在当前会话中使用，不写入磁盘。
- **Codex 状态与配置** — 侧栏显示安装 / 登录状态和配置文件路径；点击
  **配置 Codex** 打开大弹窗。Web 默认使用部署级 / 终端同款
  `CODEX_HOME`（本地通常是 `~/.codex`，云上可用 `NBLANE_CODEX_HOME` 指向
  持久化目录），在其中编辑 `config.toml`、通过 `codex login --with-api-key`
  写入共享 `auth.json`，并编辑当前 profile 的 `profiles/<name>/codex.yaml`
  保存 model、cloud env、timeout 等非密钥偏好。profile 隔离 Codex home 只作为
  显式诊断/复现模式，不是默认运行时。

---

## 4. 推荐动线（首次）

1. 侧栏选定档案。
2. 打开 **Project Board** — 先看当前项目、milestone 和目标关联，决定本轮推进对象。
3. 打开 **Kanban** — 管理日常推进；Done 卡片可单卡归档/删除，批量整理转到 Evidence Review。
4. 大任务前打开 **Gap Analysis** — 手动输入，或直接选择 current goal / Kanban task 作为上下文；若已配置 LLM 可开 AI 教练。
5. 资料阅读和研究写作用 **Research Workspace** — 先沉淀 source、chunk、research claim 和 citation，再按需转成 evidence 候选。
6. 打开 **Evidence Review** — 审阅 Done 任务摄入、编辑证据引用，并从已确认 evidence 生成 / 刷新 Claim Studio 中的 claim candidates。
7. 打开 **Skill Map** — 看长期能力状态、备注、内联证据、证据池与引用；点 **保存**
   写入 `skill-tree.yaml`、`evidence-pool.yaml` 并尽量同步 SKILL.md 生成块。
8. 阶段复盘用 **Review**，导出上下文前或阶段体检用 **Profile Health**，跨页面 Agent 候选和失败记录在 **Agent Activity** 管理。
9. 整理公开资料、博客、简历、项目/成果草稿时打开 **Output Studio**，校验和构建静态站时打开 **Public Build**；协作编辑共享池时用 **Team View**。

中文界面的侧栏采用双语标签：中文任务名在前，英文对象名在后，例如
**研究工作台 Research**、**输出工作台 Studio**、**公开构建 Build**。
英文别名用于对照文档、文件名和 CLI，不代表需要在中文界面里用英文理解页面职责。
侧栏按产品心智分组：**工作 Work** 放 Project Board、Kanban、Gap Analysis、Research 和 Evidence Review；**成长 Growth** 放 Skill Map、Review、Profile Health 和 Agent Activity；**输出 Output** 放 Output Studio 和 Public Build。

产品层地图见 [Web 体验设计](../product/web-experience.md)。

---

## 5. 分页面说明

### 5.1 首页（`app.py`）

详细使用说明见 [Dashboard 使用说明](dashboard.md)。

- **标题与说明** — 浏览器标签与子页统一为「功能 · nblane」风格；标题下
- **首屏摘要** — 首页先用原生 Streamlit 渲染 Scope strip、当前目标、本周执行、
  待整理证据与主操作，避免 React 图谱加载时出现“空首页”。
- **上下文画布** — React Dashboard / Context Canvas 下移到稳定摘要之后，用来浏览
  `Source -> Evidence -> Claim -> Skill / Output` 的当前投影。
  caption 标明当前档案与 **私人操作系统** 叙事。
- **标签页**
  - **概览** — 技能指标、分类进度；**简历 / 长文本** 摄入在折叠区内。
    底部为紧凑 **侧栏导航提示**（`st.info`）与 **详细页面说明**（可折叠）。
  - **结构化编辑** — 按 SKILL.md 章节编辑（生成块有自动覆盖提示）。
  - **原文** — 整份 SKILL.md 源码。
- **简历摄入** — 生成草案 → 预览合并 YAML → **写入** 与
  `nblane ingest-resume` 同一路径（校验 + 同步，失败回滚）。可选勾选允许
  LLM 更新 **status**（语义同 CLI `--allow-status-change`）。

### 5.2 技能树（`pages/1_Skill_Tree.py`）

- **保存** 在**标题行右侧**（与本页约定一致，区别于看板工具栏）。
- 按分类标签、等级浏览；每节点可改状态、备注、内联证据。
- **证据池** 折叠区维护共享目录；节点可多选 **引用** 池 id。**保存** 一次
  落盘树 + 池并尝试同步 SKILL.md。

### 5.3 Evidence Review（`pages/2_Evidence_Review.py`）

详细使用说明见 [Evidence Review 使用说明](evidence-review.md)。

- **审阅队列** — 承接看板 Done -> Evidence 的候选流，人工选择后才写入
  `evidence-pool.yaml` 和必要的 `skill-tree.yaml` 引用。
- **Claim Studio** — 从 Project / Goal / Skill / All Evidence / Manual 范围生成
  claim candidates；候选只在当前会话预览中存在，点击 **应用所选** 后才写入
  profile 级 `claims.yaml`。
- Claim card 会展示文本、类型、状态、刷新状态、支撑 evidence、关联 skill /
  project / goal、公开准备度、置信度和 warning。应用 claim 不会自动改
  `skill-tree.yaml` status，也不会新增顶层 Claims 页面。
- **证据池 / 链接 / 引用 / 风险** — 继续维护 evidence row、skill/project/
  experience/source refs 和断链提示；保存路径会保留已有 `claims`。

### 5.4 差距分析（`pages/2_Gap_Analysis.py`）

- 选择上下文来源：**手动输入**、**Current goal**、**Kanban task**。页面会优先复用
  上次选择；否则优先选择 Doing / Queue task，再选择允许进入 Agent context 的
  current goal，最后回退手动输入。
- 选择 Kanban task 时，任务正文会自动带入 title、context、why、outcome、
  blocked_by、dates、subtasks、details，不需要重复手输任务描述。
- private goal 或 `include_in_agent_context=false` 的 goal 不会出现在 Current goal
  选项中。手动输入和 Kanban task 默认可附加 privacy-safe current goal context；
  Current goal source 本身不会重复追加 goal context。
- 点击 **分析** 后执行规则匹配；可选 AI 首轮路由或手动选节点。
- 展示匹配、依赖闭包、建议下一步。
- 结果会显示来源 provenance，例如 manual / current goal / kanban task，以及是否使用了 current goal context。
- **AI 分析** 区 — 已配置 LLM 时为教练与追问；未配置时统一 **未配置 AI**
  提示（与首页、看板一致）。
- **写回** — 勾选缺口节点并选择新状态，写回 `skill-tree.yaml`。

### 5.5 看板（`pages/3_Kanban.py`）

**详细步骤与 FAQ：** [看板使用手册](kanban.md)。

- 工具栏 **从文件重新加载** / **保存** — 对应 `kanban.md`。
- 四列：进行中、队列、已完成、也许/将来（显示名随 `UI_LANG` 切换）。
- 新建与编辑任务时，**按列只突出主字段**（如进行中：背景 + 开始日；队列：原因 + 阻塞；已完成：结果 + 背景）；其余在 **「更多字段」** 折叠中填写（详见 [看板使用手册 · §4](kanban.md)）。
- 任务下可维护 **子任务（勾选）** 与自由备注。
- **移动列** 用列名 **按钮**（非「完成状态」菜单）；可选 **自动填写开始/结束日期**（移入进行中/已完成时）。
- Done 卡片保留单卡 **归档**（写入 `kanban-archive.md` 后移出 Done）和 **删除**；批量 Done 整理已移到 **Evidence Review → Done 队列 / 整理**，说明见 [看板使用手册](kanban.md)。
- **已完成 → 证据** 统一在 Evidence Review 处理：多选 Done 任务生成草案后，可按条勾选 **采纳** 证据行与节点更新，**应用所选条目**（或 **应用完整草案**）；可选 **应用后标记已结晶**。流程对齐 `nblane ingest-kanban`，Web 侧重分项审阅。
- 侧栏 **AI / LLM** 中的 **看板 AI 引擎** 可在普通 LLM 与本地 Codex 间切换；选择 Codex 时，Gap 节点路由、拆任务、任务理解和 Done → evidence 使用部署级 / 终端同款 `CODEX_HOME` 下的只读 `codex exec`，不需要看板内额外配置，也不会创建 patch handoff。
- 看板拆子任务的粒度和风格提示会按 profile 记入 `web-preferences.yaml`；如果 Codex 配置错误导致生成失败，卡片上的错误可跳转到 Agent Activity 中对应的 failed 条目。
- Kanban 卡片上的 **Gap** 预览会带入 privacy-safe current goal context，与
  差距分析页选择 Kanban task 时的上下文一致；不会自动写回 goal、kanban 或
  skill-tree。
- **本轮看板优化方向**：`kanban.md` 使用稳定 task id（保留 `id` meta 行；
  无 id 的旧任务会生成兼容 id），并明确拖拽方向：纵向指针位置决定插入
  `to_index`；拖入另一列会映射为 `to_section`，再沿用手动移动的 done flag /
  自动日期规则。页面级拖拽逐步接入期间，显式移动控件仍是可靠 fallback。

### 5.6 团队视图（`pages/4_Team_View.py`）

- 选择 **团队**（`teams/` 下目录名）。
- 编辑团队字段与各 **产品池** tab，保存 `team.yaml` 与
  `product-pool.yaml`。

### 5.7 Profile Health（`pages/5_Profile_Health.py`）

- 只读报告，与 `nblane health <名称>` 同源。
- 检查校验结果、生成块 drift、solid/expert 节点缺证据、Done 任务未结晶。
- 不写入 profile 文件；阶段 / 周复盘候选已拆到独立 **Review** 页面。

### 5.8 Review（`pages/8_Review.py`）

详细使用说明见 [Review 使用说明](review.md)。

- 从周 / 阶段窗口生成 `evidence`、`next_action`、`public_draft` 候选，以及只读
  `method_note`。
- 生成候选只读；保存所选会写入 `agent-activity.yaml` 的 pending 队列。
- Evidence 候选可直接写入 `evidence-pool.yaml`，并可把来源 Done task 标记为
  `crystallized`；不会自动提升 skill status。
- Next action 候选可追加到 `kanban.md` 的 Queue。
- Public draft 候选只创建 draft blog，不发布。

### 5.9 Agent Activity（`pages/9_Agent_Activity.py`）

- 读取 `agent-activity.yaml`，按 status、kind、candidate type、source page 和 owner
  过滤跨页面候选、patch 和写回结果。
- 页面按 `source_page` 分组展示。看板错误卡片跳入时会携带
  `activity_item` 与 `source_page=Kanban` 查询参数，并高亮对应条目。
- pending Review 候选可以在 Activity 页应用；其他来源的 patch 第一版只审查并跳转
  owner 页面。
- `dismissed` / `failed` 条目可以 reopen，便于重新审阅。
- Codex 配置不在本页编辑；统一使用侧栏 **AI / LLM -> 配置 Codex**。

### 5.10 Research Workspace（`pages/7_Research.py`）

详细使用说明见 [Research 使用说明](research.md)。

- **Source Inbox** 继续接收网页、论文、repo、书籍、手动链接和 Home capture；写入
  `research/sources.yaml`，不会直接写 evidence、skill status 或公开输出。
- **Paper Library** 是论文选择和整理入口；主体验已迁到 `8502 /paper-library`，
  支持 tree / paper list / detail 同 canvas、collection 操作、拖拽、右键菜单、搜索筛选、
  Abstract Preview、PDF 状态和 Reader quick action。`Find and import papers` 已迁入 8502 Paper Library 顶部，
  支持 Codex 任意来源 PDF 搜索、adaptive budget、过程 events、Cancel、provider fallback 和选中后导入到当前 collection；
  搜索结果默认用粗读候选卡展示 abstract、AI overview、relevance、讲解链接、PDF/DOI/provider 状态，
  方便先判断哪篇值得导入；8503 仅在 8502 不可用或手动打开 fallback 时显示旧 Streamlit 导入面板。
- **Reader** 是单篇论文阅读现场，不再作为 Research Workspace 的常驻一级 tab。
  从 Paper Library 的 `Open Reader` 或 Overview 的 `Continue reading` 直接进入具体论文；
  Paper Library 只做 abstract / summary 速览，不嵌完整 PDF Reader。
- **Reading Room** 对单个 source 生成翻译、摘要、claim candidates 和 citations；保存后仍停留在 source-scoped annotations。
- **Claims & Citations** 可把 source 切成 `research/chunks/*.jsonl`，创建
  `research/claims.yaml` research claim，并用 `research/citations.yaml` 绑定
  claim 到 source/chunk。Review Board 的 claim card 可直接 patch text/type/confidence、
  替换 chunk/citation links、从 chunk 建 citation、Request citation、填写 dismiss rationale，
  并支持 ready claim 批量 quote check / mark ready / promote preview 与重复 claim 合并提示。
  Research claim 生成 evidence 时仍是 `needs_review` 候选。
- **Synthesis Drafts** 从 research claims 生成 `research/drafts.yaml` 与
  `research/drafts/*.md`；空 body 会生成 outline、argument map、coverage 和
  missing citation warnings，页面会显示 draft coverage review。Citation export 支持
  Markdown、BibTeX、RIS、CSL JSON，并可创建带 `related_sources` /
  `related_research_claims` / `related_citations` 的 blog draft、project update 和
  resume bullet candidate；三类候选共用同一套 manifest gate。
- **Inbox & Connectors** 管理来源收件箱和 `research/connectors.yaml`，支持 arXiv、Semantic Scholar、
  GitHub 自动导入；dry-run/manual candidate import 可明确落到 Source Inbox、
  collection 或 metadata only。X/Twitter 与小红书第一版走手动导入或官方授权边界。
  配置文件不保存 token、cookie 或 API key。

### 5.11 Output Studio（`pages/6_Output_Studio.py`）

详细使用说明见 [Output Studio 使用说明](output-studio.md)。

- 为当前档案初始化缺失的公开层文件。
- **Generate** 从 reviewed evidence 或 accepted claims 生成 blog draft、resume bullet preview、project update draft。
- **Profile** 编辑公开姓名、headline、简介、联系方式、头像、原始 YAML，并提供实时整站预览。
- **Blog** 通过 React / BlockNote 编辑器 shell 管理 draft / published 文章，支持 front matter、媒体、AI 候选、发布检查和公开页预览。
- Blog 支持 `related_claims` 与 research provenance refs；发布校验会检查 accepted claim、promoted research claim、source visibility 和 citation/chunk 断链。
- **Resume** 编辑 `resume-source.yaml`，预览 Markdown，并生成定制简历草稿；从 accepted claims 生成的 bullet 候选不会自动写回。
- **Known Info** 将选中的 evidence 整理成 draft 公开项目。

### 5.12 Public Build（`pages/10_Public_Build.py`）

详细使用说明见 [Public Build 使用说明](public-build.md)。

- 只负责静态站校验、预览和构建，不编辑 Blog / Resume / Known Info。
- 默认构建到 `dist/public/<profile>`；可选择是否包含 draft/private 预览内容，并填写生产 `Base URL` 生成 SEO 与子路径部署链接。

### 5.13 Public Site 兼容入口（`pages/6_Public_Site.py`）

- 旧入口保留为跳转页，指向 **Output Studio** 与 **Public Build**，避免旧链接失效。

---

## 6. 与 CLI 的对照

| Web 操作 | CLI |
|----------|-----|
| 简历 / 长文本摄入 | `nblane ingest-resume <名称> …` |
| 已完成 → 证据 | `nblane ingest-kanban <名称> …` |
| 导出上下文 | `nblane context <名称>` |
| 差距结果 | `nblane gap <名称> "…"` |
| 编辑后检查 | `nblane validate <名称>` |
| 成长体检 / Profile Health | `nblane health <名称>` |
| SKILL.md 生成块 | `nblane sync <名称> --write` |
| 证据池 / 内联 | `nblane evidence <名称> …` |
| 公开站校验 / 构建 | `nblane public validate <名称>` / `nblane public build <名称>` |
| 博客与简历草稿 | `nblane public blog …`、`nblane public draft-blog …`、`nblane public draft-resume …` |

详见 [数据契约](../architecture/data-contracts.md)、
[Evidence 参考](../reference/evidence.md)、[公开站点](public-site.md)。

---

## 7. 相关文档

- [Dashboard 使用说明](dashboard.md)
- [Skill Tree 使用说明](skill-tree.md)
- [Kanban 使用说明](kanban.md)
- [Project Board 使用说明](project-board.md)
- [Evidence Review 使用说明](evidence-review.md)
- [Research 使用说明](research.md)
- [Review 使用说明](review.md)
- [Gap Analysis 使用说明](gap-analysis.md)
- [Profile Health 使用说明](profile-health.md)
- [Output Studio 使用说明](output-studio.md)
- [Public Build 使用说明](public-build.md)
- [Team View 使用说明](team-view.md)
- [Agent Activity 使用说明](agent-activity.md)
- [Web 体验设计（Streamlit）](../product/web-experience.md) — 信息架构、品牌、backlog
- [当前状态](../project/status.md) — 已交付页面表
- [架构总览](../architecture/overview.md)
- [公开个人网站、博客与简历](public-site.md) — Public Surface v1
- [MCP 服务器](../reference/mcp.md) — Cursor / 外部 Agent 集成
