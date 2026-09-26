---
status: active
owner: engineering
last_verified: 2026-09-26
source_of_truth: true
---

# 整机迁移 Runbook

本文面向「把整个 nblane 系统（代码 + 数据 + OpenClaw 集成）从旧服务器迁到
新服务器」的场景，按执行顺序列出每一步及其验证方法。各步骤的详细模板与
背景不在此重复，分别链接到既有文档：

- 部署模板与 systemd / Caddy 写法：[腾讯云小团队部署](deployment-tencent-cloud.md)
- OpenClaw 安装条件与 CW-1..CW-5 变更窗口清单：[OpenClaw 接入指南](openclaw-integration.md)
- 代理（mihomo）：[Mihomo 代理部署](mihomo-deployment.md)

密钥、域名、Owner ID 一律用占位符；示例域名沿用公网文档已有的
`www.nblane.cloud` / `spa.nblane.cloud`。真实值只放在新机的私有文件中，
不要提交到任何仓库。

## 1. 迁移总览

整机由「三棵树 + OpenClaw 侧 + 系统层」组成，迁移对象与方式各不相同：

```text
┌─ 代码仓（GitHub，git clone）        /srv/nblane-app/nblane
│    └ 前端产物随仓库提交，生产不跑 npm build
├─ 数据仓（私有 Git，git clone）      /srv/nblane-data
│    └ profiles/ schemas/ teams/ auth/users.yaml .env(0600)
├─ 大资产（不进 Git，rsync）          /srv/nblane-assets
│    └ research/ 下的论文 PDF 原件等
├─ OpenClaw 侧（tar 整目录备份还原）  ~/.openclaw
│    └ openclaw.json(含 gateway token/模型 key)、workspace、插件、登录态
└─ 系统层（手工重建，不靠拷贝）
     ├ systemd 系统 unit ×3：nblane(8501) / nblane-reader(8502) / nblane-web-api(8504)
     ├ systemd 用户 unit：openclaw-gateway(gateway 18789)
     └ Caddy：www 主站 + spa 子域名 + /openclaw 反代
```

三条原则：

- **数据仓是事实源**：`NBLANE_ROOT` 指向 `/srv/nblane-data`；代码仓下的
  `profiles/` 等目录是 gitignore 的本地产物，不要从旧机代码仓里拷数据。
- **凭证不能靠 git**：LLM key、gateway token、reader token secret 等只存在
  于 `.env` / `~/.openclaw` / `~/.config/nblane/`，清单见第 9 节。
- **旧机先不下线**：DNS 切换后旧机保留 48h 观察期，下线顺序见第 11 节。

## 2. 新机准备

- **Python ≥ 3.11**、Git、rsync；按
  [腾讯云部署](deployment-tencent-cloud.md) 创建 `nblane` 运行用户。
- **Caddy**：按官方方式安装，安全组只放 80/443（22 仅管理员 IP），
  不放行 8501/8502/8504/18789。
- **OpenClaw**：安装条件（Node 版本、linger、端口 18789、模型凭据分层
  A–F）见 [OpenClaw 接入指南「安装所需条件」](openclaw-integration.md)，
  本节不重复；迁移时先只装到 **A 最小可运行**，其余层在第 8 节恢复。
- **systemd**：系统级 unit 模板直接从
  [腾讯云部署「systemd」节](deployment-tencent-cloud.md) 复制；OpenClaw 的
  gateway 是**用户级**服务（`systemd --user`），无头主机必须
  `sudo loginctl enable-linger "$(whoami)"`。
- 需要出站代理时先装好 mihomo（见
  [Mihomo 代理部署](mihomo-deployment.md)），否则代码仓 clone 与 pip 安装
  可能先卡住。

验证：

```bash
python3 -c 'import sys; assert sys.version_info >= (3, 11)'
command -v git rsync caddy
ss -ltn | awk '/8501|8502|8504|18789/'   # 装机前应全部为空
```

## 3. 代码仓

```bash
sudo -u nblane git clone https://github.com/<org>/nblane.git /srv/nblane-app/nblane
cd /srv/nblane-app/nblane
sudo -u nblane python3 -m venv .venv
sudo -u nblane .venv/bin/pip install -e .
```

两个坑：

- **代理 + 国内镜像**：shell 里全局挂着 `http_proxy`/`https_proxy` 时，
  pip 走国内镜像的请求也会被送进代理，表现为超时或 TLS 报错。把镜像域名
  加进 `no_proxy`（对照 [mihomo 文档](mihomo-deployment.md) 的写法）：

  ```bash
  export no_proxy="localhost,127.0.0.1,::1,*.local,<pip 镜像域名>"
  export NO_PROXY="$no_proxy"
  ```

- **生产不跑 npm build**：Dashboard / Reader / SPA 等前端产物（内容哈希
  bundle）随仓库提交，生产机直接 serve 静态文件，只改源码不重新构建时
  生产看不到任何变化——所以迁移也**不要**在新机跑 `npm run build`，
  以仓库里的产物为准（见部署文档「更新前端组件」节）。

验证：

```bash
cd /srv/nblane-app/nblane
.venv/bin/nblane --help >/dev/null && echo cli-ok
.venv/bin/python - <<'PY'
import socksio   # 走 SOCKS 代理时必需，缺失会在 LLM/Reader 请求时报错
print("socksio ok")
PY
```

## 4. 数据仓

把私有数据仓 clone 到 `/srv/nblane-data`（配好 deploy key）：

```bash
sudo -u nblane git clone <私有 nblane-data 仓地址> /srv/nblane-data
ls /srv/nblane-data   # 应有 profiles/ schemas/ teams/ auth/
```

验证（数据结构对 schemas 校验全过）：

```bash
cd /srv/nblane-app/nblane
sudo -u nblane NBLANE_ROOT=/srv/nblane-data .venv/bin/nblane validate
```

随后确认远端与写时备份链路（`NBLANE_DATA_GIT_AUTOCOMMIT=1` /
`NBLANE_DATA_GIT_AUTOPUSH=1` 在三个 unit 上配置后，Web 保存会自动
commit + push，见部署文档「私有 Git 备份」节）。

`/srv/nblane-data/.env` 属于凭证，不进 git，在第 9 节单独重建。

## 5. 大资产

Research PDF 等大文件不进任何 git 仓，用 rsync 从旧机直拷：

```bash
sudo rsync -aH --info=progress2 \
  <旧机用户>@<旧机地址>:/srv/nblane-assets/ /srv/nblane-assets/
sudo chown -R nblane:nblane /srv/nblane-assets
```

profile 里只保存 `papers/<sha>-name.pdf` 形式的相对 asset ref，不保存绝对
路径，所以资产树整体平移即可，无需改数据。

验证：

```bash
du -sh /srv/nblane-assets/research
ls /srv/nblane-assets/research/profiles/*/papers/ | head
# 抽一篇:在旧机与新机各算一次 sha256 对比
sha256sum /srv/nblane-assets/research/profiles/<profile>/papers/<某个.pdf>
```

## 6. systemd 系统 unit ×3

三个 unit 的完整模板在
[腾讯云部署「systemd」节](deployment-tencent-cloud.md)：`nblane`（8501，
Streamlit）、`nblane-reader`（8502，uvicorn 单 worker）、`nblane-web-api`
（8504，uvicorn 单 worker）。迁移时按模板落到
`/etc/systemd/system/`，注意模板里 `WorkingDirectory`/`ExecStart` 的代码
路径要与本机实际检出路径一致。

**三个 unit 都不能漏的关键项**：

- `Environment=NBLANE_ROOT=/srv/nblane-data`
- `Environment=NBLANE_AUTH_FILE=/srv/nblane-data/auth/users.yaml`
- `Environment=NBLANE_DATA_GIT_AUTOCOMMIT=1` + `NBLANE_DATA_GIT_AUTOPUSH=1`
  ——8504 漏配会导致 SPA 保存不产生备份提交（部署文档 8504 节有明确警告）。
- `EnvironmentFile=-/srv/nblane-data/.env`——三 unit 共享，凭证集中在这里。

**8504 的 drop-in 三件**（放 `/etc/systemd/system/nblane-web-api.service.d/`）：

- `10-proxy.conf`：出站代理，写法照
  [mihomo 文档「让生产 systemd 服务走代理」](mihomo-deployment.md)，
  含成对的 `no_proxy`/`NO_PROXY`。
- `20-path.conf`：SPA 助手页要在服务端探测/调用 openclaw，而 openclaw
  通常装在用户级 npm-global，systemd 默认 PATH 看不到（症状是助手页显示
  「本机未安装」）。systemd 的 `Environment=` 不做 shell 展开，必须写绝对
  路径：

  ```ini
  [Service]
  Environment=PATH=/home/<实际运行用户>/.local/npm-global/bin:/usr/local/bin:/usr/bin:/bin
  ```

- `30-trust-proxy.conf`：`NBLANE_TRUST_PROXY_HEADERS=1` 让 8504 取
  `X-Forwarded-For` 首跳作为登录限流的客户端 IP。**仅当 Caddy 反代就位
  且 8504 不直接对公网可达（安全组只放 80/443）后才开启**；直连可达时
  开启等于允许客户端伪造限流身份。条件不满足前先不配这条。

启动并验证：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now nblane nblane-reader nblane-web-api
systemctl is-active nblane nblane-reader nblane-web-api   # 三个 active
curl -fsS http://127.0.0.1:8504/api/v1/health
```

## 7. Caddy

完整站点块模板与「必须用 `handle` 不用 `handle_path`」的说明在
[腾讯云部署「HTTPS 反向代理」节](deployment-tencent-cloud.md)，这里只列
迁移要点：

- **www 主站**：全部 8502 handle 集（`/reader/*`、`/paper-library*`、
  `/dashboard*`、`/api/dashboard/*`、`/api/research/*`、`/auth/*`、
  `/blog-editor*`、`/api/blog/*`、`/api/site/*`）+ `/terminal` 的
  basicauth 入口 + `/openclaw` 反代（见下）+ catch-all `reverse_proxy
  127.0.0.1:8501`。
- **spa 子域名**：复制主站的全部 8502 handle 集（漏 `/auth/*` 会让
  iframe handoff 404/401、Paper Library 整片空白），catch-all 指向
  `127.0.0.1:8504`。
- **`/openclaw` 反代**：必须**同时**写精确匹配和通配两条：

  ```caddyfile
      handle /openclaw {
          reverse_proxy 127.0.0.1:18789
      }

      handle /openclaw/* {
          reverse_proxy 127.0.0.1:18789
      }
  ```

  只写 `/openclaw/*` 时，无尾斜杠的 `/openclaw` 请求会落到主站 catch-all
  的 8501，WebSocket 握手失败（实测，见
  [openclaw 接入指南 CW-4](openclaw-integration.md)）。Gateway 侧还需
  basePath / publicOrigin / trustedProxies / allowedOrigins 四件套，
  缺一不可，配置命令同样在 CW-4。

- **DNS**：为 www 与 spa 两个域名各建 A 记录指向新机 IP。Caddy 证书自动
  签发；DNS 未生效期间申请会指数退避，DNS 就位后
  `sudo systemctl restart caddy` 可立即触发重试。

验证：

```bash
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
curl -sI https://www.nblane.cloud/            # 200(登录页)
curl -sI https://spa.nblane.cloud/            # 200(SPA index)
curl -sI https://www.nblane.cloud/openclaw/   # 200 text/html
```

## 8. OpenClaw 侧迁移

Gateway token、模型 key、微信登录态都在 `~/.openclaw` 内，整目录 tar 备份
还原即可带走；**不要**把该目录或其打包件提交到任何仓库。

1. **整目录备份还原**（以运行 Gateway 的同一用户执行）：

   ```bash
   # 旧机
   tar czf /tmp/openclaw-backup.tar.gz -C ~ .openclaw
   # 传到新机后（scp/私有加密渠道），在新机
   tar xzf /tmp/openclaw-backup.tar.gz -C ~
   ```

2. **Gateway 用户级服务**：按接入指南用官方路径安装守护进程
   （`openclaw onboard --install-daemon`）并 `enable-linger`。随后加
   drop-in `~/.config/systemd/user/openclaw-gateway.service.d/nblane-api.conf`，
   把 openclaw 服务账号密码注入 Gateway 进程环境（供自动化调 8504 用）：

   ```ini
   [Service]
   Environment=NBLANE_OPENCLAW_API_PASSWORD=<openclaw 服务账号密码>
   ```

   写完 `systemctl --user daemon-reload && systemctl --user restart
   openclaw-gateway`。

3. **skills 与插件**：在代码仓根目录运行
   `scripts/openclaw/install.sh`（先 `--dry-run` 确认）。脚本幂等：rsync
   同步 skills 到 `~/.openclaw/workspace/skills/`，在其中建专用
   `.venv`（httpx）并生成包装命令 `bin/nblane_api`，再
   `openclaw plugins install ... weixin-task-bridge --force
   --accept-capabilities`。细节见 [scripts/openclaw/README.md](../../../scripts/openclaw/README.md)。

4. **密码兜底文件**：自动化沙箱不继承 Gateway 进程环境时，环境变量注入
   会失效；`~/.config/nblane/api.env`（0600）是 `nblane_api` 的兜底密码
   来源（读取顺序见接入指南 F 节）：

   ```bash
   install -d -m 700 ~/.config/nblane
   printf 'NBLANE_OPENCLAW_API_PASSWORD=<openclaw 服务账号密码>\n' \
     > ~/.config/nblane/api.env
   chmod 600 ~/.config/nblane/api.env
   ```

5. **MCP 注册**：按接入指南 **CW-1** 执行（`nblane sync-agent-harness
   --target openclaw --profile <name>` 生成片段，`openclaw config patch`
   先 `--dry-run` 再正式应用；`NBLANE_ROOT` 必须指向 `/srv/nblane-data`）。
   验证 `openclaw mcp probe nblane` 能列出工具。

6. **备份调度**：按 **CW-2** 执行（`openclaw backup create` 手动验证一次
   后 `openclaw backup enable --every 24h`）。

7. **自动化纳管**：自动化的声明源在数据仓
   `profiles/<name>/assistant/automations.yaml`，随数据仓 clone 已就位。
   执行 **CW-3** 的 `nblane openclaw automations sync <name> --apply`
   **之前**，先确认新机 Gateway 的模型路由（模型 key 随 `~/.openclaw`
   迁来，但供应商可用性要重新确认）：

   ```bash
   openclaw config get agents.defaults.model --json
   openclaw models status --json
   ```

8. **控制台公网入口**：按 **CW-4** 执行四件套（`controlUi.basePath` /
   `gateway.publicOrigin` / `gateway.trustedProxies` /
   `controlUi.allowedOrigins`），缺一不可；publicOrigin 必须是裸 origin
   不带路径。Caddy 侧的两条 `/openclaw` 匹配见第 7 节。

验证：

```bash
systemctl --user is-active openclaw-gateway.service
curl -fsS http://127.0.0.1:18789/readyz
openclaw plugins inspect weixin-task-bridge --runtime --json   # loaded + activated
openclaw automations list --all --json
~/.openclaw/workspace/skills/bin/nblane_api health
```

## 9. 凭证重建清单

迁移中唯一不能靠 git 的部分。逐项核对：

| 凭证 | 存放位置 | 迁移方式 |
| --- | --- | --- |
| `LLM_API_KEY`（及 `LLM_BASE_URL`/`LLM_MODEL`） | `/srv/nblane-data/.env`（0600） | 参照 `.env.example` 在新机重写，不拷贝旧机文件 |
| Gateway token | `~/.openclaw/openclaw.json` 的 `gateway.auth.token` | 随 `~/.openclaw` 整目录迁移即带走 |
| 微信 bot 授权（ilink token） | `~/.openclaw` 内插件登录态 | 随目录迁移；失效则重新 `openclaw channels login --channel openclaw-weixin` 扫码 |
| `auth/users.yaml`（含 openclaw 服务账号哈希） | 数据仓 `auth/users.yaml` | 随数据仓 clone 到位 |
| `NBLANE_READER_TOKEN_SECRET` | `/srv/nblane-data/.env` | 沿用旧值或重新生成（命令见部署文档 systemd 节），8501/8502 必须一致 |
| `NBLANE_OPENCLAW_API_PASSWORD`（openclaw 服务账号明文密码） | Gateway drop-in + `~/.config/nblane/api.env` | 明文不在任何 git 仓，迁移时重新录入（第 8 节第 2/4 步） |

`.env` 权限收紧：

```bash
sudo chown nblane:nblane /srv/nblane-data/.env
sudo chmod 600 /srv/nblane-data/.env
```

HTTPS 生产环境别忘了 `NBLANE_AUTH_COOKIE_SECURE=1`（部署文档 Caddy 节）。

## 10. 验收清单

全部通过才算迁移完成：

- [ ] `cd /srv/nblane-app/nblane && .venv/bin/nblane openclaw doctor
      --profile <name>` 各项 `[OK]`；`nblane validate` 全绿。
- [ ] `systemctl is-active nblane nblane-reader nblane-web-api` 三个 active。
- [ ] 三个 HTTPS 入口 200：`https://www.nblane.cloud/`、
      `https://spa.nblane.cloud/`、`https://www.nblane.cloud/openclaw/`。
- [ ] 浏览器登录后首页星图正常渲染；SPA 内 Paper Library iframe 不空白。
- [ ] 做一次真实打卡（mutation），随后 `git -C /srv/nblane-data log
      --oneline -1` 出现新 commit 且已 push 到私有远端。
- [ ] 手动触发一次晨报（每日计划）自动化，确认真实投递（消耗 Token）：

  ```bash
  openclaw automations run <每日计划实际ID> --wait --expect-final --wait-timeout 8m --json
  ```

- [ ] 控制台 `https://www.nblane.cloud/openclaw/` 粘贴 token 完成 WS
      握手登录，桌面验证通过后再上手机。

## 11. 旧机下线顺序

1. **DNS 切换**：把 www / spa 的 A 记录指向新机；新机 Caddy 完成证书签发
   （第 7 节）。
2. **观察 48h**：期间旧机服务保持运行但不写入；确认新机第 10 节验收全部
   通过、数据仓 push 链路正常、晨报/复盘按时投递。
3. **旧机停服务**：

   ```bash
   # 旧机
   sudo systemctl disable --now nblane nblane-reader nblane-web-api
   systemctl --user disable --now openclaw-gateway
   ```

   停 Gateway 即断开微信通道，属预期动作；确认新机 Gateway 已接管后再执行。
4. **旧机数据仓保留为只读历史**：不再 push、不再挂载到任何服务，git log
   作为历史留档；确认新机数据仓历史完整后再考虑清理旧机磁盘。

## 相关文档

- [腾讯云小团队部署](deployment-tencent-cloud.md) — systemd / Caddy / 私有 Git 备份模板
- [OpenClaw 接入指南](openclaw-integration.md) — 安装条件分层与 CW-1..CW-5 变更窗口
- [Mihomo 代理部署](mihomo-deployment.md) — 出站代理与 systemd 代理 drop-in
- [安装与 LLM 配置](setup.md) — 基础安装流程
