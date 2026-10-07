# 每日复盘（21:30）

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
- 降级：任何 nblane_api 调用失败（非零退出或输出含 error 字段；退出码 3 + `confirmation_required` 是等待确认，不算失败）时，回复
  「nblane 暂不可达」并跳过该动作继续复盘；不要重试超过一次，不要编造
  数据。

## 任务步骤

1. 回顾今天的会话与你的 daily memory；情景记忆照常由你自治维护。
2. 通过 nblane MCP 资源 `profile://kanban` 读取看板原文，并调用
   `nblane_api --profile <profile> board`，对照今早早报给出的重点
   与当前看板，盘点完成情况。
3. 对可验证的进展，调用 MCP 工具 `append_growth_log` 与 `log_interaction`
   写回 nblane 成长档案。
4. 一键动作（你主动提出的建议，逐条询问，主人回「好」才执行）：
   - 对今天完成的在看卡片：「把 X 移到 Done？」→ 确认后
     `nblane_api --profile <profile> post /profiles/<profile>/kanban/cards/<卡片id>/done`
     → 回执新状态。
   - 到期 someday 提醒：从第 2 步的 board 数据找出「Someday / Maybe」区里
     排期（planned_start，即期望激活日）已到期的卡，逐条列给主人：
     「Someday 的 Z 排期已到，要激活入 Queue 吗？」→ 主人回「好」后
     `nblane_api --profile <profile> post /profiles/<profile>/kanban/cards/<卡片id>/move '{"target_section":"Queue"}'`
     → 回执新状态（排期保留，不主动清除）。
   - 对已在 Done 且未结晶的卡片：「给 Done 的 Y 起结晶草稿？」→ 确认后
     `nblane_api --profile <profile> post /profiles/<profile>/crystallize/draft '{"task_ids":["<任务id>"]}'`
     （规则版同步返回，无需 LLM）→ 调
     `nblane_api --profile <profile> post /profiles/<profile>/crystallize/apply '<草稿patch的JSON>'`，
     它会返回 `confirmation_required` → 把草稿全文连同 `summary` 一起发给主人 →
     主人同意后加 `--confirm <confirm_id>` 重跑（只确认这一次）。
   - 主人主动说「<习惯>打卡」：直接
     `nblane_api --profile <profile> checkin <习惯名>` → 回执，并回读
     `nblane_api --profile <profile> board` 附上最新 streak。
5. 证据评审不代办：评级与技能关联是主人的仪式。只调用
   `nblane_api --profile <profile> get /profiles/<profile>/evidence-stages`
   取待评审计数，连同快评深链
   `https://spa.<域名>/p/<profile>/evidence?stage=review` 一起送达。若主人在
   对话里明确指令（如「接受 E1 并关联 <技能id>」），调对应 review / skill-links
   接口，按第 2 级的确认流程完成。
6. MCP 写工具遵守同样的分级（`delete_kanban_card`、`log_skill_evidence` 会先返回
   `confirmation_required`）；不要直接改文件。
