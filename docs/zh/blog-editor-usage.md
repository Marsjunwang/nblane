# Blog 编辑器使用说明书

适用版本：Phase 4B 已完成（截至 2026-05-02）。覆盖 BlockNote 富文本编辑、内联 AI（slash + 选区浮层）、流式生成、候选审核、公式 / 配图 / 大纲 / Diagram 四大专项、AI Editor Reviewer，以及 markdown + `.blocknote.json` sidecar 双轨保存。

---

## 1. 启动与环境

```bash
# 后端 + UI
.venv/bin/streamlit run pages/6_Public_Site.py

# 前端组件改动后需重新构建
cd src/nblane/public_blog_editor_component/frontend
npm install   # 首次或依赖变动后
npm run build
```

打开浏览器访问 `http://127.0.0.1:8510`，左侧选择 Profile，进入 **Public Site** 页 → **Blog** Tab。

环境最低要求：
- Streamlit ≥ 1.31（`@st.fragment` 依赖）
- Node ≥ 20
- LLM 与 Visual 提供方按 [docs/setup.md](setup.md) 配置；缺失时 AI 入口仍可见，但触发时会在编辑器顶部红条提示具体缺失项。

---

## 2. 编辑器界面总览

```
┌────────────────────────────────────────────────────────────┐
│ 顶部 Tab：Blog 列表 / 编辑 / 媒体 / Check / 发布            │
├──────────────────────────────────┬─────────────────────────┤
│                                  │ 右侧侧栏：               │
│   BlockNote 编辑区（富文本）      │  - OutlinePanel          │
│   - 块级 / / 选区浮层             │  - CandidatePatchPanel   │
│   - 公式块 / 视觉块 / Mermaid     │  - 媒体库 / 元数据       │
│                                  │                          │
└──────────────────────────────────┴─────────────────────────┘
```

正文区与侧栏的 AI 入口共享同一套候选与流式管线；同一时刻只允许一条流式任务在编辑器内运行（取消按钮在 loading block 内）。

---

## 3. 五种 AI 入口

### 3.1 选区浮动菜单 (SelectionAIToolbar)

选中正文任意文字 → 浮层出现 9 项操作：

| 按钮 | operation | 适用场景 |
|---|---|---|
| 润色 | `polish` | 修语病、提流畅度，不改原意 |
| 改写 | `rewrite` | 同义换说法、调结构 |
| 缩短 | `shorten` | 压缩到约 60% 篇幅 |
| 扩写 | `expand` | 补论据、展开细节 |
| 续写 | `continue` | 在选区后补下一段 |
| 翻译 | `translate` | 默认中↔英 |
| 语气 | `tone` | 正式 / 轻松 / 营销等 |
| 转公式 | `formula` | 自然语言 → LaTeX `math_block` |
| 配图 | `visual` | 用选区做 caption → 生成插图 |

行为约定：选中文字会作为 `target.selection_text` 上报；polish/rewrite/shorten/expand/translate/tone 走 `replace`；continue 走 `insert after`；formula / visual 走 `insert after` 并在 CandidatePatchPanel 显示候选。

### 3.2 Slash 命令

在新行键入 `/` 触发自定义 SuggestionMenu，命中以下 6 条之一（含中英 alias）：

| 标签 | operation | aliases | 备注 |
|---|---|---|---|
| AI 续写 | `continue` | ai, write, next, continue, 写下一段, 续写 | 接当前块后 |
| 大纲 | `outline` | outline, scaffold, 大纲, 结构 | 调用 OutlinePanel 流程，需要先填标题 / 要点 |
| 公式 | `formula` | formula, latex, math, 公式 | 自然语言 → LaTeX |
| 配图 | `visual` | visual, image, picture, 图, 配图 | 生成图片候选 |
| Diagram | `visual` (kind=diagram) | diagram, mermaid, flowchart, 图表, 流程图 | 生成 Mermaid 文本 |
| 润色 | `polish` | polish, rewrite, 润色, 改写 | 当前块 |

prompt 解析规则：menu query 中**命中的 alias 前缀会被自动剥离**（`/公式 二次方程` → 实际 prompt = `二次方程`）；剥完为空时弹二级输入框补充描述。

### 3.3 OutlinePanel（右侧）

1. 填 `标题`、`要点 / 关键 evidence`、`目标读者`、`长度`
2. 点 **生成大纲** → 流式返回 `Block[]`，accept 后整篇替换为大纲骨架
3. 在大纲中将光标放在某个 heading → 点 **展开此节** → 仅扩写该 heading 子树（不动其他段落）

输入留白也能跑：未填字段会从 blog meta（title / summary / tags / related_evidence）兜底。

### 3.4 CandidatePatchPanel（右侧）

所有 AI 输出都会在右侧 panel 列一条候选卡片，包含：
- `operation` 与 `target.block_ids`
- 文本 diff（diff-match-patch 渲染）
- 若有 assets：缩略图（`preview_src`，小图直接 base64，大图走受控 endpoint）
- `accept` / `reject` / `regenerate` 三按钮

操作语义：
- **accept**：优先按 `block_patches[].op` 调 `editor.replaceBlocks / insertBlocks / removeBlocks`；仅 source-mode、legacy textarea、未知 block 类型 三种情况才降级 `markdown_fallback`。资产从 `.candidates/<patch_id>/` 晋升到 `media/blog/<slug>/`。
- **reject**：移除正文 candidate 卡片 + 清理临时文件（24h TTL 兜底 GC）。
- **regenerate**：用同一上下文重新触发，旧候选自动 reject。

### 3.5 Check Tab → AI Editor Reviewer

Check Tab 顶部仍是规则校验（必填项、tag、front matter 等），下方新增 **AI 审阅** 区块。reviewer 当前覆盖 7 类 finding：

| category | 触发 | 一键修复 |
|---|---|---|
| `weak_title` | 标题过短 / 重复字符 | 走 LLM 重写，写入 `meta_patch.title` |
| `missing_summary` | summary 为空 | 走 LLM 生成摘要 |
| `missing_tags` | tags 为空 | LLM 生成候选 tags |
| `missing_cover` | 无封面 | 提示走 `/visual` 生成封面 |
| `missing_alt_text` | 图片无 alt | 生成 alt 修复 patch |
| `unreferenced_media` | 媒体库有文件未在正文出现 | 提示删除 / 引用 |
| `privacy_path` | 正文出现 `profiles/.../...` 私域路径 | `[redacted internal reference]` 全文替换 |
| `leftover_insert_marker` | 残留 `<!-- nblane:insert -->` | 清除标记 |

每条 finding 旁的 **生成修复** 按钮会调 `repair_patch_for_finding`，结果走标准 CandidatePatchPanel 审核流；不会绕开 patch 模型。

---

## 4. AI 候选生命周期

```
触发 (slash / toolbar / OutlinePanel / Reviewer)
   │
   ▼
[正文] 出现 ai_loading_block
        ├─ formula  → 实时 KaTeX 容错预览
        ├─ visual   → 灰卡 + 进度条
        └─ text类   → 流式文本
   │
   ▼ (流式完成 onComplete)
[正文] loading_block 切换为 status=candidate（带缩略图，不消失）
[侧栏] CandidatePatchPanel 同步出现候选
   │
   ├── accept  → block_patches 应用；正文卡片替换为正式 block；资产晋升 media/
   └── reject  → 正文卡片消失；候选文件清理
```

期间整页**不会** rerun（`_render_blog_react_shell_fragment` 用 `@st.fragment` 包裹），其他段落、其他 Tab 的状态都保留。`/visual` 等长任务的 poll 间隔从 800ms 自动降到 1500ms 以减压。

---

## 5. 四大专项操作手册

### 5.1 公式（formula）

入口：选中文字 → 转公式；或 `/公式 <自然语言>`；或 `/公式` 直接选中弹输入框。

行为：
1. 流式 token 在正文 loading block 用 KaTeX 容错渲染，即便 LaTeX 暂不完整也不会显示 raw `\frac` 字符。
2. 完成后正文位置变成 candidate 卡片，CandidatePatchPanel 给出 LaTeX diff。
3. accept → 插入 `math_block` + `ai_generated` 徽章；KaTeX 正式渲染。

### 5.2 智能配图（visual）

入口：选中段落 → Visual；或 `/配图 <提示>`。

执行链：
1. caption 由 `from_caption_intent` 推导；可在 prompt 中显式给出。
2. visual 生成结果写入 `profiles/<name>/blog/.candidates/<patch_id>/<filename>`（**未** 写入 `media/blog/`，避免 reject 后污染媒体库）。
3. `assets[].preview_src` 双轨：< 2MB 直接 `data:image/png;base64,...`；超阈值 / 视频走 `/blog_candidate_preview/<patch_id>/<filename>` 受控 endpoint（仅校验当前 active session 可读）。
4. accept → 文件晋升到 `media/blog/<slug>/`；`visual_block.src` 填正式相对路径，`preview_src` 清空。

注意：reject 后立刻清理；24h 后未决候选由 TTL GC 兜底删。

### 5.3 文档架构生成（outline / expand_section）

入口：右侧 OutlinePanel；或 `/大纲`。

要点：
- `outline` 输出整套 `Block[]`，accept 后整篇替换。建议在新建 blog / 重构时使用。
- `expand_section_blocks` 仅展开当前 heading 子树，不动兄弟节点 — 想扩展某节时把光标放进该 heading 再点 **展开此节**。

### 5.4 Diagram（mermaid）

入口：`/diagram <场景描述>`。

发布渲染策略：
- **编辑器内**：`MermaidRenderer.jsx` 直接渲染。
- **公开站点**：保存时由 [public_site.py](../src/nblane/core/public_site.py) 调 mermaid 子进程**预渲染 SVG** 并内联到生成的 HTML，公开页面**不依赖外部 mermaid runtime**。预渲染失败兜底 `<pre class="mermaid">` + 受控 CDN runtime。

支持的 `visual_kind`（统一命名空间）：`flowchart / sequence / state / class / mindmap / example / video_edit`。

---

## 6. 保存与版本机制

每次保存会同时写两份：

| 文件 | 角色 | 何时优先 |
|---|---|---|
| `profiles/<name>/blog/<slug>.md` | 公开发布事实源、git diff 友好 | 公开站点构建用此 |
| `profiles/<name>/blog/<slug>.blocknote.json` | session canonical 编辑模型 | 加载时优先（带 `source_md_sha256` 校验） |

约束：
- 写顺序 **先 sidecar 再 md**，并 `fsync` 保证 sidecar 不会比 md 旧。
- 加载时若 sidecar 与 md 内容不一致（外部编辑器改了 md），以 **sidecar** 为准；md 会被 sidecar 还原后重写。
- 删除 md 后只要 sidecar 还在，下次保存可整篇还原。
- 外部编辑器（Typora / Obsidian / GitHub Web）请避免直接改正文 → 它们会吞掉 HTML 注释 round-trip 标记；如果非改不可，建议同步删除 sidecar 让其从 md 重建。

---

## 7. 常见问题

**Q1: 触发 AI 后正文位置一直转圈，右侧也没候选？**
A: 看顶部红条错误。常见原因：① LLM key 缺失；② Visual provider 未配置；③ prompt 为空（slash 直接选中未输入也会卡）。也可以 `Ctrl/Cmd+.` 取消当前流。

**Q2: accept 之后整篇全闪了一下？**
A: 不应该。如果出现是 `block_patches` 走了 `markdown_fallback` 降级。检查 React DevTools，应该只有被选中的 block 节点更新。请汇报到 `tests/test_ai_blog_phase3.py` 模式作为回归用例。

**Q3: 候选缩略图不显示？**
A: 确认 [pages/6_Public_Site.py:1495](../pages/6_Public_Site.py) `_candidate_preview_src_for_patch` 给 `assets[].preview_src` 填了值。小图未填→ 落盘失败；大图未填 → endpoint 路由没注册或 patch_id 不属当前 session。

**Q4: Mermaid 公开站点不显示？**
A: 公开站点用预渲染 SVG，不依赖外部 mermaid runtime。如果空白：① 看构建日志 `mermaid-cli` 是否安装；② 检查 `_render_visual_block_comment` 是否走到 SVG 分支；③ 兜底分支若启用 CDN，需要公开页 layout 注入了 mermaid runtime。

**Q5: 删除 md 后 blog 列表还有？**
A: 这是 sidecar 兜底机制 — 下次保存会从 sidecar 重建 md。要彻底删除 blog，需要同时删 `<slug>.md` 与 `<slug>.blocknote.json`。

**Q6: 想批量跑 AI 修复怎么办？**
A: 当前 Reviewer 是逐条修复，每个修复都进 CandidatePatchPanel 等审核。Phase 5 之后会把 Reviewer 升级为可批选 + 一次性 patch bundle，但当前阶段刻意保留逐条审核以避免误修。

---

## 8. 自动化与回归

```bash
# Python 单元测试
.venv/bin/pytest tests/test_ai_blog_phase3.py tests/test_ai_blog_phase4.py \
                  tests/test_visual_candidate_store.py tests/test_public_site.py

# 前端单测
cd src/nblane/public_blog_editor_component/frontend && npm test

# 浏览器 e2e（需先 streamlit 起在 8510）
cd src/nblane/public_blog_editor_component/frontend && npm run e2e

# 前端 bundle 检查
npm run build   # 主 chunk 应 < 1.0 MB
```

手工浏览器 7 场景（Phase 3.5 验收清单，作为回归 smoke）：

1. 选段 → polish → CandidatePatchPanel → accept → React DevTools 确认仅替换该 block
2. `/公式` 直接选 → 弹二级输入框 → 输入"二次方程" → 流式 KaTeX 容错预览 → accept → math_block 插入
3. 选段 → Visual → 候选 → reject → `media/blog/<slug>/` 不变；`.candidates/` 已清
4. 选段 → Visual → 候选 → accept → 文件晋升 + `visual_block.src` 正确
5. `/diagram 用户登录` → mermaid 流 → accept → 编辑器渲染 + public site SVG（不依赖外部 runtime）
6. `/visual` 长任务期间，整页不白屏，其他段可继续编辑
7. `/visual` 完成时 → 正文位置变 "候选已生成" 卡片（带缩略图，不消失）→ CandidatePatchPanel 同步缩略图 → accept 后正文卡片变 visual_block；reject 后正文卡片消失

---

## 9. 关键源码索引

| 关注点 | 文件 |
|---|---|
| 编辑器主入口 / 事件分发 | [main.jsx](../src/nblane/public_blog_editor_component/frontend/src/main.jsx) |
| 自定义块定义（含 ai_loading_block / math_block / visual_block） | [blogBlocks.jsx](../src/nblane/public_blog_editor_component/frontend/src/blocks/blogBlocks.jsx) |
| md round-trip | [markdown.js](../src/nblane/public_blog_editor_component/frontend/src/blocks/markdown.js) |
| 选区浮层 / slash / 候选 / 大纲 / 流式 hook | [frontend/src/ai/](../src/nblane/public_blog_editor_component/frontend/src/ai/) |
| AI 路由 / patch 拼装 | [ai_dispatcher.py](../src/nblane/core/ai_dispatcher.py) |
| 大纲生成 | [ai_blog_outline.py](../src/nblane/core/ai_blog_outline.py) |
| 视觉候选 lifecycle | [visual_candidate_store.py](../src/nblane/core/visual_candidate_store.py) |
| AI Editor Reviewer | [ai_blog_reviewer.py](../src/nblane/core/ai_blog_reviewer.py) |
| Patch / Block / Event schema | [schemas/ai_patch.py](../schemas/ai_patch.py) · [schemas/blocknote_doc.py](../schemas/blocknote_doc.py) · [schemas/editor_events.py](../schemas/editor_events.py) |
| 中英 prompt 双集（19×2） | [ai_blog_prompts/](../src/nblane/core/ai_blog_prompts/) |
| Blog 业务逻辑 / sidecar 双写 / 发布 | [public_site.py](../src/nblane/core/public_site.py) |
| UI 编排 / Check Tab / Reviewer 接入 | [pages/6_Public_Site.py](../pages/6_Public_Site.py) |
