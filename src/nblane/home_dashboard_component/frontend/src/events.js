export function makeEvent(action, payload = {}) {
  return {
    action,
    event_id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    payload,
  };
}

export function navigationEvent(path) {
  return makeEvent("navigate", { path: String(path || "") });
}

export function goalSubmitEvent(goal) {
  return makeEvent("edit_goal_submit", goal && typeof goal === "object" ? goal : {});
}

export function openSectionEvent(section) {
  return makeEvent("open_section", { section: String(section || "") });
}
