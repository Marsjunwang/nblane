import unittest
from unittest.mock import patch

from nblane import web_auth, web_page_shell
from nblane.core.auth import User


class TestWebPageShell(unittest.TestCase):
    def test_ensure_wide_page_shell_configures_layout(self) -> None:
        with patch.object(web_page_shell.st, "set_page_config") as set_page_config:
            web_page_shell.ensure_wide_page_shell()

        set_page_config.assert_called_once_with(
            layout="wide",
            initial_sidebar_state="expanded",
        )

    def test_ensure_wide_page_shell_tolerates_existing_page_config(self) -> None:
        with patch.object(
            web_page_shell.st,
            "set_page_config",
            side_effect=RuntimeError("already configured"),
        ):
            web_page_shell.ensure_wide_page_shell()

    def test_require_login_syncs_page_shell_before_auth_work(self) -> None:
        user = User(
            id="local",
            display_name="Local",
            password_hash="",
            role="admin",
            teams=("*",),
        )
        with (
            patch.object(web_auth, "ensure_wide_page_shell") as ensure_shell,
            patch.object(web_auth, "auth_enabled", return_value=False),
            patch.object(web_auth, "_local_user", return_value=user),
            patch.object(web_auth.git_backup, "start_operation") as start_operation,
        ):
            result = web_auth.require_login()

        self.assertEqual(result, user)
        ensure_shell.assert_called_once_with()
        start_operation.assert_called_once_with("local")


if __name__ == "__main__":
    unittest.main()
