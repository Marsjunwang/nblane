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

export function captureInboxSubmitEvent(draft) {
  return makeEvent("capture_inbox_submit", draft && typeof draft === "object" ? draft : {});
}

export function createGoalSubmitEvent(goal) {
  return makeEvent("create_goal_submit", goal && typeof goal === "object" ? goal : {});
}

export function editGoalSubmitEvent(goalId, goal) {
  return makeEvent("edit_goal_submit", {
    ...(goal && typeof goal === "object" ? goal : {}),
    goal_id: String(goalId || ""),
  });
}

export function archiveGoalEvent(goalId) {
  return makeEvent("archive_goal", { goal_id: String(goalId || "") });
}

export function openSectionEvent(section) {
  return makeEvent("open_section", { section: String(section || "") });
}

export function requestGoalSkillRuleMatchEvent(goalId) {
  return makeEvent("request_goal_skill_rule_match", { goal_id: String(goalId || "") });
}

export function requestGoalSkillAiMatchEvent(goalId) {
  return makeEvent("request_goal_skill_ai_match", { goal_id: String(goalId || "") });
}

export function confirmGoalSkillLinksEvent(goalId, links) {
  return makeEvent("confirm_goal_skill_links", {
    goal_id: String(goalId || ""),
    links: Array.isArray(links) ? links : [],
  });
}

export function manualGoalSkillLinkEvent(goalId, nodeId) {
  return makeEvent("manual_goal_skill_link", {
    goal_id: String(goalId || ""),
    node_id: String(nodeId || ""),
  });
}

export function setPrimaryGoalEvent(goalId) {
  return makeEvent("set_primary_goal", { goal_id: String(goalId || "") });
}

export function openProfileContextEvent() {
  return makeEvent("set_north_star_display_open_profile_context", {});
}
