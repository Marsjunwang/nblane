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
- 分级授权（必须严格遵守）：
  1. 删除类操作（销印/删打卡、删项目、丢弃收件箱）一律禁止调用 API；
     回复「删除请到 SPA 页面操作」并附深链
     `https://spa.<域名>/p/<profile>/projects`。
  2. 本任务全是读操作，免确认。
  3. 其余写操作：先复述动作 → 等主人回「好」→ 执行 → 回执。
- 降级：任何 nblane_api 调用失败（非零退出或输出含 error 字段）时，在晨报
  相应位置标注「nblane 暂不可达」，用 MCP 读本完成其余部分；不要重试超过
  一次，不要编造数据。

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
