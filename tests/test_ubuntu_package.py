from __future__ import annotations

import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGER = REPO_ROOT / "scripts" / "package-ubuntu.sh"
VERSION = "1.2.3"
ARCHIVE_NAME = f"nblane-{VERSION}-ubuntu.tar.gz"
SOURCE_NAME = f"nblane-{VERSION}-source.tar.gz"


def _write(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _git(repo: Path, *args: str) -> str:
    env = os.environ.copy()
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def _make_repository(root: Path) -> Path:
    script_path = root / "scripts" / "package-ubuntu.sh"
    script_path.parent.mkdir(parents=True)
    shutil.copy2(PACKAGER, script_path)
    _write(
        root,
        "pyproject.toml",
        f'[project]\nname = "nblane"\nversion = "{VERSION}"\n',
    )
    _write(root, "requirements.txt", "pyyaml>=6.0\n")
    _write(root, "uv.lock", "version = 1\n")
    _write(root, "src/nblane/__init__.py", '__version__ = "committed"\n')
    _write(root, "scripts/install.sh", "#!/usr/bin/env bash\n")
    _write(
        root,
        "packaging/ubuntu/install.sh",
        "#!/usr/bin/env bash\nprintf 'installer executed\\n' >&2\nexit 97\n",
    )
    _write(root, ".env.example", "LLM_API_KEY=\n")
    _write(root, "auth/users.example.yaml", "users: []\n")
    _write(root, "profiles/template/SKILL.md", "# Template\n")
    _write(
        root,
        ".gitignore",
        """.env
.env.*
!.env.example
.reader-token-secret
.venv/
.dev-data/
.dev-assets/
test-results/
dist/
build/
/blocked-bin/
profiles/*
!profiles/template/
!profiles/template/**
schemas/.learned/
config.yaml
/auth/*
!/auth/users.example.yaml
""",
    )
    _git(root, "init", "--quiet")
    _git(root, "config", "user.name", "Package Test")
    _git(root, "config", "user.email", "package-test@example.invalid")
    _git(root, "add", "--all")
    _git(root, "commit", "--quiet", "--no-gpg-sign", "-m", "initial")
    return root


def _package_env() -> dict[str, str]:
    env = os.environ.copy()
    for name in (
        "NBLANE_PACKAGE_ALLOW_DIRTY",
        "NBLANE_PACKAGE_OFFLINE",
        "NBLANE_PACKAGE_OUT",
    ):
        env.pop(name, None)
    env["NBLANE_PACKAGE_OFFLINE"] = "0"
    env["NBLANE_DISABLE_NETWORK_LOOKUPS"] = "1"
    env["PIP_NO_INDEX"] = "1"
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    return env


def _run_packager(repo: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    blocked_bin = repo / "blocked-bin"
    blocked_bin.mkdir(exist_ok=True)
    uv = blocked_bin / "uv"
    uv.write_text("#!/usr/bin/env bash\nexit 98\n", encoding="utf-8")
    uv.chmod(0o755)
    env["PATH"] = f"{blocked_bin}{os.pathsep}{env.get('PATH', '')}"
    return subprocess.run(
        ["bash", str(repo / "scripts" / "package-ubuntu.sh")],
        cwd=repo,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def _member_bytes(archive: tarfile.TarFile, name: str) -> bytes:
    member = archive.extractfile(name)
    assert member is not None
    return member.read()


def _source_archive(outer: tarfile.TarFile) -> tarfile.TarFile:
    return tarfile.open(fileobj=io.BytesIO(_member_bytes(outer, SOURCE_NAME)), mode="r:gz")


@pytest.mark.parametrize("option", ["-h", "--help"])
def test_help(option: str, tmp_path: Path) -> None:
    result = subprocess.run(
        ["bash", str(PACKAGER), option],
        cwd=tmp_path,
        env=_package_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Usage: scripts/package-ubuntu.sh" in result.stdout
    assert "NBLANE_PACKAGE_ALLOW_DIRTY" in result.stdout
    assert "NBLANE_PACKAGE_OFFLINE" in result.stdout


def test_dirty_tree_is_rejected_by_default(tmp_path: Path) -> None:
    repo = _make_repository(tmp_path)
    _write(repo, "src/nblane/__init__.py", '__version__ = "dirty"\n')

    result = _run_packager(repo, _package_env())

    assert result.returncode != 0
    assert "working tree is dirty" in result.stderr
    assert "NBLANE_PACKAGE_ALLOW_DIRTY=1" in result.stderr
    assert not (repo / "dist" / "ubuntu" / ARCHIVE_NAME).exists()


def test_clean_tree_builds_head_archive(tmp_path: Path) -> None:
    repo = _make_repository(tmp_path)

    result = _run_packager(repo, _package_env())

    assert result.returncode == 0, result.stderr
    archive_path = repo / "dist" / "ubuntu" / ARCHIVE_NAME
    with tarfile.open(archive_path, "r:gz") as outer:
        with _source_archive(outer) as source:
            assert _member_bytes(source, "src/nblane/__init__.py") == (
                b'__version__ = "committed"\n'
            )


def test_dirty_development_package_structure_and_checksum(tmp_path: Path) -> None:
    repo = _make_repository(tmp_path)
    _write(repo, "src/nblane/__init__.py", '__version__ = "working-tree"\n')
    _write(repo, "WORKING.txt", "untracked source\n")
    local_files = {
        ".env": "LLM_API_KEY=not-for-packaging\n",
        ".reader-token-secret": "not-for-packaging\n",
        "config.yaml": "private-proxy: true\n",
        "auth/users.yaml": "users: [private]\n",
        "profiles/alice/SKILL.md": "private profile\n",
        "schemas/.learned/private.yaml": "private: true\n",
        ".dev-data/private.txt": "private data\n",
        ".dev-assets/private.txt": "private asset\n",
        "test-results/private.txt": "test output\n",
        "dist/old-package.tar.gz": "old output\n",
    }
    for relative, content in local_files.items():
        _write(repo, relative, content)
    _git(
        repo,
        "add",
        "--force",
        ".env",
        ".reader-token-secret",
        "auth/users.yaml",
        "config.yaml",
        "profiles/alice/SKILL.md",
        "schemas/.learned/private.yaml",
    )
    env = _package_env()
    env["NBLANE_PACKAGE_ALLOW_DIRTY"] = "1"

    result = _run_packager(repo, env)

    assert result.returncode == 0, result.stderr
    out_dir = repo / "dist" / "ubuntu"
    archive_path = out_dir / ARCHIVE_NAME
    checksum_path = out_dir / f"{ARCHIVE_NAME}.sha256"
    assert archive_path.is_file()
    assert checksum_path.is_file()
    assert (out_dir / "BUILDINFO").is_file()

    checksum_text = checksum_path.read_text(encoding="utf-8")
    assert checksum_text.endswith("\n")
    checksum_lines = checksum_text.splitlines()
    assert len(checksum_lines) == 1
    checksum_match = re.fullmatch(r"([0-9a-f]{64})  (.+)", checksum_lines[0])
    assert checksum_match is not None
    assert checksum_match.group(2) == ARCHIVE_NAME
    assert checksum_match.group(1) == hashlib.sha256(archive_path.read_bytes()).hexdigest()

    with tarfile.open(archive_path, "r:gz") as outer:
        outer_names = set(outer.getnames())
        assert {
            "install.sh",
            "packaging/ubuntu/install.sh",
            SOURCE_NAME,
            "BUILDINFO",
        } <= outer_names
        assert "requirements-locked.txt" not in outer_names
        assert not any(name.startswith("wheelhouse/") for name in outer_names)
        bootstrap = _member_bytes(outer, "install.sh").decode("utf-8")
        assert 'packaging/ubuntu/install.sh" "$@"' in bootstrap
        assert b"exit 97" in _member_bytes(
            outer, "packaging/ubuntu/install.sh"
        )

        build_info_text = _member_bytes(outer, "BUILDINFO").decode("utf-8")
        assert build_info_text == (out_dir / "BUILDINFO").read_text(encoding="utf-8")
        build_info = dict(
            line.split("=", 1) for line in build_info_text.splitlines()
        )
        assert set(build_info) == {"VERSION", "COMMIT", "BUILD_TIME", "SOURCE_ARCHIVE"}
        assert build_info["VERSION"] == VERSION
        assert build_info["COMMIT"] == _git(repo, "rev-parse", "HEAD")
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", build_info["BUILD_TIME"])
        assert build_info["SOURCE_ARCHIVE"] == SOURCE_NAME

        with _source_archive(outer) as source:
            source_names = set(source.getnames())
            assert {
                "pyproject.toml",
                "requirements.txt",
                "uv.lock",
                "src/nblane/__init__.py",
                "scripts/install.sh",
                "scripts/package-ubuntu.sh",
                "packaging/ubuntu/install.sh",
                "profiles/template/SKILL.md",
                "auth/users.example.yaml",
                ".env.example",
                "WORKING.txt",
            } <= source_names
            assert set(local_files).isdisjoint(source_names)
            assert _member_bytes(source, "src/nblane/__init__.py") == (
                b'__version__ = "working-tree"\n'
            )


def test_offline_build_requires_uv_for_locked_dependencies(tmp_path: Path) -> None:
    repo = _make_repository(tmp_path)
    python = repo / ".venv" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.symlink_to(sys.executable)
    tools = repo / "blocked-bin"
    tools.mkdir()
    for name in (
        "bash", "git", "tar", "sha256sum", "mktemp", "date",
        "cp", "chmod", "mkdir", "mv", "rm", "dirname", "cat",
    ):
        (tools / name).symlink_to(shutil.which(name))
    env = _package_env()
    env["NBLANE_PACKAGE_OFFLINE"] = "1"
    env["PATH"] = str(tools)

    result = subprocess.run(
        ["bash", str(repo / "scripts" / "package-ubuntu.sh")],
        cwd=repo,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "uv is required" in result.stderr
    assert not (repo / "dist" / "ubuntu" / ARCHIVE_NAME).exists()
