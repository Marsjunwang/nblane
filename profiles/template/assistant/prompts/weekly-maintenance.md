# 每周巩固（周日 20:00，主会话）

> 模板说明：把 `<profile>` 替换为你的 profile 名，把 `https://spa.<域名>`
> 替换为你的 SPA 地址。

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
  本任务的 nblane_api 调用全是读操作；画像更新仍用 MCP 工具
  `submit_profile_model_candidate` 提交人审。
- 降级：任何 nblane_api 调用失败（非零退出或输出含 error 字段；退出码 3 + `confirmation_required` 是等待确认，不算失败）时，周报
  体检一节标注「nblane 暂不可达」，其余部分照常；不要重试超过一次。

## 任务步骤

1. 自治整理你的 MEMORY.md / USER.md 与本周 daily notes（情景记忆归你维护）。
2. 通过 nblane MCP 资源 `profile://summary` 与 `profile://goals` 对照
   成长档案。
3. 把已稳定的偏好与新认识打包为 `submit_profile_model_candidate` 提交人审。
4. 把与技能树矛盾的记忆条目标记出来，整理成漂移报告提交审批。
5. 调用 `nblane_api --profile <profile> health` 取档案体检摘要（校验/
   同步类 issue 计数与重点项），作为「档案体检」一节附在周报末尾一并投递。
