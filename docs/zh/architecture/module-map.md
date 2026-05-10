---
status: active
owner: engineering
last_verified: 2026-05-08
source_of_truth: true
---

# 模块总览图

## 系统层级

```mermaid
flowchart TB
  UI[Streamlit Web UI]
  CLI[nblane CLI]
  MCP[nblane MCP Server]
  Harness[Codex / OpenCode / Cursor / Claude]

  Core[src/nblane/core]
  Files[profiles / teams / schemas]
  Index[Workspace Index planned]
  Public[Static Public Site]

  UI --> Core
  CLI --> Core
  Harness --> MCP
  MCP --> Core
  Core --> Files
  Files --> Index
  Index --> UI
  Core --> Public
```

## 当前核心闭环

```mermaid
flowchart LR
  K[kanban.md Done]
  LLM[LLM JSON patch]
  E[evidence-pool.yaml]
  ST[skill-tree.yaml]
  V[validate]
  S[sync SKILL.md]
  C[context / MCP]

  K --> LLM --> E --> ST --> V --> S --> C
```

## Public Surface

```mermaid
flowchart LR
  PP[public-profile.yaml]
  RS[resume-source.yaml]
  PJ[projects.yaml]
  OP[outputs.yaml]
  BLOG[blog/*.md + sidecar]
  MEDIA[media/]
  BUILD[build_public_site]
  DIST[dist/public/profile]

  PP --> BUILD
  RS --> BUILD
  PJ --> BUILD
  OP --> BUILD
  BLOG --> BUILD
  MEDIA --> BUILD
  BUILD --> DIST
```

## 规划中的 typed graph

```mermaid
flowchart LR
  Task[Task]
  Project[Project]
  Evidence[Evidence]
  Skill[SkillNode]
  Schema[SchemaNode]
  Source[ResearchSource]
  Claim[Claim]
  Draft[SynthesisDraft]
  Blog[BlogPost]
  Team[TeamPoolItem]

  Project -->|contains| Task
  Task -->|produces| Evidence
  Evidence -->|supports| Skill
  Skill -->|conforms_to| Schema
  Source -->|supports| Claim
  Claim -->|used_in| Draft
  Draft -->|exports_to| Blog
  Blog -->|cites| Source
  Team -->|drives| Project
```

## 模块到对象映射

| 对象 | 当前模块 | 规划模块 |
|------|----------|----------|
| Profile | `profile_io.py` | `workspace_index.py` |
| SkillNode / Evidence | `models.py`、`evidence_resolve.py`、`profile_io.py` | `workspace_index.py` |
| KanbanTask | `kanban_io.py`、`kanban_events.py`、`kanban_ai.py` | `project_board.py`、`workspace_index.py` |
| Public Blog | `public_site.py`、`ai_dispatcher.py`、`ai_blog_reviewer.py` | `research.py`、`source_aware_blog.py` |
| ResearchSource / Claim | 未落地 | `research_sources.py` |
| Project / Milestone | 未落地 | `project_board.py` |
| AI Task | `llm.py` + scattered prompts | `core/ai/` |
| Agent Harness | `cursor_rule.py` 初版 | `agent_harness.py` |

## 视图原则

视图只读取索引，不成为新事实源：

- Table view：按属性过滤和排序。
- Board view：按状态/项目分组。
- Graph view：对象关系图。
- Project view：project -> milestone -> task -> evidence。
- Research matrix：source -> claim -> draft。
- Publication readiness：blog/project/output 的公开风险和出处覆盖。
