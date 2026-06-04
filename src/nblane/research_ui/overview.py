"""Workspace overview cards, badges, and queues."""
from __future__ import annotations

import html

import streamlit as st

from nblane.core.research_connectors import CONNECTOR_PROVIDERS
from nblane.core.research_papers import paper_overview
from nblane.core.research_workspace import build_research_overview_payload
from nblane.web_cache import (
    load_chunks,
    load_connectors,
    load_research_claims,
)

from .context import ResearchContext
from ._helpers import (
    _cached_paper_rows,
    _l,
    _paper_library_key,
    _paper_library_sidecar_unavailable,
    _paper_library_target_url,
    _paper_library_workspace_url,
    _reader_view_url,
    _render_sidecar_link_button,
    _short_text,
)
from .paper_library import _library_view_count


def _render_research_overview_styles() -> None:
    st.markdown(
        """
<style>
:root {
  --ro-ink: #12201d;
  --ro-muted: #435854;
  --ro-subtle: #647571;
  --ro-line: #c8d4cf;
  --ro-paper: #ffffff;
  --ro-soft: #f6f8f7;
  --ro-accent: #176b5c;
  --ro-accent-strong: #0f4f43;
  --ro-accent-soft: #ddf2ec;
  --ro-risk-soft: #fff4d8;
  --ro-risk-line: rgba(146, 64, 14, .38);
}
div[data-testid="stPopover"] button {
  min-width: 4.2rem;
}
div[data-testid="stPopover"] button p {
  white-space: nowrap;
}
div[data-testid="stButton"] button:disabled {
  opacity: 1;
  border-color: #d6dfdb;
  background: #f7f9f8;
  color: #657672;
}
div[data-testid="stButton"] button:disabled p {
  color: #657672;
}
.ro-command-strip {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(280px, .9fr);
  gap: 12px;
  align-items: stretch;
  margin: 0 0 14px;
}
.ro-command-main,
.ro-safety-panel,
.ro-panel,
.ro-card {
  border: 1px solid var(--ro-line);
  border-radius: 8px;
  background: var(--ro-paper);
}
.ro-command-main,
.ro-safety-panel,
.ro-panel {
  padding: 13px 15px;
}
.ro-kicker {
  color: var(--ro-subtle);
  font-size: .74rem;
  font-weight: 820;
  text-transform: uppercase;
}
.ro-title {
  margin: 3px 0 6px;
  color: var(--ro-ink);
  font-size: 1.28rem;
  font-weight: 860;
  line-height: 1.2;
}
.ro-copy {
  margin: 0;
  color: var(--ro-muted);
  font-size: .86rem;
  line-height: 1.45;
}
.ro-flow {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin-top: 12px;
}
.ro-stage {
  min-width: 0;
  padding: 9px 10px;
  border: 1px solid var(--ro-line);
  border-radius: 8px;
  background: var(--ro-soft);
}
.ro-stage.is-hot {
  border-color: rgba(33, 104, 91, .35);
  background: var(--ro-accent-soft);
}
.ro-stage.is-warn {
  border-color: var(--ro-risk-line);
  background: var(--ro-risk-soft);
}
.ro-stage-label {
  overflow: hidden;
  color: var(--ro-subtle);
  font-size: .7rem;
  font-weight: 820;
  text-overflow: ellipsis;
  text-transform: uppercase;
  white-space: nowrap;
}
.ro-stage-value {
  margin-top: 4px;
  color: var(--ro-ink);
  font-size: 1.38rem;
  font-weight: 860;
  line-height: 1;
}
.ro-stage-note {
  min-height: 27px;
  margin-top: 6px;
  color: var(--ro-muted);
  font-size: .74rem;
  line-height: 1.25;
}
.ro-section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin: 2px 0 9px;
  color: var(--ro-ink);
  font-size: .98rem;
  font-weight: 850;
}
.ro-section-title small {
  color: var(--ro-subtle);
  font-size: .74rem;
  font-weight: 730;
}
.ro-queue-grid,
.ro-queue-tiles {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}
.ro-queue-chip {
  min-width: 0;
  padding: 9px 10px;
  border: 1px solid var(--ro-line);
  border-radius: 8px;
  background: var(--ro-soft);
}
.ro-queue-chip.is-live {
  border-color: rgba(33, 104, 91, .28);
  background: #f3faf7;
}
.ro-queue-chip.is-risk {
  border-color: var(--ro-risk-line);
  background: var(--ro-risk-soft);
}
.ro-queue-chip strong {
  display: block;
  overflow: hidden;
  color: var(--ro-ink);
  font-size: .84rem;
  line-height: 1.2;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.ro-queue-chip span {
  display: block;
  margin-top: 5px;
  color: var(--ro-muted);
  font-size: .77rem;
}
.ro-queue-tile {
  display: grid;
  min-width: 0;
  min-height: 82px;
  padding: 10px 11px;
  border: 1px solid var(--ro-line);
  border-radius: 8px;
  background: var(--ro-paper);
  color: var(--ro-ink) !important;
  gap: 5px;
  text-decoration: none !important;
}
.ro-queue-tile:hover {
  border-color: rgba(23, 107, 92, .42);
  background: #f3faf7;
}
.ro-queue-tile.is-live {
  border-color: rgba(23, 107, 92, .36);
  background: #f3faf7;
}
.ro-queue-tile.is-risk {
  border-color: var(--ro-risk-line);
  background: var(--ro-risk-soft);
}
.ro-queue-tile.is-disabled {
  background: #f7f9f8;
  color: #586a66 !important;
  cursor: default;
}
.ro-queue-tile-title {
  overflow: hidden;
  color: inherit;
  font-size: .85rem;
  font-weight: 830;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.ro-queue-tile-count {
  color: var(--ro-ink);
  font-size: 1.1rem;
  font-weight: 860;
  line-height: 1.05;
}
.ro-queue-tile-caption,
.ro-queue-tile-action {
  color: var(--ro-muted);
  font-size: .76rem;
  line-height: 1.25;
}
.ro-queue-tile-action {
  font-weight: 760;
}
.ro-queue-tile.is-disabled .ro-queue-tile-count,
.ro-queue-tile.is-disabled .ro-queue-tile-caption,
.ro-queue-tile.is-disabled .ro-queue-tile-action {
  color: #657672;
}
.ro-action,
.ro-card {
  display: grid;
  gap: 7px;
  margin-bottom: 9px;
}
.ro-action {
  padding: 0;
  margin-bottom: 6px;
  background: transparent;
}
.ro-card {
  padding: 11px 12px;
}
.ro-card-title {
  color: var(--ro-ink);
  font-size: .94rem;
  font-weight: 850;
  line-height: 1.35;
}
.ro-card-meta {
  color: var(--ro-muted);
  font-size: .78rem;
  line-height: 1.35;
  overflow-wrap: anywhere;
}
.ro-card-body {
  color: #2f403c;
  font-size: .84rem;
  line-height: 1.45;
}
.ro-badge {
  display: inline-flex;
  align-items: center;
  max-width: 100%;
  min-height: 20px;
  padding: 1px 7px;
  margin: 0 4px 4px 0;
  border: 1px solid rgba(49, 51, 63, .14);
  border-radius: 999px;
  background: rgba(49, 51, 63, .055);
  color: rgba(31, 41, 55, .86);
  font-size: .72rem;
  font-weight: 760;
  line-height: 1.25;
}
.ro-badge-ok {
  border-color: rgba(22, 163, 74, .22);
  background: rgba(22, 163, 74, .09);
  color: rgb(22, 101, 52);
}
.ro-badge-warn {
  border-color: rgba(245, 158, 11, .32);
  background: rgba(245, 158, 11, .12);
  color: rgb(146, 64, 14);
}
.ro-badge-alert {
  border-color: rgba(220, 38, 38, .24);
  background: rgba(220, 38, 38, .08);
  color: rgb(153, 27, 27);
}
.ro-empty {
  padding: 12px;
  border: 1px dashed var(--ro-line);
  border-radius: 8px;
  background: var(--ro-soft);
  color: var(--ro-muted);
  font-size: .86rem;
  line-height: 1.45;
}
.ro-empty strong {
  color: var(--ro-ink);
}
@media (max-width: 980px) {
  .ro-command-strip { grid-template-columns: minmax(0, 1fr); }
  .ro-flow { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .ro-queue-grid,
  .ro-queue-tiles { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 520px) {
  .ro-flow,
  .ro-queue-grid,
  .ro-queue-tiles { grid-template-columns: minmax(0, 1fr); }
}
</style>
""",
        unsafe_allow_html=True,
    )


def _overview_notice_key(ctx) -> str:
    selected = ctx.selected
    return f"research_overview_notice:{selected}"


def _set_overview_notice(ctx, message: str) -> None:
    st.session_state[_overview_notice_key(ctx)] = str(message or "")


def _pop_overview_notice(ctx) -> str:
    return str(st.session_state.pop(_overview_notice_key(ctx), "") or "")


def _overview_badge(label: object, tone: str = "neutral") -> str:
    clean = html.escape(str(label or "").strip())
    if not clean:
        return ""
    safe_tone = tone if tone in {"neutral", "ok", "warn", "alert"} else "neutral"
    return f'<span class="ro-badge ro-badge-{safe_tone}">{clean}</span>'


def _overview_badge_tone(label: object) -> str:
    text = str(label or "").casefold()
    if any(part in text for part in ("missing", "broken", "failed", "private", "risk", "缺失", "断裂", "失败", "私有", "风险")):
        return "alert"
    if any(part in text for part in ("warning", "stale", "duplicate", "needs", "警告", "过期", "重复", "需要")):
        return "warn"
    if any(part in text for part in ("ready", "pdf", "promoted", "reviewed", "就绪", "已推进", "已审阅")):
        return "ok"
    return "neutral"


def _overview_localized_badge(ctx, label: object) -> str:
    ui = ctx.ui
    text = str(label or "").strip()
    if not text:
        return ""
    mapping = {
        "Unsorted": _l(ui, "badge_unsorted", "Unsorted"),
        "PDF ready": _l(ui, "badge_pdf_ready", "PDF ready"),
        "PDF missing": _l(ui, "pdf_missing", "PDF missing"),
        "Stale translation": _l(ui, "badge_stale_translation", "Stale translation"),
        "Private source": _l(ui, "badge_private_source", "Private source"),
        "Needs structured extraction": _l(ui, "badge_needs_structured_extraction", "Needs structured extraction"),
        "GROBID unavailable": _l(ui, "badge_grobid_unavailable", "GROBID unavailable"),
        "Fallback extraction": _l(ui, "badge_fallback_extraction", "Fallback extraction"),
        "Duplicate risk": _l(ui, "duplicate_risk", "Duplicate risk"),
        "AI candidates": _l(ui, "ai_candidates", "AI candidates"),
        "ready": _l(ui, "ready", "Ready"),
        "risk": _l(ui, "risk", "Risk"),
    }
    return mapping.get(text, text)


def _overview_badges(ctx, labels: list[object], *, limit: int = 5) -> str:
    clean_labels = [label for label in labels if str(label or "").strip()]
    rendered = [
        _overview_badge(_overview_localized_badge(ctx, label), _overview_badge_tone(label))
        for label in clean_labels[:limit]
    ]
    if len(clean_labels) > limit:
        rendered.append(_overview_badge(f"+{len(clean_labels) - limit}"))
    return " ".join(item for item in rendered if item)


def _overview_stage(label: str, value: object, note: str = "", tone: str = "") -> str:
    classes = ["ro-stage"]
    if tone:
        classes.append(f"is-{tone}")
    return (
        f'<div class="{" ".join(classes)}">'
        f'<div class="ro-stage-label">{html.escape(label)}</div>'
        f'<div class="ro-stage-value">{html.escape(str(value))}</div>'
        f'<div class="ro-stage-note">{html.escape(note)}</div>'
        "</div>"
    )


def _overview_queue_chip(label: str, count: object, detail: str = "", tone: str = "") -> str:
    classes = ["ro-queue-chip"]
    if tone:
        classes.append(f"is-{tone}")
    suffix = f" · {detail}" if detail else ""
    return (
        f'<div class="{" ".join(classes)}">'
        f"<strong>{html.escape(label)}</strong>"
        f"<span>{html.escape(str(count))}{html.escape(suffix)}</span>"
        "</div>"
    )


def _overview_queue_tile(
    *,
    label: str,
    count: int,
    caption: str,
    action: str,
    url: str,
    tone: str = "",
    view: str = "",
    disabled: bool = False,
) -> str:
    classes = ["ro-queue-tile"]
    if tone:
        classes.append(f"is-{tone}")
    if count <= 0 or disabled:
        classes.append("is-disabled")
    tag = "a" if count > 0 and url and not disabled else "div"
    href = f' href="{html.escape(url, quote=True)}" rel="noopener noreferrer"' if tag == "a" else ""
    data_view = html.escape(view or "", quote=True)
    return (
        f'<{tag} class="{" ".join(classes)}" data-overview-queue="{data_view}"{href}>'
        f'<div class="ro-queue-tile-title">{html.escape(label)}</div>'
        f'<div class="ro-queue-tile-count">{html.escape(str(count))}</div>'
        f'<div class="ro-queue-tile-caption">{html.escape(caption)}</div>'
        f'<div class="ro-queue-tile-action">{html.escape(action)}</div>'
        f"</{tag}>"
    )


def _overview_card_html(ctx, 
    title: object,
    meta: object = "",
    body: object = "",
    badges: list[object] | None = None,
    *,
    action: bool = False,
) -> str:
    cls = "ro-action" if action else "ro-card"
    parts = [f'<div class="{cls}">']
    parts.append(f'<div class="ro-card-title">{html.escape(str(title or ""))}</div>')
    if meta:
        parts.append(f'<div class="ro-card-meta">{html.escape(str(meta))}</div>')
    if body:
        parts.append(f'<div class="ro-card-body">{html.escape(_short_text(body, 260))}</div>')
    if badges:
        parts.append(f"<div>{_overview_badges(ctx, list(badges))}</div>")
    parts.append("</div>")
    return "".join(parts)


def _overview_status_label(ctx, status: object) -> str:
    ui = ctx.ui
    clean = str(status or "").strip()
    if not clean:
        return ""
    return _l(ui, f"status_{clean}", clean.replace("_", " ").title())


def _overview_action_label(ctx, action: dict[str, object]) -> str:
    ui = ctx.ui
    kind = str(action.get("kind") or "")
    source_count = len(action.get("source_refs") or [])
    claim_count = len(action.get("claim_refs") or [])
    citation_count = len(action.get("citation_refs") or [])
    draft_count = len(action.get("draft_refs") or [])
    action_count = action.get("count")
    if isinstance(action_count, int):
        source_count = claim_count = citation_count = draft_count = action_count
    if kind == "continue_reading":
        return _l(ui, "overview_action_continue_reading", "Continue reading {count} source(s)").format(count=source_count)
    if kind == "review_claims":
        return _l(ui, "overview_action_review_claims", "Review {count} ready research claim(s)").format(count=claim_count)
    if kind == "fix_citations":
        return _l(ui, "overview_action_fix_citations", "Fix {count} citation warning(s)").format(count=citation_count)
    if kind == "review_private_publish_risk":
        return _l(ui, "overview_action_private_risk", "Review {count} private source risk(s)").format(count=source_count)
    if kind == "review_drafts":
        return _l(ui, "overview_action_review_drafts", "Review {count} synthesis draft(s)").format(count=draft_count)
    if kind == "import_sources":
        return _l(ui, "overview_action_import_sources", "Import papers, repos, or web sources")
    return str(action.get("label") or kind or _l(ui, "next_action", "Next action"))


def _overview_risk_label(ctx, kind: object) -> str:
    ui = ctx.ui
    clean = str(kind or "risk").strip()
    mapping = {
        "private_publish_risk": _l(ui, "risk_private_publish", "Private publish risk"),
        "broken_citations": _l(ui, "risk_broken_citations", "Broken citations"),
    }
    return mapping.get(clean, clean.replace("_", " ").title())


def _overview_risk_action_label(ctx, action: object) -> str:
    ui = ctx.ui
    clean = str(action or "").strip()
    mapping = {
        "open_export_gate": _l(ui, "risk_open_export_gate", "Open export gate"),
        "open_citation_inspector": _l(ui, "risk_open_citation_inspector", "Open citation inspector"),
    }
    return mapping.get(clean, clean.replace("_", " ").title())


def _focus_paper_library_view(ctx, view: str, *, detail_id: str = "", node_id: str = "") -> None:
    st.session_state[_paper_library_key(ctx, "view")] = view or "all"
    st.session_state[_paper_library_key(ctx, "node")] = node_id
    if detail_id:
        st.session_state[_paper_library_key(ctx, "detail")] = detail_id
    else:
        st.session_state.pop(_paper_library_key(ctx, "detail"), None)


def _focus_claim_review(ctx, *, source_id: str = "", status: str = "", queue: str = "") -> None:
    selected = ctx.selected
    if source_id:
        st.session_state[f"research_cc_source:{selected}"] = source_id
    st.session_state[f"research_claim_status_filter:{selected}"] = status
    st.session_state[f"research_claim_queue_filter:{selected}"] = queue


def _first_source_ref(action: dict[str, object], source_ids: set[str]) -> str:
    for ref in action.get("source_refs") or []:
        clean = str(ref or "").strip()
        if clean in source_ids:
            return clean
    return ""


def _render_overview_action_card(ctx, 
    action: dict[str, object],
    *,
    source_ids: set[str],
    row_by_id: dict[str, dict[str, object]],
) -> None:
    selected = ctx.selected
    ui = ctx.ui
    kind = str(action.get("kind") or "")
    label = _overview_action_label(ctx, action)
    source_ref = _first_source_ref(action, source_ids)
    meta_bits = []
    if source_ref:
        meta_bits.append(source_ref)
    if action.get("claim_refs"):
        meta_bits.append(f"{ui['research_claims']}: {len(action.get('claim_refs') or [])}")
    if action.get("citation_refs"):
        meta_bits.append(f"{ui['research_citations']}: {len(action.get('citation_refs') or [])}")
    if action.get("draft_refs"):
        meta_bits.append(f"{ui['synthesis_drafts']}: {len(action.get('draft_refs') or [])}")
    target = action.get("target") if isinstance(action.get("target"), dict) else {}
    secondary_targets = [item for item in action.get("secondary_targets") or [] if isinstance(item, dict)]
    paper_target = next(
        (item for item in secondary_targets if str(item.get("surface") or "") == "paper_library"),
        target if str(target.get("surface") or "") == "paper_library" else {},
    )
    paper_url = _paper_library_target_url(ctx, paper_target, fallback_detail_id=source_ref)

    with st.container(border=True):
        st.markdown(
            _overview_card_html(ctx, label, " · ".join(meta_bits), action=True),
            unsafe_allow_html=True,
        )
        b1, b2, b3 = st.columns(3)
        if kind == "continue_reading":
            row = row_by_id.get(source_ref, {})
            with b1:
                if row.get("has_pdf") and source_ref:
                    _render_sidecar_link_button(ctx, 
                        _l(ui, "open_reader", "Open Reader"),
                        _reader_view_url(ctx, source_ref),
                        key=f"overview_reader_link:{selected}:{source_ref}",
                        icon=":material/menu_book:",
                        type="primary",
                        use_container_width=True,
                    )
                else:
                    st.button(
                        _l(ui, "open_reader", "Open Reader"),
                        disabled=True,
                        key=f"overview_reader_link_disabled:{selected}:{source_ref}",
                        icon=":material/menu_book:",
                        use_container_width=True,
                    )
            with b2:
                _render_sidecar_link_button(ctx, 
                    _l(ui, "open_in_paper_library", "Open in Library"),
                    paper_url or _paper_library_workspace_url(ctx, detail_id=source_ref, return_to="overview"),
                    key=f"overview_open_library:{selected}:{kind}:{source_ref}",
                    icon=":material/library_books:",
                    use_container_width=True,
                )
        elif kind == "review_claims":
            with b1:
                if st.button(
                    _l(ui, "focus_ready_claims", "Focus ready claims"),
                    key=f"overview_focus_ready_claims:{selected}",
                    icon=":material/rule:",
                    type="primary",
                    use_container_width=True,
                ):
                    _focus_claim_review(ctx, source_id=source_ref, status="ready", queue="ready")
                    _set_overview_notice(ctx, _l(ui, "claims_focus_saved", "Claims review is focused on ready claims."))
                    st.rerun()
            with b2:
                _render_sidecar_link_button(ctx, 
                    _l(ui, "open_source_library", "Open source"),
                    paper_url or (
                        _paper_library_workspace_url(ctx, 
                            view="claims_need_review",
                            detail_id=source_ref,
                            focus="claims",
                            action="review_claims",
                            return_to="overview",
                        )
                    ),
                    key=f"overview_review_claims_source:{selected}:{source_ref}",
                    icon=":material/library_books:",
                    use_container_width=True,
                )
        elif kind == "fix_citations":
            with b1:
                if st.button(
                    _l(ui, "focus_quote_warnings", "Focus quote warnings"),
                    key=f"overview_focus_quote_warning:{selected}",
                    icon=":material/plagiarism:",
                    type="primary",
                    use_container_width=True,
                ):
                    _focus_claim_review(ctx, source_id=source_ref, queue="quote_warning")
                    _set_overview_notice(ctx, _l(ui, "citations_focus_saved", "Citation inspector is focused on quote warnings."))
                    st.rerun()
            with b2:
                _render_sidecar_link_button(ctx, 
                    _l(ui, "open_source_library", "Open source"),
                    paper_url or _paper_library_workspace_url(ctx, 
                        detail_id=source_ref,
                        focus="claims",
                        action="fix_citations",
                        return_to="overview",
                    ),
                    key=f"overview_fix_citations_source:{selected}:{source_ref}",
                    icon=":material/library_books:",
                    use_container_width=True,
                )
        elif kind in {"review_private_publish_risk", "review_drafts"}:
            with b1:
                if st.button(
                    _l(ui, "focus_export_gate", "Focus export gate"),
                    key=f"overview_focus_export:{selected}:{kind}",
                    icon=":material/policy:",
                    type="primary",
                    use_container_width=True,
                ):
                    st.session_state[f"research_export_focus:{selected}"] = kind
                    _set_overview_notice(ctx, _l(ui, "export_focus_saved", "Export gate focus updated."))
                    st.rerun()
            with b2:
                _render_sidecar_link_button(ctx, 
                    _l(ui, "open_paper_library_workspace", "Open Paper Library"),
                    paper_url or _paper_library_workspace_url(ctx, 
                        detail_id=source_ref,
                        focus="safety",
                        action="review_visibility",
                        return_to="overview",
                    ),
                    key=f"overview_export_library:{selected}:{kind}:{source_ref}",
                    icon=":material/library_books:",
                    use_container_width=True,
                )
        elif kind == "import_sources":
            with b1:
                _render_sidecar_link_button(ctx, 
                    _l(ui, "open_paper_library_workspace", "Open Paper Library"),
                    paper_url or _paper_library_workspace_url(ctx, view="unsorted", return_to="overview"),
                    key=f"overview_import_sources_library:{selected}",
                    icon=":material/library_books:",
                    type="primary",
                    use_container_width=True,
                )
            with b2:
                if st.button(
                    _l(ui, "focus_connector_inbox", "Connector inbox"),
                    key=f"overview_focus_connectors:{selected}",
                    icon=":material/hub:",
                    use_container_width=True,
                ):
                    st.session_state[f"research_advanced_focus:{selected}"] = "connectors"
                    _set_overview_notice(ctx, _l(ui, "connector_focus_saved", "Connector inbox focus updated."))
                    st.rerun()


def _render_workspace_overview(ctx, inbox) -> None:
    selected = ctx.selected
    _pdir = ctx.pdir
    ui = ctx.ui
    _render_research_overview_styles()
    all_paper_rows = _cached_paper_rows(_pdir, view="all")
    overview = paper_overview(_pdir, inbox=inbox, rows=all_paper_rows)
    command = build_research_overview_payload(_pdir, inbox=inbox, paper_rows_all=all_paper_rows)
    connector_rows = list(load_connectors(_pdir).get("connectors") or [])
    enabled_connectors = [row for row in connector_rows if bool(row.get("enabled", True))]
    row_by_id = {str(row.get("id") or ""): row for row in all_paper_rows}
    source_ids = {source.id for source in inbox.sources}
    funnel = command.get("funnel_counts") or {}
    action_rows = list(command.get("next_actions") or [])
    risk_rows = list(command.get("risks") or [])

    notice = _pop_overview_notice(ctx)
    if notice:
        st.success(notice)

    private_public = f"{overview['private_sources']} / {overview['public_sources']}"
    safety_badges = [
        _overview_badge(f"{_l(ui, 'private_public_sources', 'Private / public')}: {private_public}", "warn" if overview["private_sources"] else "neutral"),
        _overview_badge(f"{_l(ui, 'citation_broken', 'Citation broken')}: {overview['citation_broken']}", "alert" if overview["citation_broken"] else "ok"),
        _overview_badge(f"{_l(ui, 'private_publish_risk', 'Private publish risk')}: {overview['private_publish_risk']}", "alert" if overview["private_publish_risk"] else "ok"),
        _overview_badge(f"{_l(ui, 'stale_translation_warning', 'Stale translations')}: {overview['stale_translation_warning']}", "warn" if overview["stale_translation_warning"] else "ok"),
    ]
    st.markdown(
        "".join(
            [
                '<div class="ro-command-strip">',
                '<div class="ro-command-main">',
                f'<div class="ro-kicker">{html.escape(_l(ui, "research_workspace", "Research Workspace"))}</div>',
                f'<div class="ro-title">{html.escape(_l(ui, "research_command_center", "Research Command Center"))}</div>',
                f'<p class="ro-copy">{html.escape(_l(ui, "research_command_center_caption", "Sources, reading state, review queues, and export safety in one workspace."))}</p>',
                '<div class="ro-flow">',
                _overview_stage(_l(ui, "research_sources", "Sources"), funnel.get("sources", 0), _l(ui, "source_inbox", "Source Inbox")),
                _overview_stage(_l(ui, "papers_reading", "Reading"), funnel.get("reading", 0), _l(ui, "reader", "Reader"), "hot" if funnel.get("reading") else ""),
                _overview_stage(_l(ui, "extracted", "Extracted"), overview["annotated"], _l(ui, "chunks_annotations", "Chunks / annotations")),
                _overview_stage(_l(ui, "claims_ready", "Claims ready"), funnel.get("claims_ready", 0), _l(ui, "review_queue", "Review queue"), "hot" if funnel.get("claims_ready") else ""),
                _overview_stage(
                    _l(ui, "citations", "Citations"),
                    funnel.get("citations", 0),
                    _l(ui, "warnings_count", "{count} warnings").format(count=overview["citation_broken"]),
                    "warn" if overview["citation_broken"] else "",
                ),
                _overview_stage(_l(ui, "synthesis_drafts", "Drafts"), funnel.get("drafts", 0), _l(ui, "synthesis_export", "Synthesis / Export")),
                "</div>",
                "</div>",
                '<div class="ro-safety-panel">',
                f'<div class="ro-section-title">{html.escape(_l(ui, "integrity_publish_safety", "Integrity & Publish Safety"))}</div>',
                "<div>",
                " ".join(safety_badges),
                "</div>",
                f'<p class="ro-copy">{html.escape(ui["claim_boundary_hint"])}</p>',
                "</div>",
                "</div>",
            ]
        ),
        unsafe_allow_html=True,
    )

    q_reading = _library_view_count(all_paper_rows, "reading")
    q_missing_pdf = _library_view_count(all_paper_rows, "no_pdf")
    q_needs_extraction = _library_view_count(all_paper_rows, "needs_extraction")
    q_claims_need_review = _library_view_count(all_paper_rows, "claims_need_review")
    q_duplicate = _library_view_count(all_paper_rows, "duplicate_risk")
    q_stale = _library_view_count(all_paper_rows, "stale_translation")
    q_private = _library_view_count(all_paper_rows, "private")
    q_recent = _library_view_count(all_paper_rows, "recent")
    queue_fallback = {
        "reading": {
            "label": _l(ui, "reading", "Reading"),
            "count": q_reading,
            "caption": _l(ui, "reader", "Reader"),
            "action": _l(ui, "overview_queue_continue_reading", "Continue reading"),
            "tone": "live" if q_reading else "",
        },
        "needs_extraction": {
            "label": _l(ui, "needs_extraction", "Needs extraction"),
            "count": q_needs_extraction,
            "caption": _l(ui, "parser_status", "Parser status"),
            "action": _l(ui, "overview_queue_run_extraction", "Run extraction"),
            "tone": "risk" if q_needs_extraction else "",
        },
        "no_pdf": {
            "label": _l(ui, "pdf_missing", "PDF missing"),
            "count": q_missing_pdf,
            "caption": _l(ui, "paper_library", "Paper Library"),
            "action": _l(ui, "overview_queue_attach_pdf", "Attach PDF"),
            "tone": "risk" if q_missing_pdf else "",
        },
        "claims_need_review": {
            "label": _l(ui, "claims_need_review", "Claims review"),
            "count": q_claims_need_review,
            "caption": _l(ui, "ai_candidates", "AI candidates"),
            "action": _l(ui, "overview_queue_review_candidates", "Review candidates"),
            "tone": "live" if q_claims_need_review else "",
        },
        "duplicate_risk": {
            "label": _l(ui, "duplicate_risk", "Duplicate risk"),
            "count": q_duplicate,
            "caption": _l(ui, "metadata_review", "Metadata review"),
            "action": _l(ui, "overview_queue_deduplicate", "Deduplicate"),
            "tone": "risk" if q_duplicate else "",
        },
        "stale_translation": {
            "label": _l(ui, "stale_translation_warning", "Stale translations"),
            "count": q_stale,
            "caption": _l(ui, "translation", "Translation"),
            "action": _l(ui, "overview_queue_refresh_translations", "Refresh translations"),
            "tone": "risk" if q_stale else "",
        },
        "private": {
            "label": _l(ui, "private_sources", "Private sources"),
            "count": q_private,
            "caption": _l(ui, "visibility", "Visibility"),
            "action": _l(ui, "overview_queue_review_visibility", "Review visibility"),
            "tone": "risk" if q_private else "",
        },
        "recent": {
            "label": _l(ui, "recent_papers", "Recent"),
            "count": q_recent,
            "caption": _l(ui, "paper_library", "Paper Library"),
            "action": _l(ui, "overview_queue_open_recent", "Open recent"),
            "tone": "live" if q_recent else "",
        },
    }
    queue_rows = []
    for row in command.get("work_queues") or []:
        if not isinstance(row, dict):
            continue
        view = str(row.get("id") or "")
        fallback = queue_fallback.get(view, {})
        queue_rows.append(
            {
                "label": str(fallback.get("label") or row.get("label") or view),
                "view": view,
                "count": int(row.get("count") or fallback.get("count") or 0),
                "caption": str(fallback.get("caption") or row.get("caption") or ""),
                "action": str(fallback.get("action") or _l(ui, "open_in_paper_library", "Open in Library")),
                "tone": str(fallback.get("tone") or row.get("severity") or ""),
                "target": row.get("target") if isinstance(row.get("target"), dict) else {},
            }
        )
    if not queue_rows:
        queue_rows = [
            {"view": view, "target": {}, **values}
            for view, values in queue_fallback.items()
        ]
    sidecar_unavailable, _sidecar_message = _paper_library_sidecar_unavailable(ctx)
    queue_tiles = []
    for row in queue_rows:
        label = str(row.get("label") or "")
        view = str(row.get("view") or "")
        count = int(row.get("count") or 0)
        target = row.get("target") if isinstance(row.get("target"), dict) else {}
        target_url = _paper_library_target_url(ctx, target, fallback_detail_id="")
        queue_tiles.append(
            _overview_queue_tile(
                label=label,
                count=count,
                caption=str(row.get("caption") or ""),
                action=str(row.get("action") or ""),
                url=target_url or _paper_library_workspace_url(ctx, view=view, return_to="overview"),
                tone=str(row.get("tone") or ""),
                view=view,
                disabled=sidecar_unavailable,
            )
        )
    st.markdown(
        "".join(
            [
                '<div class="ro-panel">',
                f'<div class="ro-section-title">{html.escape(_l(ui, "work_queues", "Work queues"))}<small>{html.escape(_l(ui, "paper_library", "Paper Library"))} / {html.escape(ui["claims_citations"])}</small></div>',
                '<div class="ro-queue-tiles">',
                "".join(queue_tiles),
                "</div>",
                "</div>",
            ]
        ),
        unsafe_allow_html=True,
    )

    left, center, right = st.columns([1.05, 1.35, 1.1], gap="medium")
    with left:
        st.markdown(
            f'<div class="ro-section-title">{html.escape(_l(ui, "next_actions", "Next actions"))}<small>{len(action_rows)}</small></div>',
            unsafe_allow_html=True,
        )
        if action_rows:
            for action in action_rows[:5]:
                _render_overview_action_card(ctx, action, source_ids=source_ids, row_by_id=row_by_id)
        else:
            st.markdown(
                f'<div class="ro-empty">{html.escape(_l(ui, "no_research_actions", "No research actions need attention."))}</div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            f'<div class="ro-section-title">{html.escape(_l(ui, "discovery_updates", "Discovery updates"))}<small>{len(enabled_connectors)} {html.escape(ui["connectors_enabled"])}</small></div>',
            unsafe_allow_html=True,
        )
        provider_bits = []
        for provider in CONNECTOR_PROVIDERS:
            provider_rows = [row for row in connector_rows if str(row.get("provider") or "") == provider]
            last = max(provider_rows, key=lambda row: str(row.get("last_run") or ""), default={})
            last_result = last.get("last_result") if isinstance(last.get("last_result"), dict) else {}
            imported = int(last_result.get("imported") or 0)
            skipped = int(last_result.get("skipped") or 0)
            status = str(last.get("status") or "").strip()
            provider_bits.append(
                _overview_queue_chip(
                    provider,
                    _l(ui, "overview_imported_count", "{count} imported").format(count=imported),
                    (
                        _l(ui, "overview_skipped_count", "{count} skipped").format(count=skipped)
                        if skipped
                        else _l(ui, f"connector_status_{status or 'idle'}", status or _l(ui, "connector_status_idle", "idle"))
                    ),
                    "live" if imported else "",
                )
            )
        st.markdown(
            '<div class="ro-queue-grid">' + "".join(provider_bits) + "</div>",
            unsafe_allow_html=True,
        )
        if st.button(
            _l(ui, "focus_connector_inbox", "Connector inbox"),
            key=f"overview_connectors_button:{selected}",
            icon=":material/hub:",
            use_container_width=True,
        ):
            st.session_state[f"research_advanced_focus:{selected}"] = "connectors"
            _set_overview_notice(ctx, _l(ui, "connector_focus_saved", "Connector inbox focus updated."))
            st.rerun()

    with center:
        st.markdown(
            f'<div class="ro-section-title">{html.escape(_l(ui, "recent_work", "Recent work"))}<small>{html.escape(_l(ui, "paper_library", "Paper Library"))}</small></div>',
            unsafe_allow_html=True,
        )
        recent = sorted(
            all_paper_rows,
            key=lambda row: str(row.get("last_read") or ""),
            reverse=True,
        )[:5]
        if recent:
            for row in recent:
                source_id = str(row.get("id") or "")
                meta = " · ".join(
                    str(part)
                    for part in [
                        _overview_status_label(ctx, row.get("status")),
                        row.get("tree_path"),
                        row.get("last_read"),
                    ]
                    if part
                )
                metrics = [
                    f"{_l(ui, 'chunks', 'Chunks')}: {row.get('chunks_count', 0)}",
                    f"{ui['research_claims']}: {row.get('claims_count', 0)}",
                    f"{ui['research_citations']}: {row.get('citations_count', 0)}",
                ]
                st.markdown(
                    _overview_card_html(ctx, 
                        row.get("title") or source_id,
                        meta,
                        " · ".join(metrics),
                        list(row.get("badges") or []),
                    ),
                    unsafe_allow_html=True,
                )
                actions = st.columns([1, 1, 1])
                with actions[0]:
                    if row.get("has_pdf"):
                        _render_sidecar_link_button(ctx, 
                            _l(ui, "open_reader", "Open Reader"),
                            _reader_view_url(ctx, source_id),
                            key=f"overview_recent_reader:{selected}:{source_id}",
                            icon=":material/menu_book:",
                            use_container_width=True,
                        )
                    else:
                        st.button(
                            _l(ui, "open_reader", "Open Reader"),
                            key=f"overview_recent_reader_disabled:{selected}:{source_id}",
                            disabled=True,
                            icon=":material/menu_book:",
                            use_container_width=True,
                        )
                with actions[1]:
                    _render_sidecar_link_button(ctx, 
                        _l(ui, "open_in_paper_library", "Open in Library"),
                        _paper_library_workspace_url(ctx, 
                            detail_id=source_id,
                            focus="reading" if row.get("status") == "reading" else "metadata",
                            action="open_reader" if row.get("has_pdf") else "review_metadata",
                            return_to="overview",
                        ),
                        key=f"overview_recent_library:{selected}:{source_id}",
                        icon=":material/library_books:",
                        use_container_width=True,
                    )
                with actions[2]:
                    if st.button(
                        _l(ui, "focus_claims", "Claims"),
                        key=f"overview_recent_claims:{selected}:{source_id}",
                        disabled=not bool(row.get("claims_count") or row.get("citations_count")),
                        icon=":material/rule:",
                        use_container_width=True,
                    ):
                        _focus_claim_review(ctx, source_id=source_id)
                        _set_overview_notice(ctx, _l(ui, "claims_focus_saved", "Claims review focus updated."))
                        st.rerun()
        else:
            st.markdown(
                f'<div class="ro-empty">{html.escape(_l(ui, "recent_work_empty", "No recent paper reading yet."))}</div>',
                unsafe_allow_html=True,
            )

    with right:
        st.markdown(
            f'<div class="ro-section-title">{html.escape(_l(ui, "ready_to_review", "Ready to review"))}<small>{html.escape(ui["claims_citations"])}</small></div>',
            unsafe_allow_html=True,
        )
        claim_rows = load_research_claims(_pdir)
        ready_claims = [claim for claim in claim_rows if claim.status == "ready"]
        chunk_map = {chunk.id: chunk for chunk in load_chunks(_pdir)}
        if ready_claims:
            for claim in ready_claims[:4]:
                refs = []
                for ref in claim.source_refs:
                    if ref not in refs:
                        refs.append(ref)
                for chunk_ref in claim.chunk_refs:
                    chunk = chunk_map.get(chunk_ref)
                    if chunk is not None and chunk.source_id not in refs:
                        refs.append(chunk.source_id)
                st.markdown(
                    _overview_card_html(ctx, 
                        claim.id,
                        " · ".join([claim.type, f"confidence={claim.confidence}", ", ".join(refs[:2])]),
                        claim.text,
                        ["ready", *claim.warnings[:2]],
                    ),
                    unsafe_allow_html=True,
                )
                if st.button(
                    _l(ui, "review_claim", "Review claim"),
                    key=f"overview_ready_claim:{selected}:{claim.id}",
                    icon=":material/rule:",
                    use_container_width=True,
                ):
                    _focus_claim_review(ctx, source_id=refs[0] if refs else "", status="ready", queue="ready")
                    _set_overview_notice(ctx, _l(ui, "claims_focus_saved", "Claims review is focused on ready claims."))
                    st.rerun()
            if len(ready_claims) > 4:
                st.caption(_l(ui, "more_claims_hidden", "{count} more claim(s) hidden by this compact view.").format(count=len(ready_claims) - 4))
        else:
            st.markdown(
                (
                    '<div class="ro-empty">'
                    f'<strong>{html.escape(_l(ui, "claims_empty", "No claims yet."))}</strong><br>'
                    f'{html.escape(_l(ui, "claims_empty_next_step", "Run extraction in Paper Library, then create claim candidates from the Reader."))}'
                    "</div>"
                ),
                unsafe_allow_html=True,
            )
            seed_view = "needs_extraction" if q_needs_extraction else "all"
            seed_action = "run_extraction" if q_needs_extraction else "review_claims"
            if all_paper_rows:
                _render_sidecar_link_button(ctx, 
                    _l(ui, "prepare_claim_candidates", "Prepare claim candidates"),
                    _paper_library_workspace_url(ctx, 
                        view=seed_view,
                        focus="artifacts" if q_needs_extraction else "claims",
                        action=seed_action,
                        return_to="overview",
                    ),
                    key=f"overview_prepare_claim_candidates:{selected}:{seed_view}:{seed_action}",
                    icon=":material/auto_fix_high:",
                    use_container_width=True,
                )

        st.markdown(
            f'<div class="ro-section-title">{html.escape(_l(ui, "risk_queue", "Risk queue"))}<small>{len(risk_rows)}</small></div>',
            unsafe_allow_html=True,
        )
        if risk_rows:
            for risk in risk_rows:
                refs = [str(ref) for ref in risk.get("refs") or [] if str(ref)]
                st.markdown(
                    _overview_card_html(ctx, 
                        _overview_risk_label(ctx, risk.get("kind") or "risk"),
                        ", ".join(refs[:4]),
                        _overview_risk_action_label(ctx, risk.get("action") or ""),
                        ["risk"],
                    ),
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                f'<div class="ro-empty">{html.escape(_l(ui, "risk_queue_empty", "No publish blockers in the current research queue."))}</div>',
                unsafe_allow_html=True,
            )
        if st.button(
            _l(ui, "focus_export_gate", "Focus export gate"),
            key=f"overview_export_gate_button:{selected}",
            icon=":material/policy:",
            disabled=not bool(risk_rows),
            use_container_width=True,
        ):
            st.session_state[f"research_export_focus:{selected}"] = "risk_queue"
            _set_overview_notice(ctx, _l(ui, "export_focus_saved", "Export gate focus updated."))
            st.rerun()

