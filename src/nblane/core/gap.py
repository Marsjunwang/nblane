"""Gap analysis: task -> skill match, requires closure, gap detection.

Merges logic from tools/gap.py and app/utils/gap_bridge.py into
one module with structured return types.
"""

from __future__ import annotations

import heapq
import re

from nblane.core import learned_keywords as lk_store
from nblane.core.evidence_resolve import resolved_evidence_count
from nblane.core.io import (
    load_evidence_pool,
    load_schema_raw,
    load_skill_tree_raw,
    schema_node_index,
    status_by_node_id,
)
from nblane.core.models import GapResult
from nblane.core.paths import PROFILES_DIR


def _evidence_count_by_id(
    tree: dict | None,
    profile_name: str,
) -> dict[str, int]:
    """Map skill node id -> materialized evidence count (refs + inline)."""
    if tree is None:
        return {}
    pool = load_evidence_pool(profile_name)
    out: dict[str, int] = {}
    for node in tree.get("nodes") or []:
        nid = node.get("id")
        if not nid:
            continue
        out[nid] = resolved_evidence_count(node, pool)
    return out


def _merge_root_ids(
    llm_ids: list[str],
    rule_ids: list[str],
) -> list[str]:
    """Dedupe while preserving LLM order first, then rule-only ids."""
    seen: set[str] = set()
    order: list[str] = []
    for nid in llm_ids:
        if nid not in seen:
            seen.add(nid)
            order.append(nid)
    for nid in rule_ids:
        if nid not in seen:
            seen.add(nid)
            order.append(nid)
    return order


def _build_top_matches(
    ranked: list[tuple[str, int]],
    roots_llm: list[str],
    index: dict[str, dict],
) -> list[dict]:
    """Merge ranked rule scores with LLM-only root ids."""
    llm_set = set(roots_llm)
    out: list[dict] = []
    seen: set[str] = set()
    for nid, sc in ranked[:8]:
        if nid not in index:
            continue
        src = "rule+llm" if nid in llm_set else "rule"
        out.append(
            {
                "id": nid,
                "label": index[nid].get("label", nid),
                "score": sc,
                "source": src,
            }
        )
        seen.add(nid)
    for nid in roots_llm:
        if nid in seen or nid not in index:
            continue
        out.append(
            {
                "id": nid,
                "label": index[nid].get("label", nid),
                "score": 0,
                "source": "llm",
            }
        )
        seen.add(nid)
    return out


_SYNONYMS: dict[str, tuple[str, ...]] = {
    "vla": (
        "openvla", "vlm", "vlm_robot", "imitation",
    ),
    "pi0": (
        "vla", "vlm", "vlm_robot", "diffusion_policy",
        "imitation_learning",
    ),
    "openpi": (
        "pi0", "vla", "vlm", "vlm_robot", "diffusion_policy",
        "imitation_learning",
    ),
    "openvla": ("vla", "vlm", "vlm_robot"),
    "rt2": ("vla", "vlm", "vlm_robot"),
    "diffusion": ("diffusion_policy", "policy"),
    "act": ("act_policy", "imitation", "transformer"),
    "piper": (
        "robot", "manipulation", "moveit2",
    ),
    "aloha": (
        "bimanual", "imitation_learning", "act_policy",
    ),
    "moveit": ("moveit2", "kinematics"),
    "grasp": ("grasp_planning", "manipulation"),
    "slam": ("slam_basics", "navigation"),
    "复现": ("imitation", "learning", "sim2real"),
    "机械臂": (
        "manipulation", "robot", "kinematics", "moveit2",
    ),
    "导航": ("navigation", "slam", "nav2"),
    "感知": (
        "perception", "detection", "camera", "point",
    ),
    "控制": ("control", "policy", "learning", "rl"),
    "仿真": ("simulation", "gazebo", "sim2real"),
    "抓取": ("grasp", "grasp_planning", "manipulation"),
    "模仿": ("imitation", "imitation_learning"),
    "强化": ("rl", "rl_basics", "rl_for_robotics"),
    "部署": ("deploy", "docker", "real_robot_ops"),
}


def tokenize(text: str) -> set[str]:
    """Extract tokens for overlap scoring.

    Captures ASCII alphanumeric runs, compound terms
    (e.g. ``pi0.5``), and contiguous Chinese character
    sequences. Applies synonym expansion for common
    robotics domain terms.
    """
    lower = text.lower()
    ascii_toks = set(re.findall(r"[a-z0-9]+", lower))
    compounds = set(
        re.findall(
            r"[a-z][a-z0-9]*(?:\.[a-z0-9]+)+", lower
        )
    )
    zh_runs = re.findall(r"[\u4e00-\u9fff]+", text)
    zh_toks: set[str] = set()
    for run in zh_runs:
        zh_toks.add(run)
        for ch in run:
            zh_toks.add(ch)

    tokens = ascii_toks | compounds | zh_toks

    expanded: set[str] = set()
    for t in tokens:
        if t in _SYNONYMS:
            expanded.update(_SYNONYMS[t])
    for c in compounds:
        stem = re.sub(r"\.\d+$", "", c)
        if stem in _SYNONYMS:
            expanded.update(_SYNONYMS[stem])
    tokens.update(expanded)
    return tokens


def requires_closure(
    root_ids: list[str],
    index: dict[str, dict],
) -> list[str]:
    """BFS reachable nodes; return in topological order.

    Uses Kahn's algorithm so prerequisites always precede
    dependents.  Ties broken by ``(level, id)`` for
    deterministic output among unrelated nodes.
    """
    seen: set[str] = set()
    stack = list(root_ids)
    while stack:
        nid = stack.pop()
        if nid in seen or nid not in index:
            continue
        seen.add(nid)
        for r in index[nid].get("requires") or []:
            if r not in seen:
                stack.append(r)

    dependents: dict[str, list[str]] = {
        n: [] for n in seen
    }
    in_deg: dict[str, int] = {n: 0 for n in seen}
    for nid in seen:
        for req in (
            index.get(nid, {}).get("requires") or []
        ):
            if req in seen:
                dependents[req].append(nid)
                in_deg[nid] += 1

    heap: list[tuple[int, str]] = [
        (index.get(n, {}).get("level", 99), n)
        for n, d in in_deg.items()
        if d == 0
    ]
    heapq.heapify(heap)
    result: list[str] = []
    while heap:
        _, nid = heapq.heappop(heap)
        result.append(nid)
        for dep in dependents[nid]:
            in_deg[dep] -= 1
            if in_deg[dep] == 0:
                heapq.heappush(
                    heap,
                    (
                        index.get(dep, {}).get(
                            "level", 99
                        ),
                        dep,
                    ),
                )

    remaining = sorted(
        (n for n in seen if n not in set(result)),
        key=lambda x: (
            index.get(x, {}).get("level", 99),
            x,
        ),
    )
    result.extend(remaining)
    return result


def score_nodes(
    task: str,
    schema_data: dict,
    learned: dict[str, list[str]] | None = None,
) -> list[tuple[str, int]]:
    """Return (node_id, score) sorted by score descending.

    Node matching considers id, label, an optional
    ``keywords`` list defined in the schema, and any
    learned keywords accumulated from LLM feedback.
    """
    tokens = tokenize(task)
    scored: list[tuple[str, int]] = []
    for node in schema_data.get("nodes") or []:
        nid = node.get("id")
        if nid is None:
            continue
        label = node.get("label") or ""
        node_tokens = tokenize(nid) | tokenize(label)
        for kw in node.get("keywords") or []:
            node_tokens.update(tokenize(kw))
        if learned is not None:
            for kw in learned.get(nid, []):
                node_tokens.update(tokenize(kw))
        overlap = len(tokens & node_tokens)
        if overlap > 0:
            scored.append((nid, overlap))
    scored.sort(key=lambda x: (-x[1], x[0]))
    return scored


def _build_next_steps(
    closure_ids: list[str],
    index: dict[str, dict],
    statuses: dict[str, str],
    gaps: list[str],
) -> list[str]:
    """Generate human-readable next-step suggestions."""
    if not gaps:
        return [
            "Ship evidence; raise relevant nodes to "
            "expert if warranted."
        ]
    steps: list[str] = []
    for nid in closure_ids:
        if nid not in gaps:
            continue
        meta = index.get(nid, {})
        label = meta.get("label", nid)
        prereqs = meta.get("requires") or []
        pending = [
            p
            for p in prereqs
            if statuses.get(p, "locked")
            in ("locked", "learning")
        ]
        if pending:
            steps.append(
                f"Unlock prerequisites for '{nid}' "
                f"({label}): {', '.join(pending)}"
            )
        else:
            cur = statuses.get(nid, "locked")
            steps.append(
                f"Advance '{nid}' ({label}) "
                f"from {cur} -> learning/solid"
            )
    return steps


def analyze(
    profile_name: str,
    task: str,
    explicit_node: str | None = None,
    *,
    use_rule_match: bool = True,
    use_llm_router: bool = False,
    persist_router_keywords: bool = True,
) -> GapResult:
    """Run gap analysis: optional rule overlap + optional LLM routing.

    When *explicit_node* is set, automatic matching is skipped.
    """
    p_dir = PROFILES_DIR / profile_name
    tree = load_skill_tree_raw(p_dir)
    if tree is None:
        return GapResult(error="skill-tree.yaml not found.")

    schema_name = tree.get("schema")
    if not schema_name:
        return GapResult(
            error="skill-tree.yaml has no 'schema' field."
        )

    schema_data = load_schema_raw(str(schema_name))
    if schema_data is None:
        return GapResult(
            error=f"Schema not found: {schema_name}"
        )

    index = schema_node_index(schema_data)
    statuses = status_by_node_id(tree)
    evidence_counts = _evidence_count_by_id(tree, profile_name)

    learned = lk_store.load(str(schema_name))

    roots_from_rule: list[str] = []
    roots_from_llm: list[str] = []
    learned_merged = False

    if explicit_node:
        if explicit_node not in index:
            return GapResult(
                error=(
                    f"Node '{explicit_node}' not in schema."
                ),
                error_key="node_unknown",
            )
        roots = [explicit_node]
        top_matches = [
            {
                "id": explicit_node,
                "label": index[explicit_node].get(
                    "label", explicit_node
                ),
                "score": 0,
                "source": "explicit",
            }
        ]
    else:
        if not task or not task.strip():
            return GapResult(
                error="Empty task text.",
                error_key="empty_task",
            )

        ranked: list[tuple[str, int]] = []
        roots_rule: list[str] = []

        if use_rule_match:
            ranked = score_nodes(
                task, schema_data, learned=learned
            )
            if ranked:
                max_sc = ranked[0][1]
                score_floor = max(2, max_sc // 2)
                roots_rule = [
                    nid
                    for nid, sc in ranked[:5]
                    if sc >= score_floor and nid in index
                ]
                if not roots_rule:
                    roots_rule = [ranked[0][0]]

        roots_llm: list[str] = []
        if use_llm_router:
            from nblane.core.gap_llm_router import (
                route_task_to_nodes,
            )

            outcome = route_task_to_nodes(
                task.strip(), str(schema_name), index
            )
            if outcome.ok:
                roots_llm = [
                    nid for nid in outcome.node_ids if nid in index
                ]
                if (
                    persist_router_keywords
                    and outcome.keywords
                ):
                    filtered = {
                        k: v
                        for k, v in outcome.keywords.items()
                        if k in index
                    }
                    expanded = (
                        lk_store.keywords_dict_from_router_payload(
                            filtered
                        )
                    )
                    if expanded:
                        lk_store.merge(str(schema_name), expanded)
                        learned_merged = True

        roots = _merge_root_ids(roots_llm, roots_rule)
        roots_from_rule = list(roots_rule)
        roots_from_llm = list(roots_llm)

        if not roots:
            return GapResult(
                error=(
                    "No skill nodes matched. Enable rule or AI "
                    "matching, or pick a node manually."
                ),
                error_key="no_roots",
            )

        top_matches = _build_top_matches(
            ranked, roots_llm, index
        )

    closure_ids = requires_closure(roots, index)

    closure: list[dict] = []
    gaps: list[str] = []
    strong: list[str] = []

    for nid in closure_ids:
        meta = index.get(nid, {})
        st = statuses.get(nid, "locked")
        is_gap = st in ("locked", "learning")
        closure.append(
            {
                "id": nid,
                "label": meta.get("label", nid),
                "status": st,
                "is_gap": is_gap,
                "evidence_count": evidence_counts.get(nid, 0),
            }
        )
        if is_gap:
            gaps.append(nid)
        else:
            strong.append(nid)

    next_steps = _build_next_steps(
        closure_ids, index, statuses, gaps
    )

    return GapResult(
        task=task.strip() if task else "",
        top_matches=top_matches,
        closure=closure,
        gaps=gaps,
        strong=strong,
        can_solve=not gaps,
        next_steps=next_steps,
        roots_from_rule=roots_from_rule,
        roots_from_llm=roots_from_llm,
        learned_merged=learned_merged,
    )


def format_text(result: GapResult) -> str:
    """Render a GapResult as human-readable CLI output."""
    if result.error:
        return f"ERROR: {result.error}"

    lines: list[str] = []
    if result.task:
        lines.append(f"Task: {result.task}")
        lines.append("")

    lines.append("Top matches (id: score):")
    for m in result.top_matches:
        src = m.get("source", "")
        suf = f" [{src}]" if src else ""
        lines.append(
            f"  - {m['id']} ({m['score']}): "
            f"{m['label']}{suf}"
        )
    if result.roots_from_rule or result.roots_from_llm:
        lines.append("")
        lines.append("Match sources:")
        lines.append(
            f"  rule roots: {result.roots_from_rule}"
        )
        lines.append(
            f"  LLM roots: {result.roots_from_llm}"
        )
        if result.learned_merged:
            lines.append("  learned keywords: updated")

    lines.append("")
    lines.append("--- Requires closure (ordered) ---")
    for n in result.closure:
        ec = int(n.get("evidence_count", 0) or 0)
        if ec > 0:
            status_part = f"{n['status']} ({ec} evidence)"
        else:
            status_part = n["status"]
        lines.append(
            f"  [{status_part}] {n['id']} — {n['label']}"
        )

    lines.append("")
    lines.append("--- Summary ---")
    if result.can_solve:
        lines.append(
            "can_solve: yes "
            "(all closure nodes are solid or expert)."
        )
    else:
        lines.append("can_solve: not yet (gaps below).")
        lines.append(
            "detect_gap: " + ", ".join(result.gaps)
        )

    lines.append("")
    lines.append("Suggested next steps:")
    for step in result.next_steps:
        lines.append(f"  - {step}")

    return "\n".join(lines)


def format_for_llm(result: GapResult) -> str:
    """Render a GapResult as plain text for LLM prompt."""
    lines = [f"Task: {result.task}", ""]
    lines.append("Top matched nodes:")
    for m in result.top_matches:
        src = m.get("source", "")
        extra = f" source={src}" if src else ""
        lines.append(
            f"  - {m['id']} ({m['label']}): "
            f"overlap score {m['score']}{extra}"
        )

    lines.append("")
    lines.append("Requires closure (all prerequisites):")
    for n in result.closure:
        gap_flag = " [GAP]" if n["is_gap"] else ""
        ec = int(n.get("evidence_count", 0) or 0)
        if ec > 0:
            status_part = f"{n['status']} ({ec} evidence)"
        else:
            status_part = n["status"]
        lines.append(
            f"  [{status_part}] {n['id']}"
            f" — {n['label']}{gap_flag}"
        )

    lines.append("")
    if result.can_solve:
        lines.append(
            "Conclusion: can_solve = YES "
            "(all nodes solid/expert)"
        )
    else:
        lines.append(
            "Conclusion: can_solve = NO. Gaps: "
            + ", ".join(result.gaps)
        )

    lines.append("")
    lines.append("Rule-based next steps:")
    for step in result.next_steps:
        lines.append(f"  - {step}")

    return "\n".join(lines)
