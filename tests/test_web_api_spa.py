"""Tests for serving the built SPA from the FastAPI app (nblane.web_api.spa)."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import nblane
from nblane.web_api import create_app
from nblane.web_api.spa import DEFAULT_STATIC_DIR

INDEX_HTML = "<!doctype html><html><body><div id=\"root\"></div></body></html>"
APP_JS = "console.log('app');\n"
MANIFEST = '{"name":"大佬之路","start_url":"/","scope":"/"}'
PNG_BYTES = b"\x89PNG\r\n\x1a\n"
SERVICE_WORKER = "self.addEventListener('fetch', () => {});\n"
OFFLINE_HTML = "<!doctype html><html><body>当前处于离线状态</body></html>"
ICON_NAMES = ("icon-192.png", "icon-512.png", "icon-maskable-512.png")


@pytest.fixture()
def static_dir(tmp_path: Path) -> Path:
    """A minimal fake Vite build output with the PWA static shell."""
    (tmp_path / "assets").mkdir()
    (tmp_path / "icons").mkdir()
    (tmp_path / "index.html").write_text(INDEX_HTML, encoding="utf-8")
    (tmp_path / "assets" / "app.js").write_text(APP_JS, encoding="utf-8")
    (tmp_path / "manifest.webmanifest").write_text(MANIFEST, encoding="utf-8")
    (tmp_path / "offline.html").write_text(OFFLINE_HTML, encoding="utf-8")
    (tmp_path / "sw.js").write_text(SERVICE_WORKER, encoding="utf-8")
    for icon_name in ICON_NAMES:
        (tmp_path / "icons" / icon_name).write_bytes(PNG_BYTES)
    return tmp_path


@pytest.fixture()
def client(static_dir: Path) -> TestClient:
    return TestClient(create_app(spa_static_dir=static_dir))


def test_root_serves_index_html(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.text == INDEX_HTML
    assert response.headers["Cache-Control"] == "no-cache"


def test_client_route_falls_back_to_index_html(client: TestClient) -> None:
    response = client.get("/p/alice/kanban")
    assert response.status_code == 200
    assert response.text == INDEX_HTML
    assert response.headers["Cache-Control"] == "no-cache"


def test_hashed_asset_served_with_immutable_cache(client: TestClient) -> None:
    response = client.get("/assets/app.js")
    assert response.status_code == 200
    assert response.text == APP_JS
    assert (
        response.headers["Cache-Control"]
        == "public, max-age=31536000, immutable"
    )


def test_manifest_served_with_json_mime_and_no_cache(client: TestClient) -> None:
    response = client.get("/manifest.webmanifest")
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/manifest+json")
    assert response.headers["Cache-Control"] == "no-cache"
    assert response.text == MANIFEST


@pytest.mark.parametrize("icon_name", ICON_NAMES)
def test_pwa_icons_served_with_png_mime_and_no_cache(
    client: TestClient, icon_name: str
) -> None:
    response = client.get(f"/icons/{icon_name}")
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("image/png")
    assert response.headers["Cache-Control"] == "no-cache"
    assert response.content == PNG_BYTES


@pytest.mark.parametrize(
    ("path", "media_type", "body"),
    [
        ("/sw.js", "text/javascript", SERVICE_WORKER),
        ("/offline.html", "text/html", OFFLINE_HTML),
    ],
)
def test_pwa_shell_files_served_with_no_cache(
    client: TestClient, path: str, media_type: str, body: str
) -> None:
    response = client.get(path)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(media_type)
    assert response.headers["Cache-Control"] == "no-cache"
    assert response.text == body


def test_missing_assetlinks_returns_json_404_not_spa_html(client: TestClient) -> None:
    response = client.get("/.well-known/assetlinks.json")
    assert response.status_code == 404
    assert response.headers["Content-Type"].startswith("application/json")
    assert response.json() == {"detail": "Not Found"}
    assert response.text != INDEX_HTML


def test_existing_assetlinks_uses_normal_static_file_response(
    client: TestClient, static_dir: Path
) -> None:
    well_known = static_dir / ".well-known"
    well_known.mkdir()
    assetlinks = '[{"relation":["delegate_permission/common.handle_all_urls"]}]'
    (well_known / "assetlinks.json").write_text(assetlinks, encoding="utf-8")

    response = client.get("/.well-known/assetlinks.json")
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/json")
    assert response.headers["Cache-Control"] == "no-cache"
    assert response.text == assetlinks


def test_api_health_still_json(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/json")
    assert response.json()["ok"] is True


def test_unknown_api_path_404s_not_index_html(client: TestClient) -> None:
    response = client.get("/api/v1/nonexistent")
    assert response.status_code == 404
    assert response.headers["Content-Type"].startswith("application/json")
    assert response.text != INDEX_HTML


def test_post_to_client_route_does_not_hit_spa_fallback(
    client: TestClient,
) -> None:
    # The SPA fallback is GET-only; a POST to a client route must not
    # return index.html.
    response = client.post("/p/alice/kanban")
    assert response.status_code in (404, 405)
    assert response.text != INDEX_HTML


def test_missing_static_dir_serves_build_note(tmp_path: Path) -> None:
    missing = tmp_path / "no-such-static-dir"
    client = TestClient(create_app(spa_static_dir=missing))
    response = client.get("/")
    assert response.status_code == 503
    assert "npm run build" in response.json()["detail"]
    # API still works when the SPA is not built.
    assert client.get("/api/v1/health").status_code == 200


def test_default_static_dir_lives_inside_the_package() -> None:
    # mount_spa locates the SPA payload relative to the installed package,
    # so the same path works from an editable checkout and a wheel install.
    expected = Path(nblane.__file__).resolve().parent / "web_ui" / "static"
    assert DEFAULT_STATIC_DIR == expected


def test_spa_static_payload_declared_as_package_data() -> None:
    # Wheels only ship the SPA if pyproject declares web_ui/static as
    # package data for the nblane.web_ui package.
    pyproject = Path(nblane.__file__).resolve().parents[2] / "pyproject.toml"
    if not pyproject.is_file():
        pytest.skip("pyproject.toml not available (installed test tree)")
    package_data = tomllib.loads(pyproject.read_text(encoding="utf-8"))[
        "tool"
    ]["setuptools"]["package-data"]
    entries = package_data.get("nblane.web_ui", [])
    expected_entries = {
        "static/index.html",
        "static/manifest.webmanifest",
        "static/offline.html",
        "static/sw.js",
        "static/icons/*.png",
        "static/.well-known/*",
        "static/assets/*",
    }
    assert expected_entries <= set(entries)


def test_default_static_dir_is_importable_package_data() -> None:
    # The committed build output must be reachable as package data of the
    # nblane.web_ui package (importlib.resources view of the same files).
    from importlib import resources

    web_ui_files = resources.files("nblane.web_ui")
    relative_paths = (
        "static/index.html",
        "static/manifest.webmanifest",
        "static/offline.html",
        "static/sw.js",
        "static/.well-known/assetlinks.json",
        "static/assets/.gitattributes",
        *(f"static/icons/{icon_name}" for icon_name in ICON_NAMES),
    )
    for relative_path in relative_paths:
        assert (web_ui_files / relative_path).is_file(), relative_path
