---
status: active
owner: product
last_verified: 2026-10-06
source_of_truth: true
---

# Research 使用说明

Research 是外部资料的收件箱、论文库和阅读室。日常入口全部在 SPA；Streamlit 的 `Research`
页面正在下线，不再新增功能。论文阅读材料（笔记、翻译、分析）不会自动变成 Claim 或 Evidence，
SPA 暂不提供这两类入口。

## 入口与端口

| 页面 | SPA 路由 | 说明 |
| --- | --- | --- |
| 研究台 | `/p/<name>/research` | 继续阅读、阅读队列、最近读过、论文索引（翻译与快速分析状态）。 |
| 论文库 | `/p/<name>/research/library` | 内嵌 sidecar 论文库（`embed=1&ui_lang=zh`）：导入、目录树、批量操作、导出。 |
| 论文概览 | `/p/<name>/research/papers/<id>` | 单篇论文起始页：摘要与译文、阅读/翻译进度、最近笔记、快速分析与深度研读结果。 |
| 阅读器 | `/p/<name>/research/papers/<id>/read` | 内嵌 sidecar Reader；`?mode=compare|translation&page=N` 可直达。 |
| 研究来源 | `/p/<name>/research/sources` | 来源收件箱、手动添加来源、连接器（`?tab=connectors`）、研究 AI 配置（`?tab=ai`）。 |

- SPA 后端：`8504`（隔离开发 `18504`）。Reader / Paper Library sidecar：`8502`（隔离 `18502`），
  只通过 SPA 内嵌访问；生产不要把 sidecar 端口直接暴露。
- 论文库里点「打开阅读器」会通过 `postMessage({type: "nblane.library.open_reader"})` 通知 SPA，
  跳到论文概览页，不再打开裸 sidecar 标签页。

## 推荐流程

1. 在「研究来源」添加来源或配置连接器（arXiv / Semantic Scholar / GitHub 等，配置不保存 token、cookie 或 API key），
   预览后选择导入。
2. 在「论文库」整理目录、补 PDF。导入框接受论文链接、裸 DOI（`10.xxxx/...`、`doi:...`）和
   arXiv ID（`2407.08693`、`arXiv:2407.08693v2`、`hep-th/9901001`）。
3. 打开「论文概览」先跑「快速分析」，判断是否值得细读；需要时再启动「深度研读」（耗时数分钟，需 Codex CLI）。
   模型失败时不会覆盖已有分析结果，页面会提示重试。
4. 进入「阅读器」逐段阅读：单击段落看段落译文，双击单词查词，拖选文字出现选区工具条；
   `Ctrl/Cmd+F` 全文搜索，参考文献 / 图表链接可悬停预览、点击跳转，`Alt+←` 返回；`?` 查看全部快捷键。
5. 在论文库勾选论文「导出所选」，或在详情抽屉「导出引用」，得到 BibTeX / RIS / CSL-JSON / Markdown。
   引用键（如 `vaswani2017attention`）首次导出时写入来源元数据，之后保持不变。

## Research AI 配置

「研究来源 → 研究 AI」只影响 Research 里的论文与 Reader 动作（论文搜索、翻译、快速分析、导读、问答、
深度研读、论文对比），存放在 `web-preferences.yaml` 的 `ai.actions.research.*`。看板和证据的 AI 配置不在这里。

## 本地翻译模型

管理员可以在服务器上装一个开源翻译模型，让选区和当前页翻译不再消耗 LLM 额度。没装时一切照旧走 AI 连接。

**安装（只需管理员，无需命令行）**：SPA「设置 → 本地翻译模型」，选一档点「安装」，完成后点「启用」，再用页面下方的「试译」确认效果。

| 档位 | 模型 | 文件 | 运行内存 | 适用 |
| --- | --- | --- | --- | --- |
| 适配当前服务器 | Hy-MT2 1.8B Q4_K_M | 1.13 GB | 约 2.1 GB | 2 核 4 GB；段落 5–9 秒 |
| 高质量 | Hy-MT2 7B Q4_K_M | 4.62 GB | 约 5.6 GB | 8 GB 以上内存 |

两档都是腾讯混元 Hy-MT2（Apache-2.0）。内存不够的档位会显示原因并禁止安装；服务器升级后同一页面即可安装 7B 并切换。

**谁用本地模型**：每个档案在「设置 → AI 路由 → 论文翻译分工」按范围选择「本地模型 / AI」。默认选区和当前页用本地模型，全文用 AI（1.8B 翻整篇太慢）。本地模型失败时自动改用 AI；单词始终先查本地词典。Reader 里本地模型的译文标「本地模型翻译」。

**内存**：模型服务不常驻，第一次翻译时自动启动，空闲 5 分钟后释放内存，再次使用约 3 秒唤醒。部署细节见 [腾讯云部署 · 本地翻译模型](deployment-tencent-cloud.md#本地翻译模型)。

## GROBID 与坐标

GROBID 负责结构化学术 PDF。某些 PDF 会返回结构化文本但不返回 segment 级坐标。此时 Reader 会优先使用 layout-grounded structure anchors；如果也没有可用结构锚点，才退回页级定位。这个 warning 通常不是部署失败，而是该 PDF/GROBID 组合缺少细粒度坐标。

## 全文翻译

Reader 的「全文翻译」默认走结构单元，适合论文长文。生产环境如果使用 SOCKS 代理，必须安装 `httpx[socks]`，否则会出现 `socksio` 缺失错误。部署更新后运行：

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python - <<'PY'
import socksio
print("socksio ok")
PY
```
