# 每日复盘（21:30）

> 模板说明：把 `<profile>` 替换为你的 profile 名，把 `https://spa.<域名>`
> 替换为你的 SPA 地址。

## nblane API 调用约定

- 命令形态：`~/.openclaw/workspace/skills/bin/nblane_api --profile <profile> <子命令>`。
  客户端自动登录并复用 cookie；服务账号密码从环境变量
  `NBLANE_OPENCLAW_API_PASSWORD` 读取。若报密码未设置，回复主人
  「nblane 服务账号密码未配置」，不要索要或转述密码本身。
- 分级授权（必须严格遵守）：
  1. 删除类操作（销印/删打卡、删项目、丢弃收件箱）一律禁止调用 API；
     回复「删除请到 SPA 页面操作」并附对应深链（看板/项目：
     `https://spa.<域名>/p/<profile>/projects`）。
  2. 其余写操作（打卡、移 Done、结晶 draft/apply、证据评审指令）：先用
     一句话复述动作 → 等主人回「好」→ 执行 → 回执（结果摘要 + 关键字段）。
  3. 所有 GET 与占卜免确认。
- 降级：任何 nblane_api 调用失败（非零退出或输出含 error 字段）时，回复
  「nblane 暂不可达」并跳过该动作继续复盘；不要重试超过一次，不要编造
  数据。

## 任务步骤

1. 回顾今天的会话与你的 daily memory；情景记忆照常由你自治维护。
2. 通过 nblane MCP 资源 `profile://kanban` 读取看板原文，并调用
   `nblane_api --profile <profile> board`，对照今早早报给出的重点
   与当前看板，盘点完成情况。
3. 对可验证的进展，调用 MCP 工具 `append_growth_log` 与 `log_interaction`
   写回 nblane 成长档案。
4. 一键动作（对话确认级，逐条询问，主人回「好」才执行）：
   - 对今天完成的在看卡片：「把 X 移到 Done？」→ 确认后
     `nblane_api --profile <profile> post /profiles/<profile>/kanban/cards/<卡片id>/done`
     → 回执新状态。
   - 对已在 Done 且未结晶的卡片：「给 Done 的 Y 起结晶草稿？」→ 确认后
     `nblane_api --profile <profile> post /profiles/<profile>/crystallize/draft '{"task_ids":["<任务id>"]}'`
     （规则版同步返回，无需 LLM）→ **先把草稿全文回显给主人** → 主人再次
     确认后才
     `nblane_api --profile <profile> post /profiles/<profile>/crystallize/apply '<草稿patch的JSON>'`。
   - 主人主动说「<习惯>打卡」：复述确认 →
     `nblane_api --profile <profile> checkin <习惯名>` → 回执，并回读
     `nblane_api --profile <profile> board` 附上最新 streak。
5. 证据评审不代办：评级与技能关联是主人的仪式。只调用
   `nblane_api --profile <profile> get /profiles/<profile>/evidence-stages`
   取待评审计数，连同快评深链
   `https://spa.<域名>/p/<profile>/evidence?stage=review` 一起送达。若主人在
   对话里明确指令（如「接受 E1 并关联 <技能id>」），按第 2 级复述确认后调
   对应 review / skill-links 接口。
6. 任何改变既有事实的 MCP 写仍走 candidate 审批，不要直接改文件。
