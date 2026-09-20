#!/usr/bin/env bash
# install.sh — install the repo-provided OpenClaw assets (skills + weixin-task-bridge
# plugin) into the local OpenClaw workspace. Idempotent: safe to re-run.
#
# Usage:
#   scripts/openclaw/install.sh            # perform the install
#   scripts/openclaw/install.sh --dry-run  # print actions without executing
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="${SCRIPT_DIR}/skills/"
PLUGIN_DIR="${SCRIPT_DIR}/plugins/weixin-task-bridge"
OPENCLAW_WORKSPACE="${OPENCLAW_WORKSPACE:-${HOME}/.openclaw/workspace}"
SKILLS_DST="${OPENCLAW_WORKSPACE}/skills/"

DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    -h|--help)
      echo "Usage: $0 [--dry-run]"
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      echo "Usage: $0 [--dry-run]" >&2
      exit 2
      ;;
  esac
done

run() {
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "[dry-run] $*"
  else
    "$@"
  fi
}

echo "==> Syncing skills: ${SKILLS_SRC} -> ${SKILLS_DST}"
run rsync -a --exclude='__pycache__' "${SKILLS_SRC}" "${SKILLS_DST}"

echo "==> Installing plugin: ${PLUGIN_DIR}"
run openclaw plugins install "${PLUGIN_DIR}" --force --accept-capabilities

echo ""
echo "Done. Verify with:"
echo "  openclaw plugins inspect weixin-task-bridge --runtime --json"
