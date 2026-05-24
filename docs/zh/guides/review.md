---
status: active
owner: product
last_verified: 2026-05-24
source_of_truth: true
---

# Review 使用说明

Review 用来把一段时间内的 activity、Done、learning 和 inbox 信号整理成候选：证据候选、下一步行动候选、公开草稿候选。它是复盘后的收束页面，不会自动发布内容。

## 入口与输入

- 入口：Streamlit 主应用 `8501` 的 `Review` 页面。
- 时间窗口：本周、上周、最近 30 天或自定义。
- 输入来源：activity log、Kanban Done、学习记录、inbox 和公开输出候选。

## 推荐流程

1. 选择时间窗口，点击 `生成候选`。
2. 看 `Summary`，确认 Done、证据候选、下一步候选和公开草稿候选数量是否合理。
3. 在 `Evidence candidates` 中勾选要保留的候选：
   - `Save selected to Activity`：只留痕，不改 evidence pool。
   - `Apply selected`：写入 evidence pool，并可把来源 Done 标记 crystallized。
4. 在 `Next action candidates` 中勾选要继续推进的行动，保存到 Activity 或应用到 Kanban。
5. 在 `Public draft candidates` 中创建 draft blog。这里永远不会发布，只会创建草稿。
6. 在 `Method notes` 查看候选生成依据；在 `Agent Activity` 查看写入记录。

## 与 Evidence Review 的关系

Review 偏“时间窗口复盘”和候选生成；Evidence Review 偏“证据质量、技能关联、状态风险和 claim 审阅”。如果你已经有明确的 Done 任务要变成证据，优先用 Evidence Review；如果你想从一周工作里批量发现候选，先用 Review。

## 安全边界

- 所有文件写入都需要选择行并点击应用。
- Public draft 只创建 draft，不发布。
- Evidence 写入后仍建议到 Evidence Review 补充强度、置信度、公开准备度和技能关联。
