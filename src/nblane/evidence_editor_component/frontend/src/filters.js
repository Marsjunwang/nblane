// Pure client-side filtering + search for the evidence list. No React here so
// it can be unit-tested with `node --test`.

export function matchesSearch(row, query) {
  const q = String(query || "").trim().toLowerCase();
  if (!q) return true;
  const hay = `${row.title || ""} ${row.summary || ""}`.toLowerCase();
  return hay.includes(q);
}

// filters: {origin, type, review_status, language, hasProject, needsMigration}
// Empty/falsey filter fields mean "any".
export function matchesFilters(row, filters = {}) {
  if (filters.origin && (row.origin || "") !== filters.origin) return false;
  if (filters.type && (row.type || "") !== filters.type) return false;
  if (
    filters.review_status &&
    (row.review_status || "") !== filters.review_status
  ) {
    return false;
  }
  if (filters.language && (row.language || "") !== filters.language) {
    return false;
  }
  if (filters.hasProject && !row.has_project) return false;
  if (filters.needsMigration && !row.needs_migration) return false;
  if (filters.missingRaw && row.has_original_content) return false;
  if (filters.missingDate && !row.missing_date) return false;
  if (filters.missingProject && row.has_project) return false;
  if (filters.projectWithoutGoal && row.project_resolution_status !== "project_without_goal") return false;
  if (filters.missingFormatted && !row.missing_formatted_content) return false;
  if (filters.sourceConflict && !row.source_conflict) return false;
  if (filters.danglingTaskSource && !row.dangling_task_source) return false;
  return true;
}

export function filterRows(rows, query, filters) {
  const list = Array.isArray(rows) ? rows : [];
  return list.filter(
    (row) => matchesSearch(row, query) && matchesFilters(row, filters)
  );
}

// Provenance / privacy warnings shown in the detail pane. Returns a list of
// stable warning keys (i18n resolves them to text).
export function rowWarnings(row) {
  const out = [];
  const origin = row.origin || "";
  const hasProject = !!row.has_project;
  const hasRaw = !!row.has_original_content;
  const readiness = row.public_readiness || "";
  if ((origin === "resume_parse" || origin === "manual_daily") && !hasProject) {
    out.push("ee_project_provenance_reminder");
  }
  if (!hasRaw) {
    out.push("ee_original_content_missing");
  }
  if (!row.has_date) {
    out.push("ee_missing_date");
  }
  if (row.missing_formatted_content) {
    out.push("ee_missing_formatted_content");
  }
  if (row.project_resolution_status === "project_without_goal") {
    out.push("ee_project_without_goal");
  }
  if (row.source_conflict) {
    out.push("ee_source_conflict");
  }
  if (row.dangling_task_source) {
    out.push("ee_dangling_task_source");
  }
  if (readiness && readiness !== "private" && hasRaw) {
    out.push("ee_privacy_original_content_warning");
  }
  return out;
}
