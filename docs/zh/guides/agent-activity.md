# Agent Activity 使用说明

Agent Activity 是跨页面 AI / Agent 候选的审计队列。

## 什么时候使用

- 查看 AI 或 Agent 生成的候选、补丁和写回结果。
- 处理失败的 apply 或 Codex 任务。
- 追踪某个候选来自哪个页面、会写到哪里。

## 推荐流程

1. 先按状态筛选 pending 或 failed。
2. 再按模块、类型或候选类型缩小范围。
3. 查看 preview、refs 和 changed paths。
4. 只有 owner 页面支持安全写回的候选才直接应用。
5. 过期但仍需要留痕的候选应标记丢弃，而不是删除。

## 写入边界

本页可以更新 activity item 状态。部分候选支持显式 apply，具体写入文件取决于 owner 页面。

## 注意事项

技术详情用于排查失败原因；产品判断优先看预览、引用和变更路径。
