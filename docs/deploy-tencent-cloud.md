# Tencent Cloud Small-Team Deployment

This guide deploys the nblane Streamlit Web UI with HTTPS, app-level login, file-based data, and optional private Git backup.

## Layout

Keep app code and private data separate:

```text
/srv/nblane-app       # this code repository
/srv/nblane-data      # private data repository: profiles/ schemas/ teams/ auth/
```

Set:

```bash
NBLANE_ROOT=/srv/nblane-data
NBLANE_AUTH_FILE=/srv/nblane-data/auth/users.yaml
```

Create password hashes with:

```bash
nblane auth hash-password
```

Use `auth/users.example.yaml` as the starting shape. `admin` users can access every profile/team and create profiles; `member` users can access only their configured `profile` and `teams`.

## systemd

Example `/etc/systemd/system/nblane.service`:

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

## HTTPS

Use Caddy or Nginx as the public entrypoint. Caddy example:

```caddyfile
your-domain.com {
    reverse_proxy 127.0.0.1:8501
}
```

Do not expose Streamlit port `8501` to the public internet.

## Tencent Cloud Notes

Security group:

- Open `TCP:80,443` for Web.
- Restrict `TCP:22` to administrator IPs.
- Do not open `8501`, database ports, or all ports.

Tencent Cloud references:

- [Security group overview](https://cloud.tencent.com/document/product/213/112610)
- [Add security group rules](https://cloud.tencent.com/document/product/213/112614)
- [ICP access filing](https://cloud.tencent.com/document/product/243/97669)
- [Domain filing requirements](https://cloud.tencent.com/document/product/243/18905)

## Backup

In `/srv/nblane-data`, configure a private Git remote and deploy key. With these enabled:

```bash
NBLANE_DATA_GIT_AUTOCOMMIT=1
NBLANE_DATA_GIT_AUTOPUSH=1
```

successful Web writes commit changed data files and attempt `git push`. Push failures show a Web warning but do not roll back the saved file.
