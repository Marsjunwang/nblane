"""Tests for ``nblane setup`` (commands/setup.py) and ``nblane doctor`` (core/doctor.py)."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest
import yaml

from nblane.commands import setup as setup_cmd
from nblane.commands.setup import Prompter, SetupOptions
from nblane.core import auth as auth_core
from nblane.core import doctor, llm

PW = "long-enough-password"


def scripted(answers: list[str], secrets: list[str] | None = None) -> tuple[Prompter, list[str]]:
    """A Prompter that replays *answers* / *secrets* and records output."""
    out: list[str] = []
    answer_iter = iter(answers)
    secret_iter = iter(secrets or [])

    def take(iterator):
        def fn(_prompt: str) -> str:
            try:
                return next(iterator)
            except StopIteration:
                raise EOFError from None

        return fn

    return Prompter(interactive=True, input_fn=take(answer_iter), secret_fn=take(secret_iter), out=out.append), out


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """Point profiles, .env and auth at tmp_path and restore LLM globals."""
    profiles = tmp_path / "profiles"
    profiles.mkdir()
    monkeypatch.setattr("nblane.core.profile_io.PROFILES_DIR", profiles)
    monkeypatch.setattr("nblane.core.paths.PROFILES_DIR", profiles)
    monkeypatch.setattr("nblane.core.paths.REPO_ROOT", tmp_path)
    monkeypatch.setattr(llm, "_ENV_FILE", tmp_path / ".env")
    monkeypatch.setattr(llm, "_API_KEY", "")
    monkeypatch.setattr(llm, "_BASE_URL", llm._DEFAULT_BASE_URL)
    monkeypatch.setattr(llm, "_MODEL", llm._DEFAULT_MODEL)
    for key in (
        "LLM_API_KEY",
        "LLM_BASE_URL",
        "LLM_MODEL",
        "NBLANE_AUTH_FILE",
        "NBLANE_READER_TOKEN_SECRET",
        "NBLANE_ROOT",
        "NBLANE_DATA_GIT_AUTOCOMMIT",
    ):
        monkeypatch.delenv(key, raising=False)
    auth_core.clear_users_cache()
    # The wizard sets os.environ directly (NBLANE_AUTH_FILE etc.); monkeypatch
    # does not undo keys that were absent before, so restore the whole env.
    saved_env = dict(os.environ)
    yield tmp_path
    os.environ.clear()
    os.environ.update(saved_env)
    auth_core.clear_users_cache()


class TestPrompter:
    def test_defaults_on_empty_and_eof(self):
        io, _out = scripted([""])
        assert io.ask("q", "d") == "d"
        assert io.ask("q", "d2") == "d2"  # EOF

    def test_confirm_reprompts_on_garbage(self):
        io, out = scripted(["maybe", "y"])
        assert io.confirm("q", False) is True
        assert "请输入 y 或 n。" in out

    def test_choose_by_number_and_key(self):
        options = [("a", "A"), ("b", "B")]
        io, _out = scripted(["2", "a", "9", ""])
        assert io.choose("q", options, "a") == "b"
        assert io.choose("q", options, "b") == "a"
        assert io.choose("q", options, "b") == "b"  # 9 rejected, then default

    def test_non_interactive_never_reads(self):
        def boom(_prompt: str) -> str:
            raise AssertionError("must not prompt")

        io = Prompter(interactive=False, input_fn=boom, secret_fn=boom, out=lambda _s: None)
        assert io.ask("q", "d") == "d"
        assert io.confirm("q", True) is True
        assert io.secret("q") == ""


class TestStepProfile:
    def test_creates_profile_with_chosen_schema(self, sandbox):
        io, _out = scripted(["alice", "1"])
        assert setup_cmd.step_profile(SetupOptions(), io) == "alice"
        tree = yaml.safe_load((sandbox / "profiles" / "alice" / "skill-tree.yaml").read_text(encoding="utf-8"))
        assert tree["schema"] == "autonomous-driving"  # sorted list: 1 = autonomous-driving

    def test_flags_skip_prompts(self, sandbox):
        io = Prompter(interactive=False, out=lambda _s: None)
        assert setup_cmd.step_profile(SetupOptions(profile="bob", yes=True), io) == "bob"
        assert (sandbox / "profiles" / "bob" / "SKILL.md").exists()

    def test_existing_profile_is_left_alone(self, sandbox):
        (sandbox / "profiles" / "alice").mkdir()
        marker = sandbox / "profiles" / "alice" / "SKILL.md"
        marker.write_text("mine", encoding="utf-8")
        io, out = scripted(["alice"])
        assert setup_cmd.step_profile(SetupOptions(), io) == "alice"
        assert marker.read_text(encoding="utf-8") == "mine"
        assert any("保留不动" in line for line in out)

    def test_yes_without_profile_skips(self, sandbox):
        io = Prompter(interactive=False, out=lambda _s: None)
        assert setup_cmd.step_profile(SetupOptions(yes=True), io) is None
        assert list((sandbox / "profiles").iterdir()) == []


class TestStepLlm:
    def test_preset_and_key_written_0600(self, sandbox):
        io, _out = scripted(["2", "", ""], ["sk-test"])  # deepseek, keep URL + model
        assert setup_cmd.step_llm(SetupOptions(), io) is True
        env = sandbox / ".env"
        text = env.read_text(encoding="utf-8")
        assert "LLM_API_KEY='sk-test'" in text
        assert "LLM_BASE_URL='https://api.deepseek.com/v1'" in text
        assert stat.S_IMODE(env.stat().st_mode) == 0o600
        assert llm.is_configured()

    def test_key_from_env_var(self, sandbox, monkeypatch):
        monkeypatch.setenv("MY_KEY", "sk-env")
        io = Prompter(interactive=False, out=lambda _s: None)
        opts = SetupOptions(llm="openai", llm_key_env="MY_KEY", yes=True)
        assert setup_cmd.step_llm(opts, io) is True
        assert "LLM_API_KEY='sk-env'" in (sandbox / ".env").read_text(encoding="utf-8")

    def test_skip_and_empty_key_write_nothing(self, sandbox):
        io, _out = scripted([str(len(setup_cmd.LLM_PRESETS) + 1)])
        assert setup_cmd.step_llm(SetupOptions(), io) is False
        io, _out = scripted(["1", "", ""], [""])
        assert setup_cmd.step_llm(SetupOptions(), io) is False
        assert not (sandbox / ".env").exists()


class TestStepAuth:
    def test_creates_admin_and_secret(self, sandbox):
        io, _out = scripted(["y", "boss"], ["short", PW, PW])
        setup_cmd.step_auth(SetupOptions(), io, "alice")
        users_file = sandbox / "auth" / "users.yaml"
        raw = yaml.safe_load(users_file.read_text(encoding="utf-8"))
        row = raw["users"]["boss"]
        assert row["role"] == "admin"
        assert row["profiles"] == ["alice"]
        assert auth_core.verify_password(PW, row["password_hash"])
        assert stat.S_IMODE(users_file.stat().st_mode) == 0o600
        env = (sandbox / ".env").read_text(encoding="utf-8")
        assert "NBLANE_AUTH_FILE=" in env
        assert "NBLANE_READER_TOKEN_SECRET=" in env
        assert PW not in env

    def test_declined_or_yes_does_nothing(self, sandbox):
        io, _out = scripted(["n"])
        setup_cmd.step_auth(SetupOptions(), io, None)
        setup_cmd.step_auth(SetupOptions(yes=True), Prompter(interactive=False, out=lambda _s: None), None)
        assert not (sandbox / "auth").exists()
        assert not (sandbox / ".env").exists()

    def test_short_password_from_env_is_refused(self, sandbox, monkeypatch):
        monkeypatch.setenv("ADMIN_PW", "short")
        opts = SetupOptions(auth=True, admin_user="boss", admin_password_env="ADMIN_PW", yes=True)
        setup_cmd.step_auth(opts, Prompter(interactive=False, out=lambda _s: None), None)
        assert not (sandbox / "auth" / "users.yaml").exists()


class TestCmdSetup:
    def test_non_interactive_run_reports_next_steps(self, sandbox):
        out: list[str] = []
        opts = SetupOptions(profile="alice", llm="skip", yes=True)
        code = setup_cmd.cmd_setup(opts, Prompter(interactive=False, out=out.append))
        assert code == 0
        assert (sandbox / "profiles" / "alice").is_dir()
        joined = "\n".join(out)
        assert "scripts/dev-web.sh" in joined
        assert "nblane context alice" in joined


class TestDoctor:
    def test_llm_unconfigured_is_warning(self, sandbox):
        checks = {check.name: check for check in doctor.check_llm()}
        assert checks["AI 服务"].status == doctor.WARN
        assert checks[".env"].status == doctor.INFO

    def test_readable_env_file_warns(self, sandbox):
        env = sandbox / ".env"
        env.write_text("X=1\n", encoding="utf-8")
        env.chmod(0o644)
        checks = {check.name: check for check in doctor.check_llm()}
        assert checks[".env"].status == doctor.WARN
        assert "chmod 600" in checks[".env"].hint

    def test_auth_without_secret_fails(self, sandbox, monkeypatch):
        users = sandbox / "users.yaml"
        users.write_text("users: {}\n", encoding="utf-8")
        monkeypatch.setenv("NBLANE_AUTH_FILE", str(users))
        checks = doctor.check_auth()
        assert doctor.has_failures(checks)
        monkeypatch.setenv("NBLANE_READER_TOKEN_SECRET", "x" * 32)
        assert not doctor.has_failures(doctor.check_auth())

    def test_missing_auth_file_fails(self, sandbox, monkeypatch):
        monkeypatch.setenv("NBLANE_AUTH_FILE", str(sandbox / "nope.yaml"))
        assert doctor.has_failures(doctor.check_auth())

    def test_empty_data_root_warns(self, sandbox):
        checks = {check.name: check for check in doctor.check_data_root()}
        assert checks["档案"].status == doctor.WARN

    def test_format_aligns_wide_names_and_shows_hints(self):
        text = doctor.format_checks(
            [
                doctor.Check("Git", doctor.OK, "/usr/bin/git"),
                doctor.Check("数据目录", doctor.FAIL, "missing", "fix it"),
            ]
        )
        lines = text.splitlines()
        col = lambda line, word: doctor._width(line[: line.index(word)])  # noqa: E731
        assert col(lines[0], "/usr/bin/git") == col(lines[1], "missing")
        assert "→ fix it" in text
        assert "1 项必须修复" in text

    def test_run_checks_offline_has_no_failures_on_fresh_root(self, sandbox):
        checks = doctor.run_checks(online=False, ports=False)
        names = [check.name for check in checks]
        assert names[0] == "Python"
        assert "AI 服务" in names
        assert not any(check.name.startswith("端口") for check in checks)


def test_install_script_is_executable_shell():
    script = Path(__file__).resolve().parents[1] / "scripts" / "install.sh"
    text = script.read_text(encoding="utf-8")
    assert text.startswith("#!/usr/bin/env bash")
    assert "nblane setup" in text
