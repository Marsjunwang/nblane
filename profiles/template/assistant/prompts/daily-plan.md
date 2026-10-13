# 每日计划（晨报 08:30）

> 模板说明：把 `<profile>` 替换为你的 profile 名，把 `https://spa.<域名>`
> 替换为你的 SPA 地址。
> `<workspace>` 换成 OpenClaw 工作区的绝对路径（`readlink -f ~/.openclaw/workspace`），
> 让每条命令都是 `nblane_api` 的完整路径；它不在 PATH 里，只写命令名时模型可能找不到。
> `nblane_api` 是 install.sh 生成的包装命令。不传 `--profile` 时用环境变量
> `NBLANE_API_PROFILE` 指定的档案，prompt 里显式传 `--profile` 更稳。

调用 nblane（命令、成功/失败判定、哪些能直接做、哪些要先确认、撤销）一律按 nblane 技能（`skills/nblane/SKILL.md`）的规则执行，这里只写本任务要做什么。

命令一律写完整路径 `<workspace>/skills/bin/nblane_api`（下文已写好）。它不在 PATH 里，也不在 workspace 的 `bin/` 下，不要去那些地方找；直接照抄下面的命令执行。

本任务只读，不要修改任何档案内容。调用失败时在晨报相应位置标注「nblane 暂不可达」，其余部分照常。

## 任务步骤

1. 读取上下文：`<workspace>/skills/bin/nblane_api --profile <profile> goals`（目标与北极星）与 `<workspace>/skills/bin/nblane_api --profile <profile> summary`（档案摘要）。
   除上面这个 nblane_api 命令外，不要读取任何绝对路径下的文件。
2. 依次调用（均为只读）：
   - `<workspace>/skills/bin/nblane_api --profile <profile> starmap`：取星图计数（点亮 / 在学 /
     客星数）。
   - `<workspace>/skills/bin/nblane_api --profile <profile> chronicle --limit 40`：取近期编年
     （本月新立目标数、新镌星数，与首页简报行同源）。
   - `<workspace>/skills/bin/nblane_api --profile <profile> board`：取今日排期卡片与习惯待打卡
     清单。
3. 综合看板、目标与上述数据，生成不超过 3 条的今日重点，按优先级排序；
   末尾附一行星图计数与待打卡习惯清单。
4. 把晨报作为最终回复投递即可；不要修改任何 profile 文件。
