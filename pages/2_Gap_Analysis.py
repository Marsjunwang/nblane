"""Gap Analysis -- rule-based + AI-enhanced task matching."""

from __future__ import annotations

import streamlit as st

from nblane.core import gap as gap_engine
from nblane.core import learned_keywords as lk_store
from nblane.core import llm as llm_client
from nblane.core.io import (
    STATUSES,
    load_schema_raw,
    load_skill_tree_raw,
    save_skill_tree,
    schema_node_index,
)
from nblane.web_i18n import gap_ui, status_label
from nblane.web_shared import (
    render_llm_unavailable,
    select_profile,
    skill_status_emoji,
)

_STATUS_COLOR = {
    "expert": "#1a73e8",
    "solid": "#34a853",
    "learning": "#fbbc04",
    "locked": "#dadce0",
}

_AI_SYSTEM_EN = """\
You are a learning coach helping a robotics engineer \
grow their skills.
You receive the engineer's current skill tree and a \
rule-based gap analysis for a specific task. Your job \
is to provide:

1. **Why these gaps matter** — For each gap node, one \
sentence on why it is specifically needed for this task.
2. **Learning sequence** — Optimal order to address the \
gaps (2-5 steps), with a short rationale for the ordering. \
IMPORTANT: order by dependency — prerequisites that other \
gaps depend on MUST come first; within the same dependency \
depth, order by relevance to the task.
3. **After this task** — Which skill nodes should be \
updated and to what status once the task is completed \
(format each line as: \
`node_id: current_status -> new_status`).
4. **Keywords** — For every skill node you consider \
relevant to this task (not only gaps, also matched \
nodes), list 3-5 bilingual keyword pairs that connect \
the task description to that node. Each keyword MUST be \
a Chinese/English pair separated by a slash. Format \
each line EXACTLY as: \
`node_id: 中文词/english_term, 中文词2/english_term2`

Be concise, specific, and actionable. Stay grounded in \
the task context.
Do not invent skills not in the gap analysis."""

_AI_SYSTEM_ZH = """\
你是一位帮助机器人工程师成长的学习教练。
你收到该工程师当前的技能树和针对具体任务的规则式差距分析。\
你需要提供：

1. **这些缺口为何重要** — 对每个缺口节点，用一句话说明它\
对本任务的具体作用。
2. **学习顺序** — 解决这些缺口的最优顺序（2-5 步），\
并简要说明排序依据。\
重要：必须按依赖关系排序——其他缺口依赖的前置节点排在前面；\
相同依赖深度内按与任务的相关度排序。
3. **任务完成后** — 本任务完成后应更新哪些技能节点及目标状态\
（每行格式：`node_id: current_status -> new_status`）。
4. **关键词** — 对你认为与本任务相关的每个技能节点\
（不限于缺口，也包括已匹配节点），\
列出 3-5 个连接任务描述与该节点的双语关键词对。\
每个关键词必须是"中文/英文"格式，斜线分隔。\
每行格式严格为：\
`node_id: 中文词/english_term, 中文词2/english_term2`

回复语言：中文为主，英文术语、论文名称、代码标识符保留原文。
简明、具体、可操作。紧扣任务上下文。
不要编造差距分析中没有的技能节点。"""


def _ai_system() -> str:
    """Return the system prompt for the configured language."""
    return (
        _AI_SYSTEM_ZH
        if llm_client.reply_language() == "zh"
        else _AI_SYSTEM_EN
    )


def _gap_error_text(ui: dict, result) -> str:
    """Localized gap error; fall back to result.error."""
    if result.error_key:
        k = f"gap_error_{result.error_key}"
        if k in ui:
            return ui[k]
    return result.error or ""


def _match_source_label(ui: dict, src: str) -> str:
    """Human label for match provenance."""
    key = {
        "rule": "match_source_rule",
        "llm": "match_source_llm",
        "rule+llm": "match_source_both",
        "explicit": "match_source_explicit",
    }.get(src)
    if key is not None and key in ui:
        return ui[key]
    return src


def _apply_learned_from_reply(
    reply_text: str,
    profile: str,
    ui: dict,
) -> None:
    """Extract Keywords from coach text and merge into learned store.

    Runs for the first coach reply and for every follow-up assistant
    reply so bilingual pairs accumulate via ``merge`` (deduped).
    """
    tree_data = load_skill_tree_raw(profile)
    schema_name = (
        tree_data.get("schema", "") if tree_data else ""
    )
    if not schema_name or not reply_text:
        return
    new_kws = lk_store.parse_llm_keywords(reply_text)
    if not new_kws:
        return
    merged = lk_store.merge(schema_name, new_kws)
    learned_count = sum(len(v) for v in merged.values())
    st.caption(
        ui["learned_caption"].format(
            total=learned_count,
            nodes=len(merged),
            max_kw=lk_store.MAX_LEARNED_KEYWORDS,
        )
    )


def _skill_summary(name: str) -> str:
    """Build a compact skill-tree summary for LLM prompt."""
    tree = load_skill_tree_raw(name)
    if tree is None:
        return "(skill-tree.yaml not found)"
    schema_name = tree.get("schema", "")
    schema = (
        load_schema_raw(schema_name)
        if schema_name
        else None
    )
    index = (
        schema_node_index(schema) if schema else {}
    )
    lines = [
        f"Profile: {name}",
        f"Schema: {schema_name}",
        "Skill nodes:",
    ]
    for node in tree.get("nodes") or []:
        nid = node.get("id", "")
        label = index.get(nid, {}).get("label", nid)
        status = node.get("status", "locked")
        note = node.get("note", "")
        line = f"  [{status}] {nid} — {label}"
        if note:
            line += f": {note}"
        lines.append(line)
    return "\n".join(lines)


# -- Page --------------------------------------------------------

ui = gap_ui()
st.set_page_config(
    page_title=ui["page_title"], layout="wide"
)

if "gap_result" not in st.session_state:
    st.session_state.gap_result = None
if "gap_coach_messages" not in st.session_state:
    st.session_state.gap_coach_messages = []

selected = select_profile()

st.title(ui["title"])
st.caption(ui["page_context_line"])

tree_for_opts = load_skill_tree_raw(selected)
schema_name_opts = (
    tree_for_opts.get("schema", "") if tree_for_opts else ""
)
schema_opts = (
    load_schema_raw(schema_name_opts)
    if schema_name_opts
    else None
)
index_opts = (
    schema_node_index(schema_opts) if schema_opts else {}
)
node_id_list = sorted(index_opts.keys())

col_left, col_right_top = st.columns([3, 1])
with col_right_top:
    ai_enabled = llm_client.is_configured()
    if ai_enabled:
        st.success(
            f"AI: {llm_client.model_label()}", icon="🤖"
        )
    else:
        render_llm_unavailable(ui)

with col_left:
    task = st.text_area(
        ui["task_label"],
        placeholder=ui["task_placeholder"],
        height=100,
    )
    use_rule = st.checkbox(
        ui["use_rule_match"],
        value=True,
        key="gap_use_rule",
    )
    use_llm = st.checkbox(
        ui["use_llm_router"],
        value=ai_enabled,
        disabled=not ai_enabled,
        key="gap_use_llm",
    )
    if not ai_enabled:
        st.caption(ui["ai_add_key_caption"])

    manual_node = ""
    if node_id_list:
        manual_node = st.selectbox(
            ui["manual_node_label"],
            options=[""] + node_id_list,
            format_func=lambda x: (
                ui["manual_node_none"]
                if not x
                else f"{x} — {index_opts[x].get('label', x)}"
            ),
            key="gap_manual_node",
        )

can_run = bool(task.strip() or manual_node)
run = st.button(
    f"🔍 {ui['analyze_button']}",
    type="primary",
    disabled=not can_run,
)

if run and can_run:
    with st.spinner(ui["spinner_gap"]):
        if manual_node:
            result = gap_engine.analyze(
                selected,
                task,
                explicit_node=manual_node,
            )
        else:
            result = gap_engine.analyze(
                selected,
                task,
                use_rule_match=use_rule,
                use_llm_router=use_llm,
            )
    if result.error:
        st.error(_gap_error_text(ui, result))
        st.stop()
    st.session_state.gap_result = result
    if ai_enabled:
        skill_summary = _skill_summary(selected)
        gap_text = gap_engine.format_for_llm(result)
        user_msg = (
            f"Skill tree:\n{skill_summary}\n\n"
            f"Gap analysis:\n{gap_text}"
        )
        with st.spinner(ui["spinner_ai"]):
            ai_reply = llm_client.chat(
                _ai_system(), user_msg
            )
        st.session_state.gap_coach_messages = [
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": ai_reply},
        ]
        _apply_learned_from_reply(
            ai_reply, selected, ui
        )
    else:
        st.session_state.gap_coach_messages = []
elif st.session_state.gap_result is None:
    st.info(ui["analyze_hint"])
    st.stop()

result = st.session_state.gap_result

# -- Verdict + summary metrics ---------------------------------

verdict_icon = "✅" if result.can_solve else "⚠️"
verdict_text = (
    ui["verdict_ok"]
    if result.can_solve
    else ui["verdict_gap"]
)

vc1, vc2, vc3 = st.columns(3)
vc1.metric(ui["metric_verdict"], f"{verdict_icon} {verdict_text}")
vc2.metric(ui["metric_matches"], len(result.top_matches))
vc3.metric(
    ui["metric_gaps"],
    len(result.gaps) if result.gaps else 0,
)

if result.learned_merged:
    st.caption(ui["router_learned_caption"])

# -- Closure progress ------------------------------------------

if result.closure:
    gap_count = sum(
        1 for n in result.closure if n.get("is_gap")
    )
    ok_count = len(result.closure) - gap_count
    frac = (
        ok_count / len(result.closure)
        if result.closure
        else 0
    )
    st.progress(
        frac,
        text=ui["progress_text"].format(
            ok=ok_count,
            total=len(result.closure),
            pct=frac,
        ),
    )

st.divider()

# -- Two-column: matches + closure | AI -----------------------

left, right = st.columns(2)

with left:
    st.subheader(ui["subheader_matches"])
    for m in result.top_matches:
        with st.container(border=True):
            mc1, mc2 = st.columns([3, 1])
            with mc1:
                src = m.get("source", "")
                src_lbl = (
                    _match_source_label(ui, src) if src else ""
                )
                suffix = (
                    f" · *{src_lbl}*" if src_lbl else ""
                )
                st.markdown(
                    f"**{m['label']}** `{m['id']}`{suffix}"
                )
            with mc2:
                st.markdown(
                    f"{ui['match_score']}: **{m['score']}**"
                )

    st.subheader(ui["subheader_closure"])
    for n in result.closure:
        em = skill_status_emoji(n["status"])
        em_pre = f"{em} " if em else ""
        gap_flag = n.get("is_gap", False)
        st_disp = status_label(ui, n["status"])
        with st.container(border=True):
            gc1, gc2 = st.columns([4, 1])
            with gc1:
                label = (
                    f"{em_pre}**{n['label']}** "
                    f"`{n['id']}` *({st_disp})*"
                )
                if gap_flag:
                    label += (
                        f" **← {ui['gap_mark_suffix']}**"
                    )
                st.markdown(label)
            with gc2:
                if gap_flag:
                    st.error("GAP", icon="🔻")
                else:
                    st.success("OK", icon="✅")

    if result.next_steps:
        st.subheader(ui["subheader_next"])
        for step in result.next_steps:
            st.markdown(f"- {step}")

with right:
    st.subheader(ui["subheader_ai"])
    if not ai_enabled:
        st.info(ui["ai_disabled_hint"])
    else:
        msgs = st.session_state.gap_coach_messages
        fold_first_user = bool(
            msgs and msgs[0]["role"] == "user"
        )
        st.caption(ui["subheader_coach_followup"])
        if fold_first_user:
            with st.expander(
                ui["expander_first_prompt"],
                expanded=False,
            ):
                st.text(msgs[0]["content"])
        for i, m in enumerate(msgs):
            if fold_first_user and i == 0 and m["role"] == "user":
                continue
            with st.chat_message(m["role"]):
                st.markdown(m["content"])
        prompt = st.chat_input(
            ui["chat_followup_placeholder"],
            key="gap_followup_chat_input",
        )
        if prompt:
            msgs.append({"role": "user", "content": prompt})
            with st.spinner(ui["spinner_ai_followup"]):
                reply = llm_client.chat_messages(
                    _ai_system(), msgs
                )
            msgs.append(
                {"role": "assistant", "content": reply}
            )
            _apply_learned_from_reply(
                reply, selected, ui
            )
            st.rerun()

st.divider()

# -- Write-back panel (card-based) ----------------------------

if result.gaps:
    st.subheader(ui["writeback_title"])
    st.caption(ui["writeback_caption"])

    tree = load_skill_tree_raw(selected)
    if tree is not None:
        existing: dict[str, dict] = {
            n["id"]: n
            for n in (tree.get("nodes") or [])
        }

        updates: dict[str, str] = {}

        for gap_id in result.gaps:
            cur = existing.get(gap_id, {}).get(
                "status", "locked"
            )
            options = [
                s for s in STATUSES if s != cur
            ]

            with st.container(border=True):
                gc1, gc2, gc3, gc4 = st.columns(
                    [1, 3, 2, 2]
                )
                with gc1:
                    checked = st.checkbox(
                        ui["checkbox_select"],
                        key=f"wb_{gap_id}",
                        label_visibility="collapsed",
                    )
                with gc2:
                    em = skill_status_emoji(cur)
                    em_pre = f"{em} " if em else ""
                    st.markdown(
                        f"{em_pre}**{gap_id}**"
                    )
                with gc3:
                    cur_disp = status_label(ui, cur)
                    st.caption(
                        f"{ui['current_label']}: {cur_disp}"
                    )
                with gc4:
                    new_status = st.selectbox(
                        "→",
                        options,
                        index=min(
                            1, len(options) - 1
                        ),
                        key=f"ws_{gap_id}",
                        label_visibility="collapsed",
                        format_func=lambda s, u=ui: status_label(
                            u, s
                        ),
                    )
                if checked:
                    updates[gap_id] = new_status

        if updates and st.button(
            ui["apply_button"].format(n=len(updates)),
            type="primary",
        ):
            nodes = list(tree.get("nodes") or [])
            node_index = {
                n["id"]: i
                for i, n in enumerate(nodes)
            }
            for nid, new_st in updates.items():
                if nid in node_index:
                    nodes[node_index[nid]][
                        "status"
                    ] = new_st
                else:
                    nodes.append(
                        {
                            "id": nid,
                            "status": new_st,
                        }
                    )
            tree["nodes"] = nodes
            save_skill_tree(selected, tree)
            st.success(
                ui["success_updated"]
                + " "
                + ", ".join(
                    f"{k}→{v}"
                    for k, v in updates.items()
                )
            )
            st.rerun()
