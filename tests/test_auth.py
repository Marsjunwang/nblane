"""Tests for Streamlit auth helpers without running Streamlit."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from nblane.core.auth import (
    AuthConfigError,
    hash_password,
    load_users,
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


if __name__ == "__main__":
    unittest.main()
