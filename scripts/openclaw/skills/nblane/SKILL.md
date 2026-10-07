---
name: nblane
description: 读写用户的 nblane 成长档案：打卡、加任务、改任务/子任务状态、排期、阶段计划、占卜、查看星图/看板/编年史，以及撤销自己刚做的操作。用户在聊天里提到打卡、任务、计划、习惯、占卜或"撤销刚才那个"时使用；定时任务调用 nblane 时也按这里的规则执行。
metadata:
  openclaw:
    os: [linux]
    requires:
      bins: [bash, python3]
---

# nblane：成长档案读写

这是调用 nblane 的唯一规则来源。定时任务的提示词只写要做什么，怎么调用、哪些能直接做、
哪些要先问，都以这里为准。

## 调用方式

- 读写一律用 `{baseDir}/../bin/nblane_api <子命令>`（以 `openclaw` 服务账号访问 nblane
  HTTP API），输出 JSON。完整子命令见 `nblane_api --help`。不要用 nblane 的 MCP 工具或
  `profile://` 资源：那条通道不经过账号权限，留给 Cursor 这类本机客户端。
- 服务账号密码从环境变量 `NBLANE_OPENCLAW_API_PASSWORD` 读取。若报密码未设置，告诉用户
  「nblane 服务账号密码未配置」，不要索要或转述密码本身。
- 不要读取 nblane 数据目录下的文件，也不要直接改文件；一律走 `nblane_api`。

## 成功与失败

- 退出码 0 且输出是 JSON 就是成功，必须使用其中的数据。`"total": 0`、`"entries": []`
  这类空集合是正常数据，不是失败。
- 退出码 3 + `"confirmation_required": true` 是在等用户确认（见下），不是失败。
- 其他非零退出或输出带 `error` 字段才是失败：告诉用户「nblane 暂不可达」，跳过这一步
  继续做别的；最多重试一次，不要编造数据。

## 三类写入

| 类型 | 例子 | 你要做的 |
|------|------|----------|
| 日常操作 | 打卡、加任务、改任务字段、勾子任务/todo、移动列、排期、阶段计划增改、新建目标/项目、添加资料、结晶草稿 | 用户下了指令就直接执行，执行后用一句话告诉用户做了什么 |
| 重要操作 | 所有删除、一次超过 3 条的批量操作、修改目标/北极星/技能点、编辑或评审证据、结晶 apply、套用计划模板、批量导入资料 | 先在聊天里确认，用户同意后再执行（见下） |
| 只能在页面做 | 发布公开站、简历、内容工作台、权限、系统设置 | 接口会返回 403 `agent_forbidden`；告诉用户去 nblane 页面操作，附上相关页面链接 |

读取和占卜不用确认。你主动提出的建议（"要不要把 X 移到 Done？"）先问，用户回「好」再做。

## 确认流程（重要操作）

1. 直接运行命令（不只是 delete，post/patch 也可能需要确认）。若返回
   `"confirmation_required": true`（退出码 3），**什么都还没发生**。
2. 把 `summary` 原样告诉用户，问"确认吗？"。不要替用户回答，不要在同一轮里自己确认。
3. 只有用户明确同意（"确认""好""删吧"之类）后，在**完全相同**的命令前加
   `--confirm <confirm_id>` 重新运行。确认码 10 分钟有效、只能用一次，换了参数就失效。
4. 用户拒绝或没回应：放弃，不要重试。

```bash
"{baseDir}/../bin/nblane_api" delete "/profiles/<档案>/kanban/cards/<任务id>"
# → {"confirmation_required": true, "summary": "删除任务「…」", "confirm_id": "cf_…"}
# 用户同意后：
"{baseDir}/../bin/nblane_api" --confirm cf_… delete "/profiles/<档案>/kanban/cards/<任务id>"
```

## 撤销

你做的每一次写入都能撤销（保留 30 天）。

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
nblane_api post "/profiles/<档案>/kanban/cards/<任务id>/move" '{"target_section": "Queue"}'
nblane_api post "/profiles/<档案>/crystallize/draft" '{"task_ids": ["<任务id>"]}'
nblane_api summary | goals | plans | plan-show <计划id> | board | starmap | chronicle [--limit N] | health
nblane_api growth "<一句话进展>"                       # 写进成长日志（可撤销）
nblane_api get "/profiles/<档案>/evidence-stages"
nblane_api divine --mode play|serious [--question …]
```

`patch` 的 `todos` 是整体替换：先 `board` 或 GET 任务拿到完整列表，只改要改的那一项再整体提交。
