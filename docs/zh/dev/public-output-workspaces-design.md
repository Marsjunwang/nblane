---
status: proposed
owner: product/engineering
last_verified: 2026-10-04
source_of_truth: true
---

# 公开输出三工作台重构设计

本文定义 nblane 公开输出部分的下一阶段产品边界与开发计划。目标是把当前过于
复杂的 Output Studio 收敛为三个相互独立、可以分别做好的工作台：

1. **内容工作台**：直接创作和管理博客；项目编辑暂缓，后续与项目页面合并。
2. **求职工作台**：维护主简历、上传简历、匹配 JD、生成定制简历。
3. **公开站点**：选择公开内容、预览、发布并构建个人静态网站。

本文是开发前的产品与架构基线。实现过程中如果需要改变范围、数据源或页面边界，
应先更新本文，再开始对应代码变更。

## 1. 当前实现与本阶段范围

本文同时记录现状和目标，必须区分“已有能力”“本阶段新增/调整”和“后续延期”。当前 React SPA 仍使用 `/p/:name/studio` 与 `/p/:name/public-build`；Output Studio 已支持博客草稿 CRUD、Markdown 正文、发布前检查、发布、从证据/断言生成候选以及 JD 匹配任务；Public Build 已支持校验、草稿预览、博客草稿选择性发布并构建、构建产物清单。文档后续提出的 `/content`、`/career`、构建历史和 manifest 都是目标能力，不应被理解为现状。

| 领域 | 当前实现 | 本阶段确定范围 | 后续/暂缓 |
| --- | --- | --- | --- |
| 内容工作台 | Output Studio 中已有博客列表、新建、Markdown 编辑、保存、检查、发布；仍有“从证据生成”标签 | 只建设博客创作与管理；用户先自行梳理内容，支持保存、预览、检查、发布和媒体 | 项目创建/编辑暂不做，后续与“项目”页面结合；不建设“全部内容/媒体”独立信息架构 |
| AI | 已有候选生成、JD 分析等入口 | 极度克制，仅做用户明确触发的辅助；结果必须作为候选或建议，经用户查看、修改、确认后才写入 | 自动写作、批量生成、直接覆盖正文、以 AI 代替用户梳理内容 |
| 求职工作台 | 当前主要是粘贴简历与 JD 后通过 Job + SSE 分析；主简历和导入能力尚未形成独立工作台 | 按现有设计实现最小闭环：简历输入/导入、JD 输入、匹配分析、定制简历草稿、人工编辑和导出；先不扩展复杂版本管理 | 多岗位版本历史、复杂反馈编排、完整简历产品能力 |
| 公开站点 | 已有校验、预览、草稿/私有预览开关、博客草稿发布并构建、产物列表 | 保留发布闸门职责，补齐内容选择、预览和构建体验；视觉与现有明亮、干净的公开站点对齐 | 构建历史、`.nblane-build.json` manifest、复杂发布管理 |
| 路由 | 实际为 `/p/:name/studio`、`/p/:name/public-build` | 先在现有入口上收敛能力，路由迁移另行评估 | `/content`、`/career` 三工作台完整路由迁移 |

### 1.1 背景与痛点

当前 Output Studio 同时承担内容创作、证据/Claim 生成、简历维护、JD 匹配和公开站点发布，造成以下问题：

- 用户必须理解 Evidence、Claim、候选和公开输出之间的内部链路，才能完成普通创作。
- 博客编辑、简历编辑和静态站构建被放在同一个复杂页面中。
- Streamlit 与 React SPA 存在两套交互，能力和体验不一致。
- JD 匹配主要停留在输入简历文本和 JD，结果上下文和保存方式仍较简单。
- Public Build 既承担发布控制台，也承载预览和产物检查，信息边界需要更清晰。

本阶段要消除的痛点不是“缺少更多生成按钮”，也不是让 AI 代替用户创作，而是：

> 用户应能先独立完成内容梳理，再用低干扰的辅助能力完成博客创作、求职准备和公开发布。

## 2. 产品边界

### 2.1 本阶段包含

#### 内容工作台

- 直接创建、编辑、保存和发布博客。
- 使用当前编辑器能力编辑博客正文，优先保证 Markdown、媒体、公式和代码等已支持能力稳定。
- 管理图片、视频、封面和其他内容媒体。
- AI 仅提供低风险、局部、可拒绝的辅助，例如标题建议、摘要建议、结构检查或局部改写候选；不得自动写入正文。
- 对内容做发布前检查。

#### 求职工作台

- 编辑 `resume-source.yaml` 对应的主简历。
- 上传 PDF、DOCX、TXT 简历并提取文本。
- 选择主简历、上传简历或粘贴简历作为 JD 匹配输入。
- 输入或上传 JD。
- 展示结构化匹配分析。
- 生成定制简历草稿。
- 人工编辑并导出结果；先采用简单、可恢复的保存方式，不提前引入复杂版本系统。

#### 公开站点

- 展示个人资料、博客和简历的公开准备状态；项目沿用现有公开数据读取，不新增项目编辑流程。
- 选择需要发布的内容。
- 预览个人静态网站。
- 发布选中内容并构建静态站点。
- 查看构建结果、警告、错误和产物清单。

### 2.2 本阶段明确不包含

以下页面和领域保持冻结，不作为本次重构的前置依赖：

- Evidence 页面和 evidence-pool 工作流。
- Claim 页面、Claim 选择和 Claim 生成流程。
- 从 Evidence 生成项目、博客或简历。
- Skill Tree、Kanban、Home Dashboard 的产品流程改造。
- Resume Import 原有首页流程的改造。
- MCP、CLI 既有 evidence 能力的重设计。
- 项目编辑工作台；项目后续与项目页面合并。
- 自动化或批量 AI 创作、未经确认直接写入内容的 AI 流程。
- 数据库、多人协作和在线实时协同编辑。
- Astro、Hugo、Quartz 或完整第三方简历产品的替换。

旧的 Evidence / Claim API 可以继续兼容旧数据和旧调用，但新工作台不得要求用户
进入这些页面，也不得把它们作为新流程的必要步骤。

## 3. 总体信息架构

建议将 React SPA 的个人空间逐步收敛为：

```text
个人空间
├── 内容工作台
│   └── 博客
├── 求职工作台
│   ├── 简历
│   ├── JD 匹配
│   └── 定制简历草稿
└── 公开站点
    ├── 发布准备
    ├── 网站预览
    ├── 发布管理
    └── 构建记录
```

建议路由为：

```text
/p/:name/content
/p/:name/career
/p/:name/public-build
```

现阶段优先在现有 `/p/:name/studio` 和 `/p/:name/public-build` 入口上完成收敛；是否迁移到
`/content`、`/career` 在 Phase 0 后单独决定。旧 Streamlit Output Studio 保留兼容，但不新增
与 React SPA 不一致的产品流程。

三个工作台共享公开层文件、文件锁、ETag 和静态构建器，但不共享 Evidence / Claim
交互流程。

## 4. 内容工作台

### 4.1 产品定位

内容工作台是直接创作工具，而不是证据加工工具。用户打开后应能直接新建博客，不需要先选择来源、
Claim 或生成目标。用户必须先自行梳理和确认内容，AI 只能辅助局部工作。

### 4.2 博客工作区

推荐采用三栏布局：

```text
左侧：文章列表
中间：正文编辑器
右侧：属性、低干扰辅助工具、发布检查
```

文章属性包括：标题、摘要、日期、标签、分类、封面、状态、公开 URL 和媒体引用。

正文编辑器继续使用当前 BlockNote 方向，不迁移到新的编辑器内核。需要将现有
Streamlit custom component 中的编辑器能力抽取为可由 SPA 和 Streamlit wrapper
共同使用的 React 编辑器核心。

第一阶段支持：

- 标题、段落、列表、引用和代码块。
- 数学公式、Mermaid、图片和视频。
- Markdown 快捷输入和 Markdown 源码模式。
- 快速预览和阅读模式。
- 用户主动触发的局部 AI 建议和候选 diff。
- 保存状态、冲突提示和冲突恢复。

AI 结果必须遵循：

```text
生成候选 → 查看 diff → 接受 / 拒绝 → 写入正文
```

AI 不得直接覆盖未确认的正文，也不得把用户未提供的事实包装成已验证成果。

### 4.3 项目工作区（暂缓）

项目创建与编辑不属于本阶段。后续应与现有“项目”页面合并设计；本节字段仅作为未来讨论草案，不作为当前开发契约。

建议字段：

```yaml
id: vla-training-platform
title: ""
status: draft
visibility: private
summary: ""
context: ""
responsibilities: []
actions: []
results: []
technologies: []
period:
  start: ""
  end: ""
links: []
media: []
featured: false
```

编辑器提供项目名称、简介、背景、职责、关键工作、结果、技术栈、时间、链接、媒体、
精选状态和公开状态。

项目 AI 暂缓，待项目页面合并后再单独评估。

### 4.4 内容数据边界

内容工作台只读写公开层：

```text
profiles/<name>/
  public-profile.yaml
  projects.yaml
  outputs.yaml
  blog/
  media/
```

不读写：

```text
evidence-pool.yaml
claims.yaml
skill-tree.yaml
kanban.md
SKILL.md
```

博客继续使用 `blog/<slug>.md` 和 `blog/<slug>.blocknote.json`；Markdown 是发布事实源，
BlockNote JSON 是编辑状态 sidecar。

## 5. 求职工作台

### 5.1 产品定位

求职工作台是简洁的“简历 + JD”工具，不要求用户理解 Evidence、Claim 或其他内部成长数据。
先完成一份简历和一份 JD 的最小闭环，再根据实际使用反馈扩展版本管理。

### 5.2 主简历

主简历事实源继续使用：

```text
profiles/<name>/resume-source.yaml
```

结构化编辑包括基本信息、联系方式、个人标题、摘要、技能、工作经历、项目、教育、
论文成果、语言和外部链接，并同时提供结构化编辑、Markdown 预览和 HTML 预览。

### 5.3 简历导入

复用 `src/nblane/core/resume_extract.py`，支持 PDF、DOCX、TXT 和直接粘贴。

流程：

```text
上传文件 → 文本提取 → 结果预览 → 字段识别 → 用户确认 → 保存目标
```

保存目标必须由用户明确选择：

```text
保存为主简历
保存为新的简历草稿
仅用于本次 JD 匹配
```

上传结果不得直接覆盖 `resume-source.yaml`。解析失败时必须保留手动粘贴入口。

### 5.4 JD 匹配

流程：

```text
选择或上传简历
  ↓
输入或上传 JD
  ↓
开始异步分析
  ↓
查看结构化匹配结果
  ↓
确认修改方向
  ↓
生成定制简历
  ↓
人工编辑和保存版本
```

分析结果至少包括匹配概览、JD 关键要求、已覆盖项、可加强内容、真实缺口、关键词建议、
建议弱化内容和潜在面试问题。

继续复用现有 Job + SSE 基础设施。AI 输入只包括当前简历、当前 JD 和用户手动补充，
不读取 Evidence、Claim、Skill Tree 或 Kanban。

### 5.5 定制简历草稿

当前阶段生成可明确标识目标岗位的定制简历草稿，禁止无提示覆盖主简历。复杂的多岗位版本、manifest
和历史管理暂缓，待最小流程稳定后再设计。

```text
profiles/<name>/resumes/
  generated/
    <target-slug>.md
```

保存和重新生成必须有明确提示，不能无提示覆盖用户已经编辑过的草稿。复杂 hash 和历史记录属于后续增强。

## 6. 公开站点

### 6.1 产品定位

公开站点不是另一个编辑器，而是发布控制台：

```text
准备 → 预览 → 发布 → 构建
```

它读取内容工作台和求职工作台产生的公开层文件，不负责编辑正文、项目字段或简历。

### 6.2 发布准备与选择

页面用状态卡展示个人资料、博客、简历和现有公开成果的准备状态和数量。校验结果
分为：

```text
通过
警告
阻止发布
```

新创建的博客、项目和简历不需要 Claim 才能发布。旧内容中的 `related_claims` 等字段
可以继续兼容读取，但 Claim 不应成为新内容发布的必要操作。

发布清单本阶段优先覆盖博客草稿和现有公开资料，支持预览草稿、发布选中博客、构建已发布
内容和发布并构建。项目编辑不在本阶段新增。

### 6.3 视觉风格对齐

公开站点需要与当前已生成站点的视觉语言对齐，但不应机械复制后台深色界面。基准原则是：

- 保持现有站点的明亮、干净、可阅读观感，避免整体改成深色或高饱和主题。
- 保留当前站点的留白、浅色背景、清晰层级和内容优先布局。
- 公开构建页面的预览、状态和产物信息应服务于风格校验，不把后台卡片样式直接暴露为公开站点。
- 新增模板、博客详情和简历页面必须先以实际预览验证桌面和移动端的文字可读性、图片比例和链接状态。

### 6.4 网站预览与构建记录

预览页面包括首页、关于、项目、博客、简历和成果，支持单页预览、草稿预览、桌面尺寸
和移动端尺寸。预览不改变发布状态。

当前先复用现有构建结果和产物清单；构建历史和 `.nblane-build.json` manifest 属于后续增强，
不作为本阶段交付前置条件。

## 7. 技术方案

### 7.1 前端

React SPA 是新工作台的唯一主实现。建议拆分：

```text
src/nblane/web_ui/frontend/src/pages/ContentWorkspacePage.tsx
src/nblane/web_ui/frontend/src/pages/CareerWorkspacePage.tsx
src/nblane/web_ui/frontend/src/pages/PublicBuildPage.tsx
```

组件目录：

```text
src/nblane/web_ui/frontend/src/components/content/
src/nblane/web_ui/frontend/src/components/career/
src/nblane/web_ui/frontend/src/components/editor/
src/nblane/web_ui/frontend/src/components/public-build/
```

Streamlit Output Studio 只保留兼容和迁移提示，不再新增同类能力。

### 7.2 编辑器

继续使用当前 BlockNote 方向，不在本阶段迁移编辑器内核。将
`public_blog_editor_component` 中的 Markdown、BlockNote、媒体、公式、Mermaid、
AI patch 和校验能力抽取为独立 editor core，由 SPA 和 Streamlit wrapper 共用。

Markdown 仍是最终内容源，BlockNote JSON 仍是编辑状态缓存。

### 7.3 后端模块

避免继续扩大 `web_output_studio.py` 和 `public_site.py`，建议增加：

```text
src/nblane/core/content_workspace.py
src/nblane/core/career_workspace.py
src/nblane/core/resume_versions.py
src/nblane/core/public_build_manifest.py
```

所有写入继续通过集中 I/O、原子写、文件锁、Git backup 和冲突检查完成。

## 8. API 计划

### 内容工作台

```text
GET    /api/v1/profiles/{name}/content
POST   /api/v1/profiles/{name}/content/blog
GET    /api/v1/profiles/{name}/content/blog/{slug}
PUT    /api/v1/profiles/{name}/content/blog/{slug}
POST   /api/v1/profiles/{name}/content/blog/{slug}/check
POST   /api/v1/profiles/{name}/content/blog/{slug}/publish
POST   /api/v1/profiles/{name}/content/blog/{slug}/ai
```

### 求职工作台

```text
GET  /api/v1/profiles/{name}/career
GET  /api/v1/profiles/{name}/career/resume
PUT  /api/v1/profiles/{name}/career/resume
POST /api/v1/profiles/{name}/career/resume/upload
POST /api/v1/profiles/{name}/career/resume/parse
POST /api/v1/profiles/{name}/career/match
GET  /api/v1/profiles/{name}/career/match/{job_id}
GET  /api/v1/profiles/{name}/career/match/{job_id}/events
GET  /api/v1/profiles/{name}/career/versions
POST /api/v1/profiles/{name}/career/versions
GET  /api/v1/profiles/{name}/career/versions/{version_id}
PUT  /api/v1/profiles/{name}/career/versions/{version_id}
POST /api/v1/profiles/{name}/career/versions/{version_id}/regenerate
POST /api/v1/profiles/{name}/career/versions/{version_id}/export
```

JD 分析和简历生成继续复用 Job + SSE 基础设施。

### 公开站点

优先复用现有 Public Build API，在其上补充：

```text
GET /api/v1/profiles/{name}/public-build/history
GET /api/v1/profiles/{name}/public-build/history/{build_id}
```

## 9. 开发阶段

### Phase 0：边界与契约冻结

交付信息架构、路由、文件边界、状态枚举、API 草案、旧功能保留清单和数据流图。
必须确认：

```text
Content 不读取 Evidence / Claim
Career 不读取 Evidence / Claim
Public Build 不编辑 Content / Career
```

### Phase 1：React 路由与三模块壳

交付三个路由、统一页面状态、旧 `/studio` 重定向和新导航入口。

### Phase 2：博客编辑器

交付 SPA BlockNote、Markdown round-trip、sidecar 恢复、媒体、公式、Mermaid、AI patch、
文章属性、发布检查、保存发布和冲突恢复。

验收路径：

```text
新建文章 → 编辑 → 保存 → 刷新恢复 → 预览 → 检查 → 发布
```

### Phase 3：求职工作台最小闭环

交付简历输入/导入、JD 输入、匹配分析、定制简历草稿、人工编辑和导出。

### Phase 4：求职工作台完善

交付主简历编辑、PDF/DOCX/TXT 上传、提取预览、字段确认、保存目标选择和 Markdown/HTML
预览。

### Phase 5：JD 匹配和定制简历

交付 JD 输入、Job + SSE、结构化分析、定制简历草稿、人工确认、重新生成和
Markdown/HTML/PDF 导出；复杂独立版本目录暂缓。

### Phase 6：公开站点发布和构建

交付准备状态、博客发布清单、草稿预览、选择性发布、发布并构建和构建诊断；manifest 与历史暂缓。

### Phase 7：旧入口收敛与回归

交付 Streamlit 迁移提示、旧 API/旧数据兼容、文档更新以及单元、API 和 e2e 回归。

## 10. 测试计划

建议新增或扩展：

```text
tests/test_content_workspace.py
tests/test_career_workspace.py
tests/test_web_api_content_workspace.py
tests/test_web_api_career_workspace.py
tests/e2e/content-workspace.spec.ts
tests/e2e/career-workspace.spec.ts
tests/e2e/public-build-v2.spec.ts
```

必须覆盖：博客 CRUD、简历上传、解析失败、JD 任务、定制简历草稿、ETag
冲突、文件锁、路径安全、私有内容门禁和旧数据兼容。

最小端到端路径：

1. 创建并发布博客。
2. 上传简历、匹配 JD、保存定制简历草稿。
3. 选择博客内容、预览、发布并构建静态站。

## 11. 风险与处理

### 编辑器迁移导致能力丢失

不更换 BlockNote，只抽取 editor core；先为 Markdown round-trip、媒体、公式、Mermaid
和 AI patch 补回归测试，再替换页面入口。

### React 与 Streamlit 继续分叉

React SPA 作为新功能唯一实现；Streamlit 只保留兼容和迁移提示。

### 定制简历覆盖其他版本

先使用明确的目标岗位标识和覆盖确认；独立目录、manifest、source hash 和 JD hash 属于后续增强。

### 公开站点误发布私有内容

继续使用 visibility/status 闸门、构建前校验和 If-Match；构建 manifest 属于后续增强。

### 旧内容的 Claim 字段阻塞发布

旧字段兼容读取；新内容不要求 Claim；legacy provenance 问题应优先作为警告，不应要求
用户回到 Evidence 页面处理。

## 12. 最终验收标准

### 内容工作台

- 不进入 Evidence 页面也能创建博客。
- 不选择 Claim 也能保存和发布博客。
- 编辑器支持 Markdown、媒体、公式和代码。
- AI 结果可以查看 diff 并人工确认。
- 保存冲突不会覆盖用户内容。

### 求职工作台

- 可以上传 PDF、DOCX、TXT。
- 可以选择主简历或临时简历。
- 可以直接输入 JD。
- JD 匹配不依赖 Evidence / Claim。
- 可以生成结构化分析和定制简历。
- 定制简历草稿有明确目标岗位标识。
- 不会无提示覆盖主简历。
- 可以编辑并导出结果。

### 公开站点

- 清楚显示哪些内容可以发布。
- 私有内容和未选择草稿不会误发布。
- 可以预览草稿。
- 可以选择性发布并构建。
- 构建错误可定位。
- 构建结果有明确的产物清单和错误提示；manifest 属于后续增强。
- 不需要进入 Evidence 或 Claim 页面。

## 13. 下一步

实现前先确认 Phase 0 的三项决策：

1. 是否在现有入口稳定后采用 `/content`、`/career` 路由。
2. 博客编辑器在 SPA 中的最小可用范围。
3. 求职工作台最小闭环及定制简历草稿的保存格式。

确认后优先实施 Phase 1 和 Phase 2，先让内容工作台拥有真正可用的博客编辑器，再进入
项目、简历和 JD 匹配开发。
