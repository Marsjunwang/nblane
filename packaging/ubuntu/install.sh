#!/usr/bin/env bash
# Install, upgrade or roll back nblane from an Ubuntu release package.
set -euo pipefail

package_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
action="install"
while (($#)); do
  case "$1" in
    --rollback)
      action="rollback"
      ;;
    -h|--help)
      cat <<'EOF'
Usage: ./install.sh [--rollback]

Install or upgrade nblane. Existing profiles, auth accounts and .env are kept.
Use --rollback to restore code only; existing service and Caddy config is kept.

Common environment variables:
  NBLANE_INSTALL_ROOT  Code directory (default /srv/nblane-app/nblane)
  NBLANE_ROOT          Data directory (default /srv/nblane-data)
  NBLANE_ASSET_ROOT    Asset directory (default /srv/nblane-assets/research)
  NBLANE_SERVICE_USER  Service account (default the invoking sudo user)
  NBLANE_PROFILE       Initial profile (default default)
  NBLANE_LLM           LLM preset (default skip)
  NBLANE_AUTH          1 enables login (default), 0 for a new local-only install
  NBLANE_ADMIN_USER    Initial administrator id (default admin)
  NBLANE_ADMIN_PASSWORD  Initial password for a new auth file (minimum 10 chars)
  NBLANE_DOMAIN        Configure Caddy HTTPS only when non-empty
  NBLANE_WITH_CADDY    Override Caddy setup (default follows NBLANE_DOMAIN)
  NBLANE_INSTALL_CADDY 1 permits apt installation of Caddy
  NBLANE_INSTALL_APT   1 permits apt installation of git, tmux and curl
  NBLANE_SKIP_SYSTEMD  1 installs files only; no service or Caddy changes
  NBLANE_BACKUP_DIR    Backup directory (default next to the code directory)
  NBLANE_ROLLBACK_DIR  Explicit backup to restore (must be inside backup dir)
  NBLANE_ALLOW_ONLINE_INSTALL 1 permits pip networking without a wheelhouse
EOF
      exit 0
      ;;
    *)
      printf '未知参数：%s\n' "$1" >&2
      exit 2
      ;;
  esac
  shift
done

NBLANE_INSTALL_ROOT="${NBLANE_INSTALL_ROOT:-/srv/nblane-app/nblane}"
NBLANE_ROOT="${NBLANE_ROOT:-/srv/nblane-data}"
NBLANE_ASSET_ROOT="${NBLANE_ASSET_ROOT:-/srv/nblane-assets/research}"
NBLANE_SERVICE_USER="${NBLANE_SERVICE_USER:-${SUDO_USER:-$(id -un)}}"
NBLANE_PROFILE="${NBLANE_PROFILE:-default}"
NBLANE_SCHEMA="${NBLANE_SCHEMA:-}"
NBLANE_LLM="${NBLANE_LLM:-skip}"
NBLANE_LLM_KEY_ENV="${NBLANE_LLM_KEY_ENV:-}"
NBLANE_TEST_LLM="${NBLANE_TEST_LLM:-0}"
NBLANE_AUTH="${NBLANE_AUTH:-1}"
NBLANE_ADMIN_USER="${NBLANE_ADMIN_USER:-admin}"
NBLANE_ADMIN_PASSWORD="${NBLANE_ADMIN_PASSWORD:-}"
NBLANE_DOMAIN="${NBLANE_DOMAIN:-}"
if [[ -n "$NBLANE_DOMAIN" ]]; then
  NBLANE_WITH_CADDY="${NBLANE_WITH_CADDY:-1}"
else
  NBLANE_WITH_CADDY="${NBLANE_WITH_CADDY:-0}"
fi
NBLANE_INSTALL_APT="${NBLANE_INSTALL_APT:-0}"
NBLANE_INSTALL_CADDY="${NBLANE_INSTALL_CADDY:-0}"
NBLANE_SKIP_SYSTEMD="${NBLANE_SKIP_SYSTEMD:-0}"
NBLANE_AUTH_COOKIE_SECURE="${NBLANE_AUTH_COOKIE_SECURE:-$NBLANE_WITH_CADDY}"
NBLANE_DATA_GIT_AUTOCOMMIT="${NBLANE_DATA_GIT_AUTOCOMMIT:-1}"
NBLANE_DATA_GIT_AUTOPUSH="${NBLANE_DATA_GIT_AUTOPUSH:-0}"
NBLANE_GROBID_URL="${NBLANE_GROBID_URL:-off}"
NBLANE_TRUST_PROXY_HEADERS="${NBLANE_TRUST_PROXY_HEADERS:-$NBLANE_WITH_CADDY}"
NBLANE_AUTH_FILE="${NBLANE_AUTH_FILE:-$NBLANE_ROOT/auth/users.yaml}"
NBLANE_BACKUP_DIR="${NBLANE_BACKUP_DIR:-$(dirname "$NBLANE_INSTALL_ROOT")/nblane-backups}"
code_root="$(realpath -m "$NBLANE_INSTALL_ROOT")"
data_root="$(realpath -m "$NBLANE_ROOT")"
asset_root="$(realpath -m "$NBLANE_ASSET_ROOT")"
backup_root="$(realpath -m "$NBLANE_BACKUP_DIR")"
NBLANE_ROOT="$data_root"
NBLANE_ASSET_ROOT="$asset_root"
NBLANE_ENV_FILE="$data_root/.env"
export NBLANE_ROOT NBLANE_ASSET_ROOT NBLANE_ENV_FILE NBLANE_ADMIN_PASSWORD

fail() {
  printf '错误：%s\n' "$*" >&2
  exit 1
}

case "$NBLANE_AUTH" in
  0|1) ;;
  *) fail "NBLANE_AUTH 只能是 0 或 1。" ;;
esac
if [[ "$NBLANE_AUTH" == "1" ]]; then
  NBLANE_AUTH_FILE="$(realpath -m "$NBLANE_AUTH_FILE")"
else
  NBLANE_AUTH_FILE=""
fi
export NBLANE_AUTH_FILE
id -u "$NBLANE_SERVICE_USER" >/dev/null 2>&1 || fail "服务账号不存在：$NBLANE_SERVICE_USER"
[[ "$code_root" != "/" && "$data_root" != "/" && "$asset_root" != "/" && "$backup_root" != "/" ]] || \
  fail "代码、数据、资产和备份目录不能是根目录。"
case "$data_root" in
  "$code_root"|"$code_root"/*)
    fail "数据目录不能位于代码目录内：$data_root。请使用独立的 NBLANE_ROOT。"
    ;;
esac
case "$asset_root" in
  "$code_root"|"$code_root"/*)
    fail "资产目录不能位于代码目录内：$asset_root。"
    ;;
esac
case "$backup_root" in
  "$code_root"|"$code_root"/*|"$data_root"|"$data_root"/*)
    fail "备份目录必须独立于代码和数据目录：$backup_root。"
    ;;
esac
if [[ "$NBLANE_AUTH" == "1" ]]; then
  case "$NBLANE_AUTH_FILE" in
    "$code_root"|"$code_root"/*)
      fail "账号文件不能位于代码目录内：$NBLANE_AUTH_FILE。"
      ;;
  esac
fi

require_systemd_root() {
  if [[ "$NBLANE_SKIP_SYSTEMD" != "1" && "$EUID" -ne 0 ]]; then
    fail "安装 systemd 服务需要 root；请使用 sudo，或设置 NBLANE_SKIP_SYSTEMD=1 仅安装文件。"
  fi
}

install_apt_packages() {
  [[ "$NBLANE_INSTALL_APT" == "1" ]] || return 1
  [[ "$EUID" -eq 0 ]] || fail "安装系统包需要 root。"
  export DEBIAN_FRONTEND=noninteractive
  apt-get update
  apt-get install -y "$@"
}

check_commands() {
  local missing=()
  local command_name
  for command_name in git tmux curl tar realpath find; do
    command -v "$command_name" >/dev/null 2>&1 || missing+=("$command_name")
  done
  if ((${#missing[@]})); then
    install_apt_packages git tmux curl || fail "缺少命令：${missing[*]}。请先安装，或设置 NBLANE_INSTALL_APT=1 自动安装基础包。"
  fi
}

choose_python() {
  local candidate
  for candidate in ${PYTHON:-} python3.13 python3.12 python3.11 python3; do
    [[ -n "$candidate" ]] || continue
    if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; sys.exit(sys.version_info < (3, 11))' 2>/dev/null; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  fail "需要 Python ≥ 3.11。可用 PYTHON=/path/to/python 指定解释器。"
}

service_user_home() {
  getent passwd "$NBLANE_SERVICE_USER" | cut -d: -f6
}

run_as_user() {
  if [[ "$EUID" -eq 0 && "$NBLANE_SERVICE_USER" != "root" ]]; then
    local -a env_args=(
      "HOME=$(service_user_home)"
      "NBLANE_ROOT=$NBLANE_ROOT"
      "NBLANE_AUTH_FILE=${NBLANE_AUTH_FILE:-}"
      "NBLANE_ENV_FILE=$NBLANE_ENV_FILE"
      "NBLANE_ADMIN_PASSWORD=$NBLANE_ADMIN_PASSWORD"
    )
    if [[ -n "${NBLANE_DISABLE_NETWORK_LOOKUPS:-}" ]]; then
      env_args+=("NBLANE_DISABLE_NETWORK_LOOKUPS=$NBLANE_DISABLE_NETWORK_LOOKUPS")
    fi
    if [[ -n "$NBLANE_LLM_KEY_ENV" ]]; then
      env_args+=("$NBLANE_LLM_KEY_ENV=${!NBLANE_LLM_KEY_ENV:-}")
    fi
    runuser -u "$NBLANE_SERVICE_USER" -- env "${env_args[@]}" "$@"
  else
    "$@"
  fi
}

chown_tree() {
  if [[ "$EUID" -eq 0 ]]; then
    chown -R "$NBLANE_SERVICE_USER:$(id -gn "$NBLANE_SERVICE_USER")" "$code_root" "$data_root" "$asset_root"
  fi
}

stop_services() {
  [[ "$NBLANE_SKIP_SYSTEMD" == "1" ]] && return 0
  if [[ -f /etc/systemd/system/nblane-web-api.service || -f /etc/systemd/system/nblane-reader.service ]]; then
    systemctl stop nblane-web-api nblane-reader
  fi
}

append_env_if_missing() {
  local key="$1"
  local value="$2"
  local env_file="$data_root/.env"
  if ! grep -q "^${key}=" "$env_file"; then
    printf '%s=%s\n' "$key" "$value" >> "$env_file"
  fi
}

prepare_data() {
  mkdir -p "$data_root/profiles" "$asset_root"
  if [[ "$NBLANE_AUTH" == "1" ]]; then
    mkdir -p "$(dirname "$NBLANE_AUTH_FILE")"
  fi
  local env_file="$data_root/.env"
  if [[ ! -f "$env_file" ]]; then
    (umask 077 && : > "$env_file")
  fi
  chmod 600 "$env_file"
  append_env_if_missing NBLANE_READER_TOKEN_SECRET "$($python_bin -c 'import secrets; print(secrets.token_hex(32))')"
  append_env_if_missing NBLANE_AUTH_COOKIE_SECURE "$NBLANE_AUTH_COOKIE_SECURE"
  append_env_if_missing NBLANE_GROBID_URL "$NBLANE_GROBID_URL"
}

prepare_admin_password() {
  generated_password=0
  if [[ "$NBLANE_AUTH" != "1" || -f "$NBLANE_AUTH_FILE" ]]; then
    return 0
  fi
  if [[ -z "$NBLANE_ADMIN_PASSWORD" ]]; then
    if [[ -t 0 && -t 1 ]]; then
      NBLANE_ADMIN_PASSWORD="$($python_bin -c 'import secrets; print(secrets.token_urlsafe(18))')"
      export NBLANE_ADMIN_PASSWORD
      generated_password=1
    else
      fail "首次启用登录时，请通过 NBLANE_ADMIN_PASSWORD 提供至少 10 位的初始密码，或在终端运行以自动生成。"
    fi
  fi
  ((${#NBLANE_ADMIN_PASSWORD} >= 10)) || fail "初始管理员密码至少需要 10 位。"
}

backup_code() {
  [[ -d "$code_root" ]] || return 0
  mkdir -p "$backup_root"
  local destination="$backup_root/backup-$(date -u +%Y%m%dT%H%M%SZ)-${VERSION:-previous}"
  if [[ -e "$destination" ]]; then
    destination="$destination-$$"
  fi
  mv "$code_root" "$destination"
  printf '旧代码已备份到：%s\n' "$destination"
}

install_code() {
  if [[ ! -d "$package_dir/wheelhouse" && "${NBLANE_ALLOW_ONLINE_INSTALL:-0}" != "1" ]]; then
    fail "安装包缺少离线依赖。请重新生成完整包；开发包必须显式设置 NBLANE_ALLOW_ONLINE_INSTALL=1 才允许联网安装。"
  fi
  tar -tzf "$package_dir/$SOURCE_ARCHIVE" pyproject.toml >/dev/null 2>&1 || \
    fail "源码快照损坏或缺少 pyproject.toml，尚未改动现有安装。"
  stop_services
  backup_code
  mkdir -p "$code_root"
  tar -xzf "$package_dir/$SOURCE_ARCHIVE" -C "$code_root"
  cp "$package_dir/BUILDINFO" "$code_root/BUILDINFO"
  chown_tree
  if [[ ! -x "$code_root/.venv/bin/python" ]]; then
    run_as_user "$python_bin" -m venv "$code_root/.venv" || \
      fail "创建虚拟环境失败；请先安装与 Python 版本对应的 venv 包（如 python3-venv）。"
  fi
  local -a pip_args=()
  if [[ -d "$package_dir/wheelhouse" ]]; then
    pip_args+=(--no-index --find-links "$package_dir/wheelhouse")
  fi
  run_as_user "$code_root/.venv/bin/python" -m pip install "${pip_args[@]}" -e "$code_root"
}

run_setup() {
  local -a args=(
    "$code_root/.venv/bin/nblane" setup --yes
    --profile "$NBLANE_PROFILE"
    --llm "$NBLANE_LLM"
  )
  if [[ "$NBLANE_TEST_LLM" == "1" ]]; then
    args+=(--test-llm)
  else
    args+=(--no-test-llm)
  fi
  if [[ -n "$NBLANE_SCHEMA" ]]; then
    args+=(--schema "$NBLANE_SCHEMA")
  fi
  if [[ -n "$NBLANE_LLM_KEY_ENV" ]]; then
    args+=(--llm-key-env "$NBLANE_LLM_KEY_ENV")
  fi
  if [[ "$NBLANE_AUTH" == "1" ]]; then
    args+=(--auth --admin-user "$NBLANE_ADMIN_USER" --admin-password-env NBLANE_ADMIN_PASSWORD)
  else
    args+=(--no-auth)
  fi
  run_as_user "${args[@]}"
  run_as_user "$code_root/.venv/bin/nblane" validate
}

write_unit_files() {
  [[ "$NBLANE_SKIP_SYSTEMD" == "1" ]] && return 0
  local reader_api_base="${NBLANE_READER_API_BASE:-}"
  if [[ -z "$reader_api_base" ]]; then
    if [[ "$NBLANE_WITH_CADDY" == "1" ]]; then
      reader_api_base="0"
    else
      reader_api_base="http://127.0.0.1:8502"
    fi
  fi
  local auth_environment=""
  if [[ "$NBLANE_AUTH" == "1" ]]; then
    auth_environment="Environment=NBLANE_AUTH_FILE=$NBLANE_AUTH_FILE"
  fi
  cat > /etc/systemd/system/nblane-reader.service <<EOF
[Unit]
Description=nblane Paper Reader API
After=network.target

[Service]
Type=simple
User=$NBLANE_SERVICE_USER
WorkingDirectory=$code_root
Environment=NBLANE_ROOT=$NBLANE_ROOT
Environment=NBLANE_RESEARCH_ASSET_ROOT=$NBLANE_ASSET_ROOT
Environment=NBLANE_READER_API_BASE=$reader_api_base
Environment=UI_LANG=zh
Environment=LLM_REPLY_LANG=zh
Environment=NBLANE_GROBID_URL=$NBLANE_GROBID_URL
EnvironmentFile=-$data_root/.env
$auth_environment
ExecStart=$code_root/.venv/bin/uvicorn nblane.web_reader_api:app --host 127.0.0.1 --port 8502 --workers 1
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

  cat > /etc/systemd/system/nblane-web-api.service <<EOF
[Unit]
Description=nblane Web API (SPA backend)
After=network.target nblane-reader.service

[Service]
Type=simple
User=$NBLANE_SERVICE_USER
WorkingDirectory=$code_root
Environment=NBLANE_ROOT=$NBLANE_ROOT
Environment=NBLANE_RESEARCH_ASSET_ROOT=$NBLANE_ASSET_ROOT
Environment=NBLANE_READER_API_BASE=$reader_api_base
Environment=NBLANE_DATA_GIT_AUTOCOMMIT=$NBLANE_DATA_GIT_AUTOCOMMIT
Environment=NBLANE_DATA_GIT_AUTOPUSH=$NBLANE_DATA_GIT_AUTOPUSH
Environment=NBLANE_GROBID_URL=$NBLANE_GROBID_URL
Environment=NBLANE_TRUST_PROXY_HEADERS=$NBLANE_TRUST_PROXY_HEADERS
Environment=UI_LANG=zh
Environment=LLM_REPLY_LANG=zh
EnvironmentFile=-$data_root/.env
$auth_environment
ExecStart=$code_root/.venv/bin/uvicorn nblane.web_api:app --host 127.0.0.1 --port 8504 --workers 1
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
  systemctl daemon-reload
}

configure_caddy() {
  [[ "$NBLANE_WITH_CADDY" == "1" && "$NBLANE_SKIP_SYSTEMD" != "1" ]] || return 0
  [[ -n "$NBLANE_DOMAIN" ]] || fail "配置 Caddy 必须设置 NBLANE_DOMAIN。"
  if ! command -v caddy >/dev/null 2>&1; then
    if [[ "$NBLANE_INSTALL_CADDY" == "1" && "$EUID" -eq 0 ]]; then
      export DEBIAN_FRONTEND=noninteractive
      apt-get update
      apt-get install -y caddy
    else
      fail "未找到 Caddy。请安装后重试，或设置 NBLANE_INSTALL_CADDY=1 自动安装。"
    fi
  fi
  mkdir -p /etc/caddy/sites
  cat > /etc/caddy/sites/nblane.caddy <<EOF
$NBLANE_DOMAIN {
    handle /reader/* {
        reverse_proxy 127.0.0.1:8502
    }
    handle /paper-library* {
        reverse_proxy 127.0.0.1:8502
    }
    handle /api/research/* {
        reverse_proxy 127.0.0.1:8502
    }
    handle /auth/session* {
        reverse_proxy 127.0.0.1:8502
    }
    reverse_proxy 127.0.0.1:8504
}
EOF
  local main_config=/etc/caddy/Caddyfile
  touch "$main_config"
  if ! grep -Eq '^[[:space:]]*import[[:space:]]+/etc/caddy/sites/(\*|nblane\.caddy)' "$main_config"; then
    printf '\nimport /etc/caddy/sites/nblane.caddy\n' >> "$main_config"
  fi
  caddy validate --config "$main_config"
  systemctl enable --now caddy
  systemctl reload caddy
}

check_health() {
  [[ "$NBLANE_SKIP_SYSTEMD" == "1" ]] && return 0
  systemctl enable --now nblane-reader nblane-web-api
  local attempt
  for attempt in {1..40}; do
    if curl -fsS --max-time 2 http://127.0.0.1:8504/api/v1/health >/dev/null && \
      curl -fsS --max-time 2 http://127.0.0.1:8502/auth/session-ok >/dev/null; then
      systemctl is-active nblane-web-api nblane-reader
      return 0
    fi
    sleep 0.5
  done
  systemctl status nblane-web-api nblane-reader --no-pager || true
  fail "服务健康检查失败，请检查 systemctl status 和 journalctl。"
}

rollback() {
  require_systemd_root
  [[ -d "$backup_root" ]] || fail "没有可用备份：$backup_root"
  local restore
  if [[ -n "${NBLANE_ROLLBACK_DIR:-}" ]]; then
    restore="$(realpath -m "$NBLANE_ROLLBACK_DIR")"
  else
    restore="$(find "$backup_root" -mindepth 1 -maxdepth 1 -type d -name 'backup-*' -printf '%f\n' | sort | tail -n 1)"
    [[ -n "$restore" ]] || fail "没有可用的代码备份：$backup_root"
    restore="$backup_root/$restore"
  fi
  case "$restore" in
    "$backup_root"/*) ;;
    *) fail "回滚目录必须位于 $backup_root 内。" ;;
  esac
  [[ -d "$restore" ]] || fail "备份不存在：$restore"
  [[ -f "$restore/pyproject.toml" ]] || fail "备份缺少 pyproject.toml：$restore"
  stop_services
  if [[ -d "$code_root" ]]; then
    mv "$code_root" "$backup_root/failed-$(date -u +%Y%m%dT%H%M%SZ)-$$"
  fi
  mkdir -p "$(dirname "$code_root")"
  cp -a "$restore" "$code_root"
  chown_tree
  check_health
  printf '已恢复备份：%s\n' "$restore"
}

require_systemd_root
check_commands
python_bin="$(choose_python)"
if [[ "$action" == "rollback" ]]; then
  rollback
  exit 0
fi

[[ -f "$package_dir/BUILDINFO" ]] || fail "安装包缺少 BUILDINFO：$package_dir"
# shellcheck source=BUILDINFO
source "$package_dir/BUILDINFO"
[[ -n "${SOURCE_ARCHIVE:-}" ]] || fail "BUILDINFO 缺少 SOURCE_ARCHIVE。"
[[ -f "$package_dir/$SOURCE_ARCHIVE" ]] || fail "找不到源码快照：$package_dir/$SOURCE_ARCHIVE"
if [[ -n "$NBLANE_LLM_KEY_ENV" ]]; then
  [[ "$NBLANE_LLM_KEY_ENV" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || fail "NBLANE_LLM_KEY_ENV 必须是环境变量名。"
  [[ -n "${!NBLANE_LLM_KEY_ENV:-}" ]] || fail "LLM 密钥环境变量 $NBLANE_LLM_KEY_ENV 为空。"
fi

prepare_admin_password
prepare_data
install_code
run_setup
[[ -d "$data_root/profiles/$NBLANE_PROFILE" ]] || fail "档案 $NBLANE_PROFILE 未创建，请检查名称和领域技能树。"
if [[ "${generated_password:-0}" == "1" ]]; then
  printf '初始管理员 %s 的密码（仅显示一次）：%s\n' "$NBLANE_ADMIN_USER" "$NBLANE_ADMIN_PASSWORD"
fi
chown_tree
write_unit_files
configure_caddy
check_health

printf '安装完成：代码 %s，数据 %s\n' "$code_root" "$data_root"
if [[ "$NBLANE_SKIP_SYSTEMD" == "1" ]]; then
  printf '已按 NBLANE_SKIP_SYSTEMD=1 跳过 systemd 和 Caddy 配置。\n'
elif [[ "$NBLANE_WITH_CADDY" == "1" ]]; then
  printf '访问地址：https://%s\n' "$NBLANE_DOMAIN"
else
  printf '访问地址：http://127.0.0.1:8504\n'
fi
