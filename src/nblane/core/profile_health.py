"""Deterministic profile health checks for growth review."""

from __future__ import annotations

from dataclasses import dataclass, field

from nblane.core import io as io_facade
from nblane.core.evidence_review import evidence_status_risks
from nblane.core.experience import load_experience_book
from nblane.core.io import (
    KANBAN_DONE,
    load_evidence_pool_raw,
    load_goal_book,
    load_skill_tree_raw,
    parse_kanban,
    profile_dir,
)
from nblane.core.project_board import load_project_board
from nblane.core.research_sources import load_research_sources
from nblane.core.sync import get_drifted_blocks
from nblane.core.validate import validate_one

HEALTH_SEVERITIES = ("error", "warning", "info")
HEALTH_CATEGORIES = (
    "validate",
    "sync",
    "evidence",
    "kanban",
    "refs",
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


def _evidence_issues(profile_path, tree_raw: dict | None) -> list[HealthIssue]:
    """Warn when solid/expert nodes lack evidence or enough strength."""
    if not isinstance(tree_raw, dict):
        return []
    issues: list[HealthIssue] = []
    for risk in evidence_status_risks(profile_path):
        nid = str(risk.get("id", "") or "").strip()
        label = str(risk.get("label", "") or nid)
        status = str(risk.get("status", "") or "")
        risk_level = str(risk.get("risk_level", "") or "")
        required = str(risk.get("required_strength", "") or "")
        highest = str(risk.get("highest_strength", "") or "unrated")
        if risk_level == "missing_evidence":
            detail = f"{nid} ({label}) is {status} with no resolved evidence."
        else:
            detail = (
                f"{nid} ({label}) is {status}; highest evidence strength "
                f"is {highest}, expected {required}+."
            )
        issues.append(
            _issue(
                "warning",
                "evidence",
                "Skill status lacks sufficient evidence",
                detail,
                (
                    "Add/link stronger evidence in Evidence Review or "
                    "reconsider the skill status."
                ),
            )
        )
    issues.extend(_evidence_v2_issues(profile_path))
    return issues


def _evidence_v2_issues(profile_path) -> list[HealthIssue]:
    """v2 provenance warnings (never fatal): missing raw content / unassigned.

    Aggregated counts keep the health report readable rather than emitting one
    issue per row.
    """
    raw = load_evidence_pool_raw(profile_path) or {}
    rows = [
        r
        for r in (raw.get("evidence_entries") or [])
        if isinstance(r, dict) and not r.get("deprecated")
    ]
    if not rows:
        return []
    missing_raw = 0
    unassigned = 0
    for row in rows:
        origin = str(row.get("origin", "") or "")
        if not str(row.get("original_content", "") or "").strip():
            missing_raw += 1
        project_refs = [
            p for p in (row.get("project_refs") or []) if str(p).strip()
        ]
        if origin in ("resume_parse", "manual_daily") and not project_refs:
            unassigned += 1
    issues: list[HealthIssue] = []
    if missing_raw:
        issues.append(
            _issue(
                "warning",
                "evidence",
                "Evidence missing preserved original content",
                f"{missing_raw} evidence row(s) have no original_content.",
                "Run migration in Evidence Review to backfill source content.",
            )
        )
    if unassigned:
        issues.append(
            _issue(
                "warning",
                "evidence",
                "Resume/manual evidence without a project",
                f"{unassigned} resume/manual evidence row(s) have no project.",
                (
                    "Link an internal project (or create one from the "
                    "evidence) in Evidence Review."
                ),
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


def _as_string_list(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        text = str(item or "").strip()
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _dangling_ref_issue(owner: str, ref: str, target: str) -> HealthIssue:
    return _issue(
        "warning",
        "refs",
        "Dangling workspace reference",
        f"{owner} references missing {target}: {ref}",
        "Fix refs in Project Board, Kanban, Evidence Review, or Research Source Inbox.",
    )


def _ref_integrity_issues(profile_path) -> list[HealthIssue]:
    """Warn about dangling internal project/experience/research refs."""
    issues: list[HealthIssue] = []
    projects = load_project_board(profile_path).by_id()
    experiences = load_experience_book(profile_path).by_id()
    sources = load_research_sources(profile_path).by_id()
    goals = {goal.id for goal in load_goal_book(profile_path).goals if goal.id}
    kanban = parse_kanban(profile_path)
    task_ids = {
        task.id
        for tasks in kanban.values()
        for task in tasks
        if task.id
    }
    project_ids = set(projects)
    experience_ids = set(experiences)
    source_ids = set(sources)
    evidence_ids: set[str] = set()

    pool_raw = load_evidence_pool_raw(profile_path) or {}
    for row in pool_raw.get("evidence_entries") or []:
        if not isinstance(row, dict):
            continue
        eid = str(row.get("id", "") or "").strip() or "evidence row"
        if eid != "evidence row":
            evidence_ids.add(eid)
        owner = f"evidence {eid}"
        for ref in _as_string_list(row.get("project_refs")):
            if ref not in project_ids:
                issues.append(_dangling_ref_issue(owner, ref, "project case"))
        for ref in _as_string_list(row.get("experience_refs")):
            if ref not in experience_ids:
                issues.append(_dangling_ref_issue(owner, ref, "experience case"))
        for ref in _as_string_list(row.get("source_refs")):
            if ref.startswith("source:research:") and ref not in source_ids:
                issues.append(_dangling_ref_issue(owner, ref, "research source"))

    for source in sources.values():
        owner = f"source {source.id}"
        for ref in source.project_refs:
            if ref not in project_ids:
                issues.append(_dangling_ref_issue(owner, ref, "project case"))
        for ref in source.experience_refs:
            if ref not in experience_ids:
                issues.append(_dangling_ref_issue(owner, ref, "experience case"))

    for project in projects.values():
        owner = f"project {project.id}"
        for ref in project.goal_refs:
            if ref not in goals:
                issues.append(_dangling_ref_issue(owner, ref, "goal"))
        for ref in project.task_refs:
            if ref not in task_ids:
                issues.append(_dangling_ref_issue(owner, ref, "kanban task"))
        for ref in project.evidence_refs:
            if ref not in evidence_ids:
                issues.append(_dangling_ref_issue(owner, ref, "evidence row"))
        for ref in project.experience_refs:
            if ref not in experience_ids:
                issues.append(_dangling_ref_issue(owner, ref, "experience case"))
        for ref in project.source_refs:
            if ref.startswith("source:research:") and ref not in source_ids:
                issues.append(_dangling_ref_issue(owner, ref, "research source"))
        for milestone in project.milestones:
            milestone_owner = f"milestone {milestone.id or project.id}"
            for ref in milestone.task_refs:
                if ref not in task_ids:
                    issues.append(
                        _dangling_ref_issue(
                            milestone_owner,
                            ref,
                            "kanban task",
                        )
                    )
            for ref in milestone.evidence_refs:
                if ref not in evidence_ids:
                    issues.append(
                        _dangling_ref_issue(
                            milestone_owner,
                            ref,
                            "evidence row",
                        )
                    )
            for ref in milestone.source_refs:
                if ref.startswith("source:research:") and ref not in source_ids:
                    issues.append(
                        _dangling_ref_issue(
                            milestone_owner,
                            ref,
                            "research source",
                        )
                    )

    for tasks in kanban.values():
        for task in tasks:
            owner = f"task {task.id or task.title or 'kanban task'}"
            project_id = str(task.project_id or "").strip()
            milestone_id = str(task.milestone_id or "").strip()
            if project_id and project_id not in project_ids:
                issues.append(_dangling_ref_issue(owner, project_id, "project case"))
            if milestone_id:
                project = projects.get(project_id)
                valid_milestones = {
                    milestone.id
                    for milestone in (project.milestones if project else [])
                    if milestone.id
                }
                if milestone_id not in valid_milestones:
                    issues.append(
                        _dangling_ref_issue(
                            owner,
                            milestone_id,
                            "project milestone",
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
    issues.extend(_ref_integrity_issues(pdir))

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
