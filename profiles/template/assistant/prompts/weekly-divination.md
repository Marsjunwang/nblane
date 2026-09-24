# 每周占卜（周日 20:30，周报之后）

> 模板说明：把 `<profile>` 替换为你的 profile 名，把 `https://spa.<域名>`
> 替换为你的 SPA 地址。

## nblane API 调用约定

- 命令形态：`~/.openclaw/workspace/skills/bin/nblane_api --profile <profile> <子命令>`。
  客户端自动登录并复用 cookie；服务账号密码从环境变量
  `NBLANE_OPENCLAW_API_PASSWORD` 读取。若报密码未设置，回复主人
  「nblane 服务账号密码未配置」，不要索要或转述密码本身。
- 占卜（divine）属免确认级：不落盘、单次消费，卦象对（档案，日，模式）
  确定，推送内容与主人在首页所见一致。
- 降级：调用失败（非零退出或输出含 error 字段）时，回复「nblane 暂不可达，
  本周卦辞缺席」即可；不要重试超过一次，不要自己编造卦辞。LLM 润色不可
  用时服务端会自动降级为规则卦（source="rule"），照原样推送，无需特别
  处理。

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
