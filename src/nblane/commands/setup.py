"""``nblane setup`` (first-run wizard) and ``nblane doctor`` CLI commands."""

from __future__ import annotations

import getpass
import os
import secrets
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

# (label, base_url, model). The first one matches .env.example's default.
LLM_PRESETS: dict[str, tuple[str, str, str]] = {
    "dashscope": ("阿里云百炼 DashScope", "https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen3.6-plus"),
    "deepseek": ("DeepSeek", "https://api.deepseek.com/v1", "deepseek-chat"),
    "openai": ("OpenAI", "https://api.openai.com/v1", "gpt-4.1-nano"),
    "ollama": ("本机 Ollama", "http://localhost:11434/v1", "llama3"),
    "custom": ("其他 OpenAI 兼容服务", "", ""),
}


def cmd_doctor(*, online: bool) -> None:
    """Print environment checks; exit 1 when something must be fixed."""
    from nblane.core import doctor

    checks = doctor.run_checks(online=online)
    print(doctor.format_checks(checks))
    sys.exit(1 if doctor.has_failures(checks) else 0)


@dataclass
class SetupOptions:
    """Answers given as flags; ``None`` means "ask" (or skip with --yes)."""

    profile: str | None = None
    schema: str | None = None
    llm: str | None = None  # preset key or "skip"
    llm_base_url: str | None = None
    llm_model: str | None = None
    llm_key_env: str | None = None
    auth: bool | None = None
    admin_user: str | None = None
    admin_password_env: str | None = None
    test_llm: bool | None = None
    yes: bool = False


@dataclass
class Prompter:
    """Terminal I/O, swappable in tests. EOF counts as "take the default"."""

    interactive: bool = True
    input_fn: Callable[[str], str] = input
    secret_fn: Callable[[str], str] = getpass.getpass
    out: Callable[[str], None] = print

    def ask(self, question: str, default: str = "") -> str:
        if not self.interactive:
            return default
        suffix = f" [{default}]" if default else ""
        try:
            answer = self.input_fn(f"{question}{suffix}: ").strip()
        except EOFError:
            return default
        return answer or default

    def confirm(self, question: str, default: bool) -> bool:
        if not self.interactive:
            return default
        hint = "Y/n" if default else "y/N"
        while True:
            try:
                answer = self.input_fn(f"{question} [{hint}]: ").strip().lower()
            except EOFError:
                return default
            if not answer:
                return default
            if answer in ("y", "yes", "是", "好"):
                return True
            if answer in ("n", "no", "否", "不"):
                return False
            self.out("请输入 y 或 n。")

    def choose(self, question: str, options: list[tuple[str, str]], default: str) -> str:
        """Numbered menu over ``(key, label)``; returns the chosen key."""
        if not self.interactive:
            return default
        self.out(question)
        for index, (key, label) in enumerate(options, start=1):
            mark = "  (默认)" if key == default else ""
            self.out(f"  {index}. {label}{mark}")
        keys = [key for key, _label in options]
        while True:
            answer = self.ask("选择编号", str(keys.index(default) + 1))
            if answer.isdigit() and 1 <= int(answer) <= len(keys):
                return keys[int(answer) - 1]
            if answer in keys:
                return answer
            self.out(f"请输入 1–{len(keys)}。")

    def secret(self, question: str) -> str:
        if not self.interactive:
            return ""
        try:
            return self.secret_fn(f"{question}: ").strip()
        except EOFError:
            return ""


def _heading(io: Prompter, text: str) -> None:
    io.out(f"\n== {text} ==")


def _env_file() -> Path:
    from nblane.core import llm

    return llm._ENV_FILE


def _ensure_env_file() -> Path:
    """Create ``.env`` (0600) from ``.env.example`` when it is missing."""
    from nblane.core.paths import REPO_ROOT

    path = _env_file()
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    example = Path(__file__).resolve().parents[3] / ".env.example"
    if not example.exists():
        example = REPO_ROOT / ".env.example"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        if example.exists():
            handle.write(example.read_text(encoding="utf-8"))
    return path


def _set_env(key: str, value: str) -> None:
    from dotenv import set_key

    path = _ensure_env_file()
    set_key(str(path), key, value)
    os.chmod(path, 0o600)
    os.environ[key] = value


def step_profile(opts: SetupOptions, io: Prompter) -> str | None:
    from nblane.core import schema_io
    from nblane.core.profile_io import init_profile, list_profiles

    _heading(io, "1. 档案")
    existing = list_profiles()
    if existing:
        io.out(f"已有档案：{'、'.join(existing)}")
    name = opts.profile
    if name is None:
        if opts.yes:
            io.out("跳过（未给 --profile）。")
            return existing[0] if existing else None
        prompt = "新建档案名（回车跳过）" if existing else "档案名（比如你的名字或 GitHub 用户名）"
        name = io.ask(prompt)
    name = name.strip()
    if not name:
        return existing[0] if existing else None
    if name in existing:
        io.out(f"档案「{name}」已存在，保留不动。")
        return name

    schemas = schema_io.list_schemas()
    schema = opts.schema
    if schema is None and len(schemas) > 1:
        options = []
        for key in schemas:
            loaded = schema_io.load_schema(key)
            options.append((key, f"{loaded.domain if loaded else key}（{key}）"))
        default = "robotics-engineer" if "robotics-engineer" in schemas else schemas[0]
        schema = io.choose("领域技能树：", options, default)
    try:
        dest = init_profile(name, schema=schema)
    except (ValueError, FileExistsError) as exc:
        io.out(f"创建失败：{exc}")
        return None
    io.out(f"已创建 {dest}")
    return name


def step_llm(opts: SetupOptions, io: Prompter) -> bool:
    """Write the LLM connection to .env; returns True when a key was saved."""
    from nblane.core import llm

    _heading(io, "2. AI 服务（可选）")
    if llm.is_configured() and opts.llm is None:
        io.out(f"已配置：{llm._MODEL} @ {llm._BASE_URL}")
        if opts.yes or not io.confirm("要改吗？", False):
            return False
    preset = opts.llm
    if preset is None:
        if opts.yes:
            io.out("跳过（未给 --llm）。")
            return False
        options = [(key, label) for key, (label, _url, _model) in LLM_PRESETS.items()]
        options.append(("skip", "先不配，以后在「设置 → AI 服务」里填"))
        preset = io.choose("选一个 OpenAI 兼容服务：", options, "dashscope")
    if preset == "skip":
        return False
    if preset not in LLM_PRESETS:
        io.out(f"未知的服务 {preset}，可选：{', '.join(LLM_PRESETS)}、skip")
        return False
    _label, base_url, model = LLM_PRESETS[preset]
    base_url = opts.llm_base_url or (base_url if opts.yes else io.ask("Base URL", base_url))
    model = opts.llm_model or (model if opts.yes else io.ask("模型", model))
    if not base_url or not model:
        io.out("Base URL 和模型都要填，已跳过。")
        return False
    if opts.llm_key_env:
        key = os.getenv(opts.llm_key_env, "").strip()
        if not key:
            io.out(f"环境变量 {opts.llm_key_env} 是空的，已跳过。")
            return False
    elif preset == "ollama":
        key = "ollama"
    else:
        key = io.secret("API Key（输入不显示）")
        if not key:
            io.out("没有输入 Key，已跳过。")
            return False
    _ensure_env_file()
    llm.set_env_connection(base_url, key, model)
    io.out(f"已写入 {_env_file()}（权限 600）")
    return True


def _default_auth_file() -> Path:
    from nblane.core.paths import REPO_ROOT

    return REPO_ROOT / "auth" / "users.yaml"


def step_auth(opts: SetupOptions, io: Prompter, profile: str | None) -> None:
    from nblane.core import auth, auth_store

    _heading(io, "3. 登录")
    current = auth.auth_file_path()
    if current is not None and current.exists():
        io.out(f"已开启：{current}")
        return
    enable = opts.auth
    if enable is None:
        if opts.yes:
            enable = False
        else:
            io.out("本机自己用可以不开。放到服务器、或别人能访问这台机器时必须开。")
            enable = io.confirm("开启登录？", False)
    if not enable:
        io.out("不开启。以后要开，重新运行 nblane setup。")
        return

    path = current or _default_auth_file()
    user = opts.admin_user or ("" if opts.yes else io.ask("管理员账号", "admin"))
    if not user:
        io.out("需要 --admin-user，已跳过。")
        return
    if opts.admin_password_env:
        password = os.getenv(opts.admin_password_env, "")
    else:
        password = ""
        while io.interactive:
            password = io.secret(f"密码（至少 {auth_store.MIN_PASSWORD_LENGTH} 位，输入不显示）")
            if len(password) < auth_store.MIN_PASSWORD_LENGTH:
                io.out("太短了。")
                continue
            if io.secret("再输一次") == password:
                break
            io.out("两次不一致。")
    if len(password) < auth_store.MIN_PASSWORD_LENGTH:
        io.out(f"密码至少 {auth_store.MIN_PASSWORD_LENGTH} 位，已跳过。")
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    os.environ["NBLANE_AUTH_FILE"] = str(path)
    try:
        auth_store.create_user(
            user,
            display_name=profile or user,
            role="admin",
            password=password,
            profiles=[profile] if profile else (),
            must_change_password=False,
        )
    except auth_store.AccountError as exc:
        io.out(f"创建管理员失败：{exc}")
        return
    _set_env("NBLANE_AUTH_FILE", str(path))
    if not os.getenv("NBLANE_READER_TOKEN_SECRET", "").strip():
        _set_env("NBLANE_READER_TOKEN_SECRET", secrets.token_urlsafe(32))
    io.out(f"已创建管理员 {user}：{path}（权限 600）")
    io.out(f"NBLANE_AUTH_FILE 和会话密钥已写入 {_env_file()}。")
    io.out("走 HTTPS 时在 .env 里加 NBLANE_AUTH_COOKIE_SECURE=1。")


def cmd_setup(opts: SetupOptions, io: Prompter | None = None) -> int:
    """Run the wizard; returns the doctor exit code (0 = ready)."""
    from nblane.core import doctor
    from nblane.core.paths import REPO_ROOT

    io = io or Prompter(interactive=not opts.yes and sys.stdin.isatty())
    if not io.interactive and not opts.yes:
        io.out("不是交互终端，按 --yes 处理：只做参数里给了的步骤。")
        opts.yes = True
    io.out(f"nblane 设置向导 · 数据目录 {REPO_ROOT}")
    if not os.getenv("NBLANE_ROOT"):
        io.out("（要把数据放到别处，先设置 NBLANE_ROOT 再运行。）")

    profile = step_profile(opts, io)
    if step_llm(opts, io):
        test = opts.test_llm
        if test is None:
            test = not opts.yes and io.confirm("现在测试一次连接？", True)
        if test:
            for check in doctor.check_llm(online=True):
                if check.name == "AI 服务":
                    io.out(f"{'连接正常' if check.status == doctor.OK else check.detail}")
    step_auth(opts, io, profile)

    _heading(io, "4. 环境检查")
    checks = doctor.run_checks(online=False, ports=False)
    io.out(doctor.format_checks(checks))

    _heading(io, "下一步")
    io.out("  scripts/dev-web.sh            # 启动服务")
    io.out("  打开 http://127.0.0.1:8504")
    if profile:
        io.out(f"  nblane context {profile}  # 打印给 Agent 的系统提示词")
    if not shutil.which("tmux"):
        io.out("  没有 tmux 时可以直接跑：.venv/bin/uvicorn nblane.web_api:app --port 8504")
    return 1 if doctor.has_failures(checks) else 0
