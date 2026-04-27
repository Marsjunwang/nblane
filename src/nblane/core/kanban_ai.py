"""AI helpers for kanban task gap analysis and subtask drafting."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Iterable

from nblane.core import gap, llm
from nblane.core.jsonutil import extract_json_object
from nblane.core.models import GapResult, KanbanSubtask, KanbanTask


@dataclass(frozen=True)
class KanbanSubtaskProposal:
    """Draft subtask suggested by AI for a kanban task."""

    title: str
    reason: str = ""
    gap_node_id: str = ""
    task_id: str = ""


def _clean_text(value: object) -> str:
    """Return a stripped string, tolerating ``None``."""
    return str(value or "").strip()


def _iter_tasks(
    sections: dict[str, list[KanbanTask]],
) -> Iterable[tuple[str, int, KanbanTask]]:
    """Yield section, index, task for every task in a board."""
    for section, tasks in sections.items():
        for index, task in enumerate(tasks):
            yield section, index, task


def _find_task_by_id(
    sections: dict[str, list[KanbanTask]],
    task_id: str,
) -> tuple[str, int, KanbanTask] | None:
    """Find a kanban task by stable id."""
    wanted = _clean_text(task_id)
    if not wanted:
        return None
    for section, index, task in _iter_tasks(sections):
        if _clean_text(task.id) == wanted:
            return section, index, task
    return None


def _copy_sections(
    sections: dict[str, list[KanbanTask]],
) -> dict[str, list[KanbanTask]]:
    """Copy sections and task child lists without mutating callers."""
    out: dict[str, list[KanbanTask]] = {}
    for section, tasks in sections.items():
        out[section] = [
            replace(
                task,
                subtasks=[replace(subtask) for subtask in task.subtasks],
                details=list(task.details),
            )
            for task in tasks
        ]
    return out


def format_kanban_task_for_ai(task: KanbanTask) -> str:
    """Render a kanban task as compact context for gap analysis / LLM."""
    lines = [f"Title: {_clean_text(task.title)}"]
    if task.id:
        lines.append(f"Task id: {_clean_text(task.id)}")
    if task.context:
        lines.append(f"Context: {_clean_text(task.context)}")
    if task.why:
        lines.append(f"Why: {_clean_text(task.why)}")
    if task.outcome:
        lines.append(f"Outcome: {_clean_text(task.outcome)}")
    if task.blocked_by:
        lines.append(f"Blocked by: {_clean_text(task.blocked_by)}")
    if task.started_on:
        lines.append(f"Started on: {_clean_text(task.started_on)}")
    if task.completed_on:
        lines.append(f"Completed on: {_clean_text(task.completed_on)}")
    if task.crystallized:
        lines.append("Crystallized: true")
    if task.subtasks:
        lines.append("Subtasks:")
        for subtask in task.subtasks:
            mark = "x" if subtask.done else " "
            lines.append(f"- [{mark}] {_clean_text(subtask.title)}")
    if task.details:
        lines.append("Details:")
        for detail in task.details:
            lines.append(f"- {_clean_text(detail)}")
    return "\n".join(line for line in lines if line.strip())


def analyze_kanban_task_gap(
    profile_name: str,
    sections: dict[str, list[KanbanTask]],
    task_id: str,
    explicit_node: str | None = None,
    *,
    use_rule_match: bool = True,
    use_llm_router: bool = False,
    persist_router_keywords: bool = False,
) -> GapResult:
    """Run gap analysis for a kanban task found by stable task id."""
    found = _find_task_by_id(sections, task_id)
    if found is None:
        return GapResult(
            error=f"Kanban task not found: {task_id}",
            error_key="task_not_found",
        )
    _, _, task = found
    return gap.analyze(
        profile_name,
        format_kanban_task_for_ai(task),
        explicit_node,
        use_rule_match=use_rule_match,
        use_llm_router=use_llm_router,
        persist_router_keywords=persist_router_keywords,
    )


def _proposal_system_prompt() -> str:
    """System prompt for gap-aware kanban subtask drafting."""
    return (
        "You draft small, concrete kanban subtasks from a skill gap "
        "analysis. Reply with ONE JSON object only, no markdown. "
        'Schema: {"subtasks": [{"title": "...", "reason": "...", '
        '"gap_node_id": "..."}]}. '
        "Rules: titles must be actionable checkbox items, 3-8 words when "
        "possible, and should not repeat existing subtasks. Prefer steps "
        "that create evidence or unblock the listed skill gaps. Use only "
        "gap_node_id values present in the analysis; use an empty string "
        "when no single node applies. Return at most 5 subtasks."
    )


def _proposal_user_prompt(
    task: KanbanTask,
    analysis: GapResult,
) -> str:
    """Build the user prompt sent to the LLM."""
    existing = "\n".join(
        f"- {_clean_text(st.title)}" for st in task.subtasks
    )
    if not existing:
        existing = "- (none)"
    return (
        "Kanban task:\n"
        f"{format_kanban_task_for_ai(task)}\n\n"
        "Existing subtasks:\n"
        f"{existing}\n\n"
        "Gap analysis:\n"
        f"{gap.format_for_llm(analysis)}\n"
    )


def _proposal_from_dict(
    item: object,
    *,
    task_id: str,
    allowed_gap_ids: set[str],
) -> KanbanSubtaskProposal | None:
    """Validate one JSON proposal item."""
    if not isinstance(item, dict):
        return None
    title = _clean_text(item.get("title"))
    if not title:
        return None
    reason = _clean_text(item.get("reason"))
    gap_node_id = _clean_text(
        item.get("gap_node_id") or item.get("node_id")
    )
    if gap_node_id and gap_node_id not in allowed_gap_ids:
        gap_node_id = ""
    return KanbanSubtaskProposal(
        title=title,
        reason=reason,
        gap_node_id=gap_node_id,
        task_id=task_id,
    )


def _parse_proposals(
    reply: str,
    *,
    task_id: str,
    allowed_gap_ids: set[str],
) -> list[KanbanSubtaskProposal]:
    """Parse and validate subtask proposals from LLM JSON."""
    data = extract_json_object(reply)
    if data is None:
        return []
    raw_items = data.get("subtasks")
    if not isinstance(raw_items, list):
        raw_items = data.get("proposals")
    if not isinstance(raw_items, list):
        return []

    proposals: list[KanbanSubtaskProposal] = []
    seen: set[str] = set()
    for item in raw_items:
        proposal = _proposal_from_dict(
            item,
            task_id=task_id,
            allowed_gap_ids=allowed_gap_ids,
        )
        if proposal is None:
            continue
        key = proposal.title.casefold()
        if key in seen:
            continue
        seen.add(key)
        proposals.append(proposal)
        if len(proposals) >= 5:
            break
    return proposals


def generate_kanban_subtask_proposals(
    profile_name: str,
    sections: dict[str, list[KanbanTask]],
    task_id: str,
    explicit_node: str | None = None,
    *,
    use_rule_match: bool = True,
    use_llm_router: bool = False,
    persist_router_keywords: bool = False,
) -> list[KanbanSubtaskProposal]:
    """Generate draft subtasks for a kanban task without mutating board."""
    found = _find_task_by_id(sections, task_id)
    if found is None:
        return []
    _, _, task = found
    analysis = analyze_kanban_task_gap(
        profile_name,
        sections,
        task_id,
        explicit_node,
        use_rule_match=use_rule_match,
        use_llm_router=use_llm_router,
        persist_router_keywords=persist_router_keywords,
    )
    if analysis.error:
        return []
    reply = llm.chat(
        _proposal_system_prompt(),
        _proposal_user_prompt(task, analysis),
        temperature=0.2,
    )
    if reply.startswith("LLM error:") or reply.startswith(
        "AI features not configured"
    ):
        return []
    allowed_gap_ids = {
        _clean_text(node.get("id"))
        for node in analysis.closure
        if _clean_text(node.get("id"))
    }
    return _parse_proposals(
        reply,
        task_id=task_id,
        allowed_gap_ids=allowed_gap_ids,
    )


def apply_kanban_subtask_proposals(
    sections: dict[str, list[KanbanTask]],
    task_id: str,
    proposals: list[KanbanSubtaskProposal],
) -> dict[str, list[KanbanTask]]:
    """Return a board copy with proposal titles appended as new subtasks."""
    out = _copy_sections(sections)
    found = _find_task_by_id(out, task_id)
    if found is None:
        return out
    _, _, task = found
    existing = {
        _clean_text(subtask.title).casefold()
        for subtask in task.subtasks
        if _clean_text(subtask.title)
    }
    for proposal in proposals:
        if _clean_text(proposal.task_id) not in ("", task_id):
            continue
        title = _clean_text(proposal.title)
        key = title.casefold()
        if not title or key in existing:
            continue
        task.subtasks.append(KanbanSubtask(title=title, done=False))
        existing.add(key)
    return out
