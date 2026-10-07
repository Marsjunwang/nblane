---
status: active
owner: docs
last_verified: 2026-10-07
source_of_truth: true
---

# 公开个人网站、博客与简历

本文说明已经落地的公开层：个人网站、博客和简历由 profile 下显式公开的
YAML / Markdown 文件生成，不直接渲染内部 profile 文件。

入口是 SPA「公开站点」（`/p/<name>/public-build`），命令行是 `nblane public ...`。
文章在[内容工作台](content.md)写作并发布进公开层，在这里决定是否上线。
发布、回滚等操作只能由本人在页面上做，助手不能代为执行。

**定位（2026-10-05 定）：** 公开站 = 自我介绍 + 写作 + 作品。首页是照片和简介
（来自求职工作台的主简历），主体是博客和「作品」（重点项目视频、论文、代码、
发表在别处的文章链接）。`projects.yaml` 是内部工作记录，默认不上线。

## 公开站点控制台

左边决定网站显示什么，右边是实时预览，顶部发布到线上。第一次打开时点「初始化」创建公开资料文件，
不会改动已有内容。

- **网站公开**：`public-profile.yaml` 的 `visibility`。私有时不能发布。
- **显示开关**：写在 `public-profile.yaml` 的 `site:` 下，全部可单独开关：

  ```yaml
  site:
    show_photo: true      # 首页显示主简历照片
    show_email: false     # 首页联系方式里显示邮箱
    show_phone: false     # 首页联系方式里显示电话
    resume_pdf: false     # 发布时生成 /resume.pdf 并在首页提供下载
    show_projects: false  # 公开 projects.yaml（默认不公开）
    base_url: ""          # 子路径部署时填写
  ```

  首页的姓名、头衔、简介和照片读主简历 `resume-source.yaml`（`basics.title`、
  `summary`、`basics.photo`），`public-profile.yaml` 的 `headline` / `bio_short`
  只在主简历为空时兜底。简历 PDF 用服务器上的 Chromium 打印，电话、邮箱、
  照片跟随上面的开关；生成失败只出提示，不阻断发布。网站不再有在线简历页。
- **写作**：每篇文章一个「公开」开关。打开 = 通过发布检查后发布，并把
  `public-library.yaml` 里的节点设为 public；关闭 = 撤回为草稿。徽标显示
  「线上 / 待发布 / 发布后下线 / 库中隐藏」。
- **作品**：编辑 `outputs.yaml`（见下节）。改动先在本地，点「保存作品」写盘，
  带 ETag，别处改过会提示刷新。
- **预览**：默认就是线上会看到的内容；「预览包含草稿」只影响预览。
- **发布到线上**：顶部显示与线上目录的差异（新增 / 更新 / 下线页、简历 PDF），
  确认后直接构建到线上目录（只含已公开内容），上一版保留为
  `.<name>.prev`，可以「回滚」（再回滚一次即恢复）。

### 作品字段（`outputs.yaml`）

```yaml
outputs:
  - id: arm-demo
    title: 机械臂抓取演示
    type: video          # video / paper / article / demo / code / talk / other
    year: "2026"
    summary: 一句话说明
    video: https://www.bilibili.com/video/BV1xx411c7mD
    video_mode: embed    # embed = 直接播放；link = 只放「观看视频」链接
    cover: media/works/cover-1a2b3c4d5e.png
    links:
      论文: https://arxiv.org/abs/2401.00001
      代码: https://github.com/example/repo
    status: published
    featured: true       # 首页精选；没有精选时首页显示前 4 条
```

内嵌播放支持 B 站（`bilibili.com/video/BV…` 自动转播放器）、YouTube、Vimeo，
以及本地或外链的 `mp4` / `webm`；其他网址按链接显示。控制台上传的视频和封面
放在 `media/works/`。作品页是 `/outputs/`，不再有单条作品详情页。

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
  public-library.yaml
  blog/
  media/
  resumes/generated/
```

所有公开文件默认仍是 private / draft，发布必须显式确认：

- `public-profile.yaml`：普通公开构建前需要 `visibility: public`。
- `resume-source.yaml`：首页简介与照片的来源（求职工作台的主简历）；网站不再有在线简历页。
- `blog/**/*.md`、`projects.yaml`、`outputs.yaml`：需要 `status: published`
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

Blog front matter 也可以通过 `related_claims` 记录 accepted claim provenance。
这些 claim 来自 profile 级 `claims.yaml`；旧 `evidence-pool.yaml.claims`
只作为迁移前兼容来源。发布校验会检查 claim id 是否存在、状态是否为
`accepted`、是否需要 refresh，以及 claim 里的 `evidence_refs` 是否仍存在；
静态站不会直接渲染 claim id。

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
nblane public build <profile> --include-drafts --out dist/public-preview/<profile>
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
nblane public blog new <profile> --title "VLA 笔记" --category robotics/software/vla
nblane public blog new <profile> --title "我的文章" --stdin
nblane public blog media <profile> <slug-or-route> \
  --file ./cover.png \
  --kind image \
  --alt "封面图" \
  --cover \
  --append
nblane public blog media <profile> <slug-or-route> \
  --file ./demo.mp4 \
  --kind video \
  --caption "短视频演示" \
  --append
nblane public blog publish <profile> <slug-or-route>
```

管理 Public Site 文件树：

```bash
nblane public library tree <profile>
nblane public library tree <profile> --include-trash --format yaml
nblane public library reconcile <profile>
nblane public library trash <profile> <node-id>
nblane public library restore <profile> <node-id>
nblane public library purge <profile> <node-id>
nblane public library purge <profile> <node-id> --delete-files
```

`public-library.yaml` 是公开内容的后台文件树。它可以同时管理
folder、post、media 节点，post 节点下面也可以继续挂 folder、post、media。
folder 只是后台组织元数据：新建或移动 folder 不会在磁盘上创建或移动目录。

```yaml
version: 1
profile: 王军
nodes:
  - id: root
    type: root
    title: Public Library
    parent_id: ""
    order: 0
    visibility: private
    status: active
  - id: fld_robotics
    type: folder
    title: 机器人
    parent_id: root
    order: 10
    visibility: private
    status: active
  - id: post_vla_notes
    type: post
    title: VLA 调研笔记
    ref: blog/vla-notes.md
    parent_id: fld_robotics
    order: 20
    visibility: public
    status: active
    owned: false
  - id: media_demo
    type: media
    title: demo.mp4
    ref: media/blog/vla-notes/demo.mp4
    parent_id: post_vla_notes
    order: 30
    visibility: private
    status: active
    owned: true
```

公开 URL 由 Markdown route 决定，不由文件树父子关系决定。把
`post_vla_notes` 移到另一个 folder，只改变后台组织方式；`/blog/vla-notes/`
仍保持不变。普通公开导航只显示同时满足这些条件的文章：library node 是
`status: active`、`visibility: public`，并且 Markdown front matter 是
`status: published`。

删除是两阶段：`trash` 只把节点或子树标记为 `status: trashed`，隐藏加载、保存、
发布和普通构建，但不删除文件；`restore` 尽量恢复到原父节点；`purge` 才会从
文件树中永久移除 trashed 节点。默认 purge 也不删物理文件；只有显式加
`--delete-files` 时，post 才可能删除 Markdown、BlockNote sidecar 和
`media/blog/<route>/` 目录。media 永久删除会检查 active 文章中的 cover、正文
图片、video directive 和 visual block 引用；仍被引用时拒绝删除源文件。

`reconcile` 是迁移命令：它会把现有 `blog/**/*.md` 与
`media/blog/<route>/` 文件导入 `public-library.yaml`，不会改 URL，也不会重复
创建已有节点。

`blog-taxonomy.yaml` 继续兼容旧 profile 和“URL 分类目录”需求。当
`public-library.yaml` 中已经有真实节点时，文件树成为后台组织源；taxonomy 不再
限制 folder、post、media 的自由挂载。只有在你希望 URL 本身带分类路径时，
才需要继续使用 taxonomy。

如果需要让博客 URL 带分类目录，在 profile 根目录新增 `blog-taxonomy.yaml`。
`slug` 用于文件夹和 URL，`title` 用于页面显示：

```yaml
profile: 王军
taxonomy:
  - slug: robotics
    title: 机器人
    children:
      - slug: hardware
        title: 硬件
      - slug: software
        title: 软件
        children:
          - slug: vla
            title: VLA
          - slug: motion-control
            title: 运控
  - slug: uncategorized
    title: 未分类
```

taxonomy 启用后，文章可以放在多层目录：

```text
profiles/<name>/blog/robotics/software/vla/my-post.md
```

对应公开 URL 是 `/blog/robotics/software/vla/my-post/`，本地媒体放在
`profiles/<name>/media/blog/robotics/software/vla/my-post/`。front matter
建议显式记录分类路径：

```yaml
category_path: [robotics, software, vla]
```

CLI 的 `<slug-or-route>` 兼容旧单段 slug；如果不同分类下有同名文章，需要传完整
route，例如 `robotics/software/vla/my-post`。

博客正文仍是 Markdown。图片使用标准 Markdown：

```markdown
![Alt text](media/blog/<slug-or-route>/image.png)
```

短视频使用 nblane 视频指令：

```markdown
::video[短视频演示](media/blog/<slug-or-route>/demo.mp4)
::video[外部视频](https://example.com/demo.mp4)
```

博客本地媒体放在 `profiles/<name>/media/blog/<slug-or-route>/`。图片支持
`png`、`jpg`、`jpeg`、`webp`、`gif`，单文件上限 10 MB；本地短视频支持
`mp4`、`webm`，单文件上限 25 MB。更大的视频建议使用外链或对象存储。
如果 front matter 中设置了 `cover: media/blog/<slug-or-route>/cover.png`，Blog 列表卡片、
文章详情 header、`og:image` 和 `twitter:image` 都会使用该封面；草稿预览遇到
缺失或不合法封面时会降级为纯文本布局，发布校验会继续报告该 cover 错误。

在 SPA 里写作、预览和发布文章见 [内容工作台](content.md)。

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

## 部署

推荐分离私有工作台和公开站：

```text
spa.example.com  -> 受登录保护的 SPA（127.0.0.1:8504，Reader 路由转 8502）
www.example.com  -> dist/public/<profile> 静态目录
```

公开站只需要 Caddy `file_server`：

```caddyfile
www.example.com {
    root * /srv/nblane-public/alice
    file_server
}
```

SPA 与 Reader 的完整反代配置见 [腾讯云部署](deployment-tencent-cloud.md)。

构建器会先校验，再写入临时目录，最后替换目标目录。校验或渲染失败时，不会
覆盖已有线上目录。

生产环境里 `/srv/nblane-public` 是 `/srv/nblane-data/dist/public` 的 bind
mount（`/etc/fstab`），Caddy 直接服务 `/srv/nblane-public/<profile>`。所以
**构建到 `dist/public/<profile>` 就是上线**：控制台「发布到线上」和
`nblane public build <profile>`（默认输出目录）都会立刻改变线上网站。
`--include-drafts` 构建写入这个目录会被拒绝，需要用 `--out` 指定别的目录。

## 边界

当前版本刻意不包含：

- 评论系统
- 全文搜索
- 多主题市场
- 数据库存储；当前单仓库工作流使用 `public-library.yaml` 做索引
- 对象存储媒体上传

小图片可以放在 `profiles/<name>/media/`。视频默认使用外链或对象存储。
v1 也允许把小型 `mp4` / `webm` 短视频放在 `media/blog/<slug-or-route>/`。

Public 层会拒绝博客 Markdown 和公开字段中的危险 `href` / `src` scheme，
例如 `javascript:` 与 `data:`。但 Markdown 原始 HTML 仍按“可信本地作者”
模型处理，并不是面向外部多人输入的完整 HTML sanitizer；若后续开放给外部
作者，需要再加 allowlist sanitizer。
