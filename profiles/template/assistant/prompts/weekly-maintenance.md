# 每周巩固（周日 20:00，主会话）

> 模板说明：把 `<profile>` 替换为你的 profile 名，把 `https://spa.<域名>`
> 替换为你的 SPA 地址。

## nblane API 调用约定

- 命令形态：`~/.openclaw/workspace/skills/bin/nblane_api --profile <profile> <子命令>`。
  客户端自动登录并复用 cookie；服务账号密码从环境变量
  `NBLANE_OPENCLAW_API_PASSWORD` 读取。若报密码未设置，回复主人
  「nblane 服务账号密码未配置」，不要索要或转述密码本身。
- 分级授权（必须严格遵守）：
  1. 删除类操作一律禁止调用 API；回复「删除请到 SPA 页面操作」并附深链
     `https://spa.<域名>/p/<profile>/projects`。
  2. 本任务的 nblane_api 调用全是读操作，免确认；MCP 侧的写一律走
     candidate 审批。
  3. 其余写操作：先复述动作 → 等主人回「好」→ 执行 → 回执。
- 降级：任何 nblane_api 调用失败（非零退出或输出含 error 字段）时，周报
  体检一节标注「nblane 暂不可达」，其余部分照常；不要重试超过一次。

## 任务步骤

1. 自治整理你的 MEMORY.md / USER.md 与本周 daily notes（情景记忆归你维护）。
2. 通过 nblane MCP 资源 `profile://summary` 与 `profile://goals` 对照
   成长档案。
3. 把已稳定的偏好与新认识打包为 `submit_profile_model_candidate` 提交人审。
4. 把与技能树矛盾的记忆条目标记出来，整理成漂移报告提交审批。
5. 调用 `nblane_api --profile <profile> health` 取档案体检摘要（校验/
   同步类 issue 计数与重点项），作为「档案体检」一节附在周报末尾一并投递。
