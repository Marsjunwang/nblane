# 公开站功能完善工作计划：从碎片 Evidence 到完整项目展示

Blog 编辑器的下一版交互设计见
[Public Site Blog 编辑器设计](public-site-blog-editor-design.md)。该设计把当前固定
三栏 Blog tab 升级为 BlockNote 中心的可折叠 Editor Shell，并定义左侧文章栏、右侧
Meta / Media / AI / Check 工具抽屉、专注模式和小屏编辑器优先策略。

## 当前问题

公开站已经可以构建个人网站、博客、成果和简历，但它只读取 public layer：

- `public-profile.yaml`
- `projects.yaml`
- `outputs.yaml`
- `resume-source.yaml`
- `blog/*.md`

这些文件默认是空的或草稿状态，所以页面会显得像“空壳”。真正有价值的信息通常沉淀在：

- `evidence-pool.yaml`
- `skill-tree.yaml`
- `SKILL.md`
- `kanban.md`

其中 `evidence-pool.yaml` 记录的是日常工作留痕，往往很细碎：一次复现、一次 benchmark 梳理、一次 demo 修复、一次模型加速、一次论文/专利事实。它们不是天然完整的公开项目，不能直接当项目列表展示。

## 三层关系

公开站采用三层模型：

```text
原子证据层      evidence-pool.yaml
              记录可追溯的工作事实，不物理合并、不删除、不直接公开成项目

公开聚合层      projects.yaml / outputs.yaml / blog/*.md / resume-source.yaml
              人工确认哪些 evidence 可以组成公开项目、成果、文章或简历事实

页面展示层      dist/public/<profile>/
              只渲染 published / public 的公开聚合对象
```

核心规则：

- `evidence-pool.yaml` 是原子事实库，不应为了公开展示而把多条 evidence 物理合并。
- 一个 `projects.yaml` 项目可以通过 `evidence_refs` 引用多条 evidence。
- 一个 `outputs.yaml` 成果也可以通过 `evidence_refs` 引用多条 evidence。
- 公开站展示聚合后的项目/成果，不把 evidence 列表当作项目列表。
- `skill-tree.yaml`、`SKILL.md`、`kanban.md` 不直接渲染到公开站。
- AI 或规则只能生成 `draft`，发布必须人工确认。

## 已落地命令

预览推荐分组，不写文件：

```bash
nblane public suggest-groups <profile> --dry-run
```

人工确认后，把多条 evidence 聚合成一个 draft 项目：

```bash
nblane public group <profile> \
  --id piper-home-robot \
  --title "Piper / 家庭整理机器人项目" \
  --evidence ev_piper_repro \
  --evidence ev_piper_demo_fix \
  --evidence ev_shoe_benchmark_new
```

只补明显的一对一成果草稿，例如 paper / patent evidence 到 `outputs.yaml`：

```bash
nblane public hydrate <profile> --dry-run
nblane public hydrate <profile> --write-drafts
```

命令边界：

- `suggest-groups` 永远只读。
- `group` 只写 `projects.yaml`，并且写入 `status: draft`。
- `hydrate --write-drafts` 只写 `outputs.yaml` 的 draft 成果。
- 这些命令都不会修改 `evidence-pool.yaml` 或 `skill-tree.yaml`。

## projects.yaml 推荐字段

```yaml
projects:
  - id: piper-home-robot
    title: Piper / 家庭整理机器人项目
    status: draft
    summary: Draft project aggregated from reviewed evidence.
    tags:
      - robotics
      - imitation-learning
      - home-robot
    evidence_refs:
      - ev_piper_repro
      - ev_piper_demo_fix
      - ev_shoe_benchmark_new
    skill_refs:
      - real_robot_ops
      - imitation_learning
      - experiment_design
    links: {}
    featured: false
    public_angle: ""
    review_notes: Confirm wording, privacy, links, and metrics before publishing.
```

其中：

- `evidence_refs` 是事实追溯链。
- `skill_refs` 是公开项目关联的技能信号，只展示节点 id，不展示 raw `skill-tree.yaml`。
- `public_angle` 是面向公开读者的项目叙事，需要人工整理。
- `review_notes` 是审核备注，不作为公开页面重点内容。

## 王军 profile 示例聚合

Piper / 家庭整理机器人项目 draft：

```text
ev_piper_repro
ev_piper_demo_fix
ev_shoe_benchmark_new
```

公开叙事方向：Piper 机械臂上的 PI0.5 / OpenPI 复现、桌面鞋子摆放和物体收纳 demo 修复、家庭整理场景 benchmark 梳理。

6D 位姿与鞋子摆放成果线 draft：

```text
ev_pose_paper
ev_shoe_patent
ev_shoe_benchmark
```

公开叙事方向：6D 位姿估计论文、鞋子摆放专利、家庭鞋子抓取摆放 benchmark 组成一条从算法到应用任务的成果线。

自动驾驶 / 感知模型优化项目 draft：

```text
ev_ap_boost
ev_training_speedup
ev_gaussian_3d
```

公开叙事方向：远距单目检测 AP 提升、端到端模型训练加速、自监督 Gaussian 3D 预训练，组成感知模型性能优化项目。

机器人感知 / VLA 系统架构项目 draft：

```text
ev_ros_arch
ev_spatial_forcing_vggt
```

公开叙事方向：家庭机器人分层感知系统架构、ROS 系统集成、3D-augmented VLA 监督信号探索。

## Streamlit 审核流程

`Public Site` 页面新增 `Known Info` tab：

- 查看每条 evidence 的 id、type、title、关联 skill refs、是否已被项目/成果/博客引用。
- 查看规则推荐分组。
- 勾选多条 evidence，填写项目 id / title / summary / tags，生成 `status: draft` 项目。
- 查看当前 projects 及其 `evidence_refs`。
- 从 draft project 中移除某条 `evidence_ref`，但不删除 evidence 本身。

## 静态站展示规则

首页只展示入口和最近标题：

- 姓名、联系方式、简介
- Blog 入口和最近文章标题
- Projects 入口和最近项目标题
- Outputs 入口和最近成果标题
- Resume 入口

项目列表页展示聚合后的项目。每个项目生成详情页：

```text
/projects/<project_id>/
```

项目详情页展示：

- 项目标题、摘要、public angle、tags、links。
- 关联 evidence 的简短公开摘要。
- 关联 skill refs。

成果详情页同理：

```text
/outputs/<output_id>/
```

## 验收标准

- 可以把多条 evidence 聚合成一个 draft project。
- 原始 `evidence-pool.yaml` 内容保持不变。
- 已被项目引用的 evidence 会给出 warning，不重复写入新项目。
- 不存在的 evidence id 会阻止写入。
- published project 会生成 `/projects/<id>/` 详情页。
- draft project 默认不进入公开站，`--include-drafts` 时可预览。
- 项目详情页能展示 evidence 摘要，但不泄露 raw `SKILL.md`、`kanban.md` 或 `agent-profile.yaml`。
- 首页不再承担完整内容展示，只作为个人公开信息和内容入口。
