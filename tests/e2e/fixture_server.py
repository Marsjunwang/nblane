"""Test-only server factories; never imported by production entry points."""

from __future__ import annotations

import json
import os
from pathlib import Path

from starlette.responses import JSONResponse


def _owned_app(kind: str):
    root = Path(os.environ["NBLANE_E2E_DATA_ROOT"]).resolve()
    marker = json.loads((root / ".nblane-e2e.json").read_text())
    if (
        marker["run_id"] != os.environ["NBLANE_E2E_RUN_ID"]
        or marker["root"] != str(root)
        or Path(os.environ["NBLANE_ROOT"]).resolve() != root
    ):
        raise RuntimeError("E2E data-root ownership mismatch")
    if kind == "spa":
        from nblane.web_api import app
    else:
        from nblane.web_reader_api import app

    @app.middleware("http")
    async def identify_fixture(request, call_next):
        if request.url.path == "/__nblane_e2e__/identity":
            return JSONResponse(marker)
        return await call_next(request)

    return app


def spa():
    return _owned_app("spa")


def reader():
    return _owned_app("reader")
