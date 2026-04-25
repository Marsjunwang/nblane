"""Evidence CLI commands."""

from __future__ import annotations

import argparse
import sys

from nblane.commands.common import _require_profile
from nblane.core.evidence_pool_id import (
    fingerprint_match_id,
    new_evidence_id,
)
from nblane.core.models import EVIDENCE_TYPES


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
