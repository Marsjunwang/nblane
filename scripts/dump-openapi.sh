#!/usr/bin/env bash
# Dump the FastAPI OpenAPI schema to the committed contract snapshot consumed
# by `npm run gen:api` (openapi-typescript) in src/nblane/web_ui/frontend.
# Re-run after any change under src/nblane/web_api/ that alters the API surface;
# tests/test_web_api_openapi_snapshot.py fails CI when this file drifts.
set -euo pipefail
cd "$(dirname "$0")/.."
.venv/bin/python - <<'PY'
import json
from pathlib import Path

from nblane.web_api import app

out = Path("src/nblane/web_ui/frontend/openapi.json")
# sort_keys keeps the snapshot diff-stable for review and CI.
out.write_text(
    json.dumps(app.openapi(), ensure_ascii=False, indent=1, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(f"wrote {out}")
PY
