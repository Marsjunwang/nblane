# 每日计划（晨报 08:30）

> 模板说明：把 `<profile>` 替换为你的 profile 名，把 `https://spa.<域名>`
> 替换为你的 SPA 地址。`nblane_api`（install.sh 生成的 venv 包装命令）
> 默认 profile 由环境变量 `NBLANE_API_PROFILE` 决定，prompt 里显式传
> `--profile` 更稳。

## nblane API 调用约定

- 命令形态：`~/.openclaw/workspace/skills/bin/nblane_api --profile <profile> <子命令>`。
  客户端自动登录并复用 cookie；服务账号密码从环境变量
  `NBLANE_OPENCLAW_API_PASSWORD` 读取。若报密码未设置，回复主人
  「nblane 服务账号密码未配置」，不要索要或转述密码本身。
- 分级授权（与 nblane 写入策略一致，必须严格遵守）：
  1. 日常操作（打卡、加任务、移列/移 Done、勾 todo、排期、结晶 draft、记入收件箱）：
     主人在对话里下了指令就直接执行，执行后用一句话回执。你主动提出的建议仍要先问，
     主人回「好」再执行。
  2. 重要操作（所有删除、一次超过 3 条的批量、改目标/北极星/技能点、证据评审与关联、
     结晶 apply）：直接调用；若返回 `"confirmation_required": true`（退出码 3），什么都
     还没改。把 `summary` 原样发给主人，主人明确同意后，在完全相同的命令前加
     `--confirm <confirm_id>` 重跑。不要替主人确认，主人拒绝就放弃。
  3. 只能在页面做（公开站发布、简历、审批队列、设置；接口返回 403 `agent_forbidden`）：
     附深链 `https://spa.<域名>/p/<profile>/projects` 请主人去 SPA 操作。
  4. 撤销：主人说「撤销刚才那个」「弄错了」→ `nblane_api --profile <profile> recent`
     对照 `summary` 找到那条 → `nblane_api --profile <profile> undo <id>` → 回执撤销了什么。
     `status` 为 `conflict` 时撤销会被拒绝，请主人到页面处理。
  5. 所有 GET 与占卜免确认。
  本任务全是读操作。
- 成功判定（严格遵守）：nblane_api 退出码为 0 且输出是 JSON 即为成功，
  必须解析使用其中的数据；`"total": 0`、`"entries": []` 等空集合是正常
  数据，不是失败。只有非零退出或输出含 error 字段才算失败（退出码 3 + `confirmation_required` 是等待确认，不算失败）。
- 降级：调用失败时在晨报相应位置标注「nblane 暂不可达」，用 MCP 读本完成
  其余部分；不要重试超过一次，不要编造数据。

## 任务步骤

1. 通过 nblane MCP 资源读取上下文：`profile://kanban`（当前看板）与
   `profile://goals`（目标）；可用资源清单见 `profile://summary`。
   不要读取任何绝对路径下的文件。
2. 依次调用（均为只读）：
   - `nblane_api --profile <profile> starmap`：取星图计数（点亮 / 在学 /
     客星数）。
   - `nblane_api --profile <profile> chronicle --limit 40`：取近期编年
     （本月新立目标数、新镌星数，与首页简报行同源）。
   - `nblane_api --profile <profile> board`：取今日排期卡片与习惯待打卡
     清单。
3. 综合看板、目标与上述数据，生成不超过 3 条的今日重点，按优先级排序；
   末尾附一行星图计数与待打卡习惯清单。
4. 把晨报作为最终回复投递即可；不要修改任何 profile 文件。
