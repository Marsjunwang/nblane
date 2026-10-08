"""Tests for core/auth_store.py (the only writer of users.yaml)."""

from __future__ import annotations

import os
import stat
import threading
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from nblane.core import auth as auth_core
from nblane.core import auth_store
from nblane.core.auth_store import AccountError

PW = "long-enough-password"


def _hash() -> str:
    return auth_core.hash_password(PW, iterations=100_000, salt=b"0123456789abcdef")


@pytest.fixture
def auth_file(tmp_path, monkeypatch):
    path = tmp_path / "auth" / "users.yaml"
    path.parent.mkdir()
    path.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "users": {
                    "admin": {
                        "display_name": "Admin",
                        "password_hash": _hash(),
                        "role": "admin",
                        "custom_key": "keep-me",
                    },
                    "wang": {
                        "display_name": "Wang",
                        "password_hash": _hash(),
                        "role": "member",
                        "profile": "wang",
                    },
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    os.chmod(path, 0o600)
    monkeypatch.setenv("NBLANE_AUTH_FILE", str(path))
    # Fast hashes for tests.
    real = auth_core.hash_password
    monkeypatch.setattr(
        auth_core, "hash_password", lambda pw, **kw: real(pw, iterations=100_000)
    )
    auth_core.clear_users_cache()
    yield path
    auth_core.clear_users_cache()


def _raw(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_requires_auth_configured(monkeypatch) -> None:
    monkeypatch.setenv("NBLANE_AUTH_FILE", "")
    with pytest.raises(AccountError) as exc:
        auth_store.bump_session_version("admin")
    assert exc.value.code == "auth_not_configured"


def test_create_user_and_login_fields(auth_file) -> None:
    auth_store.create_user(
        "li", display_name="Li", role="member", password="0123456789", profiles=["li"]
    )
    user = auth_core.load_users()["li"]
    assert user.must_change_password is True
    assert user.profiles == ("li",)
    assert auth_core.verify_password("0123456789", user.password_hash)
    with pytest.raises(AccountError) as exc:
        auth_store.create_user("li", display_name="x", role="member", password=PW)
    assert exc.value.code == "user_exists"


@pytest.mark.parametrize(
    ("kwargs", "code"),
    [
        ({"user_id": "a/b", "role": "member", "password": PW}, "invalid_user_id"),
        ({"user_id": "ok", "role": "root", "password": PW}, "invalid_role"),
        ({"user_id": "ok", "role": "member", "password": "short"}, "weak_password"),
    ],
)
def test_create_user_validation(auth_file, kwargs, code) -> None:
    with pytest.raises(AccountError) as exc:
        auth_store.create_user(
            kwargs["user_id"], display_name="", role=kwargs["role"], password=kwargs["password"]
        )
    assert exc.value.code == code


def test_set_password_bumps_session_version(auth_file) -> None:
    auth_store.set_password("wang", "new-password-123", must_change=True)
    user = auth_core.load_users()["wang"]
    assert user.session_version == 1
    assert user.must_change_password is True
    assert auth_core.verify_password("new-password-123", user.password_hash)
    auth_store.set_password("wang", "another-password", must_change=False)
    user = auth_core.load_users()["wang"]
    assert user.session_version == 2
    assert user.must_change_password is False


def test_disable_enable(auth_file) -> None:
    auth_store.set_disabled("wang", True, actor_id="admin")
    user = auth_core.load_users()["wang"]
    assert user.disabled and user.session_version == 1
    auth_store.set_disabled("wang", False, actor_id="admin")
    user = auth_core.load_users()["wang"]
    assert not user.disabled and user.session_version == 1


def test_cannot_disable_or_demote_self(auth_file) -> None:
    with pytest.raises(AccountError) as exc:
        auth_store.set_disabled("admin", True, actor_id="admin")
    assert exc.value.code == "cannot_disable_self"
    with pytest.raises(AccountError) as exc:
        auth_store.update_user("admin", actor_id="admin", role="member")
    assert exc.value.code == "cannot_demote_self"


def test_last_admin_guard(auth_file) -> None:
    with pytest.raises(AccountError) as exc:
        auth_store.set_disabled("admin", True, actor_id="someone-else")
    assert exc.value.code == "last_admin"
    with pytest.raises(AccountError) as exc:
        auth_store.update_user("admin", actor_id="someone-else", role="member")
    assert exc.value.code == "last_admin"
    # Nothing was written by the refused mutations.
    assert auth_core.load_users()["admin"].role == "admin"
    assert not auth_core.load_users()["admin"].disabled
    # With a second admin the demotion is allowed.
    auth_store.update_user("wang", actor_id="admin", role="admin")
    auth_store.update_user("admin", actor_id="wang", role="member")
    assert auth_core.load_users()["admin"].role == "member"


def test_unknown_user(auth_file) -> None:
    for call in (
        lambda: auth_store.set_password("ghost", PW),
        lambda: auth_store.set_disabled("ghost", True, actor_id="admin"),
        lambda: auth_store.update_user("ghost", actor_id="admin", display_name="x"),
        lambda: auth_store.bump_session_version("ghost"),
        lambda: auth_store.create_api_token("ghost", "t"),
        lambda: auth_store.revoke_api_token("ghost", "abc"),
    ):
        with pytest.raises(AccountError) as exc:
            call()
        assert exc.value.code == "user_not_found"


def test_api_tokens_create_and_revoke(auth_file) -> None:
    plaintext, record = auth_store.create_api_token("wang", "openclaw")
    assert plaintext.startswith(f"nbl_{record.id}_")
    assert plaintext not in auth_file.read_text(encoding="utf-8")
    users = auth_core.load_users()
    assert auth_core.user_for_api_token(plaintext, users).id == "wang"
    assert auth_core.user_for_api_token(plaintext + "x", users) is None
    assert auth_core.user_for_api_token("nbl_nope_secret", users) is None
    auth_store.revoke_api_token("wang", record.id)
    assert auth_core.user_for_api_token(plaintext, auth_core.load_users()) is None
    with pytest.raises(AccountError) as exc:
        auth_store.revoke_api_token("wang", record.id)
    assert exc.value.code == "token_not_found"


def test_disabled_user_token_rejected(auth_file) -> None:
    plaintext, _ = auth_store.create_api_token("wang", "t")
    auth_store.set_disabled("wang", True, actor_id="admin")
    assert auth_core.user_for_api_token(plaintext, auth_core.load_users()) is None


def test_unknown_keys_and_other_users_preserved(auth_file) -> None:
    before = _raw(auth_file)
    auth_store.set_password("wang", "new-password-123")
    after = _raw(auth_file)
    assert after["version"] == 1
    assert after["users"]["admin"] == before["users"]["admin"]
    assert after["users"]["admin"]["custom_key"] == "keep-me"
    assert after["users"]["wang"]["profile"] == "wang"


def test_list_form_users_file(auth_file) -> None:
    auth_file.write_text(
        yaml.safe_dump(
            {"users": [{"id": "admin", "password_hash": _hash(), "role": "admin", "x": 1}]}
        ),
        encoding="utf-8",
    )
    auth_store.create_user("li", display_name="Li", role="member", password=PW)
    auth_store.bump_session_version("admin")
    raw = _raw(auth_file)
    assert isinstance(raw["users"], list)
    assert [row["id"] for row in raw["users"]] == ["admin", "li"]
    assert raw["users"][0]["x"] == 1
    users = auth_core.load_users()
    assert users["admin"].session_version == 1
    assert "li" in users


def test_file_mode_preserved(auth_file) -> None:
    auth_store.bump_session_version("wang")
    assert stat.S_IMODE(auth_file.stat().st_mode) == 0o600


def test_new_file_created_0600(tmp_path, monkeypatch) -> None:
    path = tmp_path / "users.yaml"
    monkeypatch.setenv("NBLANE_AUTH_FILE", str(path))
    auth_store.create_user("admin", display_name="A", role="admin", password=PW)
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_record_change_never_called(auth_file) -> None:
    with patch("nblane.core.git_backup.record_change") as record:
        auth_store.create_user("li", display_name="Li", role="member", password=PW)
        auth_store.set_password("li", "new-password-123")
        auth_store.create_api_token("li", "t")
        auth_store.set_disabled("li", True, actor_id="admin")
    record.assert_not_called()


def test_concurrent_writes_both_persist(auth_file) -> None:
    errors: list[BaseException] = []

    def work(user_id: str) -> None:
        try:
            for _ in range(5):
                auth_store.bump_session_version(user_id)
        except BaseException as exc:  # pragma: no cover - surfaced below
            errors.append(exc)

    threads = [threading.Thread(target=work, args=(uid,)) for uid in ("admin", "wang")]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    users = auth_core.load_users()
    assert users["admin"].session_version == 5
    assert users["wang"].session_version == 5


def test_load_users_cache_returns_copies(auth_file) -> None:
    first = auth_core.load_users()
    first.pop("admin")
    assert "admin" in auth_core.load_users()


def test_user_parse_tolerates_bad_types(auth_file) -> None:
    raw = _raw(auth_file)
    raw["users"]["wang"].update(
        {"disabled": "yes", "session_version": "x", "api_tokens": "bad", "agent": 1}
    )
    auth_file.write_text(yaml.safe_dump(raw), encoding="utf-8")
    user = auth_core.load_users()["wang"]
    assert user.disabled is False
    assert user.session_version == 0
    assert user.api_tokens == ()
    assert user.agent is False
