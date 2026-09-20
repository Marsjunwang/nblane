"""Contract-snapshot test: committed openapi.json must match the live app.

The SPA frontend generates its API types (``src/api/schema.d.ts``) from the
committed snapshot ``src/nblane/web_ui/frontend/openapi.json`` (Immich-style
OpenAPI codegen, see docs/zh/architecture/frontend-spa-migration.md §2).
When a backend change alters the schema, regenerate the snapshot with
``scripts/dump-openapi.sh`` and re-run ``npm run gen:api`` in the frontend.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = REPO_ROOT / "src" / "nblane" / "web_ui" / "frontend" / "openapi.json"


def test_openapi_snapshot_matches_live_app() -> None:
    from nblane.web_api import app

    committed = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    live = json.loads(json.dumps(app.openapi(), sort_keys=True))
    assert live == committed, (
        "OpenAPI schema drifted from the committed snapshot. "
        "Run scripts/dump-openapi.sh, then `npm run gen:api` in "
        "src/nblane/web_ui/frontend."
    )
