const STATUS_ORDER = ["expert", "solid", "learning", "locked"];
const GRAPH_LAYER_ORDER = [
  "direction",
  "objective",
  "work_context",
  "activity",
  "source",
  "evidence",
  "claim",
  "capability",
  "output",
  "feedback",
  "governance",
];
const GRAPH_TYPE_LAYER = {
  north_star: "direction",
  goal: "objective",
  project_case: "work_context",
  task: "activity",
  daily_work: "activity",
  research: "activity",
  agent_run: "activity",
  source: "source",
  evidence: "evidence",
  evidence_candidate: "evidence",
  atomic_evidence: "evidence",
  composite_evidence: "evidence",
  claim: "claim",
  skill: "capability",
  gap: "capability",
  next_action: "capability",
  output: "output",
  feedback: "feedback",
  capacity: "governance",
  health: "governance",
};

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

export function normalizeNorthStar(northStar) {
  const source = asObject(northStar);
  return {
    visibility: cleanText(source.visibility, "discreet"),
    displayText: cleanText(source.display_text || source.displayText),
    isSet: Boolean(source.is_set || source.isSet),
    locked: Boolean(source.locked),
    hasBrief: Boolean(source.has_brief || source.hasBrief),
  };
}

export function normalizeSkillLink(link) {
  const source = asObject(link);
  return {
    nodeId: cleanText(source.node_id || source.nodeId || source.id),
    label: cleanText(source.label),
    source: cleanText(source.source, "manual"),
    score: Math.max(0, Number(source.score) || 0),
    rationale: cleanText(source.rationale),
  };
}

export function normalizeGoalCard(goal) {
  const normalized = normalizeGoal(goal);
  const source = asObject(goal);
  const id =
    cleanText(source.id) ||
    cleanText(normalized.projection?.id) ||
    cleanText(normalized.editor?.id);
  return {
    ...normalized,
    id,
    isPrimary: Boolean(source.is_primary || source.isPrimary),
  };
}

export function normalizeSkillAlignment(alignment) {
  const source = asObject(alignment);
  const byGoalRaw = asObject(source.by_goal || source.byGoal);
  const byGoal = {};
  Object.entries(byGoalRaw).forEach(([goalId, raw]) => {
    const item = asObject(raw);
    byGoal[goalId] = {
      confirmed: asArray(item.confirmed).map(normalizeSkillLink).filter((link) => link.nodeId),
      candidates: asArray(item.candidates).map(normalizeSkillLink).filter((link) => link.nodeId),
    };
  });
  return {
    primaryGoalId: cleanText(source.primary_goal_id || source.primaryGoalId),
    confirmedLinks: asArray(source.confirmed_links || source.confirmedLinks)
      .map(normalizeSkillLink)
      .filter((link) => link.nodeId),
    candidates: asArray(source.candidates).map(normalizeSkillLink).filter((link) => link.nodeId),
    byGoal,
    skillOptions: asArray(source.skill_options || source.skillOptions)
      .map((item) => {
        const option = asObject(item);
        return {
          id: cleanText(option.id),
          label: cleanText(option.label || option.id),
        };
      })
      .filter((option) => option.id),
  };
}

export function normalizeGraphNode(node) {
  const source = asObject(node);
  const type = cleanText(source.type, "note");
  const placeholder = Boolean(source.placeholder);
  return {
    id: cleanText(source.id),
    type,
    layer: cleanText(source.layer, GRAPH_TYPE_LAYER[type] || "activity"),
    label: cleanText(source.label),
    metric: cleanText(source.metric),
    status: cleanText(source.status),
    recordId: cleanText(source.record_id || source.recordId),
    ownerPath: cleanText(source.owner_path || source.ownerPath),
    implemented: source.implemented === undefined ? !placeholder : Boolean(source.implemented),
    placeholder,
    locked: Boolean(source.locked),
    suggested: Boolean(source.suggested),
    isPrimary: Boolean(source.is_primary || source.isPrimary),
  };
}

export function normalizeGraphEdge(edge) {
  const source = asObject(edge);
  return {
    from: cleanText(source.from || source.source),
    to: cleanText(source.to || source.target),
    type: cleanText(source.type, "link"),
    relation: cleanText(source.relation, cleanText(source.type, "link")),
    placeholder: Boolean(source.placeholder),
    suggested: Boolean(source.suggested),
  };
}

export function normalizeGraphLayers(layers, nodes = []) {
  const seen = new Set();
  const out = [];
  const add = (value) => {
    const layer = cleanText(value);
    if (!layer || seen.has(layer)) {
      return;
    }
    seen.add(layer);
    out.push(layer);
  };
  asArray(layers).forEach(add);
  if (!out.length) {
    GRAPH_LAYER_ORDER.forEach((layer) => {
      if (nodes.some((node) => node.layer === layer)) {
        add(layer);
      }
    });
  }
  nodes.forEach((node) => add(node.layer));
  return out;
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
    northStar: normalizeNorthStar(source.north_star || source.northStar),
    goal: normalizeGoal(source.goal),
    primaryGoal: normalizeGoal(source.primary_goal || source.primaryGoal || source.goal),
    activeGoals: asArray(source.active_goals || source.activeGoals).map(normalizeGoalCard),
    goalCounts: {
      active: Math.max(0, Number(asObject(source.goal_counts || source.goalCounts).active) || 0),
      total: Math.max(0, Number(asObject(source.goal_counts || source.goalCounts).total) || 0),
    },
    skillAlignment: normalizeSkillAlignment(source.skill_alignment || source.skillAlignment),
    kanban: asObject(source.kanban),
    skills: asObject(source.skills),
    sources: asObject(source.sources),
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
    graph: (() => {
      const nodes = asArray(graph.nodes).map(normalizeGraphNode).filter((node) => node.id);
      return {
        schemaVersion: cleanText(graph.schema_version || graph.schemaVersion),
        view: cleanText(graph.view),
        layers: normalizeGraphLayers(graph.layers, nodes),
        nodes,
        edges: asArray(graph.edges).map(normalizeGraphEdge).filter((edge) => edge.from && edge.to),
      };
    })(),
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
    alignment: cleanText(formData.get("alignment")),
    set_as_primary: formData.get("set_as_primary") === "on",
  };
}
