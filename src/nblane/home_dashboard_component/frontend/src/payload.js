const STATUS_ORDER = ["expert", "solid", "learning", "locked"];

export function asObject(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : {};
}

export function asArray(value) {
  return Array.isArray(value) ? value : [];
}

export function cleanText(value, fallback = "") {
  if (value === null || value === undefined) {
    return fallback;
  }
  const text = String(value).trim();
  return text || fallback;
}

export function normalizeCounts(counts, keys = []) {
  const source = asObject(counts);
  const out = {};
  keys.forEach((key) => {
    const value = Number(source[key]);
    out[key] = Number.isFinite(value) && value > 0 ? Math.round(value) : 0;
  });
  Object.entries(source).forEach(([key, raw]) => {
    if (key in out) {
      return;
    }
    const value = Number(raw);
    out[key] = Number.isFinite(value) && value > 0 ? Math.round(value) : 0;
  });
  return out;
}

export function normalizeGoal(goal) {
  const source = asObject(goal);
  const projection = asObject(source.projection);
  const editor = asObject(source.editor);
  const locked = Boolean(source.locked);
  const isSet = Boolean(source.is_set || source.isSet || projection.id || editor.id || locked);
  return {
    isSet,
    locked,
    projection: Object.keys(projection).length ? projection : null,
    editor,
    statusOptions: asArray(source.status_options || source.statusOptions).map(String),
    visibilityOptions: asArray(source.visibility_options || source.visibilityOptions).map(String),
  };
}

export function goalDisplay(goal, ui = {}) {
  const normalized = normalizeGoal(goal);
  const projection = normalized.projection || {};
  if (normalized.locked) {
    return {
      title: cleanText(ui.goal_private_locked, "Private goal"),
      eyebrow: cleanText(ui.dashboard_metric_goal, "Current goal"),
      summary: "",
      focus: [],
      visibility: "private",
      status: "",
      target: "",
    };
  }
  if (!normalized.isSet) {
    return {
      title: cleanText(ui.goal_no_current, "No current goal set."),
      eyebrow: cleanText(ui.dashboard_metric_goal, "Current goal"),
      summary: cleanText(ui.goal_module_caption, ""),
      focus: [],
      visibility: "",
      status: "",
      target: "",
    };
  }
  const visibility = cleanText(projection.visibility, "");
  const hiddenLabel = cleanText(ui.goal_strip_hidden, "Goal set");
  const defaultLabel = cleanText(ui.goal_strip_default_label, "Stage goal");
  if (visibility === "hidden") {
    return {
      title: hiddenLabel,
      eyebrow: cleanText(ui.dashboard_metric_goal, "Current goal"),
      summary: "",
      focus: [],
      visibility,
      status: cleanText(projection.status, ""),
      target: "",
    };
  }
  const title = cleanText(projection.title || projection.label, defaultLabel);
  return {
    title,
    eyebrow: cleanText(ui.dashboard_metric_goal, "Current goal"),
    summary: visibility === "visible" ? cleanText(projection.summary, "") : "",
    focus: visibility === "visible" ? asArray(projection.focus).filter(Boolean).slice(0, 3) : [],
    visibility,
    status: cleanText(projection.status, ""),
    target: cleanText(projection.target, ""),
  };
}

export function normalizePayload(payload) {
  const source = asObject(payload);
  const charts = asObject(source.charts);
  const skillChart = asObject(charts.skills);
  const evidenceChart = asObject(charts.evidence);
  const publicChart = asObject(charts.public);
  const healthChart = asObject(charts.health);
  const graph = asObject(source.graph);
  return {
    profile: cleanText(source.profile, ""),
    goal: normalizeGoal(source.goal),
    kanban: asObject(source.kanban),
    skills: asObject(source.skills),
    pendingEvidence: asObject(source.pending_evidence),
    health: asObject(source.health),
    publicLayer: asObject(source.public),
    charts: {
      skills: {
        counts: normalizeCounts(skillChart.counts, STATUS_ORDER),
        total: Math.max(0, Number(skillChart.total) || 0),
        lit: Math.max(0, Number(skillChart.lit) || 0),
        litRate: Math.max(0, Math.min(1, Number(skillChart.lit_rate) || 0)),
      },
      evidence: {
        doneUncrystallized: Math.max(0, Number(evidenceChart.done_uncrystallized) || 0),
        unlinked: Math.max(0, Number(evidenceChart.unlinked) || 0),
      },
      public: {
        draft: Math.max(0, Number(publicChart.draft) || 0),
        published: Math.max(0, Number(publicChart.published) || 0),
      },
      health: normalizeCounts(healthChart, ["error", "warning", "info"]),
    },
    graph: {
      nodes: asArray(graph.nodes).map(asObject).filter((node) => cleanText(node.id)),
      edges: asArray(graph.edges).map(asObject).filter((edge) => cleanText(edge.from) && cleanText(edge.to)),
    },
    quickLinks: asArray(source.quick_links).map(asObject).filter((link) => cleanText(link.path)),
    ai: asObject(source.ai),
    ui: asObject(source.ui),
  };
}

export function goalDraftFromFormData(formData) {
  const lines = (name) =>
    cleanText(formData.get(name))
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean);
  return {
    id: cleanText(formData.get("id")),
    title: cleanText(formData.get("title")),
    label: cleanText(formData.get("label")),
    status: cleanText(formData.get("status"), "active"),
    start: cleanText(formData.get("start")),
    target: cleanText(formData.get("target")),
    ui_visibility: cleanText(formData.get("ui_visibility"), "discreet"),
    include_in_agent_context: formData.get("include_in_agent_context") === "on",
    summary: cleanText(formData.get("summary")),
    target_skills: lines("target_skills"),
    success_criteria: lines("success_criteria"),
    focus: lines("focus"),
    evidence_refs: lines("evidence_refs"),
    task_refs: lines("task_refs"),
    output_refs: lines("output_refs"),
    notes: cleanText(formData.get("notes")),
  };
}
