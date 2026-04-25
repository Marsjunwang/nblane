"""Profile-oriented CLI commands."""

from __future__ import annotations

import shutil
import sys
from datetime import date

from nblane.commands.common import _profile_dir, _require_profile
from nblane.core.paths import TEMPLATE_DIR


def cmd_init(name: str) -> None:
    """Create a new profile directory from the template."""
    dest = _profile_dir(name)
    if dest.exists():
        print(f"Profile '{name}' already exists at {dest}")
        sys.exit(0)

    shutil.copytree(TEMPLATE_DIR, dest)

    for filepath in dest.rglob("*"):
        if filepath.is_file():
            text = filepath.read_text(encoding="utf-8")
            text = text.replace("{Name}", name)
            filepath.write_text(text, encoding="utf-8")

    print(f"Profile created: {dest}")
    print("\nNext steps:")
    print(
        f"  1. Edit {dest}/SKILL.md"
        " — fill in your identity and goals"
    )
    print(
        f"  2. Edit {dest}/skill-tree.yaml"
        " — copy node IDs from schemas/"
    )
    print(f"  3. Run:  nblane context {name}")
    print(f"  4. Optional: edit {dest}/agent-profile.yaml")

def cmd_context(
    name: str,
    mode: str,
    no_kanban: bool,
) -> None:
    """Print agent system prompt to stdout."""
    _require_profile(name)
    from nblane.core.context import generate

    try:
        prompt = generate(
            name,
            mode=mode,
            include_kanban=not no_kanban,
        )
        print(prompt)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

def cmd_status(name: str | None) -> None:
    """Print skill tree summary."""
    from nblane.core.status import (
        summarize_all,
        summarize_profile,
    )

    if name is not None:
        summarize_profile(_require_profile(name))
    else:
        summarize_all()

def cmd_log(name: str, event: str) -> None:
    """Append a dated entry to the growth log in SKILL.md."""
    from nblane.core.growth_log import append_growth_log_row

    profile_dir = _require_profile(name)
    try:
        append_growth_log_row(profile_dir, event)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    except OSError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    today = date.today().strftime("%Y-%m")
    print(f"Logged [{today}]: {event}")

def cmd_sync(
    name: str,
    check: bool,
    write: bool,
) -> None:
    """Check or sync generated SKILL.md blocks."""
    profile_dir = _require_profile(name)
    from nblane.core.sync import (
        get_drifted_blocks,
        write_generated_blocks,
    )

    try:
        if write:
            write_generated_blocks(profile_dir)
            print(
                "Synced generated blocks: "
                f"{profile_dir / 'SKILL.md'}"
            )
        else:
            drifted = get_drifted_blocks(profile_dir)
            if drifted:
                names = ", ".join(drifted)
                print(
                    "Drift detected in generated "
                    f"blocks: {names}"
                )
                sys.exit(1)
            print("Sync check passed.")
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

def cmd_validate(name: str | None) -> None:
    """Validate skill-tree vs schema."""
    from nblane.core.validate import (
        print_results,
        run_all_profiles,
        validate_one,
    )

    if name is not None:
        p = _require_profile(name)
        err, warn = validate_one(p)
        sys.exit(print_results(err, warn))
    else:
        err, warn = run_all_profiles()
        sys.exit(print_results(err, warn))
