"""Goal-to-skill alignment helpers.

Candidates are suggestions only. Callers must explicitly confirm them before
writing ``Goal.skill_links`` to ``goals.yaml``.
"""

from __future__ import annotations

from pathlib import Path

from nblane.core import learned_keywords as lk_store
from nblane.core.gap import score_nodes
from nblane.core.goals import Goal, GoalSkillLink
from nblane.core.io import (
    load_schema_raw,
    load_skill_tree_raw,
    schema_node_index,
)

ProfileRef = str | Path


def _schema_for_profile(
    profile: ProfileRef,
) -> tuple[str, dict, dict[str, dict]]:
    """Return schema name, schema raw data, and node index."""
    tree = load_skill_tree_raw(profile)
    if not isinstance(tree, dict):
        return "", {}, {}
    schema_name = str(tree.get("schema", "") or "").strip()
    if not schema_name:
        return "", {}, {}
    schema_raw = load_schema_raw(schema_name)
    if not isinstance(schema_raw, dict):
        return schema_name, {}, {}
    return schema_name, schema_raw, schema_node_index(schema_raw)


def _goal_text(goal: Goal | None, north_star_context: str = "") -> str:
    """Build the matching text from P0 goal fields."""
    if goal is None:
        return ""
    chunks: list[str] = [
        goal.title,
        goal.summary,
        goal.alignment,
        "\n".join(goal.focus),
        "\n".join(goal.success_criteria),
        "\n".join(goal.target_skills),
    ]
    if north_star_context.strip():
        chunks.append(f"North Star:\n{north_star_context.strip()}")
    return "\n\n".join(chunk.strip() for chunk in chunks if chunk.strip())


def _label(index: dict[str, dict], node_id: str) -> str:
    meta = index.get(node_id) or {}
    return str(meta.get("label") or node_id)


def rule_match_goal_to_skills(
    profile: ProfileRef,
    goal: Goal | None,
    north_star_context: str = "",
    *,
    limit: int = 5,
) -> list[GoalSkillLink]:
    """Return top rule-overlap goal-skill candidates."""
    schema_name, schema_raw, index = _schema_for_profile(profile)
    match_text = _goal_text(goal, north_star_context)
    if not schema_name or not schema_raw or not index or not match_text:
        return []

    learned = lk_store.load(schema_name)
    ranked = score_nodes(match_text, schema_raw, learned=learned)
    candidates: list[GoalSkillLink] = []
    seen: set[str] = set()
    for node_id, score in ranked:
        if node_id not in index or node_id in seen:
            continue
        seen.add(node_id)
        candidates.append(
            GoalSkillLink(
                node_id=node_id,
                label=_label(index, node_id),
                source="rule",
                score=max(0, int(score)),
                rationale=(
                    f"Rule keyword overlap matched this goal with score {score}."
                ),
            )
        )
        if len(candidates) >= limit:
            break
    return candidates


def ai_match_goal_to_skills(
    profile: ProfileRef,
    goal: Goal | None,
    north_star_context: str = "",
    *,
    backend: str = "llm",
    model: str = "",
    limit: int = 5,
) -> list[GoalSkillLink]:
    """Return AI-routed goal-skill candidates without persisting them."""
    schema_name, _schema_raw, index = _schema_for_profile(profile)
    match_text = _goal_text(goal, north_star_context)
    if not schema_name or not index or not match_text:
        return []

    from nblane.core.gap_llm_router import route_task_to_nodes, route_task_to_nodes_codex

    if backend == "codex":
        profile_name = profile.name if isinstance(profile, Path) else str(profile)
        outcome = route_task_to_nodes_codex(
            profile_name,
            match_text,
            schema_name,
            index,
            model=model or None,
        )
    else:
        outcome = route_task_to_nodes(
            match_text,
            schema_name,
            index,
            model=model or None,
        )
    if not outcome.ok:
        return []

    candidates: list[GoalSkillLink] = []
    seen: set[str] = set()
    for rank, node_id in enumerate(outcome.node_ids[:limit], start=1):
        if node_id not in index or node_id in seen:
            continue
        seen.add(node_id)
        keywords = [
            str(item).strip()
            for item in outcome.keywords.get(node_id, [])
            if str(item).strip()
        ]
        rationale = "AI routed this goal to the skill node."
        if keywords:
            rationale = "AI route keywords: " + ", ".join(keywords[:4])
        candidates.append(
            GoalSkillLink(
                node_id=node_id,
                label=_label(index, node_id),
                source="codex" if backend == "codex" else "ai",
                score=max(1, limit - rank + 1),
                rationale=rationale,
            )
        )
    return candidates


def merge_goal_skill_candidates(
    rule_candidates: list[GoalSkillLink],
    ai_candidates: list[GoalSkillLink],
    *,
    limit: int = 5,
) -> list[GoalSkillLink]:
    """Merge AI and rule candidates with AI ordering first."""
    rule_by_id = {candidate.node_id: candidate for candidate in rule_candidates}
    out: list[GoalSkillLink] = []
    seen: set[str] = set()

    for ai in ai_candidates:
        if ai.node_id in seen:
            continue
        rule = rule_by_id.get(ai.node_id)
        if rule is None:
            out.append(ai)
        else:
            rationale = ai.rationale or rule.rationale
            if ai.rationale and rule.rationale and ai.rationale != rule.rationale:
                rationale = f"{ai.rationale} {rule.rationale}"
            out.append(
                GoalSkillLink(
                    node_id=ai.node_id,
                    label=ai.label or rule.label,
                    source="rule+ai",
                    score=max(ai.score, rule.score),
                    rationale=rationale,
                )
            )
        seen.add(ai.node_id)
        if len(out) >= limit:
            return out

    for rule in rule_candidates:
        if rule.node_id in seen:
            continue
        out.append(rule)
        seen.add(rule.node_id)
        if len(out) >= limit:
            break
    return out


def skill_node_options(profile: ProfileRef) -> list[dict[str, str]]:
    """Return schema node choices for manual goal-skill links."""
    _schema_name, _schema_raw, index = _schema_for_profile(profile)
    return [
        {"id": node_id, "label": _label(index, node_id)}
        for node_id in sorted(index)
    ]


def manual_goal_skill_link(
    profile: ProfileRef,
    node_id: str,
) -> GoalSkillLink | None:
    """Build a manual link when the node exists in the profile schema."""
    clean_id = str(node_id or "").strip()
    if not clean_id:
        return None
    _schema_name, _schema_raw, index = _schema_for_profile(profile)
    if clean_id not in index:
        return None
    return GoalSkillLink(
        node_id=clean_id,
        label=_label(index, clean_id),
        source="manual",
        score=0,
        rationale="Manually linked by the user.",
    )
