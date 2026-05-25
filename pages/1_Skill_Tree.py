"""Skill Tree -- visual editor for skill-tree.yaml.

Primary persist action is the title-row **Save** (not a separate toolbar).
Kanban uses **Reload** / **Save** in a toolbar; see docs/zh/product/web-experience.md.
"""

from __future__ import annotations

import streamlit as st

from nblane.core.evidence_review import (
    EVIDENCE_REVIEW_PAGE,
    skill_evidence_summaries,
)
from nblane.core.evidence_resolve import (
    resolve_node_evidence_dict,
)
from nblane.core.io import (
    EVIDENCE_POOL_FILENAME,
    STATUSES,
    profile_dir,
    save_evidence_pool,
    save_skill_tree,
    schema_node_index,
)
from nblane.core.models import EVIDENCE_TYPES, EvidencePool
from nblane.core.sync import write_generated_blocks
from nblane.web_cache import (
    clear_web_cache,
    load_evidence_pool_raw,
    load_schema_raw,
    load_skill_tree_raw,
)
from nblane.web_i18n import skill_tree_ui, status_label
from nblane.web_auth import require_login
from nblane.web_shared import (
    apply_ui_language_from_session,
    assert_files_current,
    ensure_file_snapshot,
    refresh_file_snapshots,
    render_current_goal_strip,
    render_git_backup_notices,
    render_page_help,
    select_profile,
    skill_status_emoji,
    stash_git_backup_results,
)

apply_ui_language_from_session()

_LEVEL_KEYS = {
    1: "level_l1",
    2: "level_l2",
    3: "level_l3",
    4: "level_l4",
}


def _level_label(level: int, ui: dict[str, str]) -> str:
    """Human-readable level line from i18n."""
    key = _LEVEL_KEYS.get(level)
    if key is not None:
        return ui[key]
    return ui["level_n"].format(n=level)


def _signal_value_label(ui: dict[str, str], prefix: str, value: object) -> str:
    """Return localized evidence signal values."""
    raw = str(value or "").strip()
    if not raw:
        return ""
    return ui.get(f"{prefix}_{raw}", raw)


def _build_rows(
    tree: dict,
    index: dict[str, dict],
) -> list[dict]:
    """Merge skill-tree nodes with schema metadata."""
    node_status: dict[str, dict] = {
        n["id"]: n
        for n in (tree.get("nodes") or [])
        if "id" in n
    }
    rows = []
    for nid, meta in index.items():
        node = node_status.get(nid, {})
        ev_raw = node.get("evidence") or []
        evidence: list[dict] = []
        if isinstance(ev_raw, list):
            for item in ev_raw:
                if isinstance(item, dict):
                    evidence.append(dict(item))
        ref_raw = node.get("evidence_refs") or []
        evidence_refs: list[str] = []
        seen_ref: set[str] = set()
        if isinstance(ref_raw, list):
            for x in ref_raw:
                if isinstance(x, str) and x.strip():
                    key = x.strip()
                    if key not in seen_ref:
                        seen_ref.add(key)
                        evidence_refs.append(key)
        rows.append(
            {
                "id": nid,
                "label": meta.get("label", nid),
                "level": meta.get("level", 0),
                "category": meta.get("category", ""),
                "status": node.get("status", "locked"),
                "note": node.get("note", ""),
                "evidence": evidence,
                "evidence_refs": evidence_refs,
            }
        )
    rows.sort(
        key=lambda r: (
            r["level"],
            r["category"],
            r["id"],
        )
    )
    return rows


def _rows_to_nodes(rows: list[dict]) -> list[dict]:
    """Convert edited rows back to skill-tree nodes list."""
    out: list[dict] = []
    for r in rows:
        has_inline = bool(r.get("evidence"))
        has_refs = bool(r.get("evidence_refs"))
        has_ev = has_inline or has_refs
        if (
            r.get("status") == "locked"
            and not r.get("note")
            and not has_ev
        ):
            continue
        node: dict = {
            "id": r["id"],
            "status": r["status"],
        }
        if r.get("note"):
            node["note"] = r["note"]
        evs = r.get("evidence") or []
        cleaned: list[dict] = []
        for ev in evs:
            if not isinstance(ev, dict):
                continue
            title = str(ev.get("title", "") or "").strip()
            et = str(ev.get("type", "practice") or "practice")
            if et not in EVIDENCE_TYPES:
                et = "practice"
            if not title:
                continue
            item = {"type": et, "title": title}
            for k in ("date", "url", "summary"):
                v = str(ev.get(k, "") or "").strip()
                if v:
                    item[k] = v
            cleaned.append(item)
        if cleaned:
            node["evidence"] = cleaned
        refs_in = r.get("evidence_refs") or []
        uniq: list[str] = []
        seen: set[str] = set()
        if isinstance(refs_in, list):
            for x in refs_in:
                if not isinstance(x, str) or not x.strip():
                    continue
                key = x.strip()
                if key not in seen:
                    seen.add(key)
                    uniq.append(key)
        if uniq:
            node["evidence_refs"] = uniq
        out.append(node)
    return out


def _save_and_sync(
    profile: str,
    tree: dict,
    rows: list[dict],
    pool_entries: list[dict],
    ui: dict[str, str],
) -> str:
    """Persist skill-tree.yaml, evidence-pool.yaml, and sync SKILL.md.

    Returns a message for ``st.success`` after rerun (toast survives
    ``st.rerun()`` via session state).
    """
    nodes = _rows_to_nodes(rows)
    new_tree = dict(tree)
    new_tree["nodes"] = nodes
    pdir = profile_dir(profile)
    tree_path = pdir / "skill-tree.yaml"
    pool_path = pdir / EVIDENCE_POOL_FILENAME
    skill_path = pdir / "SKILL.md"
    assert_files_current([tree_path, pool_path, skill_path])
    save_skill_tree(profile, new_tree)
    if pool_entries or (pdir / EVIDENCE_POOL_FILENAME).exists():
        save_evidence_pool(
            profile,
            {
                "profile": profile,
                "evidence_entries": pool_entries,
            },
        )
    yaml_path = str(
        (profile_dir(profile) / "skill-tree.yaml").resolve()
    )
    try:
        write_generated_blocks(profile_dir(profile))
        msg = ui["saved_synced_path"].format(path=yaml_path)
    except Exception:
        msg = ui["saved_yaml_path"].format(path=yaml_path)
    refresh_file_snapshots([tree_path, pool_path, skill_path])
    stash_git_backup_results()
    clear_web_cache()
    return msg


_ST_EDITOR = "nblane_skill_tree_editor_rows"
_ST_EV_FOCUS = "skill_tree_evidence_focus"
_ST_POOL = "nblane_skill_tree_pool"


def _resolved_count(
    row: dict,
    pool_entries: list[dict],
) -> int:
    """Materialized evidence count for expander label."""
    pool = EvidencePool.from_dict(
        {
            "profile": "",
            "updated": "",
            "evidence_entries": pool_entries,
        }
    )
    node_dict = {
        "evidence": row.get("evidence"),
        "evidence_refs": row.get("evidence_refs"),
    }
    return len(
        resolve_node_evidence_dict(node_dict, pool)
    )


def _session_pool_entries(profile: str) -> list[dict]:
    """Working copy of evidence-pool entries for the editor."""
    entry = st.session_state.get(_ST_POOL)
    if entry is None or entry.get("profile") != profile:
        raw = load_evidence_pool_raw(profile)
        entries: list[dict] = []
        if raw and isinstance(raw.get("evidence_entries"), list):
            entries = [
                dict(e)
                for e in raw["evidence_entries"]
                if isinstance(e, dict)
            ]
        st.session_state[_ST_POOL] = {
            "profile": profile,
            "entries": entries,
        }
    return st.session_state[_ST_POOL]["entries"]


def _session_rows(
    profile: str,
    tree: dict,
    index: dict[str, dict],
) -> list[dict]:
    """Keep row edits (status, note, evidence) across Streamlit reruns.

    Rebuilding from disk every run drops in-memory evidence rows before Save
    because ``st.rerun()`` reloads YAML. Session state holds the working copy.
    """
    entry = st.session_state.get(_ST_EDITOR)
    if entry is None or entry.get("profile") != profile:
        rows = _build_rows(tree, index)
        st.session_state[_ST_EDITOR] = {
            "profile": profile,
            "rows": rows,
        }
        st.session_state.pop(_ST_EV_FOCUS, None)
    return st.session_state[_ST_EDITOR]["rows"]


def _refresh_session_rows_from_disk(
    profile: str,
    index: dict[str, dict],
) -> None:
    """Replace session rows after a successful save (or external sync)."""
    tree_after = load_skill_tree_raw(profile)
    if tree_after is None:
        return
    st.session_state[_ST_EDITOR] = {
        "profile": profile,
        "rows": _build_rows(tree_after, index),
    }
    raw_pool = load_evidence_pool_raw(profile)
    pool_list: list[dict] = []
    if raw_pool and isinstance(
        raw_pool.get("evidence_entries"),
        list,
    ):
        pool_list = [
            dict(e)
            for e in raw_pool["evidence_entries"]
            if isinstance(e, dict)
        ]
    st.session_state[_ST_POOL] = {
        "profile": profile,
        "entries": pool_list,
    }


# -- Page --------------------------------------------------------

ui = skill_tree_ui()
require_login()
selected = select_profile()
ui = skill_tree_ui()
render_git_backup_notices()
_pdir = profile_dir(selected)
for _path in (
    _pdir / "skill-tree.yaml",
    _pdir / EVIDENCE_POOL_FILENAME,
    _pdir / "SKILL.md",
    _pdir / "goals.yaml",
):
    ensure_file_snapshot(_path)
tree = load_skill_tree_raw(selected)
if tree is None:
    _empty_head_l, _empty_head_goal = st.columns(
        [5, 2],
        gap="medium",
        vertical_alignment="top",
    )
    with _empty_head_l:
        st.title(ui["title"])
        st.caption(ui["page_context_line"])
    with _empty_head_goal:
        render_current_goal_strip(
            selected,
            compact=True,
            align="right",
        )
    render_page_help(
        ui,
        key=f"skill_tree_help_empty:{selected}",
        docs_path="docs/zh/guides/skill-tree.md",
    )
    st.error(
        ui["error_no_tree"].format(profile=selected)
    )
    st.stop()

schema_name = tree.get("schema", "")
schema = (
    load_schema_raw(schema_name) if schema_name else None
)
index = schema_node_index(schema) if schema else {}

rows = _session_rows(selected, tree, index)
pool_entries = _session_pool_entries(selected)
evidence_signal_by_id = {
    str(item.get("id", "")): item
    for item in skill_evidence_summaries(selected)
}

_save_toast = st.session_state.pop(
    "_skill_tree_save_toast",
    None,
)
if _save_toast:
    st.success(_save_toast)

# -- Title + save (top right) -------------------------------------

_head_l, _head_goal, _head_r = st.columns(
    [5, 2, 1],
    gap="medium",
    vertical_alignment="top",
)
with _head_l:
    st.title(ui["title"])
    st.caption(ui["page_context_line"])
with _head_goal:
    render_current_goal_strip(selected, compact=True, align="right")
with _head_r:
    render_page_help(
        ui,
        key=f"skill_tree_help:{selected}",
        docs_path="docs/zh/guides/skill-tree.md",
    )
    if st.button(
        ui["save_button"],
        type="primary",
        use_container_width=True,
        key="skill_tree_save_top",
    ):
        st.session_state["_skill_tree_save_toast"] = (
            _save_and_sync(
                selected,
                tree,
                rows,
                pool_entries,
                ui,
            )
        )
        _refresh_session_rows_from_disk(selected, index)
        st.rerun()

st.caption(ui["save_caption"])

st.page_link(
    EVIDENCE_REVIEW_PAGE,
    label=ui["evidence_review_link"],
    help=ui["pool_caption"],
)

# -- Global metrics -----------------------------------------------

counts: dict[str, int] = {s: 0 for s in STATUSES}
for r in rows:
    counts[r["status"]] = counts.get(
        r["status"], 0
    ) + 1
total = sum(counts.values())
lit = counts["expert"] + counts["solid"]

mcols = st.columns(5)
mcols[0].metric(ui["metric_expert"], counts["expert"])
mcols[1].metric(ui["metric_solid"], counts["solid"])
mcols[2].metric(ui["metric_learning"], counts["learning"])
mcols[3].metric(ui["metric_locked"], counts["locked"])
mcols[4].metric(
    ui["metric_lit_rate"],
    f"{lit}/{total}" if total else "—",
)

if total > 0:
    st.progress(
        lit / total,
        text=ui["progress_overall"].format(
            pct=lit / total,
        ),
    )

st.divider()

# -- Category tabs ------------------------------------------------

categories = sorted(
    {r["category"] for r in rows if r["category"]}
)

if not categories:
    st.info(ui["no_categories"])
    st.stop()

cat_tabs = st.tabs(
    [f"{cat}" for cat in categories]
)

for cat_tab, cat in zip(cat_tabs, categories):
    with cat_tab:
        cat_rows = [
            r for r in rows if r["category"] == cat
        ]
        cat_lit = sum(
            1
            for r in cat_rows
            if r["status"] in ("expert", "solid")
        )
        cat_total = len(cat_rows)
        frac = (
            cat_lit / cat_total if cat_total else 0
        )

        st.progress(
            frac,
            text=ui["cat_progress"].format(
                cat=cat,
                lit=cat_lit,
                total=cat_total,
                pct=frac,
            ),
        )

        by_level: dict[int, list[dict]] = {}
        for r in cat_rows:
            by_level.setdefault(
                r["level"], []
            ).append(r)

        for level in sorted(by_level):
            level_rows = by_level[level]
            level_label = _level_label(level, ui)
            st.markdown(f"#### {level_label}")

            for r in level_rows:
                with st.container(border=True):
                    c_info, c_status, c_note = (
                        st.columns([3, 2, 4])
                    )

                    with c_info:
                        em = skill_status_emoji(r["status"])
                        em_pre = f"{em} " if em else ""
                        st.markdown(
                            f"{em_pre}**{r['label']}**"
                        )
                        cap_l, cap_r = st.columns([5, 1])
                        with cap_l:
                            st.caption(f"`{r['id']}`")
                        with cap_r:
                            if st.button(
                                "📌",
                                key=(
                                    f"evpin_{cat}_{r['id']}"
                                ),
                                help=ui["evidence_pin_help"],
                            ):
                                st.session_state[
                                    _ST_EV_FOCUS
                                ] = r["id"]
                                st.rerun()
                        signal = evidence_signal_by_id.get(r["id"], {})
                        strength_label = _signal_value_label(
                            ui,
                            "evidence_strength",
                            signal.get("highest_strength", "unrated"),
                        )
                        review_label = _signal_value_label(
                            ui,
                            "evidence_review_status",
                            signal.get("review_status", ""),
                        )
                        signal_parts = [
                            ui["evidence_signal_count"].format(
                                n=signal.get("evidence_count", 0)
                            ),
                            ui["evidence_signal_strength"].format(
                                strength=strength_label
                            ),
                        ]
                        if review_label:
                            signal_parts.append(
                                ui["evidence_signal_review"].format(
                                    status=review_label
                                )
                            )
                        st.caption(" · ".join(signal_parts))
                        if signal.get("risk_level"):
                            st.warning(
                                ui["evidence_signal_risk"].format(
                                    reason=signal.get("risk_reason", "")
                                )
                            )

                    with c_status:
                        key = (
                            f"st_{cat}_{r['id']}"
                        )
                        cur_idx = (
                            list(STATUSES).index(
                                r["status"]
                            )
                            if r["status"] in STATUSES
                            else 0
                        )
                        new_status = st.selectbox(
                            ui["widget_status"],
                            STATUSES,
                            index=cur_idx,
                            key=key,
                            label_visibility=(
                                "collapsed"
                            ),
                            format_func=lambda s, u=ui: status_label(
                                u, s
                            ),
                        )
                        if new_status != r["status"]:
                            r["status"] = new_status

                    with c_note:
                        note_key = (
                            f"nt_{cat}_{r['id']}"
                        )
                        new_note = st.text_input(
                            ui["widget_note"],
                            value=r.get("note", ""),
                            key=note_key,
                            placeholder=ui["note_placeholder"],
                            label_visibility=(
                                "collapsed"
                            ),
                        )
                        if new_note != r.get(
                            "note", ""
                        ):
                            r["note"] = new_note

                    ev_list = r.setdefault("evidence", [])
                    r.setdefault("evidence_refs", [])
                    n_res = _resolved_count(r, pool_entries)
                    exp_title = ui["evidence_expander"].format(
                        n=n_res,
                    )
                    ev_open = (
                        st.session_state.get(_ST_EV_FOCUS)
                        == r["id"]
                    )
                    with st.expander(exp_title, expanded=ev_open):
                        title_by_id = {
                            str(e.get("id", "")): str(
                                e.get("title", "")
                            )
                            for e in pool_entries
                            if e.get("id")
                        }
                        opt_ids = sorted(title_by_id.keys())
                        cur_refs = r.get("evidence_refs") or []
                        if not isinstance(cur_refs, list):
                            cur_refs = []
                        cur_clean = [
                            x.strip()
                            for x in cur_refs
                            if isinstance(x, str) and x.strip()
                        ]
                        cur_clean = [x for x in cur_clean if x in opt_ids]
                        if opt_ids:
                            sel = st.multiselect(
                                ui["evidence_refs_label"],
                                options=opt_ids,
                                default=cur_clean,
                                format_func=lambda x, tb=title_by_id: (
                                    f"{x} — {tb.get(x, '')}"
                                ),
                                key=f"refs_{cat}_{r['id']}",
                                help=ui["evidence_refs_help"],
                            )
                            if sel != r.get("evidence_refs"):
                                r["evidence_refs"] = list(sel)
                        else:
                            st.caption(ui["pool_empty_hint"])
                        for i, ev in enumerate(list(ev_list)):
                            if not isinstance(ev, dict):
                                continue
                            st.caption(
                                f"{ui['evidence_item']} {i + 1}"
                            )
                            tcols = st.columns(5)
                            ev_types = sorted(EVIDENCE_TYPES)
                            cur_t = ev.get("type", "practice")
                            if cur_t not in ev_types:
                                cur_t = "practice"
                            with tcols[0]:
                                ev["type"] = st.selectbox(
                                    ui["evidence_type"],
                                    ev_types,
                                    index=ev_types.index(cur_t),
                                    key=(
                                        f"evt_{cat}_{r['id']}_{i}"
                                    ),
                                    label_visibility="collapsed",
                                )
                            with tcols[1]:
                                ev["title"] = st.text_input(
                                    ui["evidence_title"],
                                    value=(
                                        str(ev.get("title", ""))
                                    ),
                                    key=(
                                        f"evti_{cat}_{r['id']}_{i}"
                                    ),
                                    label_visibility="collapsed",
                                )
                            with tcols[2]:
                                ev["date"] = st.text_input(
                                    ui["evidence_date"],
                                    value=(
                                        str(ev.get("date", ""))
                                    ),
                                    key=(
                                        f"evd_{cat}_{r['id']}_{i}"
                                    ),
                                    label_visibility="collapsed",
                                )
                            with tcols[3]:
                                ev["url"] = st.text_input(
                                    ui["evidence_url"],
                                    value=str(ev.get("url", "")),
                                    key=(
                                        f"evu_{cat}_{r['id']}_{i}"
                                    ),
                                    label_visibility="collapsed",
                                )
                            with tcols[4]:
                                if st.button(
                                    ui["evidence_remove"],
                                    key=(
                                        f"evrm_{cat}_{r['id']}_{i}"
                                    ),
                                ):
                                    st.session_state[
                                        _ST_EV_FOCUS
                                    ] = r["id"]
                                    ev_list.pop(i)
                                    st.rerun()
                            ev["summary"] = st.text_area(
                                ui["evidence_summary"],
                                value=str(
                                    ev.get("summary", "")
                                ),
                                key=(
                                    f"evs_{cat}_{r['id']}_{i}"
                                ),
                                label_visibility="collapsed",
                                height=68,
                            )
                        if st.button(
                            ui["evidence_add"],
                            key=f"evadd_{cat}_{r['id']}",
                        ):
                            st.session_state[
                                _ST_EV_FOCUS
                            ] = r["id"]
                            ev_list.append(
                                {
                                    "type": "practice",
                                    "title": "",
                                    "date": "",
                                    "url": "",
                                    "summary": "",
                                }
                            )
                            st.rerun()
