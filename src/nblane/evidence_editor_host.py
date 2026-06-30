"""Shared evidence-editor host: event handling + rendering for the React editor.

Extracted from ``pages/2_Evidence_Review.py`` so the same editor can be embedded
on more than one page (Evidence Review, Project Board) without duplicating the
event layer. The host owns pool/skill-tree IO, duplicate + reformat session
state, the event dispatcher, and ``render()``.

Session keys are namespaced by ``key_prefix`` + profile so two embeds can coexist
without colliding. The default prefix (``"evidence_editor"``) reproduces the
keys Evidence Review used before extraction, so its behavior is unchanged.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import streamlit as st

from nblane.core import llm as llm_client
from nblane.core.evidence_dedup import (
    apply_merge_or_deprecate,
    find_duplicate_candidates,
    suggest_duplicates_ai,
)
from nblane.core.evidence_from_output import (
    active_source_index,
    evidence_row_from_blog_post,
    evidence_row_from_output,
    evidence_source_key,
)
from nblane.core.evidence_migrate import (
    content_hash,
    detect_language,
    migrate_evidence_pool,
    refresh_from_crystallized_tasks,
    render_kanban_task_source,
)
from nblane.core.evidence_pool_id import new_evidence_id
from nblane.core.evidence_review import (
    apply_project_ref_inferences,
    build_evidence_editor_payload,
    build_evidence_review,
    bulk_set_pool_field,
    done_task_evidence_blockers,
    internal_project_goal_index,
    link_skill_to_evidence_nodes,
    set_evidence_skill_refs,
    validate_internal_project_refs,
)
from nblane.core.evidence_migrate import backfill_row
from nblane.core.ingest_parse import (
    _llm_status_effective,
    _ordinal_placeholder_to_id,
    _status_rank,
    parse_ingest_patch,
)
from nblane.core.io import (
    EVIDENCE_POOL_FILENAME,
    profile_dir,
    load_schema_raw,
    save_evidence_pool,
    save_skill_tree,
    schema_node_index,
)
from nblane.core.kanban_archive import kanban_ref, kanban_ref_id
from nblane.core.models import EVIDENCE_CONFIDENCES, EVIDENCE_STRENGTHS
from nblane.core.profile_ingest_llm import reformat_evidence
from nblane.core.profile_ingest_llm import ingest_kanban_done_json
from nblane.core.sync import write_generated_blocks
from nblane.core.web_preferences import load_web_preferences, update_web_preferences
from nblane.evidence_editor_component import (
    evidence_editor_component_available,
    st_evidence_editor,
)
from nblane.web_cache import (
    clear_web_cache,
    load_evidence_pool_raw,
    load_skill_tree_raw,
)
from nblane.web_i18n import evidence_review_ui
from nblane.web_shared import (
    assert_files_current,
    current_goal_agent_context,
    kanban_ai_backend,
    refresh_file_snapshots,
    stash_git_backup_results,
)

# v2 fields the editor is allowed to write back on save_evidence.
EDITOR_SAVE_FIELDS = (
    "title",
    "summary",
    "formatted_content",
    "source_excerpt",
    "type",
    "date",
    "url",
    "strength",
    "confidence",
    "review_status",
    "public_readiness",
    "language",
    "origin",
    "origin_ref",
    "origin_detail",
    "project_refs",
    "experience_refs",
    "source_refs",
)

# Editor-writable fields that hold a list of refs (cleaned per item).
EDITOR_SAVE_LIST_FIELDS = frozenset(
    {"project_refs", "experience_refs", "source_refs"}
)


def compact_evidence_row(row: dict) -> dict:
    """Drop empty optional fields before writing YAML. Pure."""
    out = {
        "id": str(row.get("id", "") or "").strip(),
        "type": str(row.get("type", "practice") or "practice").strip(),
        "title": str(row.get("title", "") or "").strip(),
    }
    for key in ("date", "url", "summary", "strength", "confidence"):
        value = str(row.get(key, "") or "").strip()
        if value:
            out[key] = value
    source_excerpt = str(row.get("source_excerpt", "") or "").strip()
    if source_excerpt:
        out["source_excerpt"] = source_excerpt
    # v2 provenance scalars (strip outer whitespace, keep inner newlines).
    for key in (
        "origin",
        "origin_ref",
        "origin_detail",
        "language",
        "original_language",
        "original_content_hash",
        "original_content",
        "formatted_content",
    ):
        value = str(row.get(key, "") or "").strip()
        if value:
            out[key] = value
    review_status = str(row.get("review_status", "") or "").strip()
    if review_status:
        out["review_status"] = review_status
    public_readiness = str(row.get("public_readiness", "") or "").strip()
    if public_readiness:
        out["public_readiness"] = public_readiness
    for ref_key in ("source_refs", "project_refs", "experience_refs", "kanban_refs"):
        raw_refs = row.get(ref_key) or []
        if not isinstance(raw_refs, list):
            continue
        refs = [str(item).strip() for item in raw_refs if str(item).strip()]
        if refs:
            out[ref_key] = refs
    if bool(row.get("deprecated", False)):
        out["deprecated"] = True
    replaced_by = str(row.get("replaced_by", "") or "").strip()
    if replaced_by:
        out["replaced_by"] = replaced_by
    return out


def pool_index_by_id(entries: list[dict]) -> dict[str, int]:
    """Map evidence id -> list index. Pure."""
    return {
        str(row.get("id", "") or "").strip(): idx
        for idx, row in enumerate(entries)
        if str(row.get("id", "") or "").strip()
    }


def evidence_editor_host_available() -> bool:
    """True when the built React editor bundle is present."""
    return evidence_editor_component_available()


class EvidenceEditorHost:
    """Owns the evidence-editor event layer for one profile + key namespace."""

    def __init__(
        self,
        profile: str,
        *,
        key_prefix: str = "evidence_editor",
        ui: dict[str, str] | None = None,
    ) -> None:
        self.profile = profile
        self.key_prefix = key_prefix
        # Always source labels/messages from the evidence-review namespace so an
        # embedding page (e.g. Project Board) need not carry ee_* keys itself.
        self.ui = ui or evidence_review_ui()
        self.pdir = profile_dir(profile)
        self.pool_path = self.pdir / EVIDENCE_POOL_FILENAME
        self.tree_path = self.pdir / "skill-tree.yaml"
        self.skill_path = self.pdir / "SKILL.md"

    # -- session-key helpers -------------------------------------------
    def _k(self, name: str) -> str:
        return f"{self.key_prefix}_{name}_{self.profile}"

    def _dupes_state_key(self) -> str:
        return self._k("dupes")

    def _dismissed_state_key(self) -> str:
        return self._k("dupes_dismissed")

    def _done_preview_state_key(self) -> str:
        return self._k("done_preview")

    def _bulk_reformat_state_key(self) -> str:
        return self._k("bulk_reformat")

    def _event_seen(self, event_id: str) -> bool:
        """Dedup component events by id (frontend resends last value on rerun)."""
        if not event_id:
            return False
        key = self._k("event_id")
        if st.session_state.get(key) == event_id:
            return True
        st.session_state[key] = event_id
        return False

    # -- pool / tree IO ------------------------------------------------
    def _pool_entries(self) -> list[dict]:
        raw = load_evidence_pool_raw(self.profile) or {
            "profile": self.profile,
            "evidence_entries": [],
        }
        return [
            dict(item)
            for item in (raw.get("evidence_entries") or [])
            if isinstance(item, dict)
        ]

    def _active_source_index(self, entries: list[dict] | None = None) -> dict:
        return active_source_index(entries if entries is not None else self._pool_entries())

    def _save_pool(self, entries: list[dict], message: str) -> None:
        """Persist evidence-pool.yaml and refresh generated context blocks."""
        assert_files_current([self.pool_path, self.skill_path])
        pool_raw = load_evidence_pool_raw(self.profile) or {}
        pool_raw["profile"] = self.profile
        pool_raw["evidence_entries"] = entries
        save_evidence_pool(self.profile, pool_raw)
        if self.skill_path.exists():
            write_generated_blocks(self.pdir)
        refresh_file_snapshots([self.pool_path, self.skill_path])
        stash_git_backup_results()
        clear_web_cache()
        st.success(message)

    def _save_tree(self, tree: dict, message: str) -> None:
        """Persist skill-tree.yaml and refresh generated context blocks."""
        assert_files_current([self.tree_path, self.skill_path])
        save_skill_tree(self.profile, tree)
        if self.skill_path.exists():
            write_generated_blocks(self.pdir)
        refresh_file_snapshots([self.tree_path, self.skill_path])
        stash_git_backup_results()
        clear_web_cache()
        st.success(message)

    def _save_pool_and_tree(
        self,
        entries: list[dict],
        tree: dict | None,
        message: str,
    ) -> None:
        """Persist evidence-pool.yaml and, when changed, skill-tree.yaml."""
        paths = [self.pool_path, self.skill_path]
        if tree is not None:
            paths.insert(1, self.tree_path)
        assert_files_current(paths)
        pool_raw = load_evidence_pool_raw(self.profile) or {}
        pool_raw["profile"] = self.profile
        pool_raw["evidence_entries"] = entries
        save_evidence_pool(self.profile, pool_raw)
        if tree is not None:
            save_skill_tree(self.profile, tree)
        if self.skill_path.exists():
            write_generated_blocks(self.pdir)
        refresh_file_snapshots(paths)
        stash_git_backup_results()
        clear_web_cache()
        st.success(message)

    # -- Done task AI preview / accept --------------------------------
    def _lookup_tasks_by_id(self) -> dict[str, object]:
        """Return live+archived kanban tasks keyed by stable task id."""
        from nblane.core.kanban_archive import _all_lookup_tasks

        out: dict[str, object] = {}
        for task in _all_lookup_tasks(self.profile):
            tid = str(getattr(task, "id", "") or "").strip()
            if tid and tid not in out:
                out[tid] = task
        return out

    def _candidate_task_id(
        self,
        row: dict,
        selected_task_ids: set[str],
    ) -> str:
        """Infer which selected task an AI evidence candidate describes."""
        for ref in row.get("kanban_refs") or []:
            rid = kanban_ref_id(str(ref or ""))
            if rid in selected_task_ids:
                return rid
        origin_ref = str(row.get("origin_ref", "") or "").strip()
        rid = kanban_ref_id(origin_ref)
        if rid in selected_task_ids:
            return rid
        if origin_ref in selected_task_ids:
            return origin_ref
        # For a single-task preview, tolerate a model that omitted provenance;
        # host still overwrites canonical identity from the real task.
        if len(selected_task_ids) == 1:
            return next(iter(selected_task_ids))
        return ""

    def _normalize_done_ai_row(
        self,
        *,
        ai_row: dict,
        task: object,
        ordinal: int,
        existing_id: str = "",
    ) -> dict:
        """Host-normalize one AI Done evidence candidate."""
        task_id = str(getattr(task, "id", "") or "").strip()
        project_id = str(getattr(task, "project_id", "") or "").strip()
        original = render_kanban_task_source(task)
        strength = str(ai_row.get("strength", "") or "").strip()
        confidence = str(ai_row.get("confidence", "") or "").strip()
        title = str(ai_row.get("title", "") or "").strip()
        summary = str(ai_row.get("summary", "") or "").strip()
        formatted = str(ai_row.get("formatted_content", "") or "").strip()
        blockers: list[str] = []
        if not title:
            blockers.append("AI did not return title.")
        if not summary:
            blockers.append("AI did not return summary.")
        if not formatted:
            blockers.append("AI did not return formatted_content.")
        if strength not in EVIDENCE_STRENGTHS:
            blockers.append("AI did not return a valid strength.")
        if confidence not in EVIDENCE_CONFIDENCES:
            blockers.append("AI did not return a valid confidence.")
        row = {
            "type": str(ai_row.get("type", "") or "practice"),
            "title": title,
            "summary": summary,
            "formatted_content": formatted,
            "source_excerpt": str(ai_row.get("source_excerpt", "") or "").strip(),
            "date": str(getattr(task, "completed_on", "") or "").strip(),
            "origin": "kanban_task",
            "origin_ref": kanban_ref(task_id),
            "origin_detail": f"Done task {task_id}",
            "kanban_refs": [kanban_ref(task_id)],
            "project_refs": [project_id] if project_id else [],
            "original_content": original,
            "original_content_hash": content_hash(original),
            "original_language": detect_language(original),
            "language": llm_client.reply_language(),
            "strength": strength,
            "confidence": confidence,
            "review_status": "needs_review",
            "public_readiness": "private",
        }
        url = str(ai_row.get("url", "") or "").strip()
        if url:
            row["url"] = url
        return {
            "task_id": task_id,
            "task_title": str(getattr(task, "title", "") or ""),
            "ordinal": ordinal,
            "ai_id": str(ai_row.get("id", "") or "").strip(),
            "existing_id": existing_id,
            "row": row,
            "valid": not blockers,
            "blockers": blockers,
            "source_key": ["kanban_task", kanban_ref(task_id)],
        }

    def _done_preview_payload(
        self,
        *,
        selected_ids: list[str],
        rows: list[dict] | None = None,
        task_blockers: list[dict] | None = None,
        node_updates: list[dict] | None = None,
        warnings: list[str] | None = None,
        ai_error: str = "",
        blocking_errors: list[str] | None = None,
    ) -> dict:
        rows = list(rows or [])
        task_blockers = list(task_blockers or [])
        blocking_errors = list(blocking_errors or [])
        valid_count = sum(1 for row in rows if row.get("valid"))
        invalid_ai_count = sum(1 for row in rows if not row.get("valid"))
        return {
            "preview_id": uuid4().hex,
            "selected_task_ids": selected_ids,
            "rows": rows,
            "task_blockers": task_blockers,
            "node_updates": list(node_updates or []),
            "warnings": list(warnings or []),
            "ai_error": ai_error,
            "blocking_errors": blocking_errors,
            "valid_count": valid_count,
            "invalid_count": invalid_ai_count + len(task_blockers),
            # Accept as long as at least one valid row exists: a poorly-graded
            # row no longer blocks the good ones (apply writes only valid rows).
            # ai_error / blocking_errors still gate, since those signal AI
            # confusion (e.g. multiple rows for one task) that warrants a retry.
            "can_accept": bool(valid_count)
            and not ai_error
            and not blocking_errors,
        }

    def _prepare_done_task_evidence(self, task_ids: list | None) -> bool:
        """Run strict Done-task validation, then AI preview. Does not write."""
        ids = [str(t).strip() for t in (task_ids or []) if str(t).strip()]
        if not ids:
            st.info(self.ui.get("ee_done_tasks_none", "No Done tasks selected."))
            return False
        project_index = internal_project_goal_index(self.profile)
        tasks_by_id = self._lookup_tasks_by_id()
        entries = self._pool_entries()
        source_index = active_source_index(entries)
        valid_tasks: list[object] = []
        task_blockers: list[dict] = []
        seen: set[str] = set()
        for task_id in ids:
            if task_id in seen:
                continue
            seen.add(task_id)
            task = tasks_by_id.get(task_id)
            if task is None:
                task_blockers.append(
                    {
                        "task_id": task_id,
                        "title": task_id,
                        "blockers": [
                            "Task cannot be resolved from kanban.md or kanban-archive.md."
                        ],
                    }
                )
                continue
            blockers = done_task_evidence_blockers(
                task,
                project_index,
                resolvable=True,
            )
            source_rows = source_index.get(("kanban_task", kanban_ref(task_id))) or []
            if len(source_rows) > 1:
                blockers.append(
                    f"Multiple active evidence rows already use source kanban:{task_id}."
                )
            if blockers:
                task_blockers.append(
                    {
                        "task_id": task_id,
                        "title": str(getattr(task, "title", "") or task_id),
                        "blockers": blockers,
                    }
                )
            else:
                valid_tasks.append(task)
        if not valid_tasks:
            preview = self._done_preview_payload(
                selected_ids=ids,
                task_blockers=task_blockers,
                blocking_errors=[
                    "No selected Done tasks satisfy the evidence contract."
                ],
            )
            st.session_state[self._done_preview_state_key()] = preview
            st.warning("No selected Done tasks satisfy the evidence contract.")
            return True

        try:
            backend = kanban_ai_backend(self.profile)
        except Exception:
            backend = "llm"
        try:
            goal_context = current_goal_agent_context(self.profile)
        except Exception:
            goal_context = ""
        with st.spinner(
            self.ui.get("ee_done_ai_preview_running", "Preparing AI preview...")
        ):
            patch, err = ingest_kanban_done_json(
                self.profile,
                valid_tasks,
                goal_context=goal_context,
                ai_backend=backend,
            )
        if err or patch is None:
            msg = err or "AI preview failed."
            preview = self._done_preview_payload(
                selected_ids=ids,
                task_blockers=task_blockers,
                ai_error=msg,
                blocking_errors=[msg],
            )
            st.session_state[self._done_preview_state_key()] = preview
            st.error(msg)
            return True

        parsed = parse_ingest_patch(patch)
        selected_task_ids = {
            str(getattr(task, "id", "") or "").strip()
            for task in valid_tasks
        }
        task_by_id = {
            str(getattr(task, "id", "") or "").strip(): task
            for task in valid_tasks
        }
        grouped: dict[str, list[tuple[int, dict]]] = {tid: [] for tid in selected_task_ids}
        unmapped: list[dict] = []
        for ordinal, raw in enumerate(parsed.evidence_entries, start=1):
            tid = self._candidate_task_id(raw, selected_task_ids)
            if tid:
                grouped.setdefault(tid, []).append((ordinal, dict(raw)))
            else:
                unmapped.append(
                    {
                        "task_id": "",
                        "task_title": "",
                        "ordinal": ordinal,
                        "ai_id": str(raw.get("id", "") or "").strip(),
                        "row": dict(raw),
                        "valid": False,
                        "blockers": [
                            "AI row cannot be mapped to one selected task."
                        ],
                    }
                )
        rows: list[dict] = []
        blocking_errors: list[str] = []
        for tid, candidates in grouped.items():
            task = task_by_id[tid]
            source_rows = source_index.get(("kanban_task", kanban_ref(tid))) or []
            existing_id = (
                str(source_rows[0].get("id", "") or "").strip()
                if len(source_rows) == 1
                else ""
            )
            if len(candidates) > 1:
                blocking_errors.append(
                    f"AI returned multiple evidence rows for task {tid}."
                )
                for ordinal, raw in candidates:
                    item = self._normalize_done_ai_row(
                        ai_row=raw,
                        task=task,
                        ordinal=ordinal,
                        existing_id=existing_id,
                    )
                    item["valid"] = False
                    item.setdefault("blockers", []).append(
                        "AI returned multiple evidence rows for this task; retry AI."
                    )
                    rows.append(item)
                continue
            if not candidates:
                blocking_errors.append(
                    f"AI did not return evidence row for task {tid}."
                )
                rows.append(
                    {
                        "task_id": tid,
                        "task_title": str(getattr(task, "title", "") or tid),
                        "ordinal": 0,
                        "ai_id": "",
                        "existing_id": existing_id,
                        "row": {
                            "origin": "kanban_task",
                            "origin_ref": kanban_ref(tid),
                            "project_refs": [
                                str(getattr(task, "project_id", "") or "").strip()
                            ],
                            "date": str(getattr(task, "completed_on", "") or ""),
                        },
                        "valid": False,
                        "blockers": [
                            "AI did not return evidence row for this task."
                        ],
                    }
                )
                continue
            ordinal, raw = candidates[0]
            rows.append(
                self._normalize_done_ai_row(
                    ai_row=raw,
                    task=task,
                    ordinal=ordinal,
                    existing_id=existing_id,
                )
            )
        rows.extend(unmapped)
        preview = self._done_preview_payload(
            selected_ids=ids,
            rows=rows,
            task_blockers=task_blockers,
            node_updates=parsed.node_updates,
            blocking_errors=blocking_errors,
        )
        st.session_state[self._done_preview_state_key()] = preview
        if preview["can_accept"]:
            st.success(
                self.ui.get(
                    "ee_done_ai_preview_ready", "AI preview is ready."
                )
            )
        else:
            st.warning(
                self.ui.get(
                    "ee_done_ai_preview_blocked",
                    "AI preview needs attention before it can be accepted.",
                )
            )
        return True

    def _apply_node_updates_from_done_preview(
        self,
        *,
        tree: dict,
        node_updates: list[dict],
        ref_map: dict[str, str],
        final_ids: set[str],
    ) -> tuple[dict, bool, list[str]]:
        """Append AI-suggested skill refs after remapping preview refs."""
        warnings: list[str] = []
        schema_name = str(tree.get("schema", "") or "").strip()
        allowed_node_ids: set[str] = set()
        if schema_name:
            schema_raw = load_schema_raw(schema_name)
            if isinstance(schema_raw, dict):
                allowed_node_ids = set(schema_node_index(schema_raw))
        nodes = [
            dict(node)
            for node in (tree.get("nodes") or [])
            if isinstance(node, dict)
        ]
        by_id: dict[str, int] = {}
        for idx, node in enumerate(nodes):
            nid = str(node.get("id", "") or "").strip()
            if nid:
                by_id[nid] = idx
        changed = False
        for update in node_updates:
            if not isinstance(update, dict):
                continue
            nid = str(update.get("id", "") or "").strip()
            if not nid:
                warnings.append("Skipped node_update without id.")
                continue
            if allowed_node_ids and nid not in allowed_node_ids:
                warnings.append(f"Skipped unknown node id: {nid}.")
                continue
            if nid not in by_id:
                nodes.append({"id": nid, "status": "locked"})
                by_id[nid] = len(nodes) - 1
                changed = True
            node = nodes[by_id[nid]]
            cur_refs = [
                str(ref).strip()
                for ref in (node.get("evidence_refs") or [])
                if str(ref).strip()
            ]
            seen = set(cur_refs)
            raw_refs = update.get("evidence_refs") or []
            if isinstance(raw_refs, list):
                for raw_ref in raw_refs:
                    key = str(raw_ref or "").strip()
                    if not key:
                        continue
                    resolved = ref_map.get(key)
                    if not resolved:
                        ordinal = _ordinal_placeholder_to_id(key, ref_map)
                        resolved = ordinal or ""
                    if not resolved and key in final_ids:
                        resolved = key
                    if not resolved:
                        warnings.append(
                            f"{nid}: skipped unresolved evidence ref {key}."
                        )
                        continue
                    if resolved not in seen:
                        cur_refs.append(resolved)
                        seen.add(resolved)
                        changed = True
            if cur_refs:
                node["evidence_refs"] = cur_refs
            status = _llm_status_effective(str(update.get("status", "") or ""))
            if status is not None:
                prev = str(node.get("status", "locked") or "locked")
                if prev != "expert" and _status_rank(status) >= _status_rank(prev):
                    if node.get("status") != status:
                        node["status"] = status
                        changed = True
            nodes[by_id[nid]] = node
        if changed:
            tree["nodes"] = nodes
        return tree, changed, warnings

    def _apply_done_task_evidence(
        self,
        preview_id: str,
        mark_crystallized: bool,
    ) -> bool:
        """Accept a strict AI Done preview and write evidence + skill links."""
        preview = st.session_state.get(self._done_preview_state_key())
        if not isinstance(preview, dict):
            st.warning("No Done evidence preview is available.")
            return False
        if preview_id and preview.get("preview_id") != preview_id:
            st.warning("Done evidence preview is stale; run AI preview again.")
            return False
        if not preview.get("can_accept"):
            st.error("Done evidence preview has blockers; retry AI or fix tasks first.")
            return False
        valid_rows = [r for r in (preview.get("rows") or []) if r.get("valid")]
        if not valid_rows:
            st.warning("No valid Done evidence rows to accept.")
            return False

        entries = self._pool_entries()
        by_id = pool_index_by_id(entries)
        existing_ids = {
            str(r.get("id", "") or "").strip()
            for r in entries
            if str(r.get("id", "") or "").strip()
        }
        ref_map: dict[str, str] = {}
        final_ids: set[str] = set()
        changed = 0
        for item in valid_rows:
            row = dict(item.get("row") or {})
            key = evidence_source_key(row)
            if key is None:
                st.error("Accepted row is missing canonical source identity.")
                return False
            source_rows = active_source_index(entries).get(key) or []
            if len(source_rows) > 1:
                st.error(
                    f"Multiple active evidence rows already use source {key[0]}:{key[1]}."
                )
                return False
            if source_rows:
                existing_id = str(source_rows[0].get("id", "") or "").strip()
                idx = by_id.get(existing_id)
                if idx is None:
                    st.error(f"Existing evidence id {existing_id} is missing.")
                    return False
                merged = dict(entries[idx])
                merged.update(row)
                merged["id"] = existing_id
                entries[idx] = compact_evidence_row(merged)
                final_id = existing_id
            else:
                final_id = new_evidence_id(
                    str(row.get("title", "") or "task"), existing_ids
                )
                existing_ids.add(final_id)
                row["id"] = final_id
                entries.append(compact_evidence_row(row))
                by_id[final_id] = len(entries) - 1
            changed += 1
            final_ids.add(final_id)
            ordinal = int(item.get("ordinal") or 0)
            if ordinal > 0:
                ref_map[ordinal] = final_id
                ref_map[f"first_{ordinal}"] = final_id
                ref_map[f"ev_{ordinal}"] = final_id
            ai_id = str(item.get("ai_id", "") or "").strip()
            if ai_id:
                ref_map[ai_id] = final_id
            ref_map[final_id] = final_id

        tree = load_skill_tree_raw(self.profile)
        tree_changed = False
        warnings: list[str] = []
        if isinstance(tree, dict):
            tree, tree_changed, warnings = self._apply_node_updates_from_done_preview(
                tree=tree,
                node_updates=[
                    dict(u)
                    for u in (preview.get("node_updates") or [])
                    if isinstance(u, dict)
                ],
                ref_map=ref_map,
                final_ids=final_ids,
            )
        elif preview.get("node_updates"):
            warnings.append("skill-tree.yaml not found; skipped skill links.")
            tree = None

        self._save_pool_and_tree(
            [compact_evidence_row(r) for r in entries],
            tree if tree_changed else None,
            self.ui.get("ee_done_tasks_done", "Created/updated {n} from Done tasks.").format(
                n=changed
            ),
        )
        if mark_crystallized:
            self._crystallize_and_archive(
                [str(item.get("task_id", "") or "") for item in valid_rows]
            )
        for warning in warnings:
            st.warning(warning)
        st.session_state.pop(self._done_preview_state_key(), None)
        return True

    # -- handlers ------------------------------------------------------
    def _apply_save_evidence(self, eid: str, fields: dict) -> bool:
        entries = self._pool_entries()
        by_id = pool_index_by_id(entries)
        if eid not in by_id:
            return False
        row = dict(entries[by_id[eid]])
        for key in EDITOR_SAVE_FIELDS:
            if key not in fields:
                continue
            if key in EDITOR_SAVE_LIST_FIELDS:
                row[key] = [
                    str(r).strip()
                    for r in (fields.get(key) or [])
                    if str(r).strip()
                ]
            else:
                row[key] = str(fields.get(key, "") or "")
        project_validation = validate_internal_project_refs(
            row.get("project_refs"),
            internal_project_goal_index(self.profile),
        )
        blockers: list[str] = []
        if not str(row.get("date", "") or "").strip():
            blockers.append("Evidence requires a date.")
        if not str(row.get("original_content", "") or "").strip():
            blockers.append("Evidence requires original_content.")
        if not str(row.get("formatted_content", "") or "").strip():
            blockers.append("Evidence requires formatted_content.")
        blockers.extend(project_validation["blockers"])
        if blockers:
            for blocker in blockers:
                st.error(blocker)
            return False
        entries[by_id[eid]] = compact_evidence_row(row)
        self._save_pool(entries, self.ui.get("ee_saved", "Saved."))
        return True

    def _apply_add_evidence(self, fields: dict) -> bool:
        entries = self._pool_entries()
        existing = {
            str(r.get("id", "") or "").strip()
            for r in entries
            if str(r.get("id", "") or "").strip()
        }
        title = str(fields.get("title", "") or "").strip()
        if not title:
            return False
        refs = [
            str(r).strip()
            for r in (fields.get("project_refs") or [])
            if str(r).strip()
        ]
        project_validation = validate_internal_project_refs(
            refs,
            internal_project_goal_index(self.profile),
        )
        blockers: list[str] = []
        if not str(fields.get("date", "") or "").strip():
            blockers.append("Evidence requires a date.")
        if not str(fields.get("original_content", "") or "").strip():
            blockers.append("Evidence requires original_content.")
        if not str(fields.get("formatted_content", "") or "").strip():
            blockers.append("Evidence requires formatted_content.")
        blockers.extend(project_validation["blockers"])
        if blockers:
            for blocker in blockers:
                st.error(blocker)
            return False
        new_id = new_evidence_id(title, existing)
        origin = str(fields.get("origin", "") or "manual_daily")
        origin_ref = str(fields.get("origin_ref", "") or "").strip()
        if not origin_ref:
            origin_ref = f"manual:{new_id}" if origin == "manual_daily" else f"{origin}:{new_id}"
        row = {
            "id": new_id,
            "type": str(fields.get("type", "") or "practice"),
            "title": title,
            "origin": origin,
            "origin_ref": origin_ref,
            "review_status": "needs_review",
            "public_readiness": str(fields.get("public_readiness", "") or "private"),
            "project_refs": refs,
        }
        for key in (
            "summary",
            "original_content",
            "formatted_content",
            "origin_detail",
            "date",
        ):
            val = str(fields.get(key, "") or "").strip()
            if val:
                row[key] = val
        # Backfill v2 derived fields (language / hash) deterministically.
        row, _, _ = backfill_row(
            row, profile=self.profile, target_lang=llm_client.reply_language()
        )
        entries.append(compact_evidence_row(row))
        self._save_pool(entries, self.ui.get("ee_added", "Evidence added."))
        return True

    def _apply_deprecate(self, eid: str, replaced_by: str = "") -> bool:
        entries = self._pool_entries()
        by_id = pool_index_by_id(entries)
        if eid not in by_id:
            return False
        row = dict(entries[by_id[eid]])
        row["deprecated"] = True
        if replaced_by:
            row["replaced_by"] = replaced_by
        entries[by_id[eid]] = compact_evidence_row(row)
        self._save_pool(entries, self.ui.get("ee_deprecated", "Evidence deprecated."))
        return True

    def _apply_link_project(self, eid: str, project_refs: list) -> bool:
        return self._apply_save_evidence(eid, {"project_refs": project_refs})

    def _apply_link_skills(self, eid: str, skill_ids: list) -> bool:
        """Reconcile one evidence id across skill nodes (chip add/remove, no LLM)."""
        if not eid:
            return False
        tree = load_skill_tree_raw(self.profile)
        if not isinstance(tree, dict):
            st.error("skill-tree.yaml not found.")
            return False
        nodes = [
            dict(node)
            for node in (tree.get("nodes") or [])
            if isinstance(node, dict)
        ]
        cleaned = [str(s).strip() for s in (skill_ids or []) if str(s).strip()]
        tree["nodes"] = set_evidence_skill_refs(nodes, eid, cleaned)
        self._save_tree(
            tree, self.ui.get("ee_skill_linked", self.ui.get("link_done", "Linked."))
        )
        return True

    def _apply_link_skill(self, skill_id: str, evidence_ids: list) -> bool:
        """Attach several evidence rows to ONE skill node (append-only, no LLM).

        Skill-centric counterpart of :meth:`_apply_link_skills`: used by the
        skill-gap panel to bulk-attach evidence to a skill whose claimed status
        outruns its evidence. Reuses the pure ``link_skill_to_evidence_nodes``
        (append + de-dupe + create missing node as ``learning``).
        """
        skill = str(skill_id or "").strip()
        refs = [str(e).strip() for e in (evidence_ids or []) if str(e).strip()]
        if not skill or not refs:
            st.info(self.ui.get("ee_bulk_none", "No rows selected."))
            return False
        tree = load_skill_tree_raw(self.profile)
        if not isinstance(tree, dict):
            st.error("skill-tree.yaml not found.")
            return False
        nodes = [
            dict(node)
            for node in (tree.get("nodes") or [])
            if isinstance(node, dict)
        ]
        tree["nodes"] = link_skill_to_evidence_nodes(nodes, skill, refs)
        self._save_tree(
            tree, self.ui.get("ee_skill_linked", self.ui.get("link_done", "Linked."))
        )
        return True

    def _apply_migration(self, ids: list | None) -> bool:
        entries = self._pool_entries()
        result = migrate_evidence_pool(
            self.profile, entries=entries, target_lang=llm_client.reply_language()
        )
        if ids:
            id_set = set(ids)
            before_by_id = pool_index_by_id(entries)
            merged = list(entries)
            for item in result["per_row"]:
                rid = item["id"]
                if rid in id_set and rid in before_by_id and item["changed"]:
                    merged[before_by_id[rid]] = item["after"]
            new_entries = [compact_evidence_row(r) for r in merged]
        else:
            if result["changed_count"] == 0:
                st.info(self.ui.get("ee_migration_none", "Nothing to migrate."))
                return False
            new_entries = [compact_evidence_row(r) for r in result["entries"]]
        self._save_pool(
            new_entries,
            self.ui.get(
                "ee_migration_done", "Migration applied ({n} rows)."
            ).format(n=result["changed_count"]),
        )
        return True

    def _apply_refresh_crystallized(self, task_ids: list | None) -> bool:
        entries = self._pool_entries()
        result = refresh_from_crystallized_tasks(self.profile, entries=entries)
        proposals = result.get("proposals") or []
        if task_ids:
            proposals = [p for p in proposals if p.get("task_id") in set(task_ids)]
        if not proposals:
            st.info(
                self.ui.get(
                    "ee_crystallized_none", "No crystallized tasks to refresh."
                )
            )
            return False
        return self._apply_task_proposals(
            entries,
            proposals,
            self.ui.get("ee_crystallized_done", "Refreshed {n} from tasks."),
        )

    def _apply_done_tasks_to_evidence(
        self, task_ids: list | None, mark_crystallized: bool
    ) -> bool:
        """Deterministic Done-tasks -> evidence (incl. non-crystallized).

        No LLM and no skill ``node_updates``: it only creates/repairs v2
        evidence rows for the chosen Done tasks, then optionally marks those
        tasks ``crystallized`` so they leave the Done queue.
        """
        ids = [str(t).strip() for t in (task_ids or []) if str(t).strip()]
        entries = self._pool_entries()
        result = refresh_from_crystallized_tasks(
            self.profile,
            entries=entries,
            task_ids=ids or None,
            include_uncrystallized=not ids,
        )
        proposals = result.get("proposals") or []
        if not proposals:
            st.info(self.ui.get("ee_done_tasks_none", "No Done tasks to ingest."))
            return False
        project_index = internal_project_goal_index(self.profile)
        tasks_by_id = self._lookup_tasks_by_id()
        blockers: list[str] = []
        for prop in proposals:
            task_id = str(prop.get("task_id", "") or "").strip()
            task = tasks_by_id.get(task_id)
            if task is None:
                blockers.append(
                    f"{task_id}: Task cannot be resolved from kanban.md or kanban-archive.md."
                )
                continue
            for blocker in done_task_evidence_blockers(task, project_index):
                blockers.append(f"{task_id}: {blocker}")
        if blockers:
            for blocker in blockers:
                st.error(blocker)
            return False
        saved = self._apply_task_proposals(
            entries,
            proposals,
            self.ui.get("ee_done_tasks_done", "Created/updated {n} from Done tasks."),
        )
        if saved and mark_crystallized:
            self._crystallize_and_archive([p.get("task_id") for p in proposals])
        return saved

    def _fallback_formatted_content(self, prop: dict) -> str:
        lines: list[str] = []
        title = str(prop.get("title", "") or "").strip()
        if title:
            lines.append(f"# {title}")
        completed = str(prop.get("completed_on", "") or "").strip()
        if completed:
            lines.append(f"Completed: {completed}")
        original = str(prop.get("original_content", "") or "").strip()
        if original:
            lines.append("")
            lines.append("Preserved task source:")
            lines.append(original)
        return "\n".join(lines).strip()

    def _active_evidence_task_ids(self) -> set[str]:
        """Task ids referenced by active (non-deprecated) evidence provenance.

        Used to protect Done tasks from deletion when evidence still cites them
        (archive instead). Mirrors the page-level guard, moved into the host.
        """
        out: set[str] = set()
        for row in self._pool_entries():
            if bool(row.get("deprecated", False)):
                continue
            if str(row.get("origin", "") or "").strip() == "kanban_task":
                rid = kanban_ref_id(str(row.get("origin_ref", "") or ""))
                if rid:
                    out.add(rid)
            for ref in row.get("kanban_refs") or []:
                rid = kanban_ref_id(str(ref or ""))
                if rid:
                    out.add(rid)
        return out

    def _done_indexes_for_task_ids(
        self, task_ids: list
    ) -> tuple[dict, list[int], list[str]]:
        """Resolve task ids to Done-section indexes.

        Returns (sections, indexes, missing_ids). ``sections`` is the parsed
        kanban so callers can save it without re-parsing.
        """
        from nblane.core.io import KANBAN_DONE, parse_kanban

        wanted = [str(t).strip() for t in (task_ids or []) if str(t).strip()]
        sections = parse_kanban(self.profile)
        done_tasks = list(sections.get(KANBAN_DONE) or [])
        index_by_id: dict[str, int] = {}
        for index, task in enumerate(done_tasks):
            tid = str(getattr(task, "id", "") or "").strip()
            if tid and tid not in index_by_id:
                index_by_id[tid] = index
        indexes: list[int] = []
        missing: list[str] = []
        for tid in wanted:
            if tid in index_by_id:
                indexes.append(index_by_id[tid])
            else:
                missing.append(tid)
        return sections, sorted(set(indexes)), missing

    def _sync_board(self, sections: dict) -> None:
        """Best-effort project-board sync after a kanban mutation."""
        from nblane.core.project_board_sync import sync_project_board_from_kanban

        try:
            sync_project_board_from_kanban(self.profile, sections)
        except Exception:  # pragma: no cover - sync is best effort
            pass

    def _archive_done_tasks(
        self,
        task_ids: list,
        *,
        crystallize: bool,
        missing_ok: bool,
        success_message: str | None,
    ) -> bool:
        """Archive selected Done tasks into kanban-archive.md (mutates kanban).

        When ``crystallize`` is set, the archived copies are flagged
        ``crystallized`` first so the archive preserves that they were
        ingested. ``missing_ok`` lets evidence flows skip ids that already
        left the Done column (e.g. updated existing evidence) instead of
        erroring. Returns False on hard failure; archiving zero tasks when
        ``missing_ok`` is a no-op success.
        """
        from dataclasses import replace

        from nblane.core.io import KANBAN_DONE, archive_kanban_done_tasks

        sections, indexes, missing = self._done_indexes_for_task_ids(task_ids)
        if missing and not missing_ok:
            st.error(
                self.ui.get(
                    "ee_done_housekeeping_missing",
                    "Task(s) not in Done: {ids}.",
                ).format(ids=", ".join(missing))
            )
            return False
        if not indexes:
            if missing_ok:
                return True
            st.info(self.ui.get("ee_bulk_none", "No rows selected."))
            return False
        if crystallize:
            done_tasks = list(sections.get(KANBAN_DONE) or [])
            for index in indexes:
                if not getattr(done_tasks[index], "crystallized", False):
                    done_tasks[index] = replace(done_tasks[index], crystallized=True)
            sections[KANBAN_DONE] = done_tasks
        archive_path = self.pdir / "kanban-archive.md"
        kanban_path = self.pdir / "kanban.md"
        project_path = self.pdir / "project-board.yaml"
        assert_files_current([archive_path, kanban_path, project_path])
        updated = archive_kanban_done_tasks(self.profile, sections, indexes)
        self._sync_board(updated)
        refresh_file_snapshots([archive_path, kanban_path, project_path])
        stash_git_backup_results()
        clear_web_cache()
        if success_message:
            st.success(success_message.format(n=len(indexes)))
        return True

    def _apply_archive_done_tasks(self, task_ids: list) -> bool:
        """Housekeeping: archive selected Done tasks (no crystallize flag)."""
        return self._archive_done_tasks(
            task_ids,
            crystallize=False,
            missing_ok=False,
            success_message=self.ui.get(
                "done_housekeeping_archived", "Archived {n} task(s)."
            ),
        )

    def _crystallize_and_archive(self, task_ids: list) -> None:
        """Mark evidence-ingested Done tasks crystallized, then archive them.

        Called after evidence rows are saved, so the source tasks leave the
        active Done column. Best effort: a failed archive warns but never
        rolls back the evidence that was already written.
        """
        ids = [str(t).strip() for t in (task_ids or []) if str(t).strip()]
        if not ids:
            return
        try:
            archived = self._archive_done_tasks(
                ids,
                crystallize=True,
                missing_ok=True,
                success_message=None,
            )
        except Exception:  # pragma: no cover - archive is best effort post-save
            archived = False
        if not archived:
            st.warning(
                self.ui.get(
                    "ee_done_archive_after_save_failed",
                    "Evidence saved, but the source task(s) stayed on the board "
                    "— archive them from Housekeeping.",
                )
            )

    def _apply_delete_done_tasks(self, task_ids: list) -> bool:
        """Delete selected Done tasks, blocking any cited by active evidence."""
        from nblane.core.io import KANBAN_DONE, save_kanban

        sections, indexes, missing = self._done_indexes_for_task_ids(task_ids)
        if missing:
            st.error(
                self.ui.get(
                    "ee_done_housekeeping_missing",
                    "Task(s) not in Done: {ids}.",
                ).format(ids=", ".join(missing))
            )
            return False
        if not indexes:
            st.info(self.ui.get("ee_bulk_none", "No rows selected."))
            return False
        done_tasks = list(sections.get(KANBAN_DONE) or [])
        protected = self._active_evidence_task_ids()
        blocked = [
            str(getattr(done_tasks[i], "id", "") or "").strip()
            for i in indexes
            if str(getattr(done_tasks[i], "id", "") or "").strip() in protected
        ]
        if blocked:
            st.error(
                self.ui.get(
                    "done_housekeeping_delete_blocked_evidence",
                    "Delete blocked: active evidence references task(s): {ids}. Archive instead.",
                ).format(ids=", ".join(blocked))
            )
            return False
        kanban_path = self.pdir / "kanban.md"
        project_path = self.pdir / "project-board.yaml"
        assert_files_current([kanban_path, project_path])
        updated = {section: list(tasks) for section, tasks in sections.items()}
        remaining = list(done_tasks)
        for i in sorted(indexes, reverse=True):
            remaining.pop(i)
        updated[KANBAN_DONE] = remaining
        save_kanban(self.profile, updated)
        self._sync_board(updated)
        refresh_file_snapshots([kanban_path, project_path])
        stash_git_backup_results()
        clear_web_cache()
        st.success(
            self.ui.get(
                "done_housekeeping_deleted", "Deleted {n} task(s)."
            ).format(n=len(indexes))
        )
        return True

    def _apply_task_proposals(
        self, entries: list[dict], proposals: list[dict], done_message: str
    ) -> bool:
        """Apply deterministic task proposals (update-in-place or create new)."""
        by_id = pool_index_by_id(entries)
        existing = {
            str(r.get("id", "") or "").strip()
            for r in entries
            if str(r.get("id", "") or "").strip()
        }
        changed = 0
        for prop in proposals:
            if prop["kind"] == "update" and prop.get("evidence_id") in by_id:
                row = dict(entries[by_id[prop["evidence_id"]]])
                for key in (
                    "origin",
                    "origin_ref",
                    "original_content",
                    "original_content_hash",
                    "original_language",
                    "date",
                    "formatted_content",
                ):
                    value = prop.get(key)
                    if key == "date":
                        value = prop.get("completed_on")
                    elif key == "formatted_content":
                        value = self._fallback_formatted_content(prop)
                    if not str(row.get(key, "") or "").strip() and value:
                        row[key] = value
                if not row.get("kanban_refs"):
                    row["kanban_refs"] = prop.get("kanban_refs") or []
                if not row.get("project_refs") and prop.get("project_refs"):
                    row["project_refs"] = prop.get("project_refs") or []
                entries[by_id[prop["evidence_id"]]] = compact_evidence_row(row)
                changed += 1
            elif prop["kind"] == "new":
                new_id = new_evidence_id(prop.get("title", "") or "task", existing)
                existing.add(new_id)
                row = {
                    "id": new_id,
                    "type": "practice",
                    "title": prop.get("title", "") or new_id,
                    "origin": "kanban_task",
                    "origin_ref": prop.get("origin_ref", ""),
                    "kanban_refs": prop.get("kanban_refs") or [],
                    "original_content": prop.get("original_content", ""),
                    "original_content_hash": prop.get("original_content_hash", ""),
                    "original_language": prop.get("original_language", ""),
                    "date": prop.get("completed_on", ""),
                    "formatted_content": self._fallback_formatted_content(prop),
                    "language": llm_client.reply_language(),
                    "review_status": "needs_review",
                    "public_readiness": "private",
                }
                if prop.get("project_refs"):
                    row["project_refs"] = prop["project_refs"]
                entries.append(compact_evidence_row(row))
                changed += 1
        self._save_pool(entries, done_message.format(n=changed))
        return True

    def _output_source_maps(self) -> tuple[dict[str, dict], dict[str, object]]:
        from nblane.core import public_site

        try:
            output_rows = public_site.load_outputs(self.profile)
        except FileNotFoundError:
            output_rows = []
        try:
            blog_posts = public_site.load_blog_posts(
                self.profile,
                include_drafts=True,
                include_archived=True,
            )
        except FileNotFoundError:
            blog_posts = []
        outputs = {
            str(out.get("id", "") or "").strip(): out
            for out in output_rows
            if isinstance(out, dict) and str(out.get("id", "") or "").strip()
        }
        blogs = {
            str(getattr(post, "route", "") or "").strip(): post
            for post in blog_posts
            if str(getattr(post, "route", "") or "").strip()
        }
        return outputs, blogs

    def _infer_projects_from_related_evidence_in_entries(
        self,
        entries: list[dict],
        evidence_ids: object,
    ) -> list[str]:
        pool_by_id = {
            str(row.get("id", "") or "").strip(): row
            for row in entries
            if str(row.get("id", "") or "").strip()
        }
        out: list[str] = []
        raw_ids = evidence_ids if isinstance(evidence_ids, list) else []
        for eid in raw_ids:
            row = pool_by_id.get(str(eid).strip())
            if not row:
                continue
            for ref in row.get("project_refs") or []:
                clean = str(ref).strip()
                if clean and clean not in out:
                    out.append(clean)
        return out

    def _output_evidence_proposal(
        self,
        item: dict,
        *,
        entries: list[dict],
        existing_ids: set[str],
        outputs_by_id: dict[str, dict],
        blogs_by_route: dict[str, object],
    ) -> dict:
        source_kind = str(item.get("source_kind") or "output").strip() or "output"
        source_kind = "blog" if source_kind == "blog" else "output"
        output_id = str(item.get("output_id") or item.get("id") or "").strip()
        source_key = f"{source_kind}:{output_id}" if output_id else ""
        chosen_project_refs = [
            str(r).strip()
            for r in (item.get("project_refs") or [])
            if str(r).strip()
        ]
        if not output_id:
            return {
                "source_kind": source_kind,
                "output_id": output_id,
                "source_key": source_key,
                "row": None,
                "blockers": ["Output source has no id."],
            }

        row = None
        status = ""
        if source_kind == "blog":
            post = blogs_by_route.get(output_id)
            if post is None:
                return {
                    "source_kind": source_kind,
                    "output_id": output_id,
                    "source_key": source_key,
                    "row": None,
                    "blockers": [self.ui.get("ee_output_missing", "Output not found.")],
                }
            status = str(getattr(post, "status", "") or "").strip()
            if not chosen_project_refs:
                meta = getattr(post, "meta", {})
                chosen_project_refs = self._infer_projects_from_related_evidence_in_entries(
                    entries,
                    meta.get("related_evidence") if isinstance(meta, dict) else [],
                )
            row = evidence_row_from_blog_post(
                post,
                profile=self.profile,
                project_refs=chosen_project_refs,
                existing_ids=existing_ids,
                target_lang=llm_client.reply_language(),
            )
        else:
            output = outputs_by_id.get(output_id)
            if output is None:
                return {
                    "source_kind": source_kind,
                    "output_id": output_id,
                    "source_key": source_key,
                    "row": None,
                    "blockers": [self.ui.get("ee_output_missing", "Output not found.")],
                }
            status = str(output.get("status", "") or "").strip()
            if not chosen_project_refs:
                chosen_project_refs = [
                    str(r).strip()
                    for r in (output.get("project_refs") or [])
                    if str(r).strip()
                ]
            if not chosen_project_refs:
                chosen_project_refs = self._infer_projects_from_related_evidence_in_entries(
                    entries,
                    output.get("related_evidence"),
                )
            normalized_output = dict(output)
            normalized_output["project_refs"] = chosen_project_refs
            row = evidence_row_from_output(
                normalized_output,
                profile=self.profile,
                existing_ids=existing_ids,
                target_lang=llm_client.reply_language(),
            )

        project_validation = validate_internal_project_refs(
            row.get("project_refs") if row else [],
            internal_project_goal_index(self.profile),
        )
        blockers: list[str] = []
        if status != "published":
            blockers.append(
                f"Output source status is {status or 'draft'}; publish it before creating evidence."
            )
        if not str(row.get("date", "") or "").strip():
            blockers.append("Output source has no date; evidence requires a date.")
        if not str(row.get("original_content", "") or "").strip():
            blockers.append("Output source has no original_content.")
        if not str(row.get("formatted_content", "") or "").strip():
            blockers.append("Output source has no formatted_content.")
        blockers.extend(project_validation["blockers"])
        return {
            "source_kind": source_kind,
            "output_id": output_id,
            "source_key": source_key,
            "row": row,
            "blockers": blockers,
        }

    def _apply_bulk_create_from_output(
        self,
        items: list | None,
        *,
        success_message: str | None = None,
    ) -> bool:
        raw_items = items if isinstance(items, list) else []
        clean_items = [item for item in raw_items if isinstance(item, dict)]
        if not clean_items:
            st.info(self.ui.get("ee_bulk_none", "No rows selected."))
            return False

        entries = self._pool_entries()
        existing_ids = {
            str(r.get("id", "") or "").strip()
            for r in entries
            if str(r.get("id", "") or "").strip()
        }
        source_index = active_source_index(entries)
        outputs_by_id, blogs_by_route = self._output_source_maps()
        proposals: list[dict] = []
        selected_keys: set[str] = set()
        duplicate_keys: set[str] = set()
        for item in clean_items:
            proposal = self._output_evidence_proposal(
                item,
                entries=entries,
                existing_ids=existing_ids,
                outputs_by_id=outputs_by_id,
                blogs_by_route=blogs_by_route,
            )
            source_key = str(proposal.get("source_key") or "").strip()
            if source_key:
                if source_key in selected_keys:
                    duplicate_keys.add(source_key)
                selected_keys.add(source_key)
            proposals.append(proposal)
            source_rows = source_index.get(("output", source_key)) or []
            if len(source_rows) == 0 and isinstance(proposal.get("row"), dict):
                rid = str(proposal["row"].get("id", "") or "").strip()
                if rid:
                    existing_ids.add(rid)

        all_blockers: list[str] = []
        for proposal in proposals:
            label = str(proposal.get("source_key") or proposal.get("output_id") or "")
            for blocker in proposal.get("blockers") or []:
                all_blockers.append(f"{label}: {blocker}" if label else str(blocker))
            source_key = str(proposal.get("source_key") or "").strip()
            if source_key in duplicate_keys:
                all_blockers.append(f"{source_key}: selected more than once.")
            source_rows = source_index.get(("output", source_key)) or []
            if len(source_rows) > 1:
                all_blockers.append(
                    f"{source_key}: multiple active evidence rows already use this source."
                )
        if all_blockers:
            for blocker in all_blockers:
                st.error(blocker)
            return False

        by_id = pool_index_by_id(entries)
        changed = 0
        for proposal in proposals:
            row = proposal.get("row")
            source_key = str(proposal.get("source_key") or "").strip()
            if not isinstance(row, dict) or not source_key:
                continue
            source_rows = source_index.get(("output", source_key)) or []
            if source_rows:
                # Multiple active rows were blocked above; a single row updates in place.
                eid = str(source_rows[0].get("id", "") or "").strip()
                idx = by_id.get(eid)
                if idx is None:
                    st.error(f"{source_key}: existing evidence row is missing.")
                    return False
                merged = dict(entries[idx])
                merged.update(row)
                merged["id"] = eid
                entries[idx] = compact_evidence_row(merged)
            else:
                entries.append(compact_evidence_row(row))
                rid = str(row.get("id", "") or "").strip()
                if rid:
                    by_id[rid] = len(entries) - 1
            changed += 1
        self._save_pool(
            entries,
            success_message
            or self.ui.get(
                "ee_output_bulk_created",
                "Created/updated {n} evidence row(s) from outputs.",
            ).format(n=changed),
        )
        return True

    def _infer_projects_from_related_evidence(self, evidence_ids: object) -> list[str]:
        return self._infer_projects_from_related_evidence_in_entries(
            self._pool_entries(),
            evidence_ids,
        )

    def _clean_output_candidate_items(self, items: object) -> list[dict[str, str]]:
        raw_items = items if isinstance(items, list) else []
        out: list[dict[str, str]] = []
        seen: set[str] = set()
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            source_kind = str(item.get("source_kind") or "output").strip()
            source_kind = "blog" if source_kind == "blog" else "output"
            output_id = str(item.get("output_id") or item.get("id") or "").strip()
            if not output_id:
                continue
            source_key = f"{source_kind}:{output_id}"
            if source_key in seen:
                continue
            seen.add(source_key)
            out.append(
                {
                    "source_key": source_key,
                    "source_kind": source_kind,
                    "output_id": output_id,
                }
            )
        return out

    def _apply_ignore_output_candidates(
        self,
        items: object,
        reason: str = "not_evidence",
    ) -> bool:
        clean_items = self._clean_output_candidate_items(items)
        if not clean_items:
            st.info(self.ui.get("ee_bulk_none", "No rows selected."))
            return False
        prefs = load_web_preferences(self.profile)
        evidence_review = (
            prefs.get("evidence_review")
            if isinstance(prefs.get("evidence_review"), dict)
            else {}
        )
        existing = [
            dict(item)
            for item in (evidence_review.get("ignored_output_candidates") or [])
            if isinstance(item, dict)
        ]
        by_key = {
            str(item.get("source_key") or "").strip(): item
            for item in existing
            if str(item.get("source_key") or "").strip()
        }
        ignored_at = datetime.now(timezone.utc).isoformat()
        clean_reason = str(reason or "not_evidence").strip() or "not_evidence"
        for item in clean_items:
            by_key[item["source_key"]] = {
                **item,
                "reason": clean_reason,
                "ignored_at": ignored_at,
            }
        changed = update_web_preferences(
            self.profile,
            {
                "evidence_review": {
                    "ignored_output_candidates": list(by_key.values()),
                }
            },
        )
        clear_web_cache()
        if changed:
            st.success(
                self.ui.get(
                    "ee_output_ignored", "Skipped {n} output candidate(s)."
                ).format(n=len(clean_items))
            )
        else:
            st.info(self.ui.get("pool_no_changes", "No changes"))
        return True

    def _apply_restore_output_candidates(self, items: object) -> bool:
        clean_items = self._clean_output_candidate_items(items)
        if not clean_items:
            st.info(self.ui.get("ee_bulk_none", "No rows selected."))
            return False
        restore_keys = {item["source_key"] for item in clean_items}
        prefs = load_web_preferences(self.profile)
        evidence_review = (
            prefs.get("evidence_review")
            if isinstance(prefs.get("evidence_review"), dict)
            else {}
        )
        existing = [
            dict(item)
            for item in (evidence_review.get("ignored_output_candidates") or [])
            if isinstance(item, dict)
        ]
        kept = [
            item
            for item in existing
            if str(item.get("source_key") or "").strip() not in restore_keys
        ]
        changed = update_web_preferences(
            self.profile,
            {"evidence_review": {"ignored_output_candidates": kept}},
        )
        clear_web_cache()
        if changed:
            st.success(
                self.ui.get(
                    "ee_output_restored", "Restored {n} output candidate(s)."
                ).format(n=len(clean_items))
            )
        else:
            st.info(self.ui.get("pool_no_changes", "No changes"))
        return True

    def _apply_backfill_project_refs(self, ids: list | None) -> bool:
        review = build_evidence_review(self.profile)
        candidates = [
            item
            for item in (review.get("project_ref_candidates") or [])
            if isinstance(item, dict) and bool(item.get("can_apply"))
        ]
        if not candidates:
            st.info(self.ui.get("refs_project_backfill_no_auto", "No auto candidates."))
            return False
        chosen = ids or [str(c.get("id", "") or "") for c in candidates]
        entries = self._pool_entries()
        entries, changed = apply_project_ref_inferences(entries, candidates, chosen)
        if not changed:
            st.info(self.ui.get("pool_no_changes", "No changes."))
            return False
        self._save_pool(
            entries,
            self.ui.get("refs_project_backfill_saved", "Linked {n}.").format(n=changed),
        )
        return True

    def _apply_request_ai_reformat(self, eid: str) -> bool:
        row = next((r for r in self._pool_entries() if str(r.get("id")) == eid), None)
        if row is None:
            return False
        proposal, err = reformat_evidence(
            self.profile, row, target_lang=llm_client.reply_language()
        )
        if err or not proposal:
            st.warning(err or self.ui.get("ee_reformat_failed", "Reformat failed."))
            return False
        st.session_state[self._k("reformat")] = {
            "id": eid,
            "fields": proposal,
        }
        return True

    def _apply_confirm_ai_reformat(self, eid: str, fields: dict) -> bool:
        ok = self._apply_save_evidence(eid, fields)
        st.session_state.pop(self._k("reformat"), None)
        return ok

    def _apply_bulk_request_ai_reformat(self, ids: list) -> bool:
        target = [str(i).strip() for i in (ids or []) if str(i).strip()]
        if not target:
            st.info(self.ui.get("ee_bulk_none", "No rows selected."))
            return False
        rows = {
            str(row.get("id", "") or "").strip(): row
            for row in self._pool_entries()
            if str(row.get("id", "") or "").strip()
        }
        items: list[dict] = []
        with st.spinner(
            self.ui.get("ee_bulk_reformat_running", "Preparing AI reformat preview...")
        ):
            for eid in target:
                row = rows.get(eid)
                if row is None:
                    items.append({"id": eid, "error": "Evidence row not found."})
                    continue
                proposal, err = reformat_evidence(
                    self.profile,
                    row,
                    target_lang=llm_client.reply_language(),
                )
                if err or not proposal:
                    items.append({"id": eid, "title": row.get("title", ""), "error": err or "Reformat failed."})
                    continue
                fields = {
                    key: str(proposal.get(key, "") or "")
                    for key in ("title", "summary", "formatted_content")
                    if str(proposal.get(key, "") or "").strip()
                }
                fields["language"] = llm_client.reply_language()
                items.append(
                    {
                        "id": eid,
                        "title": str(row.get("title", "") or eid),
                        "fields": fields,
                    }
                )
        preview = {
            "preview_id": uuid4().hex,
            "items": items,
            "valid_count": sum(1 for item in items if item.get("fields")),
        }
        st.session_state[self._bulk_reformat_state_key()] = preview
        if preview["valid_count"]:
            st.success(
                self.ui.get("ee_bulk_reformat_ready", "Bulk reformat preview is ready.")
            )
        else:
            st.warning(self.ui.get("ee_reformat_failed", "Reformat failed."))
        return True

    def _apply_bulk_confirm_ai_reformat(self, preview_id: str) -> bool:
        preview = st.session_state.get(self._bulk_reformat_state_key())
        if not isinstance(preview, dict):
            st.warning("No bulk reformat preview is available.")
            return False
        if preview_id and preview.get("preview_id") != preview_id:
            st.warning("Bulk reformat preview is stale; run it again.")
            return False
        entries = self._pool_entries()
        by_id = pool_index_by_id(entries)
        changed = 0
        for item in preview.get("items") or []:
            if not isinstance(item, dict) or not item.get("fields"):
                continue
            eid = str(item.get("id", "") or "").strip()
            idx = by_id.get(eid)
            if idx is None:
                continue
            row = dict(entries[idx])
            fields = item.get("fields") if isinstance(item.get("fields"), dict) else {}
            for key in ("title", "summary", "formatted_content", "language"):
                value = str(fields.get(key, "") or "").strip()
                if value:
                    row[key] = value
            entries[idx] = compact_evidence_row(row)
            changed += 1
        if not changed:
            st.info(self.ui.get("pool_no_changes", "No changes."))
            return False
        self._save_pool(
            entries,
            self.ui.get("ee_bulk_done", "Updated {n} rows.").format(n=changed),
        )
        st.session_state.pop(self._bulk_reformat_state_key(), None)
        return True

    def _apply_suggest_skills(self, eid: str) -> bool:
        """LLM skill recall for one row: route its text to candidate nodes.

        Rule suggestions already ship in the payload; this augments them with
        the LLM router (slow, explicit). Stashes results for the next render;
        never writes skill links (the human still confirms via chips).
        """
        from nblane.core import gap as gap_mod
        from nblane.core.evidence_review import _row_match_text

        row = next((r for r in self._pool_entries() if str(r.get("id")) == eid), None)
        if row is None:
            return False
        text = _row_match_text(row)
        if not text.strip():
            st.info(self.ui.get("ee_skill_suggest_empty", "No text to match."))
            return False
        with st.spinner(self.ui.get("ee_skill_suggest_running", "Asking AI…")):
            try:
                result = gap_mod.analyze(
                    self.profile,
                    text,
                    use_rule_match=True,
                    use_llm_router=True,
                    source_kind="evidence",
                    source_id=eid,
                )
            except Exception as exc:  # noqa: BLE001 - surface, never crash editor
                st.warning(str(exc))
                return False
        if getattr(result, "error", ""):
            st.warning(result.error)
            return False
        suggestions = [
            {
                "id": str(m.get("id", "")),
                "label": str(m.get("label", "") or m.get("id", "")),
                "score": int(m.get("score", 0) or 0),
                "source": str(m.get("source", "") or "rule"),
            }
            for m in (result.top_matches or [])
            if str(m.get("id", "")).strip()
        ]
        st.session_state[self._k("skill_suggest")] = {
            "id": eid,
            "suggestions": suggestions,
        }
        return True

    def _apply_create_project_from_evidence(self, suggestion: dict) -> bool:
        """Stash the suggestion for Project Board create-form prefill, then jump."""
        st.session_state["project_board_create_prefill"] = {
            "title": str(suggestion.get("suggested_title", "") or ""),
            "id": str(suggestion.get("suggested_id", "") or "").replace("project:", ""),
            "kind": str(suggestion.get("kind", "") or "work"),
            "visibility": str(suggestion.get("visibility", "") or "private"),
            "summary": str(suggestion.get("summary", "") or ""),
            "evidence_ids": list(suggestion.get("evidence_ids") or []),
        }
        st.switch_page("pages/11_Project_Board.py")
        return False

    def _apply_suggest_duplicates(self, focus_id: str, use_ai: bool) -> bool:
        """Detect duplicate candidates and stash them for the next render.

        Deterministic always; AI clustering only when use_ai (explicit, slow).
        Never writes. Returns True so the fragment reruns and surfaces the panel.
        """
        entries = self._pool_entries()
        focus = focus_id or None
        candidates = find_duplicate_candidates(entries, focus_id=focus)
        if use_ai:
            with st.spinner(self.ui.get("ee_dup_ai_running", "Scanning for duplicates…")):
                ai_pairs, err = suggest_duplicates_ai(entries)
            if err:
                st.warning(err)
            else:
                # Merge AI pairs in, de-duping by unordered id pair.
                seen = {tuple(sorted((c["a"], c["b"]))) for c in candidates}
                for p in ai_pairs:
                    key = tuple(sorted((p["a"], p["b"])))
                    if key not in seen:
                        seen.add(key)
                        candidates.append(p)
        # Drop pairs the user dismissed this session.
        dismissed = st.session_state.get(self._dismissed_state_key()) or set()
        candidates = [
            c
            for c in candidates
            if tuple(sorted((c["a"], c["b"]))) not in dismissed
        ]
        st.session_state[self._dupes_state_key()] = candidates
        if not candidates:
            st.info(self.ui.get("ee_dup_none", "No duplicate candidates found."))
        return True

    def _apply_dismiss_duplicate(self, a: str, b: str) -> None:
        if not a or not b:
            return
        key = tuple(sorted((a, b)))
        dismissed = set(st.session_state.get(self._dismissed_state_key()) or set())
        dismissed.add(key)
        st.session_state[self._dismissed_state_key()] = dismissed
        # Also drop it from the live candidate list.
        cands = st.session_state.get(self._dupes_state_key()) or []
        st.session_state[self._dupes_state_key()] = [
            c for c in cands if tuple(sorted((c["a"], c["b"]))) != key
        ]

    def _apply_merge_or_deprecate_event(
        self, keep_id: str, other_id: str, merge_fields: object
    ) -> bool:
        if not keep_id or not other_id:
            return False
        fields = (
            [str(f) for f in merge_fields]
            if isinstance(merge_fields, list)
            else None
        )
        entries = self._pool_entries()
        new_entries, changed = apply_merge_or_deprecate(
            entries, keep_id=keep_id, other_id=other_id, merge_fields=fields
        )
        if not changed:
            st.info(self.ui.get("pool_no_changes", "No changes."))
            return False
        new_entries = [compact_evidence_row(r) for r in new_entries]
        # Drop the resolved pair from the candidate list.
        key = tuple(sorted((keep_id, other_id)))
        cands = st.session_state.get(self._dupes_state_key()) or []
        st.session_state[self._dupes_state_key()] = [
            c for c in cands if tuple(sorted((c["a"], c["b"]))) != key
        ]
        self._save_pool(
            new_entries,
            self.ui.get("ee_dup_resolved", "Resolved duplicate (kept {k}).").format(
                k=keep_id
            ),
        )
        return True

    def _apply_bulk(
        self, ids: list, field: str, value: str, action: str, payload: dict
    ) -> bool:
        """Apply one bulk action across many evidence ids (one save).

        Two shapes are supported:
          * ``field``/``value`` — set a whitelisted pool field (review_status,
            public_readiness, strength, confidence) on every row.
          * ``action`` — ``deprecate`` / ``link_project`` / ``link_skills``.
        """
        target = [str(i).strip() for i in (ids or []) if str(i).strip()]
        if not target:
            st.info(self.ui.get("ee_bulk_none", "No rows selected."))
            return False
        act = str(action or "").strip()

        if act == "link_skills":
            skill_ids = [
                str(s).strip()
                for s in (payload.get("skill_ids") or [])
                if str(s).strip()
            ]
            tree = load_skill_tree_raw(self.profile)
            if not isinstance(tree, dict):
                st.error("skill-tree.yaml not found.")
                return False
            nodes = [
                dict(node)
                for node in (tree.get("nodes") or [])
                if isinstance(node, dict)
            ]
            for eid in target:
                nodes = set_evidence_skill_refs(nodes, eid, skill_ids)
            tree["nodes"] = nodes
            self._save_tree(
                tree,
                self.ui.get("ee_bulk_done", "Updated {n} rows.").format(
                    n=len(target)
                ),
            )
            return True

        entries = self._pool_entries()
        target_set = set(target)

        if act == "deprecate":
            changed = 0
            for idx, row in enumerate(entries):
                if str(row.get("id", "") or "").strip() in target_set:
                    r = dict(row)
                    r["deprecated"] = True
                    entries[idx] = compact_evidence_row(r)
                    changed += 1
            if not changed:
                return False
            self._save_pool(
                entries,
                self.ui.get("ee_bulk_done", "Updated {n} rows.").format(n=changed),
            )
            return True

        if act == "link_project":
            refs = [
                str(r).strip()
                for r in (payload.get("project_refs") or [])
                if str(r).strip()
            ]
            changed = 0
            for idx, row in enumerate(entries):
                if str(row.get("id", "") or "").strip() in target_set:
                    r = dict(row)
                    r["project_refs"] = refs
                    entries[idx] = compact_evidence_row(r)
                    changed += 1
            if not changed:
                return False
            self._save_pool(
                entries,
                self.ui.get("ee_bulk_done", "Updated {n} rows.").format(n=changed),
            )
            return True

        # Default: set one whitelisted scalar field via the validated helper.
        entries, changed = bulk_set_pool_field(
            entries, target, str(field or ""), str(value or "")
        )
        if not changed:
            st.info(self.ui.get("pool_no_changes", "No changes."))
            return False
        entries = [compact_evidence_row(r) for r in entries]
        self._save_pool(
            entries,
            self.ui.get("ee_bulk_done", "Updated {n} rows.").format(n=changed),
        )
        return True

    # -- dispatch ------------------------------------------------------
    def handle_event(self, event: dict | None) -> bool:
        """Apply one event from the React evidence editor. Returns True if saved."""
        if not isinstance(event, dict):
            return False
        action = str(event.get("action") or "")
        if not action or self._event_seen(str(event.get("event_id") or "")):
            return False
        payload = (
            event.get("payload") if isinstance(event.get("payload"), dict) else {}
        )
        fields = (
            payload.get("fields") if isinstance(payload.get("fields"), dict) else {}
        )
        eid = str(payload.get("id") or "")

        # Remember the row the user was acting on so the detail pane stays open on
        # the same evidence after the fragment reruns (avoids losing context).
        if eid:
            st.session_state[self._k("last_id")] = eid

        if action == "save_evidence":
            return self._apply_save_evidence(eid, fields)
        if action == "add_evidence":
            return self._apply_add_evidence(fields)
        if action == "deprecate_evidence":
            return self._apply_deprecate(eid, str(payload.get("replaced_by") or ""))
        if action == "link_project":
            return self._apply_link_project(eid, payload.get("project_refs") or [])
        if action == "link_skills":
            return self._apply_link_skills(eid, payload.get("skill_ids") or [])
        if action == "link_skill":
            return self._apply_link_skill(
                str(payload.get("skill_id") or ""),
                payload.get("evidence_ids") or [],
            )
        if action == "suggest_skills":
            return self._apply_suggest_skills(eid)
        if action == "backfill_project_refs":
            return self._apply_backfill_project_refs(payload.get("ids"))
        if action == "apply_migration":
            return self._apply_migration(payload.get("ids"))
        if action == "refresh_from_crystallized_tasks":
            return self._apply_refresh_crystallized(payload.get("task_ids"))
        if action == "prepare_done_task_evidence":
            return self._prepare_done_task_evidence(payload.get("task_ids"))
        if action == "apply_done_task_evidence":
            return self._apply_done_task_evidence(
                str(payload.get("preview_id") or ""),
                bool(payload.get("mark_crystallized")),
            )
        if action == "done_tasks_to_evidence":
            return self._apply_done_tasks_to_evidence(
                payload.get("task_ids"),
                bool(payload.get("mark_crystallized")),
            )
        if action == "archive_done_tasks":
            return self._apply_archive_done_tasks(payload.get("task_ids") or [])
        if action == "delete_done_tasks":
            return self._apply_delete_done_tasks(payload.get("task_ids") or [])
        if action == "bulk_apply":
            return self._apply_bulk(
                payload.get("ids") or [],
                str(payload.get("field") or ""),
                str(payload.get("value") or ""),
                str(payload.get("bulk_action") or payload.get("op") or ""),
                payload,
            )
        if action == "request_ai_reformat":
            return self._apply_request_ai_reformat(eid)
        if action == "confirm_ai_reformat":
            return self._apply_confirm_ai_reformat(eid, fields)
        if action == "bulk_request_ai_reformat":
            return self._apply_bulk_request_ai_reformat(payload.get("ids") or [])
        if action == "bulk_confirm_ai_reformat":
            return self._apply_bulk_confirm_ai_reformat(
                str(payload.get("preview_id") or "")
            )
        if action == "bulk_create_from_output":
            return self._apply_bulk_create_from_output(payload.get("items") or [])
        if action == "ignore_output_candidates":
            return self._apply_ignore_output_candidates(
                payload.get("items") or [],
                str(payload.get("reason") or "not_evidence"),
            )
        if action == "restore_output_candidates":
            return self._apply_restore_output_candidates(payload.get("items") or [])
        if action == "create_project_from_evidence":
            sug = (
                payload.get("suggestion")
                if isinstance(payload.get("suggestion"), dict)
                else {}
            )
            return self._apply_create_project_from_evidence(sug)
        if action == "suggest_duplicates":
            return self._apply_suggest_duplicates(eid, bool(payload.get("ai")))
        if action == "dismiss_duplicate":
            self._apply_dismiss_duplicate(eid, str(payload.get("other") or ""))
            return True
        if action == "merge_or_deprecate":
            return self._apply_merge_or_deprecate_event(
                str(payload.get("keep") or payload.get("id") or ""),
                str(payload.get("other") or payload.get("replaced_by") or ""),
                payload.get("merge_fields"),
            )
        return False

    # -- labels / render ----------------------------------------------
    def labels(self) -> dict[str, str]:
        """Pass-through i18n labels the React component reads by key."""
        keys = [
            k
            for k in self.ui.keys()
            if k.startswith("ee_")
            or k.startswith("field_")
            or k.startswith("origin_")
            or k.startswith("section_")
        ]
        return {k: self.ui[k] for k in keys}

    def render(self) -> None:
        """Render the React editor, persist any event, rerun in-fragment."""
        payload = build_evidence_editor_payload(self.profile)
        preview = st.session_state.get(self._k("reformat"))
        if preview:
            payload["reformat_preview"] = preview
        skill_suggest = st.session_state.get(self._k("skill_suggest"))
        if skill_suggest:
            payload["skill_suggestion_llm"] = skill_suggest
        dupes = st.session_state.get(self._dupes_state_key())
        if dupes is not None:
            payload["duplicate_candidates"] = dupes
        done_preview = st.session_state.get(self._done_preview_state_key())
        if done_preview:
            payload["done_preview"] = done_preview
        bulk_reformat = st.session_state.get(self._bulk_reformat_state_key())
        if bulk_reformat:
            payload["bulk_reformat_preview"] = bulk_reformat
        event = st_evidence_editor(
            payload=payload,
            labels=self.labels(),
            settings={
                "lang": llm_client.ui_language(),
                "target_language": llm_client.reply_language(),
                # Echo the last-touched row so the React side reselects it after a
                # rerun re-mounts the iframe.
                "last_selected_id": st.session_state.get(self._k("last_id"), ""),
            },
            key=f"{self.key_prefix}_{self.profile}",
        )
        if self.handle_event(event):
            st.rerun(scope="fragment")
