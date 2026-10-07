---
name: nblane
description: 读写用户的 nblane 成长档案：打卡、加任务、改任务/子任务状态、排期、阶段计划、占卜、查看星图/看板/编年史，以及撤销自己刚做的操作。用户在聊天里提到打卡、任务、计划、习惯、占卜或"撤销刚才那个"时使用。
metadata:
  openclaw:
    os: [linux]
    requires:
      bins: [bash, python3]
---

# nblane：成长档案读写

所有调用走 `{baseDir}/../bin/nblane_api`（以 `openclaw` 服务账号访问 nblane HTTP API），
输出 JSON。完整子命令见 `nblane_api --help`。

## 三类写入

| 类型 | 例子 | 你要做的 |
|------|------|----------|
| 日常操作 | 打卡、加任务、改任务字段、勾子任务/todo、移动列、排期、阶段计划增改、新建目标/项目、记入收件箱、添加资料 | 直接执行，执行后用一句话告诉用户做了什么 |
| 重要操作 | 所有删除、一次超过 3 条的批量操作、修改目标/北极星/技能点、编辑或评审证据、套用计划模板、批量导入资料 | 先在聊天里确认，用户同意后再执行（见下） |
| 只能在页面做 | 发布公开站、简历、内容工作台、审批队列、权限、系统设置 | 告诉用户去 nblane 页面操作（接口会返回 403 `agent_forbidden`） |

## 确认流程（重要操作）

1. 直接运行命令（不只是 delete，post/patch 也可能需要确认）。若返回 `"confirmation_required": true`（退出码 3），**什么都还没发生**。
2. 把 `summary` 原样告诉用户，问"确认吗？"。不要替用户回答，不要在同一轮里自己确认。
3. 只有用户明确同意（"确认""好""删吧"之类）后，在**完全相同**的命令前加
   `--confirm <confirm_id>` 重新运行。确认码 10 分钟有效、只能用一次，换了参数就失效。
4. 用户拒绝或没回应：放弃，不要重试。

```bash
"{baseDir}/../bin/nblane_api" delete "/profiles/<档案>/kanban/cards/<任务id>"
# → {"confirmation_required": true, "summary": "删除任务「…」（Queue）", "confirm_id": "cf_…"}
# 用户同意后：
"{baseDir}/../bin/nblane_api" --confirm cf_… delete "/profiles/<档案>/kanban/cards/<任务id>"
```

## 撤销

你做的每一次写入都能撤销（保留 30 天）。通过 MCP 工具做的写入也在同一份记录里。

- `nblane_api recent` 列出最近操作（新的在前），每条有 `id`、`summary`、`status`。
- `nblane_api undo <id>` 撤销一条。`status` 为 `conflict` 表示之后有人改过，撤销会被拒绝，
  请用户到页面处理。
- 用户说"撤销刚才那个""删错了"时：先 `recent`，对照 `summary` 找到那条再 `undo`，
  并告诉用户撤销了什么。

## 常用命令

```bash
nblane_api checkin <习惯> [--summary …] [--count N --unit km] [--plan <计划id>]
nblane_api post "/profiles/<档案>/kanban/cards" '{"title": "…", "section": "Queue"}'
nblane_api patch "/profiles/<档案>/kanban/cards/<任务id>" '{"todos": [{"text": "…", "done": true}]}'
nblane_api post "/profiles/<档案>/kanban/cards/<任务id>/done"
nblane_api plans | plan-show <计划id> | board | starmap | chronicle
nblane_api divine --mode play|serious [--question …]
```

`patch` 的 `todos` 是整体替换：先 `board` 或 GET 任务拿到完整列表，只改要改的那一项再整体提交。
