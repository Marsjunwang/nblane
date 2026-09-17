---
status: active
owner: product
last_verified: 2026-09-16
source_of_truth: true
---

# Kanban 使用说明

Kanban 是本周执行面。它回答“现在做什么、做到哪一步、完成后如何进入证据审阅”。

## 什么时候使用

- 捕捉任务、整理队列、推进 Doing、收尾 Done。
- 管理学习和运动的轻量 check-in。
- 让 AI 辅助拆子任务或澄清模糊任务。
- 把超出本周执行面的卡片派给外部 agent（Codex / opencode）处理。

## 推荐流程

1. 新想法先进入 Queue 或 Inbox。
2. Doing 保持小而清晰，确保能在当前周期内收尾。
3. 任务详情写清结果、背景、阻塞和链接。
4. 子任务用于可勾选执行步骤，不用于写长文档。
5. Done 任务完成后进入 Evidence Review，生成并人工确认 evidence。

## 快速添加（quick add）

看板工具栏的快速添加支持自然语言：输入「把评审 Narwal 论文加到 Queue #papers 周五前」会自动拆出标题、列（Doing/Queue/Someday）、`due: <日期>`（写入详情行）和 #标签，并在 toast 里回显解析结果；普通文本仍按纯标题建卡。识别为证据记录的文本（如「记一条证据：…」）不会建卡，请改用 Evidence Review 页录入（证据写入保持单一通道）。

## 派给 agent

卡片菜单的「派给 agent」可把任务交给外部执行器：

1. 在卡片内联区选择 harness（codex / opencode）、role（researcher / resume_strategist / remote_dev / reviewer），可补一句指令，确认后写入 `agent-tasks.yaml`（每次派单生成新 id，`related.kanban_task_id` 记录来源卡片），并把最新一单的 id 写回卡片（`agent_task_id` 元数据；在卡片编辑里清空即解绑）。
2. 卡片显示派单状态徽标（待领取/运行中/候选待审…）。外部 agent 提交结果后徽标变为「候选待审」，点击可跳到 Agent Activity 页审批。徽标不做实时轮询，外部状态变化后用 Reload 刷新即可。
3. 同一卡片可多次派单，历史派单按 `related.kanban_task_id` 反查；卡片只跟踪最新一单。

## 写入边界

本页写入 `kanban.md`，并同步任务的项目归属到 `project-board.yaml`。

- 看板页在每次操作时自动保存。任务 id 在任务首次保存时随机生成并写入 `kanban.md`，之后编辑标题、详情或拖动列都不会改变 id；证据池里的 `kanban:<id>` 引用因此能长期解析。
- 若 `kanban.md` 在页面打开期间被其他入口（首页快捷添加、MCP、CLI）修改，保存前会先重载磁盘内容并把本次操作重放合并，双方改动都会保留；只有当你的改动目标任务已被外部删除时，该项改动会被放弃并弹出提示。

## AI 行为

Kanban AI 只生成候选，例如子任务草案和任务理解建议。只有你接受候选后，内容才会写入文件。

- 点击「分析差距 / 拆解子任务」后，AI 在后台运行（卡片显示「AI 处理中」，菜单项暂时禁用），不阻塞看板操作；结果就绪后自动显示在卡片上。生成期间可随时用卡片的 Discard 动作取消。
