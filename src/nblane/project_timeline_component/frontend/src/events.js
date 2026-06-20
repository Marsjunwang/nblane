// Event factory for the project timeline component -> Streamlit.

export function makeEvent(action, payload = {}) {
  return {
    action,
    event_id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    payload: payload && typeof payload === "object" ? payload : {},
  };
}

export const saveBasicsEvent = (id, fields) => makeEvent("save_basics", { id, fields });
export const archiveProjectEvent = (id) => makeEvent("archive_project", { id });

export const addTaskEvent = (id, fields) => makeEvent("add_task", { id, fields });
export const saveTaskEvent = (id, taskId, fields) =>
  makeEvent("save_task", { id, task_id: taskId, fields });
export const deleteTaskEvent = (id, taskId) =>
  makeEvent("delete_task", { id, task_id: taskId });
export const moveTaskSectionEvent = (id, taskId, section) =>
  makeEvent("move_task_section", { id, task_id: taskId, section });

export const addMilestoneEvent = (id, fields) => makeEvent("add_milestone", { id, fields });
export const saveMilestoneEvent = (id, milestoneId, fields) =>
  makeEvent("save_milestone", { id, milestone_id: milestoneId, fields });
export const deleteMilestoneEvent = (id, milestoneId) =>
  makeEvent("delete_milestone", { id, milestone_id: milestoneId });

export const openEvidenceForTaskEvent = (taskId, projectId) =>
  makeEvent("open_evidence_for_task", { task_id: taskId, project_id: projectId });

export const suggestRefsEvent = (id) => makeEvent("suggest_refs", { id });
export const setRangeEvent = (start, end) =>
  makeEvent("set_range", { start: start || "", end: end || "" });
