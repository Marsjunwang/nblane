"""Tests for OpenClaw automations-as-code (loader, reconcile, apply)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nblane.core.openclaw_automations import (
    ACTION_ADD,
    ACTION_KEEP,
    ACTION_PRUNE_CANDIDATE,
    ACTION_SKIP_FOREIGN,
    ACTION_UPDATE,
    AutomationSpec,
    CommandResult,
    ReconcileAction,
    apply_reconcile,
    automations_file_path,
    build_action_argv,
    compute_drift_summary,
    fetch_live_automations,
    load_automations_file,
    plan_reconcile,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

PROMPT_PLAN = "# 每日计划\n\n读 profile://kanban，生成今日重点。\n"
PROMPT_WEEKLY = "# 每周巩固\n\n整理记忆并提交 candidate。\n"
TEST_ENV = {"WEIXIN_OWNER_ID": "owner@im.wechat"}

VALID_YAML = """\
version: 1
defaults:
  tz: Asia/Shanghai
  model: qwen/qwen3.8-flash
  fallbacks: [rightcode/gpt-6-astra]
  session: isolated
  timeout_seconds: 300
  deliver:
    channel: openclaw-weixin
    to: ${WEIXIN_OWNER_ID}
automations:
  - key: nblane:daily-plan
    name: 每日计划
    cron: "30 8 * * *"
    prompt: prompts/daily-plan.md
  - key: nblane:weekly-maintenance
    name: 每周巩固
    cron: "0 20 * * 0"
    session: main
    prompt: prompts/weekly.md
"""


def _write_tree(
    root: Path,
    yaml_text: str = VALID_YAML,
    prompts: dict[str, str] | None = None,
) -> Path:
    """Write an assistant/ declaration tree under *root* and return the yaml."""

    assistant = root / "assistant"
    (assistant / "prompts").mkdir(parents=True, exist_ok=True)
    for name, text in (prompts or {}).items():
        (assistant / "prompts" / name).write_text(text, encoding="utf-8")
    path = assistant / "automations.yaml"
    path.write_text(yaml_text, encoding="utf-8")
    return path


def _default_prompts() -> dict[str, str]:
    return {"daily-plan.md": PROMPT_PLAN, "weekly.md": PROMPT_WEEKLY}


def _spec(key: str = "nblane:daily-plan", **overrides) -> AutomationSpec:
    kwargs = dict(
        key=key,
        name="每日计划",
        cron="30 8 * * *",
        tz="Asia/Shanghai",
        session="isolated",
        model="qwen/qwen3.8-flash",
        fallbacks=("rightcode/gpt-6-astra",),
        timeout_seconds=300,
        deliver_channel="openclaw-weixin",
        deliver_to="owner@im.wechat",
        prompt_text=PROMPT_PLAN,
    )
    kwargs.update(overrides)
    return AutomationSpec(**kwargs)


def _live_job(key: str = "nblane:daily-plan", **overrides) -> dict:
    """A recorded-shaped ``automations list --all --json`` entry."""

    job = {
        "name": "每日计划",
        "declarationKey": key,
        "schedule": {"cron": "30 8 * * *", "tz": "Asia/Shanghai"},
        "session": "isolated",
        "delivery": {
            "mode": "announce",
            "channel": "openclaw-weixin",
            "to": "owner@im.wechat",
        },
        "model": "qwen/qwen3.8-flash",
        "fallbacks": ["rightcode/gpt-6-astra"],
        "timeoutSeconds": 300,
        "message": PROMPT_PLAN,
        "enabled": True,
        "failureStreak": 0,
    }
    job.update(overrides)
    return job


class FakeRunner:
    """Prefix-matched fake runner that records every invocation."""

    def __init__(self, responses: list[tuple[tuple[str, ...], CommandResult]]):
        self.responses = responses
        self.calls: list[list[str]] = []

    def __call__(self, argv) -> CommandResult:
        argv = list(argv)
        self.calls.append(argv)
        for prefix, result in self.responses:
            if argv[: len(prefix)] == list(prefix):
                return result
        return CommandResult(ok=False, returncode=1, stderr=f"unexpected: {argv}")


def _ok(stdout: str = "") -> CommandResult:
    return CommandResult(ok=True, returncode=0, stdout=stdout)


class TestLoadAutomationsFile(unittest.TestCase):
    def test_valid_file_merges_defaults_and_resolves(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_tree(Path(tmp), prompts=_default_prompts())
            specs = load_automations_file(path, env=TEST_ENV)
        self.assertEqual(len(specs), 2)
        plan, weekly = specs
        self.assertEqual(plan.key, "nblane:daily-plan")
        self.assertEqual(plan.name, "每日计划")
        self.assertEqual(plan.cron, "30 8 * * *")
        self.assertEqual(plan.tz, "Asia/Shanghai")
        self.assertEqual(plan.session, "isolated")
        self.assertEqual(plan.model, "qwen/qwen3.8-flash")
        self.assertEqual(plan.fallbacks, ("rightcode/gpt-6-astra",))
        self.assertEqual(plan.timeout_seconds, 300)
        self.assertEqual(plan.deliver_channel, "openclaw-weixin")
        self.assertEqual(plan.deliver_to, "owner@im.wechat")
        self.assertEqual(plan.prompt_text, PROMPT_PLAN)
        self.assertEqual(weekly.session, "main")
        self.assertEqual(weekly.prompt_text, PROMPT_WEEKLY)

    def test_unknown_top_level_key_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_tree(
                Path(tmp), VALID_YAML + "bogus: 1\n", _default_prompts()
            )
            with self.assertRaisesRegex(ValueError, "bogus"):
                load_automations_file(path, env=TEST_ENV)

    def test_unknown_automation_key_rejected(self) -> None:
        bad = VALID_YAML.replace(
            "    cron: \"30 8 * * *\"\n",
            "    cron: \"30 8 * * *\"\n    schedule: soon\n",
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_tree(Path(tmp), bad, _default_prompts())
            with self.assertRaisesRegex(ValueError, "unknown keys: schedule"):
                load_automations_file(path, env=TEST_ENV)

    def test_missing_required_field_rejected(self) -> None:
        bad = VALID_YAML.replace("    cron: \"30 8 * * *\"\n", "", 1)
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_tree(Path(tmp), bad, _default_prompts())
            with self.assertRaisesRegex(ValueError, "missing required field 'cron'"):
                load_automations_file(path, env=TEST_ENV)

    def test_foreign_key_rejected(self) -> None:
        bad = VALID_YAML.replace("nblane:daily-plan", "personal-assistant:daily-plan")
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_tree(Path(tmp), bad, _default_prompts())
            with self.assertRaisesRegex(ValueError, "nblane:"):
                load_automations_file(path, env=TEST_ENV)

    def test_foreign_key_with_adopt_accepted(self) -> None:
        adopted = VALID_YAML.replace(
            "  - key: nblane:daily-plan\n",
            "  - key: personal-assistant:daily-plan\n    adopt: true\n",
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_tree(Path(tmp), adopted, _default_prompts())
            specs = load_automations_file(path, env=TEST_ENV)
        plan, weekly = specs
        self.assertEqual(plan.key, "personal-assistant:daily-plan")
        self.assertTrue(plan.adopted)
        self.assertEqual(plan.name, "每日计划")
        self.assertFalse(weekly.adopted)

    def test_adopt_must_be_boolean(self) -> None:
        bad = VALID_YAML.replace(
            "  - key: nblane:daily-plan\n",
            "  - key: personal-assistant:daily-plan\n    adopt: yes please\n",
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_tree(Path(tmp), bad, _default_prompts())
            with self.assertRaisesRegex(ValueError, "'adopt' must be a boolean"):
                load_automations_file(path, env=TEST_ENV)

    def test_adopt_on_managed_key_is_not_adopted(self) -> None:
        yaml_text = VALID_YAML.replace(
            "  - key: nblane:daily-plan\n",
            "  - key: nblane:daily-plan\n    adopt: true\n",
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_tree(Path(tmp), yaml_text, _default_prompts())
            specs = load_automations_file(path, env=TEST_ENV)
        self.assertFalse(specs[0].adopted)

    def test_unset_env_var_fails_loudly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_tree(Path(tmp), prompts=_default_prompts())
            with self.assertRaisesRegex(ValueError, "WEIXIN_OWNER_ID"):
                load_automations_file(path, env={})

    def test_prompt_escape_rejected(self) -> None:
        bad = VALID_YAML.replace(
            "prompt: prompts/daily-plan.md", "prompt: ../outside.md"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_tree(Path(tmp), bad, _default_prompts())
            with self.assertRaisesRegex(ValueError, "escapes"):
                load_automations_file(path, env=TEST_ENV)

    def test_missing_prompt_file_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_tree(
                Path(tmp), prompts={"daily-plan.md": PROMPT_PLAN}
            )
            with self.assertRaisesRegex(ValueError, "prompt file not found"):
                load_automations_file(path, env=TEST_ENV)

    def test_bad_version_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_tree(
                Path(tmp), VALID_YAML.replace("version: 1", "version: 2"),
                _default_prompts(),
            )
            with self.assertRaisesRegex(ValueError, "version"):
                load_automations_file(path, env=TEST_ENV)

    def test_duplicate_key_rejected(self) -> None:
        bad = VALID_YAML.replace(
            "key: nblane:weekly-maintenance", "key: nblane:daily-plan"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_tree(Path(tmp), bad, _default_prompts())
            with self.assertRaisesRegex(ValueError, "duplicate key"):
                load_automations_file(path, env=TEST_ENV)

    def test_invalid_session_rejected(self) -> None:
        bad = VALID_YAML.replace("session: main", "session: detached")
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_tree(Path(tmp), bad, _default_prompts())
            with self.assertRaisesRegex(ValueError, "session"):
                load_automations_file(path, env=TEST_ENV)

    def test_deliver_requires_channel_and_together(self) -> None:
        bad = VALID_YAML.replace("    to: ${WEIXIN_OWNER_ID}\n", "")
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_tree(Path(tmp), bad, _default_prompts())
            with self.assertRaisesRegex(ValueError, "set together"):
                load_automations_file(path, env=TEST_ENV)

    def test_bad_cron_rejected(self) -> None:
        bad = VALID_YAML.replace('"30 8 * * *"', '"30 8 * *"')
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_tree(Path(tmp), bad, _default_prompts())
            with self.assertRaisesRegex(ValueError, "5 fields"):
                load_automations_file(path, env=TEST_ENV)

    def test_template_profile_loads(self) -> None:
        """The shipped template stays in sync with the loader schema."""

        path = automations_file_path(REPO_ROOT / "profiles" / "template")
        specs = load_automations_file(
            path, env={"WEIXIN_OWNER_ID": "owner@im.wechat"}
        )
        self.assertEqual(
            [spec.key for spec in specs],
            [
                "nblane:daily-plan",
                "nblane:daily-review",
                "nblane:weekly-maintenance",
                "nblane:weekly-divination",
            ],
        )
        self.assertEqual(specs[0].cron, "30 8 * * *")
        self.assertEqual(specs[1].cron, "30 21 * * *")
        self.assertEqual(specs[2].cron, "0 20 * * 0")
        self.assertEqual(specs[2].session, "main")
        self.assertEqual(specs[3].cron, "30 20 * * 0")
        for spec in specs:
            self.assertIn("profile://", spec.prompt_text)
            self.assertNotIn("/srv/", spec.prompt_text)


class TestPlanReconcile(unittest.TestCase):
    def test_declared_only_is_add(self) -> None:
        plan = plan_reconcile([_spec()], [])
        self.assertEqual([a.kind for a in plan], [ACTION_ADD])
        self.assertEqual(plan[0].key, "nblane:daily-plan")

    def test_identical_is_keep(self) -> None:
        plan = plan_reconcile([_spec()], [_live_job()])
        self.assertEqual([a.kind for a in plan], [ACTION_KEEP])

    def test_drifted_is_update_with_fields(self) -> None:
        live = _live_job(schedule={"cron": "0 9 * * *", "tz": "Asia/Shanghai"})
        plan = plan_reconcile([_spec()], [live])
        self.assertEqual([a.kind for a in plan], [ACTION_UPDATE])
        self.assertIn("cron", plan[0].reason)

    def test_message_drift_is_update(self) -> None:
        plan = plan_reconcile([_spec()], [_live_job(message="old prompt")])
        self.assertEqual([a.kind for a in plan], [ACTION_UPDATE])
        self.assertIn("message", plan[0].reason)

    def test_message_trailing_newline_is_not_drift(self) -> None:
        plan = plan_reconcile([_spec()], [_live_job(message=PROMPT_PLAN + "\n\n")])
        self.assertEqual([a.kind for a in plan], [ACTION_KEEP])

    def test_undeclared_managed_key_is_prune_candidate(self) -> None:
        plan = plan_reconcile([], [_live_job("nblane:old-job")])
        self.assertEqual([a.kind for a in plan], [ACTION_PRUNE_CANDIDATE])
        self.assertEqual(plan[0].key, "nblane:old-job")

    def test_foreign_keys_are_never_touched(self) -> None:
        live = [
            _live_job("personal-assistant:daily-plan"),
            _live_job("heartbeat:main"),
        ]
        plan = plan_reconcile([], live)
        self.assertEqual(
            [a.kind for a in plan], [ACTION_SKIP_FOREIGN, ACTION_SKIP_FOREIGN]
        )
        for action in plan:
            self.assertIsNone(build_action_argv(action))

    def test_all_branches_and_deterministic_order(self) -> None:
        specs = [
            _spec("nblane:keep-me"),
            _spec("nblane:add-me"),
            _spec("nblane:update-me"),
        ]
        live = [
            _live_job("nblane:prune-me"),
            _live_job("personal-assistant:daily-plan"),
            _live_job("nblane:update-me", session="main"),
            _live_job("nblane:keep-me"),
        ]
        plan_a = plan_reconcile(specs, live)
        plan_b = plan_reconcile(list(reversed(specs)), list(reversed(live)))
        self.assertEqual(
            [(a.kind, a.key) for a in plan_a],
            [(a.kind, a.key) for a in plan_b],
        )
        self.assertEqual(
            [(a.kind, a.key) for a in plan_a],
            [
                (ACTION_ADD, "nblane:add-me"),
                (ACTION_UPDATE, "nblane:update-me"),
                (ACTION_KEEP, "nblane:keep-me"),
                (ACTION_PRUNE_CANDIDATE, "nblane:prune-me"),
                (ACTION_SKIP_FOREIGN, "personal-assistant:daily-plan"),
            ],
        )


class TestAdoptReconcile(unittest.TestCase):
    """Adopted (foreign + ``adopt: true``) keys behave like managed keys."""

    def _adopted_spec(self, **overrides) -> AutomationSpec:
        return _spec("personal-assistant:daily-plan", adopted=True, **overrides)

    def test_declared_adopted_key_is_add_update_keep(self) -> None:
        [add] = plan_reconcile([self._adopted_spec()], [])
        self.assertEqual(add.kind, ACTION_ADD)
        [keep] = plan_reconcile(
            [self._adopted_spec()],
            [_live_job("personal-assistant:daily-plan")],
        )
        self.assertEqual(keep.kind, ACTION_KEEP)
        [update] = plan_reconcile(
            [self._adopted_spec()],
            [_live_job("personal-assistant:daily-plan", session="main")],
        )
        self.assertEqual(update.kind, ACTION_UPDATE)
        self.assertIn("edit", build_action_argv(update))

    def test_removed_adopted_key_is_prune_candidate_when_known(self) -> None:
        live = [_live_job("personal-assistant:daily-plan")]
        [action] = plan_reconcile(
            [], live, adopted_keys={"personal-assistant:daily-plan"}
        )
        self.assertEqual(action.kind, ACTION_PRUNE_CANDIDATE)
        self.assertEqual(
            build_action_argv(action),
            [
                "openclaw",
                "automations",
                "rm",
                "--declaration-key",
                "personal-assistant:daily-plan",
            ],
        )

    def test_removed_adopted_key_defaults_to_foreign(self) -> None:
        # Without adopted_keys, a removed foreign key reverts to skip_foreign.
        live = [_live_job("personal-assistant:daily-plan")]
        [action] = plan_reconcile([], live)
        self.assertEqual(action.kind, ACTION_SKIP_FOREIGN)
        self.assertIsNone(build_action_argv(action))

    def test_adopted_prune_executes_with_include_prune(self) -> None:
        runner = FakeRunner([(("openclaw",), _ok())])
        [action] = plan_reconcile(
            [],
            [_live_job("personal-assistant:daily-plan")],
            adopted_keys={"personal-assistant:daily-plan"},
        )
        results = apply_reconcile(
            [action], runner, dry_run=False, include_prune=True
        )
        self.assertTrue(results[0].executed)
        self.assertEqual(
            runner.calls,
            [
                [
                    "openclaw",
                    "automations",
                    "rm",
                    "--declaration-key",
                    "personal-assistant:daily-plan",
                ]
            ],
        )


class TestApplyReconcile(unittest.TestCase):
    def _mixed_plan(self) -> list[ReconcileAction]:
        return plan_reconcile(
            [_spec()],
            [_live_job(session="main"), _live_job("nblane:stale")],
        )

    def test_dry_run_never_calls_runner(self) -> None:
        def exploding_runner(argv):  # pragma: no cover - must not run
            raise AssertionError(f"runner called with {argv}")

        results = apply_reconcile(self._mixed_plan(), exploding_runner)
        self.assertTrue(all(not r.executed for r in results))
        update = next(r for r in results if r.action.kind == ACTION_UPDATE)
        self.assertIn("edit", update.argv)
        prune = next(
            r for r in results if r.action.kind == ACTION_PRUNE_CANDIDATE
        )
        self.assertIn("rm", prune.argv)

    def test_apply_add_builds_exact_argv(self) -> None:
        runner = FakeRunner([(("openclaw",), _ok())])
        [action] = plan_reconcile([_spec()], [])
        results = apply_reconcile([action], runner, dry_run=False)
        self.assertEqual(len(runner.calls), 1)
        self.assertEqual(
            runner.calls[0],
            [
                "openclaw",
                "automations",
                "add",
                "--declaration-key",
                "nblane:daily-plan",
                "--cron",
                "30 8 * * *",
                "--tz",
                "Asia/Shanghai",
                "--exact",
                "--agent",
                "main",
                "--session",
                "isolated",
                "--name",
                "nblane-daily-plan",
                "--display-name",
                "每日计划",
                "--model",
                "qwen/qwen3.8-flash",
                "--fallbacks",
                "rightcode/gpt-6-astra",
                "--timeout-seconds",
                "300",
                "--announce",
                "--best-effort-deliver",
                "--channel",
                "openclaw-weixin",
                "--to",
                "owner@im.wechat",
                "--message",
                PROMPT_PLAN,
            ],
        )
        self.assertTrue(results[0].executed)
        self.assertTrue(results[0].ok)

    def test_apply_without_delivery_omits_announce(self) -> None:
        runner = FakeRunner([(("openclaw",), _ok())])
        spec = _spec(deliver_channel="", deliver_to="")
        [action] = plan_reconcile([spec], [])
        apply_reconcile([action], runner, dry_run=False)
        self.assertNotIn("--announce", runner.calls[0])
        self.assertNotIn("--channel", runner.calls[0])

    def test_main_session_payload_uses_system_event(self) -> None:
        # OpenClaw 2026.9 rejects --message on main-session jobs.
        runner = FakeRunner([(("openclaw",), _ok())])
        [action] = plan_reconcile([_spec(session="main")], [])
        apply_reconcile([action], runner, dry_run=False)
        argv = runner.calls[0]
        self.assertNotIn("--message", argv)
        self.assertEqual(argv[argv.index("--system-event") + 1], PROMPT_PLAN)
        # 2026.9 also rejects --announce on main-session jobs: the main
        # session already is the owner's chat.
        self.assertNotIn("--announce", argv)
        self.assertNotIn("--channel", argv)

    def test_prune_requires_flag(self) -> None:
        [action] = plan_reconcile([], [_live_job("nblane:stale")])
        runner = FakeRunner([(("openclaw",), _ok())])
        results = apply_reconcile([action], runner, dry_run=False)
        self.assertEqual(runner.calls, [])
        self.assertFalse(results[0].executed)
        results = apply_reconcile(
            [action], runner, dry_run=False, include_prune=True
        )
        self.assertEqual(
            runner.calls,
            [["openclaw", "automations", "rm", "--declaration-key", "nblane:stale"]],
        )
        self.assertTrue(results[0].executed)

    def test_runner_failure_is_collected(self) -> None:
        runner = FakeRunner(
            [(("openclaw",), CommandResult(ok=False, returncode=2, stderr="boom"))]
        )
        [action] = plan_reconcile([_spec()], [])
        results = apply_reconcile([action], runner, dry_run=False)
        self.assertFalse(results[0].ok)
        self.assertIn("boom", results[0].output)


class TestFetchLiveAutomations(unittest.TestCase):
    def test_parses_list(self) -> None:
        runner = FakeRunner(
            [(("openclaw", "automations", "list"), _ok(json.dumps([_live_job()])))]
        )
        jobs = fetch_live_automations(runner)
        self.assertEqual(jobs[0]["declarationKey"], "nblane:daily-plan")

    def test_parses_wrapped_shape(self) -> None:
        runner = FakeRunner(
            [
                (
                    ("openclaw", "automations", "list"),
                    _ok(json.dumps({"automations": [_live_job()]})),
                )
            ]
        )
        self.assertEqual(len(fetch_live_automations(runner)), 1)

    def test_parses_jobs_shape(self) -> None:
        # OpenClaw 2026.9 wraps the list in a "jobs" key.
        runner = FakeRunner(
            [
                (
                    ("openclaw", "automations", "list"),
                    _ok(json.dumps({"jobs": [_live_job()], "total": 1})),
                )
            ]
        )
        jobs = fetch_live_automations(runner)
        self.assertEqual(jobs[0]["declarationKey"], "nblane:daily-plan")

    def test_cli_failure_raises(self) -> None:
        runner = FakeRunner([])
        with self.assertRaisesRegex(RuntimeError, "failed"):
            fetch_live_automations(runner)

    def test_invalid_json_raises(self) -> None:
        runner = FakeRunner(
            [(("openclaw", "automations", "list"), _ok("not json"))]
        )
        with self.assertRaisesRegex(RuntimeError, "JSON"):
            fetch_live_automations(runner)


class TestDriftSummary(unittest.TestCase):
    def test_counts_and_lines(self) -> None:
        plan = plan_reconcile(
            [_spec()],
            [_live_job(session="main"), _live_job("personal-assistant:x")],
        )
        summary = compute_drift_summary(plan)
        self.assertIn("更新 1", summary)
        self.assertIn("外部跳过 1", summary)
        self.assertIn("nblane:daily-plan", summary)
        self.assertIn("personal-assistant:x", summary)

    def test_empty_plan(self) -> None:
        self.assertIn("无声明任务", compute_drift_summary([]))


class TestCmdAutomationsSync(unittest.TestCase):
    """The CLI command honors dry-run and never hits a real gateway."""

    def _profile(self, root: Path) -> Path:
        profile = root / "alice"
        _write_tree(profile, prompts=_default_prompts())
        return profile

    def _patches(self, profile: Path):
        return (
            patch(
                "nblane.commands.openclaw._require_profile",
                lambda _name: profile,
            ),
            patch(
                "nblane.commands.openclaw.automations_file_path",
                lambda _name: profile / "assistant" / "automations.yaml",
            ),
            # cmd loads with the real process env; provide the ${VAR}.
            patch.dict(os.environ, TEST_ENV),
        )

    def test_dry_run_lists_only_and_exits_1_on_drift(self) -> None:
        from nblane.commands.openclaw import cmd_automations_sync

        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            runner = FakeRunner(
                [(("openclaw", "automations", "list"), _ok("[]"))]
            )
            p1, p2, p3 = self._patches(profile)
            with p1, p2, p3, self.assertRaises(SystemExit) as ctx:
                cmd_automations_sync("alice", runner=runner)
        self.assertEqual(ctx.exception.code, 1)
        self.assertEqual(len(runner.calls), 1)
        self.assertIn("list", runner.calls[0])

    def test_apply_executes_add(self) -> None:
        from nblane.commands.openclaw import cmd_automations_sync

        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            runner = FakeRunner(
                [
                    (("openclaw", "automations", "list"), _ok("[]")),
                    (("openclaw",), _ok()),
                ]
            )
            p1, p2, p3 = self._patches(profile)
            with p1, p2, p3, self.assertRaises(SystemExit) as ctx:
                cmd_automations_sync("alice", apply=True, runner=runner)
        self.assertEqual(ctx.exception.code, 0)
        verbs = [call[2] for call in runner.calls[1:]]
        self.assertEqual(verbs, ["add", "add"])

    def test_in_sync_dry_run_exits_0(self) -> None:
        from nblane.commands.openclaw import cmd_automations_sync

        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            live = [
                _live_job("nblane:daily-plan"),
                _live_job(
                    "nblane:weekly-maintenance",
                    name="每周巩固",
                    schedule={"cron": "0 20 * * 0", "tz": "Asia/Shanghai"},
                    session="main",
                    message=PROMPT_WEEKLY,
                ),
            ]
            runner = FakeRunner(
                [
                    (
                        ("openclaw", "automations", "list"),
                        _ok(json.dumps(live)),
                    )
                ]
            )
            p1, p2, p3 = self._patches(profile)
            with p1, p2, p3, self.assertRaises(SystemExit) as ctx:
                cmd_automations_sync("alice", runner=runner)
        self.assertEqual(ctx.exception.code, 0)

    def test_prune_without_apply_warns_and_stays_dry_run(self) -> None:
        """--prune without --apply is a no-op; say so instead of silence."""
        import contextlib
        import io

        from nblane.commands.openclaw import cmd_automations_sync

        with tempfile.TemporaryDirectory() as tmp:
            profile = self._profile(Path(tmp))
            live = [
                _live_job("nblane:daily-plan"),
                _live_job(
                    "nblane:weekly-maintenance",
                    name="每周巩固",
                    schedule={"cron": "0 20 * * 0", "tz": "Asia/Shanghai"},
                    session="main",
                    message=PROMPT_WEEKLY,
                ),
                {"declarationKey": "nblane:stale", "name": "旧任务"},
            ]
            runner = FakeRunner(
                [
                    (
                        ("openclaw", "automations", "list"),
                        _ok(json.dumps(live)),
                    )
                ]
            )
            p1, p2, p3 = self._patches(profile)
            err = io.StringIO()
            with (
                p1,
                p2,
                p3,
                contextlib.redirect_stderr(err),
                self.assertRaises(SystemExit) as ctx,
            ):
                cmd_automations_sync("alice", prune=True, runner=runner)
        self.assertEqual(ctx.exception.code, 0)
        self.assertIn("--prune 只在 --apply 时生效", err.getvalue())
        # Still dry-run: only the read-only list call happened.
        self.assertEqual(len(runner.calls), 1)
        self.assertIn("list", runner.calls[0])


class TestCliSmoke(unittest.TestCase):
    def _run(self, *argv: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", "nblane.cli", *argv],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_openclaw_help(self) -> None:
        result = self._run("openclaw", "--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("doctor", result.stdout)
        self.assertIn("automations", result.stdout)

    def test_doctor_help(self) -> None:
        result = self._run("openclaw", "doctor", "--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("--profile", result.stdout)

    def test_automations_sync_help(self) -> None:
        result = self._run("openclaw", "automations", "sync", "--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("--apply", result.stdout)
        self.assertIn("--prune", result.stdout)


if __name__ == "__main__":
    unittest.main()
