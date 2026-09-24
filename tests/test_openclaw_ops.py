"""Tests for the OpenClaw doctor checks (mocked runner, no real CLI)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from nblane.core.openclaw_automations import CommandResult
from nblane.core.openclaw_ops import (
    SEVERITY_ERROR,
    SEVERITY_INFO,
    SEVERITY_WARNING,
    check_automations_in_sync,
    check_backup_schedule,
    check_gateway_port,
    check_linger,
    check_nblane_mcp_registered,
    check_node_version,
    check_openclaw_version,
    check_weixin_plugin,
    doctor_exit_code,
    run_doctor,
)


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


def _fail(stderr: str = "boom", returncode: int = 1) -> CommandResult:
    return CommandResult(ok=False, returncode=returncode, stderr=stderr)


def _runner_for(argv_prefix: tuple[str, ...], result: CommandResult) -> FakeRunner:
    return FakeRunner([(argv_prefix, result)])


class TestNodeVersion(unittest.TestCase):
    def _check(self, stdout: str):
        return check_node_version(_runner_for(("node", "-v"), _ok(stdout)))

    def test_supported_versions(self) -> None:
        for version in ("v24.16.0", "v24.19.2", "v26.1.0", "v26.5.0", "v28.2.0"):
            with self.subTest(version=version):
                self.assertTrue(self._check(f"{version}\n").ok)

    def test_unsupported_versions(self) -> None:
        for version in ("v22.10.0", "v23.5.0", "v24.15.9", "v25.1.0", "v26.0.9"):
            with self.subTest(version=version):
                check = self._check(f"{version}\n")
                self.assertFalse(check.ok)
                self.assertEqual(check.severity, SEVERITY_ERROR)

    def test_node_missing(self) -> None:
        check = check_node_version(
            _runner_for(("node",), _fail("command not found: node", 127))
        )
        self.assertFalse(check.ok)
        self.assertEqual(check.severity, SEVERITY_ERROR)

    def test_unparsable_output(self) -> None:
        check = self._check("garbage\n")
        self.assertFalse(check.ok)
        self.assertEqual(check.severity, SEVERITY_ERROR)


class TestLinger(unittest.TestCase):
    def test_enabled(self) -> None:
        check = check_linger(_runner_for(("loginctl",), _ok("Linger=yes\n")))
        self.assertTrue(check.ok)

    def test_disabled_is_error(self) -> None:
        check = check_linger(_runner_for(("loginctl",), _ok("Linger=no\n")))
        self.assertFalse(check.ok)
        self.assertEqual(check.severity, SEVERITY_ERROR)
        self.assertIn("enable-linger", check.hint)

    def test_indeterminate_is_warning_only(self) -> None:
        check = check_linger(_runner_for(("loginctl",), _fail("no dbus")))
        self.assertFalse(check.ok)
        self.assertEqual(check.severity, SEVERITY_WARNING)
        self.assertEqual(doctor_exit_code([check]), 0)


class TestGatewayPort(unittest.TestCase):
    def test_listening(self) -> None:
        check = check_gateway_port(connect=lambda host, port: True)
        self.assertTrue(check.ok)
        self.assertIn("18789", check.detail)

    def test_down_is_error(self) -> None:
        check = check_gateway_port(connect=lambda host, port: False)
        self.assertFalse(check.ok)
        self.assertEqual(check.severity, SEVERITY_ERROR)
        self.assertEqual(doctor_exit_code([check]), 1)


class TestNblaneMcpRegistered(unittest.TestCase):
    def test_registered_json_list(self) -> None:
        runner = _runner_for(
            ("openclaw", "mcp", "list"), _ok(json.dumps([{"name": "nblane"}]))
        )
        self.assertTrue(check_nblane_mcp_registered(runner).ok)

    def test_registered_json_mapping(self) -> None:
        runner = _runner_for(
            ("openclaw", "mcp", "list"),
            _ok(json.dumps({"servers": [{"name": "nblane"}]})),
        )
        self.assertTrue(check_nblane_mcp_registered(runner).ok)

    def test_registered_top_level_servers_mapping(self) -> None:
        # OpenClaw 2026.9: `mcp list --json` prints the servers mapping
        # directly, e.g. {"nblane": {"command": ...}}.
        runner = _runner_for(
            ("openclaw", "mcp", "list"),
            _ok(json.dumps({"nblane": {"command": "/venv/bin/nblane-mcp"}})),
        )
        self.assertTrue(check_nblane_mcp_registered(runner).ok)

    def test_missing(self) -> None:
        runner = _runner_for(
            ("openclaw", "mcp", "list"), _ok(json.dumps([{"name": "other"}]))
        )
        check = check_nblane_mcp_registered(runner)
        self.assertFalse(check.ok)
        self.assertEqual(check.severity, SEVERITY_ERROR)

    def test_text_fallback_when_json_unsupported(self) -> None:
        runner = _runner_for(
            ("openclaw", "mcp", "list"), _ok("NAME    TRANSPORT\nnblane  stdio\n")
        )
        check = check_nblane_mcp_registered(runner)
        self.assertTrue(check.ok)
        self.assertIn("降级", check.detail)

    def test_text_fallback_miss(self) -> None:
        runner = _runner_for(("openclaw", "mcp", "list"), _ok("other  stdio\n"))
        self.assertFalse(check_nblane_mcp_registered(runner).ok)

    def test_cli_failure(self) -> None:
        runner = _runner_for(("openclaw",), _fail())
        self.assertFalse(check_nblane_mcp_registered(runner).ok)


class TestOpenclawVersion(unittest.TestCase):
    def test_parses_version(self) -> None:
        runner = _runner_for(("openclaw", "--version"), _ok("OpenClaw 2026.9.4\n"))
        check = check_openclaw_version(runner)
        self.assertTrue(check.ok)
        self.assertIn("2026.9.4", check.detail)

    def test_cli_missing(self) -> None:
        runner = _runner_for(
            ("openclaw",), _fail("command not found: openclaw", 127)
        )
        check = check_openclaw_version(runner)
        self.assertFalse(check.ok)
        self.assertEqual(check.severity, SEVERITY_ERROR)


class TestWeixinPlugin(unittest.TestCase):
    def _check(self, stdout: str):
        return check_weixin_plugin(
            _runner_for(("openclaw", "plugins", "list"), _ok(stdout))
        )

    def test_enabled(self) -> None:
        self.assertTrue(self._check("openclaw-weixin  1.2.3  enabled\n").ok)

    def test_disabled_is_error(self) -> None:
        check = self._check("openclaw-weixin  1.2.3  disabled\n")
        self.assertFalse(check.ok)
        self.assertEqual(check.severity, SEVERITY_ERROR)

    def test_not_installed(self) -> None:
        check = self._check("some-other-plugin  0.1.0  enabled\n")
        self.assertFalse(check.ok)
        self.assertEqual(check.severity, SEVERITY_ERROR)
        self.assertIn("plugins install", check.hint)

    def test_ambiguous_state_is_warning(self) -> None:
        check = self._check("openclaw-weixin\n")
        self.assertFalse(check.ok)
        self.assertEqual(check.severity, SEVERITY_WARNING)

    def test_cli_failure(self) -> None:
        check = check_weixin_plugin(_runner_for(("openclaw",), _fail()))
        self.assertFalse(check.ok)


_DECLARATION = """\
version: 1
defaults:
  tz: Asia/Shanghai
  session: isolated
automations:
  - key: nblane:daily-plan
    name: 每日计划
    cron: "30 8 * * *"
    prompt: prompts/daily-plan.md
"""

_PROMPT = "# 每日计划\n\n读 profile://kanban。\n"


def _declaration_tree(root: Path, yaml_text: str = _DECLARATION) -> Path:
    assistant = root / "assistant"
    (assistant / "prompts").mkdir(parents=True, exist_ok=True)
    (assistant / "prompts" / "daily-plan.md").write_text(
        _PROMPT, encoding="utf-8"
    )
    path = assistant / "automations.yaml"
    path.write_text(yaml_text, encoding="utf-8")
    return path


def _matching_live() -> list[dict]:
    return [
        {
            "name": "每日计划",
            "declarationKey": "nblane:daily-plan",
            "schedule": {"cron": "30 8 * * *", "tz": "Asia/Shanghai"},
            "session": "isolated",
            "delivery": "none",
            "model": "",
            "fallbacks": [],
            "message": _PROMPT,
        }
    ]


class TestAutomationsInSync(unittest.TestCase):
    def test_no_profile_skips(self) -> None:
        check = check_automations_in_sync(FakeRunner([]))
        self.assertTrue(check.ok)
        self.assertEqual(check.severity, SEVERITY_INFO)

    def test_missing_file_skips(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            check = check_automations_in_sync(
                FakeRunner([]),
                profile_name="alice",
                automations_path=Path(tmp) / "automations.yaml",
            )
        self.assertTrue(check.ok)
        self.assertEqual(check.severity, SEVERITY_INFO)

    def test_in_sync(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _declaration_tree(Path(tmp))
            check = check_automations_in_sync(
                FakeRunner([]),
                profile_name="alice",
                automations_path=path,
                live_jobs=_matching_live(),
            )
        self.assertTrue(check.ok)

    def test_drift_is_error(self) -> None:
        live = _matching_live()
        live[0]["schedule"] = {"cron": "0 9 * * *", "tz": "Asia/Shanghai"}
        with tempfile.TemporaryDirectory() as tmp:
            path = _declaration_tree(Path(tmp))
            check = check_automations_in_sync(
                FakeRunner([]),
                profile_name="alice",
                automations_path=path,
                live_jobs=live,
            )
        self.assertFalse(check.ok)
        self.assertEqual(check.severity, SEVERITY_ERROR)
        self.assertIn("automations sync", check.hint)

    def test_prune_only_is_warning(self) -> None:
        live = _matching_live() + [
            {"declarationKey": "nblane:stale", "name": "旧任务"}
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = _declaration_tree(Path(tmp))
            check = check_automations_in_sync(
                FakeRunner([]),
                profile_name="alice",
                automations_path=path,
                live_jobs=live,
            )
        self.assertFalse(check.ok)
        self.assertEqual(check.severity, SEVERITY_WARNING)
        self.assertEqual(doctor_exit_code([check]), 0)

    def test_invalid_declaration_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _declaration_tree(
                Path(tmp), yaml_text="version: 99\nautomations: []\n"
            )
            check = check_automations_in_sync(
                FakeRunner([]),
                profile_name="alice",
                automations_path=path,
                live_jobs=[],
            )
        self.assertFalse(check.ok)
        self.assertEqual(check.severity, SEVERITY_ERROR)

    def test_fetch_failure_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _declaration_tree(Path(tmp))
            check = check_automations_in_sync(
                _runner_for(("openclaw",), _fail()),
                profile_name="alice",
                automations_path=path,
            )
        self.assertFalse(check.ok)
        self.assertEqual(check.severity, SEVERITY_ERROR)


class TestBackupSchedule(unittest.TestCase):
    def test_backup_job_present(self) -> None:
        live = [
            {
                "declarationKey": "system:backup-daily",
                "name": "backup",
                "schedule": {"every": "24h"},
            }
        ]
        check = check_backup_schedule(FakeRunner([]), live_jobs=live)
        self.assertTrue(check.ok)

    def test_backup_job_present_new_cli_shape(self) -> None:
        # OpenClaw 2026.9: schedule is {"kind": "every", "everyMs": ...}.
        live = [
            {
                "declarationKey": "openclaw-backup-scheduled",
                "name": "openclaw-backup-scheduled",
                "schedule": {"kind": "every", "everyMs": 86400000},
            }
        ]
        check = check_backup_schedule(FakeRunner([]), live_jobs=live)
        self.assertTrue(check.ok)

    def test_backup_job_missing_is_error(self) -> None:
        check = check_backup_schedule(
            FakeRunner([]), live_jobs=[{"declarationKey": "nblane:daily-plan"}]
        )
        self.assertFalse(check.ok)
        self.assertEqual(check.severity, SEVERITY_ERROR)
        self.assertIn("backup enable", check.hint)

    def test_unscheduled_backup_mention_does_not_count(self) -> None:
        # A one-shot job that merely mentions "backup" is not the schedule.
        live = [{"declarationKey": "system:backup-notes"}]
        check = check_backup_schedule(FakeRunner([]), live_jobs=live)
        self.assertFalse(check.ok)
        self.assertEqual(check.severity, SEVERITY_ERROR)

    def test_scheduled_job_without_backup_identifier_does_not_count(self) -> None:
        live = [
            {
                "declarationKey": "nblane:daily-plan",
                "schedule": {"cron": "30 8 * * *"},
            }
        ]
        check = check_backup_schedule(FakeRunner([]), live_jobs=live)
        self.assertFalse(check.ok)
        self.assertEqual(check.severity, SEVERITY_ERROR)

    def test_substring_inside_a_word_does_not_count(self) -> None:
        # "backup" glued into a longer token (no segment boundary).
        live = [
            {
                "declarationKey": "nblane:mybackups",
                "schedule": {"cron": "0 3 * * *"},
            }
        ]
        check = check_backup_schedule(FakeRunner([]), live_jobs=live)
        self.assertFalse(check.ok)

    def test_fetch_failure_is_error(self) -> None:
        check = check_backup_schedule(_runner_for(("openclaw",), _fail()))
        self.assertFalse(check.ok)
        self.assertEqual(check.severity, SEVERITY_ERROR)


class TestRunDoctor(unittest.TestCase):
    def _all_green_runner(self) -> FakeRunner:
        return FakeRunner(
            [
                (("openclaw", "--version"), _ok("OpenClaw 2026.9.4\n")),
                (("node", "-v"), _ok("v24.16.2\n")),
                (("loginctl",), _ok("Linger=yes\n")),
                (
                    ("openclaw", "mcp", "list"),
                    _ok(json.dumps([{"name": "nblane"}])),
                ),
                (
                    ("openclaw", "plugins", "list"),
                    _ok("openclaw-weixin  1.2.3  enabled\n"),
                ),
                (
                    ("openclaw", "automations", "list"),
                    _ok(
                        json.dumps(
                            [
                                {
                                    "declarationKey": "system:backup-daily",
                                    "schedule": {"every": "24h"},
                                }
                            ]
                        )
                    ),
                ),
            ]
        )

    def test_all_green(self) -> None:
        runner = self._all_green_runner()
        checks = run_doctor(runner=runner, connect=lambda host, port: True)
        self.assertTrue(all(check.ok for check in checks))
        self.assertEqual(doctor_exit_code(checks), 0)
        # Red line: doctor must never invoke `openclaw doctor` (it restarts
        # the gateway) or any mutating automations command.
        for call in runner.calls:
            self.assertNotEqual(call[:2], ["openclaw", "doctor"])
            if call[:2] == ["openclaw", "automations"]:
                self.assertEqual(call[2], "list")

    def test_error_fails_exit_code(self) -> None:
        runner = self._all_green_runner()
        runner.responses = [
            (("node", "-v"), _ok("v22.10.0\n")),
            *runner.responses[1:],
        ]
        checks = run_doctor(runner=runner, connect=lambda host, port: True)
        self.assertEqual(doctor_exit_code(checks), 1)
        node = next(check for check in checks if check.id == "node_version")
        self.assertFalse(node.ok)

    def test_warnings_do_not_fail_exit_code(self) -> None:
        runner = self._all_green_runner()
        runner.responses = [
            *runner.responses[:2],
            (("loginctl",), _fail("no dbus")),
            *runner.responses[3:],
        ]
        checks = run_doctor(runner=runner, connect=lambda host, port: True)
        linger = next(check for check in checks if check.id == "linger")
        self.assertFalse(linger.ok)
        self.assertEqual(linger.severity, SEVERITY_WARNING)
        self.assertEqual(doctor_exit_code(checks), 0)


if __name__ == "__main__":
    unittest.main()
