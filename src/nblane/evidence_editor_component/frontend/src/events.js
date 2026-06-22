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

// Migration / refresh.
export const applyMigrationEvent = (ids) =>
  makeEvent("apply_migration", { ids });
export const refreshCrystallizedEvent = (taskIds) =>
  makeEvent("refresh_from_crystallized_tasks", { task_ids: taskIds });

// AI reformat (suggest-and-confirm).
export const requestAiReformatEvent = (id) =>
  makeEvent("request_ai_reformat", { id });
export const confirmAiReformatEvent = (id, fields) =>
  makeEvent("confirm_ai_reformat", { id, fields });

// Output -> evidence.
export const createFromOutputEvent = (outputId) =>
  makeEvent("create_from_output", { output_id: outputId });

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
