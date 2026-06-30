"""Tests for the standalone login page and its language gating."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from nblane import web_auth
from nblane.web_i18n import login_ui


class TestLoginUi(unittest.TestCase):
    def test_en_and_zh_share_keys(self) -> None:
        en, zh = login_ui("en"), login_ui("zh")
        self.assertTrue(en)
        self.assertEqual(set(en), set(zh))

    def test_distinct_translations(self) -> None:
        self.assertEqual(login_ui("en")["login_submit"], "Sign in")
        self.assertEqual(login_ui("zh")["login_submit"], "登录")

    def test_unknown_lang_falls_back_to_english(self) -> None:
        self.assertEqual(login_ui("fr"), login_ui("en"))


class TestRenderLoginGate(unittest.TestCase):
    def test_auth_disabled_proceeds_without_login_page(self) -> None:
        with (
            patch.object(web_auth, "ensure_wide_page_shell"),
            patch.object(web_auth, "auth_enabled", return_value=False),
            patch.object(web_auth, "_render_login") as render_login,
        ):
            self.assertTrue(web_auth.render_login_gate())
        render_login.assert_not_called()

    def test_signed_in_user_proceeds(self) -> None:
        with (
            patch.object(web_auth, "ensure_wide_page_shell"),
            patch.object(web_auth, "auth_enabled", return_value=True),
            patch.object(web_auth, "_load_users_or_stop", return_value={}),
            patch.object(web_auth, "current_user", return_value=object()),
            patch.object(web_auth, "_render_login") as render_login,
        ):
            self.assertTrue(web_auth.render_login_gate())
        render_login.assert_not_called()

    def test_anonymous_visitor_gets_login_page(self) -> None:
        users = {"alice": object()}
        with (
            patch.object(web_auth, "ensure_wide_page_shell"),
            patch.object(web_auth, "auth_enabled", return_value=True),
            patch.object(web_auth, "_load_users_or_stop", return_value=users),
            patch.object(web_auth, "current_user", return_value=None),
            patch.object(web_auth, "_render_login") as render_login,
        ):
            web_auth.render_login_gate()
        render_login.assert_called_once_with(users)


if __name__ == "__main__":
    unittest.main()
