# Public Site Blog 编辑器设计：BlockNote、可折叠布局与 AI 创作面板

本文是公开站 Blog 编辑器的产品 / 技术设计稿。Public Site 页面已落地 React /
BlockNote Editor Shell；Blog 区主路径覆盖文章筛选、新建草稿、从 evidence /
Done 生成、Meta、Media、AI、Visual、Check、Public Preview、专注模式、
Markdown 源码安全模式和 browser `localStorage` 布局记忆。本文继续作为后续
打磨边界：在保持 `profiles/<name>/blog/*.md` 为内容事实源的前提下，把块级
插入、选中块改写和更多视觉 provider adapter 做深。

## 1. 背景与目标

当前 `Public Site -> Blog` 已经能创建、编辑、预览、上传 / 插入媒体、生成 AI
候选、生成视觉素材候选和发布博客；React shell 已经承接主体写作界面，
Streamlit 继续承接文件 I/O、session state、AI / 视觉调用、上传落盘、发布校验、
静态预览和 Git backup。距离更完整的块编辑体验还有差距：

- front matter、媒体、AI 候选、Visual 候选、发布检查和 preview 已进入 shell，
  但块级定位仍偏简化。
- 媒体插入依赖 Markdown 片段和 `<!-- nblane:insert -->` fallback，不像块编辑器。
- 仍缺少正文块级操作、slash menu、拖拽、选中块改写、候选内容按光标/块插入等现代编辑体验。

下一版 React Blog Shell 的目标：

- 中心正文使用 BlockNote 一类 Notion-style block editor。
- 左侧文章库、右侧工具栏可折叠，写作时不抢空间。
- 右侧工具用 tabs / drawer 组织：Meta、Media、AI、Visual、Check。
- 小屏默认编辑器优先，不展示三栏并排。
- AI、图片、视频输出都以候选优先：不会自动发布、不会自动替换正文、不会自动设 cover。

## 2. 总体布局

Blog 页面长期形态应从当前 Streamlit shell 继续收敛为一个 React Editor Shell：

```text
┌──────────────────────────────────────────────────────────────┐
│ 顶部工具条：标题 / 状态 / 保存 / 公开预览 / 检查 / 发布       │
├──────────────┬──────────────────────────────┬────────────────┤
│ 左侧文章栏   │ BlockNote 正文编辑器          │ 右侧工具抽屉   │
│ 可折叠       │ 写作主区域 + Preview           │ Meta/Media/AI  │
│ 280-320px    │ 760-860px 阅读宽度            │ /Visual/Check  │
└──────────────┴──────────────────────────────┴────────────────┘
```

### 2.1 顶部工具条

顶部工具条保持轻量，始终可见：

- 左侧：文章标题、保存状态、当前 profile / slug。
- 中间：保存、预览、发布检查、发布。
- 右侧：切换左栏、切换右栏、专注模式、公开预览。

顶部工具条不放长表单，不承载 front matter 全量编辑。发布失败时，工具条只显示
紧凑错误状态，并自动打开右侧 **Check** tab。

### 2.2 左侧文章栏

左侧文章栏用于内容导航和草稿入口：

- 展开宽度：`280-320px`。
- 折叠宽度：`48px` 图标栏。
- 内容：
  - 状态筛选：全部 / draft / published / archived。
  - 文章列表：标题、状态、日期、是否有未保存修改。
  - 新建草稿。
  - 从 evidence 生成草稿。
  - 从 Done 生成草稿。

左侧不显示正文摘要，不放复杂长表单。新建草稿、从 evidence、从 Done 这些低频动作
使用弹出式小面板或短表单完成。

### 2.3 中间编辑区

中间区域是写作主场：

- 主体为 BlockNote 正文编辑器。
- 正文最大阅读宽度建议 `760-860px`，居中显示。
- 宽屏时正文不无限拉宽，避免长行影响阅读和写作判断。
- 标题可作为编辑器上方的大输入区，body 从标题下方开始。
- 在专注模式下隐藏左右 panel，只保留顶部工具条和正文。
- raw Markdown 放在高级折叠区，仅作为调试 / 高级入口。

### 2.4 右侧工具抽屉

右侧工具抽屉用于所有辅助编辑能力：

- 展开宽度：`360-420px`。
- 折叠宽度：`48px` 图标栏。
- 每次只展开一个 tab，避免多个工具纵向堆叠。

右侧 tabs：

| Tab | 内容边界 |
| --- | --- |
| Meta | `title`、`date`、`status`、`summary`、`tags`、`cover`、`related_evidence`、`related_kanban` |
| Media | 媒体库、上传图片 / 短视频、插入正文、设为封面、未引用媒体提示 |
| AI | 当前标题 / evidence id / Done 三种文字候选来源、候选正文、summary、tags、cover prompt、warnings |
| Visual | Flowchart、Cover、Example、Video edit；展示 provider、模型、key 来源；未配置时禁用生成 |
| Check | 发布前校验、公开页预览、Markdown 降级警告、隐私检查 |

## 3. 折叠与状态持久化

### 3.1 状态字段

编辑器需要记录以下 UI 状态：

```yaml
left_open: true
right_open: true
active_right_tab: Meta
focus_mode: false
preview_open: false
```

状态 key：

```text
public_blog_editor:<profile>:<slug>
```

首选由 React / BlockNote 自定义组件写入 browser `localStorage`。Streamlit 侧保留
`st.session_state` 作为本次会话 fallback。

### 3.2 默认状态

- 首次打开桌面宽屏：左栏展开，右栏展开。
- 如果有历史状态：恢复上次状态。
- 没有历史 tab 时：右侧默认打开 `Meta`。
- 重新打开文章：按 `public_blog_editor:<profile>:<slug>` 恢复状态。
- 点击专注模式：立即折叠左右栏；再次点击恢复进入专注模式前的左右栏状态。

### 3.3 抽屉交互

- 点击左侧图标栏的文章图标：展开 / 折叠左栏。
- 点击右侧图标栏的 Meta / Media / AI / Check 图标：切换 tab，并展开右栏。
- 右栏展开时再次点击当前 tab 图标：折叠右栏。
- 发布失败：自动展开右栏并切换到 `Check`。
- 插入媒体或 AI 候选后：保持当前 tab，不强制跳转，避免打断写作上下文。

## 4. 小屏策略

窗口宽度低于 `900px` 时，不展示三栏并排。默认只显示编辑器：

```text
┌──────────────────────────────┐
│ 顶部工具条                    │
├──────────────────────────────┤
│ BlockNote 编辑器              │
└──────────────────────────────┘
```

小屏交互：

- 左侧文章库通过按钮打开 overlay drawer。
- 右侧工具通过按钮打开 overlay drawer。
- 打开 drawer 后，正文背景弱化。
- 完成操作或点击遮罩后回到正文。
- 小屏支持轻量修改和预览，不追求完整桌面等价体验。

如果首版暂时无法实现 overlay drawer，可以降级为：

```text
Editor / Articles / Tools / Preview
```

四个顶层 tabs。默认停留在 `Editor`。

## 5. 写作体验优化

### 5.1 写作优先

- 编辑器默认聚焦正文，Meta 信息不抢首屏。
- 保存 / 发布状态放在顶部工具条，不插入正文。
- 发布检查不自动弹出；只有保存失败、校验失败、发布前才主动提示。
- raw Markdown 默认收起。

### 5.2 内容插入

媒体和 AI 候选内容插入优先级：

1. 当前 BlockNote 光标位置。
2. 当前选中块后方。
3. 正文末尾。
4. Markdown fallback：`<!-- nblane:insert -->` 标记。

`<!-- nblane:insert -->` 继续保留为兼容路径，但不作为主交互。

### 5.3 AI 创作面板

AI tab 中所有模型输出先进入候选区，不直接写入正文。

AI tab 支持按当前标题生成完整候选，候选内容包括正文、摘要、标签和封面
prompt。仅标题生成不被视为已核实事实，UI 需要明确提示用户在发布前补充 /
核对 evidence、链接、日期、指标和隐私边界。

候选区动作：

- 插入当前位置。
- 替换选中块。
- 追加到文末。
- 保存为备注。
- 丢弃。

图生成候选先进入媒体库，用户再选择插入正文或设为 cover。

### 5.4 Visual 面板

Visual tab 使用 `src/nblane/core/visual_generation.py` 的统一配置和 prompt builder。
配置 canonical 命名为 `VISUAL_*`，兼容读取旧式 `IMAGE_*` alias。默认 provider 为
`dashscope_wan`，默认图片模型 `wan2.7-image-pro`，默认视频编辑模型
`wan2.7-videoedit`。API key 读取顺序：

1. `VISUAL_API_KEY`
2. `DASHSCOPE_API_KEY`
3. `LLM_API_KEY`

千问 / DashScope 视觉生成默认复用现有 `LLM_API_KEY`；只有图像 / 视频和文本 LLM
使用不同凭据时才需要 `VISUAL_API_KEY`。视觉模块会复用 DashScope 域名信息，但不会
把 `/compatible-mode/v1` chat completions endpoint 当作视觉任务 endpoint。

Visual 面板资产类型：

- **Flowchart：** 主要服务“方框 + 流箭头”。Prompt 强约束 clean vector style、
  rectangular boxes、clear arrows、high contrast、no tiny text、no watermark。
- **Cover：** 使用 title、summary、tags、正文 gist 构造；不要求模型生成标题文字，
  标题由站点 HTML/CSS 叠加。
- **Example：** 用于事例图、系统示意、实验场景；涉及私密路径、人名、内部素材时
  自动泛化。
- **Video edit：** 仅用户明确选择时启用，默认模型 `wan2.7-videoedit`，输入视频 /
  参考图必须经过路径、大小、格式校验。

未配置 key 时 UI 显示缺少 `VISUAL_API_KEY / DASHSCOPE_API_KEY / LLM_API_KEY`，
Generate 按钮禁用；后端也会抛出清晰错误，不生成假图、不创建占位媒体、不把 prompt
伪装成成功结果。

### 5.5 发布检查

Check tab 展示：

- `validate_blog_text_for_publish` 的错误和警告。
- Markdown / BlockNote 转换降级提示。
- 公式安全提示：包含 `$...$`、`$$...$$`、`\(...\)` 或 `\[...\]` 时，
  自动使用 Markdown 源码编辑器，避免 BlockNote 的 lossy Markdown 往返改写公式。
- 缺失摘要、缺失 cover、空标签等内容质量提醒。
- 未引用媒体。
- 隐私提示：是否引用了不该公开的 raw 文件或私密文本。

发布按钮如果校验失败，自动打开右侧 Check tab 并定位错误。

## 6. 实现边界

下一轮优化建议把“编辑器 + 折叠布局状态”进一步收进一个 React / BlockNote
Streamlit 自定义组件：

- React 负责：
  - BlockNote 编辑器。
  - 左右 drawer 与移动端 `Editor / Articles / Tools / Preview` 顶层 tabs。
  - `localStorage` 状态。
  - 文章筛选、新建、evidence / Done 草稿入口、Media 上传表单、AI / Visual 表单。
  - 光标位置和当前 Markdown 草稿 payload。
  - 块级插入动作。
- Streamlit 负责：
  - 读取 / 写入 `blog/*.md`。
  - 解析 / 保存 front matter。
  - 公式安全模式与公开页 MathJax 渲染。
  - 文件上传落盘。
  - 调用 AI 与视觉 provider。
  - 发布校验与隐私阻断。
  - 当前草稿的 in-memory 公开预览。
  - Git backup。

组件输入：

```yaml
initial_markdown: string
layout_state:
  left_open: bool
  right_open: bool
  active_right_tab: Meta | Media | AI | Visual | Check
  focus_mode: bool
  preview_open: bool
active_post_meta: object
media_items: list # JSON-safe: name/kind/relative_path/size_kb/referenced
ai_candidates: list
visual_config: object
preview_html: string
status_filter: all | draft | published | archived
```

组件返回：

```yaml
markdown: string
layout_state: object
dirty: bool
selected_block: object | null
insert_event: object | null
```

主要 action：

```yaml
save_post
run_check
publish_request
select_post
filter_posts: {status: all | draft | published | archived}
create_post: {title: string}
draft_from_evidence: {evidence_id: string}
draft_from_done: {}
upload_media: {data_url: string, filename: string, kind: image | video, alt: string, caption: string, insert: bool, cover: bool}
generate_ai_candidate: {source: title | evidence | kanban_done, title?: string, evidence_id?: string}
generate_visual_asset: {asset_type: flowchart | cover | example | video_edit, prompt: string, style?: string, size?: string, alt?: string, caption?: string}
generate_cover_image: {prompt: string, style?: string, size?: string, alt?: string, caption?: string}
preview_post: {markdown: string, meta: object, layout_state: object, dirty: bool}
```

初版已经在 Streamlit 中覆盖了这些能力：

- 左栏显示 / 隐藏 toggle。
- 右栏 tab + 显示 / 隐藏 toggle。
- 专注模式 toggle。
- 公开预览与发布检查。

仍待 React Shell 继续补齐的是：

- 更细的光标位置与选中块感知。
- 块级插入、替换、拖拽与 slash menu。
- 更多 provider adapter，例如 OpenAI、local ComfyUI、custom HTTP。

## 7. 验收标准

设计稿验收：

- 明确桌面宽屏、窄屏、专注模式三种布局。
- 明确左侧文章栏、中心编辑器、右侧工具抽屉的默认宽度和折叠宽度。
- 明确右侧 `Meta` / `Media` / `AI` / `Visual` / `Check` 五个 tab 的内容边界。
- 明确状态持久化 key 和 fallback 策略。
- 明确小屏不展示三栏并排，而是编辑器优先 + overlay drawer。

后续实现验收：

- 用户折叠左栏、打开 AI tab、进入专注模式后，刷新页面能恢复合理状态。
- 窄屏下正文不会被左右栏挤压。
- AI 候选、媒体插入、front matter 修改都不打断正文编辑焦点。
- 发布失败会自动打开 Check tab 并定位错误。
- raw Markdown 仍可查看，但默认不占用主编辑区。

## 8. Assumptions

- Public Site / Blog 初版已实现；本文面向下一轮 React Blog Shell 与展示体验优化。
- 目标体验是接近 Notion 的写作空间，不是把所有 public site 管理功能都塞进同一个三栏屏幕。
- Blog 编辑器优先服务桌面写作；小屏支持轻量修改和预览。
- `blog/*.md` 继续是内容事实源。
- BlockNote / React layout state 只记录 UI 状态，不成为内容事实源。
