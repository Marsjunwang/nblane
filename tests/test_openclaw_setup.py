"""Tests for OpenClaw install/connect/migrate orchestration (fake CLI)."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nblane.core import openclaw_setup as oc


def _ok(stdout: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess([], 0, stdout, "")


class FakeOpenClaw:
    """Records argv and mutates a JSON config like the real CLI would."""

    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path
        self.calls: list[list[str]] = []
        self.envs: list[dict[str, str] | None] = []

    def _config(self) -> dict:
        return json.loads(self.config_path.read_text()) if self.config_path.exists() else {}

    def _save(self, data: dict) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(data))

    def __call__(self, args, *, timeout=60.0, env=None, cwd=None):
        self.calls.append(list(args))
        self.envs.append(env)
        if args[0] != "openclaw":
            return _ok()
        rest = args[1:]
        if rest[:2] == ["--profile", rest[1] if len(rest) > 1 else ""]:
            rest = rest[2:]
        data = self._config()
        if rest[:2] == ["mcp", "set"]:
            data.setdefault("mcp", {}).setdefault("servers", {})[rest[2]] = json.loads(rest[3])
            self._save(data)
        elif rest[:2] == ["config", "set"]:
            node = data
            keys = rest[2].split(".")
            for key in keys[:-1]:
                node = node.setdefault(key, {})
            node[keys[-1]] = json.loads(rest[3]) if "--strict-json" in rest else rest[3]
            self._save(data)
        elif rest[:1] == ["onboard"]:
            ws = rest[rest.index("--workspace") + 1]
            Path(ws).mkdir(parents=True, exist_ok=True)
            (Path(ws) / "AGENTS.md").write_text("# agents\n")
            self._save({"agents": {"defaults": {"workspace": ws}, "entries": {"main": {"workspace": ws}}}})
        return _ok()


class OpenClawSetupTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.env = patch.dict(
            os.environ,
            {
                "HOME": str(self.home),
                "NBLANE_OPENCLAW_PROFILE": "",
                "OPENCLAW_CONFIG_PATH": "",
                "NBLANE_AGENT_DATA_ROOT": str(self.root / "agent-data"),
                "NBLANE_BACKUP_STATE_DIR": str(self.root / "state"),
                "NBLANE_BACKUP_DIR": str(self.root / "backups"),
                "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
            },
        )
        self.env.start()
        self.home_patch = patch.object(oc.Path, "home", return_value=self.home)
        self.home_patch.start()
        self.fake = FakeOpenClaw(self.home / ".openclaw" / "openclaw.json")
        self.run_patch = patch.object(oc, "_run", side_effect=self.fake)
        self.run_patch.start()
        self.corpus = patch.object(oc, "refresh_corpus", side_effect=self._corpus)
        self.corpus.start()
        self.venv = patch.object(oc, "_ensure_skills_runner")
        self.venv.start()

    def tearDown(self) -> None:
        for item in (self.venv, self.corpus, self.run_patch, self.home_patch, self.env):
            item.stop()
        with oc._JOB_LOCK:
            oc._JOB.clear()
        self.tmp.cleanup()

    def _corpus(self, profile, workspace=None):
        out = (workspace or oc.workspace_path()) / "memory" / "nblane"
        out.mkdir(parents=True, exist_ok=True)
        (out / "profile-summary.md").write_text(profile)
        return out

    def _existing_install(self) -> Path:
        ws = self.home / ".openclaw" / "workspace"
        ws.mkdir(parents=True)
        (ws / "MEMORY.md").write_text("mem\n")
        self.fake._save({"agents": {"defaults": {"workspace": str(ws)}, "entries": {"main": {"workspace": str(ws)}}}})
        return ws

    def _openclaw_calls(self) -> list[list[str]]:
        return [call[1:] for call in self.fake.calls if call[0] == "openclaw"]


class TestPaths(OpenClawSetupTestBase):
    def test_profile_isolates_state_unit_and_cli(self) -> None:
        with patch.dict(os.environ, {"NBLANE_OPENCLAW_PROFILE": "nblane-dev"}):
            self.assertEqual(oc.state_dir(), self.home / ".openclaw-nblane-dev")
            self.assertEqual(oc.gateway_unit(), "openclaw-gateway-nblane-dev.service")
            self.assertEqual(oc.cli_prefix(), ["openclaw", "--profile", "nblane-dev"])

    def test_workspace_from_config(self) -> None:
        self.assertIsNone(oc.workspace_path())
        ws = self._existing_install()
        self.assertEqual(oc.workspace_path(), ws)

    def test_node_support(self) -> None:
        self.assertTrue(oc.node_supported("24.21.0"))
        self.assertTrue(oc.node_supported("26.1.0"))
        self.assertFalse(oc.node_supported("24.15.9"))
        self.assertFalse(oc.node_supported("25.0.0"))


class TestConnect(OpenClawSetupTestBase):
    def test_connect_registers_mcp_corpus_and_git(self) -> None:
        ws = self._existing_install()
        oc._do_connect("alice")
        config = self.fake._config()
        entry = config["mcp"]["servers"]["nblane"]
        self.assertEqual(entry["env"]["NBLANE_PROFILE"], "alice")
        self.assertEqual(config["memory"]["search"]["extraPaths"], [str(ws / "memory" / "nblane")])
        self.assertTrue((ws / ".git").is_dir())
        self.assertIn("memory/nblane/", (ws / ".gitignore").read_text())
        self.assertEqual(oc.connected_profile(), "alice")
        # Model routing is never touched by connect.
        self.assertFalse(any(call[:1] == ["onboard"] for call in self._openclaw_calls()))

    def test_skills_runner_uses_nblane_python(self) -> None:
        ws = self._existing_install()
        self.venv.stop()
        oc._ensure_skills_runner(ws)
        self.venv.start()
        wrapper = (ws / "skills" / "bin" / "nblane_api").read_text()
        self.assertIn(oc.sys.executable, wrapper)
        self.assertTrue((oc.REPO_SCRIPTS / "skills" / "bin" / "nblane_api.py").is_file())

    def test_connect_is_idempotent(self) -> None:
        self._existing_install()
        oc._do_connect("alice")
        before = len(self._openclaw_calls())
        oc._do_connect("alice")
        new_calls = self._openclaw_calls()[before:]
        self.assertFalse(any(call[:2] in (["mcp", "set"], ["config", "set"]) for call in new_calls))


class TestInstall(OpenClawSetupTestBase):
    def test_onboard_reuses_llm_key_via_env_only(self) -> None:
        config = {"base_url": "https://llm.example/v1", "model": "m-1", "api_key": "sk-secret", "configured": True}
        with patch("nblane.core.llm.current_config", return_value=config), patch.object(oc.shutil, "which", return_value="/bin/openclaw"):
            oc._do_install({"profile": "alice", "reuse_llm": True})
        onboard_index = next(i for i, call in enumerate(self.fake.calls) if "onboard" in call)
        argv = self.fake.calls[onboard_index]
        self.assertNotIn("sk-secret", " ".join(argv))
        self.assertEqual(self.fake.envs[onboard_index], {"CUSTOM_API_KEY": "sk-secret"})
        self.assertEqual(argv[argv.index("--custom-model-id") + 1], "m-1")
        self.assertEqual(argv[argv.index("--workspace") + 1], str(oc.target_workspace()))
        self.assertEqual(argv[argv.index("--gateway-bind") + 1], "loopback")
        self.assertTrue((oc.target_workspace() / ".git").is_dir())

    def test_install_without_llm_skips_auth(self) -> None:
        with patch.object(oc.shutil, "which", return_value="/bin/openclaw"):
            args, env = oc._onboard_args(Path("/w"), reuse_llm=False)
        self.assertEqual(args[args.index("--auth-choice") + 1], "skip")
        self.assertEqual(env, {})

    def test_npm_pins_version(self) -> None:
        which = {"openclaw": None}

        def fake_which(name):
            return which.get(name, f"/bin/{name}")

        def after_npm(args, **kwargs):
            if args[0] == "npm":
                which["openclaw"] = "/bin/openclaw"
            return self.fake(args, **kwargs)

        self.run_patch.stop()
        with patch.object(oc, "_run", side_effect=after_npm), patch.object(oc.shutil, "which", side_effect=fake_which):
            oc._do_install({"profile": "alice", "reuse_llm": False})
        self.run_patch.start()
        self.assertIn(["npm", "install", "-g", f"openclaw@{oc.PINNED_VERSION}"], self.fake.calls)


class TestMigrate(OpenClawSetupTestBase):
    def test_migrate_moves_symlinks_and_repoints(self) -> None:
        ws = self._existing_install()
        with patch.object(oc, "_wait_port", return_value=True):
            oc._do_migrate()
        new = oc.target_workspace()
        self.assertTrue((new / "MEMORY.md").is_file())
        self.assertTrue(ws.is_symlink())
        self.assertEqual(ws.resolve(), new.resolve())
        config = self.fake._config()
        self.assertEqual(config["agents"]["defaults"]["workspace"], str(new))
        self.assertEqual(config["agents"]["entries"]["main"]["workspace"], str(new))
        calls = self._openclaw_calls()
        self.assertLess(calls.index(["gateway", "stop", "--force"]), calls.index(["gateway", "start"]))
        archives = list((self.root / "backups").glob("*.tgz"))
        self.assertEqual(len(archives), 1)
        self.assertEqual(archives[0].stat().st_mode & 0o777, 0o600)

    def test_migrate_rolls_back_on_failure(self) -> None:
        ws = self._existing_install()
        with patch.object(oc, "_wait_port", return_value=True), patch.object(oc, "_set_workspace", side_effect=oc.OpenClawSetupError("boom")):
            with self.assertRaises(oc.OpenClawSetupError):
                oc._do_migrate()
        self.assertFalse(ws.is_symlink())
        self.assertTrue((ws / "MEMORY.md").is_file())
        self.assertFalse(oc.target_workspace().exists())
        self.assertEqual(self._openclaw_calls()[-1], ["gateway", "start"])

    def test_blocker_when_already_in_agent_root(self) -> None:
        target = oc.target_workspace()
        target.mkdir(parents=True)
        self.fake._save({"agents": {"defaults": {"workspace": str(target)}}})
        with patch.object(oc.shutil, "which", return_value="/bin/openclaw"):
            self.assertIn("已经在", oc.job_blocker("migrate", {}))


class TestForeignRoot(OpenClawSetupTestBase):
    def test_refuses_gateway_wired_to_another_data_root(self) -> None:
        self._existing_install()
        data = self.fake._config()
        data["mcp"] = {"servers": {"nblane": {"command": "x", "env": {"NBLANE_ROOT": "/srv/nblane-data"}}}}
        self.fake._save(data)
        with patch.object(oc.paths, "REPO_ROOT", self.root / "dev-data"), patch.object(oc.shutil, "which", return_value="/bin/openclaw"):
            self.assertEqual(oc.foreign_root(), "/srv/nblane-data")
            for kind in ("connect", "migrate", "weixin"):
                self.assertIn("另一个 nblane 数据目录", oc.job_blocker(kind, {"profile": "alice"}))
            with self.assertRaises(oc.OpenClawSetupError):
                oc.gateway_action("restart")
        self.assertFalse(any(call[:2] == ["gateway", "restart"] for call in self._openclaw_calls()))

    def test_gateway_restart_drains_active_work(self) -> None:
        self._existing_install()
        oc.gateway_action("restart")
        self.assertIn(["gateway", "restart", "--safe"], self._openclaw_calls())

    def test_same_root_is_not_foreign(self) -> None:
        self._existing_install()
        with patch.object(oc.paths, "REPO_ROOT", self.root / "data"):
            oc._do_connect("alice")
            self.assertEqual(oc.foreign_root(), "")


class TestJobs(OpenClawSetupTestBase):
    def test_unknown_profile_blocks_connect(self) -> None:
        self._existing_install()
        with patch.object(oc.shutil, "which", return_value="/bin/openclaw"), patch("nblane.core.profile_io.list_profiles", return_value=["alice"]):
            self.assertEqual(oc.job_blocker("connect", {"profile": "alice"}), "")
            self.assertIn("档案", oc.job_blocker("connect", {"profile": "../etc"}))

    def test_failed_job_reports_error(self) -> None:
        with patch.object(oc, "_do_migrate", side_effect=oc.OpenClawSetupError("网关坏了")):
            oc._run_job("migrate", {})
        state = oc.job_state()
        self.assertEqual(state["status"], "failed")
        self.assertEqual(state["error"], "网关坏了")


if __name__ == "__main__":
    unittest.main()
