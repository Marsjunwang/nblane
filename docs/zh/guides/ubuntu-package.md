---
status: active
owner: engineering
last_verified: 2026-10-25
source_of_truth: true
---

# Ubuntu 离线安装包

适合把某个已测试版本安装到一台 Ubuntu 服务器，之后重复生成、安装、升级和回滚。产物是 `tar.gz + SHA256`，不是 `.deb`，也不要求目标机器安装 Node.js。

只装应用与两个 Web 服务；GROBID、Chromium、Codex、OpenClaw、车间终端、本地翻译模型及远程数据仓库仍按各自文档单独配置。wheelhouse 包含默认 Python 依赖，不含可选模型或系统安装包。手机 App 不在此安装包范围内。

## 一条命令生成安装包

在 nblane 源码仓库根目录运行：

```bash
scripts/package-ubuntu.sh
```

生成到 `dist/ubuntu/`：

```text
nblane-<版本>-ubuntu.tar.gz         安装包
nblane-<版本>-ubuntu.tar.gz.sha256  完整性校验
BUILDINFO                          版本、源码 commit、构建时间
```

包内有源码快照、两个已构建前端、安装器、锁定依赖清单和 Python wheelhouse。默认使用 `uv export --frozen` 按 `uv.lock` 导出依赖，再用 pip 下载。前端不需要在目标机器重新构建。

- 建包需要 Git、Python ≥ 3.11、uv、pip，以及下载依赖的网络。
- 默认要求 Git 工作树干净，从 `HEAD` 建包，避免把未提交修改误当发布版本。
- `NBLANE_PACKAGE_ALLOW_DIRTY=1` 可打包含当前修改的开发包，不作为正式发布。
- `NBLANE_PACKAGE_OUT=/path` 可改输出目录。
- `NBLANE_PACKAGE_OFFLINE=0` 只用于打包器测试；这种包没有 wheelhouse，安装时必须显式设置 `NBLANE_ALLOW_ONLINE_INSTALL=1` 才允许 pip 联网，不是离线交付包。
- wheel 按建包机器的 Python 版本和 CPU 架构选择。目标机器应与之匹配；不同环境要分别建包。

包内排除 `.env`、真实 `profiles/`、真实账号文件、Reader 密钥、开发数据、论文资产、缓存和测试输出，只保留 `profiles/template/` 与配置示例。仍应在发布前检查源码仓库中是否有误提交的秘密。

## 目标机器准备

需要 Python ≥ 3.11（含 venv）、Git、tmux、curl、tar 和 coreutils。例如 Ubuntu 24.04 可先运行：

```bash
sudo apt update
sudo apt install -y python3 python3-venv git tmux curl
```

Ubuntu 22.04 自带的 Python 3.10 不满足要求，须先提供 Python ≥ 3.11；安装器不会擅自添加第三方软件源。缺少 Git / tmux / curl 时，可用 `NBLANE_INSTALL_APT=1` 允许安装器通过 apt 补齐。

把安装包和 `.sha256` 放在同一目录，校验后解压到独立目录：

```bash
sha256sum -c nblane-<版本>-ubuntu.tar.gz.sha256
mkdir -p nblane-installer
tar -xzf nblane-<版本>-ubuntu.tar.gz -C nblane-installer
cd nblane-installer
```

## 一键安装

交互终端直接运行：

```bash
sudo ./install.sh
```

默认创建 `default` 档案，不配置 AI Key，开启登录并自动生成管理员 `admin` 的初始密码。**密码只在终端显示一次**；已有账号时不会重建或显示密码。先记录密码，再打开 `http://127.0.0.1:8504`。

无人值守安装通过环境变量传入初始密码，不把密码写进命令行参数或 `.env`：

```bash
sudo NBLANE_ADMIN_PASSWORD='<至少10位的初始密码>' \
  NBLANE_PROFILE=default ./install.sh
```

默认目录：

| 用途 | 默认位置 |
|------|----------|
| 代码与虚拟环境 | `/srv/nblane-app/nblane` |
| 档案、`.env`、账号 | `/srv/nblane-data` |
| 论文等外部资产 | `/srv/nblane-assets/research` |
| 旧代码备份 | `/srv/nblane-app/nblane-backups` |

服务账号默认取 `SUDO_USER`。以 root 直接操作或为独立账号安装时，显式设置 `NBLANE_SERVICE_USER=<已有账号>`。代码、数据、资产和备份应使用独立的专用目录，安装器会拒绝把数据或资产放进代码目录。

安装器会：

1. 检查系统依赖、Python 和安装包完整性。
2. 在数据目录创建或复用 `.env`，补齐缺失的随机会话密钥；文件权限保持 `0600`。
3. 安装代码并创建独立 `.venv`，用 `--no-index` 从 wheelhouse 安装 Python 依赖。
4. 复用 `nblane setup` 初始化档案、可选 AI 与管理员，再运行 `nblane validate`。
5. 安装并启动 `nblane-reader.service`（8502）和 `nblane-web-api.service`（8504），检查两个服务的健康状态。

两个服务都只监听 `127.0.0.1` 且使用单 worker。已有 profile、`.env`、`auth/users.yaml` 和论文资产不被安装包覆盖；`.env` 中已有的 LLM 配置保留。首次安装后可在「设置 → AI 服务」填写 Key。

常用变量：

| 变量 | 默认 / 用途 |
|------|-------------|
| `NBLANE_INSTALL_ROOT` / `NBLANE_ROOT` | 覆盖代码 / 数据目录 |
| `NBLANE_ASSET_ROOT` / `NBLANE_BACKUP_DIR` | 覆盖资产 / 代码备份目录 |
| `NBLANE_PROFILE` / `NBLANE_SCHEMA` | 初始档案名 / 领域技能树 |
| `NBLANE_LLM=skip` | 跳过 AI 配置；已有 `.env` 不会被清空 |
| `NBLANE_LLM=dashscope` 等 | 复用 setup 的预设；用 `NBLANE_LLM_KEY_ENV` 指定密钥环境变量 |
| `NBLANE_ADMIN_USER` | 初始管理员，默认 `admin` |
| `NBLANE_AUTH=0` | 仅用于全新、本机且不登录的安装，不用于关闭已有部署的登录 |
| `NBLANE_SKIP_SYSTEMD=1` | 只安装文件，不改 systemd / Caddy；用于隔离验收 |

### 域名与 HTTPS

未设置域名时不改 Caddy，也不要把 8502 / 8504 直接暴露到公网。本机访问或 SSH 转发使用上述回环地址；SSH 转发必须同时转发 8504 和 8502，否则论文库和阅读器无法连接。手机或公网访问应配置域名与 HTTPS。

已安装 Caddy 时：

```bash
sudo NBLANE_DOMAIN=example.com ./install.sh
```

这会写入独立的 `/etc/caddy/sites/nblane.caddy`，在主配置追加对应 import，校验并重载 Caddy，同时开启安全 Cookie 与可信反代头。`NBLANE_INSTALL_CADDY=1` 可允许 apt 安装 Caddy；系统包安装与证书签发仍需要网络、域名 DNS 和 80/443 可达。

已有其他 Caddy 站点或 OpenClaw 路由时，先核对现有配置。此安装器不接管其他站点。

## 升级

解压新版本后，在与原安装相同的目录配置下再次运行：

```bash
sudo ./install.sh
```

相同命令就是升级：旧代码（包括旧 `.venv`）先移入 `backup-<时间>-<版本>` 目录，再安装新版本并重建虚拟环境。已有账号后不需要再传 `NBLANE_ADMIN_PASSWORD`。升级不会清空或重建数据目录。

升级会按本次参数重写两个 nblane unit；原安装若设置了 `NBLANE_DOMAIN`、自定义目录、服务账号或其他运行参数，每次升级都要传相同的值。例如域名安装后的升级使用 `sudo NBLANE_DOMAIN=example.com ./install.sh`。普通 drop-in 和其他 Caddy 站点不由安装器管理。

`/srv/nblane-app/nblane/BUILDINFO` 记录当前包的版本和 commit。数据 Git 自动提交默认开启，自动推送默认关闭；远程私有仓库和每日备份仍需按部署文档配置。

若安装失败，可根据输出修复后重试；旧代码在备份目录，安装器不会把失败静默转成联网安装或删除数据。

## 回滚

从已安装代码回滚到最近一次旧代码备份：

```bash
sudo /srv/nblane-app/nblane/packaging/ubuntu/install.sh --rollback
```

指定某次备份：

```bash
sudo NBLANE_ROLLBACK_DIR=/srv/nblane-app/nblane-backups/<备份目录> \
  /srv/nblane-app/nblane/packaging/ubuntu/install.sh --rollback
```

回滚前会把当前代码另存为 `failed-<时间>`，恢复后重新检查服务。默认只选择 `backup-*` 正式代码备份，不把失败安装目录当作回滚目标；`NBLANE_ROLLBACK_DIR` 必须位于代码备份目录内。回滚不重跑 setup，也不重写现有 systemd / Caddy 配置；需要更改这些配置时使用升级安装命令。

**回滚只恢复代码，不恢复数据，也不撤销数据格式变化**；数据恢复使用私有 Git 与迁移文档。

## 安装后检查

```bash
systemctl status nblane-reader nblane-web-api --no-pager
curl -fsS http://127.0.0.1:8504/api/v1/health
curl -fsS http://127.0.0.1:8502/auth/session-ok
sudo -u <服务账号> /srv/nblane-app/nblane/.venv/bin/nblane doctor \
  --unit nblane-web-api.service
journalctl -u nblane-web-api -n 100 --no-pager
```

手动 CLI 使用与安装时相同的 `NBLANE_ROOT`；systemd 服务已由安装器设置。自定义运行环境的 Codex、代理和超时参数建议放 systemd drop-in，参见[腾讯云部署](deployment-tencent-cloud.md)。开发源码安装见[本机安装](setup.md)。
