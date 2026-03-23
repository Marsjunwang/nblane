"""nblane · Web UI entry point.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import re

import yaml
import streamlit as st

from nblane.core import llm as llm_client
from nblane.core.io import (
    STATUSES,
    load_evidence_pool_raw,
    load_schema_raw,
    load_skill_md,
    load_skill_tree_raw,
    profile_dir,
    schema_node_index,
)
from nblane.core.profile_ingest import (
    ingest_preview_delta,
    merge_ingest_patch,
    run_ingest_patch,
    schema_node_labels,
)
from nblane.core.profile_ingest_llm import ingest_resume_json
from nblane.web_i18n import home_ui
from nblane.web_shared import (
    drop_streamlit_widget_keys,
    remember_allow_and_drop_yaml_preview_keys,
    select_profile,
)

ui = home_ui()

st.set_page_config(
    page_title=ui["app_page_title"],
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

selected = select_profile()

_STATUS_EMOJI = {
    "expert": "🔵",
    "solid": "🟢",
    "learning": "🟡",
    "locked": "⬜",
}


def _parse_skill_md_sections(
    text: str,
) -> list[tuple[str, str]]:
    """Split SKILL.md into (heading, body) pairs.

    Returns a list of tuples: first element is the section
    heading (e.g. '## Identity'), second is the body text
    under that heading. Content before the first heading
    is captured as '(header)'.
    """
    parts: list[tuple[str, str]] = []
    current_heading = "(header)"
    buf: list[str] = []

    for line in text.splitlines(keepends=True):
        if re.match(r"^#{1,3}\s", line):
            parts.append(
                (current_heading, "".join(buf))
            )
            current_heading = line.strip()
            buf = []
        else:
            buf.append(line)

    parts.append((current_heading, "".join(buf)))
    return parts


def _rejoin_sections(
    sections: list[tuple[str, str]],
) -> str:
    """Reassemble sections back into a single string."""
    parts: list[str] = []
    for heading, body in sections:
        if heading != "(header)":
            parts.append(heading + "\n")
        parts.append(body)
    return "".join(parts)


# -- Page header -----------------------------------------------

st.title(ui["app_page_title"])
st.caption(ui["app_caption"].format(profile=selected))

# -- Tabs: Overview | Editor | Raw ----------------------------

tab_overview, tab_editor, tab_raw = st.tabs(
    [
        ui["tab_overview"],
        ui["tab_editor"],
        ui["tab_raw"],
    ]
)

# ── TAB 1: Overview ──────────────────────────────────────────

tree = load_skill_tree_raw(selected)

with tab_overview:
    if tree is not None:
        schema_name = tree.get("schema", "")
        schema = (
            load_schema_raw(schema_name)
            if schema_name
            else None
        )
        index = (
            schema_node_index(schema) if schema else {}
        )

        counts: dict[str, int] = {s: 0 for s in STATUSES}
        for n in tree.get("nodes") or []:
            st_val = n.get("status", "locked")
            counts[st_val] = counts.get(st_val, 0) + 1
        total = sum(counts.values())
        lit = counts["expert"] + counts["solid"]

        st.subheader(ui["sub_overview"])
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric(ui["metric_expert"], counts["expert"])
        c2.metric(ui["metric_solid"], counts["solid"])
        c3.metric(ui["metric_learning"], counts["learning"])
        c4.metric(ui["metric_locked"], counts["locked"])
        c5.metric(
            ui["metric_lit_rate"],
            f"{lit}/{total}" if total else "—",
        )

        if total > 0:
            progress_val = lit / total
            st.progress(
                progress_val,
                text=ui["progress_overall"].format(
                    pct=progress_val,
                ),
            )

        st.divider()

        cats: dict[str, list[dict]] = {}
        node_status = {
            n["id"]: n.get("status", "locked")
            for n in (tree.get("nodes") or [])
            if "id" in n
        }
        for nid, meta in index.items():
            cat = meta.get("category", "other")
            status = node_status.get(nid, "locked")
            cats.setdefault(cat, []).append(
                {
                    "id": nid,
                    "label": meta.get("label", nid),
                    "status": status,
                }
            )

        st.subheader(ui["sub_category"])
        for cat in sorted(cats):
            nodes = cats[cat]
            cat_lit = sum(
                1
                for n in nodes
                if n["status"] in ("expert", "solid")
            )
            cat_total = len(nodes)
            frac = (
                cat_lit / cat_total
                if cat_total
                else 0
            )

            col_name, col_bar = st.columns([1, 3])
            with col_name:
                st.markdown(
                    f"**{cat}** "
                    f"({cat_lit}/{cat_total})"
                )
            with col_bar:
                st.progress(frac)

            with st.expander(
                ui["home_expander_cat"].format(
                    cat=cat,
                    total=cat_total,
                )
            ):
                for n in nodes:
                    em = _STATUS_EMOJI.get(
                        n["status"], "⬜"
                    )
                    st.markdown(
                        f"{em} **{n['label']}** "
                        f"`{n['id']}`"
                    )
    else:
        st.info(
            ui["info_no_skill_tree"].format(
                profile=selected,
            )
        )

    with st.expander(ui["resume_expander"], expanded=False):
        resume_text = st.text_area(
            ui["resume_placeholder"],
            height=140,
            key=f"resume_txt_{selected}",
        )
        allow_resume = st.checkbox(
            ui["resume_allow_status"],
            value=False,
            key=f"resume_allow_{selected}",
        )
        st.caption(ui["resume_allow_status_help"])
        rgen = st.button(
            ui["resume_generate"],
            key=f"resume_gen_{selected}",
        )
        if rgen and resume_text.strip():
            if not llm_client.is_configured():
                st.warning(ui["resume_no_ai"])
            else:
                with st.spinner(ui["resume_spinner"]):
                    patch, err = ingest_resume_json(
                        selected,
                        resume_text,
                    )
                if err is not None:
                    st.error(ui["resume_err"].format(msg=err))
                elif patch is not None:
                    drop_streamlit_widget_keys(
                        [
                            f"rp_pool_{selected}",
                            f"rp_tree_{selected}",
                        ]
                    )
                    st.session_state[
                        f"resume_ingest_patch_{selected}"
                    ] = patch
                    st.rerun()

        rkey = f"resume_ingest_patch_{selected}"
        if rkey in st.session_state:
            remember_allow_and_drop_yaml_preview_keys(
                allow_resume,
                prev_state_key=f"_resume_allow_prev_{selected}",
                pool_key=f"rp_pool_{selected}",
                tree_key=f"rp_tree_{selected}",
            )
            patch = st.session_state[rkey]
            pool_r = load_evidence_pool_raw(selected)
            tree_r = load_skill_tree_raw(selected)
            st.caption(
                ui["merge_preview_llm_status_line"].format(
                    mode=(
                        ui["merge_llm_status_applied"]
                        if allow_resume
                        else ui["merge_llm_status_ignored"]
                    ),
                )
            )
            rmerge = merge_ingest_patch(
                selected,
                pool_r,
                tree_r,
                patch,
                allow_status_change=allow_resume,
                bump_locked_with_evidence=True,
            )
            if rmerge.warnings:
                st.caption(ui["resume_warn"])
                for w in rmerge.warnings:
                    st.caption(f"- {w}")
            if rmerge.ok and (
                rmerge.merged_pool is not None
                or rmerge.merged_tree is not None
            ):
                lab = schema_node_labels(tree_r)
                new_ev, tree_delta = ingest_preview_delta(
                    pool_r,
                    tree_r,
                    rmerge.merged_pool,
                    rmerge.merged_tree,
                    lab,
                )
                with st.expander(
                    ui["merge_preview_delta_title"],
                    expanded=True,
                ):
                    if new_ev:
                        st.markdown(
                            f"**{ui['merge_preview_delta_new_evidence']}**"
                        )
                        for line in new_ev:
                            st.markdown(f"- {line}")
                    if tree_delta:
                        st.markdown(
                            f"**{ui['merge_preview_delta_tree']}**"
                        )
                        for line in tree_delta:
                            st.markdown(f"- {line}")
                    if not new_ev and not tree_delta:
                        st.caption(ui["merge_preview_delta_none"])
            if rmerge.ok and (
                rmerge.merged_pool is not None
                or rmerge.merged_tree is not None
            ):
                st.caption(ui["merge_preview_yaml_readonly_caption"])
            if rmerge.ok and rmerge.merged_pool:
                st.markdown(f"**{ui['resume_preview_pool']}**")
                st.code(
                    yaml.dump(
                        rmerge.merged_pool,
                        allow_unicode=True,
                        default_flow_style=False,
                        sort_keys=False,
                    ),
                    language="yaml",
                )
            if rmerge.ok and rmerge.merged_tree:
                st.markdown(f"**{ui['resume_preview_tree']}**")
                st.code(
                    yaml.dump(
                        rmerge.merged_tree,
                        allow_unicode=True,
                        default_flow_style=False,
                        sort_keys=False,
                    ),
                    language="yaml",
                )
            if not rmerge.ok:
                for e in rmerge.errors:
                    st.error(e)
            else:
                if st.button(
                    ui["resume_apply"],
                    key=f"resume_apply_{selected}",
                    type="primary",
                ):
                    _, apply_r = run_ingest_patch(
                        selected,
                        patch,
                        allow_status_change=allow_resume,
                        bump_locked_with_evidence=True,
                        dry_run=False,
                    )
                    if apply_r.ok:
                        st.success(ui["resume_applied"])
                        del st.session_state[rkey]
                    else:
                        for e in apply_r.errors:
                            st.error(e)
                        for w in apply_r.warnings:
                            st.warning(w)

    st.divider()
    st.markdown(ui["home_nav"])

# ── TAB 2: Structured SKILL.md editor ────────────────────────

with tab_editor:
    skill_path = profile_dir(selected) / "SKILL.md"
    skill_content = load_skill_md(selected)

    if not skill_content:
        st.warning(ui["warning_no_skill_md"])
    else:
        sections = _parse_skill_md_sections(
            skill_content
        )

        edited_sections: list[tuple[str, str]] = []
        for i, (heading, body) in enumerate(sections):
            if heading == "(header)":
                edited_sections.append((heading, body))
                continue

            is_generated = (
                "BEGIN GENERATED" in body
            )
            with st.expander(
                heading
                + (
                    ui["gen_suffix"]
                    if is_generated
                    else ""
                ),
                expanded=(i <= 2),
            ):
                if is_generated:
                    st.caption(ui["gen_caption"])
                    st.code(body.strip(), language="markdown")
                    edited_sections.append(
                        (heading, body)
                    )
                else:
                    new_body = st.text_area(
                        heading,
                        value=body,
                        height=max(
                            120,
                            body.count("\n") * 22 + 60,
                        ),
                        key=f"sec_{i}",
                        label_visibility="collapsed",
                    )
                    edited_sections.append(
                        (heading, new_body)
                    )

        col_save, col_hint = st.columns([1, 4])
        with col_save:
            if st.button(
                ui["save_skill_md"],
                type="primary",
                key="save_structured",
            ):
                merged = _rejoin_sections(
                    edited_sections
                )
                skill_path.write_text(
                    merged, encoding="utf-8"
                )
                st.success(ui["home_saved"])
                st.rerun()
        with col_hint:
            st.caption(
                ui["hint_after_save"].format(
                    profile=selected,
                )
            )

# ── TAB 3: Raw editor ────────────────────────────────────────

with tab_raw:
    skill_path = profile_dir(selected) / "SKILL.md"
    raw_content = load_skill_md(selected)

    if not raw_content:
        st.warning(ui["warning_no_skill_md"])
    else:
        edited_raw = st.text_area(
            ui["raw_label"],
            value=raw_content,
            height=500,
            key="skill_md_raw",
        )

        col_save2, col_hint2 = st.columns([1, 4])
        with col_save2:
            if st.button(
                ui["save_skill_md"],
                type="primary",
                key="save_raw",
            ):
                skill_path.write_text(
                    edited_raw, encoding="utf-8"
                )
                st.success(ui["home_saved"])
                st.rerun()
        with col_hint2:
            st.caption(
                ui["hint_after_save"].format(
                    profile=selected,
                )
            )
