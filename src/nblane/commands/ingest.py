"""Ingest CLI commands."""

from __future__ import annotations

import sys
from pathlib import Path


def cmd_ingest_resume(
    name: str,
    *,
    file_path: str | None,
    use_stdin: bool,
    dry_run: bool,
    allow_status_change: bool,
    bump_locked_with_evidence: bool,
) -> None:
    """LLM resume text → pool + skill-tree (validate + sync)."""
    import yaml

    _require_profile(name)
    from nblane.core.profile_ingest import run_ingest_patch
    from nblane.core.profile_ingest_llm import ingest_resume_json

    if use_stdin:
        text = sys.stdin.read()
    elif file_path:
        text = Path(file_path).read_text(encoding="utf-8")
    else:
        print(
            "Provide --file PATH or --stdin for resume text.",
            file=sys.stderr,
        )
        sys.exit(1)

    patch, err = ingest_resume_json(name, text)
    if err is not None:
        print(f"ERROR: {err}", file=sys.stderr)
        sys.exit(1)
    if patch is None:
        print("ERROR: empty patch from LLM.", file=sys.stderr)
        sys.exit(1)

    merge, apply = run_ingest_patch(
        name,
        patch,
        allow_status_change=allow_status_change,
        bump_locked_with_evidence=bump_locked_with_evidence,
        dry_run=dry_run,
    )
    for w in merge.warnings:
        print(f"WARN: {w}", file=sys.stderr)
    if not merge.ok:
        for e in merge.errors:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    if dry_run:
        print(
            yaml.dump(
                merge.merged_pool,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            )
        )
        print("---")
        print(
            yaml.dump(
                merge.merged_tree,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            )
        )
        sys.exit(0)
    if not apply.ok:
        for e in apply.errors:
            print(f"ERROR: {e}", file=sys.stderr)
        for w in apply.warnings:
            print(f"WARN: {w}", file=sys.stderr)
        sys.exit(1)
    for w in apply.warnings:
        print(f"WARN: {w}", file=sys.stderr)
    print(
        f"Ingest applied for profile {name!r}: "
        "evidence-pool.yaml, skill-tree.yaml, SKILL.md sync."
    )

def cmd_ingest_kanban(
    name: str,
    *,
    dry_run: bool,
    allow_status_change: bool,
    bump_locked_with_evidence: bool,
) -> None:
    """LLM on kanban Done tasks → pool + skill-tree."""
    import yaml

    _require_profile(name)
    from nblane.core.io import KANBAN_DONE, parse_kanban
    from nblane.core.profile_ingest import run_ingest_patch
    from nblane.core.profile_ingest_llm import ingest_kanban_done_json

    sections = parse_kanban(name)
    done_tasks = sections.get(KANBAN_DONE) or []
    patch, err = ingest_kanban_done_json(name, done_tasks)
    if err is not None:
        print(f"ERROR: {err}", file=sys.stderr)
        sys.exit(1)
    if patch is None:
        print("ERROR: empty patch from LLM.", file=sys.stderr)
        sys.exit(1)

    merge, apply = run_ingest_patch(
        name,
        patch,
        allow_status_change=allow_status_change,
        bump_locked_with_evidence=bump_locked_with_evidence,
        dry_run=dry_run,
    )
    for w in merge.warnings:
        print(f"WARN: {w}", file=sys.stderr)
    if not merge.ok:
        for e in merge.errors:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    if dry_run:
        print(
            yaml.dump(
                merge.merged_pool,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            )
        )
        print("---")
        print(
            yaml.dump(
                merge.merged_tree,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            )
        )
        sys.exit(0)
    if not apply.ok:
        for e in apply.errors:
            print(f"ERROR: {e}", file=sys.stderr)
        for w in apply.warnings:
            print(f"WARN: {w}", file=sys.stderr)
        sys.exit(1)
    for w in apply.warnings:
        print(f"WARN: {w}", file=sys.stderr)
    print(
        f"Ingest applied for profile {name!r}: "
        "evidence-pool.yaml, skill-tree.yaml, SKILL.md sync."
    )
