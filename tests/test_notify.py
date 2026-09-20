"""Tests for core.notify (nblane -> OpenClaw webhook reverse push)."""

from __future__ import annotations

import pytest

from nblane.commands.openclaw import cmd_notify
from nblane.core.notify import (
    DEFAULT_HOOK_URL,
    DEFAULT_TIMEOUT_SECONDS,
    HOOK_TOKEN_ENV,
    HOOK_URL_ENV,
    NotifyConfig,
    NotifyConfigError,
    send_notification,
)


@pytest.fixture(autouse=True)
def _clean_notify_env(monkeypatch):
    monkeypatch.delenv(HOOK_URL_ENV, raising=False)
    monkeypatch.delenv(HOOK_TOKEN_ENV, raising=False)


class _Response:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code


def _recorder(status: int = 200, calls: list | None = None):
    calls = calls if calls is not None else []

    def _post(url, *, json, headers, timeout):
        calls.append(
            {"url": url, "json": json, "headers": headers, "timeout": timeout}
        )
        return _Response(status)

    return _post, calls


def _config(token: str = "secret-token") -> NotifyConfig:
    return NotifyConfig(hook_url="http://127.0.0.1:9999/hooks/agent", hook_token=token)


def test_send_posts_payload_and_bearer_auth():
    poster, calls = _recorder(200)
    result = send_notification("看板逾期提醒", config=_config(), http_post=poster)
    assert result == {"ok": True, "status": 200, "error": None}
    assert len(calls) == 1
    call = calls[0]
    assert call["url"] == "http://127.0.0.1:9999/hooks/agent"
    assert call["json"] == {"text": "看板逾期提醒", "source": "nblane"}
    assert call["headers"]["Authorization"] == "Bearer secret-token"
    assert call["headers"]["Content-Type"] == "application/json"
    assert call["timeout"] == DEFAULT_TIMEOUT_SECONDS


def test_config_from_env_reads_url_and_token(monkeypatch):
    monkeypatch.setenv(HOOK_URL_ENV, "http://127.0.0.1:18789/hooks/ci")
    monkeypatch.setenv(HOOK_TOKEN_ENV, "tok")
    config = NotifyConfig.from_env()
    assert config.hook_url == "http://127.0.0.1:18789/hooks/ci"
    assert config.hook_token == "tok"


def test_config_from_env_defaults_url(monkeypatch):
    # URL unset -> default; token must be present.
    monkeypatch.setenv(HOOK_TOKEN_ENV, "tok")
    config = NotifyConfig.from_env()
    assert config.hook_url == DEFAULT_HOOK_URL


def test_missing_token_raises_clear_error():
    with pytest.raises(NotifyConfigError) as excinfo:
        NotifyConfig.from_env()
    message = str(excinfo.value)
    assert HOOK_TOKEN_ENV in message
    assert "cron.webhookToken" in message


def test_send_missing_token_raises():
    with pytest.raises(NotifyConfigError):
        send_notification("hello", http_post=_recorder()[0])


def test_non_2xx_returns_not_ok():
    poster, _ = _recorder(500)
    result = send_notification("hi", config=_config(), http_post=poster)
    assert result["ok"] is False
    assert result["status"] == 500
    assert result["error"]


def test_timeout_returns_error_and_never_raises():
    def _timeout(url, *, json, headers, timeout):
        raise TimeoutError("timed out")

    result = send_notification("hi", config=_config(), http_post=_timeout)
    assert result == {"ok": False, "status": None, "error": "timed out"}


def test_error_string_never_leaks_token():
    token = "super-secret-token"

    def _boom(url, *, json, headers, timeout):
        raise RuntimeError(f"connection to {url} failed")

    result = send_notification(
        "hi", config=_config(token=token), http_post=_boom
    )
    assert result["ok"] is False
    assert token not in (result["error"] or "")


def test_dry_run_prints_and_never_sends(capsys):
    poster, calls = _recorder(200)
    cmd_notify("周报内容", dry_run=True, http_post=poster)
    out = capsys.readouterr().out
    assert DEFAULT_HOOK_URL in out
    assert '"text": "周报内容"' in out
    assert '"source": "nblane"' in out
    assert calls == []


def test_cmd_notify_success_exits_zero(monkeypatch, capsys):
    monkeypatch.setenv(HOOK_TOKEN_ENV, "tok")
    poster, calls = _recorder(200)
    with pytest.raises(SystemExit) as excinfo:
        cmd_notify("done", http_post=poster)
    assert excinfo.value.code == 0
    assert len(calls) == 1
    assert "[OK]" in capsys.readouterr().out


def test_cmd_notify_failure_exits_one(monkeypatch, capsys):
    monkeypatch.setenv(HOOK_TOKEN_ENV, "tok")
    poster, _ = _recorder(502)
    with pytest.raises(SystemExit) as excinfo:
        cmd_notify("done", http_post=poster)
    assert excinfo.value.code == 1
    assert "失败" in capsys.readouterr().err


def test_cmd_notify_missing_token_exits_one(capsys):
    with pytest.raises(SystemExit) as excinfo:
        cmd_notify("done")
    assert excinfo.value.code == 1
    err = capsys.readouterr().err
    assert HOOK_TOKEN_ENV in err
    assert "cron.webhookToken" in err
