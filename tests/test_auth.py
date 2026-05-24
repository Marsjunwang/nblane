"""Tests for Streamlit auth helpers without running Streamlit."""

from __future__ import annotations

import os
import tempfile
import unittest
import unittest.mock
from pathlib import Path

import yaml

from nblane.core.auth import (
    AuthConfigError,
    can_access_profile,
    hash_password,
    load_users,
    mint_reader_token,
    verify_reader_token,
    verify_password,
)


class TestAuth(unittest.TestCase):
    """Password hashing and user config parsing."""

    def test_hash_password_verifies(self) -> None:
        """PBKDF2 hashes verify only for the original password."""
        stored = hash_password(
            "secret",
            iterations=100_000,
            salt=b"1234567890123456",
        )
        self.assertTrue(verify_password("secret", stored))
        self.assertFalse(verify_password("wrong", stored))

    def test_load_users_mapping(self) -> None:
        """users mapping supports profile and team authorization fields."""
        stored = hash_password(
            "pw",
            iterations=100_000,
            salt=b"abcdefghijklmnop",
        )
        raw = {
            "users": {
                "wang": {
                    "display_name": "Wang",
                    "password_hash": stored,
                    "role": "member",
                    "profile": "王军",
                    "teams": ["robotics"],
                }
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "users.yaml"
            path.write_text(
                yaml.dump(raw, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            users = load_users(path)

        self.assertIn("wang", users)
        self.assertEqual(users["wang"].profile, "王军")
        self.assertEqual(users["wang"].profiles, ("王军",))
        self.assertEqual(users["wang"].teams, ("robotics",))

    def test_load_users_rejects_missing_hash(self) -> None:
        """A configured user must have a password hash."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "users.yaml"
            path.write_text(
                "users:\n  alice:\n    role: member\n",
                encoding="utf-8",
            )
            with self.assertRaises(AuthConfigError):
                load_users(path)

    def test_reader_token_verifies_claims_and_source(self) -> None:
        """Reader tokens bind user, profile, source, and signature."""
        with unittest.mock.patch.dict(
            os.environ,
            {"NBLANE_READER_TOKEN_SECRET": "test-secret"},
            clear=False,
        ):
            token = mint_reader_token(
                "alice",
                "profile-a",
                "source:paper:one",
                ttl_seconds=120,
            )
            claims = verify_reader_token(
                token,
                expected_source_id="source:paper:one",
            )

            self.assertIsNone(
                verify_reader_token(
                    token,
                    expected_source_id="source:paper:other",
                )
            )

        self.assertIsNotNone(claims)
        assert claims is not None
        self.assertEqual(claims.user_id, "alice")
        self.assertEqual(claims.profile, "profile-a")
        self.assertEqual(claims.source_id, "source:paper:one")

    def test_reader_token_rejects_tampering(self) -> None:
        """Changing the signed payload invalidates the token."""
        with unittest.mock.patch.dict(
            os.environ,
            {"NBLANE_READER_TOKEN_SECRET": "test-secret"},
            clear=False,
        ):
            token = mint_reader_token(
                "alice",
                "profile-a",
                "source:paper:one",
            )
            payload, signature = token.split(".", 1)

            self.assertIsNone(verify_reader_token(f"{payload}x.{signature}"))

    def test_profile_access_helper(self) -> None:
        """Admins can access all profiles; members only configured profiles."""
        stored = hash_password(
            "pw",
            iterations=100_000,
            salt=b"abcdefghijklmnop",
        )
        raw = {
            "users": {
                "admin": {"password_hash": stored, "role": "admin"},
                "member": {
                    "password_hash": stored,
                    "role": "member",
                    "profiles": ["profile-a"],
                },
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "users.yaml"
            path.write_text(
                yaml.dump(raw, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            users = load_users(path)

        self.assertTrue(can_access_profile(users["admin"], "anything"))
        self.assertTrue(can_access_profile(users["member"], "profile-a"))
        self.assertFalse(can_access_profile(users["member"], "profile-b"))


if __name__ == "__main__":
    unittest.main()
