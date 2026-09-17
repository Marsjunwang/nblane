#!/usr/bin/env bash
# Shared entrypoint. Python passes task text as data, never shell source.
set -eu
exec python3 "$(dirname -- "${BASH_SOURCE[0]}")/dev_delegate.py" "$@"
