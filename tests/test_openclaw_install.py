"""Tests for ``nblane openclaw install`` (one-command setup, plan §5.4)."""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest

from nblane.commands.openclaw import _install_overlay, cmd_install
from nblane.core.openclaw_automations import CommandResult, substitute_env_text

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_SRC = REPO_ROOT / "scripts" / "openclaw" / "skills"
TEMPLATE_OVERLAY = (
    REPO_ROOT / "profiles" / "template" / "assistant" / "openclaw.overlay.json5"
)

SKILL_MD = """# Alice · nblane Profile

## Identity

- **Name**: Alice
- **Domain**: Robotics
- **North Star Brief**: Robotics expert
- **North Star Visibility**: discreet

---

## Core Competencies

| Area | Status | Notes |
|------|--------|-------|
| Control | solid | shipped |
"""

SKILL_TREE_YAML = """profile: alice
updated: "2026-09-18"

nodes:
  - id: ros2_basics
    status: solid
"""

GOALS_YAML = """schema_version: "1.0"
profile: alice
updated: "2026-09-18"
current_goal_id: g1
goals:
  - id: g1
    title: Ship manipulation demo
    status: active
    summary: Get the arm stacking blocks.
"""

KANBAN_MD = """# Alice · Kanban

## Doing

- [ ] Tune the impedance controller
"""

AUTOMATIONS_YAML = """\
version: 1
defaults:
  tz: Asia/Shanghai
  session: isolated
automations:
  - key: nblane:daily-plan
    cron: "30 8 * * *"
    prompt: prompts/daily-plan.md
"""

PROMPT_PLAN = "# 每日计划\n\n读 profile://kanban。\n"

OVERLAY_JSON = json.dumps(
    {
        "agents": {"defaults": {"model": {"primary": "qwen/qwen3.8-flash"}}},
        "memory": {"search": {"extraPaths": ["~/.openclaw/workspace/memory/nblane"]}},
    },
    indent=2,
)

MCP_ENTRY = {
    "command": "/venv/bin/nblane-mcp",
    "args": [],
    "env": {"NBLANE_ROOT": "/data", "NBLANE_PROFILE": "alice"},
}


def _make_profile(root: Path, *, overlay: str | None = OVERLAY_JSON) -> Path:
    profile = root / "alice"
    profile.mkdir()
    (profile / "SKILL.md").write_text(SKILL_MD, encoding="utf-8")
    (profile / "skill-tree.yaml").write_text(SKILL_TREE_YAML, encoding="utf-8")
    (profile / "goals.yaml").write_text(GOALS_YAML, encoding="utf-8")
    (profile / "kanban.md").write_text(KANBAN_MD, encoding="utf-8")
    assistant = profile / "assistant"
    (assistant / "prompts").mkdir(parents=True)
    (assistant / "prompts" / "daily-plan.md").write_text(
        PROMPT_PLAN, encoding="utf-8"
    )
    (assistant / "automations.yaml").write_text(
        AUTOMATIONS_YAML, encoding="utf-8"
    )
    if overlay is not None:
        (assistant / "openclaw.overlay.json5").write_text(
            overlay, encoding="utf-8"
        )
    return profile


def _make_plugin_dir(root: Path) -> Path:
    plugin = root / "plugins" / "weixin-task-bridge"
    plugin.mkdir(parents=True)
    (plugin / "openclaw.plugin.json").write_text("{}", encoding="utf-8")
    return plugin


class FakeRunner:
    """Records (argv, stdin) pairs; never touches a real gateway."""

    def __init__(self, live_jobs: str = "[]"):
        self.live_jobs = live_jobs
        self.calls: list[tuple[list[str], str | None]] = []

    def __call__(self, argv, input=None) -> CommandResult:
        argv = list(argv)
        self.calls.append((argv, input))
        if argv[:3] == ["openclaw", "automations", "list"]:
            return CommandResult(ok=True, returncode=0, stdout=self.live_jobs)
        return CommandResult(ok=True, returncode=0)

    def argvs(self) -> list[list[str]]:
        return [argv for argv, _ in self.calls]


class TestCmdInstall(unittest.TestCase):
    def _run(self, root: Path, profile: Path, runner: FakeRunner, **kwargs):
        """Call cmd_install against tmp dirs; return (exit_code, stdout)."""
        home = root / ".openclaw"
        home.mkdir(exist_ok=True)
        kwargs.setdefault("openclaw_home", home)
        kwargs.setdefault("corpus_out_dir", home / "workspace" / "memory" / "nblane")
        kwargs.setdefault("skills_src", SKILLS_SRC)
        if "plugin_dir" not in kwargs:
            kwargs["plugin_dir"] = _make_plugin_dir(root)
        kwargs.setdefault("runner", runner)
        out = io.StringIO()
        with (
            patch(
                "nblane.commands.openclaw._require_profile",
                lambda _name: profile,
            ),
            patch(
                "nblane.core.openclaw_corpus.profile_dir",
                lambda _name: profile,
            ),
            patch(
                "nblane.commands.openclaw.automations_file_path",
                lambda _name: profile / "assistant" / "automations.yaml",
            ),
            patch(
                "nblane.commands.openclaw.build_mcp_server_entry",
                lambda _name: dict(MCP_ENTRY),
            ),
            contextlib.redirect_stdout(out),
            self.assertRaises(SystemExit) as ctx,
        ):
            cmd_install("alice", **kwargs)
        return ctx.exception.code, out.getvalue()

    def test_dry_run_prints_all_steps_and_changes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            runner = FakeRunner()
            code, out = self._run(root, profile, runner)
            self.assertEqual(code, 0)
            for step in ("[1/4]", "[2/4]", "[3/4]", "[4/4]"):
                self.assertIn(step, out)
            self.assertIn("dry-run", out)
            self.assertIn("openclaw doctor", out)
            # The plugin install command is printed but never executed.
            self.assertIn("plugins install", out)
            # Nothing written locally.
            self.assertFalse((root / ".openclaw" / "workspace").exists())
            # Runner log: only read-only / self-dry-run gateway calls.
            for argv in runner.argvs():
                is_list = argv[:3] == ["openclaw", "automations", "list"]
                is_patch_dry = (
                    argv[:4] == ["openclaw", "config", "patch", "--stdin"]
                    and "--dry-run" in argv
                )
                self.assertTrue(is_list or is_patch_dry, argv)
            # MCP entry injected into the patch payload.
            patch_inputs = [
                stdin
                for argv, stdin in runner.calls
                if argv[:2] == ["openclaw", "config"]
            ]
            self.assertEqual(len(patch_inputs), 1)
            payload = json.loads(patch_inputs[0])
            self.assertEqual(payload["mcp"]["servers"]["nblane"], MCP_ENTRY)
            self.assertEqual(
                payload["agents"]["defaults"]["model"]["primary"],
                "qwen/qwen3.8-flash",
            )

    def test_apply_executes_every_step(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            plugin = _make_plugin_dir(root)
            runner = FakeRunner()
            code, out = self._run(
                root, profile, runner, apply=True, plugin_dir=plugin
            )
            self.assertEqual(code, 0)
            # Skills + corpus written.
            corpus = root / ".openclaw" / "workspace" / "memory" / "nblane"
            self.assertTrue((corpus / "skill-tree.md").is_file())
            skills = root / ".openclaw" / "workspace" / "skills"
            self.assertTrue((skills / "kimi-dev" / "SKILL.md").is_file())
            argvs = runner.argvs()
            # Plugin install executed with the absolute path.
            self.assertIn(
                [
                    "openclaw",
                    "plugins",
                    "install",
                    str(plugin.resolve()),
                    "--force",
                    "--accept-capabilities",
                ],
                argvs,
            )
            # Config patch executed without --dry-run, MCP entry injected.
            patches = [
                (argv, stdin)
                for argv, stdin in runner.calls
                if argv[:4] == ["openclaw", "config", "patch", "--stdin"]
            ]
            self.assertEqual(len(patches), 1)
            self.assertNotIn("--dry-run", patches[0][0])
            payload = json.loads(patches[0][1])
            self.assertEqual(payload["mcp"]["servers"]["nblane"], MCP_ENTRY)
            # Automations applied (declared job missing live → add).
            adds = [
                argv
                for argv in argvs
                if argv[:3] == ["openclaw", "automations", "add"]
            ]
            self.assertEqual(len(adds), 1)
            self.assertIn("nblane:daily-plan", adds[0])

    def test_missing_overlay_and_plugin_dir_are_skipped_with_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root, overlay=None)
            runner = FakeRunner()
            code, out = self._run(
                root, profile, runner, plugin_dir=root / "no-such-plugin"
            )
            self.assertEqual(code, 0)
            self.assertIn("跳过插件安装", out)
            self.assertIn("跳过配置 overlay", out)
            for argv in runner.argvs():
                self.assertNotEqual(argv[:2], ["openclaw", "plugins"])
                self.assertNotEqual(argv[:2], ["openclaw", "config"])
            # Automations reconcile still ran (read-only list call).
            self.assertEqual(
                runner.argvs(),
                [["openclaw", "automations", "list", "--all", "--json"]],
            )

    def test_missing_automations_file_is_skipped_with_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            (profile / "assistant" / "automations.yaml").unlink()
            runner = FakeRunner()
            code, out = self._run(root, profile, runner)
            self.assertEqual(code, 0)
            self.assertIn("跳过自动化对账", out)
            self.assertNotIn(
                ["openclaw", "automations", "list", "--all", "--json"],
                runner.argvs(),
            )

    def test_non_json_overlay_emits_two_sequential_patches(self) -> None:
        overlay_text = "// JSON5 comment, not pure JSON\n{ model: {} }\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root, overlay=overlay_text)
            runner = FakeRunner()
            code, out = self._run(root, profile, runner)
            self.assertEqual(code, 0)
            patches = [
                stdin
                for argv, stdin in runner.calls
                if argv[:4] == ["openclaw", "config", "patch", "--stdin"]
            ]
            self.assertEqual(len(patches), 2)
            # First patch passes the overlay through verbatim.
            self.assertEqual(patches[0], overlay_text)
            # Second patch is the generated JSON carrying the MCP entry.
            generated = json.loads(patches[1])
            self.assertEqual(
                generated["mcp"]["servers"]["nblane"], MCP_ENTRY
            )

    def test_config_patch_failure_exits_1(self) -> None:
        def runner_fn(argv, input=None) -> CommandResult:
            argv = list(argv)
            if argv[:2] == ["openclaw", "config"]:
                return CommandResult(ok=False, returncode=2, stderr="bad patch")
            if argv[:3] == ["openclaw", "automations", "list"]:
                return CommandResult(ok=True, returncode=0, stdout="[]")
            return CommandResult(ok=True, returncode=0)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            code, out = self._run(root, profile, runner_fn)
            self.assertEqual(code, 1)

    def test_invalid_automations_file_fails_step_not_process(self) -> None:
        """A bad automations.yaml fails step 4 like any other step (exit 1),
        after the closing hints printed — no mid-step ``sys.exit``."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            (profile / "assistant" / "automations.yaml").write_text(
                "version: 99\nautomations: []\n", encoding="utf-8"
            )
            runner = FakeRunner()
            code, out = self._run(root, profile, runner)
            self.assertEqual(code, 1)
            self.assertIn("[4/4]", out)
            self.assertIn("nblane openclaw doctor", out)

    def test_automations_list_failure_fails_step_not_process(self) -> None:
        def runner_fn(argv, input=None) -> CommandResult:
            argv = list(argv)
            if argv[:3] == ["openclaw", "automations", "list"]:
                return CommandResult(ok=False, returncode=1, stderr="gateway down")
            return CommandResult(ok=True, returncode=0)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            code, out = self._run(root, profile, runner_fn)
            self.assertEqual(code, 1)
            self.assertIn("nblane openclaw doctor", out)

    def test_install_automations_returns_false_on_load_error(self) -> None:
        """Direct contract: step 4 reports failure via its return value."""
        from nblane.commands.openclaw import _install_automations

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            (profile / "assistant" / "automations.yaml").write_text(
                "version: 99\nautomations: []\n", encoding="utf-8"
            )
            err = io.StringIO()
            with (
                patch(
                    "nblane.commands.openclaw.automations_file_path",
                    lambda _name: profile / "assistant" / "automations.yaml",
                ),
                contextlib.redirect_stderr(err),
            ):
                ok = _install_automations("alice", FakeRunner(), apply=False)
            self.assertFalse(ok)
            self.assertIn("ERROR", err.getvalue())

    def test_missing_openclaw_home_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            err = io.StringIO()
            with (
                contextlib.redirect_stderr(err),
                self.assertRaises(SystemExit) as ctx,
            ):
                cmd_install("alice", openclaw_home=root / "nope")
            self.assertEqual(ctx.exception.code, 1)
            self.assertIn("OpenClaw", err.getvalue())


class TestTemplateOverlay(unittest.TestCase):
    def test_template_overlay_is_pure_json_without_mcp_or_secrets(self) -> None:
        data = json.loads(TEMPLATE_OVERLAY.read_text(encoding="utf-8"))
        self.assertIsInstance(data, dict)
        # mcp.servers is auto-injected by install, never declared here.
        self.assertNotIn("mcp", data)
        text = TEMPLATE_OVERLAY.read_text(encoding="utf-8")
        # Placeholder env ref only; no concrete owner id or token.
        self.assertIn("${WEIXIN_OWNER_ID}", text)
        self.assertNotIn("@im.wechat\"", text.replace("${WEIXIN_OWNER_ID}", ""))
        self.assertIn(
            "~/.openclaw/workspace/memory/nblane",
            data["memory"]["search"]["extraPaths"],
        )
        self.assertTrue(
            data["channels"]["openclaw-weixin"]["replyProgressMessages"]
        )


def test_substitute_env_text_replaces_known_vars() -> None:
    assert (
        substitute_env_text('{"to": "${SOME_OWNER}"}', env={"SOME_OWNER": "x@y"})
        == '{"to": "x@y"}'
    )


def test_substitute_env_text_unset_var_raises() -> None:
    # Same fail-loud semantics as the automations.yaml loader.
    with pytest.raises(ValueError, match="DEFINITELY_UNSET_VAR"):
        substitute_env_text("${DEFINITELY_UNSET_VAR}", env={})


def test_substitute_env_text_without_refs_passes_through() -> None:
    text = '{"model": {"primary": "qwen/qwen3.8-flash"}}\n'
    assert substitute_env_text(text, env={}) == text


def _patch_mcp_entry(monkeypatch) -> None:
    monkeypatch.setattr(
        "nblane.commands.openclaw.build_mcp_server_entry",
        lambda _name: dict(MCP_ENTRY),
    )


def test_install_overlay_substitutes_env_vars(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("TEST_OVERLAY_OWNER", "owner123@im.wechat")
    _patch_mcp_entry(monkeypatch)
    overlay = tmp_path / "openclaw.overlay.json5"
    overlay.write_text(
        '{"agents": {"defaults": {"heartbeat": {"to": "${TEST_OVERLAY_OWNER}"}}}}',
        encoding="utf-8",
    )
    runner = FakeRunner()
    ok = _install_overlay("alice", overlay, runner, apply=False)
    assert ok is True
    patches = [
        stdin
        for argv, stdin in runner.calls
        if argv[:4] == ["openclaw", "config", "patch", "--stdin"]
    ]
    assert len(patches) == 1
    assert all("--dry-run" in argv for argv, _ in runner.calls)
    payload = json.loads(patches[0])
    assert payload["agents"]["defaults"]["heartbeat"]["to"] == "owner123@im.wechat"
    assert "${" not in patches[0]


def test_install_overlay_unset_var_aborts_before_patch(
    monkeypatch, tmp_path, capsys
) -> None:
    monkeypatch.delenv("TEST_OVERLAY_UNSET", raising=False)
    _patch_mcp_entry(monkeypatch)
    overlay = tmp_path / "openclaw.overlay.json5"
    overlay.write_text('{"to": "${TEST_OVERLAY_UNSET}"}', encoding="utf-8")
    runner = FakeRunner()
    ok = _install_overlay("alice", overlay, runner, apply=False)
    assert ok is False
    # Nothing was sent to the gateway.
    assert runner.calls == []
    assert "TEST_OVERLAY_UNSET" in capsys.readouterr().err


def test_template_overlay_substituted_hierarchy(monkeypatch) -> None:
    """The template overlay must land on the documented config paths.

    Guards against schema drift: the verified production paths are
    ``agents.defaults.*`` (see docs/zh/guides/openclaw-integration.md,
    2026-09-19 实测), not top-level ``model`` / ``heartbeat``.
    """
    monkeypatch.setenv("WEIXIN_OWNER_ID", "owner123@im.wechat")
    text = substitute_env_text(
        TEMPLATE_OVERLAY.read_text(encoding="utf-8"), where=str(TEMPLATE_OVERLAY)
    )
    # No unsubstituted ${...} literal may reach `openclaw config patch`.
    assert "${" not in text
    data = json.loads(text)
    for wrong_top_level in ("model", "imageModel", "heartbeat"):
        assert wrong_top_level not in data
    defaults = data["agents"]["defaults"]
    assert defaults["model"]["primary"] == "qwen/qwen3.8-flash"
    assert defaults["model"]["fallbacks"] == [
        "qwen/qwen3.7-flash",
        "rightcode/gpt-6-astra",
    ]
    assert defaults["utilityModel"] == "qwen/qwen3.7-flash"
    assert defaults["imageModel"]["primary"] == "qwen/qwen3-vl-flash"
    heartbeat = defaults["heartbeat"]
    assert heartbeat["to"] == "owner123@im.wechat"
    assert heartbeat["target"] == "openclaw-weixin"
    assert heartbeat["activeHours"]["timezone"] == "Asia/Shanghai"
    assert data["memory"]["search"]["extraPaths"] == [
        "~/.openclaw/workspace/memory/nblane"
    ]
    assert data["channels"]["openclaw-weixin"]["replyProgressMessages"] is True


class TestCliSmoke(unittest.TestCase):
    def _run(self, *argv: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", "nblane.cli", *argv],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_openclaw_help_lists_install(self) -> None:
        result = self._run("openclaw", "--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("install", result.stdout)

    def test_install_help(self) -> None:
        result = self._run("openclaw", "install", "--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("--dry-run", result.stdout)
        self.assertIn("--apply", result.stdout)
        self.assertIn("--profile", result.stdout)


if __name__ == "__main__":
    unittest.main()
