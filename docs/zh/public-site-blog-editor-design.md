# Public Site Blog 编辑器设计：BlockNote、可折叠布局与 AI 创作面板

本文是公开站 Blog 编辑器的产品 / 技术设计稿。目标是把当前
Streamlit 表单式 Markdown 编辑，升级为接近 Notion 的块编辑体验，同时继续
以 `profiles/<name>/blog/*.md` 作为内容事实源。

当前文档只定义交互与实现边界，不代表功能已经全部落地。

## 1. 背景与目标

当前 `Public Site -> Blog` 已经能创建、编辑、预览、插入媒体和发布博客，但
体验更像“结构化表单 + Markdown 文本框”：

- 左中右三列固定展开，编辑器横向空间被压缩。
- front matter、媒体、预览和发布检查混在右侧，写作时容易分心。
- 媒体插入依赖 Markdown 片段和 `<!-- nblane:insert -->` fallback，不像块编辑器。
- 缺少正文块级操作、slash menu、拖拽、选中块改写、候选内容插入等现代编辑体验。

下一版 Blog 编辑器的目标：

- 中心正文使用 BlockNote 一类 Notion-style block editor。
- 左侧文章库、右侧工具栏可折叠，写作时不抢空间。
- 右侧工具用 tabs / drawer 组织：Meta、Media、AI、Check。
- 小屏默认编辑器优先，不展示三栏并排。
- AI 只生成候选内容，用户确认后才写入正文或媒体库。

## 2. 总体布局

Blog 页面不再使用固定 `st.columns([0.8, 1.35, 1.1])` 作为长期形态，
而是设计为一个 Editor Shell：

```text
┌──────────────────────────────────────────────────────────────┐
│ 顶部工具条：标题 / 状态 / 保存 / 检查 / 发布 / 面板开关      │
├──────────────┬──────────────────────────────┬────────────────┤
│ 左侧文章栏   │ BlockNote 正文编辑器          │ 右侧工具抽屉   │
│ 可折叠       │ 写作主区域                    │ Meta/Media/AI  │
│ 280-320px    │ 760-860px 阅读宽度            │ /Check tabs    │
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
| AI | VLM 辅助写作、读图 / 读视频、生成配图 prompt、调用图生成模型、候选区 |
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

### 5.4 发布检查

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

最终实现建议把“编辑器 + 折叠布局状态”放进一个 React / BlockNote
Streamlit 自定义组件：

- React 负责：
  - BlockNote 编辑器。
  - 左右 drawer。
  - `localStorage` 状态。
  - 光标位置。
  - 块级插入动作。
- Streamlit 负责：
  - 读取 / 写入 `blog/*.md`。
  - 解析 / 保存 front matter。
  - 公式安全模式与公开页 MathJax 渲染。
  - 上传媒体。
  - 调用 AI。
  - 发布校验。
  - 构建公开预览。

组件输入：

```yaml
initial_markdown: string
layout_state:
  left_open: bool
  right_open: bool
  active_right_tab: Meta | Media | AI | Check
  focus_mode: bool
  preview_open: bool
active_post_meta: object
media_items: list
ai_candidates: list
```

组件返回：

```yaml
markdown: string
layout_state: object
dirty: bool
selected_block: object | null
insert_event: object | null
```

如果首版不做完整 React Shell，也至少要在 Streamlit 中实现：

- 左栏显示 / 隐藏 toggle。
- 右栏 tab + 显示 / 隐藏 toggle。
- 专注模式 toggle。
- 窄屏降级为 `Editor / Articles / Tools / Preview`。

## 7. 验收标准

设计稿验收：

- 明确桌面宽屏、窄屏、专注模式三种布局。
- 明确左侧文章栏、中心编辑器、右侧工具抽屉的默认宽度和折叠宽度。
- 明确右侧 `Meta` / `Media` / `AI` / `Check` 四个 tab 的内容边界。
- 明确状态持久化 key 和 fallback 策略。
- 明确小屏不展示三栏并排，而是编辑器优先 + overlay drawer。

后续实现验收：

- 用户折叠左栏、打开 AI tab、进入专注模式后，刷新页面能恢复合理状态。
- 窄屏下正文不会被左右栏挤压。
- AI 候选、媒体插入、front matter 修改都不打断正文编辑焦点。
- 发布失败会自动打开 Check tab 并定位错误。
- raw Markdown 仍可查看，但默认不占用主编辑区。

## 8. Assumptions

- 本文只定义设计，不代表已经实现。
- 目标体验是接近 Notion 的写作空间，不是把所有 public site 管理功能都塞进同一个三栏屏幕。
- Blog 编辑器优先服务桌面写作；小屏支持轻量修改和预览。
- `blog/*.md` 继续是内容事实源。
- BlockNote / React layout state 只记录 UI 状态，不成为内容事实源。
