# Dashboard 问题分析与修复计划

> 基于当前代码实读（galaxy_scene.js / main.jsx / home_dashboard.py / goals.py /
> goal_alignment.py / workspace_graph.py / web_i18n.py / i18n/zh|en/home.yaml）。
> 每条都标注「现状根因 → 改哪个文件哪一行 → 改成什么」。日期 2026-06-28。

---

## 贯穿全屏的头号问题：47 个 i18n key 缺翻译（先修这个）

`label(ui, "key", "English fallback")` 在前端用到 **217** 个 key，但其中 **47 个在
`i18n/zh/home.yaml` 和 `i18n/en/home.yaml` 里都不存在**，于是全部回退成代码里硬编码的英文。
`web_i18n.py:51-56` 的 en 兜底也救不了——因为 en 文件同样缺这些 key，`label()` 的第三参成了唯一来源。
构建产物 `static/assets/home-dashboard.js` 里能 grep 到这些英文 fallback，确认已发到用户端。

下面问题 1/3/4 提到的英文文案（`goal-relevant skills lit`、`blocking the primary goal`、
`What the visuals mean`、`Size · subtree mass`、`d overdue`、`Show archived…` 等）**全部属于这 47 个缺失 key**。

**修复（低风险，不动 JS、不重建 bundle）**：往 `i18n/zh/home.yaml` 补中文、`i18n/en/home.yaml` 补英文（用 fallback 原文）。这些是 Python payload 进程级 `ui` 字典，reader 带 `--reload` 即生效。

缺失 key 全集（按功能分组）：
- **图例**：`dashboard_graph_legend_{encoding,size,size_desc,brightness,brightness_desc,arc,arc_desc,grey,grey_desc,comet,comet_desc,octahedron,octahedron_desc,hint}`
- **目标徽章**：`dashboard_goal_{overdue,overdue_short,due_in,due_today,days}`、`goal_strip_target`、`goal_no_current`、`goal_visibility_private`
- **技能卡**：`dashboard_skill_{target_caption,target_blocked,ring_target_label,delta_label}`、`quick_skill_map`
- **归档开关 / 搜索**：`dashboard_show_archived_goals`、`dashboard_graph_search_{placeholder,aria}`
- **Action queue / onboarding / Resume / Profile**：`dashboard_action_{next_title,hero_delta_label}`、`dashboard_canvas_onboarding_*`、`resume_upload_{label,extracted}`、`profile_readiness_{ok,open,issues,blocked_prefix}`、`raw_generated_{banner_title,lines}`

---

## 问题 1 — 「goal-relevant skill」是什么、怎么生成

截图：`4/8 goal-relevant skills lit · 4 blocking the primary goal`（`main.jsx:4433-4443` `SkillProgressCard`）。

**它是什么**：不是技能树里某种特殊节点，而是「**当前 active goals 通过 `skill_links` 显式关联的那批技能节点**」的去重集合。
- 分母 `targetTotal` = 所有 active goal 的 `confirmed skill_links.nodeId` 去重数（`main.jsx:4398-4414`）。
- 分子 `targetLit` = `targetTotal − targetLocked`，其中 `targetLocked` 来自 `payload.skills.target_learning_locked`（仍是 locked/learning 的目标技能）。
- 「blocking the primary goal」= `targetLocked` 那几个还没点亮的。

**怎么生成 `skill_links`**（即 goal↔skill 关联的真实来源）：
- 持久化在 `goals.yaml` 的 `Goal.skill_links`（`goal_alignment.py:4` 注释、`GoalSkillLink`）。
- 候选由 `rule_match_goal_to_skills`（关键词重叠打分，`goal_alignment.py:61`）和 `ai_match_goal_to_skills`（LLM 路由，`:98`）产出；
  `home_dashboard.py` 经 `_goal_skill_candidates_for_home` → `skill_alignment` payload 下发，用户在 UI **确认**后写回 `goals.yaml`。
- 另有 `Goal.target_skills`（纯文本目标技能名），`_target_skill_hits`（`home_dashboard.py:486`）按文本模糊匹配技能树节点，喂 `target_learning_locked`。

**结论**：`4/8` 想表达「主目标关心的 8 个技能里点亮了 4 个」。前提是 goal 上**有 confirmed skill_links**——没有关联过技能的 goal，这行直接不显示（`targetTotal>0` 守卫，`main.jsx:4433`）。

**可改进项**（中）：
- 文案缺翻译（见头号问题）。
- 注释自己承认 `targetLit ≈ targetTotal − targetLocked` 是**近似**（payload 无 per-skill lit 查表，`main.jsx:4415-4419`）。可在 `dashboard_skill_summary`（`home_dashboard.py:645`）直接按 `skill_links.nodeId` 求交 `expert/solid` 集合，给出精确 lit 数，去掉这个近似。

---

## 问题 2 — 只能看到 active goal，如何看到其他 goal

**现状**：goal rail（`main.jsx:840-841` `activeGoals` / `secondaryGoals`）和图谱都只吃
`payload.activeGoals`，其源头是 `book.active_goals()`，**硬过滤 `status=="active"`**（`goals.py:335-337`）。
所以 `completed/paused/archived` 的目标整个不进 UI——点亮过的太阳全消失。

**好消息：底层已具备开关，只差接线**：
- 后端 `workspace_graph_payload` 已能吃 `all_goals` 并按 `all_goals or active_goals` 出节点（`workspace_graph.py:412,454`），`home_dashboard.py:1875` 已经把 `all_goals=book.goals` 传进去了——**图谱的 graph 节点其实已含非 active goal**。
- 前端 `Graph3DView` 已有 `showArchived` state（`main.jsx:3824`）+ `isExtinguished` 过滤（`main.jsx:1053-1059`）+ 「熄灭星」开关文案 key `dashboard_show_archived_goals`（缺翻译）。
- galaxy_scene 已渲染 `completed`=冷白稳定星、`archived/paused`=灰烬（`galaxy_scene.js:487-505`）。

**缺口**：
1. `payload.activeGoals`（goal rail / chip 数据源）仍只来自 `book.active_goals()`（`home_dashboard.py:1803`），rail 看不到非 active goal。
2. `showArchived` 开关 UI 默认关 + 文案缺翻译，用户不知道有这开关。

**改成**：
- `home_dashboard.py:1803-1823`：除 `active_goals` 外，增发 `all_goals` 卡片数组（带 status），或给 goal rail 一个「显示已归档/已完成」展开。
- 补 `dashboard_show_archived_goals` 翻译，让 3D 图左下的开关可读。
- goal rail（`main.jsx:840`）接入同一开关：关→只 active，开→全量并对 completed/archived 用弱化样式（对齐图谱的灰烬语义）。

---

## 问题 3 — 图1 绕 task 的 evidence 小彗星「没了」，现在这些是什么

**没删，是按设计「只在聚焦态出现」**。代码仍完整：`_addCometTrail`/`_advanceComet`/`trailGroup`/`_comets`（`galaxy_scene.js:94,104,562-565,652,687`），`moon` orb（`:438-442` r=0.55、`:507` emissive 1.6）。

根因在**布局层**：`moon` flag 只在 `nodeOrbits.tier===3` 时为真（`main.jsx:2536`），而 **tier3 只在聚焦某个 goal 时才生成**——
- 聚焦态：`evByTask` 把 `generated_by` 的 evidence 绕其 task 转、`tier:3`、14x 速度（`main.jsx:2086-2135`）→ 小彗星。
- 总览（fit）态：所有 evidence 统一给 `tier:2`、绕 project 的同心环（`main.jsx:2254-2265`），**不画逐 task 月亮/彗星**——注释明说「Per-task moons are a focused-view detail — too fine to draw zoomed out」（`main.jsx:2197`）。

**所以图1（总览）里你现在看到的**：evidence 作为 tier2 的小点，混在 project 的同心环里（紫色 fruit 环），没有彗尾、不快转——这就是为什么「彗星没了」。

**这是有意取舍**（总览太碎 → 缩放下噪声盖过结构）。若想总览也保留「task 已产出证据」的指示而不引入噪声，三个选项：
- **A（推荐，低）**：总览给「有 evidence 的 task」一个**静态微光点**（不画快彗尾），保留指示语义、零噪声。改 `main.jsx:2254-2265` 给这些 task 附 `hasEvidence` flag → orb 加一圈微 halo。
- **B（中）**：总览彗星减速到近静止（评审稿提过的分级降速），进 goal 才全速——`main.jsx:2135` 的 `orbitSpeed(Rm)*14` 按 focus 深度门控。
- **C**：维持现状，仅在图例（问题4）讲清「彗星只在进入 goal 后出现」。

---

## 问题 4 — 图2 说明面板不能折叠、不能滚轮

**能折叠，但有两个 bug**：

1. **滚轮失效（确诊）**：图例容器父节点 `.hd-graph3d-nav` 设了 `pointer-events: none`（`style.css:2053-2055`），用于让点击穿透到 canvas。子级 chip/toggle 各自 `pointer-events: auto` 重新启用，但 **`.hd-graph3d-encoding-list`（`style.css:2157-2169`，有 `max-height:220px; overflow-y:auto`）没有重新启用 pointer-events**。于是：列表能显示、能溢出，但鼠标事件穿透到下层 canvas → 滚轮被 OrbitControls 当成缩放吃掉，列表滚不动。
   **改成**：给 `.hd-graph3d-encoding-list`（和 `.hd-graph3d-legend` 滚动容器）加 `pointer-events: auto`；并在其上 `onWheel={e => e.stopPropagation()}` 防止冒泡到 canvas 缩放。

2. **折叠按钮可能也吃不到点击**：`.hd-graph3d-encoding-toggle`（`style.css:2136`）有 `cursor:pointer` 但**没显式 `pointer-events:auto`**——同样在 `pointer-events:none` 的父级下。截图里箭头是 `▾`（展开态）说明默认就是开的（`main.jsx:2832-2834`，localStorage 未设时默认 open），但点它未必能收起。
   **改成**：`.hd-graph3d-encoding-toggle { pointer-events: auto; }`。

3. **默认占满左下栏**：`encodingOpen` 默认 true（首次访问），7 行 + 滚动条喧宾夺主。
   **改成**：默认收起（`localStorage` 未设时返回 `false`，即把 `main.jsx:2834` 的判断反过来），首次给一行提示「点此看图例说明」。配合补全图例的中文翻译。

---

## 问题 5 — 图3 球体太亮/太暗、材质不行、不好看

**当前管线**（`galaxy_scene.js`）：
- 渲染器：`ACESFilmicToneMapping` + `toneMappingExposure 1.35`（`:166-167`），但经 EffectComposer，靠末尾 `OutputPass`（`:222`）才应用色调映射——这步是对的。
- 灯光：`AmbientLight(0x6c7aa6, 1.7)`（很强的冷环境光）+ key PointLight 1.0 + core PointLight 2.2（`:193-199`）。
- Bloom：`UnrealBloomPass(strength 0.85, radius 0.7, threshold 0.45)`（`:215`），低配降到 0.35（`:1701`）。
- 材质：`MeshStandardMaterial`，`emissiveIntensity` = placeholder 0.22 / moon 1.6 / goal 1.25~1.85 / 其他 0.62（`:507-517`），`roughness 0.42`、`metalness 0.22`（`:526-527`）。

**「要么太亮要么太暗」的根因**：
1. **bloom threshold 0.45 偏低 + goal emissive 高达 1.85**：超过阈值的像素全部泛光，活跃 goal 糊成一团白；而 `roughness 0.42 + metalness 0.22` 的 MeshStandard 球在只有点光源、强环境光下，背光面几乎全黑——**同一颗球高光过曝、暗面死黑**，动态范围两头顶死。
2. **AmbientLight 1.7 太强**：本意托底暗面，但冷蓝环境光（`0x6c7aa6`）把所有球染灰、压低对比，与「North Star 点光制造昼夜终结线」的设计（`:475-480` 注释）打架——环境光太亮就没有终结线了。
3. **goal 注释说「planet lit by core light」**，但 emissive 1.85 让它其实是自发光球，core 光的塑形几乎无效 → 看起来「塑料感」。

**改成（建议组合，纯前端常量，中等工作量）**：
- **降环境光**：`AmbientLight 1.7 → 0.5~0.7`，让 core PointLight 重新主导塑形，恢复昼夜终结线。
- **提 bloom threshold**：`0.45 → 0.62~0.7`，只让真正最亮的核/月亮泛光，goal 不再整颗糊白。可同时 `strength 0.85 → 0.6`。
- **拆 goal 的 size/brightness 职责**：注释已声明「进度靠 size 不靠亮度」，那就把 active goal 的 `emissiveIntensity 1.85 → 0.9~1.1`（仍亮于 project 的 0.62，但不过曝），让 core 光的高光/暗面差异回来。
- **材质质感**：goal 可换 `roughness 0.55、metalness 0.1`（更像有大气的行星、少塑料感）；或给 goal 加一层极淡 `clearcoat`（需 `MeshPhysicalMaterial`）。evidence/task 保持 Standard。
- **暗面托底**：给 core PointLight 之外加一个极弱的填充 `HemisphereLight(sky #2a3a66, ground #0a0f24, 0.3)`，避免背光面死黑——比全局 AmbientLight 更有方向感。

**验证**：改完用 playwright 截 18503 dev 的 `/dashboard?view=3d` 总览 + 聚焦两态，确认 goal 不糊白、有明暗面、project/task 仍可辨。

---

## 问题 6 — task/project 碰撞、20~30 个 task 时混乱（用公式保证，非微调参数）

**先确认数据链**：evidence 小彗星**确实绕 task 转**。聚焦态 Tier3（`main.jsx:2127-2135`）`evByTask` 按 `generated_by` 边把 evidence 绑到产出它的 task，`placeOnOrbit(ids, tid, tcenter, …)` 的 `parentId=tid`、`center=task位置`，scene `_updateOrbits` 每帧取 task 实时位置当圆心。嵌套轨道：task 绕 project、evidence 绕 task，与数据层级一致。

**碰撞根因（确诊）**：聚焦态 task 盘 `placeConcentric(tasks, pid, center, {baseR:10, gap:6, …})`（`main.jsx:2105-2107`）的几何参数撞了：
- project 球半径 `r_p` = `max(5,min(9,5·ride))` → **5~9**（`galaxy_scene.js:458`）
- task 球半径 `r_t` = `max(2.5,min(4.5,2.6·ride))` → **2.5~4.5**（`galaxy_scene.js:461`）
- task 内圈半径只有 `baseR=10`，task 球内边缘 = `10−4.5=5.5 < r_p(9)` → **task 球插进 project 球约 3 单位**（`offsetY:5` 抬不过 project 半径）。

**为什么微调常量治不了本**：`PER_RING=6` 固定、`baseR/gap` 固定，与 task 数 N 无关。N=2 时盘太空；N=30 时 5 环 × 6 = 30 硬塞，内环半径上塞不下 6 个（见约束 A），必然重叠或撑大撞邻居。必须**从碰撞约束反推参数**，让环数 K 和每环容量随 N 自适应。

### 四条碰撞约束

记 `r_p≤9`、`r_t≤4.5`、安全余量 `s≈2`、偏心因子 `f=1−ecc≈0.84`。

- **约束 B（内圈脱离 project 球）** —— 修「task 焊在 project 上」：
  ```
  R₀ = r_p + r_t + s ≈ 9 + 4.5 + 2 = 15.5   → baseR = 16
  ```
  当前 `baseR=10 < 15.5`，头号碰撞根因。

- **约束 A（同环相邻 task 不撞）** —— 修「task 混乱」。半径 R 的环最多放：
  ```
  m_max(R) = π / arcsin( (r_t + s/2) / (f·R) )
  ```
  代入：R=16→**7 个**、R=27→**12 个**、R=38→**18 个**。当前在 R=10 上塞 6 个，而 m_max(10)≈4 → `6>4 必重叠`。

- **约束 C（相邻同心环不互撞）**：
  ```
  ΔR (gap) = 2·r_t + s ≈ 11
  ```
  当前 `gap=6 < 11`，外环 task 蹭内环。

- **约束 D（task 系统装进 project 的角度槽位）** —— 修 project↔project 碰撞。project 绕 goal 在 `R1=58+min(P,8)·7`（`main.jsx:2059`）均布，相邻 project 弦距 `2·R1·sin(π/P)`，要求：
  ```
  R_out + r_t ≤ R1·sin(π/P) − s/2
  ```
  预算：P=4 时 ≈60，P=8 时 ≈43（R_out = 最外环半径）。

### 自适应公式（替代固定 PER_RING=6）

```
环半径   R_k   = R₀ + k·ΔR            (R₀=16, ΔR=11 → 16, 27, 38, 49…)
环容量   cap_k = floor(m_max(R_k))    (→ 7, 12, 18, 23…)
取最小 K 使  Σ_{k<K} cap_k ≥ N
按 cap_k 比例把 N 个 task 分配到各环（非 round-robin 均分，避免内环挤、外环空）
角度均布  ang_i = phase + (i / chunk_k.length)·2π   (已有逻辑，placeOnOrbit:1942)
```

**验算 N=30**：K=3 环（16,27,38），容量 7+12+18=37 ≥ 30 ✓，外径 = 38+4.5 = 42.5。
- P=4 预算 60 → 42.5 ✓ 宽松
- P=8 预算 43 → 42.5 ✓ 恰好（8 project × 30 task 是物理极限）

**超预算 D 的兜底（不静默重叠）**：当 `R_out+r_t > R1·sin(π/P)−s/2`（如 P=10 且每个 30 task），二选一并 `log()`：(a) 把 project 的 `R1` 系数往外推；(b) 把 `done` 状态 task 收进更密的「历史微环」（半径更小、球更小）。诚实优于假装放得下。

### 落地改法

- `main.jsx:1963` `PER_RING` 常量删除/弃用，`placeConcentric`（`:1964`）改成上面的容量驱动 K + 比例分配。
- `main.jsx:2105-2107` 调用处 `baseR:10→16`、`gap:6→11`（或让 `placeConcentric` 内部用约束 B/C 自算，调用处只传 `r_p`）。
- `r_p`/`r_t`/`s` 抽成布局层常量，与 `galaxy_scene.js:458/461` 的尺寸带保持单一来源（避免两处漂移）。
- 总览态（`main.jsx:2254` 的 `placeConcentric`）同享新公式，连带受益。

**验证**：18503 dev 灌一个 30-task 的 project（`.dev-data/profiles/dev/`），playwright 截聚焦态确认：task 不插进 project、同环不重叠、环间不蹭、外径不撞邻 project；再截 P=8 边界场景确认兜底 `log` 触发。**e2e 只验颜色数/console error、不验几何，碰撞必须截图核验。**

---

## 优先级

| 序 | 项 | 工作量 | 风险 | 收益 |
|---|---|---|---|---|
| 1 | 补 47 个缺失 i18n key（zh+en） | S | 低 | 立刻消除满屏中英混杂（含问题1/3/4 文案） |
| 2 | 图例 pointer-events + 默认收起（问题4） | S | 低 | 面板可滚可折叠、不再喧宾夺主 |
| 3 | 灯光/bloom/emissive 调参（问题5） | M | 低 | 球体质感与明暗范围 |
| 4 | goal rail / showArchived 接线（问题2） | M | 中 | 看到 completed/archived 目标 |
| 5 | 总览 evidence 指示（问题3，选 A/B） | M | 中 | 总览保留「已产出证据」语义 |
| 6 | goal-relevant lit 精确化（问题1） | S | 低 | 去掉近似，分子分母可信 |
| ★ | 碰撞自适应公式（问题6，placeConcentric 重写） | M | 中 | 任意 task 数都不碰撞/不混乱，治本 |

> 1–3 都是纯前端常量/翻译，互相独立、可单独上。建议从 1 开工。
> 问题 6（★）是几何治本项：有确定性公式兜底，建议与问题 5 一并做（同改聚焦布局），改后必须 30-task + P=8 两个场景截图核验。

---

## 问题 7 — 归档/暂停 goal 在 chip rail 不可见、不可编辑

> 2026-06-28 在 dev profile 实跑发现：goals.yaml 里 status=archived / paused / completed
> 的 goal **在 3D graph 上以「熄灭星」呈现**（已实现，看得到位置 + 颜色 + 标签），
> 但**在顶部 ACTIVE GOALS chip rail 里不显示**，于是用户点不到「编辑」入口去改它们的
> title / target_skills / 复活成 active。点 graph 上的熄灭星只能开右侧 Details 抽屉（只读
> 元信息），没有「编辑这个 goal」按钮——结论：归档 goal 是只看不动的状态。

### 根因（已读代码）

1. **payload 只发 active goals**：`home_dashboard.py:1788` 把 `book.active_goals()` 的过滤结果
   赋给 `active_goals_payload`，注入 `payload["active_goals"]`。`active_goals()` 在
   `goals.py:335-337` 硬过滤 `status == "active"`，所以 archived/paused/completed **整族不进
   `active_goals` 列表**。
2. **chip rail 只读 active_goals**：`main.jsx:837` 的 `ContextHeader` 渲染 chip 用的是
   `payload.activeGoals`（normalizePayload 来自 `active_goals`）。chip rail 因此天然看不见
   archived/paused/completed。
3. **goalById 只查 active_goals**：`main.jsx:468` 的 `goalById(payload, goalId)` 遍历
   `payload.activeGoals`。即使前端能拿到 archived goal 的 id，`setGoalEditor({mode:"edit",
   goalId})` 在 4741 行 `goalById(payload, goalEditor.goalId)` 返回 null →
   `inlineGoalEditor` 不渲染 → 编辑表单永远打不开。
4. **graph 详情抽屉无「编辑此 goal」入口**：抽屉只显示 record_id / status / 标签等只读元
   信息，没有 button 去触发 `setGoalEditor`。

### 修法（两步，互相独立）

**Step A · 后端 payload 暴露 `all_goals` (S, 1-2 文件)**

`home_dashboard.py:1788` 附近，把所有 goal 的 compact view 也发给前端，跟 active_goals 并存：

```python
all_goals_payload = [
    _compact_goal_view(goal, ui=ui, ...)  # 跟 active_goals_payload 同 schema
    for goal in book.goals
]
payload["all_goals"] = all_goals_payload
```

`_compact_goal_view` 可以是 `active_goals_payload` 已经在用的同一个函数（带 progress /
target_date / stalled / status）。**关键**：连 archived/paused/completed 一起序列化，前端再
按需过滤。

`normalizePayload` (payload.js) 加 `allGoals: asArray(source.all_goals).map(normalizeGoalCard)`。

**Step B · 前端：chip rail + 编辑入口都从 allGoals 走 (M, 改 3 处)**

1. `goalById(payload, goalId)` 改为先查 `payload.allGoals`、回退 `payload.activeGoals`，让
   archived goal 也能查到，不破坏既有调用方。
2. `ContextHeader` 的 `<div className="hd-goal-rail">` chip 渲染源由 `activeGoals` 改成
   `allGoals`，并按 status 分组：active chip 用现状样式，archived/paused/completed chip 用
   「熄灭」样式（已有 `.hd-goal-pill.stalled` 可复用，再加一个 `.hd-goal-pill.extinguished`
   做更明显的灰白 + 删除线 title）。**默认只显 active**——加一个跟 graph 同款的「Show
   archived / paused goals」开关（`hd-canvas-archived-toggle` 已经在 graph 工具栏上，复用
   state，rail 跟着切换），避免新用户被 8 个 chip 淹没。
3. 「编辑此 goal」按钮：chip 的 click 区域已经走 `onSelectGoal(id)`，archived chip 上加个
   小铅笔 icon 触发 `onEditGoal(id)`，跟 active chip 的「Edit goal」二级按钮（4852 行 的
   `onEditGoal` prop 已经存在）走同条路。

### 工作量 / 风险

| 项 | 工作量 | 风险 | 收益 |
|---|---|---|---|
| Step A (payload 加 all_goals) | S | 低 | 前端能拿到完整 goal 列表 |
| Step B.1 (goalById 兼容 allGoals) | XS | 低 | 编辑路径解锁 |
| Step B.2 (chip rail 加开关 + 渲染熄灭 chip) | S–M | 中 | 看见 + 区分历史 goal |
| Step B.3 (chip 上的编辑按钮) | XS | 低 | 一键复活/改名 |

### 验证

1. dev profile（已有 `g_archived_demo`/`g_paused_demo`/`g_influence_2026` 100% active）：
   - 默认 rail：4 个 active chip
   - 开 archived toggle：6 个 chip，2 个用 extinguished 样式
2. 点 archived chip 的铅笔 icon → 编辑表单弹出 → 改 status 为 active → 保存 → rail 上消失，
   active 列表多 1。
3. graph 的熄灭星仍照旧（status 字段没动），与 chip rail 视觉一致。

### 不做（明确缩小范围）

- **不**改 `active_goals()` 的过滤语义——它在很多别处被当作"今天要看的 goal"使用（agent
  context、growth log 推断等），扩大它的返回会污染上游业务逻辑。新加 `all_goals` 字段是
  附加，不影响既有调用。
- **不**给 graph 详情抽屉加编辑入口——chip rail 已经是更自然的编辑面板，详情抽屉保持
  「只读元数据 + 跳转」语义。
