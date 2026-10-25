from __future__ import annotations

import os
import subprocess
import tarfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = REPO_ROOT / "packaging" / "ubuntu" / "install.sh"


def _environment(tmp_path: Path) -> dict[str, str]:
    env = {
        key: value for key, value in os.environ.items() if not key.startswith("NBLANE_")
    }
    env.update(
        HOME=str(tmp_path / "home"),
        NBLANE_SKIP_SYSTEMD="1",
        NBLANE_INSTALL_ROOT=str(tmp_path / "code"),
        NBLANE_ROOT=str(tmp_path / "data"),
        NBLANE_ASSET_ROOT=str(tmp_path / "assets"),
        NBLANE_BACKUP_DIR=str(tmp_path / "backups"),
        NBLANE_AUTH="0",
    )
    return env


def _package(tmp_path: Path) -> Path:
    package = tmp_path / "package"
    installer = package / "packaging" / "ubuntu" / "install.sh"
    installer.parent.mkdir(parents=True)
    installer.write_bytes(INSTALLER.read_bytes())
    (package / "BUILDINFO").write_text(
        "VERSION=0.2.0\n"
        "COMMIT=0000000000000000000000000000000000000000\n"
        "BUILD_TIME=2026-10-25T00:00:00Z\n"
        "SOURCE_ARCHIVE=source.tar.gz\n",
        encoding="utf-8",
    )
    return package


def _run(package: Path, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(package / "packaging" / "ubuntu" / "install.sh")],
        cwd=tmp_path,
        env=_environment(tmp_path),
        text=True,
        capture_output=True,
        check=False,
    )


def test_installer_is_executable_and_has_help(tmp_path: Path) -> None:
    assert os.access(INSTALLER, os.X_OK)
    result = subprocess.run(
        [str(INSTALLER), "--help"],
        cwd=tmp_path,
        env=_environment(tmp_path),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "--rollback" in result.stdout
    assert "NBLANE_SKIP_SYSTEMD" in result.stdout


def test_incomplete_metadata_fails_before_creating_data(tmp_path: Path) -> None:
    package = _package(tmp_path)
    result = _run(package, tmp_path)
    assert result.returncode != 0
    assert "source.tar.gz" in result.stderr
    assert "unbound variable" not in result.stderr
    assert not (tmp_path / "data").exists()


def test_data_must_be_outside_the_code_directory(tmp_path: Path) -> None:
    package = _package(tmp_path)
    env = _environment(tmp_path)
    env["NBLANE_ROOT"] = str(tmp_path / "code" / "data")
    result = subprocess.run(
        ["bash", str(package / "packaging" / "ubuntu" / "install.sh")],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode != 0
    assert "数据目录不能位于代码目录内" in result.stderr
    assert not (tmp_path / "code").exists()


def test_missing_wheelhouse_does_not_replace_existing_code(tmp_path: Path) -> None:
    package = _package(tmp_path)
    with tarfile.open(package / "source.tar.gz", "w:gz") as archive:
        source = tmp_path / "source" / "pyproject.toml"
        source.parent.mkdir()
        source.write_text('[project]\nname = "nblane"\nversion = "0.2.0"\n', encoding="utf-8")
        archive.add(source, arcname="pyproject.toml")
    code = tmp_path / "code"
    code.mkdir()
    (code / "marker").write_text("keep", encoding="utf-8")

    result = _run(package, tmp_path)

    assert result.returncode != 0
    assert "缺少离线依赖" in result.stderr
    assert (code / "marker").read_text(encoding="utf-8") == "keep"
    assert not (tmp_path / "backups").exists()


def test_rollback_ignores_failed_install_directories(tmp_path: Path) -> None:
    package = _package(tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / "assets").mkdir()
    backup = tmp_path / "backups" / "backup-20261025T010203Z-0.2.0"
    backup.mkdir(parents=True)
    (backup / "pyproject.toml").write_text('[project]\nname = "nblane"\n', encoding="utf-8")
    (backup / "marker").write_text("good-backup", encoding="utf-8")
    failed = tmp_path / "backups" / "failed-20261025T020304Z-99"
    failed.mkdir()
    (failed / "marker").write_text("failed-install", encoding="utf-8")
    code = tmp_path / "code"
    code.mkdir()
    (code / "marker").write_text("current", encoding="utf-8")

    result = subprocess.run(
        ["bash", str(package / "packaging" / "ubuntu" / "install.sh"), "--rollback"],
        cwd=tmp_path,
        env=_environment(tmp_path),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert (code / "marker").read_text(encoding="utf-8") == "good-backup"
    assert (backup / "marker").read_text(encoding="utf-8") == "good-backup"
    assert (failed / "marker").read_text(encoding="utf-8") == "failed-install"
