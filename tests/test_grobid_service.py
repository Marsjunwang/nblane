"""Tests for rootless GROBID service management (no real podman/systemd)."""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nblane.core import grobid_service as gs
from nblane.core.research_papers import _pdf_backend


def _done(stdout: str = "", returncode: int = 0, stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess([], returncode, stdout, stderr)


class GrobidServiceTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.env = patch.dict(
            os.environ,
            {
                "NBLANE_GROBID_SERVICE_DIR": str(root / "svc"),
                "XDG_CONFIG_HOME": str(root / "config"),
                "NBLANE_GROBID_URL": "http://127.0.0.1:18070",
                "NBLANE_GROBID_UNIT": "nblane-grobid-test",
                "NBLANE_RESEARCH_PDF_BACKEND": "",
            },
        )
        self.env.start()
        gs._SETTINGS_CACHE.update(key=None, value={})
        with gs._INSTALL_LOCK:
            gs._INSTALL.clear()

    def tearDown(self) -> None:
        self.env.stop()
        self.tmp.cleanup()


class TestConfig(GrobidServiceTestBase):
    def test_quadlet_binds_loopback_and_pins_image(self) -> None:
        text = gs.quadlet_text()
        self.assertIn("PublishPort=127.0.0.1:18070:8070", text)
        self.assertIn(f"Image={gs.IMAGE}", text)
        self.assertIn("Pull=never", text)
        self.assertIn("SuccessExitStatus=143", text)
        self.assertIn("ContainerName=nblane-grobid-test", text)
        self.assertEqual(gs.quadlet_path().name, "nblane-grobid-test.container")

    def test_autostart_can_be_disabled(self) -> None:
        self.assertIn("WantedBy=default.target", gs.quadlet_text())
        with patch.dict(os.environ, {"NBLANE_GROBID_AUTOSTART": "0"}):
            self.assertNotIn("[Install]", gs.quadlet_text())

    def test_remote_url_is_monitor_only(self) -> None:
        with patch.dict(os.environ, {"NBLANE_GROBID_URL": "https://grobid.example.org"}):
            self.assertIsNone(gs.managed_port())
            self.assertIn("不是本机", gs.install_blocker())
            with self.assertRaises(gs.GrobidServiceError):
                gs.quadlet_text()

    def test_unit_name_is_sanitized(self) -> None:
        with patch.dict(os.environ, {"NBLANE_GROBID_UNIT": "../evil;rm -rf"}):
            self.assertEqual(gs.unit_name(), "evilrm-rf")

    def test_backend_override_wins_over_env_and_is_shared(self) -> None:
        with patch.dict(os.environ, {"NBLANE_RESEARCH_PDF_BACKEND": "pymupdf"}):
            self.assertEqual(_pdf_backend(), "pymupdf")
            gs.set_backend("grobid")
            self.assertEqual(_pdf_backend(), "grobid")
            self.assertEqual(gs.effective_backend(), "grobid")
            gs.set_backend("")
            self.assertEqual(_pdf_backend(), "pymupdf")
        with self.assertRaises(gs.GrobidServiceError):
            gs.set_backend("bogus")


class TestStatus(GrobidServiceTestBase):
    def _status(self, *, alive: bool, unit: dict | None = None) -> dict:
        unit = unit or {"installed": False, "active_state": "", "sub_state": "", "memory_mb": 0, "since": "", "restarts": 0}
        probe = (True, "true") if alive else (False, "")
        with (
            patch.object(gs, "_probe", return_value=probe),
            patch.object(gs, "_version", return_value="0.9.0"),
            patch.object(gs, "_unit_state", return_value=unit),
            patch.object(gs, "image_present", return_value=True),
            patch.object(gs, "podman_available", return_value=True),
            patch.object(gs, "user_manager_running", return_value=True),
        ):
            return gs.status()

    def test_external_service_is_reported_but_not_managed(self) -> None:
        result = self._status(alive=True)
        self.assertEqual(result["state"], "external")
        self.assertEqual(result["version"], "0.9.0")

    def test_states_follow_unit_and_health(self) -> None:
        active = {"installed": True, "active_state": "active", "sub_state": "running", "memory_mb": 1300, "since": "", "restarts": 0}
        self.assertEqual(self._status(alive=True, unit=active)["state"], "running")
        self.assertEqual(self._status(alive=False, unit=active)["state"], "starting")
        stopped = {**active, "active_state": "inactive", "sub_state": "dead"}
        self.assertEqual(self._status(alive=False, unit=stopped)["state"], "stopped")
        failed = {**active, "active_state": "failed"}
        self.assertEqual(self._status(alive=False, unit=failed)["state"], "failed")
        self.assertEqual(self._status(alive=False)["state"], "not_installed")

    def test_unit_state_parses_systemctl_show(self) -> None:
        gs.quadlet_path().parent.mkdir(parents=True)
        gs.quadlet_path().write_text("x")
        out = "LoadState=loaded\nActiveState=active\nSubState=running\nMemoryCurrent=1395864371\nNRestarts=2\nResult=success\nActiveEnterTimestamp=Tue\n"
        with patch.object(gs, "_systemctl", return_value=_done(out)), patch.object(gs.shutil, "which", return_value="/usr/bin/systemctl"):
            state = gs._unit_state()
        self.assertEqual(state["memory_mb"], 1331)
        self.assertEqual(state["restarts"], 2)
        self.assertTrue(state["installed"])


class TestLifecycle(GrobidServiceTestBase):
    def _ready(self):
        return (
            patch.object(gs, "podman_available", return_value=True),
            patch.object(gs, "user_manager_running", return_value=True),
        )

    def test_install_writes_unit_and_starts_without_pull_when_image_present(self) -> None:
        calls: list[list[str]] = []

        def fake_run(args, *, timeout=30.0):
            calls.append(args)
            return _done()

        a, b = self._ready()
        with a, b, patch.object(gs, "_run", side_effect=fake_run), patch.object(gs, "image_present", return_value=True), patch.object(gs, "_port_in_use_by_other", return_value=False):
            gs._run_install(True)
        self.assertEqual(gs.install_state()["status"], "done")
        self.assertTrue(gs.quadlet_path().is_file())
        self.assertNotIn(["podman", "pull", gs.IMAGE], calls)
        self.assertIn(["systemctl", "--user", "daemon-reload"], calls)
        self.assertIn(["systemctl", "--user", "start", "--no-block", "nblane-grobid-test.service"], calls)

    def test_install_reports_pull_failure(self) -> None:
        def fake_run(args, *, timeout=30.0):
            if args[:2] == ["podman", "pull"]:
                return _done(returncode=125, stderr="Error: connection refused")
            return _done()

        a, b = self._ready()
        with a, b, patch.object(gs, "_run", side_effect=fake_run), patch.object(gs, "image_present", return_value=False):
            gs._run_install(True)
        state = gs.install_state()
        self.assertEqual(state["status"], "failed")
        self.assertIn("拉取镜像失败", state["error"])
        self.assertFalse(gs.quadlet_path().exists())

    def test_start_refuses_when_another_grobid_owns_the_port(self) -> None:
        gs.quadlet_path().parent.mkdir(parents=True)
        gs.quadlet_path().write_text("x")
        a, b = self._ready()
        with a, b, patch.object(gs, "_port_in_use_by_other", return_value=True):
            with self.assertRaisesRegex(gs.GrobidServiceError, "不是由 nblane 管理"):
                gs.start()

    def test_start_rewrites_outdated_unit(self) -> None:
        gs.quadlet_path().parent.mkdir(parents=True)
        gs.quadlet_path().write_text("[Container]\nImage=old\n")
        a, b = self._ready()
        with a, b, patch.object(gs, "_run", return_value=_done()), patch.object(gs, "_port_in_use_by_other", return_value=False):
            gs.start()
        self.assertEqual(gs.quadlet_path().read_text(), gs.quadlet_text())

    def test_stop_requires_managed_unit(self) -> None:
        with self.assertRaisesRegex(gs.GrobidServiceError, "不是由 nblane 管理"):
            gs.stop()

    def test_uninstall_removes_unit_file(self) -> None:
        gs.quadlet_path().parent.mkdir(parents=True)
        gs.quadlet_path().write_text("x")
        with patch.object(gs, "_run", return_value=_done()):
            gs.uninstall()
        self.assertFalse(gs.quadlet_path().exists())


if __name__ == "__main__":
    unittest.main()
