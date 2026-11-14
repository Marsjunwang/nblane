"""Assistant integrations honor the same explicit environment file as the app."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("module", ["codex_adapter", "openclaw_automations"])
@pytest.mark.parametrize("use_override", [True, False])
def test_assistant_env_file_isolation(tmp_path: Path, module: str, use_override: bool) -> None:
    # A fresh interpreter exercises import-time loading without reloading shared
    # modules in the pytest process or ever reading the real repository .env.
    (tmp_path / ".env").write_text(
        "NBLANE_TEST_SOURCE=repository\nNBLANE_TEST_REPO_ONLY=present\n"
        "NBLANE_TEST_KEEP=file\n",
        encoding="utf-8",
    )
    isolated = tmp_path / "isolated.env"
    isolated.write_text(
        "NBLANE_TEST_SOURCE=isolated\nNBLANE_TEST_KEEP=file\n", encoding="utf-8"
    )
    env = {key: value for key, value in os.environ.items() if not key.startswith("NBLANE_TEST_")}
    env.update({
        "NBLANE_ROOT": str(tmp_path),
        "NBLANE_ENV_FILE": str(isolated) if use_override else "",
        "NBLANE_TEST_KEEP": "environment",
        "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"),
    })
    result = subprocess.run(
        [sys.executable, "-c", "\n".join([
            "import importlib, os, sys",
            "module = importlib.import_module('nblane.core.' + sys.argv[1])",
            "if sys.argv[1] == 'openclaw_automations': module._default_env()",
            "assert os.environ['NBLANE_TEST_SOURCE'] == sys.argv[2]",
            "assert os.environ['NBLANE_TEST_KEEP'] == 'environment'",
            "assert ('NBLANE_TEST_REPO_ONLY' in os.environ) == (sys.argv[2] == 'repository')",
        ]), module, "isolated" if use_override else "repository"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stderr
