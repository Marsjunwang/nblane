# 腾讯云小团队部署

本文面向 nblane 的 Streamlit Web UI：公网入口用域名 + HTTPS，应用内账号登录，数据继续放在纯文件 + 私有 Git 仓库中。

## 目录布局

推荐把代码和私有数据分开：

```text
/srv/nblane-app       # 本仓库代码，运行 Streamlit
/srv/nblane-data      # 私有数据仓库，含 profiles/ schemas/ teams/ auth/
```

`/srv/nblane-data` 中至少包含：

```text
profiles/
schemas/
teams/
auth/users.yaml
```

`auth/users.yaml` 可参考仓库内的 `auth/users.example.yaml`。密码哈希用：

```bash
nblane auth hash-password
```

成员配置规则：

- `role: admin`：可访问所有 profile 和 team，可创建新 profile。
- `role: member`：只能访问自己的 `profile`，以及 `teams` 列表中允许的团队。
- `teams: ["*"]`：允许访问所有团队。

## systemd

示例服务文件 `/etc/systemd/system/nblane.service`：

```ini
[Unit]
Description=nblane Streamlit Web UI
After=network.target

[Service]
Type=simple
User=nblane
WorkingDirectory=/srv/nblane-app
Environment=NBLANE_ROOT=/srv/nblane-data
Environment=NBLANE_AUTH_FILE=/srv/nblane-data/auth/users.yaml
Environment=LLM_REPLY_LANG=zh
Environment=NBLANE_DATA_GIT_AUTOCOMMIT=1
Environment=NBLANE_DATA_GIT_AUTOPUSH=1
EnvironmentFile=-/srv/nblane-data/.env
ExecStart=/srv/nblane-app/.venv/bin/streamlit run app.py --server.address=127.0.0.1 --server.port=8501 --server.headless=true
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启动：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now nblane
sudo systemctl status nblane
```

## HTTPS 反向代理

推荐 Caddy。示例 `/etc/caddy/Caddyfile`：

```caddyfile
your-domain.com {
    reverse_proxy 127.0.0.1:8501
}
```

Streamlit 只监听 `127.0.0.1:8501`，不要在腾讯云安全组开放 `8501`。

## 腾讯云安全组与备案

安全组只开放必要端口：

- `TCP:80,443`：公网 Web。
- `TCP:22`：仅允许管理员固定 IP。
- 不开放 `8501`、数据库端口或全端口。

腾讯云官方文档：

- [安全组概述](https://cloud.tencent.com/document/product/213/112610)
- [添加安全组规则](https://cloud.tencent.com/document/product/213/112614)

如果使用中国大陆地域 CVM + 域名访问，需要按腾讯云要求完成备案或接入备案：

- [接入备案](https://cloud.tencent.com/document/product/243/97669)
- [备案域名要求](https://cloud.tencent.com/document/product/243/18905)

## 私有 Git 备份

在 `/srv/nblane-data` 初始化私有 Git 远端并配置 deploy key。Web 保存成功后，若启用：

```bash
NBLANE_DATA_GIT_AUTOCOMMIT=1
NBLANE_DATA_GIT_AUTOPUSH=1
```

nblane 会自动 `git add`、`git commit`，并尝试 `git push`。如果 push 失败，页面会提示 warning，但不会回滚用户已经保存的文件。

## 验收

- `https://your-domain.com` 显示登录页。
- 未登录访问 Home 或任意 `pages/*.py` 都会被登录页拦住。
- member 账号只能看到自己的 profile；admin 可看到全部 profile。
- 修改 `kanban.md` 或 `skill-tree.yaml` 后，`/srv/nblane-data` 产生 Git commit。
- 两个浏览器同时编辑同一文件时，后保存的一方会收到刷新提示，不会静默覆盖。
