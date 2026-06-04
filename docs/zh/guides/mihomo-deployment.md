---
status: active
owner: engineering
last_verified: 2026-06-04
source_of_truth: true
---

# Mihomo 代理部署

本文说明如何在 Linux 服务器上部署 [MetaCubeX/mihomo](https://github.com/MetaCubeX/mihomo/releases) 作为本机代理，复刻 nblane 生产环境的当前配置。适用于国内服务器需要访问 GitHub、arXiv、海外 LLM API 等场景。

订阅地址通常包含 token，应按密钥处理：**不要写进公开仓库、截图或提交记录**。下文用 `<SUB_URL>` 表示你的订阅 URL。

## 环境概览

| 项目 | 值 |
|------|-----|
| 二进制 | `/usr/local/bin/mihomo` |
| 配置目录 | `~/.config/mihomo/` |
| 代理端口 | `7890`（HTTP + SOCKS 混合，`mixed-port`） |
| 控制面板 | `http://127.0.0.1:9090/ui` |
| 服务方式 | systemd 用户服务 + `linger` |
| 节点来源 | 订阅 proxy-provider（如 SSRDOG） |

## 第 1 步：安装 mihomo

```bash
cd /tmp

# x86_64 服务器；版本号可按 GitHub Releases 更新
curl -LO https://github.com/MetaCubeX/mihomo/releases/download/v1.19.24/mihomo-linux-amd64-compatible-v1.19.24.gz
gzip -d mihomo-linux-amd64-compatible-v1.19.24.gz
chmod +x mihomo-linux-amd64-compatible-v1.19.24
sudo mv mihomo-linux-amd64-compatible-v1.19.24 /usr/local/bin/mihomo

mihomo -v
```

如果 GitHub 直连不可用，可在本地下载对应架构的包后上传到服务器；只要 `/usr/local/bin/mihomo` 可执行即可。

ARM 服务器选用 `mihomo-linux-arm64-*` 等对应资产。

## 第 2 步：创建目录

```bash
mkdir -p ~/.config/mihomo/proxy_providers
mkdir -p ~/.config/systemd/user
```

## 第 3 步：写入配置

```bash
nano ~/.config/mihomo/config.yaml
```

```yaml
mixed-port: 7890
allow-lan: false
bind-address: 127.0.0.1

mode: rule
log-level: info
ipv6: false

external-controller: 127.0.0.1:9090
secret: "mihomo-local-2026"
external-ui: ui

profile:
  store-selected: true
  store-fake-ip: true

unified-delay: true
tcp-concurrent: true

geodata-mode: false

proxy-providers:
  subscription:
    type: http
    url: "<SUB_URL>"
    path: ./proxy_providers/subscription.yaml
    proxy: DIRECT
    header:
      User-Agent:
        - clash.meta
      X-Forwarded-For:
        - 114.114.114.114
    interval: 3600
    health-check:
      enable: true
      url: http://cp.cloudflare.com/generate_204
      interval: 300
      timeout: 8000
      lazy: true
      expected-status: 204

proxy-groups:
  - name: PROXY
    type: select
    use:
      - subscription
    proxies:
      - AUTO
      - DIRECT

  - name: AUTO
    type: url-test
    use:
      - subscription
    url: http://cp.cloudflare.com/generate_204
    interval: 300
    timeout: 8000
    tolerance: 50

  - name: GLOBAL
    type: select
    proxies:
      - PROXY
      - AUTO
      - DIRECT

rules:
  - DOMAIN-SUFFIX,localhost,DIRECT
  - DOMAIN-SUFFIX,local,DIRECT
  - IP-CIDR,127.0.0.0/8,DIRECT,no-resolve
  - IP-CIDR,10.0.0.0/8,DIRECT,no-resolve
  - IP-CIDR,172.16.0.0/12,DIRECT,no-resolve
  - IP-CIDR,192.168.0.0/16,DIRECT,no-resolve
  - GEOIP,CN,DIRECT
  - MATCH,PROXY
```

说明：

- `proxy: DIRECT`：拉取订阅走直连，避免循环依赖。
- 健康检查使用 `cp.cloudflare.com`，比 `gstatic.com` 更准确（后者可能命中 `GEOIP,CN,DIRECT` 导致误判）。
- `X-Forwarded-For` 是部分订阅站（如 SSRDOG）的风控兼容项；若你的订阅站不需要，可删除。
- `secret` 建议每台服务器改成独立值。

## 第 4 步：下载 GeoIP 数据库

`GEOIP,CN,DIRECT` 规则需要 `Country.mmdb`：

```bash
curl --fail -L \
  https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/country.mmdb \
  -o ~/.config/mihomo/Country.mmdb
```

若 GitHub 不通，可临时删除配置中的 `GEOIP,CN,DIRECT` 行，等代理跑起来后再通过代理下载。

## 第 5 步：安装 Web UI（可选）

```bash
cd ~/.config/mihomo
curl -LO https://github.com/MetaCubeX/metacubexd/archive/refs/heads/gh-pages.zip
unzip gh-pages.zip
mv metacubexd-gh-pages ui
rm gh-pages.zip
```

也可从已有服务器打包复制：

```bash
# 源服务器
tar czf /tmp/mihomo-ui.tar.gz -C ~/.config/mihomo ui

# 目标服务器
scp user@source:/tmp/mihomo-ui.tar.gz /tmp/
tar xzf /tmp/mihomo-ui.tar.gz -C ~/.config/mihomo/
```

浏览器访问 `http://127.0.0.1:9090/ui`，Secret 填 `config.yaml` 中的 `secret` 值。远程服务器需 SSH 端口转发：

```bash
ssh -L 9090:127.0.0.1:9090 user@your-server
```

## 第 6 步：systemd 用户服务

```bash
nano ~/.config/systemd/user/mihomo.service
```

```ini
[Unit]
Description=mihomo proxy service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/bin/mihomo -d %h/.config/mihomo
Restart=on-failure
RestartSec=3
LimitNOFILE=1048576

[Install]
WantedBy=default.target
```

启用并检查：

```bash
systemctl --user daemon-reload
systemctl --user enable --now mihomo.service
systemctl --user status mihomo.service
ss -ltnp | grep -E '7890|9090'
```

## 第 7 步：SSH 断开后保持运行

```bash
sudo loginctl enable-linger "$USER"
loginctl show-user "$USER" -p Linger
# 应显示 Linger=yes
```

## 第 8 步：配置终端代理

追加到 `~/.bashrc`：

```bash
# mihomo proxy
export http_proxy="http://127.0.0.1:7890"
export https_proxy="http://127.0.0.1:7890"
export all_proxy="http://127.0.0.1:7890"
export HTTP_PROXY="$http_proxy"
export HTTPS_PROXY="$https_proxy"
export ALL_PROXY="$all_proxy"
export no_proxy="localhost,127.0.0.1,::1,*.local"
export NO_PROXY="$no_proxy"
```

当前 shell 生效：

```bash
source ~/.bashrc
```

## 第 9 步：验证

```bash
# 订阅是否拉取成功
journalctl --user -u mihomo -n 20 --no-pager | grep subscription

# 代理连通性
curl -x http://127.0.0.1:7890 -o /dev/null -w "google: %{http_code}\n" https://www.google.com/generate_204
curl -x http://127.0.0.1:7890 -o /dev/null -w "github: %{http_code}\n" https://github.com
curl -x http://127.0.0.1:7890 https://api.ipify.org
```

注意：`ping` 使用 ICMP，不走 HTTP/SOCKS 代理。`curl https://www.google.com` 能通而 `ping www.google.com` 不通是正常的。

## 第 10 步：切换节点

```bash
# 查看当前节点
curl -s -H "Authorization: Bearer mihomo-local-2026" \
  http://127.0.0.1:9090/proxies/PROXY | python3 -m json.tool | grep '"now"'

# 切换到美国节点
curl -X PUT -H "Authorization: Bearer mihomo-local-2026" \
  -H "Content-Type: application/json" \
  -d '{"name":"🇺🇸 United States丨04"}' \
  http://127.0.0.1:9090/proxies/PROXY

# 切换回自动选节点
curl -X PUT -H "Authorization: Bearer mihomo-local-2026" \
  -H "Content-Type: application/json" \
  -d '{"name":"AUTO"}' \
  http://127.0.0.1:9090/proxies/PROXY
```

节点名称以订阅实际返回为准；也可在 Web UI 的 Proxies 页面点选。

## 第 11 步：让生产 systemd 服务走代理

终端 `.bashrc` 只影响交互式 shell。nblane 等 systemd 服务需单独配置 drop-in：

```bash
sudo install -d /etc/systemd/system/nblane.service.d
sudo tee /etc/systemd/system/nblane.service.d/10-proxy.conf <<'EOF'
[Service]
Environment="http_proxy=http://127.0.0.1:7890"
Environment="https_proxy=http://127.0.0.1:7890"
Environment="all_proxy=http://127.0.0.1:7890"
Environment="HTTP_PROXY=http://127.0.0.1:7890"
Environment="HTTPS_PROXY=http://127.0.0.1:7890"
Environment="ALL_PROXY=http://127.0.0.1:7890"
Environment="no_proxy=localhost,127.0.0.1,::1,*.local"
Environment="NO_PROXY=localhost,127.0.0.1,::1,*.local"
EOF

sudo systemctl daemon-reload
sudo systemctl restart nblane.service
```

Reader 服务同理，参见 [腾讯云部署](deployment-tencent-cloud.md)。

确认进程已拿到代理环境：

```bash
pid=$(systemctl show -p MainPID --value nblane.service)
sudo sh -c "tr '\0' '\n' < /proc/$pid/environ" | grep -i proxy
```

## 从已有服务器一键迁移

```bash
# 源服务器
tar czf /tmp/mihomo-bundle.tar.gz \
  -C ~/.config mihomo \
  -C ~/.config/systemd/user mihomo.service

# 目标服务器（需先安装二进制到 /usr/local/bin/mihomo）
scp user@source:/tmp/mihomo-bundle.tar.gz /tmp/
tar xzf /tmp/mihomo-bundle.tar.gz -C ~/.config/
mv ~/.config/mihomo.service ~/.config/systemd/user/ 2>/dev/null || true

systemctl --user daemon-reload
systemctl --user enable --now mihomo
sudo loginctl enable-linger "$USER"
```

迁移后仍需在目标服务器 `~/.bashrc` 中配置代理环境变量，并确认订阅 URL 仍有效。

## 常用运维

```bash
# 重启
systemctl --user restart mihomo

# 查看日志
journalctl --user -u mihomo -f

# 更新订阅（修改 config.yaml 中的 url 后重启）
systemctl --user restart mihomo

# 临时关闭代理
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
```

## 故障排查

| 现象 | 可能原因 | 处理 |
|------|----------|------|
| 订阅拉取 403 | 订阅链接过期或被撤销 | 在服务商面板重新获取 `<SUB_URL>` 并更新配置 |
| 全部节点 delay=0 | 节点不可用或健康检查 URL 误判 | 确认订阅有效；健康检查应用 `cp.cloudflare.com` |
| `curl` 走代理超时 | 节点故障或选错节点 | 在 UI 或 API 切换到 AUTO 或其他节点 |
| 启动卡住 | 缺少 `Country.mmdb` | 下载 GeoIP 数据库或临时删除 `GEOIP,CN,DIRECT` |
| SSH 退出后服务停止 | 未启用 linger | `sudo loginctl enable-linger "$USER"` |

## 相关文档

- [安装与 LLM 配置](setup.md) — nblane 主安装流程（含 mihomo 简要说明）
- [腾讯云部署](deployment-tencent-cloud.md) — 生产环境 systemd 与 Reader 代理配置
