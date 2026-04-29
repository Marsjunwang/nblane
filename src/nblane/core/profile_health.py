"""Deterministic profile health checks for growth review."""

from __future__ import annotations

from dataclasses import dataclass, field

from nblane.core import io as io_facade
from nblane.core.evidence_resolve import resolved_evidence_count
from nblane.core.io import (
    KANBAN_DONE,
    load_evidence_pool,
    load_schema_raw,
    load_skill_tree_raw,
    parse_kanban,
    profile_dir,
    schema_node_index,
)
from nblane.core.sync import get_drifted_blocks
from nblane.core.validate import validate_one

HEALTH_SEVERITIES = ("error", "warning", "info")
HEALTH_CATEGORIES = (
    "validate",
    "sync",
    "evidence",
    "kanban",
    "freshness",
)


@dataclass
class HealthIssue:
    """One actionable profile health finding."""

    severity: str
    category: str
    title: str
    detail: str = ""
    action: str = ""


@dataclass
class HealthReport:
    """Health summary for one profile."""

    profile: str
    issues: list[HealthIssue] = field(default_factory=list)
    can_publish_context: bool = True

    @property
    def summary_counts(self) -> dict[str, int]:
        """Count issues by severity."""
        counts = {s: 0 for s in HEALTH_SEVERITIES}
        for issue in self.issues:
            if issue.severity in counts:
                counts[issue.severity] += 1
        return counts


def _issue(
    severity: str,
    category: str,
    title: str,
    detail: str = "",
    action: str = "",
) -> HealthIssue:
    """Build a health issue with normalized severity/category."""
    sev = severity if severity in HEALTH_SEVERITIES else "info"
    cat = category if category in HEALTH_CATEGORIES else "freshness"
    return HealthIssue(
        severity=sev,
        category=cat,
        title=title,
        detail=detail,
        action=action,
    )


def _schema_labels(tree_raw: dict | None) -> dict[str, str]:
    """Return node id -> schema label for a tree snapshot."""
    if not isinstance(tree_raw, dict):
        return {}
    schema_name = tree_raw.get("schema")
    if not schema_name:
        return {}
    schema_raw = load_schema_raw(str(schema_name))
    if schema_raw is None:
        return {}
    return {
        nid: str(meta.get("label") or nid)
        for nid, meta in schema_node_index(schema_raw).items()
    }


def _validate_issues(profile_name: str) -> tuple[list[HealthIssue], bool]:
    """Run validate and return issues plus publish-blocking flag."""
    pdir = profile_dir(profile_name)
    errors, warnings = validate_one(pdir, check_sync=False)
    issues: list[HealthIssue] = []
    for err in errors:
        issues.append(
            _issue(
                "error",
                "validate",
                "Validation error",
                err,
                "Fix profile YAML and rerun nblane validate.",
            )
        )
    for warn in warnings:
        issues.append(
            _issue(
                "warning",
                "validate",
                "Validation warning",
                warn,
                "Review the warning; promote prerequisites or adjust status.",
            )
        )
    return issues, bool(errors)


def _sync_issues(profile_name: str) -> tuple[list[HealthIssue], bool]:
    """Report generated block drift as sync issues."""
    pdir = profile_dir(profile_name)
    try:
        drifted = get_drifted_blocks(pdir)
    except ValueError as exc:
        return [
            _issue(
                "error",
                "sync",
                "Generated block sync check failed",
                str(exc),
                f"Restore SKILL.md markers or run nblane sync {profile_name} --write.",
            )
        ], True
    if not drifted:
        return [], False
    joined = ", ".join(drifted)
    return [
        _issue(
            "error",
            "sync",
            "Generated SKILL.md blocks drifted",
            f"Drifted blocks: {joined}",
            f"Run nblane sync {profile_name} --write.",
        )
    ], True


def _evidence_issues(
    profile_path,
    tree_raw: dict | None,
) -> list[HealthIssue]:
    """Warn when solid/expert nodes lack materialized evidence."""
    if not isinstance(tree_raw, dict):
        return []
    pool = load_evidence_pool(profile_path)
    labels = _schema_labels(tree_raw)
    issues: list[HealthIssue] = []
    for node in tree_raw.get("nodes") or []:
        if not isinstance(node, dict):
            continue
        status = str(node.get("status", "locked") or "locked")
        if status not in ("solid", "expert"):
            continue
        if resolved_evidence_count(node, pool) > 0:
            continue
        nid = str(node.get("id", "") or "").strip()
        label = labels.get(nid, nid)
        issues.append(
            _issue(
                "warning",
                "evidence",
                "Solid/expert node has no evidence",
                f"{nid} ({label}) is {status} with no resolved evidence.",
                "Add inline evidence or link an evidence-pool record.",
            )
        )
    return issues


def _kanban_issues(profile_name: str, profile_path) -> list[HealthIssue]:
    """Surface inconsistent Kanban crystallization state."""
    old_profile_dir = io_facade.profile_dir
    try:
        io_facade.profile_dir = lambda _name: profile_path
        sections = parse_kanban(profile_name)
    except OSError as exc:
        return [
            _issue(
                "warning",
                "kanban",
                "Kanban could not be read",
                str(exc),
                "Check kanban.md permissions and format.",
            )
        ]
    finally:
        io_facade.profile_dir = old_profile_dir
    issues: list[HealthIssue] = []
    non_done_crystallized: list[str] = []
    for section, tasks in sections.items():
        if section == KANBAN_DONE:
            continue
        for task in tasks:
            if getattr(task, "crystallized", False):
                non_done_crystallized.append(f"{task.title} ({section})")
    if non_done_crystallized:
        preview = ", ".join(non_done_crystallized[:5])
        if len(non_done_crystallized) > 5:
            preview += f", ... (+{len(non_done_crystallized) - 5} more)"
        issues.append(
            _issue(
                "warning",
                "kanban",
                "Non-Done tasks marked crystallized",
                f"{len(non_done_crystallized)} task(s): {preview}",
                "Remove crystallized: true outside Done tasks.",
            )
        )

    done = sections.get(KANBAN_DONE) or []
    pending = [
        task.title
        for task in done
        if not getattr(task, "crystallized", False)
    ]
    if not pending:
        return issues
    preview = ", ".join(pending[:5])
    if len(pending) > 5:
        preview += f", ... (+{len(pending) - 5} more)"
    issues.append(
        _issue(
            "info",
            "kanban",
            "Done tasks not crystallized",
            f"{len(pending)} Done task(s): {preview}",
            "Use Kanban Done -> evidence to crystallize finished work.",
        )
    )
    return issues


def _tree_shape_issues(tree_raw: dict | None) -> list[HealthIssue]:
    """Check for empty or incomplete skill-tree shape."""
    if not isinstance(tree_raw, dict):
        return []
    issues: list[HealthIssue] = []
    if not tree_raw.get("schema"):
        issues.append(
            _issue(
                "warning",
                "freshness",
                "Skill tree schema is missing",
                "skill-tree.yaml has no schema field.",
                "Set schema to one of schemas/*.yaml.",
            )
        )
    nodes = tree_raw.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        issues.append(
            _issue(
                "warning",
                "freshness",
                "Skill tree has no nodes",
                "No node rows are configured in skill-tree.yaml.",
                "Add relevant schema node ids to start tracking progress.",
            )
        )
    return issues


def analyze_profile_health(name: str) -> HealthReport:
    """Analyze one profile without writing any files."""
    pdir = profile_dir(name)
    issues: list[HealthIssue] = []
    validate_issues, validate_blocks = _validate_issues(name)
    sync_issues, sync_blocks = _sync_issues(name)
    issues.extend(validate_issues)
    issues.extend(sync_issues)

    tree_raw = load_skill_tree_raw(pdir)
    issues.extend(_tree_shape_issues(tree_raw))
    issues.extend(_evidence_issues(pdir, tree_raw))
    issues.extend(_kanban_issues(name, pdir))

    return HealthReport(
        profile=name,
        issues=issues,
        can_publish_context=not (validate_blocks or sync_blocks),
    )


def format_health_text(report: HealthReport) -> str:
    """Format a health report for CLI output."""
    counts = report.summary_counts
    publish = (
        "yes" if report.can_publish_context else "no"
    )
    lines = [
        f"nblane health · {report.profile}",
        (
            "Summary: "
            f"errors={counts['error']}, "
            f"warnings={counts['warning']}, "
            f"info={counts['info']}"
        ),
        f"Can publish context: {publish}",
    ]
    if not report.issues:
        lines.append("No health issues found.")
        return "\n".join(lines)
    for issue in report.issues:
        lines.append("")
        lines.append(
            f"[{issue.severity.upper()}] "
            f"{issue.category}: {issue.title}"
        )
        if issue.detail:
            lines.append(f"  {issue.detail}")
        if issue.action:
            lines.append(f"  action: {issue.action}")
    return "\n".join(lines)
