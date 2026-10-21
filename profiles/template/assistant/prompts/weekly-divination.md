# 每周占卜（周日 20:30，周报之后）

> 模板说明：把 `<profile>` 替换为你的 profile 名，把 `https://spa.<域名>`
> 替换为你的 SPA 地址。
> `<workspace>` 换成 OpenClaw 工作区的绝对路径（`readlink -f ~/.openclaw/workspace`），
> 让每条命令都是 `nblane_api` 的完整路径；它不在 PATH 里，只写命令名时模型可能找不到。

调用 nblane（命令、成功/失败判定、哪些能直接做、哪些要先确认、撤销）一律按 nblane 技能（`skills/nblane/SKILL.md`）的规则执行，这里只写本任务要做什么。

命令一律写完整路径 `<workspace>/skills/bin/nblane_api`（下文已写好）。它不在 PATH 里，也不在 workspace 的 `bin/` 下，不要去那些地方找；直接照抄下面的命令执行。

调用失败时回复「nblane 暂不可达，本周卦辞缺席」即可，不要自己编造卦辞。LLM 润色不可用时服务端会自动降级为规则卦（source="rule"），照原样推送。

## 执行要点（必读）

- `divine` 起卦要在服务端做 LLM 润色，单条命令约需 1–2.5 分钟才返回。
  调用 exec 工具时务必设置 `timeout: 200`、`yieldMs: 170000`，让命令在
  前台等到结束；若命令仍被自动转入后台，用 process 工具轮询直到它退出。
  退出码为 0 且输出是 JSON 才算成功。
- nblane 的调用一律使用本文件给出的 nblane_api 命令；禁止自己拼接 URL、
  禁止用 curl / wget 直接请求 nblane 接口（那样只会 401/404，毫无帮助）。
- 只有命令本身失败（退出码非 0、执行超时、输出不是合法 JSON）时才回复
  「nblane 暂不可达，本周卦辞缺席」；命令成功就必须投递卦辞。
- 整个任务自身有 300 秒上限：起卦成功后立即整理投递，不要再做别的尝试。

## 任务步骤

1. 戏占（默认）：调用
   `<workspace>/skills/bin/nblane_api --profile <profile> divine --mode play`
   取本周卦辞，把卦名、卦辞与简释原样整理成一条微信消息投递，末尾附一行
   首页深链 `https://spa.<域名>/p/<profile>/home`。
2. 正占（仅当主人点名且给出所问之事）：调用
   `<workspace>/skills/bin/nblane_api --profile <profile> divine --mode serious --question "<所问之事>"`。
   主人只说「正占」却没说问什么时，先追问所问之事，拿到后再占；正占结果
   会锚定真实 gap 缺口，推送时保留卦辞卡上「化为任务」的提示，引导主人到
   SPA 一键入看板。
3. 同一模式同一天不要重复起卦（结果相同且徒耗调用）；一次运行只推送一卦。
4. 如需结合档案近况解读卦辞，可调用 `<workspace>/skills/bin/nblane_api --profile <profile> summary`；不要读取任何
   绝对路径下的文件。
