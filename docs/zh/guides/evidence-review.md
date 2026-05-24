---
status: active
owner: product
last_verified: 2026-05-24
source_of_truth: true
---

# Evidence Review 使用说明

Evidence Review 是把“已完成工作”变成可信证据、把证据变成可复用 claim 的审阅工作台。它不是自动写入器：AI 只生成候选，真正写入前都需要预览、选择和应用。

## 入口与职责

- 入口：Streamlit 主应用 `8501` 的 `Evidence Review` 页面。
- 主要文件：`evidence-pool.yaml`、`skill-tree.yaml`、`kanban.md`、`project-board.yaml`、`experience.yaml`、`research/sources.yaml`。
- AI 配置：页面右上角 `证据 AI`。它只影响当前 profile 的 Done 到证据草案、看板任务理解，不影响 Research 的论文翻译/Reader 配置。

## 推荐流程

1. 打开 `Done 队列 / 整理`，选择尚未 crystallized 的 Done 任务。
2. 点击 `生成 Done -> evidence 草案`，检查 AI 返回的池条目和技能树变更预览。
3. 只选择可信条目应用；如果来源 Done 已经被证据覆盖，保留“应用后标记 crystallized”。
4. 进入 `Evidence Pool` 补充强度、置信度、审阅状态、公开准备度和引用。
5. 进入 `技能关联`，把活跃 evidence 绑定到技能节点。
6. 进入 `项目 / 经历引用`，把 evidence 关联到项目案例、经历案例或 Research source。
7. 进入 `状态风险`，确认 solid/expert 技能有足够强的证据支撑。
8. 需要公开表达时，再到 `Claim Studio` 从 reviewed evidence 生成 public-ready claim 候选。

## AI 配置

`证据 AI` 提供两个动作的统一配置：

- `Done -> 证据模型`：从所选 Done 任务生成可审阅 evidence 草案。
- `任务理解模型`：在看板任务描述不完整时，先做任务理解和澄清。

引擎可选：

- `LLM`：使用侧边栏 AI / LLM 的服务商、base URL、API key 和默认模型。
- `Codex`：使用部署共享的 service-level Codex CLI，只读生成候选。

模型输入框留空时使用应用默认。这里保存的是当前 profile 的非密钥偏好，不会保存 API key。

## 常见问题

### 为什么不能让 AI 直接改状态？

技能状态是对外能力 claim。默认模式会忽略 AI 的 `status` 字段，只写证据和引用；允许 AI 更新状态时也只允许升级路径，且 `expert` 不会自动采信。

### Done 任务什么时候可以归档？

建议先完成 Done -> evidence 审阅并标记 crystallized，再用 Done housekeeping 批量归档。未 crystallized 的任务仍可归档，但页面会要求你确认风险。

### Research claim 和 Evidence claim 有什么区别？

Research claim 是带来源的工作断言，仍需要审阅。Evidence Review 中 accepted/reviewed 的证据和 public-ready claim 才适合进入输出链路。
