# 每日复盘（21:30）

> 模板说明：把 `<profile>` 替换为你的 profile 名，把 `https://spa.<域名>`
> 替换为你的 SPA 地址。
> `<workspace>` 换成 OpenClaw 工作区的绝对路径（`readlink -f ~/.openclaw/workspace`），
> 让每条命令都是 `nblane_api` 的完整路径；它不在 PATH 里，只写命令名时模型可能找不到。

调用 nblane（命令、成功/失败判定、哪些能直接做、哪些要先确认、撤销）一律按 nblane 技能（`skills/nblane/SKILL.md`）的规则执行，这里只写本任务要做什么。

命令一律写完整路径 `<workspace>/skills/bin/nblane_api`（下文已写好）。它不在 PATH 里，也不在 workspace 的 `bin/` 下，不要去那些地方找；直接照抄下面的命令执行。

## 任务步骤

1. 回顾今天的会话与你的 daily memory；情景记忆照常由你自治维护。
2. 调用
   `<workspace>/skills/bin/nblane_api --profile <profile> board`，对照今早早报给出的重点
   与当前看板，盘点完成情况。
3. 对可验证的进展，调用 `<workspace>/skills/bin/nblane_api --profile <profile> growth "<一句话进展>"` 写进成长日志。
4. 一键动作（你主动提出的建议，逐条询问，主人回「好」才执行）：
   - 对今天完成的在看卡片：「把 X 移到 Done？」→ 确认后
     `<workspace>/skills/bin/nblane_api --profile <profile> post /profiles/<profile>/kanban/cards/<卡片id>/done`
     → 回执新状态。
   - 到期 someday 提醒：从第 2 步的 board 数据找出「Someday / Maybe」区里
     排期（planned_start，即期望激活日）已到期的卡，逐条列给主人：
     「Someday 的 Z 排期已到，要激活入 Queue 吗？」→ 主人回「好」后
     `<workspace>/skills/bin/nblane_api --profile <profile> post /profiles/<profile>/kanban/cards/<卡片id>/move '{"target_section":"Queue"}'`
     → 回执新状态（排期保留，不主动清除）。
   - 对已在 Done 且未结晶的卡片：「给 Done 的 Y 起结晶草稿？」→ 确认后
     `<workspace>/skills/bin/nblane_api --profile <profile> post /profiles/<profile>/crystallize/draft '{"task_ids":["<任务id>"]}'`
     （规则版同步返回，无需 LLM）→ 把草稿全文发给主人看 → 调
     `<workspace>/skills/bin/nblane_api --profile <profile> post /profiles/<profile>/crystallize/apply '<草稿patch的JSON>'`
     （重要操作，按技能里的确认流程走）。
   - 主人主动说「<习惯>打卡」：直接
     `<workspace>/skills/bin/nblane_api --profile <profile> checkin <习惯名>` → 回执，并回读
     `<workspace>/skills/bin/nblane_api --profile <profile> board` 附上最新 streak。
5. 证据评审不代办：评级与技能关联是主人的仪式。只调用
   `<workspace>/skills/bin/nblane_api --profile <profile> get /profiles/<profile>/evidence-stages`
   取待评审计数，连同快评深链
   `https://spa.<域名>/p/<profile>/evidence?stage=review` 一起送达。若主人在
   对话里明确指令（如「接受 E1 并关联 <技能id>」），调对应 review / skill-links
   接口（重要操作，按技能里的确认流程走）。
