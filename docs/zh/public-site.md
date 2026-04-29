# 公开个人网站、博客与简历

本文说明已经落地的公开层：个人网站、博客和简历由 profile 下显式公开的
YAML / Markdown 文件生成，不直接渲染内部 profile 文件。

English version: [../public-site.md](../public-site.md).

**当前状态：** Public Surface v1 已落地。仓库现在包含 profile 级公开数据文件、
`nblane public ...` CLI、静态站构建器，以及 Streamlit **Public Site** 页面。
后续重点不再是“是否有公开面”，而是继续打磨 React Blog Shell 工作流、
更完整的 SEO、部署链路与展示质量。

## 数据层

已有 profile 先执行一次：

```bash
nblane public init <profile>
```

新 profile 会通过 `profiles/template/` 自动带上这些文件：

```text
profiles/<name>/
  public-profile.yaml
  resume-source.yaml
  projects.yaml
  outputs.yaml
  blog/
  media/
  resumes/generated/
```

所有公开文件默认仍是 private / draft，发布必须显式确认：

- `public-profile.yaml`：普通公开构建前需要 `visibility: public`。
- `resume-source.yaml`：需要 `visibility: public` 才会进入在线简历页。
- `blog/*.md`、`projects.yaml`、`outputs.yaml`：需要 `status: published`
  才会进入普通构建。
- `--include-drafts` 只用于本地预览草稿 / 私有内容。

生成器不会渲染这些内部文件：

```text
SKILL.md
skill-tree.yaml
kanban.md
kanban-archive.md
agent-profile.yaml
auth/users.yaml
```

公开对象可以通过 `evidence_refs` 引用证据，但不会把整个
`evidence-pool.yaml` 当成公开 CMS 渲染。

公开项目是 evidence 的聚合视图。`evidence-pool.yaml` 继续保留原子工作
留痕；只有人工确认后，才把多条 evidence id 聚合进 `projects.yaml`。

## CLI

校验公开层：

```bash
nblane public validate <profile>
nblane public validate <profile> --include-drafts
```

构建静态站：

```bash
nblane public build <profile>
nblane public build <profile> --out dist/public/<profile>
nblane public build <profile> --include-drafts
nblane public build <profile> --base-url https://www.example.com
nblane public build <profile> --base-url https://www.example.com/site
```

`--base-url` 会用于 canonical / OpenGraph、`robots.txt`、`sitemap.xml`
以及站内链接。若 URL 带有 `/site` 一类子路径，生成的 `href` / `src`
会自动加上此前缀，便于子路径部署。

生成简历 HTML 与 Markdown：

```bash
nblane public resume <profile>
nblane public resume <profile> --out profiles/<profile>/resumes/generated/default.html
```

创建公开输出草稿：

```bash
nblane public draft-blog <profile> --from-evidence <evidence_id>
nblane public draft-blog <profile> --from-kanban-done
nblane public draft-resume <profile> --target "VLA robotics engineer"
nblane public draft-project-update <profile> --project <project_id>
```

草稿命令在配置 `LLM_API_KEY` 后会使用 LLM；没有配置时使用保守模板兜底。
它们只写入 draft，不会自动发布。

写作与发布博客：

```bash
nblane public blog list <profile> --include-drafts
nblane public blog new <profile> --title "我的文章" --tag robotics
nblane public blog new <profile> --title "我的文章" --stdin
nblane public blog media <profile> <slug> \
  --file ./cover.png \
  --kind image \
  --alt "封面图" \
  --cover \
  --append
nblane public blog media <profile> <slug> \
  --file ./demo.mp4 \
  --kind video \
  --caption "短视频演示" \
  --append
nblane public blog publish <profile> <slug>
```

博客正文仍是 Markdown。图片使用标准 Markdown：

```markdown
![Alt text](media/blog/<slug>/image.png)
```

短视频使用 nblane 视频指令：

```markdown
::video[短视频演示](media/blog/<slug>/demo.mp4)
::video[外部视频](https://example.com/demo.mp4)
```

博客本地媒体放在 `profiles/<name>/media/blog/<slug>/`。图片支持
`png`、`jpg`、`jpeg`、`webp`、`gif`，单文件上限 10 MB；本地短视频支持
`mp4`、`webm`，单文件上限 25 MB。更大的视频建议使用外链或对象存储。
如果 front matter 中设置了 `cover: media/blog/<slug>/cover.png`，Blog 列表卡片、
文章详情 header、`og:image` 和 `twitter:image` 都会使用该封面；草稿预览遇到
缺失或不合法封面时会降级为纯文本布局，发布校验会继续报告该 cover 错误。

Blog 编辑器的 Public Preview 使用当前会话中的 meta/body 做 in-memory 渲染，
不需要先保存到磁盘。发布则走 `publish_blog_text()`：先校验未保存的 meta/body，
通过后才写回 `blog/<slug>.md` 并记录 `publish ...` Git backup action。

视觉生成配置使用 `VISUAL_*` 命名，并兼容旧式 `IMAGE_*` alias。默认 provider 是
DashScope / 通义万相：

```env
LLM_API_KEY=sk-...
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen3.6-plus

# Optional visual overrides
VISUAL_PROVIDER=dashscope_wan
VISUAL_IMAGE_MODEL=wan2.7-image-pro
VISUAL_VIDEO_MODEL=wan2.7-videoedit
VISUAL_API_KEY=
```

千问 / DashScope 视觉生成默认复用现有 `LLM_API_KEY`；只有图像 / 视频任务与文本
LLM 使用不同账号或不同凭据时才需要 `VISUAL_API_KEY`。视觉模块只复用 key 和
DashScope 域名信息，不会把 chat completions 的 `/compatible-mode/v1` 当成图像
或视频任务 endpoint。

把已知信息整理成公开草稿：

```bash
nblane public suggest-groups <profile> --dry-run
nblane public group <profile> \
  --id piper-home-robot \
  --title "Piper / 家庭整理机器人项目" \
  --evidence ev_piper_repro \
  --evidence ev_piper_demo_fix
nblane public hydrate <profile> --dry-run
nblane public hydrate <profile> --write-drafts
```

`suggest-groups` 只读预览。`group` 只向 `projects.yaml` 写入
`status: draft` 项目，不修改 evidence 或 skill 文件。`hydrate` 只把明显的
paper / patent evidence 一对一补成 `outputs.yaml` 成果草稿。

## Streamlit

生成出的首页是一个紧凑的内容总入口。它展示公开姓名、headline、简介、联系
方式，并固定提供 Blog、Projects、Outputs、Resume 四类入口。首页每块只展示
标题、数量或最近条目；点击后进入全量列表、博客详情、项目/成果列表或完整
简历。

Web UI 新增 **Public Site** 页面：

- **Profile** 提供结构化表单编辑公开姓名、headline、简介、联系方式与头像；
  保存时会把头像写入 `media/` 并同步 `public-profile.yaml` 的 `avatar` 路径。
  右侧提供实时整站预览，未保存的文字和新上传头像也会进入预览；原始 YAML 仍
  在折叠区内可直接编辑。
- **Blog** 通过 React / BlockNote 编辑器 shell 创建、编辑、检查并发布博客。
  shell 包含文章筛选、新建草稿、从 evidence / Done 生成、正文编辑区、
  Meta / Media / AI / Visual / Check 右侧抽屉、Public Preview、移动端
  Editor / Articles / Tools / Preview tab、专注模式和 browser `localStorage`
  布局记忆。Streamlit 继续负责文件 I/O、session state、上传落盘、AI / 视觉调用、
  发布校验、静态预览与 Git backup。
- **Resume** 编辑 `resume-source.yaml`，预览生成简历，并生成定制简历草稿。
- **Known Info** 展示 evidence 上下文、推荐分组，并支持勾选多条 evidence
  生成 draft 项目。
- **Build** 校验并构建静态站，也可以生成项目更新草稿。

该页面复用现有 profile 选择器、文件 snapshot 冲突保护、缓存清理与可选 Git
备份。

## 当前 v1 与下一步优化

已落地的 v1 覆盖完整公开闭环：

- **数据层：** `public-profile.yaml`、`resume-source.yaml`、`projects.yaml`、
  `outputs.yaml`、`blog/*.md` 与 profile 媒体目录。
- **CLI：** 初始化、校验、静态构建、简历生成、博客创建/媒体/发布、草稿生成、
  evidence 到公开项目的人工整理。
- **Web UI：** **Public Site** 页面，含 Profile、Blog、Resume、Known Info、
  Build 五个 tab。
- **静态输出：** 首页、Blog、Projects、Outputs、可选 Resume、复制后的媒体、
  Blog cover 展示、Open Graph / Twitter 图片、`robots.txt`、`sitemap.xml` 与页面
  meta description。

下一轮优化方向：

- **React Blog Shell 打磨：** Markdown / front matter 仍是事实源，继续补齐
  更细的块级光标插入、更多 visual provider adapter 和前端 smoke 测试。
- **SEO 质量：** 继续优化 canonical、Open Graph、社交分享 metadata、按 profile
  优化 title，并在部署时校验 `base-url` / base path。
- **部署质量：** 补静态托管、缓存刷新、草稿预览 vs 公开构建、小团队受保护
  Streamlit 工作台的生产说明。
- **展示质量：** 改进生成主题、响应式布局、媒体展示、项目/成果详情页与简历可读性。

## 部署

推荐分离私有工作台和公开站：

```text
app.nblane.cloud  -> 受登录保护的 Streamlit 工作台
www.nblane.cloud  -> dist/public/<profile> 静态目录
```

Caddy 示例：

```caddyfile
www.example.com {
    root * /srv/nblane-app/dist/public/alice
    file_server
}

app.example.com {
    reverse_proxy 127.0.0.1:8501
}
```

构建器会先校验，再写入临时目录，最后替换目标目录。校验或渲染失败时，不会
覆盖已有线上目录。

## 边界

当前版本刻意不包含：

- PDF 简历生成
- 评论系统
- 全文搜索
- 多主题市场
- 数据库存储
- 对象存储媒体上传

小图片可以放在 `profiles/<name>/media/`。视频默认使用外链或对象存储。
v1 也允许把小型 `mp4` / `webm` 短视频放在 `media/blog/<slug>/`。

Public 层会拒绝博客 Markdown 和公开字段中的危险 `href` / `src` scheme，
例如 `javascript:` 与 `data:`。但 Markdown 原始 HTML 仍按“可信本地作者”
模型处理，并不是面向外部多人输入的完整 HTML sanitizer；若后续开放给外部
作者，需要再加 allowlist sanitizer。
