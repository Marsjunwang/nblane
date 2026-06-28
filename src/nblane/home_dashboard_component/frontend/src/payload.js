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

// Visual role (star-tree prototype) fallback when the backend omits `role`.
// Single source of truth is growth_graph_contract.py; this mirror keeps the
// frontend resilient against older payloads. The 6 out-of-tree types map to "".
export const ROLE_FOR_TYPE = {
  north_star: "trunk",
  goal: "direction",
  project_case: "branch",
  task: "leaf",
  output: "leaf",
  daily_work: "sand",
  research: "sand",
  source: "sand",
  evidence: "fruit",
  evidence_candidate: "fruit",
  atomic_evidence: "fruit",
  composite_evidence: "fruit",
  claim: "constellation",
  skill: "star",
  agent_run: "",
  gap: "",
  next_action: "",
  feedback: "",
  capacity: "",
  health: "",
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
  const rawProgress = source.progress;
  const progress =
    typeof rawProgress === "number"
      ? rawProgress
      : rawProgress === null || rawProgress === undefined || rawProgress === ""
        ? null
        : Number(rawProgress);
  const rawDaysToTarget = source.days_to_target ?? source.daysToTarget;
  const daysToTarget =
    rawDaysToTarget === null || rawDaysToTarget === undefined || rawDaysToTarget === ""
      ? null
      : Number(rawDaysToTarget);
  const rawDaysSinceActivity =
    source.days_since_activity ?? source.daysSinceActivity;
  const daysSinceActivity =
    rawDaysSinceActivity === null ||
    rawDaysSinceActivity === undefined ||
    rawDaysSinceActivity === ""
      ? null
      : Number(rawDaysSinceActivity);
  return {
    ...normalized,
    id,
    isPrimary: Boolean(source.is_primary || source.isPrimary),
    progress: Number.isFinite(progress) ? progress : null,
    stalled: Boolean(source.stalled),
    daysSinceActivity: Number.isFinite(daysSinceActivity) ? daysSinceActivity : null,
    targetDate: cleanText(source.target_date || source.targetDate),
    daysToTarget: Number.isFinite(daysToTarget) ? daysToTarget : null,
    projectCount: Math.max(0, Number(source.project_count || source.projectCount) || 0),
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
    role: cleanText(source.role) || ROLE_FOR_TYPE[type] || "",
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
    summary: cleanText(source.summary),
    description: cleanText(source.description),
    // Derived goal state (project-completion progress + stall). progress is a
    // number 0..1 or null (no projects); kept verbatim so the goal progress arc
    // and stalled-grey rendering can read them. Whitelisted explicitly — the rest
    // of this normalizer drops unknown fields.
    progress:
      typeof source.progress === "number"
        ? source.progress
        : source.progress === null || source.progress === undefined
          ? null
          : Number(source.progress),
    stalled: Boolean(source.stalled),
    itemKind: cleanText(source.item_kind || source.itemKind),
    meta: asObject(source.meta),
    primaryAction: normalizeGraphAction(source.primary_action || source.primaryAction),
    secondaryActions: asArray(source.secondary_actions || source.secondaryActions)
      .map(normalizeGraphAction)
      .filter((action) => action.id || action.event.action),
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

export function normalizeGraphAction(action) {
  const source = asObject(action);
  const event = asObject(source.event);
  return {
    id: cleanText(source.id),
    nodeId: cleanText(source.node_id || source.nodeId),
    label: cleanText(source.label),
    severity: cleanText(source.severity),
    event: {
      action: cleanText(event.action),
      payload: asObject(event.payload),
    },
  };
}

export function normalizeGraphAttention(attention) {
  const source = asObject(attention);
  return {
    counts: normalizeCounts(source.counts),
    nodes: asArray(source.nodes)
      .map((item) => {
        const row = asObject(item);
        return {
          id: cleanText(row.id),
          reason: cleanText(row.reason),
          severity: cleanText(row.severity),
        };
      })
      .filter((item) => item.id),
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

export function normalizeProfileContext(source) {
  const value = asObject(source);
  const identityFields = asArray(value.identity_fields || value.identityFields)
    .map((field) => cleanText(field))
    .filter(Boolean);
  const narrativeSections = asArray(
    value.narrative_sections || value.narrativeSections,
  )
    .map((title) => cleanText(title))
    .filter(Boolean);
  const visibilities = asArray(
    value.north_star_visibilities || value.northStarVisibilities,
  )
    .map((item) => cleanText(item))
    .filter(Boolean);
  const generatedBlocks = asArray(value.generated_blocks || value.generatedBlocks)
    .map((item) => cleanText(item))
    .filter(Boolean);
  const competencyStatuses = asArray(
    value.competency_statuses || value.competencyStatuses,
  )
    .map((item) => cleanText(item))
    .filter(Boolean);
  const coreCompetencies = asArray(
    value.core_competencies || value.coreCompetencies,
  )
    .map((row) => {
      const item = asObject(row);
      return {
        area: cleanText(item.area),
        status: cleanText(item.status),
        notes: cleanText(item.notes),
      };
    })
    .filter((row) => row.area || row.notes);
  const identityRaw = asObject(value.identity);
  const identity = {};
  identityFields.forEach((field) => {
    identity[field] = cleanText(identityRaw[field]);
  });
  const narrativeRaw = asObject(value.narrative);
  const narrative = {};
  narrativeSections.forEach((title) => {
    narrative[title] = typeof narrativeRaw[title] === "string" ? narrativeRaw[title] : "";
  });
  const generatedBlockRaw = asObject(
    value.generated_block_text || value.generatedBlockText,
  );
  const generatedBlockText = {};
  generatedBlocks.forEach((block) => {
    generatedBlockText[block] =
      typeof generatedBlockRaw[block] === "string" ? generatedBlockRaw[block] : "";
  });
  const readinessRaw = asObject(value.readiness);
  return {
    hasSkillMd: Boolean(value.has_skill_md || value.hasSkillMd),
    identityFields,
    identity,
    narrativeSections,
    narrative,
    northStarVisibilities: visibilities,
    coreCompetencies,
    competencyStatuses,
    generatedBlocks,
    generatedBlockText,
    rawMarkdown: typeof value.raw_markdown === "string" ? value.raw_markdown : "",
    readiness: {
      contextReady: Boolean(readinessRaw.context_ready || readinessRaw.contextReady),
      errors: Math.max(0, Number(readinessRaw.errors) || 0),
      warnings: Math.max(0, Number(readinessRaw.warnings) || 0),
      ownerPath: cleanText(readinessRaw.owner_path || readinessRaw.ownerPath),
    },
  };
}

export function normalizeResumeIngest(source) {
  const value = asObject(source);
  const mergeRaw = value.merge && typeof value.merge === "object" ? value.merge : null;
  const merge = mergeRaw
    ? {
        ok: Boolean(mergeRaw.ok),
        warnings: asArray(mergeRaw.warnings).map((item) => cleanText(item)).filter(Boolean),
        errors: asArray(mergeRaw.errors).map((item) => cleanText(item)).filter(Boolean),
        newEvidence: asArray(mergeRaw.new_evidence || mergeRaw.newEvidence)
          .map((item) => cleanText(item))
          .filter(Boolean),
        treeDelta: asArray(mergeRaw.tree_delta || mergeRaw.treeDelta)
          .map((item) => cleanText(item))
          .filter(Boolean),
        mergedPoolYaml:
          typeof mergeRaw.merged_pool_yaml === "string"
            ? mergeRaw.merged_pool_yaml
            : typeof mergeRaw.mergedPoolYaml === "string"
            ? mergeRaw.mergedPoolYaml
            : "",
        mergedTreeYaml:
          typeof mergeRaw.merged_tree_yaml === "string"
            ? mergeRaw.merged_tree_yaml
            : typeof mergeRaw.mergedTreeYaml === "string"
            ? mergeRaw.mergedTreeYaml
            : "",
      }
    : null;
  return {
    llmConfigured: Boolean(value.llm_configured || value.llmConfigured),
    hasPendingPatch: Boolean(value.has_pending_patch || value.hasPendingPatch),
    allowStatusChange: Boolean(value.allow_status_change || value.allowStatusChange),
    merge,
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
    revision: cleanText(source.revision, ""),
    northStar: normalizeNorthStar(source.north_star || source.northStar),
    goal: normalizeGoal(source.goal),
    primaryGoal: normalizeGoal(source.primary_goal || source.primaryGoal || source.goal),
    activeGoals: asArray(source.active_goals || source.activeGoals).map(normalizeGoalCard),
    allGoals: asArray(source.all_goals || source.allGoals).map(normalizeGoalCard),
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
        needsReview: Math.max(0, Number(evidenceChart.needs_review) || 0),
        statusRisk: Math.max(0, Number(evidenceChart.status_risk) || 0),
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
        contract: asObject(graph.contract),
        layers: normalizeGraphLayers(graph.layers, nodes),
        nodes,
        edges: asArray(graph.edges).map(normalizeGraphEdge).filter((edge) => edge.from && edge.to),
        focusPath: asArray(graph.focus_path || graph.focusPath).map((item) => cleanText(item)).filter(Boolean),
        attention: normalizeGraphAttention(graph.attention),
        actions: asArray(graph.actions).map(normalizeGraphAction).filter((action) => action.id || action.event.action),
      };
    })(),
    quickLinks: asArray(source.quick_links).map(asObject).filter((link) => cleanText(link.path)),
    canvasEmbed: asObject(source.canvas_embed || source.canvasEmbed),
    profileContext: normalizeProfileContext(source.profile_context || source.profileContext),
    resumeIngest: normalizeResumeIngest(source.resume_ingest || source.resumeIngest),
    trends: (() => {
      const t = asObject(source.trends);
      const deltasRaw = asObject(t.deltas);
      const sparkRaw = asObject(t.sparkline);
      const deltas = {};
      Object.keys(deltasRaw).forEach((k) => {
        deltas[k] = Number(deltasRaw[k]) || 0;
      });
      const sparkline = {};
      Object.keys(sparkRaw).forEach((k) => {
        sparkline[k] = asArray(sparkRaw[k])
          .map((n) => Number(n) || 0);
      });
      return {
        daysBack: Math.max(1, Number(t.days_back || t.daysBack) || 7),
        baselineDate: cleanText(t.baseline_date || t.baselineDate),
        deltas,
        sparkline,
      };
    })(),
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

// Parent→child CONTAINMENT relations: the real goal→project→task→evidence
// nesting. Deliberately NARROWER than the full structural edge set — relations
// like `supports`/`drives` link work to shared skills and to the North Star,
// which would make almost every node transitively reachable from every goal and
// defeat any "is this shared?" test. Containment is the spine buildGalaxyInputs
// walks to decide a project's owning goal, so we mirror exactly that here.
export const ARCHIVE_STRUCT_RELATIONS = new Set([
  "contains", "alignment", "drives", "produces", "supports", "generated_by", "derives", "review",
]);

// The "work" tree-roles buildGalaxyInputs can re-parent into the synthetic
// "Other" hub: projects (branch), tasks/outputs (leaf), evidence (fruit). The
// archive cascade walks ONLY between these roles, which stops it at skills
// (star), claims (constellation), the North Star (trunk) and sources (sand).
// Those are shared hubs (every task supports a skill, every skill links to the
// North Star); including them would make the whole graph transitively reachable
// from any goal and the "is this shared work?" test below would always say yes.
export const ARCHIVE_WORK_ROLES = new Set(["branch", "leaf", "fruit"]);

// Ids to hide when the "show archived / paused goals" toggle is OFF: every
// extinguished (archived|paused) goal PLUS the containment subtree that hangs
// off it ALONE. The subtree has to go too — a project/task/evidence whose only
// containing parent is a hidden goal would otherwise be detected as an orphan
// and adopted into the synthetic "Other" hub (3D galaxy) or flung onto a stray
// ring (2D flow), so toggling a goal OFF would paradoxically RELOCATE its work
// into view instead of removing it.
//
// We cascade level-by-level along containment edges, not by transitive
// reachability: a child is hidden only when EVERY one of its containing parents
// is itself hidden. A project (or task) also contained by a still-visible goal
// is shared work and stays — and because it stays, its own descendants are
// reached from a visible parent and stay too. Returns an empty Set when the
// toggle is ON or nothing is extinguished.
// Ids to hide when the "show archived / paused goals" toggle is OFF: every
// extinguished (archived|paused) goal PLUS the work that hangs off it ALONE.
// The subtree has to go too — a project/task/evidence whose only parent is a
// hidden goal would otherwise be detected as an orphan and adopted into the
// synthetic "Other" hub (3D galaxy) or flung onto a stray ring (2D flow), so
// toggling a goal OFF would paradoxically RELOCATE its work into view instead
// of removing it.
//
// Cascade is level-by-level over work-role nodes, not transitive reachability:
// a work node is hidden only when EVERY one of its structural parents is itself
// hidden. A project (or task) also parented by a still-visible goal is shared
// work and stays — and because it stays, its descendants keep a visible parent
// and stay too. Returns an empty Set when the toggle is ON or nothing is
// extinguished.
export function hiddenArchivedSubtreeIds(payload, showArchived) {
  if (showArchived) return new Set();
  const nodes = asArray(payload?.graph?.nodes);
  const byId = new Map(nodes.map((n) => [n.id, n]));
  const isExtinguished = (n) =>
    n && n.type === "goal" && (n.status === "archived" || n.status === "paused");
  const extinguished = nodes.filter(isExtinguished);
  if (!extinguished.length) return new Set();
  const isWork = (id) => ARCHIVE_WORK_ROLES.has(byId.get(id)?.role);
  const children = new Map(); // parent id -> [work child id]
  const parents = new Map(); // work child id -> Set(parent id)
  asArray(payload?.graph?.edges).forEach((e) => {
    if (!ARCHIVE_STRUCT_RELATIONS.has(cleanText(e.relation || e.type))) return;
    if (!isWork(e.to)) return; // only ever hide work-role nodes
    if (!children.has(e.from)) children.set(e.from, []);
    children.get(e.from).push(e.to);
    if (!parents.has(e.to)) parents.set(e.to, new Set());
    parents.get(e.to).add(e.from);
  });
  const hidden = new Set(extinguished.map((n) => n.id));
  // BFS down the work tree. A node enters `hidden` only once all of its parents
  // are hidden; then we descend into its children.
  const queue = extinguished.map((n) => n.id);
  while (queue.length) {
    const id = queue.shift();
    (children.get(id) || []).forEach((childId) => {
      if (hidden.has(childId)) return;
      const ps = parents.get(childId);
      const allParentsHidden = ps && [...ps].every((p) => hidden.has(p));
      if (allParentsHidden) {
        hidden.add(childId);
        queue.push(childId);
      }
    });
  }
  return hidden;
}
