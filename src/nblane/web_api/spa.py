"""Serve the built SPA (``web_ui/static``) from the FastAPI app.

One uvicorn process serves both the JSON API (``/api/v1``) and the React
SPA. The SPA uses client-side routing (React Router ``BrowserRouter``), so
unknown non-API GET paths fall back to ``index.html``.

Caching policy:

- ``/assets/*`` — Vite emits content-hashed filenames, so they get
  ``Cache-Control: public, max-age=31536000, immutable``.
- ``index.html`` and any other file at the static root — ``no-cache`` so
  new deploys are picked up immediately.

Auth: the SPA HTML/JS/CSS is **not secret** (it ships to every browser
anyway), so static files and the ``index.html`` fallback are intentionally
left open — no ``require_user`` dependency. The API stays protected
per-route; the login page itself is a client route (``/login``) served by
this same fallback.

When the static dir is missing (frontend not built), a single ``GET /``
route is registered returning **503** with a build hint; all other paths
behave as before (API routes work, everything else 404s).
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Response
from fastapi.responses import FileResponse, JSONResponse

DEFAULT_STATIC_DIR = Path(__file__).resolve().parent.parent / "web_ui" / "static"

_IMMUTABLE_CACHE = "public, max-age=31536000, immutable"
_NO_CACHE = "no-cache"

_NOT_BUILT_NOTE = "SPA not built; run npm run build in src/nblane/web_ui/frontend"


def _file_response(path: Path, *, immutable: bool) -> FileResponse:
    response = FileResponse(path)
    response.headers["Cache-Control"] = _IMMUTABLE_CACHE if immutable else _NO_CACHE
    return response


def mount_spa(app: FastAPI, static_dir: Path | None = None) -> None:
    """Mount SPA static files + client-route fallback onto ``app``.

    ``static_dir`` defaults to ``web_ui/static`` next to this package. Must
    be called **after** all API routers are included so existing routes win
    over the catch-all.
    """
    static_dir = Path(static_dir) if static_dir is not None else DEFAULT_STATIC_DIR
    index_html = static_dir / "index.html"

    if not index_html.is_file():

        @app.get("/", include_in_schema=False)
        def spa_not_built() -> JSONResponse:
            # 503: the API is up, the UI payload is just not deployed yet.
            return JSONResponse({"detail": _NOT_BUILT_NOTE}, status_code=503)

        return

    static_root = static_dir.resolve()

    def _resolve(full_path: str) -> Path | None:
        """Return the file under ``static_root`` for ``full_path``, or None."""
        candidate = (static_root / full_path).resolve()
        if not candidate.is_file() or not candidate.is_relative_to(static_root):
            return None
        return candidate

    @app.get("/", include_in_schema=False)
    def spa_index() -> FileResponse:
        return _file_response(index_html, immutable=False)

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str) -> Response:
        if full_path == "api" or full_path.startswith("api/"):
            # API paths must 404 from the API surface, never as index.html.
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        asset = _resolve(full_path)
        if asset is not None:
            immutable = asset.is_relative_to(static_root / "assets")
            return _file_response(asset, immutable=immutable)
        # Client-side route (e.g. /p/alice/kanban): hand over to the SPA.
        return _file_response(index_html, immutable=False)
