---

## status: draft
owner: product
last_verified: 2026-05-19
source_of_truth: true

# Paper Reading Studio 开发文档

本文定义 Research Workspace 中论文阅读能力的产品目标、页面组织、数据契约、
AI 行为、第三方库选择、后端抽取策略和测试计划。它是后续实现
`Paper Reading Studio` 的开发交接文档。

## 1. 目标

Research 当前已有 Source Inbox、Reading Room、Claims & Citations、
Synthesis Drafts 和 Connectors，但论文阅读仍停留在“导入 source + 粘贴
excerpt + 生成草稿”的形态。目标是打通完整论文阅读闭环：

```text
按主题搜索论文
  -> 选择导入
  -> PDF 私有保存
  -> PDF 高亮阅读
  -> 原文 / 中文翻译对齐
  -> 批注 / 摘录 / chunk
  -> AI 总结 / 解释 / 问答 / 深读
  -> research claim / citation
  -> BibTeX / Markdown 引用导出
  -> Evidence Review / Output Studio 上游
```

核心原则：

- `Paper Source` 说明读了什么。
- `Annotation / Chunk` 说明哪里值得引用。
- `Research Claim` 说明这篇论文支撑了什么判断。
- 论文阅读产生的 `Evidence` 默认是非常弱的 evidence：它证明“我读过、
摘录过、理解过、引用过某篇论文”，但不直接证明“我做成了某个项目结果”。
- 论文阅读产生的 `Research Claim` 更适合成为 blog 读后感、文献综述、
learning note、项目背景分析的素材；只有经过 Evidence Review / Claim Studio
重新审查、连接到真实 project / goal / skill 事实后，才可能成为更强的
accepted claim。
- `Evidence / Accepted Claim / Output` 才进入对外表达；其中读论文 evidence
在公开表达里应该被标记为阅读/引用来源，而不是成果证明。
- PDF 原件不进 Git；批注、翻译、摘要、claim、citation 进 profile，便于迁移。
- AI 只产出 candidate；用户接受后才写 Research facts。

## 2. 产品形态

Research 顶层仍是一个页面，不新增顶层导航。内部改成类似 Output Studio 的
小页面结构：

```text
Research
  Overview
  Paper Library
    Find / Import Papers
    Collections
    Work Queue
  Reader
  Claims & Citations
  Synthesis / Export
  Advanced Connectors
```

### 2.1 Overview

首屏回答“当前有哪些论文需要处理”：

- papers total
- reading / annotated / candidate ready / archived 数量
- ready research claims / promoted research claims
- private / public sources 数量
- 最近阅读论文
- 需要处理的 AI candidates
- citation 断链、private publish risk、stale translation warning

这些指标不是装饰性统计，而是论文阅读工作流的导航器：


| 指标                        | 含义                                                                                                                         | 主要用途                              |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------- | --------------------------------- |
| papers total              | 当前 profile 中 `kind: paper` 的 source 总数，不包含普通网页、书籍、访谈、博客等非论文 source。                                                        | 给用户资料库规模感。                        |
| reading                   | 正在阅读中的论文，通常已经导入或打开过 Reader，但还没有完成批注、整理或归档。                                                                                 | 帮用户继续未完成阅读。                       |
| annotated                 | 已产生高亮、批注、摘录或 chunk 的论文。                                                                                                    | 找出“已经读出东西，但还没沉淀”的论文。              |
| candidate ready           | 已有可审核 AI / research candidate 的论文，例如 claim candidate、citation candidate、source guide、summary、evidence promotion candidate。 | 把用户带到人工审核队列。                      |
| archived                  | 阶段性处理完或暂时不再处理的论文。归档不删除 PDF、批注、claim 或 citation。                                                                            | 控制主阅读队列噪音。                        |
| ready research claims     | Research 层已经准备好审核或复用的 source-aware claims。                                                                                 | 用于读后感、文献综述、blog draft、项目背景分析的素材池。 |
| promoted research claims  | 已从 Research 层提升到 Evidence Review / Claim Studio / Output Studio 上游的 claims。                                                | 表示该论文观点已经进入更正式的证据或表达链路。           |
| private / public sources  | 按 `visibility` 统计 private 和 public paper sources。                                                                          | 判断哪些材料能用于公开输出，哪些只能私下使用。           |
| 最近阅读论文                    | 最近打开、批注、翻译、总结或编辑过的论文。                                                                                                      | 一键回到上次阅读位置。                       |
| 需要处理的 AI candidates       | AI 生成但尚未接受/丢弃的候选项。AI 输出不自动成为事实。                                                                                            | 防止 AI 结果散落在各处无人审核。                |
| citation 断链               | citation 指向的 source、chunk、annotation、quote 不存在或校验失败。                                                                       | 确保引用能追溯回原文。                       |
| private publish risk      | 准备公开的 output / claim / citation 引用了 private source。                                                                        | 阻止把私有材料误带进公开输出。                   |
| stale translation warning | 翻译保存时的 `source_hash` 和当前 segment hash 不一致。                                                                                 | 提醒重新翻译或人工确认原文/中文是否仍然对应。           |


Overview 推荐分成三块：

```text
Reading Pipeline
  papers total / reading / annotated / candidate ready / archived / 最近阅读论文

Review Queue
  ready research claims / promoted research claims / AI candidates

Integrity & Publish Safety
  private-public sources / citation 断链 / private publish risk / stale translation warning
```

证据强度提示：

- `annotated` 和 `candidate ready` 不等于项目 evidence 已经成立。
- 从论文阅读生成的 evidence 主要证明阅读行为、引用依据和理解过程，是弱证据。
- Blog 读后感可以直接消费 ready/promoted research claims，但 resume bullet、
public project proof、goal progress 不应该只依赖论文阅读 evidence。
- 如果一个 claim 要支撑项目能力或目标进展，必须再连接真实 project evidence，
例如代码提交、实验结果、上线记录、用户反馈、项目复盘等。

Overview 不提供复杂编辑表单，只提供进入主流程的快捷入口：

- Find papers in Library
- Open Library
- Continue reading
- Review claims
- Export citations

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
- `Analyze Paper`，在用户需要结构化阅读报告、深度阅读计划或项目相关性分析时触发。

### 2.3 Paper Library

Paper Library 是论文资料库，也是 **Paper Search 和 Reader 之间的桥梁**。
它应该首先是一个 **主题树**，而不是一组状态列表：用户按主题、问题域和研究方向
组织论文；`inbox / reading / annotated / candidate ready / archived` 这些只是
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
    Candidate Ready
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
| status | inbox / reading / annotated / candidate_ready / archived / discarded | 否，只用于筛选和队列。 |
| tags | memory、perception、benchmark、survey | 否，只用于横向检索。 |
| project_refs | 某个项目 case id | 否，只说明论文和项目相关。 |
| goal_refs | 某个目标 id | 否，只说明论文服务哪个目标。 |
| PDF asset | `papers/<sha>-title.pdf` | 否，只是外置文件引用。 |
| extraction state | PyMuPDF / GROBID / needs extraction | 否，只是处理状态。 |
| reading state | annotations、chunks、translations、claims、citations | 否，只是阅读沉淀状态。 |
| library_node_refs | `paper-node:vla-memory` | 是，决定论文在树上的位置。 |

这能避免资料库变成很多互相冲突的“状态文件夹”。例如同一篇论文可以同时：

- 位于 `VLA / Memory`。
- 状态是 `reading`。
- 带有 `perception` tag。
- 关联 `project:vla-memory-module`。
- 有 PDF asset。
- 有 12 条 annotations 和 3 条 claim candidates。

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
derived state，例如 `annotated`、`candidate ready`、`stale translation`、
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
| Candidate Ready | 有 AI / research candidates 等待处理的 paper。 | 进入审核队列。 |
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
- claims count
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
| chunks count | 可引用摘录数量，表示是否可进入 claim/citation 工作流。 |
| claims count | research claims 数量，表示是否可用于读后感、文献综述或 Evidence Review 上游。 |
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
- `AI candidates`
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
- synthesis status：research claims、citations、promoted status、exports。
- risks：private publish risk、citation 断链、stale translation、duplicate conflict。
- actions：Open Reader、Move in Tree、Run extraction、Analyze Paper、Archive、Discard。

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
| archive | 把所选论文状态改为 `archived`，保留树位置、PDF、批注、翻译、claims、citations。 |
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

Reader 是核心体验，目标接近 Zotero PDF Reader 的“页面内高亮、批注、note
可回到原文位置”，但保持 nblane 的 candidate-first 写入边界。
它需要同时支持两类读者：

- 快速扫读者：想快速知道论文讲什么、值不值得继续读。
- 深度阅读者：需要中英文对照、批注、引用、claim、和项目相关性分析。

推荐布局：

```text
┌─────────────────────────────────────────────────────────────┐
│ Toolbar: Paper / page / zoom / search / highlight / AI mode │
├──────────────┬─────────────────────────────┬────────────────┤
│ Paper list   │ PDF.js page viewer          │ Notes          │
│ TOC          │ text selection              │ Translation    │
│ Page thumbs  │ highlights / anchors        │ AI             │
│ Sections     │                             │ Claims         │
└──────────────┴─────────────────────────────┴────────────────┘
```

中间 PDF 区：

- PDF.js 渲染 PDF 页面。
- 支持 page jump、zoom、text search。
- 支持文字选择、rects、高亮颜色。
- 高亮不写回 PDF 文件，只写 `research/annotations/*.jsonl`。
- 点击 annotation / chunk / citation 可以跳回页码和高亮位置。

右栏 tabs：

- `Notes`
  - 当前论文批注列表。
  - 支持新建 note、编辑 note、按 tag/filter 展示。
- `Translation`
  - 原文段落与中文翻译对齐。
  - 支持 translate selection / page / section / paper / all missing。
- `AI`
  - Explain selection
  - Ask paper
  - Source guide
  - Codex deep read
- `Claims`
  - 当前论文的 claim candidates。
  - 当前论文已保存 research claims / citations。

选择文本后的浮动工具条：

- Highlight
- Annotate
- Translate
- Explain
- Create Chunk
- Create Citation
- Ask AI about this

组件不可用或没有 PDF 时，Reader 降级为 Streamlit 文本模式：

- page text list
- segment list
- annotation list
- translate/analyze buttons

#### 2.4.1 中英文对照和全文翻译

Reader 必须支持中英文对照和全文翻译，但实现方式不是把整篇论文一次性发给模型。
全文翻译是一个“分段、缓存、可追溯”的阅读能力：

```text
PDF / GROBID TEI
  -> pages
  -> sections
  -> segments
  -> batch translation
  -> translations JSONL
  -> bilingual aligned reader
```

支持的翻译粒度：

| 功能 | 作用 | 适合场景 |
| --- | --- | --- |
| Translate selection | 只翻译当前选中的一句或一段。 | 精读某个难句、公式解释附近文字、定义句。 |
| Translate paragraph / segment | 翻译当前结构化段落。 | 中英文逐段对照阅读。 |
| Translate page | 翻译当前页的所有 segments。 | 按页推进阅读。 |
| Translate section | 翻译 Introduction / Method / Experiments 等章节。 | 重点读某一节。 |
| Translate paper | 为整篇论文创建翻译任务。 | 准备完整中文对照阅读。 |
| Translate all missing | 只翻译还没有翻译或已经 stale 的 segments。 | 增量补全，不浪费 token。 |

中英文对照 UI：

- 左侧保持 PDF 原文或 extracted text。
- 右侧显示中文翻译，按 segment 对齐。
- 每个中文段落显示 locator，例如 `p. 3 § Method`。
- 鼠标 hover 原文段落时，高亮对应中文。
- 点击中文段落时，PDF 跳回对应页码和 rect。
- 翻译旁显示状态：`translated`、`missing`、`stale`、`failed`。
- stale 翻译不覆盖旧内容，但提示用户重新翻译。

全文翻译的边界：

- 不把整篇论文一次性发给模型。
- 不把完整翻译写入 Agent Activity。
- 不覆盖原文。
- 不修改 PDF 文件。
- 每条翻译必须绑定 `segment_id` 和 `source_hash`。
- GROBID 结构化抽取可用时，优先按 section / paragraph 对齐。
- GROBID 不可用时，退化为 PyMuPDF page text / heuristic segment 对齐。

这样读者可以先全文机器翻译建立整体理解，再回到 PDF 原文逐段核对。系统要始终让用户
知道“这段中文对应哪一段原文”，避免翻译变成不可追溯的独立文本。

#### 2.4.2 Reader 功能清单

Reader 面向读者提供这些核心功能：

| 功能 | 读者收益 |
| --- | --- |
| PDF 阅读 | 不离开 nblane 就能打开论文，保留页码、缩放、搜索和阅读位置。 |
| TOC / sections | 快速跳到 Abstract、Introduction、Method、Experiments、Conclusion。 |
| 页面缩略图 | 快速定位图表、实验结果和附录。 |
| 文本搜索 | 在全文中查关键词，例如 `memory`、`benchmark`、`ablation`。 |
| 中英文对照 | 英文原文和中文翻译并排，降低阅读门槛。 |
| 全文翻译 | 对整篇论文创建增量翻译缓存，后续打开不需要重新翻。 |
| 选区解释 | 对难句、术语、公式附近文本进行局部解释。 |
| 高亮批注 | 把重要句子变成可回溯 annotation。 |
| Chunk 创建 | 把可引用段落沉淀为 research chunk。 |
| Citation 创建 | 从选区或 chunk 生成带 locator 的 citation。 |
| Ask Paper | 针对当前论文问答，答案必须带 segment / chunk / annotation refs。 |
| Analyze Paper | 生成结构化阅读报告、评分、项目相关性和下一步阅读建议。 |
| Claim candidate | 从阅读内容生成 research claim candidate，用于读后感、文献综述或 blog。 |
| Jump back | 从 annotation / chunk / citation / translation 跳回 PDF 原文位置。 |

#### 2.4.3 如何方便读者

Reader 的体验目标是减少论文阅读中的上下文切换：

- 不用在浏览器、PDF 阅读器、翻译工具、笔记软件之间来回复制。
- 不用担心“这段中文翻译对应原文哪里”，因为每条翻译都有 segment 和页码。
- 不用读完后重新整理引用，选区可以直接变成 annotation / chunk / citation。
- 不用把 AI 总结当成事实，所有 AI 输出都必须带来源 refs，用户接受后才沉淀。
- 不用每次从头读，Library 和 Reader 会记录 last read、阅读状态、批注数量和翻译状态。
- 不用把论文阅读误当成强 evidence；Reader 产出的 claim 更适合 blog 读后感、
  literature memo 和项目背景分析。

推荐的实际阅读路径：

```text
Open Reader
  -> Analyze Paper
  -> Translate abstract / introduction
  -> Ask Paper: 这篇论文和我的项目有什么关系？
  -> 高亮关键贡献和限制
  -> Translate Method / Experiments
  -> Create chunks / citations
  -> Generate claim candidates
  -> Export reading note 或 blog 读后感素材
```

深读路径：

```text
Open Reader
  -> Translate paper / all missing
  -> Analyze Paper
  -> Section-by-section review
  -> Compare with same tree node papers
  -> Create literature memo
```

### 2.5 Claims & Citations

Claims & Citations 保留为独立小页面，但主入口来自 Reader 的 selection、
annotation 和 chunk。

分三个小 tab：

- Chunks
- Claims
- Citations

Claim card 显示：

- text
- status：draft / ready / promoted / dismissed
- source_refs
- chunk_refs
- citation_refs
- confidence
- warnings

Citation card 显示：

- quote
- locator
- chunk
- bibliography
- quote validation status

`Promote to Evidence candidate` 继续走现有
`research_claim_to_evidence_candidate()`。论文阅读不能直接写 accepted public
claim。

### 2.6 Synthesis / Export

这个小页面负责把论文阅读结果变成可复用材料：

- 从 selected claims/chunks/citations 生成 reading note。
- 从某个 tree node / subtree 中多篇论文生成 literature memo。
- 从 promoted research claims 生成 blog candidate。
- 导出引用：
  - BibTeX
  - Markdown bibliography / quote list

导出默认只提供 copy / download。只有用户点击 `Save export` 才写：

```text
research/exports/<timestamp>.bib
research/exports/<timestamp>.md
```

### 2.7 Advanced Connectors

现有 Connectors 移到高级区。arXiv / Semantic Scholar 的日常搜索优先通过
Paper Search 使用；Connectors 用于长期 query sync。

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
/srv/nblane-data      # 私有数据 Git 仓库，含 profiles/ schemas/ teams/ auth/
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

### 4.1 默认前端：FastAPI sidecar + PDF.js

PDF Reader 的主入口是 FastAPI sidecar 提供的 `/reader/view/{source_id}`。
`research_paper_reader_component` 的静态 Streamlit runtime 已停用，仅保留
`events.py` 作为事件常量契约。前端 PDF 渲染由 sidecar 模板加载 bundled PDF.js
资产完成。

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
NBLANE_RESEARCH_STRUCTURE_BACKEND=grobid
```

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
- GROBID 不可用或返回错误时，回退 PyMuPDF page text / heuristic segments。
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
NBLANE_RESEARCH_STRUCTURE_BACKEND=grobid
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
  `GROBID unavailable` / `Needs structured extraction`，并回退到 PyMuPDF page text /
  heuristic segments。

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


依赖合入原则：

- 默认依赖包含 PyMuPDF，默认部署包含 GROBID。
- 部署文档必须明确 PyMuPDF 的 AGPL / commercial dual licensing 边界。
- GROBID 服务不可用时不能阻断 PDF 导入，但页面需要显示结构化抽取降级 warning。
- 如果某个部署不能接受 PyMuPDF 许可，需要提供明确的替代构建方案；该方案不作为
  Paper Reading Studio v1 默认体验。

## 5. AI 策略

### 5.1 AI Actions

所有论文 AI 都走 AI Gateway，不在页面直接调用 `llm.chat`。

新增 actions：

- `research.paper_search_codex`
- `research.paper_translate`
- `research.paper_explain_selection`
- `research.paper_source_guide`
- `research.paper_qa`
- `research.paper_claim_extract`
- `research.paper_deep_read_codex`
- `research.paper_compare_codex`

不变量：

- 论文阅读类 AI prompt 只能使用传入的 source metadata、segments、chunks、
  annotations。
- Paper Search 类 AI / Codex prompt 可以使用 web search / provider search，
  但输出必须带可检查的 URL / DOI / provider refs。
- 输出必须包含 `cited_segment_refs`、`cited_chunk_refs` 或 `cited_annotation_refs`。
- 没有依据时必须返回 warning，不能编造答案。
- AI run metadata 不保存完整 PDF 文本、完整翻译或完整 prompt。

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

翻译输入：

```json
{
  "source": {"id": "...", "title": "...", "authors": []},
  "target_lang": "zh",
  "segments": [
    {
      "segment_id": "seg:...",
      "page": 3,
      "locator": "p. 3 § Method",
      "text_hash": "sha256:...",
      "text": "..."
    }
  ],
  "glossary_hint": {
    "memory encoder": "记忆编码器"
  }
}
```

AI 输出：

```json
{
  "translations": [
    {
      "segment_id": "seg:...",
      "source_hash": "sha256:...",
      "translated_text": "...",
      "glossary": {},
      "warnings": []
    }
  ]
}
```

保存前校验：

- 输出 segment 数不能超过输入 segment。
- 每条 `segment_id` 必须来自输入。
- `source_hash` 必须匹配当前 segment。
- hash 不匹配时标记 stale，不覆盖旧翻译。
- 单 batch 失败不影响其他 batch。

UI 对齐：

- 默认左原文、右中文。
- PDF 页 hover 某段时，高亮右侧中文。
- 中文段落点击可跳回 PDF 页。
- 支持 translate selection / page / section / all missing。

### 5.3 AI 阅读要点总结

`Source Guide` 生成结构化阅读报告：

- one-sentence takeaway
- TL;DR
- problem / motivation
- main contributions
- method / architecture
- datasets / experiment setup
- results / metrics
- limitations
- useful definitions / terms
- key equations / figures to inspect
- open questions for my project
- candidate claims
- candidate citations

长论文使用 map-reduce：

1. 按 section 生成 section summaries。
2. 保存 accepted summaries 到 `research/analysis/<source>.yaml`。
3. whole-paper synthesis 只读 section summaries + key segments。
4. 每条 conclusion 必须带 refs。

用户操作：

- `Accept as note` -> 写 `research/notes/<source>.md`
- `Accept as claim candidate` -> 写 `research/claims.yaml`
- `Create citations` -> 写 `research/citations.yaml`

### 5.4 AI 问答

v1 不引入向量数据库，使用本地 retrieval：

- query token overlap
- section title boost
- chunk / annotation boost
- current page boost
- recent reading boost

流程：

```text
question
  -> retrieve top K segments/chunks
  -> AI answer with citations
  -> user clicks cited refs
  -> jump to PDF page / segment / annotation
```

回答格式：

```json
{
  "answer": "...",
  "cited_segment_refs": [],
  "cited_chunk_refs": [],
  "cited_annotation_refs": [],
  "warnings": []
}
```

如果 refs 为空，UI 不显示为可信回答，只显示 warning。

### 5.5 Codex Paper Search and Analyze Paper

Codex 不用于每次小段翻译。Codex 用于更强的搜索和长任务：

- Paper Search：根据 topic / project / goal 使用 web search 和 provider search
  找论文、检查链接、去重、返回导入候选。
- Analyze Paper long read：通读全文 segments，生成结构化阅读报告。
- Compare Papers：比较某个 tree node / subtree 中多篇论文的方法、假设、结果、缺口。
- Project Fit：结合 current goal / project refs 判断论文对当前项目的价值。
- Code Link：如果论文关联 GitHub repo，分析论文方法与代码实现对应关系。
- Next Reading Plan：根据已读论文和 gap 推荐下一批搜索 query。

Codex 默认使用部署级 / 终端同款 Web Codex：

- 使用 service-level `CODEX_HOME`（本地通常是 `~/.codex`，云上可用 `NBLANE_CODEX_HOME` 指向持久化目录）。
- 只读 `codex exec`。
- 不给 Codex 访问 PDF asset root 全目录。
- Paper Search 场景只传 search context bundle：
  - user query
  - provider filters
  - current project / goal / library tree hint
  - already imported DOI / arXiv / Semantic Scholar ids
- Analyze Paper 场景只传当前 source 的必要 context bundle：
  - source metadata
  - selected segments
  - chunks
  - annotations
  - user question
- Codex Search 输出必须是结构化候选列表，并且不能自动导入。页面必须要求用户确认。

Agent Activity 瘦身：

- 成功只记录 action、source_id、summary、output refs。
- 失败记录短错误摘要和 activity item id。
- 不把整篇论文、全文翻译、完整 prompt 存入 `agent-activity.yaml`。

## 6. Core API 设计

新增模块建议：

```text
src/nblane/core/research_papers.py
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

Reader 由 FastAPI sidecar 提供 `/reader/view/{source_id}` 主入口。旧
`research_paper_reader_component` runtime 不再作为 PDF Reader fallback；仅保留事件常量
模块作为前后端契约来源：

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
- `analyze_selection`
- `ask_paper`
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

### Phase 1: Core and Search

- 新增 `research_papers.py`。
- 增加 PyMuPDF dependency。
- 实现 asset root、PDF import、download、sha256、page count、page text、
  coordinates fallback。
- 扩展 arXiv / Semantic Scholar search result。
- 实现 Codex-first Paper Search UI，支持 topic search、provider search、
  URL/DOI import、PDF upload。
- 实现 provider API + LLM normalization fallback。
- 实现 link check、duplicate preview、YAML preview。
- 实现 BibTeX / Markdown export。

验收：

- 能用 Codex 按主题搜论文，并返回可检查链接的结构化候选。
- Codex 不可用时，能回退到 arXiv / Semantic Scholar provider search。
- 能选择导入 metadata。
- 能粘贴 URL / DOI 导入 metadata。
- 能上传 / 下载 OA PDF 到 external asset root。
- PDF 不进入 profile Git。
- 能用 PyMuPDF 抽取 page text、page count 和基础坐标信息。

### Phase 2: GROBID Default Structured Extraction

- 增加 GROBID REST adapter。
- 默认部署配置 `NBLANE_GROBID_URL`。
- 实现 header/fulltext/reference/coordinate extraction。
- TEI -> segments/chunks/citations。
- GROBID 失败回退 PyMuPDF page text / heuristic segments。
- 文档更新部署方式。

验收：

- 默认配置 GROBID 时，source metadata 更完整。
- segments 有 section_path / locator / rects。
- references 可生成 BibTeX / citations。
- GROBID unavailable 时仍能用 PyMuPDF 打开和阅读 PDF，并显示结构化抽取降级 warning。

### Phase 3: PDF Reader Component

- 新增 React component。
- PDF.js 渲染。
- selection / highlight / annotation events。
- translation aligned panel。
- fallback text mode。
- build/package data。

验收：

- 能打开 PDF。
- 能选择文本高亮。
- 能保存 annotation。
- 能点击 annotation 跳页。
- 能从选区生成 chunk。

### Phase 4: AI Reading

- 新增 AI actions。
- 实现 segment batch translation。
- 实现 source guide map-reduce。
- 实现 paper QA local retrieval + grounded answer。
- 实现 claim/citation candidates preview/apply。
- 实现 Codex Paper Search activity 记录和 Analyze Paper preview。

验收：

- 长文翻译按 segment 对齐。
- AI 总结每条重要结论带 refs。
- 问答无依据时不编造。
- Codex 只读 context bundle，不写大 payload 到 Activity。

### Phase 5: Polish and Public Boundary

- Paper Library 批量整理。
- Library Tree 管理 UI。
- Synthesis / Export 完整化。
- Public validation 增强。
- 文档同步。

验收：

- private paper source 不能发布。
- unpromoted research claim 不能发布。
- citation/chunk 断链阻断发布。
- promoted research claim + public source + valid citation 可以通过。

## 9. Subagent 分工

可以合理使用 subagent 并行：

- Core Worker
  - `research_papers.py`
  - PDF asset root
  - PyMuPDF extraction
  - GROBID adapter
  - export formatter
- Frontend Worker
  - `src/nblane/web_reader_api/templates/index.html`
  - PDF.js viewer / left rail / translation flow
  - annotation event schema
  - sidecar template contract tests
- Research UI Worker
  - `pages/7_Research.py` 小页面重排
  - Paper Search / Library / Reader / Export UI
  - fallback text mode
- AI Worker
  - AI Gateway actions
  - Codex paper search
  - translation batching
  - source guide
  - QA retrieval
  - Codex deep read
- Docs/Test Worker
  - docs 同步
  - tests 扩展
  - deployment asset root 说明

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
  - annotation -> chunk -> claim -> citation -> evidence candidate。
  - quote 在 chunk 中可校验通过。
  - quote 不匹配时保存 warning。
  - archived source 保留 PDF/annotations/chunks。
  - library node refs 断链产生诊断。

### Public / Output

- 扩展 `tests/test_public_site.py`
  - private paper source 阻断 publish。
  - unpromoted research claim 阻断 publish。
  - dangling citation/chunk 阻断 publish。
  - promoted research claim + public source + valid citation 通过。
  - unsafe quote/path/token 失败。

### Frontend

PDF Reader 不再构建 `research_paper_reader_component/frontend`。前端主路径在
`src/nblane/web_reader_api/templates/index.html`，PDF.js 资产打包在
`src/nblane/web_reader_api/static/assets/`。如需调试 legacy overlay，设置
`NBLANE_READER_DEBUG_OVERLAY=1` 后走 sidecar Reader。

JS tests：

- selection payload schema。
- rect normalization。
- annotation create/update/delete events。
- translation event carries segment/page/source hash。
- translate paper / all missing event 不直接携带全文，只携带 source_id、scope、stale/missing selector。
- citation click emits jump event。

Playwright smoke：

- 打开 fixture PDF。
- 选择文本并高亮。
- 创建 annotation。
- 点击 annotation 跳页。
- 触发 translate/analyze event。
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
  pages/7_Research.py \
  src/nblane/core/research_papers.py

git diff --check
```

## 11. Assumptions

- v1 做 PDF 高亮阅读器，但不做 OCR、公式结构化识别、表格完整复原、
  Zotero 双向同步、多人实时协作。
- PDF 二进制必须外置到 `NBLANE_RESEARCH_ASSET_ROOT`，不进入 profile Git。
- 批注、翻译、page text、segments、chunks、claims、citations、阅读笔记是轻量研究事实，可进入 profile 文件。
- Paper Search v1 推荐 Codex-first；Codex 不可用时回退 arXiv +
  Semantic Scholar provider search，再由 LLM 做轻量归一化。
- GROBID 是默认结构化抽取服务，Apache-2.0，适合学术 PDF 的结构化抽取。
- PyMuPDF 是默认本地 PDF backend；部署方需要接受 AGPL 或使用 commercial license。
- pypdf 不作为主路径默认后端，只保留为极简 fallback / fixture 选项。
- Codex 是论文搜索、链接检查和长任务 deep-reading agent，不是普通 selection 翻译器。
- Research claim 继续是 source-aware claim；公开表达仍走 Evidence Review /
  Claim Studio / Output Studio。
