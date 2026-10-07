# 每周占卜（周日 20:30，周报之后）

> 模板说明：把 `<profile>` 替换为你的 profile 名，把 `https://spa.<域名>`
> 替换为你的 SPA 地址。

调用 nblane（命令、成功/失败判定、哪些能直接做、哪些要先确认、撤销）一律按 nblane 技能（`skills/nblane/SKILL.md`）的规则执行，这里只写本任务要做什么。

调用失败时回复「nblane 暂不可达，本周卦辞缺席」即可，不要自己编造卦辞。LLM 润色不可用时服务端会自动降级为规则卦（source="rule"），照原样推送。

## 任务步骤

1. 戏占（默认）：调用
   `nblane_api --profile <profile> divine --mode play`
   取本周卦辞，把卦名、卦辞与简释原样整理成一条微信消息投递，末尾附一行
   首页深链 `https://spa.<域名>/p/<profile>/home`。
2. 正占（仅当主人点名且给出所问之事）：调用
   `nblane_api --profile <profile> divine --mode serious --question "<所问之事>"`。
   主人只说「正占」却没说问什么时，先追问所问之事，拿到后再占；正占结果
   会锚定真实 gap 缺口，推送时保留卦辞卡上「化为任务」的提示，引导主人到
   SPA 一键入看板。
3. 同一模式同一天不要重复起卦（结果相同且徒耗调用）；一次运行只推送一卦。
4. 如需结合档案近况解读卦辞，可经 nblane MCP 读本读取
   `profile://summary`；读本与占卜均为免确认级，不要读取任何绝对路径下的
   文件。
