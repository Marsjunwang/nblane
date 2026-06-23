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

import streamlit as st

from nblane.core import llm as llm_client
from nblane.core.evidence_dedup import (
    apply_merge_or_deprecate,
    find_duplicate_candidates,
    suggest_duplicates_ai,
)
from nblane.core.evidence_from_output import evidence_row_from_output
from nblane.core.evidence_migrate import (
    migrate_evidence_pool,
    refresh_from_crystallized_tasks,
)
from nblane.core.evidence_pool_id import new_evidence_id
from nblane.core.evidence_review import (
    apply_project_ref_inferences,
    build_evidence_editor_payload,
    build_evidence_review,
    bulk_set_pool_field,
    set_evidence_skill_refs,
)
from nblane.core.evidence_migrate import backfill_row
from nblane.core.io import (
    EVIDENCE_POOL_FILENAME,
    profile_dir,
    save_evidence_pool,
    save_skill_tree,
)
from nblane.core.profile_ingest_llm import reformat_evidence
from nblane.core.sync import write_generated_blocks
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
            if key == "project_refs":
                row[key] = [
                    str(r).strip()
                    for r in (fields.get(key) or [])
                    if str(r).strip()
                ]
            else:
                row[key] = str(fields.get(key, "") or "")
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
        new_id = new_evidence_id(title, existing)
        row = {
            "id": new_id,
            "type": str(fields.get("type", "") or "practice"),
            "title": title,
            "origin": str(fields.get("origin", "") or "manual_daily"),
            "review_status": "needs_review",
            "public_readiness": str(fields.get("public_readiness", "") or "private"),
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
        refs = [
            str(r).strip()
            for r in (fields.get("project_refs") or [])
            if str(r).strip()
        ]
        if refs:
            row["project_refs"] = refs
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
        saved = self._apply_task_proposals(
            entries,
            proposals,
            self.ui.get("ee_done_tasks_done", "Created/updated {n} from Done tasks."),
        )
        if saved and mark_crystallized:
            self._mark_tasks_crystallized([p.get("task_id") for p in proposals])
        return saved

    def _mark_tasks_crystallized(self, task_ids: list) -> None:
        """Set ``crystallized`` on the given Done tasks (best effort)."""
        from dataclasses import replace

        from nblane.core.io import KANBAN_DONE, parse_kanban, save_kanban

        wanted = {str(t).strip() for t in (task_ids or []) if str(t).strip()}
        if not wanted:
            return
        kanban_path = self.pdir / "kanban.md"
        sections = parse_kanban(self.profile)
        done_tasks = sections.get(KANBAN_DONE) or []
        changed = False
        for index, task in enumerate(done_tasks):
            tid = str(getattr(task, "id", "") or "").strip()
            if tid in wanted and not getattr(task, "crystallized", False):
                done_tasks[index] = replace(task, crystallized=True)
                changed = True
        if not changed:
            return
        sections[KANBAN_DONE] = done_tasks
        assert_files_current([kanban_path])
        save_kanban(self.profile, sections)
        refresh_file_snapshots([kanban_path])
        stash_git_backup_results()
        clear_web_cache()

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
                ):
                    if not str(row.get(key, "") or "").strip() and prop.get(key):
                        row[key] = prop[key]
                if not row.get("kanban_refs"):
                    row["kanban_refs"] = prop.get("kanban_refs") or []
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

    def _apply_create_from_output(self, output_id: str) -> bool:
        import yaml as _yaml

        entries = self._pool_entries()
        existing = {
            str(r.get("id", "") or "").strip()
            for r in entries
            if str(r.get("id", "") or "").strip()
        }
        out_path = self.pdir / "outputs.yaml"
        output = None
        if out_path.exists():
            data = _yaml.safe_load(out_path.read_text(encoding="utf-8")) or {}
            for o in data.get("outputs") or []:
                if isinstance(o, dict) and str(o.get("id", "")) == output_id:
                    output = o
                    break
        if output is None:
            st.warning(self.ui.get("ee_output_missing", "Output not found."))
            return False
        row = evidence_row_from_output(
            output,
            profile=self.profile,
            existing_ids=existing,
            target_lang=llm_client.reply_language(),
        )
        entries.append(compact_evidence_row(row))
        self._save_pool(
            entries, self.ui.get("ee_output_created", "Evidence created from output.")
        )
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
        if action == "suggest_skills":
            return self._apply_suggest_skills(eid)
        if action == "backfill_project_refs":
            return self._apply_backfill_project_refs(payload.get("ids"))
        if action == "apply_migration":
            return self._apply_migration(payload.get("ids"))
        if action == "refresh_from_crystallized_tasks":
            return self._apply_refresh_crystallized(payload.get("task_ids"))
        if action == "done_tasks_to_evidence":
            return self._apply_done_tasks_to_evidence(
                payload.get("task_ids"),
                bool(payload.get("mark_crystallized")),
            )
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
        if action == "create_from_output":
            return self._apply_create_from_output(str(payload.get("output_id") or ""))
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
