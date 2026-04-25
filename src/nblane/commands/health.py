"""Profile health CLI command."""

from __future__ import annotations

import sys

from nblane.commands.common import _require_profile
from nblane.core.io import list_profiles
from nblane.core.profile_health import (
    analyze_profile_health,
    format_health_text,
)


def cmd_health(name: str | None) -> None:
    """Print deterministic profile health report(s)."""
    names = [name] if name is not None else list_profiles()
    exit_code = 0
    for i, profile_name in enumerate(names):
        if profile_name != "template":
            _require_profile(profile_name)
        report = analyze_profile_health(profile_name)
        if i:
            print()
        print(format_health_text(report))
        if any(issue.severity == "error" for issue in report.issues):
            exit_code = 1
    sys.exit(exit_code)
