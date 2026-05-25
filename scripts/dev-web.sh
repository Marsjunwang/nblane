#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

mode="local"
command="start"
reload="0"
profile="${NBLANE_DEV_PROFILE:-dev}"
reader_port="${NBLANE_DEV_READER_PORT:-8502}"
streamlit_port="${NBLANE_DEV_STREAMLIT_PORT:-8503}"
grobid_port="${NBLANE_DEV_GROBID_PORT:-18070}"
use_grobid="0"
runtime="${NBLANE_PAPER_LIBRARY_RUNTIME:-fastapi_iframe}"
env_file="${NBLANE_DEV_ENV_FILE:-$repo_root/.env}"
root_arg=""
asset_root_arg=""

usage() {
  cat <<'EOF'
Usage: scripts/dev-web.sh [start|stop|status] [options]

Starts the development Streamlit UI and FastAPI Reader sidecar in tmux.

Commands:
  start              Start or restart dev tmux sessions. This is the default.
  stop               Stop dev tmux sessions.
  status             Show tmux sessions and health-check URLs.

Options:
  --isolated         Use isolated dev ports and data:
                     18502 / 18503, .dev-data, .dev-assets.
  --reload           Start uvicorn with --reload --reload-dir src.
  --no-reload        Start uvicorn without reload. This is the default.
  --reader-port N    Reader sidecar port. Default: 8502, or 18502 with --isolated.
  --streamlit-port N Streamlit port. Default: 8503, or 18503 with --isolated.
  --profile NAME     Profile to create when --isolated data is first prepared.
                     Default: dev.
  --root PATH        NBLANE_ROOT for this dev run.
  --asset-root PATH  NBLANE_RESEARCH_ASSET_ROOT for this dev run.
  --runtime VALUE    Paper Library runtime: fastapi_iframe, fastapi_link,
                     or streamlit_component. Default: fastapi_iframe.
  --grobid           Point dev extraction at http://127.0.0.1:<grobid-port>.
  --grobid-port N    Host port for a dev GROBID container. Default: 18070.
  --env-file PATH    Source this shell-style env file before starting.

Examples:
  scripts/dev-web.sh
  scripts/dev-web.sh --reload
  scripts/dev-web.sh --isolated --reload
  scripts/dev-web.sh --isolated --grobid
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
      if [[ "${NBLANE_DEV_READER_PORT:-}" == "" ]]; then
        reader_port="18502"
      fi
      if [[ "${NBLANE_DEV_STREAMLIT_PORT:-}" == "" ]]; then
        streamlit_port="18503"
      fi
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

if [[ ! -x ".venv/bin/uvicorn" || ! -x ".venv/bin/streamlit" ]]; then
  echo "Missing .venv tools. Run: python3 -m venv .venv && .venv/bin/pip install -e ." >&2
  exit 1
fi

if [[ "$command" == "start" && -f "$env_file" ]]; then
  set -a
  # shellcheck disable=SC1090
  . "$env_file"
  set +a
fi

reader_session="nblane-reader-api"
streamlit_session="nblane-streamlit-ui"
if [[ "$mode" == "isolated" ]]; then
  reader_session="nblane-dev-reader-api"
  streamlit_session="nblane-dev-streamlit-ui"
fi

dev_root="${root_arg:-${NBLANE_DEV_ROOT:-$repo_root/.dev-data}}"
asset_root="${asset_root_arg:-${NBLANE_DEV_ASSET_ROOT:-$repo_root/.dev-assets/research}}"
if [[ "$mode" == "local" ]]; then
  dev_root="${root_arg:-${NBLANE_ROOT:-$repo_root}}"
  asset_root="${asset_root_arg:-${NBLANE_RESEARCH_ASSET_ROOT:-$repo_root/.dev-assets/research}}"
fi

reader_base="http://127.0.0.1:${reader_port}"
streamlit_base="http://127.0.0.1:${streamlit_port}"

stop_sessions() {
  tmux kill-session -t "$reader_session" 2>/dev/null || true
  tmux kill-session -t "$streamlit_session" 2>/dev/null || true
}

show_status() {
  tmux ls 2>/dev/null | grep -E "^(${reader_session}|${streamlit_session}):" || true
  echo
  echo "Streamlit:     ${streamlit_base}"
  echo "Reader API:    ${reader_base}"
  echo "Paper Library: ${reader_base}/paper-library?profile=${profile}"
  echo
  echo "Health checks:"
  echo "  curl -i ${streamlit_base}/_stcore/health"
  echo "  curl -i '${reader_base}/paper-library?profile=${profile}'"
}

if [[ "$command" == "stop" ]]; then
  stop_sessions
  echo "Stopped ${reader_session} and ${streamlit_session}."
  exit 0
fi

if [[ "$command" == "status" ]]; then
  show_status
  exit 0
fi

if [[ "$mode" == "isolated" ]]; then
  mkdir -p "$dev_root/profiles" "$dev_root/schemas" "$dev_root/teams" "$asset_root"
  if [[ ! -d "$dev_root/profiles/template" ]]; then
    cp -a "$repo_root/profiles/template" "$dev_root/profiles/template"
  fi
  if [[ ! -d "$dev_root/schemas" || -z "$(find "$dev_root/schemas" -mindepth 1 -maxdepth 1 2>/dev/null)" ]]; then
    cp -a "$repo_root/schemas/." "$dev_root/schemas/"
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
if [[ "$reload" == "1" ]]; then
  uvicorn_args="${uvicorn_args} --reload --reload-dir src"
fi

grobid_env=""
if [[ "$use_grobid" == "1" ]]; then
  grobid_env="NBLANE_GROBID_URL=http://127.0.0.1:${grobid_port} NBLANE_RESEARCH_STRUCTURE_BACKEND=grobid"
else
  grobid_env="NBLANE_GROBID_URL= NBLANE_RESEARCH_STRUCTURE_BACKEND=pymupdf"
fi

auth_env=""
if [[ "$mode" == "isolated" && "${NBLANE_DEV_AUTH_FILE:-}" == "" ]]; then
  auth_env="NBLANE_AUTH_FILE="
fi

lang_env=""
if [[ "${UI_LANG:-}" == "en" || "${UI_LANG:-}" == "zh" ]]; then
  lang_env="UI_LANG=${UI_LANG}"
fi
if [[ "${LLM_REPLY_LANG:-}" == "en" || "${LLM_REPLY_LANG:-}" == "zh" ]]; then
  lang_env="${lang_env} LLM_REPLY_LANG=${LLM_REPLY_LANG}"
fi

stop_sessions

tmux new-session -d -s "$reader_session" -c "$repo_root" \
  "NBLANE_ROOT='$dev_root' \
   NBLANE_RESEARCH_ASSET_ROOT='$asset_root' \
   NBLANE_STREAMLIT_BASE_URL='$streamlit_base' \
   ${auth_env} ${grobid_env} ${lang_env} \
   PYTHONPATH=src .venv/bin/uvicorn ${uvicorn_args}"

tmux new-session -d -s "$streamlit_session" -c "$repo_root" \
  "NBLANE_ROOT='$dev_root' \
   NBLANE_READER_API_BASE='$reader_base' \
   NBLANE_DASHBOARD_CANVAS_BASE='$reader_base' \
   NBLANE_STREAMLIT_BASE_URL='$streamlit_base' \
   NBLANE_PAPER_LIBRARY_RUNTIME='$runtime' \
   NBLANE_RESEARCH_ASSET_ROOT='$asset_root' \
   ${auth_env} ${grobid_env} ${lang_env} \
   PYTHONPATH=src .venv/bin/streamlit run app.py \
     --server.address=127.0.0.1 --server.port=${streamlit_port} --server.headless=true"

echo "Started ${mode} development Web UI."
echo "  root:        ${dev_root}"
echo "  assets:      ${asset_root}"
echo "  streamlit:   ${streamlit_base}"
echo "  reader API:  ${reader_base}"
if [[ "$reload" == "1" ]]; then
  echo "  uvicorn:     reload enabled for src/"
else
  echo "  uvicorn:     reload disabled"
fi
if [[ "$use_grobid" == "1" ]]; then
  echo "  grobid:      http://127.0.0.1:${grobid_port}"
fi
