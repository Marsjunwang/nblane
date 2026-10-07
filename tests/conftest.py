from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("NBLANE_DISABLE_NETWORK_LOOKUPS", "1")

# Production runs as the same OS user, so its admin choices (active local
# model, GROBID backend override) live in this user's home. Point tests at
# an empty scratch dir so those choices never leak into test results.
_STATE_DIR = Path(tempfile.mkdtemp(prefix="nblane-test-state-"))
os.environ["NBLANE_LOCAL_MODELS_DIR"] = str(_STATE_DIR / "local-models")
os.environ["NBLANE_GROBID_SERVICE_DIR"] = str(_STATE_DIR / "grobid")
# The Quadlet path and unit name are real systemd --user state: without these
# a test that calls stop()/uninstall() acts on the production GROBID.
os.environ["XDG_CONFIG_HOME"] = str(_STATE_DIR / "config")
os.environ["NBLANE_GROBID_UNIT"] = "nblane-grobid-pytest"
