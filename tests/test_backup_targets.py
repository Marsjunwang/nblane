"""Tests for git backup targets (local bare repositories, no network/ssh)."""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nblane.core import backup_targets as bt


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


class BackupTargetsTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        (self.workspace / "MEMORY.md").write_text("# memory\n", encoding="utf-8")
        (self.workspace / "skills" / ".venv").mkdir(parents=True)
        (self.workspace / "skills" / ".venv" / "pyvenv.cfg").write_text("x", encoding="utf-8")
        self.env = patch.dict(
            os.environ,
            {
                "NBLANE_BACKUP_KEY_DIR": str(self.root / "keys"),
                "NBLANE_BACKUP_STATE_DIR": str(self.root / "state"),
                "XDG_CONFIG_HOME": str(self.root / "config"),
                "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
            },
        )
        self.env.start()
        self.target = bt.BackupTarget(
            id=bt.TARGET_OPENCLAW_WORKSPACE,
            label="ws",
            description="",
            path=self.workspace,
            commit_mode=bt.COMMIT_ALL,
            gitignore=bt.WORKSPACE_GITIGNORE,
            untrack=bt.WORKSPACE_UNTRACK,
        )
        self.targets = patch.object(bt, "list_targets", return_value=[self.target])
        self.targets.start()

    def tearDown(self) -> None:
        self.targets.stop()
        self.env.stop()
        self.tmp.cleanup()

    def _bare(self, name: str = "remote.git") -> Path:
        bare = self.root / name
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(bare)], check=True)
        return bare

    def _local_url(self, bare: Path):
        info = {"url": str(bare), "host": "local", "owner": "o", "repo": "r"}
        return patch.object(bt, "validate_remote_url", return_value=info)


class TestValidateRemoteUrl(unittest.TestCase):
    def test_accepts_ssh_forms(self) -> None:
        self.assertEqual(bt.validate_remote_url("git@github.com:alice/ws.git")["repo"], "ws")
        self.assertEqual(bt.validate_remote_url("ssh://git@github.com/alice/ws")["owner"], "alice")

    def test_rejects_https_options_and_injection(self) -> None:
        for bad in (
            "https://github.com/alice/ws.git",
            "--upload-pack=evil",
            "git@github.com:alice/ws.git; rm -rf /",
            "git@-oProxyCommand=x:a/b",
            "",
        ):
            with self.subTest(bad=bad), self.assertRaises(bt.BackupError):
                bt.validate_remote_url(bad)


class TestRepoAndStatus(BackupTargetsTestBase):
    def test_ensure_repo_creates_snapshot_without_venv(self) -> None:
        self.assertTrue(bt.ensure_repo(self.workspace, bt.WORKSPACE_GITIGNORE, untrack=bt.WORKSPACE_UNTRACK))
        files = _git(self.workspace, "ls-files").splitlines()
        self.assertIn("MEMORY.md", files)
        self.assertNotIn("skills/.venv/pyvenv.cfg", files)
        self.assertFalse(bt.ensure_repo(self.workspace, bt.WORKSPACE_GITIGNORE))

    def test_ensure_repo_snapshots_empty_existing_repo(self) -> None:
        subprocess.run(["git", "init", "-q", "-b", "master", str(self.workspace)], check=True)
        self.assertFalse(bt.ensure_repo(self.workspace, bt.WORKSPACE_GITIGNORE, untrack=bt.WORKSPACE_UNTRACK))
        self.assertIn("MEMORY.md", _git(self.workspace, "ls-files"))

    def test_ensure_repo_untracks_previously_committed_venv(self) -> None:
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.workspace)], check=True)
        _git(self.workspace, "add", "-A")
        _git(self.workspace, "commit", "-qm", "init")
        self.assertIn("skills/.venv/pyvenv.cfg", _git(self.workspace, "ls-files"))
        bt.ensure_repo(self.workspace, bt.WORKSPACE_GITIGNORE, untrack=bt.WORKSPACE_UNTRACK)
        self.assertNotIn("skills/.venv/pyvenv.cfg", _git(self.workspace, "ls-files", "--cached"))
        self.assertTrue((self.workspace / "skills" / ".venv" / "pyvenv.cfg").exists())

    def test_status_reports_dirty_and_unpushed(self) -> None:
        bt.init_target(self.target.id)
        (self.workspace / "USER.md").write_text("me\n", encoding="utf-8")
        data = bt.target_status(self.target)
        self.assertTrue(data["is_git"])
        self.assertEqual(data["remote_url"], "")
        self.assertEqual(data["dirty"], 1)
        self.assertEqual(data["ahead"], 1)

    def test_generate_key_is_stable(self) -> None:
        first = bt.generate_key(self.target.id)
        self.assertTrue(first.startswith("ssh-ed25519 "))
        self.assertEqual(bt.generate_key(self.target.id), first)
        key = bt.default_key_path(self.target.id)
        self.assertEqual(key.stat().st_mode & 0o777, 0o600)


class TestRemoteFlow(BackupTargetsTestBase):
    def setUp(self) -> None:
        super().setUp()
        bt.init_target(self.target.id)
        bt.generate_key(self.target.id)

    def test_public_repository_is_refused(self) -> None:
        bare = self._bare()
        with self._local_url(bare), patch.object(bt, "_network_visibility", return_value="public"):
            result = bt.test_remote(self.target.id, "git@github.com:a/b.git")
        self.assertFalse(result["ok"])
        self.assertIn("公开", result["message"])

    def test_requires_key(self) -> None:
        bt.default_key_path(self.target.id).unlink()
        with self._local_url(self._bare()):
            result = bt.test_remote(self.target.id, "x")
        self.assertFalse(result["ok"])
        self.assertIn("部署密钥", result["message"])

    def test_connect_push_and_daily_run(self) -> None:
        bare = self._bare()
        with self._local_url(bare), patch.object(bt, "_network_visibility", return_value="hidden"):
            check = bt.test_remote(self.target.id, "git@github.com:a/b.git")
            self.assertTrue(check["ok"], check["message"])
            self.assertTrue(check["remote_empty"])
            status = bt.connect_remote(self.target.id, "git@github.com:a/b.git")
        self.assertEqual(status["ahead"], 0)
        self.assertIn("-i ", _git(self.workspace, "config", "core.sshCommand"))
        self.assertEqual(_git(bare, "rev-parse", "main"), _git(self.workspace, "rev-parse", "HEAD"))

        (self.workspace / "memory").mkdir()
        (self.workspace / "memory" / "2026-10-06.md").write_text("note\n", encoding="utf-8")
        [result] = bt.run_backup()
        self.assertTrue(result["ok"], result["error"])
        self.assertTrue(result["committed"])
        self.assertIn("memory/2026-10-06.md", _git(bare, "ls-tree", "-r", "--name-only", "main"))
        self.assertTrue(bt.target_status(self.target)["last_run"]["pushed"])

    def test_diverged_remote_is_rejected(self) -> None:
        bare = self._bare()
        other = self.root / "other"
        subprocess.run(["git", "clone", "-q", str(bare), str(other)], check=True, capture_output=True)
        (other / "x").write_text("x", encoding="utf-8")
        _git(other, "add", "x")
        _git(other, "commit", "-qm", "x")
        _git(other, "push", "-q", "origin", "HEAD:main")
        with self._local_url(bare):
            result = bt.test_remote(self.target.id, "x")
        self.assertFalse(result["ok"])
        self.assertIn("历史", result["message"])

    def test_push_only_target_never_commits(self) -> None:
        data = bt.BackupTarget(
            id=bt.TARGET_NBLANE_DATA, label="d", description="", path=self.workspace,
            commit_mode=bt.COMMIT_PUSH_ONLY, gitignore=bt.DATA_GITIGNORE,
        )
        (self.workspace / "loose.txt").write_text("x", encoding="utf-8")
        result = bt.backup_target(data)
        self.assertFalse(result["committed"])
        self.assertIn("远端", result["error"])
        self.assertIn("loose.txt", _git(self.workspace, "status", "--porcelain"))


class TestTimer(BackupTargetsTestBase):
    def test_units_written_and_enabled(self) -> None:
        calls: list[tuple[str, ...]] = []

        def fake(*args: str, timeout: float = 30.0):
            calls.append(args)
            return subprocess.CompletedProcess(args, 0, "enabled\n" if args[0] == "is-enabled" else "", "")

        with patch.object(bt, "_systemctl", side_effect=fake), patch.object(bt.shutil, "which", return_value="/bin/systemctl"):
            state = bt.set_timer(True)
        unit_dir = self.root / "config" / "systemd" / "user"
        self.assertIn("OnCalendar=*-*-* 03:30:00", (unit_dir / "nblane-backup.timer").read_text())
        self.assertIn("-m nblane.cli backup run", (unit_dir / "nblane-backup.service").read_text())
        self.assertIn(("enable", "--now", "nblane-backup.timer"), calls)
        self.assertTrue(state["enabled"])


if __name__ == "__main__":
    unittest.main()
