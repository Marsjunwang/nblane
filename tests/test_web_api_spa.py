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


@pytest.fixture()
def static_dir(tmp_path: Path) -> Path:
    """A minimal fake Vite build output: index.html + assets/app.js."""
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text(INDEX_HTML, encoding="utf-8")
    (tmp_path / "assets" / "app.js").write_text(APP_JS, encoding="utf-8")
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
    assert "static/index.html" in entries
    assert "static/assets/*" in entries


def test_default_static_dir_is_importable_package_data() -> None:
    # The committed build output must be reachable as package data of the
    # nblane.web_ui package (importlib.resources view of the same files).
    from importlib import resources

    web_ui_files = resources.files("nblane.web_ui")
    assert (web_ui_files / "static" / "index.html").is_file()
