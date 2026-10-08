---
status: draft
owner: product
last_verified: 2026-10-08
source_of_truth: true
---

# Paper Reading Studio 开发文档

本文定义 Research Workspace 中论文阅读能力的产品目标、页面组织、数据契约、
AI 行为、第三方库选择、后端抽取策略和测试计划。它是后续实现
`Paper Reading Studio` 的开发交接文档。

## 1. 目标

Research 论文阅读先形成一个独立、可回溯的阅读闭环：

```text
论文导入
  -> PDF 私有保存
  -> 页面与结构化抽取
  -> 中文摘要 / 论文导读
  -> 逐段阅读或原文对照
  -> 翻译、解释、笔记、引用
  -> 阅读材料整理
```

本阶段的产品边界是“读懂论文并留下可回到原文的研究材料”。论文阅读暂时不进入
能力证据闭环：不创建 Claim，不创建 Evidence，不修改 skill status，也不提供
`Promote to Evidence` 入口。

核心原则：

- `Paper Source` 说明读了什么。
- `Annotation / Note` 说明用户记下了什么。
- `Chunk / Citation` 说明哪里可以回到原文或用于引用。
- 翻译、摘要、AI 导读都必须绑定 source、segment、页码或 locator。
- AI 导读只产生待核对的阅读材料；用户确认后才保存为笔记或引用材料。
- 论文阅读材料不是项目成果证明，也不自动改变目标、项目或技能状态。
- PDF 原件不进 Git；批注、翻译、摘要、分析、引用和阅读状态进 profile，便于迁移。
- Reader 复用现有 PDF.js、GROBID、PyMuPDF、AI Gateway 和文件优先存储，不引入数据库。

## 1.1 原文—译文对照实施约束（2026-10-02）

当前 Reader 曾把“已有旧段落翻译”作为选择阅读结构的依据，导致旧 GROBID
segment 覆盖带 PDF 坐标的新结构；无页码 segment 又被临时放入第一页。结果是摘要
缺失、附录标题和表格误入第一页、原文翻页后译文仍停留在旧页。对照栏的滚动锁还
依赖左右页面的滚动比例，而流式中文与 PDF 原文高度不同，无法稳定对应。

本轮实施按下列顺序收束：

1. **完整解析**：GROBID TEI 转换同时读取标题、摘要和正文；解析质量明确区分
   `ready` 与 `incomplete`。只有完整结构允许发起全文翻译。
2. **唯一结构投影**：`paper-structure` 是 Reader 阅读顺序、页码、坐标和翻译单元的
   唯一事实源。旧 segment 可以保留用于兼容和诊断，但不能覆盖当前结构。
3. **旧译文安全复用**：通过相同 source hash 或唯一的规范化全文匹配，把旧 segment
   译文只读映射到当前结构；无法唯一匹配的译文不进入正常阅读流，也不修改旧数据。
4. **移除伪页码**：未知页码内容不再作为第一页展示。正常逐页阅读流中的可翻译单元
   必须有真实页码、稳定顺序和原文坐标。
5. **按页译文**：对照模式只呈现当前页附近内容；仅译文模式保持全文连续阅读，但按
   `page -> order` 分页，不跨页合并同名章节或统一 `Captions` 大桶。
6. **段落锚点同步**：滚动锁改成 `structure_unit_id + PDF rects` 驱动的语义同步。
   原文滚动时，将视口参考线处的原文段落与同 ID 译文对齐；译文点击或滚动可以反向
   定位原文。滚动比例只允许作为同一页内部、缺少段落锚点时的降级。
7. **对应关系可见**：当前原文矩形和译文卡使用同色高亮，并显示页码和页内段落序号；
   右栏页头显示当前页，不再用“页 1-15”掩盖当前对应关系。
8. **闭环验收**：浏览器测试覆盖摘要进入翻译流、第三页双向跟随、长短译文不累积
   漂移、无坐标旧内容不进入第一页，以及翻译缓存映射后的刷新和重开恢复。

现有 profile 论文文件不批量重写。兼容通过读取投影完成；版本过期的本地派生解析结果
在打开 Reader 时按需升级，手动重试仍可显式触发。BabelDOC / PDFMathTranslate 的版式保持双语 PDF 可作为后续可选能力，
本轮不直接引入其 AGPL 代码或替换现有 PDF.js Reader。

### 1.1.1 实施结果与验收记录

上述约束已于 2026-10-02 落入 Reader 主链路：

- GROBID TEI 抽取覆盖标题、Abstract 与正文；全文翻译会检查 canonical structure
  的页码、稳定 ID 和 PDF 坐标，结构不完整时拒绝启动。
- `paper-structure` 已升级到 `v6`。打开旧论文时只按需重建派生结构缓存，不批量
  改写 PDF、旧 segment、翻译、笔记或批注。
- 结构生成使用 GROBID 的标题、caption 和章节边界作为语义提示，同时保留
  PyMuPDF 的页码与矩形。已修复 Figure caption 吞正文、章节标题被误判为表格、
  `Encoder:` / `Decoder:` 与首行顺序颠倒，以及短尾词被拆成独立段落的问题。
- Reader 始终投影 canonical structure；旧译文只有在 source hash 相同，或双方均
  唯一的规范化全文精确匹配时复用。未知页码的旧内容不会进入第一页。
- 研究台和 SPA Reader 顶部的翻译进度也按 canonical structure 计算，不能再用旧
  segment 数量显示“已全部翻译”，而页内仍存在缺失或 stale 单元。
- 对照模式采用按页流式译文。译文卡包含页码与页内序号；“跟随原文”通过
  `structure_unit_id + rects` 双向同步，页面比例只在缺少锚点时降级使用。
- 默认翻译布局为 `flow`；`overlay` 仍可通过显式环境配置启用，供版式译文实验使用。

### 1.1.2 下一待办：把快速分析收束到论文概览页

这是接下来第一个产品待办，目标是消除“阅读器”和“阅读前判断”混在同一排工具栏造成的认知负担。

- **论文概览页**是单篇论文的起始页，负责标题、作者、Abstract、摘要翻译、PDF 状态、快速分析结果和继续阅读入口；它不是全局 Home，也不是研究台列表页。
- “分析论文”改名为“快速分析”，主要回答“这篇论文做了什么、是否值得继续读”，结果在论文概览页直接展示，并可从 Reader 的 Review 面板查看。
- 快速分析结果包括 TL;DR、关键贡献、方法概览、实验概览、局限、评分、项目相关性和阅读建议；结果必须保留 page/segment 引用，能够跳回 PDF。
- Reader 顶部移除“分析论文”主按钮，保留“全文翻译”和阅读相关操作；Reader 内仍可在 Review 面板查看已有快速分析。
- “深读”改名为“深度研读”。论文概览页和 Reader Review 面板都可以启动它；Reader 顶部不再把深度研读作为与 PDF、对照、翻译同级的主要阅读控制。
- “保存进度”改名为“保存位置”。它只保存页码、阅读模式、缩放、面板布局、当前翻译锚点和最近可见页，不保存翻译、分析、深读、笔记或标注内容。页码和阅读布局应以自动保存为主，手动按钮用于明确记录当前阅读位置。
- 快速分析与深度研读共用论文分析文件但不重复渲染同一份 TL;DR。概览页按“快速判断 → 打开 Reader → 深度研读”组织，Reader 按“阅读 → 标注/笔记 → Review”组织。

验收条件：

1. 从 Paper Library 或 Research 进入论文时先看到论文概览，而不是直接面对一排 AI 操作按钮。
2. 快速分析完成后，概览页能直接展示结果；没有结果时显示未开始或待生成状态。
3. Reader Review 能查看已有快速分析，并能启动深度研读；顶部不再显示“分析论文”。
4. Reader 的“保存位置”恢复上次页码和阅读模式，但不会被误认为保存了翻译或 AI 结果。
5. 快速分析和深度研读的结果可以共存，页面能明确显示生成时间、覆盖范围和状态。

实施状态（2026-10-06，已完成）：SPA 新增论文概览页 `/p/<name>/research/papers/<id>`，Reader 下沉到
`.../read`（旧的 `?mode=` 深链自动重定向）。概览页展示摘要与译文、PDF/翻译/阅读进度、最近笔记，
快速分析与深度研读以铭文卡呈现，引用 chip 跳到 `/read?page=N`；两者通过 SPA 任务
`paper-quick-analysis` / `paper-deep-read` 启动，刷新页面可重新接上进行中的任务。Reader 顶栏的
AI 动作收进「AI 研读」菜单，Review 面板可启动并显示生成时间与覆盖范围。模型失败退回 `rule_fallback`
时不再覆盖已有快速分析（`core/reader_actions.py` 统一守护，Reader 与概览页两条入口一致）。

实施状态（2026-10-08，全文阅读）：快速分析和深度研读都改为读整篇论文，不再按章节抽样或分批综合。
`core/paper_markdown.py` 把已抽取段落按阅读顺序拼成 Markdown，段尾带〔sN〕短锚点并保存锚点到段落 ID 的映射；
GROBID 单独输出的「Table N :」标签并回表题，参考文献集中放在文末。导出同时裁出表格/图，并整页渲染公式页和
没有裁图的表格页，按 PDF 指纹 + 段落摘要缓存在研究资产目录 `paper-markdown/`。快速分析只发文本；深度研读一次
Codex 调用，带上 Markdown、最多 24 张图（`codex exec --image`）、活跃项目和论文库里已分析论文的摘要。深度研读
产出 v2 精读笔记（verdict / setting / method{components, equations, training} / experiments{tables} / claims /
reproduction / sections / terms / relevance / next），保存时 `schema_version: "2"` 并直接覆盖旧结果；Codex 失败时
不写入。旧的 v1 结果仍按原字段展示。深度研读的术语表同时用于阅读器查词，优先于本地词典。

### 1.1.3 第二待办：修复 PDF 清晰度与降级渲染可见性

当前验收发现，PDF 原件是带文本层的矢量 PDF，但 Reader 的部分页面仍停留在
`pr-canvas pending-fallback` 与 `pr-page-preview visible` 状态，实际显示的是 PyMuPDF
生成的 PNG 页面预览。预览接口当前使用 `max_width=1100`，整页显示时基本可读，放大或
截图后会出现文字变软，因此需要把“原始 PDF.js 渲染”和“页面预览降级”分开验收。

- 先记录 PDF.js `getDocument`、`page.render`、worker、Range 请求和超时的真实错误，不能只显示 `Fallback text ready`。
- 正常 PDF 优先使用 PDF.js canvas；成功后必须移除 `pending-fallback`，隐藏预览图片，并在页面状态中标记为原始 PDF 渲染。
- 只有 PDF.js 明确失败、超时或 PDF 没有可用渲染能力时才使用 PNG fallback；fallback 要显示“页面预览降级”状态。
- fallback 预览不再固定为 1100 像素，按当前阅读宽度和设备像素比生成，至少覆盖 1.5 倍放大；不改变 PDF 原件和文件存储。
- 验收时同时检查 canvas 像素尺寸、CSS 显示尺寸、`devicePixelRatio`、页面状态和实际截图；在适应宽度、1:1、1.5x/2x 放大下文字都应保持可读。
- 如果 PDF.js 仍无法渲染，再单独处理 sidecar 的 PDF 认证/Range/worker 问题，不能把提高 PNG 尺寸当成根本修复。

验收条件：

1. 带文本层的普通 PDF 页面最终状态为 PDF.js canvas，`pending-fallback` 不存在。
2. PDF.js 失败时页面明确显示降级原因和重试入口，不能静默使用低分辨率图片。
3. 1.5x/2x 放大时文字边缘不会因为 1100 像素预览而明显模糊。
4. 文本层、段落定位、翻译高亮和 PDF canvas 使用同一页面尺寸，不因提高分辨率产生偏移。

实施状态（2026-10-06，已完成）：每个页面容器带 `data-render-source="pdfjs|preview"`；PDF.js
成功后移除 `pending-fallback` 并隐藏预览图。降级页右上角显示「图片预览降级」徽标，悬停可见
失败原因，PDF 文档可用时附「重试」。预览宽度改为按当前页宽 × `devicePixelRatio` × 1.5 请求
（接口 `page-preview/{page}?max_width=` 限制在 800–2200）。页面缓存位图改为空闲时编码为 WebP，
不再阻塞渲染主路径；远离视口的页面调用 `page.cleanup()`，重新加载时 `pdfDoc.destroy()`。

### 1.1.4 第三待办：统一双击翻译语义并降低原文高亮遮挡

当前 PDF text layer 同时存在两套双击路径：纯 PDF 模式会保留浏览器双击选词并触发单词快速翻译；
对照/仅译文模式的 `dblclick` 又会按坐标直接命中结构化段落并打开段落翻译。两条路径可能先后触发，
造成单词气泡与段落气泡互相覆盖，也让用户无法预测同一个双击动作的结果。

统一交互规则：

- **单击正文段落**：打开该段落的翻译气泡；已有缓存时直接显示，没有缓存时显示“翻译此段”。
- **双击英文单词**：保留浏览器原生选词，并显示单词词典释义或本地快速翻译；不再因阅读模式不同而改成整段翻译。
- **拖选句子或多词**：显示选区工具条，由用户点击“翻译选区”；不会自动把一个词的译文套到整段。
- **点击翻译流中的段落卡片**：定位 PDF 对应矩形并打开段落翻译气泡。
- **Esc**：关闭当前气泡和选区工具条。

同一待办同时修复当前定位框的视觉遮挡：截图中的绿色实心填充覆盖了过多原文字形，
不适合长段落阅读。新的视觉规则是：

- 当前段落以细金色/青绿色边框和极低透明度底色表示，正文保持清晰可读。
- 普通 hover 只显示边框，不改变大面积背景。
- 锁定的当前锚点可以增加外圈或左侧短标记，不继续提高填充不透明度。
- 翻译卡和 PDF 原文使用同一锚点颜色，但不使用相同的实心遮罩；焦点状态必须能在浅色 PDF 上辨认，也不能依赖颜色 alone。
- 选区高亮与段落定位高亮分开：选区用于用户操作，段落框用于同步定位，不能互相覆盖。

实现时需要处理双击的两次 `mouseup`、段落单击延迟确认和选区状态清理，避免出现“先显示单词、
再被段落翻译覆盖”的闪烁。段落框验收需要同时检查原文可读性、键盘焦点、缩放和对照滚动同步。

验收条件：

1. 所有阅读模式下，单击段落、双击单词、拖选句子的语义一致。
2. 双击一个英文单词只显示单词翻译；不会打开整段翻译，也不会产生两次翻译请求。
3. 拖选长句后不会复用单词译文，选区工具条只对当前精确文本生效。
4. 当前段落边框可见但不压住原文；长段落、深色文字和参考文献仍然清晰。
5. 段落定位、选区高亮、译文卡高亮三者状态可区分，并能在 1:1、适应宽度和放大模式下保持一致。

实施状态（2026-10-06，已完成）：

- 单击段落在 PDF / 对照 / 仅译文三种模式下都打开段落翻译（此前 PDF 模式不响应）；双击单词
  走本地词典/缓存，不再被段落单击的抑制窗口吞掉（此前 240ms 检查落在 420ms 抑制窗口内，
  双击单词实际从不翻译）；拖选只出现选区工具条。
- 段落定位框改为泥金细边框 + 5%–9% 透明底色，绿色只保留给成功语义。

### 1.1.5 Reader 基础阅读能力补齐（2026-10-06）

对照 Zotero 7 / Semantic Reader 补齐的基本功，全部在 sidecar Reader 内实现：

- **全文搜索**：`Ctrl/Cmd+F` 或 `/` 打开搜索栏，逐页扫描 PDF 文本层，页面上高亮全部命中、
  当前命中加框；Enter / Shift+Enter（或 F3）跳下一处 / 上一处，显示「第 n / N 处」和扫描进度；
  目录与中文译文命中单列。
- **可点击链接**：渲染 PDF.js 的 Link 注释。外部链接新标签打开（只放行 http/https/mailto）；
  内部链接（参考文献、图表、章节）点击跳转到目标坐标并短暂标出落点，悬停 320ms 显示目标区域
  的裁剪预览卡，命中 GROBID 参考文献时附标题、作者和检索链接。
- **跳转返回**：内部跳转前记录位置，左下角「← 返回第 N 页」胶囊或 `Alt+←` 返回。
- **顶栏重组**：单行布局——标题 + 解析状态｜翻页 + 缩放下拉（适应宽度 / 适应页面 / 1:1 / 当前百分比）
  ｜阅读模式分段控件（「跟随原文」只在对照模式出现）｜全文翻译 + 「AI 研读」菜单（快速分析、深度研读、
  提问）+「更多」菜单（保存位置、全屏、面板、快捷键）。`Ctrl/Cmd+滚轮` 缩放，`?` 打开快捷键说明。
- **Review 面板**：顶部固定「快速分析 / 深度研读」两行，显示生成时间、引用覆盖数与「开始 / 重新生成」。
- **任务状态**：SSE 为主通道、轮询只在 SSE 出错或 8 秒无首帧时接管，二者不再并行；同一任务的完成
  只处理一次；轮询遇网络错误按退避重试 5 次再报错。
- **视觉**：界面元素统一使用 SPA `theme.ts` 的靛蓝 / 泥金 / 月白色板，只有 PDF 页面和译文卡保留纸色；
  可见文案全部走 `_reader_ui` 中英词典。
- 阅读位置在 `pagehide` / `visibilitychange` 时也会上报，覆盖移动端 Safari 不触发 `beforeunload` 的情况。

翻译入口按作用域分开，避免研究台、Reader 和右侧面板重复执行同一件事：

- Reader 工具栏的“全文翻译”处理整篇 canonical structure 的缺失或过期单元，适合
  后台批量完成；它会切换到仅译文模式并显示整体进度。
- Reader 右侧翻译面板只保留四类状态计数、实际生成后端和“翻译当前可见页”入口。
  后者只处理当前 PDF 视口内的页，适合先读先译；段落队列和无范围的全局重试不再在
  右侧重复出现。
- 中间翻译阅读流是逐段操作的唯一位置。缺失、过期或失败的段落在原文对应卡片上
  执行“翻译”或“重新翻译此段”，并可点击卡片回到 PDF 锚点。
- “隐藏原文”不再作为右侧全局按钮。对照模式的原文始终是左侧 PDF；仅译文模式的
  源文摘录是否显示属于阅读布局设置，不作为批量翻译操作。

翻译后端边界保持明确：

- 选区翻译先走缓存和本地词典，命中即返回；未命中时调用论文翻译 action。
- 在配置了 CPU OPUS-MT/Marian 模型时，论文翻译 action 默认选择本地翻译后端，
  全文、可见页和段落翻译使用同一后端契约，但作用域不同。
- 未配置本地模型或用户在 AI 设置中指定 `direct_llm` 时，论文翻译 action 调用
  OpenAI-compatible LLM；这条路径适合需要上下文和更高质量的整段翻译，代价是延迟
  和网络/额度依赖更高。
- Reader 面板显示已保存译文的生成来源（本地 CPU、AI 模型或缓存/词典），避免把
  “全文翻译”误解成本地模型和远程模型的两个独立数据系统。

自动化验收覆盖：

- GROBID 标题与 Abstract 进入结构；
- caption 与后续正文保持独立；
- 同基线标签和正文恢复正确阅读顺序；
- 第 1 页 Abstract、第 3 页段落双向定位、第 4 页按页跟随；
- 旧译文安全复用与未知页码隔离；
- 翻译缓存刷新、Reader 重开和 PDF 矩形高亮。

真实论文《Attention Is All You Need》的端口验收结果：canonical structure 包含
169 个可翻译单元，全部具有 PDF 定位矩形，结构质量检查无 blocker；第 3 页的
Figure 1、Model Architecture、Encoder and Decoder Stacks、Attention 已恢复为可辨识的
图题、正文和章节结构。

论文阅读的三种能力不是三个同级页面：

```text
论文概览 / AI 导读
        -> 逐段阅读
        <-> 原文对照
```

- **论文概览 / AI 导读**：回答“这篇论文做了什么，是否值得继续读”。
- **逐段阅读**：回答“这一段英文具体是什么意思”。
- **原文对照**：回答“中文和原文如何对应，译文是否需要核对”。

笔记、局部解释和引用操作贯穿三者；Claim 和 Evidence 暂不显示。

## 2. 产品形态

Research 顶层仍是一个页面，不新增顶层导航。内部改成类似内容工作台的
小页面结构：

```text
Research
  Overview
  Paper Library
    Find / Import Papers
    Collections
    Work Queue
  Reader
  Reading Materials
  Synthesis / Export
  Inbox & Connectors
```

### 2.1 Overview

研究台首页首先回答“现在该读什么、上次读到哪里、下一步是什么”，而不是重复完整
Paper Library。建议分成三个区域：

```text
继续阅读
待处理队列
论文库入口
```

研究台需要展示：

- 最近阅读论文和上次页码；
- 缺 PDF 的论文；
- 翻译未完成或已经 stale 的论文；
- 尚未生成论文导读的论文；
- 有笔记但还没有整理的论文；
- 最近完成或归档的论文。

论文卡片的状态分开显示，不用一个 `status` 代表所有事实：

```text
Reading · PDF ready
Translation 42 / 119
AI guide ready
Notes 6 · Citations 3
Last read: p. 5
```

推荐的状态维度：

| 维度 | 示例 |
| --- | --- |
| 来源状态 | `inbox` / `reading` / `archived` |
| PDF 状态 | `missing` / `ready` / `failed` |
| 抽取状态 | `pending` / `ready` / `fallback` / `failed` |
| 翻译状态 | `not_started` / `partial` / `translated` / `stale` |
| 导读状态 | `not_started` / `running` / `ready` / `needs_review` / `failed` |
| 阅读状态 | `unread` / `reading` / `annotated` / `organized` |

主动作根据状态变化：

| 当前状态 | 主动作 |
| --- | --- |
| 没有 PDF | 获取 PDF / 上传 PDF |
| 有 PDF、未阅读 | 开始阅读 |
| 已读到一半 | 继续阅读第 N 页 |
| 翻译未完成 | 补齐翻译 |
| 没有导读 | 生成论文导读 |
| 有笔记未整理 | 整理阅读材料 |
| 已归档 | 查看论文 |

Research、Paper Library、Reader 的职责保持清晰：

- **Research**：继续阅读、待处理队列、最近活动和阅读结果状态。
- **Paper Library**：导入、搜索、主题树、标签、批量整理、归档和 PDF 资产管理。
- **Reader**：单篇论文的 PDF 阅读、翻译、导读、对照、笔记和引用。

研究台不重复 Paper Library 的完整树管理；Reader 也不承担 token、连接器或批量导入配置。

### 2.2 Paper Search

Paper Search 不再作为顶层并列 tab，而是 Paper Library 里的 **Find / Import**
工作流：用户在某个 collection 或 smart view 中发起搜索，结果先显示摘要和导入预览，
确认后再写入 Paper Library。这样搜索行为天然带着当前资料库上下文，不会像一个
独立框架悬在资料库之外。

推荐采用 **Codex-first**：
Codex 负责 agentic paper discovery，使用 web search / provider search / link
checking 组合能力找到论文、核对 PDF 链接、整理导入建议；Codex 不可用时，再回退到
provider API + LLM 轻量归一化。

Paper Search 不只是一个搜索框，它包含四种入口：


| 入口               | 作用                                             | 推荐后端                                                         |
| ---------------- | ---------------------------------------------- | ------------------------------------------------------------ |
| Topic Search     | 根据主题、问题、项目方向搜索论文，例如 `VLA memory`。              | Codex web search 优先；无 Codex 时用 arXiv / Semantic Scholar API。 |
| Provider Search  | 精确查 arXiv、Semantic Scholar 等结构化源。              | provider API，LLM 只做结果归一化和摘要压缩。                               |
| URL / DOI Import | 粘贴 DOI、arXiv URL、Semantic Scholar URL、PDF URL。 | Codex / connector 检查链接和补 metadata。                           |
| Upload PDF       | 直接上传本地 PDF，适合用户已有论文文件。                         | PyMuPDF + GROBID 默认抽取 metadata / full text / coordinates / TEI；必要时让 LLM 辅助补标题、作者、摘要候选。 |


#### 2.2.1 Search 输入区

输入区字段和作用：


| 功能                       | 作用                                                                                                                           |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| query                    | 用户的自然语言搜索意图，例如 `VLA memory`、`robot foundation model memory`、`long-horizon embodied agent memory`。Codex 可以把 query 扩展成多个英文检索式。 |
| search mode              | `Codex Search`、`Provider Search`、`Manual URL`、`Upload PDF`。默认推荐 `Codex Search`。                                              |
| provider toggles         | 限定或补充搜索来源，例如 `arXiv`、`Semantic Scholar`。Codex-first 仍可使用这些 provider 作为约束。                                                    |
| year range               | 控制论文年份，避免结果过旧或过新。                                                                                                            |
| has open-access PDF      | 只保留能下载或打开 PDF 的结果，便于后续进入 Reader。                                                                                             |
| min citation count       | 过滤引用数过低的结果；适合综述或入门阅读，不适合最前沿预印本。                                                                                              |
| field/category           | 限定学科或 arXiv category。                                                                                                        |
| exclude already imported | 排除当前 profile 已导入的论文，避免重复导入。                                                                                                  |
| project_refs / goal_refs | 告诉 Codex 当前搜索服务于哪个项目或目标，让它给出更贴近上下文的排序理由。                                                                                     |
| library node hint        | 导入时建议放入哪个主题树位置，例如 `VLA / Memory`。                                                                                         |


Codex Search 行为：

1. 读取当前 profile 的 project / goal / library tree hint。
2. 根据 query 生成 3-8 个检索式。
3. 使用 web search 和 provider search 找候选论文。
4. 检查 DOI / arXiv / Semantic Scholar / PDF 链接是否可访问。
5. 标记 open-access PDF、重复导入、metadata 冲突和可能的非论文结果。
6. 返回结构化候选，不直接写入 `research/sources.yaml`。

Codex 返回的每条结果必须包含：

```yaml
title: ""
authors: []
year: ""
venue: ""
abstract: ""
doi: ""
arxiv_id: ""
semantic_scholar_id: ""
canonical_url: ""
pdf_url: ""
open_access_pdf: false
provider_refs: []
why_relevant: ""
link_check:
  status: ok
  checked_at: ""
warnings: []
```

LLM fallback 边界：

- 如果 Codex 不可用，优先使用 arXiv / Semantic Scholar API 做真实搜索。
- LLM 只用于整理摘要、生成 relevance reason、归一化字段和生成导入建议。
- 没有 provider / URL 支撑时，LLM 不能凭空生成论文条目。
- LLM fallback 结果必须标记 `needs_link_check: true`，用户确认前不能自动下载 PDF。

搜索结果表格：


| 列         | 说明                       |
| --------- | ------------------------ |
| Select    | 是否导入                     |
| Title     | 论文标题                     |
| Year      | 年份                       |
| Venue     | 会议 / 期刊                  |
| Authors   | 前 3 位作者                  |
| Provider  | arXiv / Semantic Scholar |
| Citations | 引用数，若 provider 有         |
| OA PDF    | 是否有 open-access PDF URL  |
| Link      | Codex / connector 链接检查状态 |
| Imported  | 是否已在当前 profile 中         |
| Relevance | Codex / LLM 给出的相关性理由摘要   |
| Tags      | category / field         |


每列作用：

- `Select`：用户显式选择要导入的论文，避免搜索结果自动污染资料库。
- `Title / Year / Venue / Authors`：快速判断论文身份和可信度。
- `Provider`：说明 metadata 来源，方便定位冲突。
- `Citations`：辅助排序，不作为质量唯一标准。
- `OA PDF`：决定能否一键下载 PDF 进入 Reader。
- `Link`：显示链接检查状态，例如 `ok`、`pdf missing`、`403`、`needs check`。
- `Imported`：提示重复导入和已有 source id。
- `Relevance`：解释为什么这篇论文和 query / project / goal 相关。
- `Tags`：用于导入后的横向筛选和后续综合阅读；真实归档位置由 library tree 决定。

右侧 detail drawer 显示：

- abstract
- DOI / arXiv id / Semantic Scholar paper id
- PDF URL
- provider metadata
- duplicate / conflict reason
- suggested library nodes / tags
- Codex relevance rationale
- link check details
- suggested next actions

导入流程：

1. 用户勾选结果。
2. 点击 `Import selected`。
3. 弹窗设置：
   - library tree location
   - tags
   - visibility，默认 `private`
   - status，默认 `inbox`
   - goal_refs / project_refs
   - PDF 策略：
     - `Metadata only`
     - `Download open-access PDF`
     - `Upload local PDF after import`
4. 显示 YAML preview 和 duplicate/conflict preview。
5. 用户确认后才写文件。

PDF 上传流程：

1. 用户选择 `Upload PDF`。
2. 上传本地 PDF。
3. 系统计算 sha256、大小、页数，保存到 `NBLANE_RESEARCH_ASSET_ROOT`。
4. 使用 PyMuPDF 抽取基础 metadata、页数、page text、坐标；同时使用 GROBID 抽取
   header / references / full text / coordinates / TEI。
5. 如果 metadata 不完整，AI 只生成候选标题、作者、摘要、年份，用户确认后才写入 source。
6. 如果用户同时粘贴 DOI / arXiv URL，优先用外部 metadata 修正 PDF 抽取结果。

去重优先级：

```text
doi
  -> arxiv_id
  -> semantic_scholar_id
  -> canonical_url
  -> normalized_title + year
```

导入后给三个操作：

- `Open Reader`
- `Move in Library Tree`
- `Generate Paper Guide`，在用户需要结构化论文导读、深度阅读计划或项目相关性分析时触发。

### 2.3 Paper Library

Paper Library 是论文资料库，也是 **Paper Search 和 Reader 之间的桥梁**。
它应该首先是一个 **主题树**，而不是一组状态列表：用户按主题、问题域和研究方向
组织论文；`inbox / reading / annotated / archived` 这些只是
论文属性和筛选条件，不应该决定论文在资料库里的位置。

核心原则：

- 树结构表达“这篇论文归档到哪里”。
- 状态、标签、项目、目标、PDF 资产表达“这篇论文现在是什么情况”。
- Library 内的 Find / Import 搜索结果必须先展示摘要、相关性理由、PDF 状态和重复风险，
  再由用户选择导入到树上的特定位置。
- 树节点可以由用户手动创建，也可以由 Codex / LLM 根据论文标题、摘要、已有树结构
  生成建议。
- Reader 只打开一个已经被 Library 管理好的 paper source。

#### 2.3.1 Tree-first 信息架构

Paper Library 左侧主导航是主题树，右侧是当前节点下的论文列表和详情抽屉：

```text
Paper Library
  All Papers
  Library Tree
    VLA
      Memory
      Perception
      Motion Control
      Evaluation
    Robotics
      Imitation Learning
      Planning
    Foundation Models
      Multimodal
      Agents
  Smart Views
    Inbox
    Reading
    Annotated
    Needs Translation
    Needs Guide
    Archived
    Discarded
  Other Sources
```

这里 `VLA / Memory / Perception / Motion Control` 是存储和浏览结构；
`Inbox / Reading / Annotated / Archived` 是 smart views。也就是说，一篇论文可以放在：

```text
Library Tree / VLA / Memory
```

同时它的属性可以是：

```yaml
status: reading
tags: [memory, long-horizon, robotics]
project_refs: [...]
goal_refs: [...]
pdf_asset_ref: papers/...
```

UI 上应避免把 smart views 做成和主题树平级的“真实文件夹”。它们是搜索结果视图，
不是存储位置。

#### 2.3.2 树节点和论文属性的边界

树节点只回答一个问题：

```text
这篇论文应该放在哪个研究主题下面？
```

论文属性回答其他问题：

| 维度 | 示例 | 是否影响树位置 |
| --- | --- | --- |
| status | inbox / reading / annotated / archived / discarded | 否，只用于筛选和队列。 |
| tags | memory、perception、benchmark、survey | 否，只用于横向检索。 |
| project_refs | 某个项目 case id | 否，只说明论文和项目相关。 |
| goal_refs | 某个目标 id | 否，只说明论文服务哪个目标。 |
| PDF asset | `papers/<sha>-title.pdf` | 否，只是外置文件引用。 |
| extraction state | PyMuPDF / GROBID / needs extraction | 否，只是处理状态。 |
| reading state | annotations、notes、chunks、translations、analysis、citations | 否，只是阅读沉淀状态。 |
| library_node_refs | `paper-node:vla-memory` | 是，决定论文在树上的位置。 |

这能避免资料库变成很多互相冲突的“状态文件夹”。例如同一篇论文可以同时：

- 位于 `VLA / Memory`。
- 状态是 `reading`。
- 带有 `perception` tag。
- 关联 `project:vla-memory-module`。
- 有 PDF asset。
- 有 12 条 annotations、3 条 citations，且仍有部分翻译待处理。

#### 2.3.3 Search -> Library Tree -> Reader 桥接

导入后的 paper 不应该直接消失到 `sources.yaml`，也不应该只进入一个临时 Inbox。
Paper Search 的导入弹窗必须让用户选择“归档位置”：

```text
Paper Search
  -> Codex / provider search
  -> Select papers
  -> Choose library tree location
  -> Optional: create new tree node
  -> Optional: accept AI placement suggestions
  -> Import into Paper Library
  -> Open Reader
```

导入选项：

- `Archive to existing node`：归档到已有树节点，例如 `VLA / Memory`。
- `Create child node`：在当前节点下创建子主题，例如 `VLA / Memory / Episodic Memory`。
- `Ask AI to suggest location`：让 Codex / LLM 根据标题、摘要、已有 tree 生成位置建议。
- `Import to Unsorted Inbox`：暂时不知道放哪里时进入未分类队列。
- `Import as metadata only`：只保存 source，不下载 PDF。
- `Download open-access PDF`：下载 PDF asset。
- `Upload local PDF`：上传本地 PDF 并绑定到 source。

Codex Search 应返回 `suggested_library_nodes`：

```yaml
suggested_library_nodes:
  - node_ref: paper-node:vla-memory
    path: ["VLA", "Memory"]
    confidence: 0.84
    rationale: "The abstract focuses on persistent memory for embodied VLA agents."
  - node_ref: paper-node:robotics-planning
    path: ["Robotics", "Planning"]
    confidence: 0.42
    rationale: "The paper also discusses long-horizon planning."
```

用户必须确认位置后才写入 `library_node_refs`。模型不能静默重排资料库。

Reader 写入 annotations、chunks、translations、analysis 后，Library 负责重新计算
derived state，例如 `annotated`、`needs translation`、`needs guide`、`stale translation`、
`citation risk`，但这些仍然只是筛选属性，不改变树位置。

#### 2.3.4 树节点设计

树节点是轻量 taxonomy，不是文件夹里的真实 PDF 拷贝：

```yaml
nodes:
  - id: paper-node:vla
    title: VLA
    parent_id: ""
    description: Vision-Language-Action model papers.
    order: 10
    color: teal
    icon: ""
    status: active
    project_refs: []
    goal_refs: []
    created_by: user
  - id: paper-node:vla-memory
    title: Memory
    parent_id: paper-node:vla
    description: Memory mechanisms for long-horizon embodied agents.
    order: 20
    color: teal
    status: active
    project_refs:
      - project:vla-memory-module
    goal_refs: []
    created_by: ai
```

论文通过 `library_node_refs` 连接到一个或多个节点：

```yaml
sources:
  - id: source:research:20260519-001
    kind: paper
    title: "..."
    library_node_refs:
      - paper-node:vla-memory
    status: reading
    tags: [memory, vla]
```

规则：

- 一个 paper 至少应该有一个 library node；没有时显示在 `Unsorted Inbox`。
- 一个 paper 可以属于多个 tree node，但 UI 默认推荐一个 primary node。
- 移动论文只改 `library_node_refs`，不移动 PDF 文件。
- 重命名树节点不影响 source id、PDF asset ref、annotations 或 citations。
- 删除树节点前必须选择：移动论文到父节点、移动到 Unsorted、或取消删除。

#### 2.3.5 Smart Views

Smart Views 是系统筛选，不是存储结构：

| Smart View | 筛选逻辑 | 作用 |
| --- | --- | --- |
| All Papers | 所有 `kind: paper` 的 sources。 | 全局搜索和批量整理。 |
| Unsorted Inbox | 没有 `library_node_refs` 或显式待分类的 paper。 | 接住 Paper Search 临时导入结果。 |
| Reading | `status=reading`。 | 继续阅读。 |
| Annotated | 有 annotation / chunk / note 的 paper。 | 找出已经读出内容但还没沉淀的论文。 |
| Needs Translation | 有缺失或 stale 翻译的 paper。 | 进入翻译队列。 |
| Needs Guide | 没有论文导读或导读需要重新核对的 paper。 | 进入导读队列。 |
| Archived | `status=archived`。 | 已阶段性处理完的论文。 |
| Discarded | `status=discarded`。 | 明确不再阅读的论文。 |
| Other Sources | 非 paper 的 research sources。 | 避免网页、repo、书籍混入论文树。 |

Smart View 中的论文仍显示它们所属 tree path，例如：

```text
Reading
  A paper about embodied memory     VLA / Memory
  A paper about robot control       VLA / Motion Control
```

#### 2.3.6 主列表字段

主列表字段：

- title
- tree path
- status
- has PDF
- annotations count
- chunks count
- notes count
- citations count
- last read

字段作用：

| 字段 | 作用 |
| --- | --- |
| title | 论文标题，主点击区，进入 Reader 或详情页。 |
| tree path | 论文在主题树中的位置，例如 `VLA / Memory`。这是存储结构。 |
| status | 管理状态：inbox / reading / archived / discarded 等。这是属性。 |
| has PDF | 是否已有本地 PDF asset；没有 PDF 时 Reader 进入 metadata/text fallback。 |
| annotations count | 用户产生的高亮和批注数量，表示阅读深度。 |
| chunks count | 可复用摘录数量，表示阅读材料是否已经结构化。 |
| notes count | 用户笔记和高亮数量，表示阅读沉淀深度。 |
| citations count | citations 数量，表示引用材料是否已经结构化。 |
| last read | 最近阅读或编辑时间，用于继续阅读。 |

推荐额外显示轻量 badges：

- `Unsorted`
- `PDF missing`
- `Needs extraction`
- `GROBID ready`
- `Stale translation`
- `Citation broken`
- `Private source`
- `Guide pending`
- `Duplicate risk`

这些 badge 应该可点击进入对应的修复动作，例如选择树位置、重新抽取、重新翻译、
检查 citation、打开 duplicate preview。

#### 2.3.7 AI 生成分组和自动归档建议

模型可以帮助生成树结构，但只生成 candidate：

- `Suggest library tree`：根据当前论文库生成主题树草案。
- `Suggest location for selected papers`：给选中论文推荐树节点。
- `Split node`：发现某节点过大时建议拆分为子节点。
- `Merge nodes`：发现重复主题时建议合并。
- `Rename node`：把含糊命名改成更清晰的研究主题。

AI 生成分组时必须展示 preview：

```text
Create node: VLA / Memory / Episodic Memory
Move papers:
  - Paper A
  - Paper B
Reason:
  These papers all discuss memory persistence across long-horizon tasks.
```

用户点击接受后才修改 tree nodes 或 source 的 `library_node_refs`。

#### 2.3.8 详情抽屉

点击列表行时打开 detail drawer，不直接把用户带离 Library：

- metadata：title、authors、year、venue、abstract、DOI、arXiv id、URL。
- tree：primary node、secondary nodes、suggested nodes、move action。
- storage：PDF asset ref、sha256、page count、extraction backend、last extracted。
- organization：tags、project_refs、goal_refs、priority。
- reading status：last read page、annotations、chunks、translations、analysis。
- reading materials：notes、chunks、citations、analysis、exports。
- risks：private publish risk、citation 断链、stale translation、duplicate conflict。
- actions：Open Reader、Move in Tree、Run extraction、Generate Paper Guide、Archive、Discard。

这个 drawer 是“整理站”，Reader 是“阅读现场”。不要把批注编辑、长翻译和大段 AI
问答塞进 Library。

#### 2.3.9 批量动作

支持 bulk action：

- move to node
- archive
- discard
- add tags
- set status

每个批量动作的含义：

| 动作 | 含义 |
| --- | --- |
| move to node | 把所选论文放到指定树节点；只改 `library_node_refs`，不移动 PDF 文件。 |
| archive | 把所选论文状态改为 `archived`，保留树位置、PDF、批注、翻译、notes、chunks、citations。 |
| discard | 把所选论文状态改为 `discarded`，表示不再阅读；默认仍保留 source 和 asset refs，避免误删。 |
| add tags | 给所选论文增加 tags，用于横向检索。 |
| set status | 批量设置 inbox / reading / archived / discarded 等管理状态。 |

推荐后续增加但不放在 v1 主路径的危险动作：

- delete source record
- delete PDF asset
- delete extracted pages / segments
- purge discarded papers

归档只把 source status 改为 `archived`，不删除 PDF asset，也不从主题树移除。
删除 PDF asset 不放在 v1 主路径，后续作为危险管理动作。

### 2.4 Reader

Reader 是单篇论文的阅读现场。它保持 PDF 原文的白纸可读性，外层导航、目录、AI
面板和状态栏使用 nblane 的深色石雕星空语言。

Reader 的用户入口和产品外壳属于 SPA。当前实现采用渐进式集成：

```text
SPA ResearchPage
  -> SPA PaperReaderPage
     -> Reader sidecar iframe（过渡承载）
        -> PDF.js / Reader API
```

这意味着用户从研究台进入论文、看到标题和阅读状态、返回列表以及恢复深链，都发生在
SPA 路由中；现阶段 PDF.js 画布和部分阅读交互仍由 FastAPI sidecar 提供。iframe 是
兼容现有 PDF 渲染和 Reader API 的过渡方案，不是最终的产品页面。SPA 和 sidecar 不能
各自维护一套阅读状态，页码、模式、章节、锚点、翻译任务和阅读进度必须由同一组
Reader API 和 URL 状态驱动。

目标状态是把 Reader UI 逐步迁移为 SPA 原生 React 页面：

- SPA 原生负责目录、PDF 阅读区、逐段翻译、原文对照、笔记和 AI 导读。
- FastAPI sidecar 只保留 PDF 文件流、页面预览、text layer / segment payload、翻译与
  AI task、annotations、notes、chunks、citations 和 progress API。
- 旧的 sidecar HTML 保留为兼容入口和故障降级路径，不能继续扩展为第二套主界面。

Reader 不是三个互相独立的页面，而是一个共享阅读会话中的两个主视图和一个导读层：

```text
论文概览 / AI 导读
        -> 逐段阅读
        <-> 原文对照
```

共享状态包括：

- 当前页、章节和 segment；
- 当前选区和原文定位；
- 当前翻译锚点；
- 阅读模式和滚动位置；
- 笔记面板状态；
- 上次阅读进度。

URL 可以恢复关键上下文，例如：

```text
?mode=translation&page=3&anchor=segment-42
?mode=summary&section=method
?mode=compare&page=5&anchor=segment-88
```

#### 2.4.1 论文概览 / AI 导读

打开新论文时先显示中文摘要和结构化导读；已经读过的论文优先显示“继续阅读第 N 页”。

导读包含：

- 一句话结论；
- 研究问题；
- 核心方法；
- 主要发现；
- 局限与风险；
- 与当前项目或目标的关系；
- 推荐先读的章节。

每条内容都应该能跳回页码、章节、segment 或原文高亮。导读不是普通聊天窗口，
也不把没有依据的内容显示成确定结论。

导读状态明确区分：

```text
未生成 / 生成中 / 已完成 / 部分完成 / 待核对 / 失败
```

没有可靠结构化结果时显示“未评估”或“需要人工核对”，不把 fallback 结果显示成零分。

#### 2.4.2 逐段阅读

逐段阅读是主要的中文精读视图。它优先保证段落完整、译文可读和原文可追溯，
不强行把中文塞回英文 PDF 的原始文字框。

桌面端布局：

```text
┌──────────────┬──────────────────────────┬───────────────┐
│ 目录 / 页面    │ 原文段落 + 中文译文        │ 笔记 / 导读     │
│              │                          │               │
│              │ 原文段落                  │               │
│              │ 中文译文                  │               │
└──────────────┴──────────────────────────┴───────────────┘
```

支持：

- 摘要、当前章节、当前页和全文翻译；
- 只翻译缺失或 stale 的段落；
- 翻译完成度和失败原因；
- 原文与译文同步高亮；
- 点击译文跳回 PDF 页码和 rect；
- 选区翻译、解释、做笔记和创建引用。

移动端采用原文在上、译文在下的单栏布局，不强行使用三栏。

#### 2.4.3 原文对照

原文对照用于核对译文、页面结构、图表、公式和实验结果，不作为所有用户的默认视图。

```text
┌──────────────────────────┬──────────────────────────┐
│ PDF 原文页面              │ 对应中文页面              │
│ 原始双栏、图表、公式       │ 可伸缩的结构化中文排版     │
└──────────────────────────┴──────────────────────────┘
```

支持：

- 页码和滚动同步；
- 原文段落和译文段落共同高亮；
- 点击任一侧跳到另一侧；
- 页面缩放；
- 图表、公式和参考文献保留原文；
- 中文过长时从 overlay 自动降级为 flow 布局。

overlay 只适合短标题、摘要和简单正文。正文、长中文段落、多栏不确定区域和复杂表格
优先采用可伸缩排版或段落对照，不为了保持位置把文字缩到不可读。

#### 2.4.4 段落翻译和选区操作

PDF 原文仍然是主要阅读对象。用户可以点击结构化段落，也可以拖选精确文本。

交互规则：

- 已有缓存译文时，点击段落直接显示译文气泡；
- 没有缓存时，先显示“翻译此段”操作，不自动消耗 AI 请求；
- 拖选文字时显示翻译、解释、笔记和引用工具条；
- 双击和三击保留浏览器原生选词行为；
- `Esc` 关闭气泡；键盘焦点可以用 `Enter` 打开段落操作；
- 桌面端气泡使用绝对定位，不增加 PDF 横向宽度；
- 气泡避开当前段落，空间不足时回退到右侧面板；
- 移动端使用底部抽屉；
- 识别不到可靠坐标时提示用户拖选文字，不猜测段落。

气泡默认显示中文译文，原文折叠显示；同时显示页码、章节、翻译状态和保存操作。

#### 2.4.5 笔记、Chunk 和 Citation

笔记贯穿论文概览、逐段阅读和原文对照。选区工具条只提供阅读材料操作：

```text
翻译 | 解释 | 做笔记 | 创建引用 | 加入 Chunk
```

本阶段不提供：

```text
创建 Claim | Promote to Evidence | 关联技能 | 修改 Evidence
```

保存的阅读材料继续绑定：

```text
source_id
segment_id
page
locator
rects
selected_text
translated_text
note
```

点击笔记、Chunk 或 Citation 必须能够回到 PDF 原文位置。

#### 2.4.6 Reader 功能清单

| 功能 | 读者收益 |
| --- | --- |
| PDF 阅读 | 保留页码、缩放、搜索和阅读位置。 |
| TOC / sections | 快速跳到 Abstract、Introduction、Method、Experiments、Conclusion。 |
| 页面缩略图 | 快速定位图表、实验结果和附录。 |
| 论文导读 | 先判断论文做了什么以及是否值得深入。 |
| 逐段翻译 | 逐段阅读中文内容，译文可回到原文。 |
| 原文对照 | 核对英文、译文、版面、公式和图表。 |
| 选区解释 | 解释术语、难句和公式上下文。 |
| 高亮批注 | 把重要句子保存为可回溯笔记。 |
| Chunk 创建 | 保存可复用的原文片段。 |
| Citation 创建 | 从选区或 Chunk 生成带 locator 的引用材料。 |
| Ask Paper | 围绕当前论文提问，回答必须带来源 refs。 |
| Jump back | 从导读、笔记、Chunk、Citation 或译文回到 PDF。 |

#### 2.4.7 阅读路径

```text
打开论文
  -> 中文摘要 / 论文导读
  -> 逐段阅读或直接打开原文
  -> 点击段落翻译，或拖选文本
  -> 保存笔记 / Chunk / Citation
  -> 需要核对时切换原文对照
  -> 保存阅读进度
```

论文阅读不自动产生 Claim 或 Evidence。

### 2.5 Claims & Evidence 边界

论文阅读阶段暂时屏蔽 Claim 和 Evidence。

这是产品入口和写入行为的限制，不是删除现有历史数据或兼容字段。已有
`research/claims.yaml`、`claim_refs` 和 Evidence 相关 API 暂时保留，
Reader 本阶段不展示、不创建、不更新这些数据。

Reader 不显示：

- Claims tab；
- claim candidate；
- `Promote to Evidence`；
- Evidence Review 入口；
- 技能关联和项目成果证明。

论文阅读仍保留 Citation，因为 Citation 是可回到论文原文的研究材料，不等于 Evidence。

未来如果重新开启 Claim，需要另行定义从阅读材料到 Claim 的审核流程；本阶段不提前
写入 `research/claims.yaml`，也不调用 `research_claim_to_evidence_candidate()`。

### 2.6 Synthesis / Export

本阶段只处理阅读材料，不处理 Claim 或 Evidence promotion。

支持：

- 从已选笔记、Chunk 和 Citation 生成 reading note；
- 导出 BibTeX；
- 导出 Markdown bibliography / quote list；
- 复制或下载阅读材料。

只有用户点击 `Save export` 才写入：

```text
research/exports/<timestamp>.bib
research/exports/<timestamp>.md
```

多篇论文 literature memo、Claim、证据审阅和内容工作台的上游连接后置，
不阻塞单篇论文阅读闭环。

### 2.7 Inbox & Connectors

连接器不再使用含糊的“高级连接器”命名。它属于 Research 的「收件箱与连接器」区：
手动 URL、CSV、JSON、arXiv / Semantic Scholar 等导入先进入 Source Inbox、
collection 或 metadata-only 队列。Reader 只消费已经导入的 source，不负责配置
token、cookie 或 API key。

## 3. 存储设计

### 3.1 PDF asset root

PDF 二进制必须外置保存，不进入 profile Git 目录。

新增环境变量：

```bash
NBLANE_RESEARCH_ASSET_ROOT=/srv/nblane-assets/research
```

默认路径：

```text
~/.nblane/research-assets/profiles/<safe-profile>/papers/
```

部署推荐：

```text
/srv/nblane-app       # 应用代码
/srv/nblane-data      # 私有数据 Git 仓库，含 profiles/ schemas/ auth/
/srv/nblane-assets    # 大文件资产，不进 Git，含 research PDFs
```

profile 文件只保存 asset ref，不保存绝对路径：

```yaml
metadata:
  pdf_asset_ref: papers/ab12cd34ef56-vla-memory.pdf
  pdf_sha256: ab12cd34...
  pdf_byte_size: 2345678
  page_count: 16
```

迁移服务器时需要同步：

- `NBLANE_ROOT`
- `NBLANE_RESEARCH_ASSET_ROOT`

### 3.2 `research/sources.yaml`

扩展 `ResearchSource`，保持向后兼容。

```yaml
sources:
  - id: source:research:20260519-001
    kind: paper
    title: "A Survey of Vision-Language-Action Models"
    status: reading
    visibility: private
    origin: connector
    url: https://arxiv.org/abs/2605.00001
    authors:
      - Alice Zhang
      - Bob Wang
    published: "2026-05-01"
    tags:
      - VLA
      - robotics
    goal_refs: []
    project_refs: []
    library_node_refs:
      - paper-node:vla-memory
    summary: "..."
    metadata:
      doi: ""
      arxiv_id: "2605.00001"
      semantic_scholar_id: ""
      venue: arXiv
      citation_count: 0
      fields_of_study:
        - Computer Science
      open_access_pdf_url: https://arxiv.org/pdf/2605.00001
      pdf_asset_ref: papers/ab12cd34-vla-survey.pdf
      pdf_sha256: ab12cd34...
      pdf_byte_size: 2345678
      page_count: 16
      text_extracted_at: "2026-05-19T12:00:00+08:00"
      structure_backend: grobid
```

### 3.3 `research/library-tree.yaml`

```yaml
schema_version: "1.0"
profile: 王军
updated: "2026-05-19"
nodes:
  - id: paper-node:vla
    title: VLA
    parent_id: ""
    description: Vision-Language-Action model papers.
    color: teal
    order: 10
    status: active
    created_by: user
  - id: paper-node:vla-memory
    title: Memory
    parent_id: paper-node:vla
    description: Papers about embodied memory and long-horizon VLA systems.
    color: teal
    order: 20
    status: active
    created_by: ai
    project_refs:
      - project:vla-memory-module
    goal_refs: []
```

成员关系保存在 source 的 `library_node_refs`，避免 tree 文件成为 source 的第二
事实源。树节点只负责主题结构；status、tags、project_refs、goal_refs、PDF asset
仍然保存在 source 或 metadata 中。

### 3.4 `research/paper-pages/<source_slug>.jsonl`

页级文本，主要用于 fallback 阅读、粗粒度 QA、翻译 page。

```json
{"source_id":"source:research:20260519-001","page":1,"text":"...","char_count":4200,"text_hash":"sha256:...","extracted_at":"2026-05-19T12:00:00+08:00"}
```

### 3.5 `research/paper-segments/<source_slug>.jsonl`

段落 / section / figure caption / table caption 的稳定单元，是翻译对齐和长文本
AI 的核心。

```json
{"segment_id":"seg:source-research-20260519-001:00042","source_id":"source:research:20260519-001","page":3,"order":42,"section_path":["Method","Memory Encoder"],"kind":"paragraph","text":"...","text_hash":"sha256:...","locator":"p. 3 § Method","rects":[{"page":3,"x":72,"y":120,"w":440,"h":58}]}
```

### 3.6 `research/annotations/<source_slug>.jsonl`

高亮、批注、人工问题、阅读笔记。

```json
{"id":"ann:source-research-20260519-001:0001","source_id":"source:research:20260519-001","kind":"highlight","page":3,"locator":"p. 3","selected_text":"The memory encoder stores...","selected_text_hash":"sha256:...","note":"和我们的 VLA memory 模块相关。","color":"yellow","rects":[{"page":3,"x":100,"y":220,"w":320,"h":36}],"tags":["memory"],"chunk_refs":["chunk:source-research-20260519-001:001"],"status":"active","created":"2026-05-19T12:00:00+08:00","updated":"2026-05-19T12:00:00+08:00"}
```

### 3.7 `research/translations/<source_slug>.jsonl`

接受后的翻译缓存。翻译不覆盖原文。

```json
{"id":"tr:source-research-20260519-001:0001","source_id":"source:research:20260519-001","scope_type":"segment","scope_ref":"seg:source-research-20260519-001:00042","segment_id":"seg:source-research-20260519-001:00042","page":3,"source_hash":"sha256:...","source_text":"The memory encoder stores...","target_lang":"zh","translated_text":"记忆编码器会存储……","glossary":{"memory encoder":"记忆编码器"},"generated_by":"llm:research.paper_translate","created":"2026-05-19T12:00:00+08:00"}
```

### 3.8 `research/analysis/<source_slug>.yaml`

用户接受后的 AI 阅读报告。

```yaml
schema_version: "1.0"
source_id: source:research:20260519-001
updated: "2026-05-19T12:00:00+08:00"
generated_by: llm:research.paper_source_guide
tldr: "..."
contributions:
  - text: "..."
    cited_segment_refs: [seg:source-research-20260519-001:00042]
methods: []
datasets: []
results: []
limitations: []
open_questions: []
key_terms: []
section_summaries: []
warnings: []
```

### 3.9 `research/notes/<source_slug>.md`

阅读笔记使用 Markdown + front matter，可选 BlockNote sidecar。

```markdown
---
source_id: source:research:20260519-001
reading_status: reading
visibility: private
library_node_refs:
  - paper-node:vla-memory
chunk_refs: []
claim_refs: []
citation_refs: []
---

# A Survey of Vision-Language-Action Models

## TL;DR

...
```

## 4. 第三方库和后端策略

### 4.1 当前过渡前端：SPA 外壳 + FastAPI sidecar + PDF.js

SPA 的 `/research` 和 `/research/papers/:source_id/reader` 是用户可见的主入口。
`PaperReaderPage` 负责标题、返回、阅读状态、URL 深链、错误反馈和 sidecar 生命周期；
当前 PDF 阅读画布由 FastAPI sidecar 的 `/reader/view/{source_id}` 通过 iframe 承载。
`research_paper_reader_component/events.py` 只作为事件常量契约。前端 PDF 渲染由 sidecar 模板加载 bundled PDF.js 资产完成。

近期不重写 PDF.js，也不让 SPA 和 sidecar 分别实现翻译、批注或进度保存。先把 SPA 作为
唯一产品外壳，再以同一套 API 和 URL 契约逐步替换 iframe 内的 UI。

目标前端：SPA 原生 Reader + Reader API。sidecar 只作为 PDF/结构化数据和任务 API 服务，
并在原生 Reader 尚未覆盖的情况下保留兼容降级入口。

职责：

- PDF render
- text layer selection
- rects normalization
- page / zoom / search
- highlight rendering
- annotation click -> page jump
- translate / analyze / ask event emit

不负责：

- 写文件
- 调 AI
- 管 PDF asset root
- 修改 PDF 原件

### 4.2 默认本地 PDF 后端：PyMuPDF

默认安装并使用 `PyMuPDF` 作为本地 PDF backend。

用途：

- 校验 PDF 可读。
- 读取 page count。
- 抽取 PDF metadata。
- 抽取 page text。
- 抽取 text blocks / spans / coordinates。
- 支撑 PDF.js 高亮 rect 对齐。
- 在 GROBID 不可用时提供 page text / heuristic segments fallback。

选择理由：

- 速度快。
- 坐标和 layout 支持强。
- 适合 Reader 的高亮、跳转、选区、页级翻译和 LLM-ready extraction。

许可决策：

- PyMuPDF 官方采用 AGPL / commercial dual licensing。
- 本计划将 PyMuPDF 作为默认依赖，意味着项目部署方需要明确接受 AGPL 约束，
  或为生产/闭源/商业部署准备 commercial license。
- 文档和部署页必须把该许可边界写清楚；不能把 PyMuPDF 作为“无许可成本”的普通依赖。

默认配置：

```bash
NBLANE_RESEARCH_PDF_BACKEND=pymupdf
```

### 4.3 默认结构化抽取服务：GROBID

GROBID 默认纳入 Paper Reading Studio 的部署和抽取流程，用于学术 PDF 的结构化解析。
它是默认 structured extraction backend；PyMuPDF 是默认 local PDF backend。两者配合：

```text
PyMuPDF
  -> PDF 可读性、页数、page text、坐标 fallback、Reader 高亮支撑

GROBID
  -> header、abstract、body sections、references、TEI、学术结构化 segments
```

GROBID 适合学术 PDF：

- header extraction
- reference extraction
- full text extraction
- section / paragraph / figure / table 结构化
- PDF coordinates
- TEI XML 输出
- reference annotations

许可和来源：

- GROBID 仓库声明 Apache-2.0 license。
- 官方文档说明它将 PDF 转为结构化 XML/TEI，并聚焦 technical / scientific publications。
- 官方 REST API 支持 `processHeaderDocument`、`processFulltextDocument`、
  `processReferences`、reference annotation 等服务。

配置：

```bash
NBLANE_GROBID_URL=http://127.0.0.1:8070
NBLANE_RESEARCH_PDF_BACKEND=grobid
```

`NBLANE_RESEARCH_PDF_BACKEND` 取值 `pymupdf|grobid|auto`，默认 `auto`：按
`NBLANE_GROBID_URL` 探测 GROBID，不可达时回退 PyMuPDF；设为 `pymupdf` 可强制
禁用 GROBID 探测。

行为：

- 默认尝试使用 GROBID 做结构化抽取。
- GROBID 成功时生成：
  - page text
  - segments
  - section path
  - figure/table captions
  - references
  - coordinates
  - BibTeX metadata
- GROBID 不可用或返回错误时，优先使用 PyMuPDF text layer 的版面/列/段落启发式生成带
  rect 的段落级 segments；只有 PDF 没有可用 text layer 时才回退到 page text segments。
  旧的 page-sized segments 仅作为兼容性最后 fallback，不作为 Reader 的主要阅读结构。
- 本地结构缓存版本为 `v6`。缓存签名包含 PDF 指纹和 segment 内容；PDF 或 GROBID
  语义输入发生变化时重建，重复打开直接复用缓存。暂时无法读取 PDF 时保留已保存结构，
  包括显式强制重建失败的情况，避免清空原本可读的目录和段落。
- Reader 检测到旧本地 fallback 时，通过现有后台准备任务按需重建页级派生解析；
  `pymupdf` 模式不探测 GROBID，GROBID 冷却期内也只做本地升级。PDF 原件、笔记、批注
  和翻译文件保留；旧译文仍按内容唯一匹配复用，匹配不了的译文不能绑定到新段落。
- 抽取 metadata 的 `fallback_structure_quality` 记录正文、标题、caption、坐标覆盖、
  段落平均/最大长度等指标。坐标覆盖说明可定位，不代表学术语义已经人工核验；
  全文翻译仍以 canonical structure 的 `translation_readiness` 检查为准。
- 双栏页面按跨栏标题分区，在每个区内先读左栏再读右栏；标题不能排到整页正文之后。
  内联 `Abstract:` 分为标题与正文；加粗编号章节与正文分开，低字号图内编号不进入目录。
- 验收先打开含 Abstract 的第一页，再点击第三页章节目录、切换原文对照、点击译文卡
  确认原文矩形高亮，最后刷新重开确认结果一致。只有文本层缺失的扫描 PDF 才需要另行
  引入 OCR；本轮没有新增 Docling/MinerU 依赖。
- GROBID error 要转成用户可读 warning，不阻塞 PDF 导入，但 Library 应显示
  `GROBID unavailable` / `Needs structured extraction` badge。

推荐部署：

```bash
docker run -d --name nblane-grobid --restart unless-stopped \
  -p 127.0.0.1:8070:8070 \
  grobid/grobid:0.9.0-crf
```

启动后验证：

```bash
curl http://127.0.0.1:8070/api/isalive
```

返回 `true` 代表 nblane 可以使用该服务。生产或本机 `.env` 中应配置：

```bash
NBLANE_GROBID_URL=http://127.0.0.1:8070
NBLANE_RESEARCH_PDF_BACKEND=grobid
```

依赖和启动要求：

- GROBID 本身不是云 API，而是自托管 REST 服务；nblane 只要求能访问
  `GET /api/isalive` 和 `POST /api/processFulltextDocument`。
- 推荐使用 Docker 镜像部署，避免手工处理 Java / Gradle / 模型依赖。
- 本地源码方式也可行，但需要 Java 21，并按 GROBID 官方 Gradle 流程启动服务。
- 为保护私有论文，默认建议只绑定 `127.0.0.1:8070`，不要直接暴露公网。
- 国内环境拉 Docker Hub 可能失败，可先配置 Docker registry mirror，再拉
  `grobid/grobid:0.9.0-crf`。
- GROBID 服务不可用时，Reader 仍能工作，但结构化抽取会显示
  `GROBID unavailable` / `Needs structured extraction`，并回退到 PyMuPDF 带坐标段落；
  page text 只保留为无可用版面结果时的最后回退。

常用维护命令：

```bash
sudo docker ps --filter name=nblane-grobid
sudo docker logs -f nblane-grobid
sudo docker restart nblane-grobid
sudo docker stop nblane-grobid
```

实现优先级：

1. 先实现 direct REST adapter，不强依赖 grobid-client-python。
2. 解析 TEI 中 header、abstract、body div、paragraph、figure/table、biblStruct。
3. 后续再考虑 grobid-client-python 的 Markdown / JSON converter。

### 4.4 备用后端：pypdf

pypdf 不作为 v1 主路径默认后端。它可以保留为测试 fixture 或极简部署 fallback，
但 Paper Reading Studio 默认实现不依赖它完成核心阅读体验。

策略：

- 默认依赖包含 PyMuPDF。
- 默认部署包含 GROBID 服务。
- pypdf 只用于：
  - PyMuPDF 安装失败时的临时诊断。
  - 轻量 metadata fixture。
  - 不需要坐标、不需要 Reader 高亮的极简 fallback。
- pypdf fallback 不保证双栏论文、caption、表格和坐标体验。

### 4.5 参考链接和许可决策

实现前需要以官方来源再次确认依赖边界：


| 组件                    | 用途                                                              | 许可 / 引入策略                                 | 官方链接                                                                                                                                          |
| --------------------- | --------------------------------------------------------------- | ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| PDF.js / `pdfjs-dist` | 前端 PDF 渲染、text layer、selection                                  | 默认前端依赖                                    | [https://mozilla.github.io/pdf.js/](https://mozilla.github.io/pdf.js/)                                                                        |
| PyMuPDF               | 默认本地 PDF 抽取、坐标、图片、表格、LLM-ready extraction                      | 默认依赖；部署方需要接受 AGPL 或使用 commercial license | [https://pymupdf.io/pymupdf](https://pymupdf.io/pymupdf)                                                                                      |
| GROBID                | 默认学术 PDF header / reference / full-text / coordinates / TEI 结构化抽取 | 默认结构化服务，Apache-2.0                         | [https://grobid.readthedocs.io/](https://grobid.readthedocs.io/) / [https://github.com/grobidOrg/grobid](https://github.com/grobidOrg/grobid) |
| pypdf                 | 极简 fallback / fixture metadata / page text 基础抽取                   | 非主路径 fallback，BSD-3-Clause                   | [https://pypdf.readthedocs.io/](https://pypdf.readthedocs.io/)                                                                                |
| Zotero PDF Reader     | 交互参考：页内高亮、批注跳回原文、阅读位置                         | 不作为运行时依赖；只借鉴交互                                     | [https://www.zotero.org/support/pdf_reader](https://www.zotero.org/support/pdf_reader)                                                        |
| Hypothesis            | 交互参考：文本锚点、PDF 批注和稳定定位                             | 不作为运行时依赖；只借鉴 selector / anchor 设计                  | [https://web.hypothes.is/help/annotations/](https://web.hypothes.is/help/annotations/)                                                        |


依赖合入原则：

- 默认依赖包含 PyMuPDF，默认部署包含 GROBID。
- 部署文档必须明确 PyMuPDF 的 AGPL / commercial dual licensing 边界。
- GROBID 服务不可用时不能阻断 PDF 导入，但页面需要显示结构化抽取降级 warning。
- 如果某个部署不能接受 PyMuPDF 许可，需要提供明确的替代构建方案；该方案不作为
  Paper Reading Studio v1 默认体验。

## 5. AI 策略

### 5.1 AI Actions

所有论文 AI 都走 AI Gateway，不在页面直接调用 provider SDK 或 `llm.chat`。

本阶段 actions：

- `research.paper_search_codex`
- `research.paper_translate`
- `research.paper_explain_selection`
- `research.paper_source_guide`
- `research.paper_qa`
- `research.paper_deep_read_codex`
- `research.paper_compare_codex`

暂时不启用：

- `research.paper_claim_extract`
- 任何 `research_claim_to_evidence_candidate` 路径。

不变量：

- 论文阅读类 AI prompt 只能使用传入的 source metadata、segments、chunks、annotations。
- 输出必须包含 `cited_segment_refs`、`cited_chunk_refs` 或 `cited_annotation_refs`；没有依据时返回 warning。
- AI 导读的每个重要条目应保存 page/segment refs，方便跳回 PDF。
- AI 运行 metadata 不保存完整 PDF 文本、完整翻译或完整 prompt。
- 翻译和导读都只是阅读材料，不修改 skill、goal、project 或 evidence。

### 5.2 长文本翻译

不把整篇论文一次性发给模型。流程：

```text
PDF
  -> pages
  -> segments
  -> token budget batching
  -> AI JSON translation rows
  -> source_hash check
  -> translations JSONL
  -> aligned UI
```

保存前校验：

- 输出 segment 数不能超过输入 segment。
- 每条 `segment_id` 必须来自输入。
- `source_hash` 必须匹配当前 segment。
- hash 不匹配时标记 stale，不覆盖旧翻译。
- 单 batch 失败不影响其他 batch。

### 5.3 论文导读

`Source Guide` 生成结构化论文导读，而不是默认生成聊天回答或审稿评分：

- one-sentence takeaway；
- TL;DR；
- problem / motivation；
- main contributions；
- method / architecture；
- datasets / experiment setup；
- results / metrics；
- limitations；
- useful definitions / terms；
- key equations / figures to inspect；
- open questions for my project；
- reading plan。

长论文使用 map-reduce：

1. 按 section 生成 section summaries。
2. whole-paper synthesis 只读取 section summaries 和 key segments。
3. 每条重要结论保存 page/segment refs。
4. 没有可靠依据时标记 `needs_review`，不显示成确定事实或零分。

用户操作：

- `Save as note` -> 写入 `research/notes/<source>.md`；
- `Create citations` -> 写入 `research/citations.yaml`；
- `Jump to source` -> 回到 PDF 页码、segment 或 rect。

本阶段不生成 claim，也不提供 evidence promotion。

### 5.4 AI 问答

v1 不引入向量数据库，使用本地 retrieval：

- query token overlap；
- section title boost；
- chunk / annotation boost；
- current page boost；
- recent reading boost。

回答必须带 segment、chunk 或 annotation refs。refs 为空时，UI 只显示 warning，
不把结果渲染为可信结论。

### 5.5 Codex Paper Search and Long-Task Guide

Codex 用于论文搜索、链接检查和长任务论文导读，不用于每次小段翻译。
论文阅读本阶段不使用 Codex 生成 Claim 或 Evidence。

## 6. Core API 设计

新增模块建议：

```text
src/nblane/core/research_papers/
```

主要 helper：

```python
def research_asset_root(profile: str) -> Path: ...
def import_paper_pdf(profile: str, source_id: str, file_bytes: bytes, filename: str, *, pdf_url: str = "") -> PaperAsset: ...
def download_paper_pdf(profile: str, source_id: str, pdf_url: str) -> PaperAsset: ...
def load_paper_pdf_bytes(profile: str, source_id: str) -> bytes: ...
def extract_paper_pages(profile: str, source_id: str, *, backend: str = "auto") -> list[PaperPage]: ...
def extract_paper_segments(profile: str, source_id: str, *, backend: str = "auto") -> list[PaperSegment]: ...
def auto_chunk_paper(profile: str, source_id: str, *, overwrite: bool = False) -> list[ResearchChunk]: ...
def search_papers(query: str, providers: tuple[str, ...], limit: int, filters: dict | None = None) -> list[PaperSearchResult]: ...
def search_papers_with_codex(profile: str, query: str, *, filters: dict | None = None, context_refs: dict | None = None) -> list[PaperSearchResult]: ...
def check_paper_links(results: list[PaperSearchResult]) -> list[PaperSearchResult]: ...
def import_paper_url(profile: str, url: str, options: dict) -> str: ...
def import_paper_search_results(profile: str, results: list[dict], selected_ids: list[str], options: dict) -> list[str]: ...
def load_paper_annotations(profile: str, source_id: str) -> list[PaperAnnotation]: ...
def save_paper_annotations(profile: str, source_id: str, rows: list[PaperAnnotation | dict]) -> Path: ...
def load_paper_translations(profile: str, source_id: str) -> list[PaperTranslation]: ...
def save_paper_translations(profile: str, source_id: str, rows: list[PaperTranslation | dict]) -> Path: ...
def format_research_citations(profile: str, refs: list[str], *, format: str) -> str: ...
```

GROBID adapter：

```python
def grobid_available() -> bool: ...
def process_grobid_fulltext(profile: str, source_id: str) -> GrobidDocument: ...
def grobid_tei_to_segments(source_id: str, tei_xml: str) -> list[PaperSegment]: ...
def grobid_tei_to_bibliography(source_id: str, tei_xml: str) -> list[ResearchCitation]: ...
```

PyMuPDF default adapter：

```python
def pymupdf_available() -> bool: ...
def extract_with_pymupdf(profile: str, source_id: str) -> PyMuPDFDocument: ...
def pymupdf_document_to_pages(source_id: str, doc: PyMuPDFDocument) -> list[PaperPage]: ...
def pymupdf_document_to_fallback_segments(source_id: str, doc: PyMuPDFDocument) -> list[PaperSegment]: ...
```

## 7. Reader Sidecar 事件协议

Reader 由 FastAPI sidecar 提供 `/reader/view/{source_id}` 主入口。`research_paper_reader_component/events.py`
是前后端事件常量的契约来源：

```text
src/nblane/research_paper_reader_component/events.py
```

Sidecar 前端通过 mutation/task endpoint 发送 event：

```json
{
  "action": "create_annotation",
  "payload": {
    "source_id": "source:...",
    "page": 3,
    "selected_text": "...",
    "rects": [],
    "color": "yellow",
    "note": ""
  }
}
```

支持 actions：

- `create_annotation`
- `update_annotation`
- `delete_annotation`
- `create_chunk_from_selection`
- `translate_selection`
- `translate_page`
- `translate_section`
- `translate_paper`
- `translate_all_missing`
- `explain_selection`
- `ask_paper`
- `generate_review_card`
- `save_progress`
- `create_citation_from_annotation`
- `jump_to_chunk`
- `set_reader_state`

FastAPI/core handler 负责：

- 校验 payload
- 调 core helper
- 调 AI Gateway
- 写文件
- 刷新 snapshots/cache

## 8. 实施阶段

开发顺序围绕单篇论文阅读闭环，不先扩展 Claim、Evidence 或多论文综合。

### Phase 0: 产品契约和边界冻结

- 更新 Research / Paper Library / Reader 的职责说明。
- 冻结多维状态：source、PDF、extraction、translation、guide、reading。
- 隐藏 Claims tab、Claim candidate、Evidence promotion 和技能关联入口。
- 保留 Notes、Annotations、Chunks、Citations。
- 定义 Reader URL 状态：`mode`、`page`、`section`、`anchor`。

验收：

- 页面上没有 Claim / Evidence 操作。
- 论文阅读不会修改 evidence-pool、skill-tree 或项目状态。
- 刷新和返回可以恢复阅读模式和页码。

### Phase 1: Research 研究台重组

- 将 ResearchPage 改成“继续阅读 / 待处理队列 / 论文库入口”。
- 论文卡片展示 PDF、抽取、翻译、导读、笔记、引用和上次阅读状态。
- 根据状态显示开始阅读、继续阅读、补齐翻译、生成导读等主动作。
- Paper Library 保留导入、搜索、主题树、标签和批量整理。
- Reader 只负责单篇论文阅读现场。

验收：

- 研究台不重复 Paper Library 的完整管理界面。
- 用户打开研究台能直接找到下一步动作。
- 缺 PDF 的论文不会显示 PDF ready 或进入 Reader。

### Phase 2: SPA Reader 外壳和两种主视图

- 以 `ResearchPage` 和 `PaperReaderPage` 作为唯一用户入口。
- 短期保留 FastAPI sidecar、PDF.js 和 Reader API，通过 `SidecarFrame` 承载现有阅读画布。
- 统一 SPA 与 sidecar 的导航、返回、标题、加载、错误反馈和状态栏。
- 让 URL 统一承载 `source_id`、`mode`、`page`、`section`、`anchor`，刷新和分享链接能恢复
  同一论文的阅读上下文。
- Reader 外层采用石雕星空风格，PDF 正文保持白纸高对比。
- 在现有 API 上实现“逐段阅读”和“原文对照”两个主视图，不重复建设数据写入逻辑。
- 目录、缩略图、搜索、页码、缩放和阅读进度在过渡期也必须回传到同一套 Reader 状态。
- 为后续 SPA 原生迁移拆出 PDF viewport、segment layer、translation popover、notes panel
  和 guide panel 的前端边界。

验收：

- 从 SPA ResearchPage 进入 PaperReaderPage 后，用户能看到论文标题、PDF/抽取/翻译/导读状态
  和明确的加载或失败反馈。
- iframe 内 PDF 页面仍然可读，外层视觉、返回和状态栏与 SPA 一致。
- 刷新 `?mode=translation&page=3&anchor=segment-42` 能恢复相同论文、模式、页码和锚点。
- 逐段阅读和原文对照有明确用途差异；桌面端双栏，移动端单栏降级。
- Reader API 或 iframe 加载失败时，SPA 显示可操作的错误状态和返回/重试入口。

### Phase 3: 段落翻译、选区翻译和阅读材料

- 使用现有 segment、rects 和 source hash 实现段落命中。
- 已缓存译文单击直接显示气泡。
- 未缓存段落先显示“翻译此段”操作。
- 拖选文字显示翻译、解释、笔记和引用工具条。
- 气泡不增加 PDF 横向宽度，空间不足时回退到侧栏或移动端底部抽屉。
- 保存笔记、Chunk 和 Citation，全部保留原文定位。
- 不显示 Claim 和 Evidence 操作。

验收：

- 点击段落可以翻译并回到原文定位。
- 选区翻译不会误触发段落点击。
- 笔记刷新后仍可跳回同一页和同一段。
- 坐标不可靠时提示拖选，不猜测段落。

### Phase 4: 论文概览和 AI 导读

- 首屏显示中文摘要、快速分析结果和继续阅读位置。
- 将 Analyze Paper 对用户命名为“快速分析”，将 Deep read 对用户命名为“深度研读”；Review 是结果承载区域，不再作为第三个 AI 动作。
- 导读按研究问题、方法、结果、局限和阅读计划组织。
- 每项重要结论带 page/segment refs，可跳回 PDF。
- 无可靠结果显示“待核对”或“未评估”，不显示误导性的零分。
- 允许保存为 reading note 或 citation，不写 Claim/Evidence。

验收：

- AI 导读中的依据可以跳回原文。
- 导读生成中、失败和待核对状态清晰可见。
- 没有来源的回答不会显示成确定结论。

### Phase 5: 任务恢复、抽取降级和跨页联动

- 翻译、抽取和导读显示阶段、进度、失败原因和重试入口。
- 页面刷新后重新计算已保存结果，不重复生成已有翻译。
- 服务重启后，已保存的翻译和导读不被误报为未完成。
- 显示 GROBID ready、PyMuPDF fallback、无坐标等抽取状态。
- Research、Reader、Paper Library 的缓存失效范围统一。

验收：

- 长任务不会让页面永久卡在 loading。
- 失败任务可以单独重试。
- 缺失资产、抽取失败和翻译失败有可操作提示。

### Phase 6: SPA 原生迁移、视觉、移动端和端到端验收

- 统一深色工作台、白色论文页、金色定位标记和状态颜色。
- 在 API 和 URL 契约稳定后，把目录、阅读区、段落翻译、对照、笔记和 AI 导读逐步迁入
  SPA 原生组件；每次迁移只替换一块 UI，不同时重做 PDF 渲染、后端任务和数据文件。
- 保留 sidecar HTML 作为兼容入口，直到 SPA 原生 Reader 覆盖主阅读路径。
- 完成桌面、窄屏、键盘导航和减少动效支持。
- 验收开发环境 `Attention Is All You Need` 完整阅读路径。
- 检查 SPA、Reader sidecar、PDF asset root、iframe 到原生页面的登录 handoff 和状态兼容。
- 更新部署和用户文档。

## 9. 开发范围说明

本阶段按顺序实现，不把多个研究域同时拆成并行大改：

- 先稳定 ResearchPage、Reader 外壳和单篇论文阅读闭环。
- Core 继续通过现有 `research_papers`、`reader_actions` 和文件写入模块工作。
- 当前前端主路径是 SPA 页面加 `src/nblane/web_reader_api/templates/index.html` 的 sidecar
  过渡组合；目标是迁移到 SPA 原生 Reader，期间保持 URL、API 和状态兼容。
- 不新建数据库，不迁移现有 PDF、translation、annotation、analysis 文件。
- 不把 Claim、Evidence、技能关联和公开成果作为本阶段交付内容。

## 10. Test Plan

### Core

- `tests/test_research_papers.py`
  - asset root default / env override。
  - PDF import 不写 profile Git 目录。
  - source metadata 写入 asset ref / sha256 / byte_size / page_count。
  - 非 PDF、path traversal、超限文件被拒绝。
  - PyMuPDF fixture 抽取 page text、page count 和坐标 fallback。
  - GROBID fixture TEI 解析为 segments / references / coordinates。
  - GROBID unavailable 时回退 PyMuPDF heuristic segments，并显示 warning。
  - annotations / translations / analysis / library tree round-trip。
  - BibTeX / Markdown export 稳定。

### Search

- 扩展 `tests/test_connectors.py`
  - arXiv 解析 `pdf_url/arxiv_id/categories`。
  - Semantic Scholar 解析 `doi/openAccessPdf/citationCount/venue/fieldsOfStudy`。
  - Codex search 输出必须包含 title、URL/DOI/provider refs、link check、warnings。
  - Codex search 不直接写 `research/sources.yaml`。
  - Codex unavailable 时回退 provider API。
  - search dry-run 不写文件。
  - URL / DOI import 能生成 metadata preview。
  - PDF upload 能写 external asset root，并拒绝非 PDF / path traversal。
  - import selected 去重并只写勾选项。
  - API key/token 不落盘。

### AI

- 扩展 `tests/test_ai_gateway.py`
  - 新 actions 注册。
  - `research.paper_search_codex` 只保存短 activity metadata。
  - long translation batch 输出 `segment_id/source_hash`。
  - hash mismatch 不覆盖旧翻译。
  - QA 无依据时不编造。
  - Codex deep read 只记录短 activity metadata。

### Workspace

- 扩展 `tests/test_research_workspace.py`
  - annotation -> chunk -> citation round-trip。
  - quote 在 chunk 中可校验通过。
  - quote 不匹配时保存 warning。
  - archived source 保留 PDF/annotations/chunks。
  - library node refs 断链产生诊断。
  - Reader 不会写入 claims 或 evidence。

### Public / Output

本阶段不测试论文阅读到 Claim/Evidence 的 promotion；保留现有公共发布测试，
确保论文阅读新增的 notes、translations、analysis 和 citations 不会绕过公共边界。

### Frontend

PDF Reader 不再构建 `research_paper_reader_component/frontend`。前端主路径在
`src/nblane/web_reader_api/templates/index.html`，PDF.js 资产打包在
`src/nblane/web_reader_api/static/assets/`。如需调试 legacy overlay，设置
`NBLANE_READER_DEBUG_OVERLAY=1` 后走 sidecar Reader。

JS tests：

- selection payload schema。
- rect normalization 和 segment 命中。
- 段落点击、气泡打开/关闭和选区操作互不误触发。
- annotation create/update/delete events。
- translation event carries segment/page/source hash。
- translate paper / all missing event 不直接携带全文，只携带 source_id、scope、stale/missing selector。
- citation、note、translation click 都能发出 jump event。
- Claims/Evidence 控件不渲染。

Playwright smoke：

- `ResearchPage -> PaperReaderPage -> sidecar iframe` 主路径可打开并显示加载、失败和重试状态。
- 从 ResearchPage 点击“继续阅读”后，PaperReaderPage 的 source、页码和模式与 API 一致。
- `?mode=translation&page=3&anchor=segment-42` 深链刷新后恢复同一阅读位置；原生 SPA Reader
  迁移后继续兼容同一 URL。
- Reader iframe 暂时不可用时，SPA 不会永久卡在 loading，能显示返回或重试入口。
- 打开 fixture PDF。
- 选择文本并高亮。
- 创建 annotation。
- 点击 annotation 跳页。
- 触发 translate/generate-guide event。
- 触发 translate paper 后生成分段任务状态，而不是阻塞 UI。

### Full Run

```bash
PYTHONPATH=src .venv/bin/python -m unittest \
  tests.test_research_sources \
  tests.test_research_workspace \
  tests.test_research_papers \
  tests.test_connectors \
  tests.test_ai_gateway \
  tests.test_public_site

PYTHONPATH=src .venv/bin/python -m py_compile \
  src/nblane/web_api/routes_v1.py \
  src/nblane/core/research_papers/__init__.py \
  src/nblane/core/reader_actions.py

git diff --check
```

## 11. Assumptions

- v1 做 PDF 高亮阅读器，但不做 OCR、公式结构化识别、表格完整复原、
  Zotero 双向同步、多人实时协作。
- PDF 二进制必须外置到 `NBLANE_RESEARCH_ASSET_ROOT`，不进入 profile Git。
- 批注、翻译、page text、segments、chunks、citations、analysis 和阅读笔记是轻量研究事实，可进入 profile 文件。
- 本阶段论文阅读不创建 Claim、不创建 Evidence、不修改 skill/goal/project 状态。
- Paper Search v1 推荐 Codex-first；Codex 不可用时回退 arXiv +
  Semantic Scholar provider search，再由 LLM 做轻量归一化。
- GROBID 是默认结构化抽取服务，Apache-2.0，适合学术 PDF 的结构化抽取。
- PyMuPDF 是默认本地 PDF backend；部署方需要接受 AGPL 或使用 commercial license。
- pypdf 不作为主路径默认后端，只保留为极简 fallback / fixture 选项。
- Codex 是论文搜索、链接检查和长任务论文导读 agent，不是普通 selection 翻译器。
- Claims、Evidence Review、技能关联、项目成果证明和多论文综合后置。
