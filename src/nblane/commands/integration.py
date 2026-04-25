"""IDE integration and crystallization CLI commands."""

from __future__ import annotations

from nblane.commands.common import _require_profile


def cmd_sync_cursor(name: str) -> None:
    """Write ``.cursor/rules/nblane-context.mdc`` from profile data."""
    from nblane.core.cursor_rule import write_nblane_context_rule

    _require_profile(name)
    path = write_nblane_context_rule(name)
    print(f"Wrote {path}")

def cmd_crystallize(
    name: str,
    project: str,
    body: str,
) -> None:
    """Write a method draft markdown file."""
    from nblane.core.crystallize import write_method_draft

    _require_profile(name)
    path = write_method_draft(name, project, body)
    print(f"Wrote {path}")


# -- main -------------------------------------------------------------------
