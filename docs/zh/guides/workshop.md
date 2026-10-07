---
status: active
owner: docs
last_verified: 2026-10-07
source_of_truth: true
---

# 车间（网页终端）使用说明

车间是服务器上的网页终端：一个入口，落在仓库目录的 tmux 会话里，可以运行 codex、claude、kimi、openclaw
等任意已装工具。锁屏、断线、关页面后重进，会话内容都还在。只有管理员能用。

## 入口

- 顶栏「车间」，打开 `/workshop`。它总在同一个独立标签页里打开，切回其他页面不会断开终端。
- 终端本身是 ttyd（xterm.js）把 tmux 会话变成网页，经 `/terminal/` 访问。`/terminal/` 由 SPA 后端（8504）反代，
  HTTP 和 WebSocket 都要求管理员登录，WebSocket 另校验同源。ttyd 只监听 `127.0.0.1`。
- ttyd 没运行时，页面显示「车间终端未运行」和启动指引，不渲染空白终端。

## 手机快捷输入

触屏设备默认显示，桌面可以手动打开。

- **快捷键栏**：Esc、Esc×2、Ctrl-C、Shift-Tab、Tab、方向键、回车、Ctrl-O / R / T / L / D / Z、上下翻页。
  按钮不抢焦点，不会收起软键盘。
- **输入框**：用手机输入法打字后点发送，文字按粘贴送进终端，可选是否带回车。用来绕开 xterm.js 在手机上
  中文输入法不好用的问题。
- 手机上下滑动即可翻历史。

## 设置：车间终端（管理员）

「设置 → 系统 → 车间终端」（`/settings/workshop`）。

- **车间终端服务**：一键安装（下载 ttyd 并校验哈希、写 tmux 配置和用户级 systemd 服务、启动）、启动、停止、
  重启 ttyd、查看日志、移除服务。检测到手写的旧服务时显示「接管」。需要 root 或网络受限的步骤
  （装 tmux、开 linger、改 Caddy、离线放 ttyd）给出逐步命令。
- **独立 tmux**：车间用自己的 tmux socket 和配置，不读写 `~/.tmux.conf`。重启 ttyd 或改设置时，
  tmux 里正在跑的 Agent 不中断。停止服务时会询问是否同时结束 tmux 会话。
- **终端显示与输入**：渲染方式（Canvas 最稳，WebGL 滚动最快但部分安卓 GPU 会糊字，DOM 兼容性最好）、
  超宽字形缩放（修复中文叠字）、浏览器原生滚动（关掉 tmux 备用屏幕，手机才能滑动翻历史）、tmux 鼠标模式、
  Esc 等待毫秒、网页滚动行数、tmux 历史行数、状态栏、新会话工作目录、手机字号和电脑字号。
  默认值来自手机实测；字号在重新打开车间时生效，滚动方式要刷新车间页面。
- **Happy Coder**：检测 `happy` CLI、手机配对和后台服务状态，并给接入指引。Happy 把 Agent 会话渲染成手机上的聊天界面，
  推送权限请求和错误；车间负责终端，Happy 负责看进度和审批。同一个 Claude 会话不要同时开两个进程。

## 部署注意

公网入口必须走 nblane 登录。如果 Caddy 还把 `/terminal/` 直接转给 ttyd（旧的 basic_auth 方式），
设置页会提示：删掉 Caddyfile 里的 `handle /terminal/*` 块，让 `/terminal/` 落到 8504 即可（需要 root）。
其余部署见 [腾讯云部署](deployment-tencent-cloud.md)，方案与实施记录见
[Phase 0.5 远程车间](../dev/phase0.5-remote-terminal.md)。

开发隔离：`scripts/dev-web.sh --isolated` 使用独立的车间服务和端口 `17668`，不碰生产会话。
