---
status: active
owner: 王军 + kimi
last_verified: 2026-09-22
source_of_truth: 远程车间(网页终端)接入方案;Step 0/1 已实施并验收(见文末实施记录)
---

# Phase 0.5 · 远程车间(网页终端)接入方案

## 目标

远程(尤其手机)进入 nblane 的实际运行环境:一个网页入口,落在 `/home/ubuntu/nblane`,可调用 codex / kimi / openclaw 等任意已安装工具。**工具无关**——它是车间大门,不是某台机器的界面。定位:元基建(脚手架),加速所有 Phase 的迭代,不属于功能 Phase。

## 侦察事实(2026-09-22)

- 生产:`https://www.nblane.cloud`,Caddy 自动 TLS;**Caddy 层零认证**,认证全在应用层(`NBLANE_AUTH_FILE` 生产已启用,cookie session,Streamlit/Reader/SPA 共享登录态)。
- **SPA(8504)未上生产**,Caddyfile 无其入口。
- tmux 3.4 已装;ttyd / code-server 未装。
- openclaw Control UI(127.0.0.1:18789)**自带终端且已开启**,token 认证,但 `X-Frame-Options: DENY` 不可 iframe,且绑死 openclaw(违反工具可切换原则)——只作过渡备胎。
- 已修隐患:Vite 5199 曾绑 0.0.0.0,已改 127.0.0.1。
- 遗留已知问题(不在本期范围,登记):reader/handoff token 走 URL query;8501/8502 登录面无应用层限流。

## 方案:ttyd + tmux sidecar,两道门

**核心选择:ttyd(不自建、不用 code-server、不依赖 openclaw)。**
ttyd 一个二进制把 bash 暴露为网页终端(xterm.js 内核);配 tmux 得持久会话,手机锁屏重进还在。code-server 偏重(手机 IDE 需求未证实),自建 xterm.js 留作后期打磨。

### 架构

```
手机/浏览器 ──HTTPS──> Caddy ──basic_auth(门一)──> ttyd(127.0.0.1:7668)
                                                     └─ tmux 会话 workshop,cwd=/home/ubuntu/nblane
后期:SPA(8504)上生产后,迁为 8504 WebSocket 代理 ── nblane cookie 认证(门二,撤门一)
```

- **ttyd 服务**:`ttyd -i 127.0.0.1 -p 7668 -t fontSize=16 tmux new-session -A -s workshop`;systemd unit `nblane-workshop.service`,User=ubuntu,Restart=always。
- **Caddy**:`www.nblane.cloud/terminal/*` → 反代 7668,挂 **basic_auth**(独立于 nblane 用户体系的第一道门,密码存 Caddy 哈希)。
- **tmux 会话**:`workshop` 常驻,默认 cwd 仓库根;启动脚本备好 `kimi` / `codex` / `openclaw` 快捷进入。

### 分步实施

| 步 | 内容 | 预估 | 状态 |
|---|---|---|---|
| 0 | 装 ttyd、systemd unit、tmux 会话、本机 127.0.0.1 跑通 | 半小时 | ✅ 2026-09-22 |
| 1 | Caddy 公网入口 + basic_auth,手机实测(锁屏重进、输入体验) | 半小时 | ✅ 入口已通(手机实测待王军) |
| 2 | SPA 加「车间」页 iframe 嵌入(路由 /p/:name/workshop 或全局页,侧栏注册) | 半天 | 未开始 |
| 3 | SPA 上生产后,迁 8504 WS 代理 + nblane 会话认证,撤 basic_auth | 随 SPA 上生产 | 未开始 |

### 安全关卡(逐条验收)

1. ttyd 只绑 127.0.0.1,永远不直接暴露。
2. 公网入口必须有认证:第一期 Caddy basic_auth;SPA 上生产后换 nblane 会话(require_user 全覆盖)。两道工序都是"不开认证不开门"。
3. 会话日志:journald 可查 ttyd 访问;Caddy 访问日志保留。
4. 手机的公网体验 = HTTPS + 认证,无例外。
5. 不把 openclaw 18789 暴露到公网(它是备胎,不是正门)。

## 验收标准

- 手机浏览器公网打开 → 过认证 → 进入 tmux 会话,cwd=/home/ubuntu/nblane,`kimi` 可用;
- 锁屏/断网后重进,会话内容还在;
- 未认证访问被 401 拦截;
- `pytest -q` 与既有服务不受影响。

## 实施记录(2026-09-22,Step 0/1 完成)

- **入口 URL**: `https://www.nblane.cloud/terminal/`(裸 `/terminal` 308 跳转到带斜杠形式)。basicauth 用户名 `workshop`,密码为强随机串(已线下交付王军,明文不入库;bcrypt 哈希在 `/etc/caddy/Caddyfile`)。
- **ttyd**: 1.7.7 静态二进制,装于 `~/.local/bin/ttyd`(GitHub releases,走 mihomo 代理下载);启动脚本 `~/.local/bin/nblane-workshop-ttyd.sh`(`-W` 可写、绑 127.0.0.1:7668、fontSize=24(王军实测手机端选定;URL 参数 ?fontSize=N 可临时覆盖)、命令 `tmux new-session -A -s workshop`)。
- **持久化**: 用户级 systemd unit `nblane-workshop.service`(`~/.config/systemd/user/`,`systemctl --user` 管理,已 enable)。tmux 会话 `workshop` 常驻,cwd=/home/ubuntu/nblane。
- **Caddy**: 备份 `/etc/caddy/Caddyfile.bak.20260922-174644`;`www.nblane.cloud` 站点内新增 `handle /terminal/* { basicauth; uri strip_prefix /terminal; reverse_proxy 127.0.0.1:7668 }`,`caddy validate` 通过后 `systemctl reload caddy`。
- **验收**: 本机 `curl 127.0.0.1:7668/` 200;公网无认证 401、带认证 200;WebSocket 经前缀握手 101(`curl` 需 `--http1.1`,HTTP/2 的 Upgrade 头会被剥离,浏览器 WebSocket 不受影响);tmux 会话 send-keys 执行命令成功;8501/8502/18503/18504/5199/18789 全部健康。
- **坑记录**: ① systemd ExecStart 会把 `key=value` 拆成两个参数,故 `-t` 选项放进 wrapper 脚本;② `handle` 块内 `redir` 不能写数字状态码(会被当成跳转目标),裸路径跳转用站点级 `redir /terminal /terminal/ 308`;③ ttyd 1.7.7 HTML 无 viewport meta,手机端体验待真机确认(xterm.js fit addon 会自适应宽高)。
- **待办**: 手机真机实测(锁屏重进、软键盘输入);SPA「车间」页(Step 2)。
