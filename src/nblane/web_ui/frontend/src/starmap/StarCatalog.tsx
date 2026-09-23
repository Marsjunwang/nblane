/* 星表面板 (star catalog) — the management channel of the home starmap
 * (design home-starmap-enhancements §2, 王军裁决版): 北极星 + all goal stars
 * grouped 进行中 / 暂停 / 已镌刻. The panel stays open while a row is
 * selected (the detail card on the right updates live); ↑/↓ (or j/k) moves
 * the row highlight with wrap-around, Enter focuses the star + opens the
 * card, and clicking a star on the chart highlights + scrolls to the
 * matching row here. Esc (handled by StarmapView) is the one-key return to
 * the pure chart. Opened by the pale-gold「+」seal button in the corner. */
import { useEffect, useMemo, useRef, useState } from 'react';

import { useCreateGoal } from '../api/hooks';
import type { StarmapSelection } from './StarmapScene';
import type { SnapshotGoal, StarmapSnapshot } from './snapshot';

export interface StarCatalogProps {
  open: boolean;
  snapshot: StarmapSnapshot;
  profile: string;
  /** Chart-side selection, for chart → catalog highlight sync. */
  selection: StarmapSelection | null;
  /** focusStar + open the inscription card (scene-side contract). */
  onFocus: (id: string) => void;
}

export interface CatalogRow {
  id: string;
  goal?: SnapshotGoal;
}

const SECTIONS: { key: string; title: string; match: (g: SnapshotGoal) => boolean }[] = [
  { key: 'active', title: '进行中', match: (g) => g.status === 'active' },
  { key: 'paused', title: '暂停', match: (g) => g.status === 'paused' },
  { key: 'carved', title: '已镌刻', match: (g) => g.status === 'completed' },
];

/** Flattened row order (北极星 first, then goals in section order) — the
 * keyboard selection walks this list. */
export function catalogRows(snapshot: StarmapSnapshot): CatalogRow[] {
  const rows: CatalogRow[] = [{ id: 'north' }];
  for (const sec of SECTIONS) {
    for (const g of snapshot.goals.filter(sec.match)) rows.push({ id: g.id, goal: g });
  }
  return rows;
}

/** Wrap-around index step for ↑/↓ navigation. */
export function wrapIndex(len: number, cur: number, delta: number): number {
  if (len <= 0) return -1;
  const i = cur < 0 ? 0 : cur;
  return (((i + delta) % len) + len) % len;
}

const HINT_SESSION_KEY = 'nblane-starmap-catalog-hint-seen';

export function StarCatalog({ open, snapshot, profile, selection, onFocus }: StarCatalogProps) {
  const [creating, setCreating] = useState(false);
  const [createdNote, setCreatedNote] = useState('');
  const [activeId, setActiveId] = useState<string>('north');
  const [showHint, setShowHint] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const createGoal = useCreateGoal(profile);

  const rows = useMemo(() => catalogRows(snapshot), [snapshot]);

  const northLabel = snapshot.north.is_set
    ? snapshot.north.brief || snapshot.north.full || '北极星'
    : '虚位 · 点击立星';

  const focus = (id: string) => {
    setActiveId(id);
    onFocus(id);
  };

  // Chart → catalog: a star clicked on the disc highlights (and scrolls to)
  // its row; non-catalog kinds (planet/guest/skill) leave the highlight.
  useEffect(() => {
    if (!open || !selection) return;
    const id =
      selection.kind === 'north' ? 'north' : selection.kind === 'goal' ? selection.id : null;
    if (id && rows.some((r) => r.id === id)) setActiveId(id);
  }, [open, selection, rows]);

  // Keep the highlighted row in view.
  useEffect(() => {
    if (!open || !activeId) return;
    rootRef.current
      ?.querySelector(`[data-catalog-id="${CSS.escape(activeId)}"]`)
      ?.scrollIntoView?.({ block: 'nearest' });
  }, [open, activeId]);

  // Keyboard: ↑/↓ (j/k) moves the highlight with wrap, Enter opens the card.
  // Esc is owned by StarmapView (one-key return to the pure chart).
  useEffect(() => {
    if (!open || creating) return;
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      if (target && /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName)) return;
      const delta =
        e.key === 'ArrowDown' || e.key === 'j' ? 1 : e.key === 'ArrowUp' || e.key === 'k' ? -1 : 0;
      if (delta !== 0) {
        e.preventDefault();
        const idx = rows.findIndex((r) => r.id === activeId);
        const next = rows[wrapIndex(rows.length, idx, delta)];
        if (next) setActiveId(next.id);
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (activeId && rows.some((r) => r.id === activeId)) onFocus(activeId);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, creating, rows, activeId, onFocus]);

  // One-time 2s fading hint bar on the catalog's first open (per session).
  useEffect(() => {
    if (!open) return;
    try {
      if (sessionStorage.getItem(HINT_SESSION_KEY)) return;
      sessionStorage.setItem(HINT_SESSION_KEY, '1');
    } catch {
      /* storage blocked: show the hint anyway, it is harmless */
    }
    setShowHint(true);
    const t = window.setTimeout(() => setShowHint(false), 2600);
    return () => window.clearTimeout(t);
  }, [open]);

  return (
    <div
      className={`starmap-catalog${open ? ' open' : ''}`}
      ref={rootRef}
      data-starmap-ui
      data-testid="starmap-catalog"
      aria-hidden={!open}
    >
      {open && (
        <>
          <h3>星表</h3>
          {showHint && (
            <p className="starmap-catalog-hintbar" data-testid="catalog-hintbar">
              <kbd>↑</kbd>
              <kbd>↓</kbd> 移动 · <kbd>Enter</kbd> 开卡 · <kbd>Esc</kbd> 回纯图
            </p>
          )}
          <div className="starmap-catalog-section" data-testid="catalog-north">
            <h4>北极星</h4>
            <CatalogRowButton
              id="north"
              active={activeId === 'north'}
              className={snapshot.north.is_set ? '' : ' vacant'}
              title={northLabel}
              sub={snapshot.north.visibility === 'public' ? '可公开' : '仅本地'}
              onFocus={focus}
            />
          </div>
          {SECTIONS.map((sec) => {
            const goals = snapshot.goals.filter(sec.match);
            return (
              <div
                className="starmap-catalog-section"
                key={sec.key}
                data-testid={`catalog-${sec.key}`}
              >
                <h4>
                  {sec.title}
                  {goals.length > 0 && <span className="sec-count">{goals.length}</span>}
                </h4>
                {goals.length === 0 && sec.key === 'active' && (
                  <p className="starmap-catalog-empty">恒星虚位 — 自下方新增目标。</p>
                )}
                {goals.map((g) => (
                  <CatalogRowButton
                    key={g.id}
                    id={g.id}
                    active={activeId === g.id}
                    className={g.status === 'completed' ? ' carved' : ''}
                    title={g.title}
                    sub={g.target || ''}
                    onFocus={focus}
                  />
                ))}
              </div>
            );
          })}
          {!creating && (
            <button
              type="button"
              className="starmap-catalog-add"
              onClick={() => {
                setCreatedNote('');
                setCreating(true);
              }}
              data-testid="catalog-add-goal"
            >
              ＋ 新增目标
            </button>
          )}
          {creating && (
            <GoalCreateForm
              saving={createGoal.isPending}
              error={createGoal.error}
              onCancel={() => setCreating(false)}
              onSubmit={(body) =>
                createGoal.mutate(body, {
                  onSuccess: (res) => {
                    setCreating(false);
                    setCreatedNote(`「${res.goal.title || res.goal.id}」已入星表`);
                  },
                })
              }
            />
          )}
          {createdNote && <p className="starmap-catalog-note">{createdNote}</p>}
        </>
      )}
    </div>
  );
}

function CatalogRowButton({
  id,
  active,
  className,
  title,
  sub,
  onFocus,
}: {
  id: string;
  active: boolean;
  className: string;
  title: string;
  sub: string;
  onFocus: (id: string) => void;
}) {
  return (
    <button
      type="button"
      className={`starmap-catalog-row${active ? ' active' : ''}${className}`}
      onClick={() => onFocus(id)}
      data-catalog-id={id}
      data-testid={`catalog-row-${id}`}
    >
      <span className="row-title">{title}</span>
      <span className="row-sub">{sub}</span>
      <kbd className="row-kbd">Enter</kbd>
    </button>
  );
}

function GoalCreateForm({
  saving,
  error,
  onSubmit,
  onCancel,
}: {
  saving: boolean;
  error: Error | null;
  onSubmit: (body: { title: string; summary: string; target: string }) => void;
  onCancel: () => void;
}) {
  const [title, setTitle] = useState('');
  const [summary, setSummary] = useState('');
  const [target, setTarget] = useState('');
  return (
    <div className="starmap-edit starmap-catalog-form" data-testid="catalog-goal-form">
      <label>
        <span>标题</span>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="新恒星之名"
          data-testid="create-goal-title"
        />
      </label>
      <label>
        <span>摘要</span>
        <textarea
          value={summary}
          onChange={(e) => setSummary(e.target.value)}
          rows={2}
          data-testid="create-goal-summary"
        />
      </label>
      <label>
        <span>目标日期</span>
        <input
          type="date"
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          data-testid="create-goal-target"
        />
      </label>
      {error && (
        <p className="starmap-edit-error" role="alert">
          {error.message}
        </p>
      )}
      <div className="starmap-edit-actions">
        <button
          type="button"
          className="starmap-save"
          disabled={saving || !title.trim()}
          onClick={() => onSubmit({ title: title.trim(), summary: summary.trim(), target })}
          data-testid="create-goal-save"
        >
          {saving ? '镌刻中…' : '落印'}
        </button>
        <button type="button" className="starmap-cancel" disabled={saving} onClick={onCancel}>
          收起刻刀
        </button>
      </div>
    </div>
  );
}
