import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { Streamlit } from "streamlit-component-lib";

import "./style.css";
import {
  asArray,
  cleanText,
  expandableIds,
  filterItems,
  nodeId,
  nodeTitle,
  nodeType,
  normalizePayload,
} from "./payload.js";

function eventId() {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function label(labels, key, fallback) {
  return cleanText(labels?.[key]) || fallback;
}

function makeEvent(action, payload = {}) {
  return {
    action,
    event_id: eventId(),
    payload,
  };
}

function ContextMenu({ menu, payload, onClose, onAction }) {
  const ref = useRef(null);
  useEffect(() => {
    if (!menu) {
      return undefined;
    }
    const onPointer = (event) => {
      if (!ref.current?.contains(event.target)) {
        onClose();
      }
    };
    const onKey = (event) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("pointerdown", onPointer);
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("pointerdown", onPointer);
      window.removeEventListener("keydown", onKey);
    };
  }, [menu, onClose]);

  if (!menu) {
    return null;
  }
  const item = menu.item || {};
  const type = nodeType(item);
  const id = nodeId(item);
  const paperIds = asArray(menu.paperIds || (type === "paper" ? [id] : []))
    .map(cleanText)
    .filter(Boolean);
  const selectedCount = payload.selectedPaperIds.length;
  const canCollections = payload.capabilities.create_collection !== false;
  const canDropPapers = payload.capabilities.drop_papers !== false;
  const rows = [];
  const addRow = (key, text, action, disabled = false, danger = false) => {
    rows.push({ key, text, action, disabled, danger });
  };

  if (type === "collection_root") {
    addRow(
      "create",
      label(payload.labels, "new_collection", "New collection"),
      () => onAction("dialog:create", { parent_id: "" }),
      !canCollections,
    );
    addRow(
      "move-selected-root",
      label(payload.labels, "move_selected_here", "Move selected papers here"),
      () => onAction("emit", makeEvent("paper_library_move_selected_papers_to_collection", { node_id: "", paper_ids: payload.selectedPaperIds })),
      !canDropPapers || selectedCount < 1,
    );
  } else if (type === "collection") {
    addRow(
      "create-child",
      label(payload.labels, "new_subcollection", "New subcollection"),
      () => onAction("dialog:create", { parent_id: id }),
      !canCollections,
    );
    addRow(
      "add-selected",
      label(payload.labels, "add_selected_here", "Add selected papers here"),
      () => onAction("emit", makeEvent("paper_library_add_selected_papers_to_collection", { node_id: id, paper_ids: payload.selectedPaperIds })),
      !canDropPapers || selectedCount < 1,
    );
    addRow(
      "move-selected",
      label(payload.labels, "move_selected_here", "Move selected papers here"),
      () => onAction("emit", makeEvent("paper_library_move_selected_papers_to_collection", { node_id: id, paper_ids: payload.selectedPaperIds })),
      !canDropPapers || selectedCount < 1,
    );
    rows.push({ key: "sep-1", separator: true });
    addRow(
      "rename",
      label(payload.labels, "rename", "Rename"),
      () => onAction("dialog:rename", { node_id: id, title: nodeTitle(item) }),
      payload.capabilities.rename_collection === false,
    );
    addRow(
      "move",
      label(payload.labels, "move_collection", "Move collection"),
      () => onAction("dialog:move", { node_id: id, parent_id: cleanText(item.parent_id) }),
      payload.capabilities.move_collection === false,
    );
    addRow(
      "up",
      label(payload.labels, "move_up", "Move up"),
      () => onAction("emit", makeEvent("paper_library_reorder_collection", { node_id: id, direction: "up" })),
      payload.capabilities.move_collection === false,
    );
    addRow(
      "down",
      label(payload.labels, "move_down", "Move down"),
      () => onAction("emit", makeEvent("paper_library_reorder_collection", { node_id: id, direction: "down" })),
      payload.capabilities.move_collection === false,
    );
    rows.push({ key: "sep-2", separator: true });
    addRow(
      "delete",
      label(payload.labels, "delete_collection", "Delete collection"),
      () => onAction("dialog:delete", { node_id: id, title: nodeTitle(item), parent_id: cleanText(item.parent_id) }),
      payload.capabilities.delete_collection === false,
      true,
    );
  } else if (type === "paper") {
    const activeNodeId = cleanText(payload.activeNodeId);
    if (item.reader_url) {
      addRow(
        "open-reader",
        label(payload.labels, "open_reader", "Open Reader"),
        () => window.open(cleanText(item.reader_url), "_blank", "noopener,noreferrer"),
      );
    }
    addRow(
      "show-details",
      label(payload.labels, "show_details", "Show details"),
      () => onAction("emit", makeEvent("paper_library_select_paper", { source_id: id })),
    );
    rows.push({ key: "sep-paper-1", separator: true });
    addRow(
      "move-paper",
      label(payload.labels, "move_to_collection", "Move to collection"),
      () => onAction("dialog:paper-location", { mode: "move", paper_ids: paperIds }),
      !canDropPapers || paperIds.length < 1,
    );
    addRow(
      "add-paper",
      label(payload.labels, "add_to_collection", "Add to collection"),
      () => onAction("dialog:paper-location", { mode: "add", paper_ids: paperIds }),
      !canDropPapers || paperIds.length < 1,
    );
    addRow(
      "remove-paper",
      label(payload.labels, "remove_from_current_collection", "Remove from current collection"),
      () => onAction("emit", makeEvent("paper_library_remove_papers_from_collection", { node_id: activeNodeId, paper_ids: paperIds })),
      !activeNodeId || paperIds.length < 1,
    );
    rows.push({ key: "sep-paper-2", separator: true });
    addRow(
      "mark-reading",
      label(payload.labels, "mark_as_reading", "Mark as reading"),
      () => onAction("emit", makeEvent("paper_library_update_papers_status", { paper_ids: paperIds, status: "reading" })),
      paperIds.length < 1,
    );
    addRow(
      "archive",
      label(payload.labels, "archive", "Archive"),
      () => onAction("emit", makeEvent("paper_library_update_papers_status", { paper_ids: paperIds, status: "archived" })),
      paperIds.length < 1,
    );
    addRow(
      "discard",
      label(payload.labels, "discard", "Discard"),
      () => onAction("emit", makeEvent("paper_library_update_papers_status", { paper_ids: paperIds, status: "discarded" })),
      paperIds.length < 1,
      true,
    );
    addRow(
      "run-extraction",
      label(payload.labels, "run_extraction", "Run extraction"),
      () => onAction("emit", makeEvent("paper_library_run_extraction", { paper_ids: paperIds })),
      paperIds.length < 1,
    );
  }

  if (!rows.length) {
    return null;
  }
  const style = {
    left: Math.max(8, Number(menu.x || 0)),
    top: Math.max(8, Number(menu.y || 0)),
  };
  return (
    <div ref={ref} className="paper-tree-menu" style={style} role="menu">
      <div className="paper-tree-menu-title">{nodeTitle(item)}</div>
      {rows.map((row) => row.separator ? (
        <div className="paper-tree-menu-separator" key={row.key} />
      ) : (
        <button
          type="button"
          key={row.key}
          className={row.danger ? "is-danger" : ""}
          disabled={row.disabled}
          onClick={() => {
            if (row.disabled) {
              return;
            }
            row.action();
            onClose();
          }}
        >
          {row.text}
        </button>
      ))}
    </div>
  );
}

function Dialog({ dialog, payload, onClose, onEmit }) {
  const [title, setTitle] = useState(dialog?.title || "");
  const [parentId, setParentId] = useState(dialog?.parent_id || "");
  const [policy, setPolicy] = useState("move_to_parent");
  const [targetId, setTargetId] = useState("");

  useEffect(() => {
    setTitle(dialog?.title || "");
    setParentId(dialog?.parent_id || "");
    setPolicy("move_to_parent");
    setTargetId("");
  }, [dialog]);

  if (!dialog) {
    return null;
  }
  const collections = asArray(payload.sections.find((section) => section.id === "collections")?.items)
    .flatMap((item) => item.type === "collection_root" ? asArray(item.children) : [item]);
  const flatCollections = [];
  const collect = (items, depth = 0) => {
    for (const item of asArray(items)) {
      if (nodeType(item) === "collection") {
        flatCollections.push({ item, depth });
      }
      collect(item.children, depth + 1);
    }
  };
  collect(collections);
  const parentOptions = [{ id: "", title: label(payload.labels, "top_level", "Top level"), depth: 0 }];
  for (const row of flatCollections) {
    if (nodeId(row.item) !== dialog.node_id) {
      parentOptions.push({ id: nodeId(row.item), title: nodeTitle(row.item), depth: row.depth });
    }
  }
  const targetOptions = parentOptions.filter((option) => option.id && option.id !== dialog.node_id);
  const submit = () => {
    if (dialog.kind === "create") {
      onEmit(makeEvent("paper_library_create_collection", { parent_id: parentId, title }));
    } else if (dialog.kind === "rename") {
      onEmit(makeEvent("paper_library_rename_collection", { node_id: dialog.node_id, title }));
    } else if (dialog.kind === "move") {
      onEmit(makeEvent("paper_library_move_collection", { node_id: dialog.node_id, parent_id: parentId }));
    } else if (dialog.kind === "delete") {
      const paperPolicy = policy === "move_to_collection" ? `move_to:${targetId}` : policy;
      onEmit(makeEvent("paper_library_trash_collection", {
        node_id: dialog.node_id,
        paper_policy: paperPolicy,
      }));
    } else if (dialog.kind === "paper-location") {
      onEmit(makeEvent(
        dialog.mode === "add"
          ? "paper_library_add_selected_papers_to_collection"
          : "paper_library_move_selected_papers_to_collection",
        {
          node_id: targetId,
          paper_ids: asArray(dialog.paper_ids).map(cleanText).filter(Boolean),
        },
      ));
    }
    onClose();
  };
  const titleText = {
    create: label(payload.labels, "new_collection", "New collection"),
    rename: label(payload.labels, "rename", "Rename"),
    move: label(payload.labels, "move_collection", "Move collection"),
    delete: label(payload.labels, "delete_collection", "Delete collection"),
    "paper-location": dialog.mode === "add"
      ? label(payload.labels, "add_to_collection", "Add to collection")
      : label(payload.labels, "move_to_collection", "Move to collection"),
  }[dialog.kind] || "";
  const disabled =
    (dialog.kind === "create" && !title.trim()) ||
    (dialog.kind === "rename" && !title.trim()) ||
    (dialog.kind === "delete" && policy === "move_to_collection" && !targetId) ||
    (dialog.kind === "paper-location" && !targetId);
  return (
    <div className="paper-tree-dialog-backdrop" role="presentation">
      <div className="paper-tree-dialog" role="dialog" aria-modal="true">
        <div className="paper-tree-dialog-title">{titleText}</div>
        {dialog.kind === "create" || dialog.kind === "rename" ? (
          <label className="paper-tree-field">
            <span>{label(payload.labels, "collection_title", "Collection title")}</span>
            <input value={title} onChange={(event) => setTitle(event.target.value)} autoFocus />
          </label>
        ) : null}
        {dialog.kind === "create" || dialog.kind === "move" ? (
          <label className="paper-tree-field">
            <span>{label(payload.labels, "parent_collection", "Parent collection")}</span>
            <select value={parentId} onChange={(event) => setParentId(event.target.value)}>
              {parentOptions.map((option) => (
                <option key={option.id || "__root"} value={option.id}>
                  {"  ".repeat(option.depth)}{option.title}
                </option>
              ))}
            </select>
          </label>
        ) : null}
        {dialog.kind === "delete" ? (
          <>
            <div className="paper-tree-dialog-note">{dialog.title}</div>
            <label className="paper-tree-field">
              <span>{label(payload.labels, "paper_policy", "Paper policy")}</span>
              <select value={policy} onChange={(event) => setPolicy(event.target.value)}>
                <option value="move_to_parent">{label(payload.labels, "move_papers_to_parent", "Move papers to parent collection")}</option>
                <option value="move_to_unsorted">{label(payload.labels, "move_papers_to_unsorted", "Move papers to Unsorted Inbox")}</option>
                <option value="move_to_collection">{label(payload.labels, "move_papers_to_collection", "Move papers to collection")}</option>
              </select>
            </label>
            {policy === "move_to_collection" ? (
              <label className="paper-tree-field">
                <span>{label(payload.labels, "target_collection", "Target collection")}</span>
                <select value={targetId} onChange={(event) => setTargetId(event.target.value)}>
                  <option value=""></option>
                  {targetOptions.map((option) => (
                    <option key={option.id} value={option.id}>
                      {"  ".repeat(option.depth)}{option.title}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
          </>
        ) : null}
        {dialog.kind === "paper-location" ? (
          <label className="paper-tree-field">
            <span>{label(payload.labels, "target_collection", "Target collection")}</span>
            <select value={targetId} onChange={(event) => setTargetId(event.target.value)} autoFocus>
              <option value=""></option>
              {parentOptions.map((option) => (
                <option key={option.id || "__unsorted"} value={option.id}>
                  {"  ".repeat(option.depth)}{option.title}
                </option>
              ))}
            </select>
          </label>
        ) : null}
        <div className="paper-tree-dialog-actions">
          <button type="button" onClick={onClose}>{label(payload.labels, "cancel", "Cancel")}</button>
          <button type="button" className="is-primary" disabled={disabled} onClick={submit}>
            {dialog.kind === "delete" ? label(payload.labels, "delete_collection", "Delete collection") : label(payload.labels, "save", "Save")}
          </button>
        </div>
      </div>
    </div>
  );
}

function TreeRow({
  item,
  depth,
  payload,
  expandedIds,
  dragTarget,
  onToggle,
  onSelect,
  onMenu,
  onDropCollection,
  onDragStart,
  onDragTarget,
}) {
  const id = nodeId(item);
  const type = nodeType(item);
  const children = asArray(item.children);
  const hasChildren = children.length > 0;
  const isExpanded = expandedIds.has(id);
  const isActive =
    (type === "view" && !payload.activeNodeId && payload.activeView === id) ||
    ((type === "collection" || type === "collection_root") && payload.activeNodeId === cleanText(item.node_id ?? id));
  const count = item.count === undefined || item.count === null ? "" : cleanText(item.count);
  const draggable = type === "collection";
  const droppable = type === "collection" || type === "collection_root";
  const activeDropPosition = dragTarget?.id === id ? dragTarget.position : "";
  const dropPositionForEvent = (event) => {
    if (type === "collection_root") {
      return "into";
    }
    const rect = event.currentTarget.getBoundingClientRect();
    const y = event.clientY - rect.top;
    if (y < rect.height * 0.28) {
      return "before";
    }
    if (y > rect.height * 0.72) {
      return "after";
    }
    return "into";
  };
  return (
    <>
      <div
        className={`paper-tree-row is-${type} ${isActive ? "is-active" : ""} ${activeDropPosition ? `is-drop-${activeDropPosition}` : ""}`}
        style={{ "--depth": depth }}
        draggable={draggable}
        onDragStart={(event) => {
          if (!draggable) {
            return;
          }
          event.dataTransfer.effectAllowed = "move";
          event.dataTransfer.setData("text/plain", id);
          onDragStart(id);
        }}
        onDragOver={(event) => {
          if (droppable) {
            event.preventDefault();
            event.dataTransfer.dropEffect = "move";
            onDragTarget({ id, position: dropPositionForEvent(event) });
          }
        }}
        onDragLeave={() => {
          if (droppable) {
            onDragTarget(null);
          }
        }}
        onDrop={(event) => {
          if (!droppable) {
            return;
          }
          event.preventDefault();
          const position = dropPositionForEvent(event);
          onDragTarget(null);
          onDropCollection(type === "collection_root" ? "" : id, position, event);
        }}
        onContextMenu={(event) => {
          event.preventDefault();
          onMenu(event, item);
        }}
      >
        <button
          type="button"
          className="paper-tree-toggle"
          disabled={!hasChildren}
          onClick={() => onToggle(id)}
          aria-label={isExpanded ? label(payload.labels, "collapse", "Collapse") : label(payload.labels, "expand", "Expand")}
        >
          {hasChildren ? (isExpanded ? "v" : ">") : ""}
        </button>
        <button type="button" className="paper-tree-main" onClick={() => onSelect(item)}>
          <span className="paper-tree-icon">{type === "view" ? "V" : type === "collection_root" ? "L" : type === "taxonomy" ? "T" : "C"}</span>
          <span className="paper-tree-title">{nodeTitle(item)}</span>
          {count ? <span className="paper-tree-count">{count}</span> : null}
        </button>
        {(type === "collection" || type === "collection_root") ? (
          <button
            type="button"
            className="paper-tree-more"
            onClick={(event) => {
              const rect = event.currentTarget.getBoundingClientRect();
              onMenu({ clientX: rect.left, clientY: rect.bottom + 4, preventDefault() {} }, item);
            }}
            aria-label={label(payload.labels, "collection_actions", "Collection actions")}
          >
            ...
          </button>
        ) : null}
      </div>
      {hasChildren && isExpanded ? children.map((child) => (
        <TreeRow
          key={nodeId(child)}
          item={child}
          depth={depth + 1}
          payload={payload}
          expandedIds={expandedIds}
          dragTarget={dragTarget}
          onToggle={onToggle}
          onSelect={onSelect}
          onMenu={onMenu}
          onDropCollection={onDropCollection}
          onDragStart={onDragStart}
          onDragTarget={onDragTarget}
        />
      )) : null}
    </>
  );
}

function Section({
  section,
  payload,
  expanded,
  dragTarget,
  onToggle,
  onSelect,
  onMenu,
  onDialog,
  onDropCollection,
  onDragStart,
  onDragTarget,
}) {
  const [open, setOpen] = useState(true);
  const items = asArray(section.items);
  return (
    <section className={`paper-tree-section is-${section.id || ""}`}>
      <div className="paper-tree-section-head">
        <button type="button" className="paper-tree-section-toggle" onClick={() => setOpen(!open)}>
          {open ? "v" : ">"}
        </button>
        <span>{cleanText(section.title || section.id)}</span>
        {section.id === "collections" ? (
          <button
            type="button"
            className="paper-tree-head-action"
            onClick={() => onDialog({ kind: "create", parent_id: "" })}
            aria-label={label(payload.labels, "new_collection", "New collection")}
          >
            +
          </button>
        ) : null}
      </div>
      {open ? (
        <div className="paper-tree-section-items">
          {items.map((item) => (
            <TreeRow
              key={nodeId(item)}
              item={item}
              depth={0}
              payload={payload}
              expandedIds={expanded}
              dragTarget={dragTarget}
              onToggle={onToggle}
              onSelect={onSelect}
              onMenu={onMenu}
              onDropCollection={onDropCollection}
              onDragStart={onDragStart}
              onDragTarget={onDragTarget}
            />
          ))}
        </div>
      ) : null}
    </section>
  );
}

function PaperList({
  payload,
  selectedPaperIds,
  setSelectedPaperIds,
  setDragPayload,
  emit,
  onPaperMenu,
}) {
  const papers = asArray(payload.papers);
  const selected = selectedPaperIds;
  const allSelected = papers.length > 0 && papers.every((paper) => selected.has(cleanText(paper.id)));
  const togglePaper = (paperId, checked) => {
    const next = new Set(selected);
    if (checked) {
      next.add(paperId);
    } else {
      next.delete(paperId);
    }
    setSelectedPaperIds(next);
  };
  const toggleAll = () => {
    if (allSelected) {
      setSelectedPaperIds(new Set());
    } else {
      setSelectedPaperIds(new Set(papers.map((paper) => cleanText(paper.id)).filter(Boolean)));
    }
  };
  return (
    <main className="paper-list-pane">
      <div className="paper-list-head">
        <div>
          <div className="paper-list-title">{payload.activeLabel || label(payload.labels, "papers", "Papers")}</div>
          <div className="paper-list-caption">
            {label(payload.labels, "library_result_count", "{count} papers").replace("{count}", papers.length)}
          </div>
        </div>
        <button type="button" className="paper-list-select-all" onClick={toggleAll} disabled={!papers.length}>
          {allSelected ? label(payload.labels, "clear_selection", "Clear") : label(payload.labels, "select_all", "Select all")}
        </button>
      </div>
      {!papers.length ? (
        <div className="paper-list-empty">{label(payload.labels, "library_empty", "No papers match this view.")}</div>
      ) : (
        <div className="paper-card-list">
          {papers.map((paper) => {
            const paperId = cleanText(paper.id);
            const isSelected = selected.has(paperId);
            const isActive = payload.detailId === paperId;
            const dragIds = isSelected ? [...selected] : [paperId];
            return (
              <article
                key={paperId}
                data-paper-id={paperId}
                className={`paper-list-card ${isActive ? "is-active" : ""} ${isSelected ? "is-selected" : ""}`}
                draggable
                onContextMenu={(event) => {
                  event.preventDefault();
                  onPaperMenu(event, paper, dragIds);
                }}
                onDragStart={(event) => {
                  event.dataTransfer.effectAllowed = "move";
                  event.dataTransfer.setData("text/plain", dragIds.join("\n"));
                  setDragPayload({ kind: "papers", paperIds: dragIds, append: event.altKey || event.shiftKey });
                }}
                onDragEnd={() => setDragPayload(null)}
              >
                <label className="paper-card-check">
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={(event) => togglePaper(paperId, event.target.checked)}
                    aria-label={label(payload.labels, "select_paper", "Select paper")}
                  />
                </label>
                <button
                  type="button"
                  className="paper-card-body"
                  onClick={() => emit(makeEvent("paper_library_select_paper", { source_id: paperId }))}
                >
                  <span className="paper-card-title">{cleanText(paper.title || paperId)}</span>
                  {paper.meta ? <span className="paper-card-meta">{cleanText(paper.meta)}</span> : null}
                  {paper.summary ? <span className="paper-card-summary">{cleanText(paper.summary)}</span> : null}
                  <span className="paper-card-badges">
                    {asArray(paper.badges).slice(0, 5).map((badge) => (
                      <span key={cleanText(badge)}>{cleanText(badge)}</span>
                    ))}
                  </span>
                  {paper.metrics ? <span className="paper-card-metrics">{cleanText(paper.metrics)}</span> : null}
                </button>
              </article>
            );
          })}
        </div>
      )}
    </main>
  );
}

function App() {
  const [args, setArgs] = useState({});
  const [query, setQuery] = useState("");
  const [expanded, setExpanded] = useState(new Set());
  const [selectedPaperIds, setSelectedPaperIds] = useState(new Set());
  const [menu, setMenu] = useState(null);
  const [dialog, setDialog] = useState(null);
  const [dragPayload, setDragPayload] = useState(null);
  const [dragTarget, setDragTarget] = useState(null);
  const payload = useMemo(() => normalizePayload(args.payload), [args.payload]);
  const activePayload = useMemo(
    () => ({ ...payload, selectedPaperIds: [...selectedPaperIds] }),
    [payload, selectedPaperIds],
  );
  const filteredSections = useMemo(() => {
    return payload.sections.map((section) => ({
      ...section,
      items: filterItems(section.items, query),
    }));
  }, [payload.sections, query]);

  useEffect(() => {
    Streamlit.setComponentReady();
    const onRender = (event) => {
      setArgs(event.detail.args || {});
    };
    Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender);
    Streamlit.setFrameHeight();
    return () => {
      Streamlit.events.removeEventListener(Streamlit.RENDER_EVENT, onRender);
    };
  }, []);

  useEffect(() => {
    setSelectedPaperIds(new Set(payload.selectedPaperIds));
  }, [payload.selectedPaperIds.join("\u0000")]);

  useEffect(() => {
    const ids = new Set();
    for (const section of payload.sections) {
      for (const id of expandableIds(section.items)) {
        ids.add(id);
      }
    }
    setExpanded(ids);
  }, [payload.sections]);

  useEffect(() => {
    window.setTimeout(() => Streamlit.setFrameHeight(), 0);
  }, [filteredSections, menu, dialog, expanded]);

  const emit = (event) => {
    Streamlit.setComponentValue(event);
    window.setTimeout(() => Streamlit.setFrameHeight(), 0);
  };
  const handleSelect = (item) => {
    const type = nodeType(item);
    if (type === "view") {
      emit(makeEvent("paper_library_select_view", { view_id: nodeId(item) }));
    } else if (type === "collection" || type === "collection_root") {
      emit(makeEvent("paper_library_select_collection", {
        node_id: type === "collection_root" ? "" : nodeId(item),
      }));
    }
  };
  const handleAction = (kind, data) => {
    if (kind === "emit") {
      emit(data);
      return;
    }
    if (kind.startsWith("dialog:")) {
      setDialog({ kind: kind.split(":", 2)[1], ...data });
    }
  };
  const dropCollection = (targetId, position = "into", event = null) => {
    if (!dragPayload) {
      return;
    }
    if (dragPayload.kind === "collection") {
      if (!dragPayload.nodeId || dragPayload.nodeId === targetId) {
        return;
      }
      const eventPayload = {
        node_id: dragPayload.nodeId,
      };
      if (position === "before") {
        eventPayload.before_node_id = targetId;
      } else if (position === "after") {
        eventPayload.after_node_id = targetId;
      } else {
        eventPayload.parent_id = targetId;
      }
      emit(makeEvent("paper_library_move_collection", eventPayload));
    } else if (dragPayload.kind === "papers") {
      const paperIds = asArray(dragPayload.paperIds).map(cleanText).filter(Boolean);
      if (!paperIds.length) {
        return;
      }
      emit(makeEvent("paper_library_drop_papers_to_collection", {
        node_id: targetId,
        paper_ids: paperIds,
        append: Boolean(dragPayload.append || event?.altKey || event?.shiftKey),
      }));
    }
    setDragPayload(null);
    setDragTarget(null);
  };

  const liveSelectedCount = selectedPaperIds.size;
  const hasPapers = payload.papers.length > 0 || args.payload?.papers;
  const treePane = (
    <>
      <div className="paper-tree-toolbar">
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={label(payload.labels, "search_collections", "Search collections")}
        />
        <button type="button" onClick={() => {
          const ids = new Set();
          for (const section of payload.sections) {
            for (const id of expandableIds(section.items)) {
              ids.add(id);
            }
          }
          setExpanded(ids);
        }}>
          {label(payload.labels, "expand_all", "Expand all")}
        </button>
        <button type="button" onClick={() => setExpanded(new Set())}>
          {label(payload.labels, "collapse_all", "Collapse all")}
        </button>
      </div>
      {liveSelectedCount ? (
        <div className="paper-tree-selection">
          {label(payload.labels, "selected_papers", "{count} papers selected").replace("{count}", liveSelectedCount)}
        </div>
      ) : null}
      <div className="paper-tree-sections">
        {filteredSections.map((section) => (
          <Section
            key={section.id || section.title}
            section={section}
            payload={activePayload}
            expanded={expanded}
            dragTarget={dragTarget}
            onToggle={(id) => {
              const next = new Set(expanded);
              if (next.has(id)) {
                next.delete(id);
              } else {
                next.add(id);
              }
              setExpanded(next);
            }}
            onSelect={handleSelect}
            onMenu={(event, item) => setMenu({ item, x: event.clientX, y: event.clientY })}
            onDialog={setDialog}
            onDropCollection={dropCollection}
            onDragStart={(nodeIdValue) => setDragPayload({ kind: "collection", nodeId: nodeIdValue })}
            onDragTarget={setDragTarget}
          />
        ))}
      </div>
    </>
  );
  return (
    <div className={`paper-tree-shell ${hasPapers ? "has-papers" : ""}`}>
      {hasPapers ? (
        <div className="paper-workbench">
          <aside className="paper-tree-pane">{treePane}</aside>
          <PaperList
            payload={payload}
            selectedPaperIds={selectedPaperIds}
            setSelectedPaperIds={setSelectedPaperIds}
            setDragPayload={setDragPayload}
            emit={emit}
            onPaperMenu={(event, paper, paperIds) => setMenu({
              item: { ...paper, type: "paper" },
              paperIds,
              x: event.clientX,
              y: event.clientY,
            })}
          />
        </div>
      ) : treePane}
      <ContextMenu
        menu={menu}
        payload={activePayload}
        onClose={() => setMenu(null)}
        onAction={handleAction}
      />
      <Dialog
        dialog={dialog}
        payload={payload}
        onClose={() => setDialog(null)}
        onEmit={emit}
      />
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
