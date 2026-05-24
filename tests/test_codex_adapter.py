"""Tests for optional Codex CLI / Codex Cloud integration."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nblane.commands.codex import cmd_codex_install
from nblane.core import codex_adapter
from nblane.core.agent_tasks import (
    create_agent_task,
    load_agent_tasks,
    update_agent_task_remote,
)
from nblane.core.codex_adapter import (
    CodexCommandResult,
    CodexConfig,
    codex_auth_path,
    codex_cli_config_path,
    codex_home,
    codex_status,
    current_config,
    install_codex,
    load_codex_cli_config_text,
    load_profile_config,
    login_with_api_key,
    parse_cloud_task_id,
    parse_diff_changed_paths,
    readable_codex_error,
    profile_codex_home,
    profile_config_template,
    refresh_codex_cloud_task,
    run_local_codex_task,
    run_readonly_codex_prompt,
    save_codex_cli_config_text,
    save_profile_config,
    save_profile_config_text,
    submit_codex_cloud_task,
    validate_codex_cli_config_text,
    validate_profile_config_text,
)


class _Completed:
    """Small subprocess.CompletedProcess stand-in."""

    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class TestCodexAdapter(unittest.TestCase):
    """Codex Cloud stays optional and candidate-first."""

    def test_status_reports_missing_codex(self) -> None:
        """Missing Codex binary is a typed not-installed state."""

        with patch("nblane.core.codex_adapter.shutil.which", return_value=""):
            status = codex_status(CodexConfig(cloud_env_id="env_1"))

        self.assertFalse(status.installed)
        self.assertEqual(status.error, "codex_not_found")
        self.assertTrue(status.cloud_env_configured)
        self.assertIn("@openai/codex", status.install_command)

    def test_status_reports_version_and_login(self) -> None:
        """Installed Codex status includes version and login readiness."""

        with (
            patch("nblane.core.codex_adapter.shutil.which", return_value="/bin/codex"),
            patch(
                "nblane.core.codex_adapter.subprocess.run",
                side_effect=[
                    _Completed(stdout="codex-cli 1.2.3\n"),
                    _Completed(stdout="Logged in using an API key - sk-test123456\n"),
                ],
            ),
        ):
            status = codex_status(CodexConfig(cloud_env_id="env_1"))

        self.assertTrue(status.installed)
        self.assertEqual(status.version, "codex-cli 1.2.3")
        self.assertTrue(status.logged_in)
        self.assertIn("sk-test***", status.login_status)

    def test_install_requires_npm(self) -> None:
        """Install reports an actionable error when npm is missing."""

        with patch("nblane.core.codex_adapter.shutil.which", return_value=""):
            result = install_codex()

        self.assertFalse(result.ok)
        self.assertEqual(result.returncode, 127)
        self.assertIn("npm_not_found", result.error)

    def test_cli_install_print_command_does_not_execute(self) -> None:
        """The CLI print-command mode is a safe dry path."""

        with (
            patch("builtins.print") as mocked_print,
            patch("nblane.commands.codex.install_codex") as mocked_install,
        ):
            cmd_codex_install(print_command=True)

        mocked_install.assert_not_called()
        mocked_print.assert_called_with("npm i -g @openai/codex")

    def test_codex_cli_paths_follow_codex_home(self) -> None:
        """Codex CLI config/auth paths are resolved from CODEX_HOME."""

        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict("os.environ", {"CODEX_HOME": tmp}):
                self.assertEqual(codex_home(), Path(tmp))
                self.assertEqual(codex_cli_config_path(), Path(tmp) / "config.toml")
                self.assertEqual(codex_auth_path(), Path(tmp) / "auth.json")

    def test_profile_codex_home_is_stable_and_profile_isolated(self) -> None:
        """Web Codex homes live outside profiles/<name> and differ by profile."""

        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict("os.environ", {"NBLANE_CODEX_HOME_ROOT": tmp}):
                alice = profile_codex_home("Alice Smith")
                alice_again = profile_codex_home("Alice Smith")
                bob = profile_codex_home("Bob Smith")

        self.assertEqual(alice, alice_again)
        self.assertEqual(alice.parent, Path(tmp))
        self.assertTrue(alice.name.startswith("alice-smith-"))
        self.assertNotEqual(alice, bob)

    def test_current_config_uses_service_codex_home_by_default(self) -> None:
        """Profiles keep config preferences but share the service Codex home."""

        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch.dict(
                    "os.environ",
                    {
                        "CODEX_HOME": str(Path(tmp) / "global"),
                        "NBLANE_CODEX_HOME_ROOT": str(Path(tmp) / "web"),
                    },
                ),
            ):
                self.assertEqual(codex_home(), Path(tmp) / "global")
                self.assertEqual(
                    Path(current_config(include_runtime=False).codex_home),
                    Path(tmp) / "global",
                )
                cfg = current_config(profile="alice", include_runtime=False)
                isolated = current_config(
                    profile="alice",
                    include_runtime=False,
                    codex_home_policy="profile",
                )
                expected = profile_codex_home("alice")

        self.assertEqual(Path(cfg.codex_home), Path(tmp) / "global")
        self.assertEqual(Path(isolated.codex_home), expected)
        self.assertIn("alice-", Path(isolated.codex_home).name)

    def test_missing_codex_cli_config_loads_valid_template(self) -> None:
        """A missing config.toml starts from a valid editable TOML template."""

        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict("os.environ", {"CODEX_HOME": tmp}):
                text = load_codex_cli_config_text()
                parsed = validate_codex_cli_config_text(text)

        self.assertIsInstance(parsed, dict)
        self.assertIn("Codex CLI config", text)

    def test_save_codex_cli_config_preserves_raw_text_and_backs_up(self) -> None:
        """Raw config.toml editor keeps comments and creates a local backup."""

        original = "# old\nmodel = \"gpt-4o\"\n"
        edited = "# keep\nmodel = \"gpt-5.1-codex\""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.toml"
            path.write_text(original, encoding="utf-8")
            with patch.dict("os.environ", {"CODEX_HOME": tmp}):
                saved = save_codex_cli_config_text(edited)
                backup = Path(tmp) / "config.toml.nblane.bak"

            saved_text = saved.read_text(encoding="utf-8")
            backup_text = backup.read_text(encoding="utf-8")

        self.assertEqual(saved_text, edited + "\n")
        self.assertEqual(backup_text, original)

    def test_invalid_codex_cli_config_does_not_overwrite(self) -> None:
        """Invalid TOML is rejected before touching config.toml."""

        original = "model = \"gpt-4o\"\n"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.toml"
            path.write_text(original, encoding="utf-8")
            with patch.dict("os.environ", {"CODEX_HOME": tmp}):
                with self.assertRaises(ValueError):
                    save_codex_cli_config_text("model = [")
                current = path.read_text(encoding="utf-8")

        self.assertEqual(current, original)

    def test_login_with_api_key_uses_stdin_and_sanitizes_result(self) -> None:
        """API keys are passed through stdin, not command args or output."""

        secret = "sk-test123456789"
        with (
            patch("nblane.core.codex_adapter.shutil.which", return_value="/bin/codex"),
            patch(
                "nblane.core.codex_adapter.subprocess.run",
                return_value=_Completed(stdout=f"Logged in with {secret}\n"),
            ) as run,
        ):
            result = login_with_api_key(
                secret,
                config=CodexConfig(timeout_seconds=12),
            )

        args = run.call_args.args[0]
        kwargs = run.call_args.kwargs
        self.assertTrue(result.ok)
        self.assertEqual(args, ["/bin/codex", "login", "--with-api-key"])
        self.assertEqual(kwargs["input"], f"{secret}\n")
        self.assertNotIn(secret, result.output)
        self.assertNotIn(secret, result.command)

    def test_login_with_profile_config_uses_service_codex_home_env(self) -> None:
        """Web login writes to the shared service-level Codex home."""

        secret = "sk-test123456789"
        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch.dict(
                    "os.environ",
                    {
                        "NBLANE_CODEX_HOME": str(Path(tmp) / "service"),
                        "NBLANE_CODEX_HOME_ROOT": str(Path(tmp) / "profiles"),
                    },
                ),
                patch("nblane.core.codex_adapter.shutil.which", return_value="/bin/codex"),
                patch(
                    "nblane.core.codex_adapter.subprocess.run",
                    return_value=_Completed(stdout=f"Logged in with {secret}\n"),
                ) as run,
            ):
                cfg = current_config(profile="alice", include_runtime=False)
                expected = Path(tmp) / "service"
                result = login_with_api_key(secret, config=cfg)

        kwargs = run.call_args.kwargs
        self.assertTrue(result.ok)
        self.assertEqual(kwargs["input"], f"{secret}\n")
        self.assertEqual(kwargs["env"]["CODEX_HOME"], str(expected))
        self.assertNotIn(secret, run.call_args.args[0])

    def test_codex_status_uses_service_codex_home_env(self) -> None:
        """Status probes run against the shared service-level Codex home."""

        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch.dict(
                    "os.environ",
                    {
                        "NBLANE_CODEX_HOME": str(Path(tmp) / "service"),
                        "NBLANE_CODEX_HOME_ROOT": str(Path(tmp) / "profiles"),
                    },
                ),
                patch("nblane.core.codex_adapter.shutil.which", return_value="/bin/codex"),
                patch(
                    "nblane.core.codex_adapter.subprocess.run",
                    side_effect=[
                        _Completed(stdout="codex-cli 1.2.3\n"),
                        _Completed(stdout="Logged in\n"),
                    ],
                ) as run,
            ):
                expected = Path(tmp) / "service"
                status = codex_status(current_config(profile="alice", include_runtime=False))

        self.assertTrue(status.installed)
        for call in run.call_args_list:
            self.assertEqual(
                call.kwargs["env"]["CODEX_HOME"],
                str(expected),
            )

    def test_profile_cli_config_text_uses_service_codex_home_by_default(self) -> None:
        """Web config.toml editor reads and writes the shared Codex home."""

        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(
                "os.environ",
                {
                    "NBLANE_CODEX_HOME": str(Path(tmp) / "service"),
                    "NBLANE_CODEX_HOME_ROOT": str(Path(tmp) / "profiles"),
                },
            ):
                saved = save_codex_cli_config_text(
                    'model = "gpt-5.1-codex"',
                    profile="alice",
                )
                expected = Path(tmp) / "service" / "config.toml"
                loaded = load_codex_cli_config_text(profile="alice")
                bob_path = codex_cli_config_path(profile="bob")

        self.assertEqual(saved, expected)
        self.assertEqual(loaded, 'model = "gpt-5.1-codex"\n')
        self.assertEqual(bob_path, expected)

    def test_profile_cli_config_text_can_use_legacy_profile_codex_home(self) -> None:
        """The old profile-isolated Codex home remains available explicitly."""

        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict("os.environ", {"NBLANE_CODEX_HOME_ROOT": tmp}):
                saved = save_codex_cli_config_text(
                    'model = "gpt-5.1-codex"',
                    profile="alice",
                    codex_home_policy="profile",
                )
                expected = profile_codex_home("alice") / "config.toml"
                loaded = load_codex_cli_config_text(
                    profile="alice",
                    codex_home_policy="profile",
                )
                bob_path = codex_cli_config_path(
                    profile="bob",
                    codex_home_policy="profile",
                )

        self.assertEqual(saved, expected)
        self.assertEqual(loaded, 'model = "gpt-5.1-codex"\n')
        self.assertFalse(bob_path.exists())

    def test_submit_codex_cloud_task_records_remote_metadata(self) -> None:
        """Cloud submit stores task id under remote metadata."""

        with tempfile.TemporaryDirectory() as tmp:
            pdir = Path(tmp) / "alice"
            pdir.mkdir()
            with patch("nblane.core.agent_tasks.profile_dir", lambda _name: pdir):
                task = create_agent_task(
                    "alice",
                    target_harness="codex",
                    role="remote_dev",
                    title="Patch gateway",
                    input_refs=["kanban:task_1"],
                    expected_outputs=["patch_review"],
                )
                with (
                    patch(
                        "nblane.core.codex_adapter.shutil.which",
                        return_value="/bin/codex",
                    ),
                    patch(
                        "nblane.core.codex_adapter.subprocess.run",
                        return_value=_Completed(stdout="Task id: task_abc123456\n"),
                    ),
                ):
                    result = submit_codex_cloud_task(
                        "alice",
                        task["id"],
                        config=CodexConfig(cloud_env_id="env_1", attempts=2),
                    )
                loaded = load_agent_tasks("alice")["tasks"][0]

        self.assertTrue(result.ok)
        self.assertEqual(result.cloud_task_id, "task_abc123456")
        self.assertEqual(loaded["status"], "running")
        self.assertEqual(loaded["remote"]["provider"], "codex_cloud")
        self.assertEqual(loaded["remote"]["attempts"], 2)

    def test_profile_config_overrides_env_for_submit(self) -> None:
        """Profile codex.yaml can provide its own Codex Cloud env."""

        with tempfile.TemporaryDirectory() as tmp:
            pdir = Path(tmp) / "alice"
            pdir.mkdir()
            with (
                patch("nblane.core.agent_tasks.profile_dir", lambda _name: pdir),
                patch("nblane.core.codex_adapter.profile_dir", lambda _name: pdir),
                patch.dict("os.environ", {"NBLANE_CODEX_CLOUD_ENV_ID": ""}),
            ):
                save_profile_config(
                    "alice",
                    CodexConfig(cloud_env_id="env_profile", attempts=3),
                )
                cfg = current_config(profile="alice")
                task = create_agent_task(
                    "alice",
                    target_harness="codex",
                    role="remote_dev",
                    title="Patch gateway",
                )
                with (
                    patch(
                        "nblane.core.codex_adapter.shutil.which",
                        return_value="/bin/codex",
                    ),
                    patch(
                        "nblane.core.codex_adapter.subprocess.run",
                        return_value=_Completed(stdout="Task id: task_profile\n"),
                    ) as run,
                ):
                    result = submit_codex_cloud_task("alice", task["id"])
                stored = load_profile_config("alice")

        self.assertEqual(cfg.cloud_env_id, "env_profile")
        self.assertEqual(cfg.attempts, 3)
        self.assertTrue(result.ok)
        self.assertEqual(stored["codex"]["cloud_env_id"], "env_profile")
        args = run.call_args.args[0]
        self.assertIn("env_profile", args)
        self.assertIn("3", args)

    def test_readonly_codex_prompt_uses_readonly_ephemeral_exec(self) -> None:
        """Read-only Codex helper returns text without worktree/diff behavior."""

        captured: dict[str, object] = {}

        def fake_run(args, *, timeout, cwd=None, stdin=None, env=None):
            command = " ".join(str(arg) for arg in args)
            captured["args"] = list(args)
            captured["stdin"] = stdin
            captured["timeout"] = timeout
            captured["env"] = dict(env or {})
            output_path = Path(args[args.index("--output-last-message") + 1])
            output_path.write_text('{"evidence_summary": ["ok"]}', encoding="utf-8")
            return CodexCommandResult(True, command, 0, stdout="events\n")

        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch("nblane.core.codex_adapter.shutil.which", return_value="/bin/codex"),
                patch("nblane.core.codex_adapter._run", side_effect=fake_run),
            ):
                result = run_readonly_codex_prompt(
                    "alice",
                    "Summarize this kanban task.",
                    config=CodexConfig(timeout_seconds=33, codex_home=tmp),
                )

        args = captured["args"]
        self.assertTrue(result.ok)
        self.assertEqual(result.output, '{"evidence_summary": ["ok"]}')
        self.assertEqual(captured["stdin"], "Summarize this kanban task.")
        self.assertEqual(captured["timeout"], 33)
        self.assertIn("--ephemeral", args)
        self.assertIn("--sandbox", args)
        self.assertEqual(args[args.index("--sandbox") + 1], "read-only")
        self.assertNotIn("worktree", " ".join(map(str, args)))
        self.assertEqual(captured["env"].get("CODEX_HOME"), tmp)

    def test_readonly_codex_prompt_can_enable_search_and_xhigh_reasoning(self) -> None:
        """Paper search can opt into native Codex web search and deeper reasoning."""

        captured: dict[str, object] = {}

        def fake_run(args, *, timeout, cwd=None, stdin=None, env=None):
            command = " ".join(str(arg) for arg in args)
            captured["args"] = list(args)
            output_path = Path(args[args.index("--output-last-message") + 1])
            output_path.write_text('{"ok": true}', encoding="utf-8")
            return CodexCommandResult(True, command, 0)

        with (
            patch("nblane.core.codex_adapter.shutil.which", return_value="/bin/codex"),
            patch("nblane.core.codex_adapter._run", side_effect=fake_run),
        ):
            result = run_readonly_codex_prompt(
                "alice",
                "Search for papers.",
                config=CodexConfig(),
                enable_search=True,
                reasoning_effort="xhigh",
            )

        args = captured["args"]
        self.assertTrue(result.ok)
        self.assertEqual(args[:3], ["/bin/codex", "--search", "exec"])
        self.assertIn("model_reasoning_effort=\"xhigh\"", args)

    def test_streaming_run_reports_output_progress(self) -> None:
        """Long Codex helpers can surface process output before completion."""

        events: list[dict[str, object]] = []

        result = codex_adapter._run_streaming(
            [
                "/bin/sh",
                "-c",
                "printf 'web search: VLA steering\\n' >&2; "
                "printf '{\"query\":\"VLA steering\",\"results\":[]}\\n'; "
                "printf 'two\\n' >&2",
            ],
            timeout=5,
            progress_callback=events.append,
        )

        self.assertTrue(result.ok)
        self.assertIn('"results"', result.stdout)
        self.assertIn("two", result.stderr)
        self.assertTrue(any(event.get("event") == "output" for event in events))
        self.assertTrue(any(event.get("output_kind") == "web_search" for event in events))
        self.assertTrue(any(event.get("output_kind") == "structured_result" for event in events))
        self.assertFalse(any(event.get("stream") == "stderr" and "web search:" in event.get("message", "") for event in events))
        self.assertTrue(any(event.get("event") == "command_finished" for event in events))

    def test_streaming_run_hides_codex_prompt_echo_noise(self) -> None:
        """Prompt echoes and setup noise should not dominate Paper Library progress."""

        events: list[dict[str, object]] = []

        result = codex_adapter._run_streaming(
            [
                "/bin/sh",
                "-c",
                "printf 'You are the nblane AI Gateway.\\n' >&2; "
                "printf '}\\n' >&2; "
                "printf 'warning: Codex could not find bubblewrap on PATH\\n' >&2; "
                "printf 'fatal: early EOF git_binary=\"git\"\\n' >&2; "
                "printf 'web search: https://arxiv.org/abs/2605.13403\\n' >&2",
            ],
            timeout=5,
            progress_callback=events.append,
        )

        self.assertTrue(result.ok)
        visible_messages = [event.get("message", "") for event in events if event.get("visible") is not False]
        self.assertFalse(any("You are the nblane AI Gateway" in message for message in visible_messages))
        self.assertFalse(any(message == "}" for message in visible_messages))
        self.assertFalse(any("bubblewrap" in message for message in visible_messages))
        self.assertTrue(any(event.get("output_kind") == "plugin_warning" for event in events))
        self.assertTrue(any(event.get("output_kind") == "web_search" for event in events))

    def test_streaming_run_can_cancel_process(self) -> None:
        """Cancellation requests stop a running Codex process."""

        result = codex_adapter._run_streaming(
            ["/bin/sh", "-c", "sleep 5"],
            timeout=10,
            cancel_check=lambda: True,
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.error, "command_cancelled")

    def test_readable_codex_error_prefers_provider_error_json(self) -> None:
        """Codex stderr banners should not hide the actual provider error."""

        message = readable_codex_error(
            "",
            "\n".join(
                [
                    "OpenAI Codex v0.131.0-alpha.9",
                    "--------",
                    "workdir: /home/ubuntu/nblane",
                    "model: qwen-plus",
                    'ERROR: {"error":"端点/codex未配置模型qwen-plus"}',
                ]
            ),
            "",
            "",
        )

        self.assertEqual(message, "端点/codex未配置模型qwen-plus")

    def test_readable_codex_error_prefers_timeout_over_plugin_warning(self) -> None:
        """Remote plugin warnings should not hide the real timeout cause."""

        message = readable_codex_error(
            "command_timeout: exceeded 60s",
            "authentication required to sync remote plugins; api key auth is not supported",
        )

        self.assertEqual(message, "command_timeout: exceeded 60s")

    def test_profile_config_template_is_valid_yaml(self) -> None:
        """Missing codex.yaml can start from a valid editable template."""

        text = profile_config_template("alice")
        parsed = validate_profile_config_text(text)

        self.assertEqual(parsed["profile"], "alice")
        self.assertIn("codex", parsed)
        self.assertEqual(parsed["codex"]["bin_path"], "codex")

    def test_save_profile_config_text_preserves_raw_document(self) -> None:
        """Raw editor saves comments and profile overrides without reformatting."""

        body = (
            "# keep this comment\n"
            "schema_version: '1.0'\n"
            "profile: alice\n"
            "codex:\n"
            "  cloud_env_id: env_raw\n"
            "  attempts: 5\n"
            "  timeout_seconds: 250\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            pdir = Path(tmp) / "alice"
            pdir.mkdir()
            with patch("nblane.core.codex_adapter.profile_dir", lambda _name: pdir):
                saved = save_profile_config_text("alice", body.rstrip("\n"))
                cfg = current_config(profile="alice", include_runtime=False)
                raw = saved.read_text(encoding="utf-8")

        self.assertEqual(cfg.cloud_env_id, "env_raw")
        self.assertEqual(cfg.attempts, 5)
        self.assertEqual(cfg.timeout_seconds, 250.0)
        self.assertEqual(raw, body)

    def test_invalid_profile_config_text_does_not_overwrite_existing_file(self) -> None:
        """Invalid raw editor saves are rejected before touching disk."""

        original = "codex:\n  cloud_env_id: env_original\n"
        with tempfile.TemporaryDirectory() as tmp:
            pdir = Path(tmp) / "alice"
            pdir.mkdir()
            path = pdir / "codex.yaml"
            path.write_text(original, encoding="utf-8")
            with patch("nblane.core.codex_adapter.profile_dir", lambda _name: pdir):
                with self.assertRaises(ValueError):
                    save_profile_config_text("alice", "codex: [")
                with self.assertRaises(ValueError):
                    save_profile_config_text("alice", "- not-a-mapping\n")
                with self.assertRaises(ValueError):
                    save_profile_config_text("alice", "codex: nope\n")

            current = path.read_text(encoding="utf-8")

        self.assertEqual(current, original)

    def test_profile_config_text_rejects_secret_like_keys(self) -> None:
        """Profile codex.yaml must not store CLI auth or API tokens."""

        with self.assertRaises(ValueError):
            validate_profile_config_text(
                "codex:\n"
                "  cloud_env_id: env_safe\n"
                "  api_key: sk-nope\n"
            )

    def test_missing_profile_config_inherits_env_defaults(self) -> None:
        """Absent profile codex.yaml should not mask global env defaults."""

        with tempfile.TemporaryDirectory() as tmp:
            pdir = Path(tmp) / "alice"
            pdir.mkdir()
            with (
                patch("nblane.core.codex_adapter.profile_dir", lambda _name: pdir),
                patch.dict(
                    "os.environ",
                    {
                        "NBLANE_CODEX_ATTEMPTS": "4",
                        "NBLANE_CODEX_TIMEOUT_SECONDS": "240",
                    },
                ),
            ):
                cfg = current_config(profile="alice", include_runtime=False)

        self.assertEqual(cfg.attempts, 4)
        self.assertEqual(cfg.timeout_seconds, 240.0)

    def test_partial_profile_config_only_overrides_present_fields(self) -> None:
        """A profile file can override one Codex field while inheriting others."""

        with tempfile.TemporaryDirectory() as tmp:
            pdir = Path(tmp) / "alice"
            pdir.mkdir()
            (pdir / "codex.yaml").write_text(
                "codex:\n  cloud_env_id: env_profile\n",
                encoding="utf-8",
            )
            with (
                patch("nblane.core.codex_adapter.profile_dir", lambda _name: pdir),
                patch.dict(
                    "os.environ",
                    {
                        "NBLANE_CODEX_CLOUD_ENV_ID": "env_global",
                        "NBLANE_CODEX_ATTEMPTS": "4",
                        "NBLANE_CODEX_TIMEOUT_SECONDS": "240",
                    },
                ),
            ):
                cfg = current_config(profile="alice", include_runtime=False)

        self.assertEqual(cfg.cloud_env_id, "env_profile")
        self.assertEqual(cfg.attempts, 4)
        self.assertEqual(cfg.timeout_seconds, 240.0)

    def test_submit_requires_cloud_env_id(self) -> None:
        """Cloud submit fails clearly before spawning Codex when env id is absent."""

        with tempfile.TemporaryDirectory() as tmp:
            pdir = Path(tmp) / "alice"
            pdir.mkdir()
            with patch("nblane.core.agent_tasks.profile_dir", lambda _name: pdir):
                task = create_agent_task(
                    "alice",
                    target_harness="codex",
                    role="remote_dev",
                    title="Patch gateway",
                )
                with patch("nblane.core.codex_adapter.subprocess.run") as run:
                    result = submit_codex_cloud_task(
                        "alice",
                        task["id"],
                        config=CodexConfig(cloud_env_id=""),
                    )

        self.assertFalse(result.ok)
        self.assertIn("codex_cloud_env_missing", result.error)
        run.assert_not_called()

    def test_refresh_with_diff_submits_candidate_metadata(self) -> None:
        """Pulling a diff makes the task candidate_ready without applying it."""

        diff = (
            "diff --git a/src/a.py b/src/a.py\n"
            "+++ b/src/a.py\n"
            "@@\n"
            "+print('x')\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            pdir = Path(tmp) / "alice"
            pdir.mkdir()
            with patch("nblane.core.agent_tasks.profile_dir", lambda _name: pdir):
                task = create_agent_task(
                    "alice",
                    target_harness="codex",
                    role="remote_dev",
                    title="Patch gateway",
                )
                update_agent_task_remote(
                    "alice",
                    task["id"],
                    {"provider": "codex_cloud", "cloud_task_id": "task_abc"},
                    status="running",
                )
                with (
                    patch(
                        "nblane.core.codex_adapter.shutil.which",
                        return_value="/bin/codex",
                    ),
                    patch(
                        "nblane.core.codex_adapter.subprocess.run",
                        side_effect=[
                            _Completed(stdout="status: completed\n"),
                            _Completed(stdout=diff),
                        ],
                    ),
                ):
                    result = refresh_codex_cloud_task(
                        "alice",
                        task["id"],
                        include_diff=True,
                        config=CodexConfig(),
                    )
                loaded = load_agent_tasks("alice")["tasks"][0]

        self.assertTrue(result.ok)
        self.assertEqual(result.status, "candidate_ready")
        self.assertEqual(result.changed_paths, ["src/a.py"])
        self.assertEqual(loaded["status"], "candidate_ready")
        self.assertEqual(loaded["changed_paths"], ["src/a.py"])
        self.assertIn("diff --git", loaded["remote"]["diff"])

    def test_local_codex_run_submits_diff_candidate(self) -> None:
        """Local Codex runs in a worktree and stores the collected diff."""

        diff = (
            "diff --git a/src/local.py b/src/local.py\n"
            "--- a/src/local.py\n"
            "+++ b/src/local.py\n"
            "@@\n"
            "+print('local')\n"
        )

        def fake_run(args, *, timeout, cwd=None, stdin=None, env=None):
            command = " ".join(str(arg) for arg in args)
            if args[:3] == ["/bin/git", "status", "--porcelain"]:
                if cwd is None:
                    return CodexCommandResult(True, command, 0, stdout="")
                return CodexCommandResult(
                    True,
                    command,
                    0,
                    stdout=" M src/local.py\n",
                )
            if args[:3] == ["/bin/git", "worktree", "add"]:
                return CodexCommandResult(True, command, 0)
            if args[:3] == ["/bin/git", "worktree", "remove"]:
                return CodexCommandResult(True, command, 0)
            if args[:3] == ["/bin/git", "diff", "--stat"]:
                return CodexCommandResult(
                    True,
                    command,
                    0,
                    stdout=" src/local.py | 1 +\n",
                )
            if args[:4] == ["/bin/git", "diff", "--no-ext-diff", "--binary"]:
                return CodexCommandResult(True, command, 0, stdout=diff)
            if args[:3] == ["/bin/git", "ls-files", "--others"]:
                return CodexCommandResult(True, command, 0, stdout="")
            if args[:2] == ["/bin/codex", "exec"]:
                self.assertIn("nblane Agent Task Handoff", stdin or "")
                return CodexCommandResult(
                    True,
                    command,
                    0,
                    stdout="done\n",
                )
            return CodexCommandResult(True, command, 0)

        with tempfile.TemporaryDirectory() as tmp:
            pdir = Path(tmp) / "alice"
            pdir.mkdir()
            worktree_root = Path(tmp) / "runs"
            with (
                patch("nblane.core.agent_tasks.profile_dir", lambda _name: pdir),
                patch("nblane.core.agent_activity.profile_dir", lambda _name: pdir),
                patch("nblane.core.codex_adapter.profile_dir", lambda _name: pdir),
                patch(
                    "nblane.core.codex_adapter.shutil.which",
                    side_effect=lambda name: f"/bin/{name}",
                ),
                patch("nblane.core.codex_adapter._run", side_effect=fake_run),
            ):
                task = create_agent_task(
                    "alice",
                    target_harness="codex",
                    role="remote_dev",
                    title="Patch local runner",
                )
                result = run_local_codex_task(
                    "alice",
                    task["id"],
                    config=CodexConfig(timeout_seconds=60),
                    worktree_root=worktree_root,
                )
                loaded = load_agent_tasks("alice")["tasks"][0]

        self.assertTrue(result.ok)
        self.assertEqual(result.status, "candidate_ready")
        self.assertEqual(result.changed_paths, ["src/local.py"])
        self.assertEqual(loaded["status"], "candidate_ready")
        self.assertEqual(loaded["changed_paths"], ["src/local.py"])
        self.assertEqual(loaded["result_payload"]["provider"], "local_codex")
        self.assertIn("diff --git", loaded["result_payload"]["diff"])

    def test_parse_helpers_are_best_effort(self) -> None:
        """Parsing keeps working for JSON, text, and plain diffs."""

        self.assertEqual(
            parse_cloud_task_id('{"task_id": "task_json123"}'),
            "task_json123",
        )
        self.assertEqual(
            parse_cloud_task_id("Cloud task id: 123e4567-e89b-12d3-a456-426614174000"),
            "123e4567-e89b-12d3-a456-426614174000",
        )
        self.assertEqual(
            parse_diff_changed_paths(
                "diff --git a/old.py b/new.py\n--- a/old.py\n+++ b/new.py\n"
            ),
            ["new.py"],
        )


if __name__ == "__main__":
    unittest.main()
