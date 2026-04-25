"""nblane -- CLI entry point.

Commands:
    nblane init <name>              Create a new profile
    nblane context <name> [--mode | --chat | --review | ...]
                                    Print agent system prompt
    nblane status [name]            Show skill tree summary
    nblane log <name> <event>       Append growth log entry
    nblane sync <name> [--check|--write]
                                    Sync generated sections
    nblane validate [name]          Validate skill-tree
    nblane gap <name> [task]        Task -> skills / gaps
    nblane team <team_id>           Show team summary
    nblane evidence <name> <skill_id> add --type <t> --title <t>
                                    Append inline evidence on a node
    nblane evidence <name> pool add --type <t> --title <t>
                                    Create a pool record (shared id)
    nblane evidence <name> pool remove <evidence_id> [--prune-refs]
                                    Remove a pool row (see docs/evidence.md)
    nblane evidence <name> pool deprecate <evidence_id> [--replaced-by ID]
                                    Mark pool row deprecated (soft retire)
    nblane evidence <name> link <skill_id> <evidence_id>
                                    Attach pool id to a node
    nblane evidence <name> unlink <skill_id> <evidence_id>
                                    Remove pool id from that node's refs
    nblane ingest-resume <name> --file path | --stdin
                                    Resume text → pool + tree (LLM)
    nblane ingest-kanban <name>     Done column → pool + tree (LLM)

Examples:
    nblane init alice
    nblane context alice
    nblane context alice --mode review
    nblane context alice --review
    nblane status
    nblane log alice "finished first manipulation demo"
    nblane sync alice --check
    nblane validate
    nblane gap alice "VLM robot control"
    nblane team example-team
    nblane evidence alice ros2_basics add \\
        --type project --title "Bringup demo"
    nblane evidence alice pool add --type project --title "Demo"
    nblane evidence alice pool remove 20260322_demo --prune-refs
    nblane evidence alice unlink ros2_basics 20260322_demo
    nblane evidence alice link ros2_basics 20260322_demo
"""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import date
from pathlib import Path

from nblane.core.evidence_pool_id import (
    fingerprint_match_id,
    new_evidence_id,
)
from nblane.core.models import EVIDENCE_TYPES
from nblane.core.paths import (
    PROFILES_DIR,
    TEAMS_DIR,
    TEMPLATE_DIR,
)


def _profile_dir(name: str) -> Path:
    """Return the profile directory path."""
    return PROFILES_DIR / name


def _require_profile(name: str) -> Path:
    """Return profile dir, exit if not found."""
    d = _profile_dir(name)
    if not d.exists():
        print(
            f"Profile '{name}' not found. "
            f"Run: nblane init {name}",
            file=sys.stderr,
        )
        sys.exit(1)
    return d


# -- commands ---------------------------------------------------------------


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


def cmd_gap(
    name: str,
    task: str,
    node: str | None,
    *,
    use_llm_router: bool = False,
    use_rule_match: bool = True,
) -> None:
    """Run gap analysis."""
    _require_profile(name)
    from nblane.core.gap import analyze, format_text

    result = analyze(
        name,
        task,
        explicit_node=node,
        use_llm_router=use_llm_router,
        use_rule_match=use_rule_match,
    )
    print(format_text(result))
    if result.error:
        sys.exit(1)


def cmd_evidence_add(
    name: str,
    skill_id: str,
    *,
    type_: str,
    title: str,
    date: str,
    url: str,
    summary: str,
) -> None:
    """Append one evidence item to a skill-tree node."""
    from nblane.core.skill_evidence_inline import (
        add_inline_evidence,
    )

    _require_profile(name)
    try:
        add_inline_evidence(
            name,
            skill_id,
            type_=type_,
            title=title,
            date=date,
            url=url,
            summary=summary,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    print(
        f"Evidence added on {skill_id!r}: {title.strip()!r}"
    )


def cmd_evidence_pool_add(
    name: str,
    argv: list[str],
) -> None:
    """Create or upsert one row in evidence-pool.yaml."""
    from nblane.core.io import (
        load_evidence_pool_raw,
        save_evidence_pool,
    )

    _require_profile(name)
    pa = argparse.ArgumentParser(
        prog="nblane evidence <name> pool add",
        add_help=False,
    )
    pa.add_argument(
        "--type",
        dest="ev_type",
        required=True,
        choices=sorted(EVIDENCE_TYPES),
    )
    pa.add_argument("--title", required=True)
    pa.add_argument("--id", dest="ev_id", default="")
    pa.add_argument("--date", default="")
    pa.add_argument("--url", default="")
    pa.add_argument("--summary", default="")
    opts = pa.parse_args(argv)

    title = opts.title.strip()
    if not title:
        print("--title must be non-empty.", file=sys.stderr)
        sys.exit(1)

    raw = load_evidence_pool_raw(name)
    if raw is None:
        raw = {
            "profile": name,
            "updated": "",
            "evidence_entries": [],
        }
    entries = list(raw.get("evidence_entries") or [])
    if not isinstance(entries, list):
        entries = []

    plain_entries = [e for e in entries if isinstance(e, dict)]
    existing_ids = {
        str(e.get("id", "") or "")
        for e in plain_entries
        if str(e.get("id", "") or "").strip()
    }

    fp_id = fingerprint_match_id(
        plain_entries,
        opts.ev_type,
        title,
        opts.date,
    )
    if fp_id is not None:
        print(
            f"Evidence pool upsert (existing): id={fp_id!r}"
        )
        return

    ev_id = opts.ev_id.strip()
    if ev_id:
        if ev_id in existing_ids:
            print(
                f"ERROR: id {ev_id!r} already exists.",
                file=sys.stderr,
            )
            sys.exit(1)
    else:
        ev_id = new_evidence_id(title, existing_ids)

    row: dict = {
        "id": ev_id,
        "type": opts.ev_type,
        "title": title,
    }
    if opts.date.strip():
        row["date"] = opts.date.strip()
    if opts.url.strip():
        row["url"] = opts.url.strip()
    if opts.summary.strip():
        row["summary"] = opts.summary.strip()

    plain_entries.append(row)
    raw["profile"] = name
    raw["evidence_entries"] = plain_entries
    save_evidence_pool(name, raw)
    print(f"Evidence pool record: id={ev_id!r}")


def cmd_evidence_link(
    name: str,
    skill_id: str,
    evidence_id: str,
) -> None:
    """Append evidence_id to a node's evidence_refs if missing."""
    from nblane.core.io import (
        load_schema_raw,
        load_skill_tree_raw,
        save_skill_tree,
        schema_node_index,
    )

    profile_dir = _require_profile(name)
    tree = load_skill_tree_raw(profile_dir)
    if tree is None:
        print("skill-tree.yaml not found.", file=sys.stderr)
        sys.exit(1)

    schema_name = tree.get("schema")
    if not schema_name:
        print(
            "skill-tree.yaml has no 'schema' field.",
            file=sys.stderr,
        )
        sys.exit(1)

    schema_data = load_schema_raw(str(schema_name))
    if schema_data is None:
        print(
            f"Schema not found: {schema_name!r}",
            file=sys.stderr,
        )
        sys.exit(1)

    index = schema_node_index(schema_data)
    if skill_id not in index:
        print(
            f"Unknown skill id (not in schema): {skill_id!r}",
            file=sys.stderr,
        )
        sys.exit(1)

    eid = evidence_id.strip()
    if not eid:
        print("evidence_id must be non-empty.", file=sys.stderr)
        sys.exit(1)

    nodes = list(tree.get("nodes") or [])
    found: dict | None = None
    for n in nodes:
        if n.get("id") == skill_id:
            found = n
            break

    if found is None:
        nodes.append(
            {
                "id": skill_id,
                "status": "learning",
                "evidence_refs": [eid],
            }
        )
    else:
        refs = found.setdefault("evidence_refs", [])
        if not isinstance(refs, list):
            refs = []
            found["evidence_refs"] = refs
        str_refs = [r for r in refs if isinstance(r, str)]
        if eid not in [r.strip() for r in str_refs]:
            str_refs.append(eid)
        found["evidence_refs"] = str_refs

    tree["nodes"] = nodes
    save_skill_tree(name, tree)
    print(
        f"Linked {eid!r} -> node {skill_id!r} "
        f"(evidence_refs)"
    )


def cmd_evidence_unlink(
    name: str,
    skill_id: str,
    evidence_id: str,
) -> None:
    """Remove evidence_id from one node's evidence_refs."""
    from nblane.core.io import (
        load_schema_raw,
        load_skill_tree_raw,
        save_skill_tree,
        schema_node_index,
    )
    from nblane.core.sync import write_generated_blocks

    profile_dir = _require_profile(name)
    tree = load_skill_tree_raw(profile_dir)
    if tree is None:
        print(
            "skill-tree.yaml not found.",
            file=sys.stderr,
        )
        sys.exit(1)

    schema_name = tree.get("schema")
    if not schema_name:
        print(
            "skill-tree.yaml has no 'schema' field.",
            file=sys.stderr,
        )
        sys.exit(1)

    schema_data = load_schema_raw(str(schema_name))
    if schema_data is None:
        print(
            f"Schema not found: {schema_name!r}",
            file=sys.stderr,
        )
        sys.exit(1)

    index = schema_node_index(schema_data)
    if skill_id not in index:
        print(
            f"Unknown skill id (not in schema): {skill_id!r}",
            file=sys.stderr,
        )
        sys.exit(1)

    eid = evidence_id.strip()
    if not eid:
        print(
            "evidence_id must be non-empty.",
            file=sys.stderr,
        )
        sys.exit(1)

    nodes = list(tree.get("nodes") or [])
    found: dict | None = None
    for n in nodes:
        if n.get("id") == skill_id:
            found = n
            break

    if found is None:
        print(
            f"Node {skill_id!r} not in skill-tree overlay; "
            "nothing to unlink."
        )
        return

    refs = found.get("evidence_refs")
    if not isinstance(refs, list) or not refs:
        print(
            f"{eid!r} was not linked on {skill_id!r} "
            "(no evidence_refs)."
        )
        return

    uniq: list[str] = []
    seen: set[str] = set()
    for r in refs:
        if not isinstance(r, str):
            continue
        key = r.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        uniq.append(key)

    if eid not in uniq:
        print(
            f"{eid!r} was not linked on {skill_id!r}."
        )
        return

    new_refs = [x for x in uniq if x != eid]
    if new_refs:
        found["evidence_refs"] = new_refs
    else:
        found.pop("evidence_refs", None)

    tree["nodes"] = nodes
    save_skill_tree(name, tree)

    skill_md = profile_dir / "SKILL.md"
    if skill_md.exists():
        try:
            write_generated_blocks(profile_dir)
        except (OSError, ValueError) as exc:
            print(
                f"WARN: SKILL.md sync failed: {exc}",
                file=sys.stderr,
            )
    print(
        f"Unlinked {eid!r} from node {skill_id!r}."
    )


def cmd_evidence_pool_remove(
    name: str,
    argv: list[str],
) -> None:
    """Remove one evidence-pool row; optional ref prune."""
    from nblane.core.evidence_ops import (
        pool_id_referenced_by_nodes,
        prune_pool_id_from_tree,
    )
    from nblane.core.io import (
        load_evidence_pool_raw,
        load_skill_tree_raw,
    )
    from nblane.core.profile_ingest import apply_merged_profile

    profile_dir = _require_profile(name)
    pa = argparse.ArgumentParser(
        prog="nblane evidence <name> pool remove",
        add_help=False,
    )
    pa.add_argument("evidence_id")
    pa.add_argument(
        "--prune-refs",
        action="store_true",
    )
    opts = pa.parse_args(argv)
    eid = opts.evidence_id.strip()
    if not eid:
        print(
            "evidence_id must be non-empty.",
            file=sys.stderr,
        )
        sys.exit(1)

    tree = load_skill_tree_raw(profile_dir)
    if tree is None:
        print(
            "skill-tree.yaml not found.",
            file=sys.stderr,
        )
        sys.exit(1)

    pool_raw = load_evidence_pool_raw(name)
    if pool_raw is None:
        print(
            "evidence-pool.yaml not found.",
            file=sys.stderr,
        )
        sys.exit(1)

    entries = list(pool_raw.get("evidence_entries") or [])
    plain_entries = [e for e in entries if isinstance(e, dict)]
    new_plain: list[dict] = []
    found_row = False
    for e in plain_entries:
        pid = str(e.get("id", "") or "").strip()
        if pid == eid:
            found_row = True
            continue
        new_plain.append(dict(e))

    if not found_row:
        print(
            f"ERROR: pool id {eid!r} not found.",
            file=sys.stderr,
        )
        sys.exit(1)

    refs = pool_id_referenced_by_nodes(tree, eid)
    if refs and not opts.prune_refs:
        nodes_s = ", ".join(refs)
        print(
            f"ERROR: {eid!r} is still referenced by nodes: "
            f"{nodes_s}",
            file=sys.stderr,
        )
        print(
            "Use --prune-refs to remove those refs and "
            "delete the pool row.",
            file=sys.stderr,
        )
        sys.exit(1)

    new_tree = tree
    if opts.prune_refs:
        new_tree = prune_pool_id_from_tree(tree, eid)

    merged_pool = {
        "profile": name,
        "evidence_entries": new_plain,
    }
    outcome = apply_merged_profile(
        name,
        merged_pool,
        new_tree,
    )
    if not outcome.ok:
        for err in outcome.errors:
            print(err, file=sys.stderr)
        sys.exit(1)
    for w in outcome.warnings:
        print(w)
    print(f"Removed pool evidence {eid!r}.")


def cmd_evidence_pool_deprecate(
    name: str,
    argv: list[str],
) -> None:
    """Set deprecated on a pool row (optional replaced_by)."""
    from nblane.core.io import (
        load_evidence_pool_raw,
        save_evidence_pool,
    )
    from nblane.core.sync import write_generated_blocks
    from nblane.core.validate import validate_one

    profile_dir = _require_profile(name)
    pa = argparse.ArgumentParser(
        prog="nblane evidence <name> pool deprecate",
        add_help=False,
    )
    pa.add_argument("evidence_id")
    pa.add_argument(
        "--replaced-by",
        default="",
        dest="replaced_by",
    )
    opts = pa.parse_args(argv)
    eid = opts.evidence_id.strip()
    if not eid:
        print(
            "evidence_id must be non-empty.",
            file=sys.stderr,
        )
        sys.exit(1)
    rb = str(opts.replaced_by or "").strip()

    pool_raw = load_evidence_pool_raw(name)
    if pool_raw is None:
        print(
            "evidence-pool.yaml not found.",
            file=sys.stderr,
        )
        sys.exit(1)

    entries = list(pool_raw.get("evidence_entries") or [])
    plain_entries = [e for e in entries if isinstance(e, dict)]
    hit = False
    new_plain: list[dict] = []
    for e in plain_entries:
        row = dict(e)
        pid = str(row.get("id", "") or "").strip()
        if pid == eid:
            hit = True
            row["deprecated"] = True
            if rb:
                row["replaced_by"] = rb
            else:
                row.pop("replaced_by", None)
        new_plain.append(row)

    if not hit:
        print(
            f"ERROR: pool id {eid!r} not found.",
            file=sys.stderr,
        )
        sys.exit(1)

    pool_raw["profile"] = name
    pool_raw["evidence_entries"] = new_plain
    save_evidence_pool(name, pool_raw)

    errors, warnings = validate_one(profile_dir, check_sync=False)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        sys.exit(1)
    for w in warnings:
        print(w)

    skill_md = profile_dir / "SKILL.md"
    if skill_md.exists():
        try:
            write_generated_blocks(profile_dir)
        except (OSError, ValueError) as exc:
            print(
                f"WARN: SKILL.md sync failed: {exc}",
                file=sys.stderr,
            )
    print(
        f"Deprecated pool evidence {eid!r}"
        + (f" (replaced_by={rb!r})" if rb else "")
        + "."
    )


def cmd_evidence_dispatch(name: str, tokens: list[str]) -> None:
    """Handle ``evidence`` sub-commands from remainder argv."""
    if not tokens:
        print(
            "Usage: nblane evidence <name> pool add | pool remove | "
            "pool deprecate | link | unlink | <skill_id> add ...",
            file=sys.stderr,
        )
        sys.exit(1)

    head = tokens[0]
    if head == "unlink":
        if len(tokens) < 3:
            print(
                "Expected: nblane evidence <name> unlink "
                "<skill_id> <evidence_id>",
                file=sys.stderr,
            )
            sys.exit(1)
        cmd_evidence_unlink(name, tokens[1], tokens[2])
        return

    if head == "pool":
        if len(tokens) < 2:
            print(
                "Expected: nblane evidence <name> pool add | "
                "pool remove | pool deprecate ...",
                file=sys.stderr,
            )
            sys.exit(1)
        sub = tokens[1]
        if sub == "add":
            cmd_evidence_pool_add(name, tokens[2:])
            return
        if sub == "remove":
            cmd_evidence_pool_remove(name, tokens[2:])
            return
        if sub == "deprecate":
            cmd_evidence_pool_deprecate(name, tokens[2:])
            return
        print(
            "Expected: nblane evidence <name> pool add | "
            "pool remove | pool deprecate ...",
            file=sys.stderr,
        )
        sys.exit(1)

    if head == "link":
        if len(tokens) < 3:
            print(
                "Expected: nblane evidence <name> link "
                "<skill_id> <evidence_id>",
                file=sys.stderr,
            )
            sys.exit(1)
        cmd_evidence_link(name, tokens[1], tokens[2])
        return

    if len(tokens) >= 2 and tokens[1] == "add":
        skill_id = head
        pa = argparse.ArgumentParser(
            prog="nblane evidence <name> <skill_id> add",
            add_help=False,
        )
        pa.add_argument(
            "--type",
            dest="ev_type",
            required=True,
            choices=sorted(EVIDENCE_TYPES),
        )
        pa.add_argument("--title", required=True)
        pa.add_argument("--date", default="")
        pa.add_argument("--url", default="")
        pa.add_argument("--summary", default="")
        opts = pa.parse_args(tokens[2:])
        cmd_evidence_add(
            name,
            skill_id,
            type_=opts.ev_type,
            title=opts.title,
            date=opts.date,
            url=opts.url,
            summary=opts.summary,
        )
        return

    print(
        "Expected: pool add | pool remove | pool deprecate | "
        "link | unlink | <skill_id> add ...",
        file=sys.stderr,
    )
    sys.exit(1)


def cmd_team(team_id: str) -> None:
    """Show team summary."""
    team_dir = TEAMS_DIR / team_id
    if not team_dir.is_dir():
        print(
            f"Team directory not found: {team_dir}",
            file=sys.stderr,
        )
        sys.exit(1)
    from nblane.core.team import summarize_team

    sys.exit(summarize_team(team_dir))


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


def main() -> None:
    """Parse arguments and dispatch to command handlers."""
    parser = argparse.ArgumentParser(
        prog="nblane",
        description=(
            "nblane — track the path to becoming "
            "a domain expert."
        ),
    )
    sub = parser.add_subparsers(
        dest="command", required=True
    )

    p_init = sub.add_parser(
        "init", help="Create a new profile"
    )
    p_init.add_argument(
        "name",
        help="Profile name (e.g. your GitHub handle)",
    )

    p_ctx = sub.add_parser(
        "context",
        help="Generate agent system prompt from a profile",
        epilog=(
            "Mode shortcuts: --chat, --review, --write, --plan "
            "(equivalent to --mode <name>). Default is chat."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_ctx.add_argument("name", help="Profile name")
    ctx_mode = p_ctx.add_mutually_exclusive_group()
    ctx_mode.add_argument(
        "--mode",
        choices=["chat", "review", "write", "plan"],
        dest="context_mode",
        help="Prompt mode (default: chat)",
    )
    for _mode in ("chat", "review", "write", "plan"):
        ctx_mode.add_argument(
            f"--{_mode}",
            action="store_const",
            const=_mode,
            dest="context_mode",
            help=argparse.SUPPRESS,
        )
    p_ctx.add_argument(
        "--no-kanban",
        action="store_true",
        help="Exclude kanban.md from the prompt",
    )

    p_status = sub.add_parser(
        "status", help="Show skill tree summary"
    )
    p_status.add_argument(
        "name", nargs="?", default=None
    )

    p_log = sub.add_parser(
        "log", help="Append entry to growth log"
    )
    p_log.add_argument("name", help="Profile name")
    p_log.add_argument(
        "event", help="What happened (quoted string)"
    )

    p_sync = sub.add_parser(
        "sync",
        help="Sync generated SKILL.md sections",
    )
    p_sync.add_argument("name", help="Profile name")
    mode_group = p_sync.add_mutually_exclusive_group(
        required=True
    )
    mode_group.add_argument(
        "--check",
        action="store_true",
        help="Check generated section drift only",
    )
    mode_group.add_argument(
        "--write",
        action="store_true",
        help="Rewrite generated sections in SKILL.md",
    )

    p_val = sub.add_parser(
        "validate",
        help="Validate skill-tree.yaml against schemas/",
    )
    p_val.add_argument(
        "name",
        nargs="?",
        default=None,
        help="Profile name (omit to validate all)",
    )

    p_gap = sub.add_parser(
        "gap",
        help="Match a task to skills and list gaps",
    )
    p_gap.add_argument("name", help="Profile name")
    p_gap.add_argument(
        "task",
        nargs="?",
        default="",
        help="Natural language task (optional if --node)",
    )
    p_gap.add_argument(
        "--node",
        dest="node",
        default=None,
        help="Target schema node id",
    )
    p_gap.add_argument(
        "--llm-router",
        action="store_true",
        help="Use LLM to suggest schema nodes (requires API key)",
    )
    p_gap.add_argument(
        "--no-rule",
        action="store_true",
        help="Disable rule-based keyword overlap",
    )

    p_team = sub.add_parser(
        "team",
        help="Show team.yaml and product-pool summary",
    )
    p_team.add_argument(
        "team_id",
        help="Directory name under teams/",
    )

    p_evidence = sub.add_parser(
        "evidence",
        help=(
            "Inline evidence, evidence pool, or link pool id "
            "to a skill"
        ),
    )
    p_evidence.add_argument("name", help="Profile name")
    p_evidence.add_argument(
        "tokens",
        nargs=argparse.REMAINDER,
        help=(
            "pool add|remove|deprecate | link | unlink | "
            "<skill_id> add …"
        ),
    )

    p_ing_res = sub.add_parser(
        "ingest-resume",
        help=(
            "Ingest resume or long text via LLM into "
            "evidence pool + skill tree"
        ),
    )
    p_ing_res.add_argument("name", help="Profile name")
    src = p_ing_res.add_mutually_exclusive_group(
        required=True
    )
    src.add_argument(
        "--file",
        dest="resume_file",
        metavar="PATH",
        help="Path to resume text file",
    )
    src.add_argument(
        "--stdin",
        action="store_true",
        help="Read resume text from stdin",
    )
    p_ing_res.add_argument(
        "--dry-run",
        action="store_true",
        help="Print merged YAML only; do not write",
    )
    p_ing_res.add_argument(
        "--allow-status-change",
        action="store_true",
        help="Apply status fields from the LLM patch",
    )
    p_ing_res.add_argument(
        "--no-bump-locked",
        action="store_true",
        help=(
            "Do not set learning on nodes that remain locked "
            "but have evidence"
        ),
    )

    p_ing_kan = sub.add_parser(
        "ingest-kanban",
        help=(
            "Ingest kanban Done tasks via LLM into "
            "evidence pool + skill tree"
        ),
    )
    p_ing_kan.add_argument("name", help="Profile name")
    p_ing_kan.add_argument(
        "--dry-run",
        action="store_true",
        help="Print merged YAML only; do not write",
    )
    p_ing_kan.add_argument(
        "--allow-status-change",
        action="store_true",
        help="Apply status fields from the LLM patch",
    )
    p_ing_kan.add_argument(
        "--no-bump-locked",
        action="store_true",
        help=(
            "Do not set learning on nodes that remain locked "
            "but have evidence"
        ),
    )

    p_sync_cur = sub.add_parser(
        "sync-cursor",
        help=(
            "Write .cursor/rules/nblane-context.mdc from profile "
            "summary"
        ),
    )
    p_sync_cur.add_argument("name", help="Profile name")

    p_cryst = sub.add_parser(
        "crystallize",
        help="Write a method draft under profiles/<name>/methods/",
    )
    p_cryst.add_argument("name", help="Profile name")
    p_cryst.add_argument(
        "project",
        help="Project or session label (used in filename)",
    )
    p_cryst.add_argument(
        "--file",
        dest="crystallize_file",
        metavar="PATH",
        default=None,
        help="Read draft body from file (utf-8)",
    )
    p_cryst.add_argument(
        "--stdin",
        action="store_true",
        help="Read draft body from stdin",
    )

    args = parser.parse_args()

    if args.command == "init":
        cmd_init(args.name)
    elif args.command == "context":
        ctx_mode = (
            args.context_mode
            if args.context_mode is not None
            else "chat"
        )
        cmd_context(args.name, ctx_mode, args.no_kanban)
    elif args.command == "status":
        cmd_status(args.name)
    elif args.command == "log":
        cmd_log(args.name, args.event)
    elif args.command == "sync":
        cmd_sync(args.name, args.check, args.write)
    elif args.command == "validate":
        cmd_validate(args.name)
    elif args.command == "gap":
        cmd_gap(
            args.name,
            args.task,
            args.node,
            use_llm_router=args.llm_router,
            use_rule_match=not args.no_rule,
        )
    elif args.command == "team":
        cmd_team(args.team_id)
    elif args.command == "evidence":
        cmd_evidence_dispatch(args.name, args.tokens)
    elif args.command == "ingest-resume":
        cmd_ingest_resume(
            args.name,
            file_path=args.resume_file,
            use_stdin=args.stdin,
            dry_run=args.dry_run,
            allow_status_change=args.allow_status_change,
            bump_locked_with_evidence=not args.no_bump_locked,
        )
    elif args.command == "ingest-kanban":
        cmd_ingest_kanban(
            args.name,
            dry_run=args.dry_run,
            allow_status_change=args.allow_status_change,
            bump_locked_with_evidence=not args.no_bump_locked,
        )
    elif args.command == "sync-cursor":
        cmd_sync_cursor(args.name)
    elif args.command == "crystallize":
        if args.stdin:
            body = sys.stdin.read()
        elif args.crystallize_file:
            from pathlib import Path

            body = Path(
                args.crystallize_file
            ).read_text(encoding="utf-8")
        else:
            body = (
                "_Add playbook notes here. "
                "Re-run with --file or --stdin for content._\n"
            )
        cmd_crystallize(args.name, args.project, body)


if __name__ == "__main__":
    main()
