# Growth Graph 星树重构开发计划

> 临时工作文档。用于把 Home Dashboard 的 3D Growth Graph 从“扁平力导向图”重构成语义化的「星树」可视化。稳定后再合并进 `docs/zh/product/growth-graph.md` 与 `docs/zh/guides/web-ui.md`。
>
> 生成日期：2026-06-23
> 对照来源：`src/nblane/core/home_dashboard.py`、`src/nblane/core/workspace_graph.py`、`src/nblane/core/growth_graph_contract.py`、`src/nblane/home_dashboard_component/frontend/src/{main.jsx,payload.js,payload.test.mjs}`、`schemas/robotics-engineer.yaml`、`docs/zh/dev/dashboard-development-plan.md`。
>
> 本文档自包含：不依赖任何对话上下文，接手人（或 AI）可直接照此执行。

---

## 0. 背景与目标

### 0.1 为什么做

现有 3D Growth Graph（`react-force-graph-3d` + three.js）把 **20 种 node type、11 个 layer** 全部用同一种「小球 + 连线」的力导向方式渲染，语义被压平 —— 看不出谁是主干、谁托举谁、什么是结果。力导向稳定后图是**静态的**（`cooldownTicks=100` 后停），"Live" 名不副实；且每次刷新布局随机，形状不稳定。

### 0.2 星树隐喻（目标形态）

用 8 个视觉原型（role）承载成长系统语义：

| role（视觉原型） | 含义 | 对应现有 node type | 现有关系/数据支撑 |
|---|---|---|---|
| **trunk** 主干 | 北极星方向 | `north_star` | — |
| **direction** 方向 | 阶段目标 | `goal` | `alignment` 对齐主干 |
| **branch** 分支 | 项目 | `project_case` | `contains` 挂在 goal 下 |
| **leaf** 叶 | 任务/产出 | `task`、`output` | `produces` / `contains` |
| **fruit** 果（结果） | 证据 | `evidence`、`evidence_candidate`、`atomic_evidence`、`composite_evidence` | `generated_by` 从叶结出 |
| **star** 星辰 | 技能 ×82 | `skill` | `supports` 证据托举；亮度随 `status` |
| **constellation** 星座 | 断言 | `claim` | `derives` / `supports` 从证据汇成 |
| **sand** 沙子 | 日常研究/学习 | `research`、`daily_work`、`source` | 按 `tags`/`goal_refs`/`kind` 聚主题 |

**不入树的 6 类**：`health`、`capacity`、`gap`、`next_action`、`feedback`、`agent_run`。它们已有专属 UI（HealthSummaryPanel / ActionQueue 等），在星树视图中默认隐去 —— 强行塞进隐喻反而破坏可读性。

### 0.3 三个已确认的产品决策

1. **塌缩到 8 类落在 `role` 维度**（新增 role 作视觉语义），**保留 `type`** 作功能标识 —— 见 §1 铁律。
2. **沙子 = GPU 粒子场 + 悬停聚合**：`THREE.Points` 粒子场，非可点击节点；悬停某主题簇时浮出该主题条目列表。
3. **固定骨架 + 呼吸动效**：树形坐标确定性钉死（`fx/fy/fz`）保证可读；"Live" 感来自持续 animation loop 的呼吸/闪烁/飘动，而非力导向漂移。

### 0.4 交付方式（已确认）

- **分两大交付块**：
  - **块 A = 数据 + 功能保护**（阶段 0-2）：完成并验证后形成“不弄坏现有功能”的安全基线。
  - **块 B = 视觉重构**（阶段 3-7）：一次性做完星树视觉后统一验证。
- **星树替掉现有 3D 视图**：星树渲染**替换** `viewMode === "3d"` 的 `Graph3DView` 分支；`focus`/`canvas`/`attention` 三个旧视图**保留不动**。

---

## 1. 铁律：`type` 不能删（否则编辑功能断裂）

**这是整份计划最关键的约束。** `node.type` 不只是视觉标签，还在前端驱动功能判断。`main.jsx` 有 4 处精确匹配：

| 位置 | 代码 | 作用 | 删 type 的后果 |
|---|---|---|---|
| `main.jsx:2592` | `selectedNode.type === "goal" && selectedGoal` | 渲染目标编辑表单 | 目标无法编辑 |
| `main.jsx:2653` | `selectedNode.type === "skill"` | 显示 Gap 分析按钮 | Gap 分析消失 |
| `main.jsx:495-499` | `preferredNode` 里 `goal/skill/task/north_star` | 默认选中优先级 | 选中逻辑错乱 |
| `main.jsx:3012,3029` | `item.type === "goal"` + `recordId===goalId` | `selectGoal` 定位 | 目标选中失效 |

**结论**：`role` 是**新增**的视觉语义维度，`type` **保留**作 record-kind 功能标识。"塌缩到 8 类" 在 role 维度达成（前端视觉只认 role）；功能判断改为认 `role` + `recordId`（见阶段 2）。两者由 contract 单一映射源保证一致。

---

## ▏块 A — 数据 + 功能保护（安全基线）

### 阶段 0 — 后端：发全 82 个 skill

**问题**：当前只发用户**已追踪**的 skill。`dashboard_skill_summary` 的 `items` 只遍历 `tree_raw["nodes"]`（`home_dashboard.py:414`），而 82 是 schema 全集。

**改法**（`src/nblane/core/home_dashboard.py`，`dashboard_skill_summary` 372-438）：
- 把 `items` 的遍历源从 `_as_list(tree_raw.get("nodes"))` 改为 schema 全集 `index`（已由 `_status_counts` 在 391-392 行返回，`index = schema_node_index(schema_raw)`）。
- 对每个 schema 节点：`status` 取 tree 中实际值，**未追踪默认 `"locked"`**（最暗）；`label` 走 `_node_label(index, node_id)`；`category` 走 `index`。
- `counts/total/lit` 维持现有计算不变。
- 已确认 `workspace_graph.py:921` 的 `_clean_item_rows(..., limit=180)` > 82，无需改 limit。

**已确认事实**：skill 节点已带 `status`（`workspace_graph.py:935`），取值 `locked/learning/solid/expert`，亮度 4 档映射零额外数据成本。

**验证**：`dashboard_skill_summary(dev)` 返回 `len(items) == 82`；`workspace_graph_payload` 中 `type=="skill"` 的节点数 == 82。

### 阶段 1 — 数据层：role 塌缩（后端 contract + 测试）

**1a. contract**（`src/nblane/core/growth_graph_contract.py`）：
- 新增 `roles` 定义（8 个）：`trunk/direction/branch/leaf/fruit/star/constellation/sand`，各带 `label`/`label_zh`。
- 给每个 `node_types` 项加 `role` 字段（映射见 §0.2 表）；6 个不入树类型 `role` 设为 `""`（标记不入树）。
- `schema_version`：`"1.0"` → `"1.1"`。
- 加 helper `growth_graph_node_type_roles()`（类比现有 `growth_graph_node_type_layers()`），返回 `{type: role}`。

**1b. workspace_graph**（`src/nblane/core/workspace_graph.py`）：
- `_node()`（42-87）增 `role` 参数；若未显式传，从 contract 的 type→role 映射自动填充（加 `_role_for_type(type)` helper，读 contract）。
- 节点输出统一带 `role`。focus_path（1243-1258）/attention（1200-1239）基于 node_id，**不受影响**。
- `workspace_graph_node_type_roles()` 封装委托给 contract（类比 `workspace_graph_node_types()`）。

**1c. 测试**：
- `tests/test_growth_graph_contract.py`：`schema_version` 改 `"1.1"`；新增断言 roles 存在、`node_type_roles()["north_star"]=="trunk"`、`["skill"]=="star"` 等。
- `tests/test_workspace_graph.py`：在 skeleton 断言里增 `node["role"]` 校验（每个节点 role 在 8 个 role 或 `""` 内）。

**验证**：`pytest tests/test_growth_graph_contract.py tests/test_workspace_graph.py`。

### 阶段 2 — 前端 normalize + 功能 rewire（不改视觉，先保功能）

**2a. normalize**（`payload.js`，`normalizeGraphNode` 153-180）：
- 注入 role：`role: cleanText(source.role) || ROLE_FOR_TYPE[type] || ""`。
- 前端补一份 `ROLE_FOR_TYPE` 兜底表（类比现有 `GRAPH_TYPE_LAYER` 15-36），后端没发也能推导。

**2b. 功能 rewire**（`main.jsx`，改 type 判断为 role + recordId）：

```
2592  type==="goal" && selectedGoal   →  role==="direction" && selectedGoal
2653  type==="skill"                  →  role==="star"
3012  item.type==="goal" && recordId  →  item.role==="direction" && recordId
3029  同上
495-499 preferredNode:
        north_star → role==="trunk"
        goal       → role==="direction"
        skill      → role==="star"
        task       → role==="leaf" && type==="task"   (leaf 含 output，task 需保优先)
```
> `selectedGoal` 本就靠 `recordId` 从 goal 列表解析，改 role 安全。preferredNode 中 task 单独保 `type==="task"` 以区分同为 leaf 的 output。

**2c. 测试**（`payload.test.mjs`，现有 5 个 test）：增 role 注入断言（后端带 role 时透传、不带时按 ROLE_FOR_TYPE 推导）。

**验证**：`npm run build` + `node --test src/*.test.mjs`；dev 起服务，点 goal 节点确认编辑表单在、点 skill 节点确认 Gap 按钮在。

> **块 A 完成 = 安全基线**：此时视觉未变，但数据带 role、82 星全发、功能判断已迁到 role+recordId，后续视觉重构不会再碰功能。

---

## ▏块 B — 视觉重构（星树，替换 3D 视图）

> 集中实现，完成后统一验证。替换 `main.jsx` 中 `viewMode === "3d"` 的 `Graph3DView` 分支（2226-2232 及 GraphHeroPanel 2043-2051）；旧三视图保留。现有 `graph3DSeedPosition` 随机环形布局被星树固定骨架取代。

### 阶段 3 — 星树固定骨架（确定性布局）

**新增 `growthTreeLayout(payload)`**（`main.jsx`，替代 `graph3DSeedPosition` 1364-1377）：按 role 算 3D 坐标写入 `node.fx/fy/fz` 钉死。骨架伪代码：

```
trunk:        (0, y∈[0,H], 0)                  // 竖直主轴，H≈树高
direction:    沿主干上半部，按 goal 数均分方位角 θ，向外斜上
              (r·cosθ, y_goal, r·sinθ)
branch:       从所属 goal（alignment/contains 边）末端，二级展开成枝
leaf:         从所属 branch（contains/produces 边）末端散开，y 略升（叶在枝梢）
fruit:        从所属 leaf（generated_by 边）下垂，y 略低于叶（果实下坠）
无父兜底:     挂到 trunk 对应高度
```
- 父子关系用现有 edges 解析：`alignment`（goal→trunk）、`contains`（goal→project, project→task）、`produces`/`generated_by`。
- 关力导向漂移：`cooldownTicks={0}`、`warmupTicks={0}`，位置由 fx/fy/fz 主导；保留 `enableNodeDrag` 可选。

**验证**：build + dev，树形可读，多次刷新形状稳定。

### 阶段 4 — 星辰层 + bloom（82 skills 发光穹顶）

**已确认**：`three/examples/jsm/postprocessing/{UnrealBloomPass,EffectComposer,RenderPass}.js` 已在 node_modules，**无需装包**。

- **star 布局**：82 skill 浮在树冠上方半球穹顶（按 `category` 分扇区 + fibonacci sphere 分布），fx/fy/fz 钉住。
- **亮度按 status**（`nodeThreeObject` 1477-1508，改 `emissiveIntensity`）：
  ```
  locked   0.05   (最暗)
  learning 0.18
  solid    0.40
  expert   0.70   (最亮)
  ```
  star 用较小球体 + 高 emissive。
- **bloom 接入**（`Graph3DView` 挂载后）：
  ```js
  import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass.js";
  // graphRef.current 暴露 postProcessingComposer()
  const composer = graphRef.current.postProcessingComposer();
  composer.addPass(new UnrealBloomPass(resolution, strength, radius, threshold));
  // 调 threshold 让亮星泛光、暗星(locked)不泛
  ```
- `supports` 边（evidence→skill）做成「托举」光丝（用现有 `relationColor`）。

**验证**：build + dev，82 星显示、expert 最亮 locked 最暗、bloom 生效不糊。

### 阶段 5 — 星座层（claims）

- claim（role=constellation）定位在其关联 evidence/skill（`derives`/`supports` 边）质心上方。
- 用 `THREE.LineSegments` 把 claim 与来源 evidence 连成星座轮廓；claim 本体做亮点 + 标签（复用 `createLabelSprite` 1438-1475）。

**验证**：build + dev，claim 与来源证据连成星座。

### 阶段 6 — 沙子粒子场 + 悬停聚合

- source/research/daily_work（role=sand）**从 ForceGraph nodes 过滤掉**，单独建 `THREE.Points`：
  - 按 `tags`/`goal_refs`/`kind` 聚成主题簇，簇心散布树底部平面，簇内高斯抖动。
  - 顶点着色按主题，`sizeAttenuation`，低透明度求「轻盈」。
  - `graphRef.current.scene().add(points)`；组件卸载 `dispose()`。
- **悬停聚合**：`THREE.Raycaster` + Points `threshold` 命中某簇 → HTML overlay 列出该主题 source 条目（title/kind，复用 `payload.sources.items`）；移开消失。

**验证**：build + dev，底部粒子按主题成簇、悬停浮出条目、不抢树/星注意力。

> 注：source 原本是可点击节点，改粒子后失去点击编辑入口 —— 已与用户确认采用「纯氛围 + 悬停浮出」。若 Inspector 有 source 依赖需回归确认。

### 阶段 7 — 呼吸动效（Live）

- 自建 `requestAnimationFrame` loop（`Graph3DView` 内 useEffect 挂载，清理时 `cancelAnimationFrame`）：
  - **树**：trunk/branch 极轻微摆动（sin 相位偏移）。
  - **星辰**：`emissiveIntensity` 叠加小幅呼吸/闪烁（各星相位错开）。
  - **沙子**：Points position attribute 缓慢漂移（`needsUpdate=true`）。
- 与 force-graph 协调：force 已停，独立 rAF 只更新材质/position；**单一 loop、卸载清理**，防内存泄漏。

**验证**：build + dev，持续微动、CPU/GPU 占用可接受。

---

## 2. 复用的现有资产

- **后端**：`schema_node_index`（home_dashboard.py:147）、`_node_label`、`_clean_item_rows`、`_node()/_edge()`（workspace_graph.py:42-108）、现有 `supports/derives/generated_by/contains/produces/alignment` 边生成逻辑、`growth_graph_node_type_layers()` 范式。
- **前端**：`normalizeGraphNode`、`graph3DData`（1379-1415）、`createLabelSprite`（1438-1475）、`fitGraphCamera/focusGraphCamera`、`relationColor`、`GRAPH_TYPE_LAYER` 范式、ForceGraph3D 的 `.scene()/.camera()/.renderer()/.postProcessingComposer()`、`node.fx/fy/fz`。
- **依赖**：three 0.184 自带 postprocessing（bloom），无需新包。

## 3. 风险

- **性能**：82 星 bloom + 粒子场 + 每帧动画在 Streamlit iframe 内。缓解：bloom 单 pass；粒子用单个 `THREE.Points`（非逐粒子 mesh）；动画只更新材质/attribute 不重建几何；粒子数限制在数百量级。dev 实测帧率。
- **role/type 双轨一致性**：靠 contract 单一映射源 + 测试守住。
- **leaf 含 task+output**：preferredNode rewire 时单独保 task 优先（阶段 2b）。
- **sand 失去点击入口**：已确认接受。

## 4. 端到端验证

```bash
# 后端
PYTHONPATH=src .venv/bin/python -m pytest \
  tests/test_growth_graph_contract.py \
  tests/test_workspace_graph.py \
  tests/test_home_dashboard.py

# 前端
cd src/nblane/home_dashboard_component/frontend
npm run build
node --test src/*.test.mjs
```

- **集成**：dev 服务（18502/18503）起 Streamlit，打开 dashboard 切到 3D（星树）视图，逐项目视核验：树形可读 / 82 星亮度分档 / 星座连线 / 沙子悬停浮出 / 持续呼吸；并回归点击 goal 节点（编辑表单）、skill 节点（Gap 按钮）确认功能未断。

## 5. 文件清单（改动落点速查）

| 文件 | 阶段 | 改动 |
|---|---|---|
| `src/nblane/core/home_dashboard.py` | 0 | `dashboard_skill_summary` items 遍历 schema 全集 |
| `src/nblane/core/growth_graph_contract.py` | 1 | 加 roles + type→role + schema_version 1.1 |
| `src/nblane/core/workspace_graph.py` | 1 | `_node()` 加 role 参数 + `_role_for_type` |
| `tests/test_growth_graph_contract.py` | 1 | role/schema_version 断言 |
| `tests/test_workspace_graph.py` | 1 | node role 断言 |
| `.../frontend/src/payload.js` | 2 | normalizeGraphNode 注入 role + ROLE_FOR_TYPE |
| `.../frontend/src/payload.test.mjs` | 2 | role 注入测试 |
| `.../frontend/src/main.jsx` | 2-7 | 4 处功能 rewire + 星树布局/星辰/星座/沙子/呼吸 |
