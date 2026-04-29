"""Pure helpers for kanban board component events."""

from __future__ import annotations

from dataclasses import replace

from nblane.core.kanban_ai import KanbanSubtaskProposal
from nblane.core.models import KanbanSubtask, KanbanTask


def _clean_text(value: object) -> str:
    """Return a stripped string, tolerating ``None``."""
    return str(value or "").strip()


def split_kanban_details(value: object) -> list[str]:
    """Split a textarea/list value into non-empty kanban detail lines."""
    if isinstance(value, list):
        return [_clean_text(item) for item in value if _clean_text(item)]
    return [
        line.strip()
        for line in str(value or "").splitlines()
        if line.strip()
    ]


def _bool_from_payload(value: object) -> bool:
    """Coerce common JSON/form truthy values without treating 'false' as true."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().casefold() in {
            "1",
            "true",
            "yes",
            "y",
            "on",
            "checked",
            "done",
            "x",
        }
    if isinstance(value, (int, float)):
        return bool(value)
    return False


def apply_kanban_card_update(
    task: KanbanTask,
    card: dict,
) -> KanbanTask | None:
    """Return a task updated from a board card payload.

    ``None`` means the payload tried to blank a required title. Subtasks are
    replaced only when the payload supplies a list; an invalid non-list value
    is ignored so malformed events do not accidentally clear existing work.
    """
    changes: dict[str, object] = {}
    if "title" in card:
        title = _clean_text(card.get("title"))
        if not title:
            return None
        changes["title"] = title
    for field in ("context", "why", "blocked_by", "outcome", "tags"):
        if field in card:
            changes[field] = _clean_text(card.get(field))
    if "started_on" in card:
        changes["started_on"] = _clean_text(card.get("started_on")) or None
    if "completed_on" in card:
        changes["completed_on"] = (
            _clean_text(card.get("completed_on")) or None
        )
    if "notes" in card:
        changes["details"] = split_kanban_details(card.get("notes"))
    elif "details" in card:
        changes["details"] = split_kanban_details(card.get("details"))
    if "subtasks" in card and isinstance(card.get("subtasks"), list):
        next_subtasks: list[KanbanSubtask] = []
        for item in card["subtasks"]:
            if isinstance(item, dict):
                title = _clean_text(item.get("title"))
                done = _bool_from_payload(item.get("done"))
            else:
                title = _clean_text(item)
                done = False
            if title:
                next_subtasks.append(KanbanSubtask(title=title, done=done))
        changes["subtasks"] = next_subtasks
    return replace(task, **changes) if changes else task


def event_subtask_index(
    payload: dict,
    task: KanbanTask,
) -> int:
    """Return a subtask index from current or older frontend payloads."""
    try:
        subtask_index = int(payload.get("subtask_index", -1))
    except (TypeError, ValueError):
        subtask_index = -1
    if 0 <= subtask_index < len(task.subtasks):
        return subtask_index

    subtask_id = _clean_text(payload.get("subtask_id"))
    if subtask_id.startswith("subtask-"):
        try:
            subtask_index = int(subtask_id.removeprefix("subtask-"))
        except ValueError:
            subtask_index = -1
        if 0 <= subtask_index < len(task.subtasks):
            return subtask_index
    return -1


def alignment_context_from_payload(payload: dict) -> str:
    """Build confirmed task-understanding text from a board event payload."""
    alignment_mode = _clean_text(payload.get("alignment_mode")).casefold()
    alignment_kind = _clean_text(payload.get("alignment_kind")).casefold()
    custom = _clean_text(payload.get("custom_context"))
    granularity = _clean_text(payload.get("granularity"))

    if alignment_mode == "custom_only" or alignment_kind == "other":
        if not custom:
            return ""
        parts = []
        if granularity:
            parts.append(f"Granularity: {granularity}")
        if custom:
            parts.append(f"User clarification: {custom}")
        return "\n".join(parts).strip()

    parts: list[str] = []

    def add_alignment_block(alignment: object, index: int | None = None) -> None:
        if not isinstance(alignment, dict):
            return
        block: list[str] = []
        label = _clean_text(alignment.get("label"))
        goal = _clean_text(alignment.get("goal"))
        style = _clean_text(alignment.get("subtask_style"))
        assumptions = alignment.get("assumptions")
        if label:
            block.append(f"Label: {label}")
        if goal:
            block.append(f"Goal: {goal}")
        if isinstance(assumptions, list):
            clean_assumptions = [
                _clean_text(item)
                for item in assumptions
                if _clean_text(item)
            ]
        else:
            clean_assumptions = split_kanban_details(assumptions)
        if clean_assumptions:
            block.append("Assumptions: " + "; ".join(clean_assumptions))
        if style:
            block.append(f"Subtask style: {style}")
        if not block:
            return
        if index is None:
            parts.extend(block)
        else:
            parts.append(f"Selected understanding {index}:")
            parts.extend(block)

    selected = payload.get("selected_alignments")
    if isinstance(selected, list):
        for idx, alignment in enumerate(selected, start=1):
            add_alignment_block(alignment, idx)
    else:
        alignment = payload.get("alignment")
        add_alignment_block(alignment, None)

    has_understanding = bool(parts)
    if granularity:
        parts.append(f"Granularity: {granularity}")
    if custom:
        parts.append(f"User clarification: {custom}")
    if not has_understanding and not custom:
        return ""
    return "\n".join(parts).strip()


def subtask_proposals_from_payload(
    payload: dict,
    task_id: str,
) -> list[KanbanSubtaskProposal]:
    """Return selected edited AI drafts from current and legacy payloads."""
    raw_drafts = payload.get("drafts")
    if isinstance(raw_drafts, list):
        items = raw_drafts
    else:
        raw_titles = payload.get("titles")
        items = raw_titles if isinstance(raw_titles, list) else []

    proposals: list[KanbanSubtaskProposal] = []
    seen: set[str] = set()
    for item in items:
        selected = True
        artifact = ""
        verification = ""
        if isinstance(item, dict):
            if "selected" in item and not _bool_from_payload(item.get("selected")):
                continue
            title = _clean_text(item.get("title"))
            artifact = _clean_text(
                item.get("artifact")
                or item.get("deliverable")
                or item.get("output")
            )
            verification = _clean_text(
                item.get("verification")
                or item.get("verify")
                or item.get("evidence")
                or item.get("validation")
            )
        else:
            title = _clean_text(item)
        key = title.casefold()
        if not selected or not title or key in seen:
            continue
        seen.add(key)
        proposals.append(
            KanbanSubtaskProposal(
                title=title,
                task_id=task_id,
                artifact=artifact,
                verification=verification,
            )
        )
    return proposals


def discard_subtask_proposal_at(
    proposals_by_task: dict,
    task_id: str,
    index: int,
) -> bool:
    """Remove one session-only AI subtask draft by index."""
    task_key = _clean_text(task_id)
    proposals = proposals_by_task.get(task_key)
    if not isinstance(proposals, list) or not 0 <= index < len(proposals):
        return False
    proposals.pop(index)
    if proposals:
        proposals_by_task[task_key] = proposals
    else:
        proposals_by_task.pop(task_key, None)
    return True


def discard_task_ai_state(
    proposals_by_task: dict | None,
    alignments_by_task: dict | None,
    errors_by_task: dict | None,
    task_id: str,
    *,
    scope: str = "all",
) -> bool:
    """Clear session-only AI state for one task."""
    task_key = _clean_text(task_id)
    changed = False
    normalized_scope = _clean_text(scope).casefold() or "all"
    if normalized_scope in {"all", "drafts", "proposals"} and isinstance(
        proposals_by_task,
        dict,
    ):
        changed = proposals_by_task.pop(task_key, None) is not None or changed
    if normalized_scope in {"all", "alignments", "understanding"} and isinstance(
        alignments_by_task,
        dict,
    ):
        changed = alignments_by_task.pop(task_key, None) is not None or changed
    if normalized_scope in {"all", "errors"} and isinstance(errors_by_task, dict):
        changed = errors_by_task.pop(task_key, None) is not None or changed
    return changed
