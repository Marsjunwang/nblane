"""Tests for ``nblane openclaw sync`` (corpus + skills + automations plan)."""

from __future__ import annotations

import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nblane.commands.openclaw import cmd_sync
from nblane.core.openclaw_automations import CommandResult

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_SRC = REPO_ROOT / "scripts" / "openclaw" / "skills"

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
  - id: moveit2
    status: learning
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


def _make_profile(root: Path) -> Path:
    profile = root / "alice"
    profile.mkdir()
    (profile / "SKILL.md").write_text(SKILL_MD, encoding="utf-8")
    (profile / "skill-tree.yaml").write_text(SKILL_TREE_YAML, encoding="utf-8")
    (profile / "goals.yaml").write_text(GOALS_YAML, encoding="utf-8")
    (profile / "kanban.md").write_text(KANBAN_MD, encoding="utf-8")
    return profile


def _add_automations(profile: Path) -> None:
    assistant = profile / "assistant"
    (assistant / "prompts").mkdir(parents=True)
    (assistant / "prompts" / "daily-plan.md").write_text(
        PROMPT_PLAN, encoding="utf-8"
    )
    (assistant / "automations.yaml").write_text(
        AUTOMATIONS_YAML, encoding="utf-8"
    )


def _list_empty(argv) -> CommandResult:
    return CommandResult(ok=True, returncode=0, stdout="[]")


class TestCmdSync(unittest.TestCase):
    """Write and check modes against a tmp fake OpenClaw workspace."""

    def _run(self, root: Path, profile: Path, **kwargs):
        """Call cmd_sync with tmp dirs; return (exit_code, stdout)."""
        home = root / ".openclaw"
        home.mkdir(exist_ok=True)
        kwargs.setdefault("openclaw_home", home)
        kwargs.setdefault("corpus_out_dir", home / "workspace" / "memory" / "nblane")
        kwargs.setdefault("skills_src", SKILLS_SRC)
        kwargs.setdefault("runner", _list_empty)
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
            contextlib.redirect_stdout(out),
            self.assertRaises(SystemExit) as ctx,
        ):
            cmd_sync("alice", **kwargs)
        return ctx.exception.code, out.getvalue()

    def test_write_renders_corpus_and_copies_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            code, out = self._run(root, profile)
            self.assertEqual(code, 0)

            corpus = root / ".openclaw" / "workspace" / "memory" / "nblane"
            for name in (
                "skill-tree.md",
                "goals.md",
                "kanban.md",
                "profile-summary.md",
            ):
                self.assertTrue((corpus / name).is_file(), name)
            self.assertIn("[写入] skill-tree.md", out)

            skills_dst = root / ".openclaw" / "workspace" / "skills"
            self.assertTrue((skills_dst / "codex-dev" / "SKILL.md").is_file())
            self.assertTrue((skills_dst / "kimi-dev" / "SKILL.md").is_file())
            self.assertTrue(
                (skills_dst / "bin" / "dev_delegate.py").is_file()
            )
            self.assertFalse(
                (skills_dst / "bin" / "tests" / "__pycache__").exists()
            )
            self.assertIn("跳过自动化对账", out)

    def test_check_in_sync_exits_0(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            code, _ = self._run(root, profile)
            self.assertEqual(code, 0)
            code, out = self._run(root, profile, check=True)
            self.assertEqual(code, 0)
            self.assertIn("全部一致", out)

    def test_check_corpus_drift_exits_1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            self._run(root, profile)
            drifted = (
                root
                / ".openclaw"
                / "workspace"
                / "memory"
                / "nblane"
                / "kanban.md"
            )
            drifted.write_text(
                drifted.read_text(encoding="utf-8") + "\nhand edit\n",
                encoding="utf-8",
            )
            code, out = self._run(root, profile, check=True)
            self.assertEqual(code, 1)
            self.assertIn("语料漂移", out)
            self.assertIn("kanban.md", out)

    def test_check_skills_drift_exits_1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            self._run(root, profile)
            target = (
                root
                / ".openclaw"
                / "workspace"
                / "skills"
                / "codex-dev"
                / "SKILL.md"
            )
            target.write_text("tampered\n", encoding="utf-8")
            code, out = self._run(root, profile, check=True)
            self.assertEqual(code, 1)
            self.assertIn("codex-dev", out)

    def test_check_missing_skills_exits_1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            self._run(root, profile)
            skills_dst = root / ".openclaw" / "workspace" / "skills"
            (skills_dst / "kimi-dev" / "SKILL.md").unlink()
            code, out = self._run(root, profile, check=True)
            self.assertEqual(code, 1)
            self.assertIn("+ kimi-dev", out)

    def test_missing_automations_file_is_skipped_not_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            code, out = self._run(root, profile, check=True)
            # Only corpus/skills drift (nothing written yet), never an error.
            self.assertEqual(code, 1)
            self.assertIn("跳过自动化对账", out)
            # --check wrote nothing.
            self.assertFalse(
                (root / ".openclaw" / "workspace").exists()
            )

    def test_automations_drift_exits_1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            _add_automations(profile)
            self._run(root, profile)  # corpus + skills now in sync
            code, out = self._run(root, profile, check=True)
            self.assertEqual(code, 1)
            self.assertIn("自动化对账", out)
            self.assertIn("nblane:daily-plan", out)

    def test_write_mode_reports_automations_drift_without_applying(self) -> None:
        calls: list[list[str]] = []

        def runner(argv) -> CommandResult:
            calls.append(list(argv))
            return CommandResult(ok=True, returncode=0, stdout="[]")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            _add_automations(profile)
            code, out = self._run(root, profile, runner=runner)
            self.assertEqual(code, 1)
            self.assertIn("automations sync alice --apply", out)
            # Only the read-only list call happened; never add/edit/rm.
            self.assertEqual(
                calls, [["openclaw", "automations", "list", "--all", "--json"]]
            )

    def test_write_removes_stale_skill_files(self) -> None:
        """A file deleted from the skills source is pruned from dst on sync."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            skills_src = root / "skills-src"
            (skills_src / "myskill" / "sub").mkdir(parents=True)
            (skills_src / "myskill" / "SKILL.md").write_text(
                "# myskill\n", encoding="utf-8"
            )
            (skills_src / "myskill" / "sub" / "helper.md").write_text(
                "# helper\n", encoding="utf-8"
            )
            code, _ = self._run(root, profile, skills_src=skills_src)
            self.assertEqual(code, 0)
            skills_dst = root / ".openclaw" / "workspace" / "skills"
            self.assertTrue((skills_dst / "myskill" / "sub" / "helper.md").is_file())

            (skills_src / "myskill" / "sub" / "helper.md").unlink()
            code, out = self._run(root, profile, skills_src=skills_src)
            self.assertEqual(code, 0)
            self.assertIn("- myskill/sub/helper.md", out)
            self.assertFalse((skills_dst / "myskill" / "sub" / "helper.md").exists())
            # The emptied managed subdirectory is cleaned up too.
            self.assertFalse((skills_dst / "myskill" / "sub").exists())
            self.assertTrue((skills_dst / "myskill" / "SKILL.md").is_file())
            # And a check run afterwards is clean.
            code, out = self._run(root, profile, skills_src=skills_src, check=True)
            self.assertEqual(code, 0)

    def test_write_preserves_foreign_skill_tree(self) -> None:
        """Files outside the managed top-level entries are never pruned."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            skills_src = root / "skills-src"
            (skills_src / "myskill").mkdir(parents=True)
            (skills_src / "myskill" / "SKILL.md").write_text(
                "# myskill\n", encoding="utf-8"
            )
            skills_dst = root / ".openclaw" / "workspace" / "skills"
            (skills_dst / "other-skill").mkdir(parents=True)
            (skills_dst / "other-skill" / "SKILL.md").write_text(
                "# foreign\n", encoding="utf-8"
            )
            code, _ = self._run(root, profile, skills_src=skills_src)
            self.assertEqual(code, 0)
            self.assertTrue((skills_dst / "other-skill" / "SKILL.md").is_file())
            code, _ = self._run(root, profile, skills_src=skills_src, check=True)
            self.assertEqual(code, 0)
            self.assertTrue((skills_dst / "other-skill" / "SKILL.md").is_file())

    def test_check_reports_stale_skill_files_without_deleting(self) -> None:
        """--check flags dst-only files under managed roots as drift."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            skills_src = root / "skills-src"
            (skills_src / "myskill").mkdir(parents=True)
            (skills_src / "myskill" / "SKILL.md").write_text(
                "# myskill\n", encoding="utf-8"
            )
            code, _ = self._run(root, profile, skills_src=skills_src)
            self.assertEqual(code, 0)
            skills_dst = root / ".openclaw" / "workspace" / "skills"
            (skills_dst / "myskill" / "extra.md").write_text(
                "stale\n", encoding="utf-8"
            )
            code, out = self._run(root, profile, skills_src=skills_src, check=True)
            self.assertEqual(code, 1)
            self.assertIn("- myskill/extra.md", out)
            # Check mode never deletes.
            self.assertTrue((skills_dst / "myskill" / "extra.md").exists())

    def test_missing_profile_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / ".openclaw"
            home.mkdir()
            err = io.StringIO()
            with (
                contextlib.redirect_stderr(err),
                self.assertRaises(SystemExit) as ctx,
            ):
                cmd_sync(
                    "no-such-profile",
                    openclaw_home=home,
                    corpus_out_dir=root / "corpus",
                    runner=_list_empty,
                )
            self.assertEqual(ctx.exception.code, 1)
            self.assertIn("no-such-profile", err.getvalue())

    def test_missing_openclaw_home_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            err = io.StringIO()
            with (
                contextlib.redirect_stderr(err),
                self.assertRaises(SystemExit) as ctx,
            ):
                cmd_sync("alice", openclaw_home=root / "nope")
            self.assertEqual(ctx.exception.code, 1)
            self.assertIn("OpenClaw", err.getvalue())

    def test_unknown_profile_flag_required_when_ambiguous(self) -> None:
        err = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".openclaw").mkdir()
            with (
                patch(
                    "nblane.commands.openclaw.list_profiles",
                    lambda: ["alice", "bob"],
                ),
                contextlib.redirect_stderr(err),
                self.assertRaises(SystemExit) as ctx,
            ):
                cmd_sync(None, openclaw_home=root / ".openclaw")
        self.assertEqual(ctx.exception.code, 1)
        self.assertIn("--profile", err.getvalue())

    def test_single_profile_is_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = _make_profile(root)
            home = root / ".openclaw"
            home.mkdir()
            with (
                patch(
                    "nblane.commands.openclaw.list_profiles",
                    lambda: ["alice"],
                ),
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
                contextlib.redirect_stdout(io.StringIO()),
                self.assertRaises(SystemExit) as ctx,
            ):
                cmd_sync(
                    None,
                    openclaw_home=home,
                    corpus_out_dir=home / "workspace" / "memory" / "nblane",
                    skills_src=SKILLS_SRC,
                    runner=_list_empty,
                )
            self.assertEqual(ctx.exception.code, 0)


class TestCliSmoke(unittest.TestCase):
    def _run(self, *argv: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", "nblane.cli", *argv],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_openclaw_help_lists_sync(self) -> None:
        result = self._run("openclaw", "--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("sync", result.stdout)

    def test_sync_help(self) -> None:
        result = self._run("openclaw", "sync", "--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("--profile", result.stdout)
        self.assertIn("--check", result.stdout)


if __name__ == "__main__":
    unittest.main()
