# Reader 打磨计划

## 背景

Reader 功能已基本完整（PDF 渲染、GROBID 结构化分段、翻译覆盖层、导航、深读、标注），现阶段目标是消除已知 bug、改善用户感知体验、提升可观测性。

## 实施状态

全部 12 项已完成。下方逐项保留实施摘要，方便回查。

---

## P0 — 用户直接感知的体验问题

### 1. GROBID 降级提示被误渲染为 Warning  ✅ 已完成

**改动摘要：**
- [src/nblane/core/research_papers/__init__.py](src/nblane/core/research_papers/__init__.py) 拆分了 `structured_extraction_warnings`（真正的告警）与新增的 `structured_extraction_notices`（中性的降级提示），同时新增 `reading_artifacts_notices`、`grobid_last_error_detail`、`structured_extraction_error_detail` 等用于诊断的明细字段；
- [paper_reader.py:957-965](src/nblane/research_ui/paper_reader.py#L957-L965)、[paper_library.py:626-666](src/nblane/research_ui/paper_library.py#L626-L666)、[paper_library.py:1383-1391](src/nblane/research_ui/paper_library.py#L1383-L1391) 改为对 notices 用 `st.info`，对 warnings 保留 `st.warning`；
- 文案统一改为中文，并明确标注「已自动处理，无需操作」。

**文件：** `src/nblane/core/research_papers/__init__.py:1424-1425`  
`src/nblane/research_ui/paper_reader.py:957-961`  
`src/nblane/research_ui/paper_library.py:628-657`

**问题：** "GROBID returned structured text without segment coordinates; Reader will use layout-grounded structure anchors…" 是一条中性的降级通知，但被存入 `structured_extraction_warnings` 后，UI 用 `st.warning` 渲染，给用户的观感像是出了错误。

**方案：**
- 在 metadata 里新增 `structured_extraction_notices` 键，存放"已自动降级、无需用户处理"的提示；
- UI 对 notices 用 `st.info` 渲染，对真正的 warnings 保留 `st.warning`；
- 同时把 `f"GROBID extraction failed: {exc}"` 的原始异常文本抹掉，改为"结构化提取遇到问题，已自动切换到文本降级方案"。

---

### 2. 页面加载失败无视觉反馈  ✅ 已完成

**改动摘要：**
- [index.html](src/nblane/web_reader_api/templates/index.html) 中 `showPageError` 新增页面级浮层（CSS 类 `pr-page-error`）：失败页右上角显示「页码 + 错误简述 + 重试按钮」，长文本以 `…` 截断，`title` 内挂完整原文；
- 新增 `clearPageError` / `retryPageRender`，渲染成功或进入 preview 时自动清除浮层；
- 重试按钮调用 `ensurePageRendered(page, { force: true })`。

**文件：** `src/nblane/web_reader_api/templates/index.html:5604-5606`

**问题：** `showPageError` 只把错误消息推到顶部状态栏，用户滚动后就再也看不到哪一页失败了。

**方案：**
- 在失败的 page 容器上覆盖一个简短的错误提示块（"第 N 页加载失败"）；
- 提示块内附一个"重试"按钮，点击后重新触发该页的渲染流程。

---

### 3. Bulk 翻译合并失败静默  ✅ 已完成

**改动摘要：**
- `mergeBulkTranslationsIntoArgs` 出错时清空 `bulkTranslations` / `bulkTranslationsEtag`，触发 `status(label("translation_sync_failed"))` 顶部状态条提示；
- 调度 `scheduleBulkTranslationsFetch(120, { force: true, skipCache: true })` 强制下次重新拉取，避免长期使用过期缓存；
- 新增 `translation_sync_failed` i18n 键（中英文）。

**文件：** `src/nblane/web_reader_api/templates/index.html:1722-1755`

**问题：** `mergeBulkTranslationsIntoArgs` 的 catch 块静默吞错，合并失败时翻译面板保留旧数据但不提示用户。

**方案：**
- catch 块内显示一个短暂的吐司提示（"翻译数据同步失败，请刷新"）；
- 同时将 `bulkTranslationsEtag` 置空，下次轮询时强制重拉。

---

### 4. Fallback 锚点键冲突  ✅ 已完成

**改动摘要：**
- `translationUnits` 在 fallback 模式下生成 anchor key 时把段落 `obj.order`（或数组 index 兜底）并入键，格式从 `${page}:${text.slice(0,16)}` 改为 `${page}:${order}:${text.slice(0,16)}`；
- 同页两段开头相同的文本不再共用同一锚点。

**文件：** `src/nblane/web_reader_api/templates/index.html:2891-2892`

**问题：** 当 GROBID 没有返回坐标时，fallback 锚点键为 `${page}:${text.slice(0,16)}`。同一页内两段开头相同的文本会产生键冲突，导致翻译覆盖层定位到错误的段落。

**方案：**
- 将 `obj.order`（段落序号）并入键：`${page}:${order}:${text.slice(0,16)}`；
- 若 order 为空则用段落在数组中的 index 兜底。

---

### 5. 缺少键盘快捷键  ✅ 已完成

**实现键位：**

| 快捷键 | 动作 |
|--------|------|
| `ArrowLeft` / `PageUp` / `[` | 上一页 |
| `ArrowRight` / `PageDown` / `]` | 下一页 |
| `+` / `=` | 放大 |
| `-` / `_` | 缩小 |
| `0` | 适应宽度 |
| `/` | 聚焦搜索框 |
| `Esc` | 关闭浮层（保持原有） |

输入框 / textarea 中按键会被忽略；`/` 在表单元素外按下时聚焦搜索框；带 `Ctrl` / `Cmd` / `Alt` 修饰键时让浏览器自身处理。

**文件：** `src/nblane/web_reader_api/templates/index.html`（当前只绑了 Esc）

**问题：** 键盘用户无法高效操作 Reader，常用动作全靠鼠标。

**方案（最小集）：**

| 快捷键 | 动作 |
|--------|------|
| `ArrowLeft` / `ArrowRight` 或 `[` / `]` | 上一页 / 下一页 |
| `+` / `-` | 放大 / 缩小 |
| `/` | 聚焦搜索框 |
| `Esc` | 关闭浮层（已有） |

---

## P1 — 一致性 / 可观测性

### 6. 34 处静默 catch 缺少日志  ✅ 已完成

**改动摘要：**
关键路径加上 `console.warn(..., error)`：
- `fetchTranslationsBulk` 网络异常；
- `readTranslationsCache` / `writeTranslationsCache` IndexedDB 异常；
- `mergeBulkTranslationsIntoArgs` 合并异常；
- `EventSource` 初始化失败回退到 polling。

其余 UI 装饰性的 try/catch（如 `refreshLeftRail`）保持原样，避免噪音。

**文件：** `src/nblane/web_reader_api/templates/index.html`（`} catch {}` 共 34 处）

**方案：** 挑出涉及网络请求、IndexedDB 缓存、本地存储的 catch 块，改为 `catch (e) { console.warn(..., e); }`，方便线上排查。不需要全改，优先改以下几类：
- `fetchTranslationsBulk` 的网络 catch；
- `readTranslationsCache` / `writeTranslationsCache` 的存储 catch；
- `loadReaderPayload` 的初始化 catch。

---

### 7. `_json_body` 吞掉 400 错误  ✅ 已完成

**改动摘要：**
- 重写 `_json_body`：空 body 仍然返回 `{}`；解析失败时直接 raise `HTTPException(status_code=400, detail="invalid request body")`，不再返回伪造的空字典；
- 客户端可以拿到清晰的 400 错误来排查。

**文件：** `src/nblane/web_reader_api/__init__.py:426-437`

**问题：** 请求体 JSON 解析失败时静默返回 `{}`，调用方拿到空字典还要再判断，且客户端收不到任何错误信号。

**方案：** 解析失败时 raise `HTTPException(status_code=400, detail="invalid request body")`，由路由层统一处理。

---

### 8. 任务轮询无退避  ✅ 已完成

**改动摘要：**
- 新增模块级 `activeTaskStartedAt` 与 `readerPollDelayMs()` 函数；
- 阶梯退避：< 30s → 1s；30–120s → 3s；> 120s → 5s；
- `watchReaderTask` / `pollReaderTask` 全部改用 `readerPollDelayMs()`，避免长任务期间持续按 750ms 打后端；
- `stopTaskWatchers` 重置 `activeTaskStartedAt`，确保下一次任务从头开始计时。

**文件：** `src/nblane/web_reader_api/templates/index.html`（轮询间隔约 2500ms / 750ms 固定值）

**问题：** 全文翻译等长任务期间，前端以固定间隔持续打后端。

**方案：** 改为阶梯退避：
- 0–30s：每 1s 轮询一次；
- 30–120s：每 3s；
- 120s 以上：每 5s；
- 任务完成或失败后立即停止。

---

### 9. PyMuPDF 精修失败不可见  ✅ 已完成

**改动摘要：**
- PyMuPDF 异常被收集到 metadata：`page_refinement_failed_at`（时间戳）+ `page_refinement_error_detail`（原始堆栈，仅诊断使用，不展示给用户）；
- 用户侧仅看到中性 notice「PDF 页面精修未完成，已使用 GROBID 原始坐标」。

**文件：** `src/nblane/core/research_papers/__init__.py:1145-1154`

**问题：** PyMuPDF 页文本精修异常被吞，段落坐标可能仍是旧的，但 metadata 里没有任何记录。

**方案：** 失败时在 metadata 里写入 `page_refinement_failed_at` 和 `page_refinement_error`，让上层诊断可见。

---

## P2 — 视觉 / 响应式

### 10. iframe 高度写死  ✅ 已完成

**改动摘要：**
- [paper_reader.py:976-980](src/nblane/research_ui/paper_reader.py#L976-L980) 将 iframe 高度改为环境变量 `NBLANE_READER_IFRAME_HEIGHT` 控制（默认 1200，最小 640）；
- 部署时可按目标设备改写，例如小屏窗口设为 800、超大屏设为 1500。

**文件：** `src/nblane/research_ui/paper_reader.py:973`

**问题：** `height=1200` 在小屏上会出现两层滚动条，体验差。

**方案：** 改为动态高度（如 `height=max(800, screen_height - 200)`），或通过 JS postMessage 让 iframe 上报自身内容高度后动态调整。

---

### 11. 模式切换不保留滚动位置  ✅ 已完成

**改动摘要：**
- `setReaderMode` 切换前抓取 `currentPage` 作为 `anchorPage`；
- 切换后调用 `scrollToPage(anchorPage, { smooth: false })` 即时滚回原页码；
- pdf / compare / translation 模式互切体验连贯。

**文件：** `src/nblane/web_reader_api/templates/index.html`（`readerMode` 切换逻辑）

**问题：** 在 `pdf` / `compare` / `translation` 三种模式间切换时，滚动位置重置到顶部，长文档体验割裂。

**方案：** 切换前记录 `currentPage`，切换后恢复到同一页。

---

### 12. 错误文案泄露技术细节  ✅ 已完成

**改动摘要：**
- 用户可见的 warning / notice 文案改为统一中文短句（如「结构化提取遇到问题，已自动切换到文本降级方案」）；
- 原始异常堆栈写入 `grobid_last_error_detail` / `structured_extraction_error_detail` / `page_refinement_error_detail`，仅作诊断字段保存，UI 层不渲染；
- `_metadata_has_recent_grobid_failure` 同时识别中英文标记 + `grobid_last_error_detail`，cooldown 仍然有效。

**文件：** `src/nblane/core/research_papers/__init__.py:1176`

**问题：** `f"GROBID extraction failed: {exc}"` 把原始异常（可能含路径、堆栈片段）直接存入 metadata 并展示给用户。

**方案：** 用户侧只展示"结构化提取遇到问题，已切换到文本降级方案"；原始 `exc` 写入日志或单独的 `grobid_last_error_detail` 键（不在 UI 展示）。

---

## 实施顺序

P0 + P1 + P2 全部完成。一次性合并即可，不需要分轮。

---

## 测试记录

- `pytest tests/test_research_papers.py` → 90 passed
- `pytest tests/test_reader_actions.py tests/test_reader_tasks.py tests/test_web_reader_api.py tests/test_research_paper_reader_component.py` → 60 passed
- 全量 `pytest tests/`（除三个慢测试） → 540 passed, 11 subtests passed

需要在浏览器层面手工验证的场景：
- 断网下打开 Reader，确认失败页有覆盖提示和重试按钮（P0.2）
- DevTools 中 mock `/translations/bulk` 返回 500，确认顶部状态条出现"翻译数据同步失败，正在重新拉取..."（P0.3）
- 用键盘完成翻页 / 缩放 / 搜索 / 关闭浮层全流程（P0.5）
- 触发全文翻译，在 Network 面板观察轮询间隔随时间从 1s → 3s → 5s（P1.8）
- 设置 `NBLANE_READER_IFRAME_HEIGHT=800` 后重启，iframe 高度生效（P2.10）
- pdf / compare / translation 模式互切，滚动位置保持在同一页（P2.11）

---

## 验证方式

- **P0.1（GROBID 提示）：** 用一篇 GROBID 无坐标的 PDF 走完 prepare_reading_artifacts 流程，确认 UI 显示 `st.info` 而非 `st.warning`。
- **P0.2（页面错误）：** 断网后打开 Reader，确认失败页上有覆盖提示和重试按钮。
- **P0.3（翻译合并）：** 在 DevTools 中 mock `/translations/bulk` 返回 500，确认出现吐司提示。
- **P0.4（锚点键）：** 构造同页开头相同的两段文本，确认翻译覆盖层分别定位到正确段落。
- **P0.5（键盘）：** 打开 Reader，用键盘完成翻页、缩放、搜索全流程。
- **P1.8（退避）：** 触发全文翻译，在 DevTools Network 面板确认轮询间隔随时间增大。
