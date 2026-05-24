---
status: active
owner: product
last_verified: 2026-05-24
source_of_truth: true
---

# Research 使用说明

Research 是外部资料的收件箱、论文阅读室和 source-aware claim 工作台。它的核心原则是：先把来源、摘录、引用和研究断言整理清楚，再把经过审阅的候选推进到 Evidence Review 或公开输出。

## 入口与端口

- Streamlit 主页面：`8501` 的 `Research`。
- Reader / Paper Library sidecar：`8502`，用于 PDF Reader、Paper Library standalone、长任务 job 状态和静态前端。
- 生产环境不要把 `8502` 当作 Research 的写入入口；保存 source、claim、citation、draft 的主入口仍在 `8501`。

## 页面结构

- `Overview`：研究中控台，展示阅读、解析、引用、隐私、导出等待处理队列。
- `Paper Library`：导入论文、补 PDF、打开 Reader、运行结构化解析、翻译、标注和生成论文 claim。
- `Claims & Citations`：审阅 research claims、citations，并把确认过的候选推进到 evidence。
- `Synthesis / Export`：把已审阅 claims 组织成综合草稿、博客候选或项目更新候选。
- `Inbox & Connectors`：手动添加 source、预览 evidence candidate、配置连接器发现。连接器配置不保存 token、cookie 或 API key。

## 推荐流程

1. 在 `Overview` 看下一步动作，优先处理 PDF 缺失、结构化解析、引用断裂和隐私风险。
2. 在 `Paper Library` 导入论文或外部来源。PDF 就绪后打开 Reader。
3. 在 Reader 中运行解析、翻译、可见页翻译、全文翻译、标注、chunk 和 paper claim。
4. 回到 `Claims & Citations` 审阅断言和引用，修复 quote warning。
5. 确认可信后，推进到 Evidence Review 或生成 synthesis/export 候选。

## Research AI 配置

右上角 `研究 AI` 只影响 Research 里的论文与 Reader 动作：

- Paper search
- Paper translation / Reader translation
- Paper review card
- Source guide
- Paper Q&A
- Claim extraction
- Deep read
- Paper compare

看板和 Evidence Review 的 AI 配置不在这里，避免不同页面互相覆盖。

## GROBID 与坐标

GROBID 负责结构化学术 PDF。某些 PDF 会返回结构化文本但不返回 segment 级坐标。此时 Reader 会优先使用 layout-grounded structure anchors；如果也没有可用结构锚点，才退回页级定位。这个 warning 通常不是部署失败，而是该 PDF/GROBID 组合缺少细粒度坐标。

## 全文翻译

Reader 的 Full translation 默认走结构单元，适合论文长文。生产环境如果使用 SOCKS 代理，必须安装 `httpx[socks]`，否则会出现 `socksio` 缺失错误。部署更新后运行：

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python - <<'PY'
import socksio
print("socksio ok")
PY
```
