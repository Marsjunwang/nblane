"""AI helpers for kanban task gap analysis and subtask drafting."""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Iterable

import yaml

from nblane.core import gap, llm
from nblane.core.jsonutil import extract_json_object
from nblane.core.models import GapResult, KanbanSubtask, KanbanTask
from nblane.core.paths import PROFILES_DIR


@dataclass(frozen=True)
class KanbanSubtaskProposal:
    """Draft subtask suggested by AI for a kanban task."""

    title: str
    reason: str = ""
    gap_node_id: str = ""
    task_id: str = ""
    artifact: str = ""
    verification: str = ""


@dataclass(frozen=True)
class KanbanTaskAlignment:
    """One candidate understanding of an underspecified kanban task."""

    label: str
    goal: str
    assumptions: tuple[str, ...] = ()
    subtask_style: str = ""
    task_id: str = ""


@dataclass(frozen=True)
class KanbanSubtaskGenerationResult:
    """Detailed outcome for AI subtask proposal generation."""

    proposals: list[KanbanSubtaskProposal] = field(default_factory=list)
    error_key: str = ""
    message: str = ""
    raw_count: int = 0
    accepted_count: int = 0
    filtered_count: int = 0


_VAGUE_SUBTASK_TERMS = {
    "learn",
    "learning",
    "research",
    "study",
    "improve",
    "understand",
    "explore",
    "investigate",
    "学习",
    "研究",
    "提升",
    "了解",
}

_DOMAIN_PRIOR_TERMS = {
    "vla",
    "vlm",
    "openvla",
    "openpi",
    "pi0",
    "pi05",
    "pi0.5",
    "piper",
    "vggt",
    "memory",
    "robot",
    "robotics",
    "pose",
    "6d",
    "benchmark",
    "鞋",
    "鞋子",
    "抓取",
    "摆放",
    "机器人",
    "具身",
    "机械臂",
}


def _clean_text(value: object) -> str:
    """Return a stripped string, tolerating ``None``."""
    return str(value or "").strip()


def _proposal_title_key(value: object) -> str:
    """Normalize a subtask title enough to catch checkbox/spacing repeats."""
    text = _clean_text(value).casefold()
    for prefix in ("- [ ] ", "- [x] ", "[ ] ", "[x] "):
        if text.startswith(prefix):
            text = text[len(prefix) :]
            break
    return " ".join(text.split())


def _is_vague_subtask_title(title: str) -> bool:
    """Reject generic learning/research items that are not checklist work."""
    lowered = title.casefold()
    words = {
        word.strip(".,:;!?()[]{}")
        for word in lowered.replace("/", " ").split()
    }
    return any(
        term in lowered if any(ord(ch) > 127 for ch in term) else term in words
        for term in _VAGUE_SUBTASK_TERMS
    )


def _read_text(path: Path) -> str:
    """Read a profile text file if it exists."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _load_yaml(path: Path) -> object:
    """Load a YAML file defensively for prompt context."""
    raw = _read_text(path)
    if not raw:
        return None
    try:
        return yaml.safe_load(raw)
    except yaml.YAMLError:
        return None


def _context_tokens(text: str) -> set[str]:
    """Extract lightweight relevance tokens for grounding context."""
    lower = text.casefold()
    tokens = set(re.findall(r"[a-z0-9]+(?:\.[a-z0-9]+)?", lower))
    for run in re.findall(r"[\u4e00-\u9fff]+", text):
        tokens.add(run)
    if "vla" in tokens or "memory" in tokens or "模块" in text:
        tokens.update(
            {
                "vla",
                "openpi",
                "openvla",
                "pi0",
                "pi05",
                "pi0.5",
                "piper",
                "vggt",
                "memory",
                "vlm",
                "robot",
                "机器人",
                "具身",
            }
        )
    if "鞋" in text or "shoe" in lower:
        tokens.update(
            {
                "shoe",
                "shoes",
                "鞋",
                "鞋子",
                "home",
                "robot",
                "piper",
                "pose",
                "6d",
                "benchmark",
                "抓取",
                "摆放",
                "机器人",
                "机械臂",
            }
        )
    tokens.update(_DOMAIN_PRIOR_TERMS & tokens)
    return {token for token in tokens if len(token) > 1 or ord(token[0]) > 127}


def _score_context_text(text: str, tokens: set[str]) -> int:
    """Return a tiny deterministic relevance score for a context line."""
    if not tokens:
        return 0
    lower = text.casefold()
    return sum(1 for token in tokens if token and token.casefold() in lower)


def _shorten(value: object, limit: int = 220) -> str:
    """Collapse and truncate context text for prompts."""
    text = " ".join(_clean_text(value).split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def _format_task_one_line(section: str, task: KanbanTask) -> str:
    """Render a task as one compact prior line."""
    bits = [f"{section}: {task.title}"]
    if task.context:
        bits.append(f"context={task.context}")
    if task.outcome:
        bits.append(f"outcome={task.outcome}")
    if task.blocked_by:
        bits.append(f"blocked_by={task.blocked_by}")
    if task.subtasks:
        bits.append(
            "subtasks="
            + "; ".join(
                _clean_text(subtask.title)
                for subtask in task.subtasks[:4]
                if _clean_text(subtask.title)
            )
        )
    if task.crystallized:
        bits.append("crystallized=true")
    return _shorten(" | ".join(bit for bit in bits if bit), 260)


def _extract_archive_tasks(profile_name: str) -> list[str]:
    """Extract compact task blocks from kanban-archive.md."""
    path = PROFILES_DIR / profile_name / "kanban-archive.md"
    text = _read_text(path)
    if not text:
        return []
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in text.splitlines():
        if re.match(r"^- \[(?:x|X| )\]\s+", line) or re.match(
            r"^- (?!\()", line
        ):
            if current:
                blocks.append(current)
            title = re.sub(r"^- \[(?:x|X| )\]\s*", "- ", line).strip()
            current = [title]
            continue
        if current and line.startswith("  - "):
            clean = line.strip()
            if any(
                key in clean
                for key in (
                    "context:",
                    "outcome:",
                    "crystallized:",
                    "baseline",
                    "OpenPI",
                    "openpi",
                    "VGGT",
                    "vggt",
                    "Piper",
                    "piper",
                    "鞋",
                    "VLA",
                    "vla",
                    "PI0",
                    "pi0",
                )
            ):
                current.append(clean)
    if current:
        blocks.append(current)
    return [_shorten(" | ".join(block), 320) for block in blocks]


def _extract_profile_prior(profile_name: str) -> list[str]:
    """Extract a few stable profile priors from SKILL.md."""
    text = _read_text(PROFILES_DIR / profile_name / "SKILL.md")
    if not text:
        return []
    out: list[str] = []
    in_taste = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("## "):
            in_taste = line == "## Research Fingerprint"
            continue
        if (
            line.startswith("- **Domain**")
            or line.startswith("- **Current Role**")
            or line.startswith("- **North Star**")
            or "VLA" in line
            or "机器人" in line
            or "具身" in line
        ):
            out.append(_shorten(line, 180))
        elif in_taste and line.startswith("- "):
            out.append(_shorten(line, 180))
        if len(out) >= 8:
            break
    return out


def _extract_evidence_prior(
    profile_name: str,
    tokens: set[str],
    *,
    max_items: int,
) -> list[str]:
    """Return relevant evidence lines for the current task."""
    data = _load_yaml(PROFILES_DIR / profile_name / "evidence-pool.yaml")
    if not isinstance(data, dict):
        return []
    entries = data.get("evidence_entries")
    if not isinstance(entries, list):
        return []
    scored: list[tuple[int, int, str]] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        title = _clean_text(entry.get("title"))
        summary = _clean_text(entry.get("summary"))
        eid = _clean_text(entry.get("id"))
        text = " ".join([eid, title, summary])
        score = _score_context_text(text, tokens)
        if score <= 0:
            continue
        line = _shorten(f"{eid}: {title} — {summary}", 300)
        scored.append((score, -index, line))
    scored.sort(reverse=True)
    return [line for _score, _index, line in scored[:max_items]]


def _extract_skill_prior(
    profile_name: str,
    tokens: set[str],
    *,
    max_items: int,
) -> list[str]:
    """Return relevant skill status lines."""
    data = _load_yaml(PROFILES_DIR / profile_name / "skill-tree.yaml")
    if not isinstance(data, dict):
        return []
    nodes = data.get("nodes")
    if not isinstance(nodes, list):
        return []
    scored: list[tuple[int, int, str]] = []
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            continue
        nid = _clean_text(node.get("id"))
        status = _clean_text(node.get("status"))
        evidence_refs = node.get("evidence_refs") or []
        text = " ".join([nid, status, " ".join(map(str, evidence_refs))])
        score = _score_context_text(text, tokens)
        if score <= 0:
            continue
        suffix = ""
        if isinstance(evidence_refs, list) and evidence_refs:
            suffix = " evidence=" + ", ".join(map(str, evidence_refs[:4]))
        scored.append((score, -index, f"{nid}: {status or 'unknown'}{suffix}"))
    scored.sort(reverse=True)
    return [line for _score, _index, line in scored[:max_items]]


def build_kanban_ai_context(
    profile_name: str,
    sections: dict[str, list[KanbanTask]],
    task_id: str,
    *,
    max_items: int = 8,
) -> str:
    """Build a compact grounding prior for kanban AI prompts."""
    found = _find_task_by_id(sections, task_id)
    if found is None:
        return ""
    section_name, _index, task = found
    task_text = format_kanban_task_for_ai(task)
    tokens = _context_tokens(task_text)
    profile = _clean_text(profile_name)
    if not profile:
        return ""

    lines: list[str] = ["Profile/recent work prior for grounding:"]
    lower_task = task_text.casefold()
    if "鞋" in task_text or "shoe" in lower_task:
        lines.append(
            "- Domain guard: interpret shoes as home-robot shoe placement, "
            "manipulation benchmark, Piper demo, 6D pose, or VLA scene; "
            "not as online retail/catalog testing unless the user says so."
        )
    if (
        "vla" in lower_task
        or "memory" in lower_task
        or "模块" in task_text
    ):
        lines.append(
            "- Domain guard: interpret VLA memory as robotics "
            "Vision-Language-Action work tied to OpenPI/PI0.5, VGGT, "
            "Piper, data construction, training, and evaluation loops."
        )

    lines.append("- Current task: " + _format_task_one_line(section_name, task))

    active: list[str] = []
    for sec, _idx, item in _iter_tasks(sections):
        if item.id == task.id:
            continue
        if sec == "Doing" or sec == section_name:
            active.append("- " + _format_task_one_line(sec, item))
    if active:
        lines.append("Nearby active work:")
        lines.extend(active[:max_items])

    done_lines = [
        "- " + _format_task_one_line("Done", item)
        for item in sections.get("Done", [])[: max(1, max_items // 2)]
    ]
    if done_lines:
        lines.append("Current Done work:")
        lines.extend(done_lines)

    archive = _extract_archive_tasks(profile)
    scored_archive = [
        (_score_context_text(item, tokens), -idx, item)
        for idx, item in enumerate(archive)
    ]
    scored_archive = [item for item in scored_archive if item[0] > 0]
    scored_archive.sort(reverse=True)
    if scored_archive:
        lines.append("Recent archived/crystallized work:")
        lines.extend(
            f"- {line}"
            for _score, _idx, line in scored_archive[: max_items]
        )

    evidence = _extract_evidence_prior(
        profile,
        tokens,
        max_items=max(3, max_items // 2),
    )
    if evidence:
        lines.append("Relevant evidence:")
        lines.extend(f"- {line}" for line in evidence)

    skills = _extract_skill_prior(
        profile,
        tokens,
        max_items=max(3, max_items // 2),
    )
    if skills:
        lines.append("Relevant skill status:")
        lines.extend(f"- {line}" for line in skills)

    profile_prior = _extract_profile_prior(profile)
    if profile_prior:
        lines.append("Profile prior:")
        lines.extend(f"- {line}" for line in profile_prior[:max_items])

    lines.append(
        "Use this prior to disambiguate the task and avoid unrelated domains."
    )
    return "\n".join(lines)


def kanban_task_needs_alignment(task: KanbanTask) -> bool:
    """Return True when a task is too thin to safely auto-draft subtasks."""
    if not _clean_text(task.title):
        return True
    context_bits = [
        task.context,
        task.why,
        task.blocked_by,
        task.outcome,
        "\n".join(task.details),
        "\n".join(subtask.title for subtask in task.subtasks),
    ]
    return not any(_clean_text(bit) for bit in context_bits)


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


def _proposal_system_prompt(granularity: str = "milestone") -> str:
    """System prompt for gap-aware kanban subtask drafting."""
    granularity = (_clean_text(granularity) or "milestone").casefold()
    if granularity not in {"milestone", "checklist", "implementation"}:
        granularity = "milestone"
    detail_policy = {
        "milestone": (
            "Default granularity is milestone-level: each title should be a "
            "meaningful phase, outcome, checkpoint, or reviewable work slice. "
            "Do not decompose into tiny implementation files, helper scripts, "
            "environment checks, shell commands, directories, CSVs, or code "
            "artifacts unless the human explicitly requested implementation "
            "details. For reproduction, training, and evaluation tasks, prefer "
            "milestones such as complete one full training/evaluation run, "
            "align the evaluation protocol, compare baseline metrics and "
            "training time, record deltas, and decide follow-up fixes. For "
            "iup-pose reproduction, use the user's existing abstraction level "
            "as the guide: full training/evaluation and baseline effect/time "
            "alignment, not env_check.py, data_prep_4090.py, dataset_cache/, "
            "train_4090.sh, or hyperparam_mapping.csv."
        ),
        "checklist": (
            "Granularity is checklist-level: titles may be more concrete than "
            "milestones, but should still avoid invented filenames, scripts, "
            "directories, or one-off commands unless the task context already "
            "names them."
        ),
        "implementation": (
            "Granularity is implementation-level: detailed execution steps are "
            "allowed when useful, but do not invent irrelevant technology or "
            "unrelated domain framing."
        ),
    }[granularity]
    return (
        "You draft kanban subtask drafts from the "
        "current task context and skill gap analysis. Reply with ONE JSON "
        "object only, no markdown. "
        'Schema: {"subtasks": [{"title": "...", "reason": "...", '
        '"gap_node_id": "...", "artifact": "...", '
        '"verification": "..."}]}. '
        "Return 3 to 5 subtasks. Do not replace, summarize, or repeat any "
        "existing subtask. Existing subtasks are evidence of the user's "
        "preferred abstraction level; use them as a granularity reference "
        "while still avoiding duplicates. "
        f"{detail_policy} "
        "Each item must be verifiable: put the expected evidence, review, "
        "metric, artifact, or observable result in verification. Artifact "
        "and verification are review metadata; do not force the title to be "
        "a file, command, or script. Keep each item tightly tied to the "
        "current task, outcome, blockers, details, and the listed gap. "
        "Do not output vague learning goals or generic items such as learn, "
        "study, research, improve, understand, explore, investigate, 学习, "
        "研究, 提升, or 了解. Prefer work slices that create evidence or unblock "
        "a specific gap. Use only gap_node_id values present in the "
        "analysis; use an empty string when no single node applies."
    )


def _proposal_user_prompt(
    task: KanbanTask,
    analysis: GapResult,
    alignment_context: str = "",
    ai_context: str = "",
    granularity: str = "milestone",
) -> str:
    """Build the user prompt sent to the LLM."""
    existing = "\n".join(
        f"- {_clean_text(st.title)}" for st in task.subtasks
    )
    if not existing:
        existing = "- (none)"
    alignment_block = ""
    if _clean_text(alignment_context):
        alignment_block = (
            "Confirmed task understanding:\n"
            f"{_clean_text(alignment_context)}\n\n"
        )
    prior_block = ""
    if _clean_text(ai_context):
        prior_block = (
            "Grounding prior from this profile and recent work:\n"
            f"{_clean_text(ai_context)}\n\n"
        )
    return (
        "Kanban task:\n"
        f"{format_kanban_task_for_ai(task)}\n\n"
        f"{prior_block}"
        f"{alignment_block}"
        "Existing subtasks:\n"
        f"{existing}\n\n"
        "Gap analysis:\n"
        f"{gap.format_for_llm(analysis)}\n\n"
        "Drafting requirements:\n"
        f"- Output 3-5 new subtasks only at {(_clean_text(granularity) or 'milestone')} granularity.\n"
        "- Do not duplicate or overwrite the existing subtasks above.\n"
        "- Default to outcome-level milestones unless the confirmed "
        "understanding explicitly asks for implementation details.\n"
        "- Do not invent file names, scripts, directories, CSVs, or commands "
        "when the task did not name them.\n"
        "- For reproduction/training/evaluation work, prefer full run, "
        "evaluation protocol alignment, baseline metric/time comparison, "
        "delta recording, and follow-up decision milestones.\n"
        "- Fill artifact and verification so a human can check completion.\n"
        "- Avoid generic learning/research/improvement wording.\n"
    )


def _alignment_system_prompt() -> str:
    """System prompt for task-understanding alignment candidates."""
    return (
        "You help a human confirm the intended scope and granularity of a "
        "kanban task before drafting subtasks. Reply with ONE JSON object "
        "only, no markdown. "
        'Schema: {"alignments": [{"label": "...", "goal": "...", '
        '"assumptions": ["..."], "subtask_style": "..."}]}. '
        "Return 2 or 3 distinct, plausible task understandings. The first "
        "option should be a high-level milestone understanding unless the "
        "task clearly asks for implementation details. Keep them concise and "
        "grounded in the task fields, existing subtasks, and recent-work "
        "prior. Do not invent dates, links, metrics, employers, or private "
        "facts."
    )


def _alignment_user_prompt(task: KanbanTask) -> str:
    """Build the user prompt for alignment candidates."""
    return _alignment_user_prompt_with_context(task)


def _alignment_user_prompt_with_context(
    task: KanbanTask,
    ai_context: str = "",
) -> str:
    """Build the user prompt for alignment candidates."""
    prior_block = ""
    if _clean_text(ai_context):
        prior_block = (
            "Grounding prior from this profile and recent work:\n"
            f"{_clean_text(ai_context)}\n\n"
        )
    return (
        "Before drafting subtasks for the kanban task below, offer candidate "
        "understandings that the user can edit, combine, or replace with a "
        "personal clarification. Keep each candidate grounded in the task, "
        "existing subtasks, and prior; do not drift into unrelated domains. "
        "Prefer milestone-level decomposition by default.\n\n"
        f"{prior_block}"
        f"{format_kanban_task_for_ai(task)}\n"
    )


def _parse_assumptions(value: object) -> tuple[str, ...]:
    """Normalize an assumptions field from JSON."""
    if isinstance(value, list):
        return tuple(_clean_text(item) for item in value if _clean_text(item))
    text = _clean_text(value)
    return (text,) if text else ()


def _parse_alignments(
    reply: str,
    *,
    task_id: str,
) -> list[KanbanTaskAlignment]:
    """Parse task-understanding options from LLM JSON."""
    data = extract_json_object(reply)
    if data is None:
        return []
    raw_items = data.get("alignments")
    if not isinstance(raw_items, list):
        raw_items = data.get("options")
    if not isinstance(raw_items, list):
        return []

    out: list[KanbanTaskAlignment] = []
    seen: set[str] = set()
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        label = _clean_text(item.get("label") or item.get("title"))
        goal = _clean_text(item.get("goal") or item.get("understanding"))
        if not label or not goal:
            continue
        key = f"{label.casefold()} {goal.casefold()}"
        if key in seen:
            continue
        seen.add(key)
        out.append(
            KanbanTaskAlignment(
                label=label,
                goal=goal,
                assumptions=_parse_assumptions(item.get("assumptions")),
                subtask_style=_clean_text(
                    item.get("subtask_style") or item.get("style")
                ),
                task_id=task_id,
            )
        )
        if len(out) >= 3:
            break
    return out


def _fallback_alignments(task: KanbanTask) -> list[KanbanTaskAlignment]:
    """Return deterministic alignment options when the model is unavailable."""
    title = _clean_text(task.title) or "this task"
    return [
        KanbanTaskAlignment(
            label="Milestone pass",
            goal=f"Turn {title} into a few high-level, reviewable milestones.",
            assumptions=("The task should stay above implementation-file detail.",),
            subtask_style="milestone-level subtasks with evidence or validation",
            task_id=task.id,
        ),
        KanbanTaskAlignment(
            label="Execution checklist",
            goal=f"Break {title} into concrete but still non-microscopic steps.",
            assumptions=("The user wants a trackable checklist without invented files.",),
            subtask_style="medium-grain checklist with artifacts",
            task_id=task.id,
        ),
        KanbanTaskAlignment(
            label="Implementation detail",
            goal=f"Draft lower-level execution steps for {title}.",
            assumptions=("Only use file or script-level detail if the user confirms it.",),
            subtask_style="implementation-oriented steps",
            task_id=task.id,
        ),
    ]


def generate_kanban_task_alignment_options(
    sections: dict[str, list[KanbanTask]],
    task_id: str,
    *,
    profile_name: str = "",
) -> list[KanbanTaskAlignment]:
    """Generate candidate task understandings without mutating the board."""
    found = _find_task_by_id(sections, task_id)
    if found is None:
        return []
    _, _, task = found
    ai_context = build_kanban_ai_context(
        profile_name,
        sections,
        task_id,
    )
    reply = llm.chat(
        _alignment_system_prompt(),
        _alignment_user_prompt_with_context(task, ai_context),
        temperature=0.2,
    )
    if reply.startswith("LLM error:") or reply.startswith(
        "AI features not configured"
    ):
        return _fallback_alignments(task)
    parsed = _parse_alignments(reply, task_id=task_id)
    return parsed or _fallback_alignments(task)


def _proposal_from_dict(
    item: object,
    *,
    task_id: str,
    allowed_gap_ids: set[str],
    existing_titles: set[str],
) -> KanbanSubtaskProposal | None:
    """Validate one JSON proposal item."""
    if not isinstance(item, dict):
        return None
    title = _clean_text(item.get("title"))
    if not title:
        return None
    if _proposal_title_key(title) in existing_titles:
        return None
    if _is_vague_subtask_title(title):
        return None
    reason = _clean_text(item.get("reason"))
    gap_node_id = _clean_text(
        item.get("gap_node_id") or item.get("node_id")
    )
    if gap_node_id and gap_node_id not in allowed_gap_ids:
        gap_node_id = ""
    artifact = _clean_text(
        item.get("artifact") or item.get("deliverable") or item.get("output")
    )
    verification = _clean_text(
        item.get("verification")
        or item.get("verify")
        or item.get("evidence")
        or item.get("validation")
    )
    return KanbanSubtaskProposal(
        title=title,
        reason=reason,
        gap_node_id=gap_node_id,
        task_id=task_id,
        artifact=artifact,
        verification=verification,
    )


def _proposal_from_dict_with_reason(
    item: object,
    *,
    task_id: str,
    allowed_gap_ids: set[str],
    existing_titles: set[str],
) -> tuple[KanbanSubtaskProposal | None, str]:
    """Validate one JSON proposal item and explain rejection."""
    if not isinstance(item, dict):
        return None, "invalid"
    title = _clean_text(item.get("title"))
    if not title:
        return None, "invalid"
    if _proposal_title_key(title) in existing_titles:
        return None, "duplicate"
    if _is_vague_subtask_title(title):
        return None, "vague"
    proposal = _proposal_from_dict(
        item,
        task_id=task_id,
        allowed_gap_ids=allowed_gap_ids,
        existing_titles=existing_titles,
    )
    if proposal is None:
        return None, "invalid"
    return proposal, ""


def _generation_message(error_key: str) -> str:
    """Return a display-safe default diagnostic message."""
    messages = {
        "task_not_found": "Kanban task was not found.",
        "gap_error": "Gap analysis could not run for this task.",
        "llm_error": "The model call failed or AI is not configured.",
        "parse_empty": "The model did not return valid JSON subtasks.",
        "empty_json": "The model returned no subtask items.",
        "invalid_schema": "The model returned subtask items without usable titles.",
        "filtered_vague": (
            "The model returned drafts, but every title was too vague. "
            "Add a concrete artifact or verification detail and retry."
        ),
        "filtered_duplicate": (
            "The model only returned subtasks that already exist."
        ),
        "filtered_empty": "The model returned drafts, but none passed validation.",
    }
    return messages.get(error_key, "No usable subtask draft was generated.")


def _parse_proposals_detailed(
    reply: str,
    *,
    task_id: str,
    allowed_gap_ids: set[str],
    existing_titles: Iterable[str] = (),
) -> KanbanSubtaskGenerationResult:
    """Parse subtask proposals and keep rejection diagnostics."""
    data = extract_json_object(reply)
    if data is None:
        return KanbanSubtaskGenerationResult(
            error_key="parse_empty",
            message=_generation_message("parse_empty"),
        )
    raw_items = data.get("subtasks")
    if not isinstance(raw_items, list):
        raw_items = data.get("proposals")
    if not isinstance(raw_items, list):
        return KanbanSubtaskGenerationResult(
            error_key="parse_empty",
            message=_generation_message("parse_empty"),
        )
    raw_count = len(raw_items)
    if raw_count == 0:
        return KanbanSubtaskGenerationResult(
            error_key="empty_json",
            message=_generation_message("empty_json"),
            raw_count=0,
        )

    proposals: list[KanbanSubtaskProposal] = []
    seen: set[str] = {_proposal_title_key(title) for title in existing_titles}
    rejected = {"invalid": 0, "duplicate": 0, "vague": 0}
    for item in raw_items:
        proposal, reason = _proposal_from_dict_with_reason(
            item,
            task_id=task_id,
            allowed_gap_ids=allowed_gap_ids,
            existing_titles=seen,
        )
        if proposal is None:
            rejected[reason or "invalid"] = rejected.get(reason, 0) + 1
            continue
        key = _proposal_title_key(proposal.title)
        if key in seen:
            rejected["duplicate"] += 1
            continue
        seen.add(key)
        proposals.append(proposal)
        if len(proposals) >= 5:
            break

    filtered_count = raw_count - len(proposals)
    if proposals:
        return KanbanSubtaskGenerationResult(
            proposals=proposals,
            raw_count=raw_count,
            accepted_count=len(proposals),
            filtered_count=filtered_count,
        )

    if rejected["vague"] == raw_count:
        error_key = "filtered_vague"
    elif rejected["duplicate"] == raw_count:
        error_key = "filtered_duplicate"
    elif rejected["invalid"] == raw_count:
        error_key = "invalid_schema"
    else:
        error_key = "filtered_empty"
    return KanbanSubtaskGenerationResult(
        error_key=error_key,
        message=_generation_message(error_key),
        raw_count=raw_count,
        accepted_count=0,
        filtered_count=filtered_count,
    )


def _parse_proposals(
    reply: str,
    *,
    task_id: str,
    allowed_gap_ids: set[str],
    existing_titles: Iterable[str] = (),
) -> list[KanbanSubtaskProposal]:
    """Parse and validate subtask proposals from LLM JSON."""
    return _parse_proposals_detailed(
        reply,
        task_id=task_id,
        allowed_gap_ids=allowed_gap_ids,
        existing_titles=existing_titles,
    ).proposals


def generate_kanban_subtask_proposals(
    profile_name: str,
    sections: dict[str, list[KanbanTask]],
    task_id: str,
    explicit_node: str | None = None,
    *,
    use_rule_match: bool = True,
    use_llm_router: bool = False,
    persist_router_keywords: bool = False,
    alignment_context: str = "",
    granularity: str = "milestone",
) -> list[KanbanSubtaskProposal]:
    """Generate draft subtasks for a kanban task without mutating board."""
    return generate_kanban_subtask_proposals_detailed(
        profile_name,
        sections,
        task_id,
        explicit_node,
        use_rule_match=use_rule_match,
        use_llm_router=use_llm_router,
        persist_router_keywords=persist_router_keywords,
        alignment_context=alignment_context,
        granularity=granularity,
    ).proposals


def generate_kanban_subtask_proposals_detailed(
    profile_name: str,
    sections: dict[str, list[KanbanTask]],
    task_id: str,
    explicit_node: str | None = None,
    *,
    use_rule_match: bool = True,
    use_llm_router: bool = False,
    persist_router_keywords: bool = False,
    alignment_context: str = "",
    granularity: str = "milestone",
) -> KanbanSubtaskGenerationResult:
    """Generate draft subtasks with diagnostic detail."""
    found = _find_task_by_id(sections, task_id)
    if found is None:
        return KanbanSubtaskGenerationResult(
            error_key="task_not_found",
            message=_generation_message("task_not_found"),
        )
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
        return KanbanSubtaskGenerationResult(
            error_key="gap_error",
            message=analysis.error or _generation_message("gap_error"),
        )
    ai_context = build_kanban_ai_context(
        profile_name,
        sections,
        task_id,
    )
    reply = llm.chat(
        _proposal_system_prompt(granularity),
        _proposal_user_prompt(
            task,
            analysis,
            alignment_context=alignment_context,
            ai_context=ai_context,
            granularity=granularity,
        ),
        temperature=0.2,
    )
    if reply.startswith("LLM error:") or reply.startswith(
        "AI features not configured"
    ):
        return KanbanSubtaskGenerationResult(
            error_key="llm_error",
            message=_generation_message("llm_error"),
        )
    allowed_gap_ids = {
        _clean_text(node.get("id"))
        for node in analysis.closure
        if _clean_text(node.get("id"))
    }
    return _parse_proposals_detailed(
        reply,
        task_id=task_id,
        allowed_gap_ids=allowed_gap_ids,
        existing_titles=[subtask.title for subtask in task.subtasks],
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
