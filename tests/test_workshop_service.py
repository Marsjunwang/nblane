"""Tests for core/workshop_service.py (ttyd + dedicated tmux management).

Service state lives in a temp dir (NBLANE_WORKSHOP_SERVICE_DIR, conftest);
XDG_CONFIG_HOME is pointed at a temp dir so no real unit is ever read or
written. Key-injection tests run against a throwaway tmux server on its own
socket and are skipped when tmux is not installed.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
import time
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from nblane.core import workshop_service as ws


class _TempServiceMixin:
    def setUp(self) -> None:  # noqa: D401 - unittest hook
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self._env = patch.dict(
            os.environ,
            {
                "NBLANE_WORKSHOP_SERVICE_DIR": str(root / "svc"),
                "XDG_CONFIG_HOME": str(root / "config"),
                "NBLANE_WORKSHOP_UNIT": "nblane-workshop-test",
                "NBLANE_CADDYFILE": str(root / "Caddyfile"),
            },
        )
        self._env.start()
        self.root = root

    def tearDown(self) -> None:  # noqa: D401 - unittest hook
        self._env.stop()
        self._tmp.cleanup()


class TestSettings(_TempServiceMixin, unittest.TestCase):
    def test_defaults_when_nothing_saved(self) -> None:
        self.assertEqual(ws.settings(), ws.DEFAULTS)

    def test_save_persists_and_merges(self) -> None:
        ws.save_settings({"font_size_mobile": 20, "renderer": "webgl"})
        values = ws.settings()
        self.assertEqual(values["font_size_mobile"], 20)
        self.assertEqual(values["renderer"], "webgl")
        self.assertEqual(values["scrollback"], ws.DEFAULTS["scrollback"])

    def test_invalid_values_rejected(self) -> None:
        for patch_ in (
            {"font_size_mobile": 99},
            {"font_size_mobile": True},
            {"renderer": "svg"},
            {"mouse": "yes"},
            {"cwd": "relative/path"},
            {"cwd": "/definitely/not/here"},
            {"nope": 1},
        ):
            with self.subTest(patch_=patch_):
                with self.assertRaises(ws.WorkshopServiceError):
                    ws.save_settings(patch_)
        self.assertEqual(ws.settings(), ws.DEFAULTS)

    def test_corrupt_stored_values_fall_back_to_defaults(self) -> None:
        path = Path(os.environ["NBLANE_WORKSHOP_SERVICE_DIR"]) / "settings.json"
        path.parent.mkdir(parents=True)
        path.write_text('{"font_size_mobile": "huge", "mouse": true}', encoding="utf-8")
        values = ws.settings()
        self.assertEqual(values["font_size_mobile"], ws.DEFAULTS["font_size_mobile"])
        self.assertTrue(values["mouse"])

    def test_save_on_unmanaged_service_does_not_touch_systemd(self) -> None:
        with patch.object(ws, "_systemctl") as systemctl:
            result = ws.save_settings({"scrollback": 20000})
        systemctl.assert_not_called()
        self.assertEqual(result, {"tmux_reloaded": False, "ttyd_restarted": False, "reattach_needed": False})


class TestGeneratedFiles(_TempServiceMixin, unittest.TestCase):
    def test_tmux_conf_follows_scroll_and_mouse_settings(self) -> None:
        text = ws.tmux_conf_text()
        self.assertIn("smcup@:rmcup@", text)
        self.assertIn("set -g mouse off", text)
        self.assertIn("set -sg escape-time 10", text)
        other = ws.tmux_conf_text({**ws.DEFAULTS, "native_scroll": False, "mouse": True})
        self.assertIn("set -g terminal-overrides 'xterm*:Tc'\n", other)
        self.assertIn("set -g mouse on", other)

    def test_ttyd_command_uses_dedicated_tmux_server(self) -> None:
        command = ws.ttyd_command({**ws.DEFAULTS, "cwd": "/tmp"}, binary="/x/ttyd")
        self.assertEqual(command[0], "/x/ttyd")
        self.assertIn("127.0.0.1", command)
        self.assertIn("rendererType=canvas", command)
        tail = command[command.index("--") + 1:]
        self.assertEqual(tail[1:3], ["-L", ws.tmux_socket()])
        self.assertEqual(tail[3], "-f")
        self.assertIn("new-session", tail)
        self.assertEqual(tail[-2:], ["-c", "/tmp"])

    def test_unit_keeps_tmux_alive_across_restarts(self) -> None:
        text = ws.unit_text()
        self.assertIn(ws.MANAGED_MARKER, text)
        self.assertIn("KillMode=process", text)
        self.assertIn("WantedBy=default.target", text)
        with patch.dict(os.environ, {"NBLANE_WORKSHOP_AUTOSTART": "0"}):
            self.assertNotIn("[Install]", ws.unit_text())

    def test_start_script_quotes_theme_json(self) -> None:
        text = ws.start_script_text()
        self.assertIn("exec ", text)
        self.assertIn("'theme={", text)


class TestStatus(_TempServiceMixin, unittest.TestCase):
    def test_not_installed(self) -> None:
        with patch.object(ws, "probe", return_value=False):
            self.assertEqual(ws.status()["state"], "not_installed")

    def test_hand_written_unit_is_legacy(self) -> None:
        unit = ws.unit_path()
        unit.parent.mkdir(parents=True)
        unit.write_text("[Service]\nExecStart=/bin/true\n", encoding="utf-8")
        with patch.object(ws, "probe", return_value=True), patch.object(ws, "_unit_state", return_value={"installed": True, "active_state": "active", "sub_state": "running", "since": "", "restarts": 0}):
            data = ws.status()
        self.assertEqual(data["state"], "legacy")
        self.assertFalse(data["managed"])

    def test_caddy_legacy_route_detection(self) -> None:
        caddy = Path(os.environ["NBLANE_CADDYFILE"])
        caddy.write_text("handle /terminal/* {\n  reverse_proxy 127.0.0.1:7668\n}\n", encoding="utf-8")
        self.assertTrue(ws.caddy_legacy_route())
        caddy.write_text("handle {\n  reverse_proxy 127.0.0.1:8504\n}\n", encoding="utf-8")
        self.assertFalse(ws.caddy_legacy_route())

    def test_lifecycle_refuses_unmanaged_unit(self) -> None:
        for action in (ws.start, ws.stop, ws.restart):
            with self.subTest(action=action.__name__):
                with self.assertRaises(ws.WorkshopServiceError):
                    action()


class TestEnsureTtyd(_TempServiceMixin, unittest.TestCase):
    def test_copies_matching_local_binary(self) -> None:
        source = self.root / "ttyd-local"
        source.write_bytes(b"fake ttyd")
        digest = hashlib.sha256(b"fake ttyd").hexdigest()
        with patch.dict(ws.TTYD_SHA256, {ws.machine_arch(): digest}), patch.object(ws, "_ttyd_candidates", return_value=[source]):
            self.assertEqual(ws.ensure_ttyd(), "copied")
            self.assertEqual(ws.ensure_ttyd(), "present")
        self.assertTrue(os.access(ws.ttyd_path(), os.X_OK))

    def test_checksum_mismatch_is_rejected(self) -> None:
        with patch.dict(ws.TTYD_SHA256, {ws.machine_arch(): "0" * 64}), \
                patch.object(ws, "_ttyd_candidates", return_value=[]), \
                patch.object(ws, "_download", return_value=b"tampered"):
            with self.assertRaises(ws.WorkshopServiceError):
                ws.ensure_ttyd()
        self.assertFalse(ws.ttyd_path().exists())

    def test_download_failure_is_user_facing(self) -> None:
        def boom(url: str) -> bytes:
            raise OSError("no network")

        with patch.object(ws, "_ttyd_candidates", return_value=[]), patch.object(ws, "_download", side_effect=boom):
            with self.assertRaises(ws.WorkshopServiceError) as ctx:
                ws.ensure_ttyd()
        self.assertIn("https_proxy", str(ctx.exception))


class TestKeyValidation(unittest.TestCase):
    def test_unknown_and_empty_keys_rejected(self) -> None:
        with self.assertRaises(ws.WorkshopServiceError):
            ws.send_keys(["esc", "rm -rf"])
        with self.assertRaises(ws.WorkshopServiceError):
            ws.send_keys([])

    def test_oversized_text_rejected(self) -> None:
        with self.assertRaises(ws.WorkshopServiceError):
            ws.send_text("x" * (ws.MAX_INPUT_CHARS + 1), submit=False)


@unittest.skipIf(shutil.which("tmux") is None, "tmux not installed")
class TestKeyInjectionWithRealTmux(unittest.TestCase):
    """send_keys / send_text against a throwaway tmux server."""

    def setUp(self) -> None:
        self.socket = f"nblane-test-{uuid.uuid4().hex[:8]}"
        self._env = patch.dict(os.environ, {"NBLANE_WORKSHOP_TMUX_SOCKET": self.socket})
        self._env.start()
        env = {k: v for k, v in os.environ.items() if k != "TMUX"}
        subprocess.run(
            ["tmux", "-L", self.socket, "-f", "/dev/null", "new-session", "-d", "-s", ws.SESSION, "-x", "100", "-y", "20", "cat -v"],
            check=True, env=env,
        )

    def tearDown(self) -> None:
        subprocess.run(["tmux", "-L", self.socket, "kill-server"], check=False, capture_output=True)
        self._env.stop()

    def _screen(self) -> str:
        deadline = time.monotonic() + 3
        text = ""
        while time.monotonic() < deadline:
            text = subprocess.run(
                ["tmux", "-L", self.socket, "capture-pane", "-p", "-t", f"={ws.SESSION}:"],
                capture_output=True, text=True, check=False,
            ).stdout
            if text.strip():
                time.sleep(0.2)
                return subprocess.run(
                    ["tmux", "-L", self.socket, "capture-pane", "-p", "-t", f"={ws.SESSION}:"],
                    capture_output=True, text=True, check=False,
                ).stdout
            time.sleep(0.05)
        return text

    def test_session_is_detected(self) -> None:
        self.assertTrue(ws.session_alive())

    def test_text_with_cjk_and_leading_dash_then_enter(self) -> None:
        ws.send_text("-n 你好 world", submit=True)
        self.assertIn("-n 你好 world", self._screen())

    def test_escape_reaches_the_program(self) -> None:
        ws.send_keys(["esc"])
        ws.send_text("", submit=True)
        self.assertIn("^[", self._screen())

    def test_missing_session_is_user_facing(self) -> None:
        subprocess.run(["tmux", "-L", self.socket, "kill-server"], check=False, capture_output=True)
        with self.assertRaises(ws.WorkshopServiceError):
            ws.send_keys(["esc"])


if __name__ == "__main__":
    unittest.main()
