import React, { useCallback, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { Streamlit, withStreamlitConnection } from "streamlit-component-lib";
import "./style.css";

const DEFAULT_ORDER = ["todo", "doing", "blocked", "done"];

const DEFAULT_LABELS = {
  add: "Add",
  ai_done_ingest: "Ingest Done",
  ai_gap_ingest: "Ingest Gaps",
  ai_subtask_ingest: "Ingest Subtasks",
  blocked: "Blocked",
  cancel: "Cancel",
  context: "Context",
  crystallized: "Crystallized",
  details: "Details",
  done: "Done",
  done_uncrystallized: "Done, not crystallized",
  doing: "Doing",
  edit: "Edit",
  empty_column: "No cards",
  links: "Links",
  new_card: "New card",
  notes: "Notes",
  outcome: "Outcome",
  quick_add: "Quick Add",
  save: "Save",
  subtasks: "Subtasks",
  title: "Title",
  todo: "To do",
  untitled: "Untitled",
  why: "Why",
};

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function asObject(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : {};
}

function cleanText(value) {
  return value === null || value === undefined ? "" : String(value);
}

function label(labels, key, fallback = "") {
  return cleanText(labels[key] || DEFAULT_LABELS[key] || fallback || key);
}

function cardId(card, fallback) {
  return cleanText(card.id || card.task_id || card.key || fallback);
}

function normalizeSubtask(item, index) {
  if (typeof item === "string") {
    return { id: `subtask-${index}`, title: item, done: false };
  }
  const source = asObject(item);
  return {
    ...source,
    id: cleanText(source.id || source.key || `subtask-${index}`),
    title: cleanText(source.title || source.text || source.name || ""),
    done: Boolean(source.done || source.completed || source.checked),
  };
}

function normalizeLink(item, index) {
  if (typeof item === "string") {
    return { id: `link-${index}`, label: item, url: item };
  }
  const source = asObject(item);
  return {
    ...source,
    id: cleanText(source.id || source.key || source.url || `link-${index}`),
    label: cleanText(source.label || source.title || source.name || source.url || ""),
    url: cleanText(source.url || source.href || source.path || ""),
  };
}

function normalizeCard(raw, sectionKey, index) {
  const source = asObject(raw);
  const id = cardId(source, `${sectionKey}-${index}`);
  return {
    ...source,
    id,
    section: cleanText(source.section || source.status || sectionKey),
    title: cleanText(source.title || source.name || source.summary || DEFAULT_LABELS.untitled),
    context: cleanText(source.context || source.description || source.subtitle || ""),
    why: cleanText(source.why || ""),
    outcome: cleanText(source.outcome || ""),
    notes: cleanText(source.notes || source.body || ""),
    crystallized: Boolean(source.crystallized),
    subtasks: asArray(source.subtasks).map(normalizeSubtask),
    links: asArray(source.links || source.evidence || source.refs).map(normalizeLink),
  };
}

function normalizeSections(rawSections, rawLabels, settings) {
  const labels = asObject(rawLabels);
  const configuredOrder = asArray(settings.section_order || settings.sections)
    .map(cleanText)
    .filter(Boolean);
  const order = configuredOrder.length ? configuredOrder.slice(0, 4) : DEFAULT_ORDER;

  if (Array.isArray(rawSections)) {
    const source = rawSections.slice(0, 4);
    return source.map((section, sectionIndex) => {
      const object = asObject(section);
      const key = cleanText(object.key || object.id || object.section || order[sectionIndex]);
      return {
        key,
        label: cleanText(object.label || object.title || labels[key] || label(labels, key)),
        cards: asArray(object.cards || object.tasks || object.items).map((card, index) =>
          normalizeCard(card, key, index),
        ),
      };
    });
  }

  const source = asObject(rawSections);
  return order.map((key) => ({
    key,
    label: label(labels, key),
    cards: asArray(source[key]).map((card, index) => normalizeCard(card, key, index)),
  }));
}

function findCard(sections, cardIdValue) {
  for (const section of sections) {
    const card = section.cards.find((item) => item.id === cardIdValue);
    if (card) {
      return card;
    }
  }
  return null;
}

function boardSnapshot(sections) {
  return sections.map((section) => ({
    section: section.key,
    task_ids: section.cards.map((card) => card.id),
  }));
}

function moveCard(sections, cardIdValue, targetSectionKey) {
  let moved = null;
  const without = sections.map((section) => ({
    ...section,
    cards: section.cards.filter((card) => {
      if (card.id !== cardIdValue) {
        return true;
      }
      moved = { ...card, section: targetSectionKey };
      return false;
    }),
  }));
  if (!moved) {
    return sections;
  }
  return without.map((section) =>
    section.key === targetSectionKey
      ? { ...section, cards: [...section.cards, moved] }
      : section,
  );
}

function QuickAdd({ labels, section, onEvent }) {
  const [title, setTitle] = useState("");
  const submit = useCallback(
    (event) => {
      event.preventDefault();
      const cleanTitle = title.trim();
      if (!cleanTitle) {
        return;
      }
      onEvent("quick_add", { section: section.key, title: cleanTitle });
      setTitle("");
    },
    [onEvent, section.key, title],
  );

  return (
    <form className="quick-add" onSubmit={submit}>
      <input
        aria-label={`${label(labels, "quick_add")} ${section.label}`}
        value={title}
        onChange={(event) => setTitle(event.target.value)}
        placeholder={label(labels, "new_card")}
      />
      <button type="submit" title={label(labels, "add")}>
        +
      </button>
    </form>
  );
}

function Card({ card, labels, selected, onSelect, onDragStart }) {
  const doneSubtasks = card.subtasks.filter((item) => item.done).length;
  return (
    <button
      type="button"
      className={`card${selected ? " selected" : ""}${card.crystallized ? " crystallized" : ""}`}
      draggable
      onClick={() => onSelect(card.id)}
      onDragStart={(event) => onDragStart(event, card.id)}
    >
      <span className="card-title">{card.title || label(labels, "untitled")}</span>
      {card.context ? <span className="card-context">{card.context}</span> : null}
      <span className="card-meta">
        {card.subtasks.length ? (
          <span>{`${doneSubtasks}/${card.subtasks.length} ${label(labels, "subtasks")}`}</span>
        ) : null}
        {card.links.length ? <span>{`${card.links.length} ${label(labels, "links")}`}</span> : null}
        {card.crystallized ? <span>{label(labels, "crystallized")}</span> : null}
      </span>
    </button>
  );
}

function Column({ section, labels, selectedId, onSelect, onEvent, onDropCard }) {
  const [over, setOver] = useState(false);
  return (
    <section
      className={`column${over ? " drop-over" : ""}`}
      onDragOver={(event) => {
        event.preventDefault();
        setOver(true);
      }}
      onDragLeave={() => setOver(false)}
      onDrop={(event) => {
        event.preventDefault();
        setOver(false);
        onDropCard(event.dataTransfer.getData("text/plain"), section.key);
      }}
    >
      <header className="column-header">
        <h2>{section.label}</h2>
        <span>{section.cards.length}</span>
      </header>
      <QuickAdd labels={labels} section={section} onEvent={onEvent} />
      <div className="card-list">
        {section.cards.length ? (
          section.cards.map((card) => (
            <Card
              key={card.id}
              card={card}
              labels={labels}
              selected={selectedId === card.id}
              onSelect={onSelect}
              onDragStart={(event, id) => event.dataTransfer.setData("text/plain", id)}
            />
          ))
        ) : (
          <div className="empty-column">{label(labels, "empty_column")}</div>
        )}
      </div>
    </section>
  );
}

function DetailPanel({ card, labels, onEvent }) {
  const [draft, setDraft] = useState(card || {});

  useEffect(() => {
    setDraft(card || {});
  }, [card]);

  if (!card) {
    return (
      <aside className="detail-panel">
        <h2>{label(labels, "details")}</h2>
        <p className="muted">{label(labels, "empty_column")}</p>
      </aside>
    );
  }

  const update = (key, value) => setDraft((current) => ({ ...current, [key]: value }));
  const save = () => onEvent("edit_card", { card_id: card.id, card: draft });

  return (
    <aside className="detail-panel">
      <div className="detail-head">
        <h2>{label(labels, "details")}</h2>
        <button type="button" onClick={save}>
          {label(labels, "save")}
        </button>
      </div>
      <label>
        <span>{label(labels, "title")}</span>
        <input value={cleanText(draft.title)} onChange={(event) => update("title", event.target.value)} />
      </label>
      <label>
        <span>{label(labels, "context")}</span>
        <textarea value={cleanText(draft.context)} onChange={(event) => update("context", event.target.value)} />
      </label>
      <div className="field-grid">
        <label>
          <span>{label(labels, "why")}</span>
          <textarea value={cleanText(draft.why)} onChange={(event) => update("why", event.target.value)} />
        </label>
        <label>
          <span>{label(labels, "outcome")}</span>
          <textarea value={cleanText(draft.outcome)} onChange={(event) => update("outcome", event.target.value)} />
        </label>
      </div>
      <label>
        <span>{label(labels, "notes")}</span>
        <textarea value={cleanText(draft.notes)} onChange={(event) => update("notes", event.target.value)} />
      </label>
      <div className="subtasks">
        <h3>{label(labels, "subtasks")}</h3>
        {card.subtasks.map((item) => (
          <label className="check-row" key={item.id}>
            <input
              type="checkbox"
              checked={item.done}
              onChange={(event) =>
                onEvent("toggle_subtask", {
                  card_id: card.id,
                  subtask_id: item.id,
                  done: event.target.checked,
                })
              }
            />
            <span>{item.title}</span>
          </label>
        ))}
      </div>
      <div className="links">
        <h3>{label(labels, "links")}</h3>
        <div className="chips">
          {card.links.map((item) => (
            <a key={item.id} href={item.url || undefined} target="_blank" rel="noreferrer" className="chip">
              {item.label || item.url}
            </a>
          ))}
        </div>
      </div>
    </aside>
  );
}

function AiBar({ labels, aiState, onEvent }) {
  const state = asObject(aiState);
  return (
    <div className="ai-bar">
      <button type="button" onClick={() => onEvent("ai_gap_ingest", { source: "button" })}>
        {label(labels, "ai_gap_ingest")}
      </button>
      <button type="button" onClick={() => onEvent("ai_subtask_ingest", { source: "button" })}>
        {label(labels, "ai_subtask_ingest")}
      </button>
      <button type="button" onClick={() => onEvent("ai_done_ingest", { source: "button" })}>
        {label(labels, "ai_done_ingest")}
      </button>
      {state.status ? <span className="ai-status">{cleanText(state.status)}</span> : null}
    </div>
  );
}

function DoneUncrystallized({ labels, cards, onEvent }) {
  if (!cards.length) {
    return null;
  }
  return (
    <section className="done-uncrystallized">
      <h2>{label(labels, "done_uncrystallized")}</h2>
      <div className="chips">
        {cards.map((card) => (
          <button
            key={card.id}
            type="button"
            className="chip action-chip"
            onClick={() => onEvent("crystallize_card", { card_id: card.id })}
          >
            {card.title}
          </button>
        ))}
      </div>
    </section>
  );
}

function KanbanBoard(props) {
  const args = asObject(props.args);
  const payload = { ...args, ...asObject(args.payload) };
  const labels = asObject(payload.labels);
  const settings = asObject(payload.settings);
  const height = Number(args.height || 760);
  const normalized = useMemo(
    () => normalizeSections(payload.sections, labels, settings),
    [payload.sections, labels, settings],
  );
  const [sections, setSections] = useState(normalized);
  const [selectedId, setSelectedId] = useState("");

  useEffect(() => {
    setSections(normalized);
    setSelectedId((current) => current || normalized[0]?.cards[0]?.id || "");
  }, [normalized]);

  useEffect(() => {
    Streamlit.setFrameHeight(Math.max(420, height));
  }, [height, sections, selectedId]);

  const selectedCard = findCard(sections, selectedId);
  const doneUncrystallized = sections
    .find((section) => section.key === "done")
    ?.cards.filter((card) => !card.crystallized) || [];

  const sendEvent = useCallback(
    (action, payload = {}) => {
      Streamlit.setComponentValue({
        action,
        payload,
        sections: boardSnapshot(sections),
        ui: { selected_card_id: selectedId },
      });
    },
    [sections, selectedId],
  );

  const dropCard = useCallback(
    (cardIdValue, targetSection) => {
      if (!cardIdValue || !targetSection) {
        return;
      }
      const before = findCard(sections, cardIdValue);
      if (!before || before.section === targetSection) {
        return;
      }
      const next = moveCard(sections, cardIdValue, targetSection);
      setSections(next);
      Streamlit.setComponentValue({
        action: "move_card",
        payload: {
          card_id: cardIdValue,
          from_section: before.section,
          to_section: targetSection,
        },
        sections: boardSnapshot(next),
        ui: { selected_card_id: cardIdValue },
      });
    },
    [sections],
  );

  return (
    <main className="kanban-shell" style={{ minHeight: `${Math.max(420, height - 12)}px` }}>
      <AiBar labels={labels} aiState={payload.ai_state} onEvent={sendEvent} />
      <div className="board-layout">
        <div className="columns">
          {sections.map((section) => (
            <Column
              key={section.key}
              section={section}
              labels={labels}
              selectedId={selectedId}
              onSelect={setSelectedId}
              onEvent={sendEvent}
              onDropCard={dropCard}
            />
          ))}
        </div>
        <DetailPanel card={selectedCard} labels={labels} onEvent={sendEvent} />
      </div>
      <DoneUncrystallized labels={labels} cards={doneUncrystallized} onEvent={sendEvent} />
    </main>
  );
}

const ConnectedKanbanBoard = withStreamlitConnection(KanbanBoard);

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <ConnectedKanbanBoard />
  </React.StrictMode>,
);
