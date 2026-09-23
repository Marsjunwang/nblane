---
status: active
owner: 王军 + kimi
last_verified: 2026-09-22
source_of_truth: 远程车间(网页终端)接入方案;Step 0/1/2 已实施并验收(见文末实施记录)
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
| 2 | SPA 加「车间」页 iframe 嵌入(路由 /p/:name/workshop 或全局页,侧栏注册) | 半天 | ✅ 2026-09-22(全局页 /workshop,见文末) |
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
- **tmux 配置**: `~/.tmux.conf` 新增 `mouse on` + `history-limit 50000`(2026-09-22,修复网页端无法滚动翻历史:tmux 备用屏幕会清空 xterm.js 回滚缓冲,`mouse on` 后滚轮进入 tmux copy-mode 翻页;此前超过 2000 行的历史已不可追)。鼠标拖选文本会进 tmux 选区,按住 Shift 拖选走浏览器原生选择/复制。
  同日在 `~/.tmux.conf` 追加 `terminal-overrides 'xterm*:smcup@:rmcup@'`(禁用 tmux 对外备用屏幕,内容画进 xterm.js 普通缓冲区):修复手机触屏无法翻历史——xterm.js 不把触摸拖动转成鼠标上报,mouse on 对触屏无效;副作用是全屏 TUI 重绘帧会留在滚动历史、程序退出后画面不再清走。刷新网页(新 tmux client 接入)即生效,无需重启 tmux server。
  二轮修复(同日,实测手机仍滑不动后定位):xterm.js 无原生触摸处理(xtermjs/xterm.js#5377),手机浏览器把触摸拖动合成为鼠标拖动,`mouse on` 的 tmux 将其当作拖选文本而非滚动——故改回 `mouse off`,滚动完全交给 xterm.js 原生 viewport(桌面滚轮+手机触摸统一);ttyd wrapper 加 `-t scrollback=10000`(xterm 滚动缓冲 1000→10000 行)并 `systemctl --user restart nblane-workshop.service`。验证方法:只读 attach 同尺寸 pty 抓初始化字节,确认无 `1049h`(备用屏幕已禁)、`1000h` 已随 mouse off 消失。
  三轮修复(同日):首轮 `set-option -t workshop mouse on` 是**会话级**配置,覆盖了二轮的全局 `mouse off`(抓字节发现 `1000h` 仍在),`tmux set-option -u -t workshop mouse` 撤掉会话级覆盖后,新客户端初始化字节确认 `1049h=0、1000h=0`。教训:改 tmux 配置后用抓字节验证,不要只看 show。**2026-09-22 王军手机实测:上下滑动翻历史正常,移动端滚动闭环完成。**
- **Caddy**: 备份 `/etc/caddy/Caddyfile.bak.20260922-174644`;`www.nblane.cloud` 站点内新增 `handle /terminal/* { basicauth; uri strip_prefix /terminal; reverse_proxy 127.0.0.1:7668 }`,`caddy validate` 通过后 `systemctl reload caddy`。
- **验收**: 本机 `curl 127.0.0.1:7668/` 200;公网无认证 401、带认证 200;WebSocket 经前缀握手 101(`curl` 需 `--http1.1`,HTTP/2 的 Upgrade 头会被剥离,浏览器 WebSocket 不受影响);tmux 会话 send-keys 执行命令成功;8501/8502/18503/18504/5199/18789 全部健康。
- **坑记录**: ① systemd ExecStart 会把 `key=value` 拆成两个参数,故 `-t` 选项放进 wrapper 脚本;② `handle` 块内 `redir` 不能写数字状态码(会被当成跳转目标),裸路径跳转用站点级 `redir /terminal /terminal/ 308`;③ ttyd 1.7.7 HTML 无 viewport meta,手机端体验待真机确认(xterm.js fit addon 会自适应宽高)。
- **待办**: 手机真机实测(锁屏重进、软键盘输入);SPA「车间」页(Step 2)。

## 实施记录(2026-09-22,Step 2 完成)

- **页面**: SPA 新增全局页 `/workshop`(`web_ui/frontend/src/pages/WorkshopPage.tsx`),顶栏「车间」按钮与「助手」并列(AppLayout.tsx)。选型说明:车间终端是机器级资源(tmux 会话 cwd=仓库根,不属任何 profile),故走 `/assistant` 同款全局页模式,而非 `/p/:name/workshop` 侧栏项;SPA 导航本无 admin 门控,无需额外权限分支。页面列入 `FULL_BLEED_SEGMENTS`(终端要满宽)。
- **配置端点**: `GET /api/v1/system/workshop`(`web_api/workshop.py`,require_user,60s 缓存)返回 `{url, reachable, checked_at}`:
  - `url`(iframe 地址)取 `NBLANE_WORKSHOP_URL`,默认 `/terminal/`(同源相对路径,生产 Caddy 反代);本地 dev 无此反代,在 `.env` 设 `NBLANE_WORKSHOP_URL=http://127.0.0.1:7668/`(dev-web.sh 会 source .env)。
  - `reachable` 为服务端探活 ttyd(`NBLANE_WORKSHOP_PROBE_URL`,默认 `http://127.0.0.1:7668`;ttyd 只绑 loopback,服务端探测不受 Caddy/basic_auth 影响);探活走 `app.state.workshop_http_get` 注入缝,测试不触网。
- **降级体验**: 探活失败时页面不渲染死 iframe,改显启动指引卡(`systemctl --user start nblane-workshop.service` / wrapper 脚本)+ 重新检测按钮;可达时复用 `SidecarFrame`(加载遮罩 + 重新加载),另附「新标签页打开」。
- **契约**: openapi.json 快照与 `schema.d.ts` 已重生成(dump-openapi.sh + `npm run gen:api`);`types.ts` 加 `WorkshopStatus` 别名,hooks.ts 加 `useWorkshopStatus`。
- **测试**: `tests/test_web_api_workshop.py` 7 例(URL 默认/覆盖、探活成败、probe URL 覆盖、缓存、401 门控);`WorkshopPage.test.tsx` 3 例。全量 `pytest -q` 1627 通过;前端 `vitest run` 147 通过;`npx tsc --noEmit` 与 `npx vite build --outDir /tmp/spa-build-check` 通过。
- **未做(刻意推迟)**: 未执行 `npm run build` 写入 `src/nblane/web_ui/static/`(当日该目录正服务于 18504 的另一特性验证)。后续重建命令:`cd src/nblane/web_ui/frontend && npm run build`(脚本内含 `tsc --noEmit`,输出至 `../static`,随包分发)。
- **打包清单**: Step 2 无新增系统级依赖/端口/服务,docs/zh/guides/packaging-manifest.md 无需改动;仅新增环境变量 `NBLANE_WORKSHOP_URL` / `NBLANE_WORKSHOP_PROBE_URL`,已登入 `.env.example`。
