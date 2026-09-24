"""Tests for scripts/openclaw/skills/bin/nblane_api.py (openclaw API client).

All HTTP is faked with httpx.MockTransport; no network, no real /srv data.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import httpx
import pytest

MODULE_PATH = (
    Path(__file__).resolve().parent.parent
    / "scripts" / "openclaw" / "skills" / "bin" / "nblane_api.py"
)
spec = importlib.util.spec_from_file_location("nblane_api", MODULE_PATH)
nblane_api = importlib.util.module_from_spec(spec)
sys.modules.setdefault("nblane_api", nblane_api)
spec.loader.exec_module(nblane_api)

PASSWORD = "s3cret-test-password"
COOKIE = "nblane_auth_session"


class FakeServer:
    """Stateful fake of the /api/v1 surface the client exercises."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.logged_in = False
        self.login_calls = 0
        self.fail_logins = 0
        self.etag = 'W/"v1"'
        self.precondition_failures = 0
        self.unauthorized_reads = 0

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path = request.url.path
        authed = bool(request.headers.get("cookie")) and self.logged_in
        if path == "/api/v1/auth/login":
            self.login_calls += 1
            if self.fail_logins:
                self.fail_logins -= 1
                return httpx.Response(401, json={"detail": "Invalid credentials"})
            body = json.loads(request.content)
            assert body["username"] == "openclaw"
            assert body["password"] == PASSWORD
            self.logged_in = True
            return httpx.Response(
                200,
                json={"id": "openclaw", "role": "member", "profiles": ["王军"]},
                headers={"set-cookie": f"{COOKIE}=token-{self.login_calls}; Path=/; HttpOnly"},
            )
        if not authed:
            self.unauthorized_reads += 1
            return httpx.Response(401, json={"detail": "Authentication required"})
        if request.method == "POST" and self.precondition_failures:
            self.precondition_failures -= 1
            self.etag = f'W/"v{self.login_calls + 9}"'
            return httpx.Response(
                412,
                json={"code": "etag_mismatch", "message": "changed since loaded"},
                headers={"ETag": self.etag} if self.send_etag_on_412 else {},
            )
        if request.method == "GET":
            return httpx.Response(
                200, json={"ok": True, "path": path}, headers={"ETag": self.etag}
            )
        return httpx.Response(201, json={"created": True}, headers={"ETag": 'W/"v2"'})

    send_etag_on_412 = True

    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self.handler)


@pytest.fixture
def server():
    return FakeServer()


@pytest.fixture
def session(server, tmp_path):
    return nblane_api.Session(
        "http://127.0.0.1:8504",
        password=PASSWORD,
        jar_path=tmp_path / "api-cookies.json",
        transport=server.transport(),
    )


@pytest.fixture
def authed(session):
    """Session with a completed login, so tests start from an authed wire."""
    session.login()
    return session


def test_login_writes_cookie_jar(session, server, tmp_path):
    user = session.login()
    assert user["id"] == "openclaw"
    jar = tmp_path / "api-cookies.json"
    data = json.loads(jar.read_text())
    assert data["base_url"] == "http://127.0.0.1:8504"
    assert data["cookies"][COOKIE].startswith("token-")
    assert jar.stat().st_mode & 0o777 == 0o600
    # A second request reuses the cached cookie without another login.
    other = nblane_api.Session(
        "http://127.0.0.1:8504",
        password=PASSWORD,
        jar_path=jar,
        transport=server.transport(),
    )
    assert other.get("/profiles/x/starmap").status_code == 200
    assert server.login_calls == 1


def test_401_triggers_one_relogin_and_retry(session, server, tmp_path):
    assert server.logged_in is False  # jar empty: first read will 401
    response = session.get("/profiles/x/starmap")
    assert response.status_code == 200
    assert server.login_calls == 1
    assert server.unauthorized_reads == 1
    # Exactly one retry: the original request ran twice in total.
    reads = [r for r in server.requests if r.url.path.endswith("/starmap")]
    assert len(reads) == 2


def test_412_refetches_etag_and_retries_once(authed, server):
    server.precondition_failures = 1
    response = authed.mutation("/profiles/x/checkins", {"habit": "锻炼"})
    assert response.status_code == 201
    posts = [r for r in server.requests if r.method == "POST"
             and r.url.path.endswith("/checkins")]
    assert len(posts) == 2
    # First POST carries no If-Match; the retry carries the fresh ETag.
    assert "if-match" not in {k.lower() for k in posts[0].headers.keys()}
    assert posts[1].headers["If-Match"] == server.etag


def test_412_without_header_falls_back_to_reget(authed, server):
    server.precondition_failures = 1
    server.send_etag_on_412 = False
    response = authed.mutation("/profiles/x/checkins", {"habit": "锻炼"})
    assert response.status_code == 201
    paths = [(r.method, r.url.path) for r in server.requests
             if not r.url.path.endswith("/auth/login")]
    # POST (412) -> GET same path for the ETag -> POST retry with If-Match.
    assert paths == [
        ("POST", "/api/v1/profiles/x/checkins"),
        ("GET", "/api/v1/profiles/x/checkins"),
        ("POST", "/api/v1/profiles/x/checkins"),
    ]


def test_persistent_412_fails(authed, server):
    server.precondition_failures = 5
    with pytest.raises(nblane_api.ApiFailure, match="persists"):
        authed.mutation("/profiles/x/checkins", {"habit": "锻炼"})
    posts = [r for r in server.requests if r.method == "POST"
             and r.url.path.endswith("/checkins")]
    assert len(posts) == 2  # retry exactly once, never a third attempt


def test_delete_discard_hard_refused_without_http(session, server):
    for path in (
        "/profiles/x/inbox/E1/discard",
        "/profiles/x/habits/h1/delete",
    ):
        with pytest.raises(nblane_api.ApiFailure, match="page-confirmation"):
            nblane_api.normalize_path(path)
    with pytest.raises(nblane_api.ApiFailure, match=r"\.\."):
        nblane_api.normalize_path("/profiles/x/checkins/c1/../discard")
    assert server.requests == []  # nothing reached the wire
    # There is no delete subcommand at all.
    parser = nblane_api.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["delete", "/profiles/x/checkins/c1"])


def test_password_never_logged(session, server, capsys, tmp_path):
    server.fail_logins = 2
    with pytest.raises(nblane_api.ApiFailure):
        session.login()
    assert not (tmp_path / "api-cookies.json").exists()
    code = nblane_api.main(["login"], session=session)
    captured = capsys.readouterr()
    assert code != 0
    assert PASSWORD not in captured.err
    assert PASSWORD not in captured.out
    # The login request itself is the only place the password appears.
    logins = [r for r in server.requests if r.url.path.endswith("/auth/login")]
    assert all(PASSWORD in r.content.decode() for r in logins)


def test_missing_password_env_errors_cleanly(server, tmp_path, monkeypatch, capsys):
    monkeypatch.delenv(nblane_api.PASSWORD_ENV, raising=False)
    session = nblane_api.Session(
        "http://127.0.0.1:8504",
        jar_path=tmp_path / "api-cookies.json",
        transport=server.transport(),
    )
    code = nblane_api.main(["login"], session=session)
    captured = capsys.readouterr()
    assert code == 2
    assert nblane_api.PASSWORD_ENV in captured.err
    assert server.login_calls == 0


def test_semantic_commands_hit_expected_routes(authed, server):
    run = nblane_api.run
    ns = nblane_api.build_parser().parse_args
    assert run(ns(["starmap"]), authed).json()["path"].endswith("/profiles/王军/starmap")
    assert run(ns(["board"]), authed).json()["path"].endswith("/projects-board")
    assert run(ns(["health"]), authed).json()["path"].endswith("/health")
    run(ns(["chronicle"]), authed)
    assert "limit=40" in str(server.requests[-1].url)
    assert run(ns(["activity", "--status", "all"]), authed).status_code == 200
    assert run(ns(["checkin", "锻炼", "--note", "微信打卡"]), authed).status_code == 201
    checkin = [r for r in server.requests if r.url.path.endswith("/checkins")][-1]
    assert json.loads(checkin.content) == {"habit": "锻炼", "note": "微信打卡"}
    assert run(ns(["divine", "--mode", "serious", "--question", "Q"]), authed).status_code == 201
    divine = [r for r in server.requests if r.url.path.endswith("/divination")][-1]
    assert json.loads(divine.content) == {"mode": "serious", "question": "Q"}


def test_path_normalization():
    assert nblane_api.normalize_path("/api/v1/health") == "/health"
    assert nblane_api.normalize_path("/health") == "/health"
    with pytest.raises(nblane_api.ApiFailure):
        nblane_api.normalize_path("http://evil.example/health")
    with pytest.raises(nblane_api.ApiFailure):
        nblane_api.normalize_path("health")
