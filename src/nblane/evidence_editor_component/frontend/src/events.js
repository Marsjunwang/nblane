// Event factory for the evidence editor component -> Streamlit.
// Each event is {action, event_id, payload}. Python dedups by event_id.

export function makeEvent(action, payload = {}) {
  return {
    action,
    event_id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    payload: payload && typeof payload === "object" ? payload : {},
  };
}

// Pool editing.
export const saveEvidenceEvent = (id, fields) =>
  makeEvent("save_evidence", { id, fields });
export const addEvidenceEvent = (fields) =>
  makeEvent("add_evidence", { fields });
export const deprecateEvidenceEvent = (id, replacedBy = "") =>
  makeEvent("deprecate_evidence", { id, replaced_by: replacedBy });

// Project linking (internal Project Board only).
export const linkProjectEvent = (id, projectRefs) =>
  makeEvent("link_project", { id, project_refs: projectRefs });
export const backfillProjectRefsEvent = (ids) =>
  makeEvent("backfill_project_refs", { ids });
export const createProjectFromEvidenceEvent = (suggestion) =>
  makeEvent("create_project_from_evidence", { suggestion });

// Skill linking (skill tree nodes; no LLM, add/remove reconcile).
export const linkSkillsEvent = (id, skillIds) =>
  makeEvent("link_skills", { id, skill_ids: skillIds });

// Optional LLM skill recall: ask the router for extra candidate skills for one
// row. Rule suggestions ship in the payload already; this augments them.
export const suggestSkillsEvent = (id) =>
  makeEvent("suggest_skills", { id });

// Migration / refresh.
export const applyMigrationEvent = (ids) =>
  makeEvent("apply_migration", { ids });
export const refreshCrystallizedEvent = (taskIds) =>
  makeEvent("refresh_from_crystallized_tasks", { task_ids: taskIds });

// Done tasks -> evidence (deterministic, incl. non-crystallized; no LLM).
export const prepareDoneTaskEvidenceEvent = (taskIds) =>
  makeEvent("prepare_done_task_evidence", { task_ids: taskIds });
export const applyDoneTaskEvidenceEvent = (previewId, markCrystallized = true) =>
  makeEvent("apply_done_task_evidence", {
    preview_id: previewId,
    mark_crystallized: !!markCrystallized,
  });
export const doneTasksToEvidenceEvent = (taskIds, markCrystallized = false) =>
  makeEvent("done_tasks_to_evidence", {
    task_ids: taskIds,
    mark_crystallized: !!markCrystallized,
  });

// Bulk apply across many selected rows (one save). Either set a whitelisted
// pool field ({field, value}) or run a named action ({action, ...payload}).
export const bulkApplyEvent = (ids, opts = {}) =>
  makeEvent("bulk_apply", {
    ids,
    field: opts.field || "",
    value: opts.value || "",
    bulk_action: opts.action || "",
    project_refs: opts.projectRefs || undefined,
    skill_ids: opts.skillIds || undefined,
  });

// AI reformat (suggest-and-confirm).
export const requestAiReformatEvent = (id) =>
  makeEvent("request_ai_reformat", { id });
export const confirmAiReformatEvent = (id, fields) =>
  makeEvent("confirm_ai_reformat", { id, fields });
export const bulkRequestAiReformatEvent = (ids) =>
  makeEvent("bulk_request_ai_reformat", { ids });
export const bulkConfirmAiReformatEvent = (previewId) =>
  makeEvent("bulk_confirm_ai_reformat", { preview_id: previewId });

// Output -> evidence.
export const createFromOutputEvent = (outputId, sourceKind = "output", projectRefs = []) =>
  makeEvent("create_from_output", {
    output_id: outputId,
    source_kind: sourceKind,
    project_refs: projectRefs,
  });
export const bulkCreateFromOutputEvent = (items) =>
  makeEvent("bulk_create_from_output", { items: Array.isArray(items) ? items : [] });
export const ignoreOutputCandidatesEvent = (items, reason = "not_evidence") =>
  makeEvent("ignore_output_candidates", {
    items: Array.isArray(items) ? items : [],
    reason,
  });
export const restoreOutputCandidatesEvent = (items) =>
  makeEvent("restore_output_candidates", { items: Array.isArray(items) ? items : [] });

// Duplicates.
export const suggestDuplicatesEvent = (id, ai = false) =>
  makeEvent("suggest_duplicates", { id: id || "", ai: !!ai });
export const mergeOrDeprecateEvent = (keep, other, mergeFields = null) =>
  makeEvent("merge_or_deprecate", {
    keep,
    other,
    merge_fields: mergeFields,
  });
export const dismissDuplicateEvent = (a, b) =>
  makeEvent("dismiss_duplicate", { id: a, other: b });
