"""Connector UI and manual import flow."""
from __future__ import annotations

import streamlit as st
import yaml

from nblane.core.research_connectors import (
    CONNECTOR_PROVIDERS,
    discover_connector_items,
    import_connector_items,
    import_manual_connector_items,
    preview_manual_connector_items,
    sync_connector,
    upsert_connector,
)
from nblane.web_cache import clear_web_cache, load_connectors, load_research_sources
from nblane.web_shared import (
    assert_files_current,
    refresh_file_snapshots,
    stash_git_backup_results,
)

from .context import ResearchContext
from ._helpers import (
    _l,
    _node_options,
    _paper_library_workspace_url,
    _reader_view_url,
    _render_sidecar_link_button,
    _short_text,
)


def _render_connector_candidate_picker(ctx, 
    preview: dict[str, object],
    *,
    key_prefix: str,
) -> tuple[list[str], str, str]:
    ui = ctx.ui
    st.subheader(_l(ui, "connector_inbox", "Connector Inbox"))
    p1, p2, p3 = st.columns(3)
    p1.metric(_l(ui, "discovered", "Discovered"), preview.get("discovered", 0))
    p2.metric(_l(ui, "importable", "Importable"), preview.get("importable", 0))
    p3.metric(_l(ui, "duplicates", "Duplicates"), preview.get("skipped", 0))
    for warning in preview.get("warnings") or []:
        st.warning(str(warning))

    node_options = _node_options(ctx, include_unsorted=False)
    metadata_only_ref = "__metadata_only__"
    target_options = {
        "": _l(ui, "source_inbox", "Source Inbox"),
        metadata_only_ref: _l(ui, "metadata_only", "Metadata only"),
        **node_options,
    }
    target_value = st.selectbox(
        _l(ui, "connector_import_target", "Import target"),
        options=list(target_options),
        format_func=lambda ref: target_options.get(ref, ref),
        key=f"{key_prefix}:target",
    )
    target_node = "" if target_value == metadata_only_ref else target_value
    target_kind = (
        "metadata_only"
        if target_value == metadata_only_ref
        else "collection"
        if target_node
        else "source_inbox"
    )
    selected_fingerprints: list[str] = []
    for index, candidate in enumerate(preview.get("candidates") or []):
        if not isinstance(candidate, dict):
            continue
        item = candidate.get("item") if isinstance(candidate.get("item"), dict) else {}
        duplicate = candidate.get("duplicate") if isinstance(candidate.get("duplicate"), dict) else {}
        fingerprint = str(candidate.get("fingerprint") or "")
        with st.container(border=True):
            head, pick = st.columns([4, 1], vertical_alignment="center")
            with head:
                st.markdown(f"**{item.get('title') or fingerprint}**")
                st.caption(
                    " · ".join(
                        str(value)
                        for value in [
                            item.get("provider"),
                            item.get("kind"),
                            item.get("published"),
                            item.get("url"),
                        ]
                        if value
                    )
                )
                if item.get("summary"):
                    st.write(_short_text(item.get("summary"), 320))
                if duplicate.get("is_duplicate"):
                    st.warning(
                        _l(ui, 
                            "connector_duplicate",
                            "Duplicate candidate: {reason} -> {source_id}",
                        ).format(
                            reason=duplicate.get("reason") or "duplicate",
                            source_id=duplicate.get("existing_source_id") or "",
                        )
                    )
            with pick:
                selected_candidate = st.checkbox(
                    _l(ui, "import_candidate", "Import"),
                    value=bool(candidate.get("selected")) and not bool(duplicate.get("is_duplicate")),
                    disabled=bool(duplicate.get("is_duplicate")) or not fingerprint,
                    key=f"{key_prefix}:candidate:{index}",
                )
            if selected_candidate and fingerprint:
                selected_fingerprints.append(fingerprint)
    return selected_fingerprints, target_node, target_kind


def _connector_import_result_key(ctx) -> str:
    selected = ctx.selected
    return f"research_connector_import_result:{selected}"


def _remember_connector_import_result(ctx, 
    result,
    *,
    provider: str,
    target_node: str,
    target_kind: str,
) -> None:
    if not result.imported_source_ids:
        return
    st.session_state[_connector_import_result_key(ctx)] = {
        "provider": provider,
        "target_node": target_node,
        "target_kind": target_kind,
        "imported": int(result.imported),
        "skipped": int(result.skipped),
        "source_ids": [str(source_id) for source_id in result.imported_source_ids if str(source_id)],
    }


def _render_connector_import_next_actions(ctx) -> None:
    selected = ctx.selected
    ui = ctx.ui
    state = st.session_state.get(_connector_import_result_key(ctx))
    if not isinstance(state, dict):
        return
    source_ids = [str(source_id) for source_id in state.get("source_ids") or [] if str(source_id)]
    source_map = load_research_sources(selected).by_id()
    imported = [source_map[source_id] for source_id in source_ids if source_id in source_map]
    if not imported:
        st.session_state.pop(_connector_import_result_key(ctx), None)
        return

    papers = [source for source in imported if source.kind == "paper"]
    pdf_ready = [source for source in papers if (source.metadata or {}).get("pdf_asset_ref")]
    first_paper = papers[0] if papers else None
    first_pdf = pdf_ready[0] if pdf_ready else None
    target_node = str(state.get("target_node") or "")
    target_kind = str(state.get("target_kind") or ("collection" if target_node else "source_inbox"))
    review_url = (
        _paper_library_workspace_url(ctx, node_id=target_node, detail_id=first_paper.id)
        if target_node and first_paper
        else _paper_library_workspace_url(ctx, view="unsorted", detail_id=first_paper.id)
        if first_paper
        else ""
    )

    try:
        container = st.container(border=True)
    except TypeError:
        container = st.container()
    with container:
        st.success(
            _l(ui, 
                "connector_import_next_actions",
                "Imported {imported} source(s). Continue with the imported queue below.",
            ).format(imported=state.get("imported") or len(imported))
        )
        st.caption(
            " · ".join(
                part
                for part in [
                    str(state.get("provider") or ""),
                    (
                        _l(ui, "metadata_only", "Metadata only")
                        if target_kind == "metadata_only"
                        else _l(ui, "connector_target_collection", "Collection target")
                        if target_node
                        else _l(ui, "source_inbox", "Source Inbox")
                    ),
                    (
                        _l(ui, "connector_skipped_count", "Skipped {skipped}").format(skipped=state.get("skipped"))
                        if state.get("skipped")
                        else ""
                    ),
                ]
                if part
            )
        )
        for source in imported[:4]:
            st.write(f"- **{source.title or source.id}** `{source.id}`")
        if len(imported) > 4:
            st.caption(_l(ui, "connector_more_imports", "And {count} more imported source(s).").format(count=len(imported) - 4))

        a1, a2, a3, a4, a5 = st.columns(5)
        with a1:
            if first_paper:
                _render_sidecar_link_button(ctx, 
                    _l(ui, "open_in_paper_library", "Open in Paper Library"),
                    _paper_library_workspace_url(ctx, node_id=target_node, detail_id=first_paper.id),
                    key=f"connector_open_library:{selected}:{first_paper.id}:{target_node}",
                    icon=":material/library_books:",
                    type="primary",
                    use_container_width=True,
                )
            else:
                st.button(
                    _l(ui, "open_in_paper_library", "Open in Paper Library"),
                    disabled=True,
                    key=f"connector_open_library_disabled:{selected}",
                    use_container_width=True,
                )
        with a2:
            if review_url:
                _render_sidecar_link_button(ctx, 
                    _l(ui, "review_imported_sources", "Review imported"),
                    review_url,
                    key=f"connector_review_imported:{selected}:{first_paper.id if first_paper else ''}:{target_node}",
                    icon=":material/rule:",
                    use_container_width=True,
                )
            else:
                st.button(
                    _l(ui, "review_imported_sources", "Review imported"),
                    disabled=True,
                    key=f"connector_review_imported_disabled:{selected}",
                    use_container_width=True,
                )
        with a3:
            if first_pdf:
                _render_sidecar_link_button(ctx, 
                    _l(ui, "open_reader", "Open Reader"),
                    _reader_view_url(ctx, first_pdf.id),
                    key=f"connector_open_reader:{selected}:{first_pdf.id}",
                    icon=":material/menu_book:",
                    use_container_width=True,
                )
            else:
                st.button(
                    _l(ui, "open_reader", "Open Reader"),
                    disabled=True,
                    key=f"connector_open_reader_disabled:{selected}",
                    use_container_width=True,
                )
        with a4:
            if st.button(
                _l(ui, "run_extraction", "Run extraction"),
                key=f"connector_prepare_reader:{selected}:{':'.join(source_ids[:3])}",
                disabled=not pdf_ready,
                icon=":material/auto_fix_high:",
                use_container_width=True,
            ):
                result = _prepare_reader_artifacts_for_sources(ctx, [source.id for source in pdf_ready])
                st.success(
                    _l(ui, "connector_prepared_sources", "Prepared Reader artifacts for {count} source(s).").format(
                        count=len(result.get("prepared") or [])
                    )
                )
                for warning in result.get("warnings") or []:
                    st.warning(str(warning))
        with a5:
            if st.button(
                _l(ui, "dismiss", "Dismiss"),
                key=f"connector_import_next_actions_dismiss:{selected}",
                icon=":material/close:",
                use_container_width=True,
            ):
                st.session_state.pop(_connector_import_result_key(ctx), None)
                st.rerun()
        if not papers:
            st.caption(
                _l(ui, 
                    "connector_non_paper_review_hint",
                    "Non-paper imports stay in the Source Inbox queue on the Inbox & Connectors tab.",
                )
            )
        elif not pdf_ready:
            st.caption(
                _l(ui, 
                    "connector_pdf_needed_hint",
                    "Reader and extraction actions appear after an imported paper has a local PDF asset.",
                )
            )


def _render_connector_provider_cards(ctx, rows: list[dict[str, object]]) -> None:
    ui = ctx.ui
    st.markdown(f"**{_l(ui, 'connector_provider_status', 'Provider status')}**")
    columns = st.columns(3)
    for index, provider in enumerate(CONNECTOR_PROVIDERS):
        provider_rows = [row for row in rows if str(row.get("provider") or "") == provider]
        latest = max(
            provider_rows,
            key=lambda row: str(row.get("last_run") or ""),
            default={},
        )
        last_result = latest.get("last_result") if isinstance(latest.get("last_result"), dict) else {}
        with columns[index % len(columns)]:
            with st.container(border=True):
                st.markdown(f"**{provider}**")
                if not provider_rows:
                    st.caption(_l(ui, "connector_provider_unconfigured", "No saved automation connector."))
                else:
                    enabled_count = sum(1 for row in provider_rows if bool(row.get("enabled", True)))
                    st.caption(
                        _l(ui, 
                            "connector_provider_configured",
                            "{configured} configured · {enabled} enabled",
                        ).format(configured=len(provider_rows), enabled=enabled_count)
                    )
                    s1, s2 = st.columns(2)
                    s1.metric(_l(ui, "status", "Status"), str(latest.get("status") or "idle"))
                    s2.metric(_l(ui, "last_imported", "Imported"), last_result.get("imported", 0))
                    st.caption(
                        " · ".join(
                            part
                            for part in [
                                f"{_l(ui, 'last_run', 'Last run')}: {latest.get('last_run') or '-'}",
                                f"{_l(ui, 'skipped', 'Skipped')}: {last_result.get('skipped', 0)}",
                            ]
                            if part
                        )
                    )
                    if last_result.get("error"):
                        st.warning(str(last_result.get("error")))
                if provider in {"x_twitter", "xiaohongshu"}:
                    st.caption(
                        _l(ui, 
                            "connector_manual_provider_hint",
                            "Manual import remains available when automation is unavailable.",
                        )
                    )


def _render_connector_run_history(ctx, rows: list[dict[str, object]]) -> None:
    ui = ctx.ui
    history = []
    for row in rows:
        last_result = row.get("last_result") if isinstance(row.get("last_result"), dict) else {}
        history.append(
            {
                "id": row.get("id"),
                "provider": row.get("provider"),
                "status": row.get("status") or "idle",
                "last_run": row.get("last_run") or "",
                "discovered": last_result.get("discovered", 0),
                "imported": last_result.get("imported", 0),
                "skipped": last_result.get("skipped", 0),
                "selected": last_result.get("selected", ""),
                "warnings": "; ".join(str(item) for item in last_result.get("warnings") or []),
                "error": last_result.get("error") or "",
            }
        )
    if not history:
        return
    with st.expander(_l(ui, "connector_run_history", "Connector run history"), expanded=False):
        st.dataframe(history, use_container_width=True, hide_index=True)


def _render_connectors(ctx) -> None:
    selected = ctx.selected
    _pdir = ctx.pdir
    ui = ctx.ui
    _sources_path = ctx.sources_path
    _research_connectors_path = ctx.research_connectors_path
    st.subheader(ui["connectors"])
    st.caption(ui["connectors_caption"])
    rows = list(load_connectors(_pdir).get("connectors") or [])
    _render_connector_provider_cards(ctx, rows)
    _render_connector_run_history(ctx, rows)
    _render_connector_import_next_actions(ctx)
    manual_key = f"research_manual_connector_preview:{selected}"
    with st.expander(_l(ui, "manual_connector_import", "Manual connector import"), expanded=False):
        with st.form(f"research_manual_connector:{selected}"):
            manual_provider = st.selectbox(
                ui["connector_provider"],
                CONNECTOR_PROVIDERS,
                key=f"research_manual_connector_provider:{selected}",
            )
            manual_privacy = st.selectbox(
                ui["privacy_default"],
                ["private", "public"],
                key=f"research_manual_connector_privacy:{selected}",
            )
            manual_raw = st.text_area(
                _l(ui, "manual_connector_items", "Paste URLs, CSV, or JSON list"),
                height=120,
                key=f"research_manual_connector_raw:{selected}",
            )
            manual_preview = st.form_submit_button(_l(ui, "preview", "Preview"), type="primary")
        if manual_preview:
            try:
                st.session_state[manual_key] = {
                    "provider": manual_provider,
                    "privacy": manual_privacy,
                    "raw": manual_raw,
                    "preview": preview_manual_connector_items(_pdir, manual_provider, manual_raw),
                }
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
        manual_state = st.session_state.get(manual_key)
        if isinstance(manual_state, dict) and isinstance(manual_state.get("preview"), dict):
            selected_manual, manual_target, manual_target_kind = _render_connector_candidate_picker(ctx, 
                manual_state["preview"],
                key_prefix=f"research_manual_connector_picker:{selected}",
            )
            if st.button(
                _l(ui, "import_selected_connector_items", "Import selected"),
                type="primary",
                disabled=not selected_manual,
                key=f"research_manual_connector_import:{selected}",
            ):
                try:
                    assert_files_current([_sources_path])
                    result = import_manual_connector_items(
                        _pdir,
                        str(manual_state.get("provider") or manual_provider),
                        manual_state.get("raw") or "",
                        selected_manual,
                        privacy_default=str(manual_state.get("privacy") or "private"),
                        target={
                            "kind": manual_target_kind,
                            "node_id": manual_target,
                        },
                    )
                    _remember_connector_import_result(ctx, 
                        result,
                        provider=str(manual_state.get("provider") or manual_provider),
                        target_node=manual_target,
                        target_kind=manual_target_kind,
                    )
                    refresh_file_snapshots([_sources_path])
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(
                        _l(ui, 
                            "connector_imported_count",
                            "Imported {imported} candidate(s); skipped {skipped}.",
                        ).format(imported=result.imported, skipped=result.skipped)
                    )
                    st.session_state.pop(manual_key, None)
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
    rows = list(load_connectors(_pdir).get("connectors") or [])
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.caption(ui["connectors_empty"])

    with st.expander(ui["configure_connector"], expanded=not rows):
        with st.form(f"research_connector_config:{selected}"):
            provider = st.selectbox(ui["connector_provider"], CONNECTOR_PROVIDERS)
            connector_id = st.text_input(ui["connector_id"])
            query = st.text_input(ui["connector_query"])
            enabled = st.checkbox(ui["connector_enabled"], value=True)
            privacy_default = st.selectbox(ui["privacy_default"], ["private", "public"])
            options_raw = st.text_area(ui["connector_options"], height=90)
            submitted = st.form_submit_button(ui["save"], type="primary")
        if submitted:
            try:
                options = yaml.safe_load(options_raw) if options_raw.strip() else {}
                if options is None:
                    options = {}
                if not isinstance(options, dict):
                    raise ValueError("Connector options must be a YAML mapping.")
                row = upsert_connector(
                    _pdir,
                    provider=provider,
                    connector_id=connector_id,
                    query=query,
                    enabled=enabled,
                    privacy_default=privacy_default,
                    options=options,
                )
                stash_git_backup_results()
                clear_web_cache()
                st.success(ui["created"].format(id=row["id"]))
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    rows = list(load_connectors(_pdir).get("connectors") or [])
    if not rows:
        return
    picked = st.selectbox(
        ui["connector_id"],
        options=[str(row.get("id")) for row in rows],
        key=f"research_connector_run:{selected}",
    )
    preview_key = f"research_connector_preview:{selected}:{picked}"
    dry_col, run_col = st.columns(2)
    with dry_col:
        if st.button(ui["connector_dry_run"]):
            try:
                st.session_state[preview_key] = discover_connector_items(_pdir, picked)
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
    with run_col:
        if st.button(ui["connector_run_now"], type="primary"):
            try:
                assert_files_current([_sources_path, _research_connectors_path])
                result = sync_connector(_pdir, picked, dry_run=False)
                refresh_file_snapshots([_sources_path, _research_connectors_path])
                stash_git_backup_results()
                clear_web_cache()
                st.code(
                    yaml.dump(result.to_dict(), allow_unicode=True, default_flow_style=False, sort_keys=False),
                    language="yaml",
                )
            except Exception as exc:
                st.error(str(exc))

    preview = st.session_state.get(preview_key)
    if not isinstance(preview, dict):
        return
    selected_fingerprints, target_node, target_kind = _render_connector_candidate_picker(ctx, 
        preview,
        key_prefix=f"research_connector_picker:{selected}:{picked}",
    )

    if st.button(
        _l(ui, "import_selected_connector_items", "Import selected"),
        type="primary",
        disabled=not selected_fingerprints,
        key=f"research_connector_import_selected:{selected}:{picked}",
    ):
        try:
            assert_files_current([_sources_path, _research_connectors_path])
            result = import_connector_items(
                _pdir,
                picked,
                selected_fingerprints,
                target={
                    "kind": target_kind,
                    "node_id": target_node,
                },
            )
            _remember_connector_import_result(ctx, 
                result,
                provider=str(preview.get("provider") or picked),
                target_node=target_node,
                target_kind=target_kind,
            )
            refresh_file_snapshots([_sources_path, _research_connectors_path])
            stash_git_backup_results()
            clear_web_cache()
            st.success(
                _l(ui, 
                    "connector_imported_count",
                    "Imported {imported} candidate(s); skipped {skipped}.",
                ).format(imported=result.imported, skipped=result.skipped)
            )
            st.session_state.pop(preview_key, None)
            st.rerun()
        except Exception as exc:
            st.error(str(exc))


