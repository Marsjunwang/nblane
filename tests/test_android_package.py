from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "package-android.sh"
TWA_DIR = REPO_ROOT / "packaging" / "android" / "twa"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def _repository(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    script = repo / "scripts" / "package-android.sh"
    script.parent.mkdir(parents=True)
    shutil.copy2(SCRIPT, script)
    manifest = repo / "packaging" / "android" / "twa" / "twa-manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps({"appVersion": "0.1.0", "appVersionCode": 1, "packageId": "cloud.nblane.app"}),
        encoding="utf-8",
    )
    gradlew = repo / "packaging" / "android" / "twa" / "gradlew"
    gradlew.write_text("#!/usr/bin/env bash\nexit 99\n", encoding="utf-8")
    gradlew.chmod(0o755)
    _git(repo, "init", "--quiet")
    _git(repo, "config", "user.name", "Android Test")
    _git(repo, "config", "user.email", "android-test@example.invalid")
    _git(repo, "add", "--all")
    _git(repo, "commit", "--quiet", "--no-gpg-sign", "-m", "fixture")
    return repo


def _run(repo: Path, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("NBLANE_ANDROID_", "BUBBLEWRAP_"))
    }
    env.update(
        HOME=str(tmp_path / "home"),
        NBLANE_ANDROID_BUILD_HOME=str(tmp_path / "home"),
        NBLANE_ANDROID_OUT=str(tmp_path / "out"),
    )
    return subprocess.run(
        [str(repo / "scripts" / "package-android.sh")],
        cwd=repo,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_help_and_executable() -> None:
    assert os.access(SCRIPT, os.X_OK)
    result = subprocess.run([str(SCRIPT), "--help"], text=True, capture_output=True, check=False)
    assert result.returncode == 0
    assert "Check, sign and package" in result.stdout
    assert "BUBBLEWRAP_KEYSTORE_PASSWORD" in result.stdout


def test_manifest_matches_public_assetlinks() -> None:
    manifest = json.loads((TWA_DIR / "twa-manifest.json").read_text(encoding="utf-8"))
    links = json.loads(
        (REPO_ROOT / "src/nblane/web_ui/frontend/public/.well-known/assetlinks.json").read_text(
            encoding="utf-8"
        )
    )
    target = links[0]["target"]
    assert manifest["packageId"] == target["package_name"]
    assert manifest["host"] == "www.nblane.cloud"
    assert manifest["startUrl"] == "/"
    assert manifest["minSdkVersion"] >= 24
    assert target["sha256_cert_fingerprints"]


def test_generated_twa_uses_production_web_manifest() -> None:
    gradle = (TWA_DIR / "app" / "build.gradle").read_text(encoding="utf-8")
    assert 'webManifestUrl", \'https://www.nblane.cloud/manifest.webmanifest\'' in gradle
    assert "127.0.0.1" not in gradle
    assert "minSdkVersion 24" in gradle


def test_dirty_tree_is_rejected_before_build(tmp_path: Path) -> None:
    repo = _repository(tmp_path)
    (repo / "untracked.txt").write_text("dirty", encoding="utf-8")
    result = _run(repo, tmp_path)
    assert result.returncode != 0
    assert "working tree is dirty" in result.stderr
    assert not (tmp_path / "out").exists()


def test_clean_repo_requires_signing_configuration(tmp_path: Path) -> None:
    repo = _repository(tmp_path)
    result = _run(repo, tmp_path)
    assert result.returncode != 0
    assert "NBLANE_ANDROID_KEYSTORE" in result.stderr
    assert not (tmp_path / "out").exists()


def test_signing_material_is_not_tracked() -> None:
    files = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, text=True, capture_output=True, check=True
    ).stdout.splitlines()
    assert not any(
        path.endswith((".p12", ".keystore", ".jks"))
        or path.endswith("signing.env")
        or path.endswith("local.properties")
        for path in files
    )
