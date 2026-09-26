#!/usr/bin/env python3
"""nblane HTTP API CLI client for openclaw automation (production-launch-plan §3.1).

Talks to the FastAPI backend (default http://127.0.0.1:8504, prefix /api/v1)
as the ``openclaw`` service account. The session cookie (TTL 12h) is cached in
a per-user jar; on 401 the client re-logs in once and retries. Mutations
follow the SPA's postEtagMutation discipline: the first POST carries no
If-Match; on 412 the fresh ETag is taken from the 412 response header (the
server always sets it) or, failing that, by re-GETting the resource, and the
POST is retried exactly once with If-Match.

Tiered-authorization contract (plan §3.3): delete-class actions are
page-confirmation tier and are hard-refused here. There is deliberately no
``delete`` subcommand, and the generic get/post escape hatches reject any
path carrying a delete/discard segment (e.g. inbox discard is a POST, so
method filtering alone is not enough). Deletions stay in the SPA where a
human confirms them — habit-plan deletion included (DELETE habit-plans is
never issued from this client).

Habit-plan creation has no dedicated subcommand either (the body shape is
too complex for flags); use the escape hatch instead:
``post /profiles/<p>/habit-plans '<json>'``.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from urllib.parse import quote

import httpx

API_PREFIX = "/api/v1"
DEFAULT_BASE_URL = "http://127.0.0.1:8504"
DEFAULT_USERNAME = "openclaw"
DEFAULT_PROFILE = "王军"
BASE_URL_ENV = "NBLANE_API_BASE"
USERNAME_ENV = "NBLANE_OPENCLAW_API_USERNAME"
PASSWORD_ENV = "NBLANE_OPENCLAW_API_PASSWORD"
PROFILE_ENV = "NBLANE_API_PROFILE"
COOKIE_JAR_ENV = "NBLANE_API_COOKIE_JAR"

# Delete/discard-class route segments refused by the escape hatches. This is
# the client-side half of the tiered-authorization contract: conversation-tier
# automation never deletes; the page tier (SPA) owns deletion with human
# confirmation.
FORBIDDEN_SEGMENTS = {"delete", "discard", "del"}


class ApiFailure(Exception):
    """Fatal client error; the message is printed to stderr, exit non-zero."""


def cookie_jar_path() -> Path:
    override = os.environ.get(COOKIE_JAR_ENV, "").strip()
    if override:
        return Path(override).expanduser()
    cache_home = os.environ.get("XDG_CACHE_HOME", "").strip()
    root = Path(cache_home).expanduser() if cache_home else Path.home() / ".cache"
    return root / "nblane" / "api-cookies.json"


def _read_password() -> str:
    """Service-account password: env first, then ~/.config/nblane/api.env.

    The file fallback exists because automation sandboxes do not always
    inherit the gateway process environment (2026-09-26 incident: the
    morning-report cron saw an expired cookie and no password env).
    Format: KEY=VALUE lines, ``#`` comments; file should be chmod 0600.
    """
    env_value = os.environ.get(PASSWORD_ENV, "").strip()
    if env_value:
        return env_value
    config_home = os.environ.get("XDG_CONFIG_HOME", "").strip()
    root = Path(config_home).expanduser() if config_home else Path.home() / ".config"
    try:
        for line in (root / "nblane" / "api.env").read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            if key.strip() == PASSWORD_ENV:
                return value.strip().strip('"').strip("'")
    except OSError:
        pass
    return ""


def load_cookies(path: Path, base_url: str) -> dict[str, str]:
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict) or data.get("base_url") != base_url:
        return {}
    cookies = data.get("cookies")
    if not isinstance(cookies, dict):
        return {}
    return {str(name): str(value) for name, value in cookies.items()}


def save_cookies(path: Path, base_url: str, cookies: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    payload = {"base_url": base_url, "cookies": cookies}
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    temporary.chmod(0o600)
    temporary.replace(path)


def error_message(response: httpx.Response) -> str:
    """Best-effort server error text: {code, message} or FastAPI {detail}."""
    try:
        body = response.json()
    except ValueError:
        return response.text.strip()[:200]
    if isinstance(body, dict):
        for key in ("message", "detail"):
            value = body.get(key)
            if isinstance(value, str) and value.strip():
                return value
            if value is not None:
                return json.dumps(value, ensure_ascii=False)
    return f"HTTP {response.status_code}"


def normalize_path(path: str) -> str:
    """Validate a user-supplied API path and strip an optional /api/v1 prefix."""
    path = path.strip()
    if "://" in path:
        raise ApiFailure("pass an API path (e.g. /profiles/<name>/starmap), not a URL")
    if path.startswith(API_PREFIX):
        path = path[len(API_PREFIX):]
    if not path.startswith("/"):
        raise ApiFailure(f"API path must start with '/': {path!r}")
    target = path.split("?", 1)[0]
    if ".." in target.split("/"):
        raise ApiFailure(f"API path must not contain '..': {path!r}")
    lowered = {segment.lower() for segment in target.split("/")}
    denied = lowered & FORBIDDEN_SEGMENTS
    if denied:
        raise ApiFailure(
            f"refused: {sorted(denied)[0]!r} is a delete-class action "
            "(page-confirmation tier); open the SPA to perform it"
        )
    return path


class Session:
    """httpx wrapper: cookie persistence, one 401 re-login, ETag mutation retry."""

    def __init__(
        self,
        base_url: str | None = None,
        *,
        username: str | None = None,
        password: str | None = None,
        jar_path: Path | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = (
            base_url or os.environ.get(BASE_URL_ENV, "").strip() or DEFAULT_BASE_URL
        ).rstrip("/")
        self.username = (
            username or os.environ.get(USERNAME_ENV, "").strip() or DEFAULT_USERNAME
        )
        # The password is only ever sent in the login request body; it is
        # never logged, never echoed, and never written to the cookie jar.
        self._password = password
        self.jar_path = jar_path or cookie_jar_path()
        self.client = httpx.Client(
            base_url=self.base_url, timeout=30.0, transport=transport
        )
        for name, value in load_cookies(self.jar_path, self.base_url).items():
            self.client.cookies.set(name, value)

    def login(self) -> dict:
        """POST /auth/login, persist the session cookie, return the user JSON."""
        password = self._password or _read_password()
        if not password:
            raise ApiFailure(
                f"{PASSWORD_ENV} is not set; configure the openclaw "
                "service-account password in the environment or in "
                "~/.config/nblane/api.env (0600) (plan §3.1)"
            )
        response = self.client.post(
            f"{API_PREFIX}/auth/login",
            json={"username": self.username, "password": password},
        )
        if response.status_code != 200:
            raise ApiFailure(
                f"login failed: HTTP {response.status_code}: {error_message(response)}"
            )
        # dict(client.cookies) raises CookieConflict when the server sets the
        # same cookie name for multiple paths; dedupe by name, last wins.
        merged: dict[str, str] = {}
        for cookie in self.client.cookies.jar:
            merged[cookie.name] = cookie.value
        save_cookies(self.jar_path, self.base_url, merged)
        return response.json()

    def request(
        self,
        method: str,
        path: str,
        body: object = None,
        headers: dict[str, str] | None = None,
        _reauth: bool = True,
    ) -> httpx.Response:
        kwargs: dict = {}
        if body is not None:
            kwargs["json"] = body
        if headers:
            kwargs["headers"] = headers
        response = self.client.request(method, f"{API_PREFIX}{path}", **kwargs)
        if response.status_code == 401 and _reauth:
            # Expired/absent cookie (TTL 12h): re-login once and retry once.
            self.login()
            response = self.request(method, path, body, headers, _reauth=False)
        return response

    def refresh_etag(self, path: str) -> str:
        """Re-GET the resource for its current ETag (header, then JSON field)."""
        try:
            response = self.request("GET", path.split("?", 1)[0])
        except ApiFailure:
            return ""
        if response.status_code != 200:
            return ""
        etag = response.headers.get("ETag", "").strip()
        if etag:
            return etag
        try:
            body = response.json()
        except ValueError:
            return ""
        if isinstance(body, dict) and isinstance(body.get("etag"), str):
            return body["etag"]
        return ""

    def get(self, path: str) -> httpx.Response:
        return self.checked(self.request("GET", path))

    def mutation(self, path: str, body: object = None) -> httpx.Response:
        """POST without If-Match first; on 412 refetch the ETag and retry once."""
        response = self.request("POST", path, body)
        if response.status_code == 412:
            etag = response.headers.get("ETag", "").strip() or self.refresh_etag(path)
            if not etag:
                raise ApiFailure(
                    f"412 etag_mismatch on {path} and no fresh ETag available; "
                    "re-check the resource state before retrying"
                )
            response = self.request("POST", path, body, {"If-Match": etag})
            if response.status_code == 412:
                raise ApiFailure(
                    f"412 etag_mismatch persists on {path} after one ETag retry; "
                    "the resource is changing under us — stop and re-read it"
                )
        return self.checked(response)

    @staticmethod
    def checked(response: httpx.Response) -> httpx.Response:
        if response.status_code >= 400:
            raise ApiFailure(
                f"HTTP {response.status_code}: {error_message(response)}"
            )
        return response


def profile_path(args: argparse.Namespace, suffix: str) -> str:
    return f"/profiles/{quote(args.profile, safe='')}{suffix}"


def emit(response_or_data) -> None:
    if isinstance(response_or_data, httpx.Response):
        if response_or_data.status_code == 204:
            data: object = {"ok": True}
        else:
            try:
                data = response_or_data.json()
            except ValueError:
                data = {"text": response_or_data.text}
    else:
        data = response_or_data
    print(json.dumps(data, ensure_ascii=False, indent=2))


def run(args: argparse.Namespace, session: Session) -> object:
    command = args.command
    if command == "login":
        return session.login()
    if command == "get":
        return session.get(normalize_path(args.path))
    if command == "post":
        body = None
        if args.json is not None:
            try:
                body = json.loads(args.json)
            except ValueError as exc:
                raise ApiFailure(f"--json body is not valid JSON: {exc}") from exc
        return session.mutation(normalize_path(args.path), body)
    if command == "checkin":
        body: dict = {"habit": args.habit}
        for field in ("date", "summary", "note", "unit", "project_id", "plan_id"):
            value = getattr(args, field)
            if value:
                body[field] = value
        if args.count is not None:
            body["count"] = args.count
        return session.mutation(profile_path(args, "/checkins"), body)
    if command == "plans":
        query = "/habit-plans"
        params = []
        if args.habit:
            params.append(f"habit_id={quote(args.habit, safe='')}")
        if args.status:
            params.append(f"status={quote(args.status, safe='')}")
        if params:
            query += "?" + "&".join(params)
        return session.get(profile_path(args, query))
    if command == "plan-show":
        listing = session.get(profile_path(args, "/habit-plans")).json()
        for plan in listing.get("plans", []):
            if plan.get("id") == args.plan_id:
                return plan
        raise ApiFailure(
            f"unknown habit plan for profile {args.profile}: {args.plan_id}"
        )
    if command == "starmap":
        return session.get(profile_path(args, "/starmap"))
    if command == "board":
        suffix = "/projects-board" + ("?include_archived=true" if args.archived else "")
        return session.get(profile_path(args, suffix))
    if command == "chronicle":
        return session.get(profile_path(args, f"/chronicle?limit={args.limit}"))
    if command == "divine":
        body = {"mode": args.mode, "question": args.question or ""}
        return session.mutation(profile_path(args, "/divination"), body)
    if command == "health":
        return session.get(profile_path(args, "/health"))
    if command == "activity":
        query = f"/activity?status={args.status}&limit={args.limit}"
        if args.kind:
            query += f"&kind={args.kind}"
        return session.get(profile_path(args, query))
    raise ApiFailure(f"unknown command: {command}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nblane_api",
        description=__doc__.split("\n", 1)[0],
    )
    parser.add_argument(
        "--profile",
        default=os.environ.get(PROFILE_ENV, "").strip() or DEFAULT_PROFILE,
        help=f"profile name (env {PROFILE_ENV}; default: %(default)s)",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help=f"API base URL (env {BASE_URL_ENV}; default: {DEFAULT_BASE_URL})",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("login", help="force a fresh login and cache the cookie")
    get = commands.add_parser("get", help="generic GET escape hatch")
    get.add_argument("path")
    post = commands.add_parser("post", help="generic POST escape hatch (ETag retry)")
    post.add_argument("path")
    post.add_argument("json", nargs="?", help="JSON request body")
    checkin = commands.add_parser("checkin", help="append one habit check-in")
    checkin.add_argument("habit", help="habit id or title")
    checkin.add_argument("--date", default="", help="ISO date (default: today)")
    checkin.add_argument("--count", type=float, default=None)
    checkin.add_argument("--unit", default="")
    checkin.add_argument("--summary", default="")
    checkin.add_argument("--note", default="")
    checkin.add_argument("--project-id", dest="project_id", default="")
    checkin.add_argument(
        "--plan",
        dest="plan_id",
        default="",
        help="bind the check-in to an active habit plan id",
    )
    plans = commands.add_parser(
        "plans", help="GET habit plans (阶段计划) with computed progress"
    )
    plans.add_argument("--habit", default="", help="filter by habit id or title")
    plans.add_argument(
        "--status", default="", help="filter by status (active/completed/archived)"
    )
    plan_show = commands.add_parser(
        "plan-show",
        help="show one habit plan by id (incl. current_day/today_tasks)",
    )
    plan_show.add_argument("plan_id")
    commands.add_parser("starmap", help="GET the growth-starmap snapshot")
    board = commands.add_parser("board", help="GET the aggregated projects board")
    board.add_argument("--archived", action="store_true", help="include archived habits")
    chronicle = commands.add_parser("chronicle", help="GET chronicle entries")
    chronicle.add_argument("--limit", type=int, default=40)
    divine = commands.add_parser("divine", help="POST one divination cast (no persistence)")
    divine.add_argument("--mode", choices=["play", "serious"], default="play")
    divine.add_argument("--question", default="", help="required for --mode serious")
    commands.add_parser("health", help="GET the profile health report")
    activity = commands.add_parser("activity", help="GET the agent activity queue")
    activity.add_argument("--status", default="pending")
    activity.add_argument("--kind", default="")
    activity.add_argument("--limit", type=int, default=50)
    return parser


def main(argv: list[str] | None = None, session: Session | None = None) -> int:
    os.umask(0o077)
    args = build_parser().parse_args(argv)
    try:
        session = session or Session(base_url=args.base_url)
        emit(run(args, session))
        return 0
    except ApiFailure as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    except httpx.HTTPError as exc:
        # Never include request bodies here: only the transport-level error.
        print(
            json.dumps({"error": f"request failed: {exc.__class__.__name__}: {exc}"},
                       ensure_ascii=False),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
