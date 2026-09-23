#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

mode="local"
command="start"
reload="0"
profile="${NBLANE_DEV_PROFILE:-dev}"
reader_port="${NBLANE_DEV_READER_PORT:-}"
streamlit_port="${NBLANE_DEV_STREAMLIT_PORT:-}"
web_api_port="${NBLANE_DEV_WEB_API_PORT:-}"
grobid_port="${NBLANE_DEV_GROBID_PORT:-18070}"
use_grobid="0"
use_web_api="1"
runtime="${NBLANE_PAPER_LIBRARY_RUNTIME:-fastapi_iframe}"
env_file="${NBLANE_DEV_ENV_FILE:-$repo_root/.env}"
auth_file="${NBLANE_DEV_AUTH_FILE:-}"
root_arg=""
asset_root_arg=""

usage() {
  cat <<'EOF'
Usage: scripts/dev-web.sh [start|stop|status] [options]

Starts the development Streamlit UI, FastAPI Reader sidecar, and the SPA
backend (nblane.web_api) in tmux.

Commands:
  start              Start or restart dev tmux sessions. This is the default.
  stop               Stop dev tmux sessions.
  status             Show tmux sessions and health-check URLs.

Options:
  --isolated         Use isolated dev ports and data:
                     18502 / 18503 / 18504, .dev-data, .dev-assets.
  --reload           Start uvicorn with --reload --reload-dir src.
  --no-reload        Start uvicorn without reload. This is the default.
  --reader-port N    Reader sidecar port. Default: 8502, or 18502 with --isolated.
  --streamlit-port N Streamlit port. Default: 8503, or 18503 with --isolated.
  --web-api-port N   SPA backend (nblane.web_api) port.
                     Default: 8504, or 18504 with --isolated.
  --no-web-api       Do not start the SPA backend service.
  --profile NAME     Profile to create when --isolated data is first prepared.
                     Default: dev.
  --root PATH        NBLANE_ROOT for this dev run.
  --asset-root PATH  NBLANE_RESEARCH_ASSET_ROOT for this dev run.
  --runtime VALUE    Paper Library runtime: fastapi_iframe, fastapi_link,
                     or streamlit_component. Default: fastapi_iframe.
  --grobid           Point dev extraction at http://127.0.0.1:<grobid-port>.
  --grobid-port N    Host port for a dev GROBID container. Default: 18070.
  --env-file PATH    Source this shell-style env file before starting.
  --auth-file PATH   Enable app-level auth on the SPA backend (web-api)
                     session with this users.yaml (NBLANE_AUTH_FILE).
                     Default: NBLANE_DEV_AUTH_FILE, or auto-detected
                     .dev-data/auth/users.yaml in --isolated mode.
                     The Reader/Streamlit sessions stay auth-less.

Examples:
  scripts/dev-web.sh
  scripts/dev-web.sh --reload
  scripts/dev-web.sh --isolated --reload
  scripts/dev-web.sh --isolated --grobid
  scripts/dev-web.sh --no-web-api
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    start|stop|status)
      command="$1"
      shift
      ;;
    --isolated)
      mode="isolated"
      shift
      ;;
    --reload)
      reload="1"
      shift
      ;;
    --no-reload)
      reload="0"
      shift
      ;;
    --reader-port)
      reader_port="${2:?missing reader port}"
      shift 2
      ;;
    --streamlit-port)
      streamlit_port="${2:?missing streamlit port}"
      shift 2
      ;;
    --web-api-port)
      web_api_port="${2:?missing web api port}"
      shift 2
      ;;
    --no-web-api)
      use_web_api="0"
      shift
      ;;
    --profile)
      profile="${2:?missing profile name}"
      shift 2
      ;;
    --root)
      root_arg="${2:?missing root path}"
      shift 2
      ;;
    --asset-root)
      asset_root_arg="${2:?missing asset root path}"
      shift 2
      ;;
    --runtime)
      runtime="${2:?missing runtime}"
      shift 2
      ;;
    --grobid)
      use_grobid="1"
      shift
      ;;
    --grobid-port)
      grobid_port="${2:?missing grobid port}"
      shift 2
      ;;
    --env-file)
      env_file="${2:?missing env file}"
      shift 2
      ;;
    --auth-file)
      auth_file="${2:?missing auth file path}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

# Resolve port defaults after the argument loop so CLI flags always win over
# the --isolated defaults regardless of argument order.
if [[ -z "$reader_port" ]]; then
  if [[ "$mode" == "isolated" ]]; then
    reader_port="18502"
  else
    reader_port="8502"
  fi
fi
if [[ -z "$streamlit_port" ]]; then
  if [[ "$mode" == "isolated" ]]; then
    streamlit_port="18503"
  else
    streamlit_port="8503"
  fi
fi
if [[ -z "$web_api_port" ]]; then
  if [[ "$mode" == "isolated" ]]; then
    web_api_port="18504"
  else
    web_api_port="8504"
  fi
fi

if [[ "$command" == "start" && -f "$env_file" ]]; then
  set -a
  # shellcheck disable=SC1090
  . "$env_file"
  set +a
fi

reader_session="nblane-reader-api"
streamlit_session="nblane-streamlit-ui"
web_api_session="nblane-web-api"
if [[ "$mode" == "isolated" ]]; then
  reader_session="nblane-dev-reader-api"
  streamlit_session="nblane-dev-streamlit-ui"
  web_api_session="nblane-dev-web-api"
fi

dev_root="${root_arg:-${NBLANE_DEV_ROOT:-$repo_root/.dev-data}}"
asset_root="${asset_root_arg:-${NBLANE_DEV_ASSET_ROOT:-$repo_root/.dev-assets/research}}"
if [[ "$mode" == "local" ]]; then
  dev_root="${root_arg:-${NBLANE_ROOT:-$repo_root}}"
  asset_root="${asset_root_arg:-${NBLANE_RESEARCH_ASSET_ROOT:-$repo_root/.dev-assets/research}}"
fi

reader_base="http://127.0.0.1:${reader_port}"
streamlit_base="http://127.0.0.1:${streamlit_port}"
web_api_base="http://127.0.0.1:${web_api_port}"

spa_static_index="$repo_root/src/nblane/web_ui/static/index.html"

spa_build_hint() {
  if [[ ! -f "$spa_static_index" ]]; then
    echo "  hint: SPA static not built ($spa_static_index missing)."
    echo "        Build it:  (cd src/nblane/web_ui/frontend && npm install && npm run build)"
    echo "        Or dev it: npm run dev (vite on 5173, set VITE_API_PROXY_TARGET=${web_api_base})"
  fi
}

stop_sessions() {
  tmux kill-session -t "$reader_session" 2>/dev/null || true
  tmux kill-session -t "$streamlit_session" 2>/dev/null || true
  tmux kill-session -t "$web_api_session" 2>/dev/null || true
}

show_status() {
  tmux ls 2>/dev/null | grep -E "^(${reader_session}|${streamlit_session}|${web_api_session}):" || true
  echo
  echo "Streamlit:     ${streamlit_base}"
  echo "Reader API:    ${reader_base}"
  echo "Paper Library: ${reader_base}/paper-library?profile=${profile}"
  if [[ "$use_web_api" == "1" ]]; then
    echo "Web API (SPA): ${web_api_base}"
  fi
  echo
  echo "Health checks:"
  echo "  curl -i ${streamlit_base}/_stcore/health"
  echo "  curl -i '${reader_base}/paper-library?profile=${profile}'"
  if [[ "$use_web_api" == "1" ]]; then
    echo "  curl -i ${web_api_base}/api/v1/health"
    if command -v curl >/dev/null 2>&1; then
      if web_api_body="$(curl -fsS --max-time 2 "${web_api_base}/api/v1/health" 2>/dev/null)"; then
        echo "  Web API liveness: ok (${web_api_body})"
      else
        echo "  Web API liveness: unreachable at ${web_api_base}"
      fi
    fi
    spa_build_hint
  fi
}

if [[ "$command" == "stop" ]]; then
  stop_sessions
  echo "Stopped ${reader_session}, ${streamlit_session} and ${web_api_session}."
  exit 0
fi

if [[ "$command" == "status" ]]; then
  show_status
  exit 0
fi

# --- start-only prerequisites (stop/status above must work without them) ---
if [[ ! -x ".venv/bin/uvicorn" || ! -x ".venv/bin/streamlit" ]]; then
  echo "Missing .venv tools. Run: python3 -m venv .venv && .venv/bin/pip install -e ." >&2
  exit 1
fi
if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux is required for dev sessions. Install it (e.g. sudo apt install tmux) and retry." >&2
  exit 1
fi

if [[ "$mode" == "isolated" ]]; then
  mkdir -p "$dev_root/profiles" "$dev_root/schemas" "$dev_root/teams" "$asset_root"
  if [[ ! -d "$dev_root/profiles/template" ]]; then
    cp -a "$repo_root/profiles/template" "$dev_root/profiles/template"
  fi
  if [[ ! -d "$dev_root/schemas" || -z "$(find "$dev_root/schemas" -mindepth 1 -maxdepth 1 2>/dev/null)" ]]; then
    cp -a "$repo_root/schemas/." "$dev_root/schemas/"
    rm -rf "$dev_root/schemas/.learned"
  fi
  if [[ ! -d "$dev_root/teams" || -z "$(find "$dev_root/teams" -mindepth 1 -maxdepth 1 2>/dev/null)" ]]; then
    cp -a "$repo_root/teams/." "$dev_root/teams/"
  fi
  if [[ ! -d "$dev_root/profiles/$profile" ]]; then
    NBLANE_ROOT="$dev_root" PYTHONPATH=src .venv/bin/nblane init "$profile"
  fi
else
  mkdir -p "$asset_root"
fi

uvicorn_args="nblane.web_reader_api:app --host 127.0.0.1 --port ${reader_port}"
web_api_uvicorn_args="nblane.web_api:app --host 127.0.0.1 --port ${web_api_port}"
if [[ "$reload" == "1" ]]; then
  uvicorn_args="${uvicorn_args} --reload --reload-dir src"
  web_api_uvicorn_args="${web_api_uvicorn_args} --reload --reload-dir src"
fi

grobid_env=""
if [[ "$use_grobid" == "1" ]]; then
  grobid_env="NBLANE_GROBID_URL=http://127.0.0.1:${grobid_port} NBLANE_RESEARCH_PDF_BACKEND=grobid"
else
  grobid_env="NBLANE_RESEARCH_PDF_BACKEND=pymupdf"
fi

# Auth in dev is a SPA-backend (web-api) concern: the Reader/Streamlit
# sessions stay auth-less so their pages and e2e specs keep working, and
# isolated mode pins NBLANE_AUTH_FILE empty for them so a production value
# from the env file cannot leak into the sandbox. The web-api session gets
# the auth file from --auth-file / NBLANE_DEV_AUTH_FILE, or auto-detects
# <dev-root>/auth/users.yaml in isolated mode.
auth_env=""
if [[ "$mode" == "isolated" ]]; then
  auth_env="NBLANE_AUTH_FILE="
fi

web_api_auth_env="$auth_env"
web_api_auth_env_file=""
if [[ "$mode" == "isolated" && -z "$auth_file" && -f "$dev_root/auth/users.yaml" ]]; then
  auth_file="$dev_root/auth/users.yaml"
fi
if [[ -n "$auth_file" ]]; then
  if [[ ! -f "$auth_file" ]]; then
    echo "Auth file not found: $auth_file" >&2
    exit 1
  fi
  auth_file="$(cd "$(dirname "$auth_file")" && pwd)/$(basename "$auth_file")"
  web_api_auth_env="NBLANE_AUTH_FILE='$auth_file'"
  # core/auth requires NBLANE_READER_TOKEN_SECRET once auth is on (it keys the
  # HMAC session tokens the web-api mints at login). Keep it out of `ps` the
  # same way as the LLM keys: a 0600 env file the web-api session sources.
  web_api_auth_env_file="$(dirname "$auth_file")/dev-auth.env"
  if [[ ! -f "$web_api_auth_env_file" ]]; then
    (
      umask 077
      printf 'NBLANE_READER_TOKEN_SECRET=%s\n' \
        "$(.venv/bin/python -c 'import secrets; print(secrets.token_urlsafe(32))')" \
        > "$web_api_auth_env_file"
    )
  fi
fi

lang_env=""
if [[ "${UI_LANG:-}" == "en" || "${UI_LANG:-}" == "zh" ]]; then
  lang_env="UI_LANG=${UI_LANG}"
fi
if [[ "${LLM_REPLY_LANG:-}" == "en" || "${LLM_REPLY_LANG:-}" == "zh" ]]; then
  lang_env="${lang_env} LLM_REPLY_LANG=${LLM_REPLY_LANG}"
fi

# LLM credentials must never appear on the tmux command line (`ps` would show
# them). Each session sources the env file itself before starting the server;
# only non-sensitive settings stay on the command line. The explicit VAR=value
# prefixes below still override whatever the env file defines for this run.
env_load=""
if [[ -f "$env_file" ]]; then
  env_load="set -a; . '$env_file'; set +a;"
fi
web_api_env_load="$env_load"
if [[ -n "$web_api_auth_env_file" ]]; then
  web_api_env_load="${web_api_env_load} set -a; . '$web_api_auth_env_file'; set +a;"
fi

port_in_use() {
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    ss -ltnH 2>/dev/null | awk -v port="$port" '{split($4, parts, ":"); if (parts[length(parts)] == port) found=1} END {exit(found ? 0 : 1)}'
    return $?
  fi
  if command -v lsof >/dev/null 2>&1; then
    lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
    return $?
  fi
  return 1
}

port_owner() {
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    ss -ltnpH 2>/dev/null | awk -v port="$port" '{split($4, parts, ":"); if (parts[length(parts)] == port) print}' || true
  elif command -v lsof >/dev/null 2>&1; then
    lsof -nP -iTCP:"$port" -sTCP:LISTEN 2>/dev/null || true
  fi
}

wait_for_free_port() {
  # Briefly tolerate a just-stopped previous session releasing the port.
  local port="$1" attempt
  for ((attempt=0; attempt<10; attempt++)); do
    if ! port_in_use "$port"; then
      return 0
    fi
    sleep 0.3
  done
  return 1
}

stop_sessions

ports_to_check=("$reader_port" "$streamlit_port")
if [[ "$use_web_api" == "1" ]]; then
  ports_to_check+=("$web_api_port")
fi
for port in "${ports_to_check[@]}"; do
  if ! wait_for_free_port "$port"; then
    echo "Port ${port} is already in use:" >&2
    port_owner "$port" >&2
    echo "Stop that process first, or pick another port via --reader-port/--streamlit-port/--web-api-port." >&2
    exit 1
  fi
done

tmux new-session -d -s "$reader_session" -c "$repo_root" \
  "${env_load} \
   NBLANE_ROOT='$dev_root' \
   NBLANE_ENV_FILE='$env_file' \
   NBLANE_RESEARCH_ASSET_ROOT='$asset_root' \
   NBLANE_STREAMLIT_BASE_URL='$streamlit_base' \
   ${auth_env} ${grobid_env} ${lang_env} \
   PYTHONPATH=src .venv/bin/uvicorn ${uvicorn_args}"

tmux new-session -d -s "$streamlit_session" -c "$repo_root" \
  "${env_load} \
   NBLANE_ROOT='$dev_root' \
   NBLANE_ENV_FILE='$env_file' \
   NBLANE_READER_API_BASE='$reader_base' \
   NBLANE_DASHBOARD_CANVAS_BASE='$reader_base' \
   NBLANE_STREAMLIT_BASE_URL='$streamlit_base' \
   NBLANE_PAPER_LIBRARY_RUNTIME='$runtime' \
   NBLANE_RESEARCH_ASSET_ROOT='$asset_root' \
   ${auth_env} ${grobid_env} ${lang_env} \
   PYTHONPATH=src .venv/bin/streamlit run app.py \
     --server.address=127.0.0.1 --server.port=${streamlit_port} --server.headless=true"

if [[ "$use_web_api" == "1" ]]; then
  # Workshop iframe URL: /terminal/ only exists behind the production Caddy
  # proxy; locally there is no proxy, so default to the ttyd port directly.
  # Evaluated in the tmux shell AFTER the env file is sourced, so an explicit
  # NBLANE_WORKSHOP_URL there still wins.
  tmux new-session -d -s "$web_api_session" -c "$repo_root" \
    "${web_api_env_load} \
     NBLANE_ROOT='$dev_root' \
     NBLANE_ENV_FILE='$env_file' \
     NBLANE_READER_API_BASE='$reader_base' \
     NBLANE_WORKSHOP_URL=\"\${NBLANE_WORKSHOP_URL:-http://127.0.0.1:7668/}\" \
     ${web_api_auth_env} ${lang_env} \
     PYTHONPATH=src .venv/bin/uvicorn ${web_api_uvicorn_args}"
fi

if command -v curl >/dev/null 2>&1; then
  reader_health="${reader_base}/auth/session-ok"
  healthy="0"
  for ((attempt=0; attempt<20; attempt++)); do
    if curl -fsS -o /dev/null --max-time 2 "$reader_health" 2>/dev/null; then
      healthy="1"
      break
    fi
    sleep 0.5
  done
  if [[ "$healthy" != "1" ]]; then
    echo "Reader API did not come up at ${reader_health}." >&2
    echo "Inspect logs: tmux capture-pane -pt ${reader_session} -S -200" >&2
    exit 1
  fi
else
  echo "curl not found; skipping Reader API health check at ${reader_base}/auth/session-ok." >&2
fi

if [[ "$use_web_api" == "1" ]]; then
  if command -v curl >/dev/null 2>&1; then
    web_api_health="${web_api_base}/api/v1/health"
    web_api_healthy="0"
    for ((attempt=0; attempt<20; attempt++)); do
      if curl -fsS -o /dev/null --max-time 2 "$web_api_health" 2>/dev/null; then
        web_api_healthy="1"
        break
      fi
      sleep 0.5
    done
    if [[ "$web_api_healthy" != "1" ]]; then
      echo "Web API (SPA backend) did not come up at ${web_api_health}." >&2
      echo "Inspect logs: tmux capture-pane -pt ${web_api_session} -S -200" >&2
    fi
  else
    echo "curl not found; skipping Web API health check at ${web_api_base}/api/v1/health." >&2
  fi
fi

echo "Started ${mode} development Web UI."
echo "  root:        ${dev_root}"
echo "  assets:      ${asset_root}"
echo "  streamlit:   ${streamlit_base}"
echo "  reader API:  ${reader_base}"
if [[ "$use_web_api" == "1" ]]; then
  echo "  web API:     ${web_api_base} (SPA backend; serves web_ui/static when built)"
  if [[ -n "$auth_file" ]]; then
    echo "  web API auth: ON (${auth_file})"
  else
    echo "  web API auth: off"
  fi
  spa_build_hint
fi
if [[ "$reload" == "1" ]]; then
  echo "  uvicorn:     reload enabled for src/"
else
  echo "  uvicorn:     reload disabled"
fi
if [[ "$use_grobid" == "1" ]]; then
  echo "  grobid:      http://127.0.0.1:${grobid_port}"
fi
