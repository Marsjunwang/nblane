#!/usr/bin/env bash
# First install: create .venv, install nblane, then run the setup wizard.
# Safe to re-run; an existing .venv is reused. Extra arguments go to
# `nblane setup` (e.g. scripts/install.sh --yes --profile alice --llm skip).
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

python_bin="${PYTHON:-}"
if [[ -z "$python_bin" ]]; then
  for candidate in python3.13 python3.12 python3.11 python3; do
    if command -v "$candidate" >/dev/null 2>&1 &&
      "$candidate" -c 'import sys; sys.exit(sys.version_info < (3, 11))' 2>/dev/null; then
      python_bin="$candidate"
      break
    fi
  done
fi
if [[ -z "$python_bin" ]]; then
  echo "需要 Python ≥ 3.11（可用 PYTHON=/path/to/python 指定）。" >&2
  exit 1
fi
if ! command -v git >/dev/null 2>&1; then
  echo "需要 Git：apt install git / brew install git" >&2
  exit 1
fi

if [[ ! -x .venv/bin/python ]]; then
  echo "== 创建 .venv（$("$python_bin" --version)）"
  if ! "$python_bin" -m venv .venv; then
    echo "创建虚拟环境失败；Debian/Ubuntu 上先装 python3-venv。" >&2
    exit 1
  fi
fi

echo "== 安装 nblane 和依赖"
.venv/bin/python -m pip install --quiet --upgrade pip
.venv/bin/python -m pip install --quiet -e .

echo "== 设置向导"
exec .venv/bin/nblane setup "$@"
