/* 铭文卡 (inscription detail card) — read mode + 重刻 edit mode for the pole
 * star (北极星) and goal stars (恒星), per docs/zh/dev/home-editing-starmap-design.md
 * §2. The edit mode stays inside the inscription card visual (dark ground,
 * hairline gold); saving ends with a 落印 seal micro-animation and the
 * starmap refreshes in place via query invalidation. */
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { usePatchGoal, usePatchNorthStar } from '../api/hooks';
import type { StarmapSelection } from './StarmapScene';
import { goalStatusLabel, type StarmapSnapshot } from './snapshot';

const GOAL_STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: 'active', label: '进行中' },
  { value: 'paused', label: '暂停' },
  { value: 'completed', label: '已镌刻' },
];

export interface InscriptionCardProps {
  selection: StarmapSelection;
  snapshot: StarmapSnapshot;
  profile: string;
  /** Replace the open card's contents after a successful 重刻 (the scene
   * refreshes itself via invalidation; this keeps the card truthful in the
   * meantime). */
  onSaved: (selection: StarmapSelection) => void;
}

export function InscriptionCard({ selection, snapshot, profile, onSaved }: InscriptionCardProps) {
  const editable = selection.kind === 'north' || selection.kind === 'goal';
  // 虚位空星: clicking the vacant pole opens the card straight in edit mode.
  const [editing, setEditing] = useState(
    selection.kind === 'north' && !snapshot.north.is_set,
  );
  const [sealed, setSealed] = useState(false);
  const patchNorthStar = usePatchNorthStar(profile);
  const patchGoal = usePatchGoal(profile);

  const goal =
    selection.kind === 'goal'
      ? snapshot.goals.find((g) => g.id === selection.id)
      : undefined;

  // North-star draft state
  const [full, setFull] = useState(snapshot.north.full);
  const [brief, setBrief] = useState(snapshot.north.brief);
  const [visibility, setVisibility] = useState(
    snapshot.north.visibility === 'public' ? 'public' : 'private',
  );
  // Goal draft state
  const [title, setTitle] = useState(goal?.title ?? '');
  const [summary, setSummary] = useState(goal?.summary ?? '');
  const [start, setStart] = useState(goal?.start ?? '');
  const [target, setTarget] = useState(goal?.target ?? '');
  const [status, setStatus] = useState(goal?.status ?? 'active');

  // Re-seed the drafts when the underlying data refreshes (post-save
  // invalidation) or another star is selected with the same key.
  useEffect(() => {
    setFull(snapshot.north.full);
    setBrief(snapshot.north.brief);
    setVisibility(snapshot.north.visibility === 'public' ? 'public' : 'private');
  }, [snapshot.north.full, snapshot.north.brief, snapshot.north.visibility]);
  useEffect(() => {
    setTitle(goal?.title ?? '');
    setSummary(goal?.summary ?? '');
    setStart(goal?.start ?? '');
    setTarget(goal?.target ?? '');
    setStatus(goal?.status ?? 'active');
  }, [goal?.id, goal?.title, goal?.summary, goal?.start, goal?.target, goal?.status]);

  const saving = patchNorthStar.isPending || patchGoal.isPending;
  const saveError = patchNorthStar.error ?? patchGoal.error;

  const sealThen = (next: StarmapSelection) => {
    setSealed(true);
    window.setTimeout(() => {
      setSealed(false);
      setEditing(false);
      onSaved(next);
    }, 950);
  };

  const saveNorthStar = () => {
    patchNorthStar.mutate(
      { full: full.trim(), brief: brief.trim(), visibility },
      {
        onSuccess: (res) => {
          const n = res.north_star;
          sealThen({
            ...selection,
            title: '北极星',
            rows: [
              ['类型', '北极星'],
              ['铭文', n?.full || '—'],
              ['简称', n?.brief || '—'],
              ['可见性', n?.visibility === 'public' ? '可公开' : '仅本地'],
            ],
          });
        },
      },
    );
  };

  const saveGoal = () => {
    if (!goal) return;
    patchGoal.mutate(
      {
        goalId: goal.id,
        body: { title: title.trim(), summary: summary.trim(), start, target, status },
      },
      {
        onSuccess: (res) => {
          const g = res.goal;
          sealThen({
            ...selection,
            title: g.title || goal.title,
            rows: [
              ['状态', goalStatusLabel(g.status ?? 'active')],
              ['起始', g.start || '—'],
              ['目标', g.target || '—'],
              ['铭文', g.summary || '—'],
            ],
          });
        },
      },
    );
  };

  return (
    <>
      {sealed && (
        <div className="starmap-seal" aria-hidden="true" data-testid="starmap-seal">
          印
        </div>
      )}
      {!editing && (
        <>
          <h3>{selection.title}</h3>
          <dl>
            {selection.rows.map(([k, v]) => (
              <div key={k}>
                <dt>{k}</dt>
                <dd>{v}</dd>
              </div>
            ))}
          </dl>
          <div className="starmap-detail-actions">
            {editable && (
              <button
                type="button"
                className="starmap-recarve"
                data-testid="starmap-recarve"
                onClick={() => setEditing(true)}
              >
                重刻
              </button>
            )}
            <DetailLink kind={selection.kind} profile={profile} />
          </div>
        </>
      )}
      {editing && selection.kind === 'north' && (
        <div className="starmap-edit" data-testid="starmap-edit-north">
          <h3>重刻 · 北极星铭文</h3>
          <label>
            <span>全文</span>
            <textarea
              value={full}
              onChange={(e) => setFull(e.target.value)}
              rows={4}
              placeholder="写下你的北极星…"
              data-testid="edit-north-full"
            />
          </label>
          <label>
            <span>简称(图面与列表展示)</span>
            <input
              value={brief}
              onChange={(e) => setBrief(e.target.value)}
              placeholder="一句话简称"
              data-testid="edit-north-brief"
            />
          </label>
          <div className="starmap-edit-field">
            <span>可见性</span>
            <div className="starmap-vis-toggle" role="group" aria-label="可见性">
              <button
                type="button"
                className={visibility === 'public' ? 'on' : ''}
                onClick={() => setVisibility('public')}
                data-testid="edit-north-public"
              >
                可公开
              </button>
              <button
                type="button"
                className={visibility === 'private' ? 'on' : ''}
                onClick={() => setVisibility('private')}
                data-testid="edit-north-private"
              >
                仅本地
              </button>
            </div>
            <p className="starmap-edit-hint">助手始终可见全文;此开关只影响公开产物。</p>
          </div>
          <EditActions
            saving={saving}
            error={saveError}
            saveDisabled={!full.trim() && !brief.trim()}
            onSave={saveNorthStar}
            onCancel={() => setEditing(false)}
          />
        </div>
      )}
      {editing && selection.kind === 'goal' && goal && (
        <div className="starmap-edit" data-testid="starmap-edit-goal">
          <h3>重刻 · 恒星铭文</h3>
          <label>
            <span>标题</span>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              data-testid="edit-goal-title"
            />
          </label>
          <label>
            <span>摘要</span>
            <textarea
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              rows={3}
              data-testid="edit-goal-summary"
            />
          </label>
          <label>
            <span>起始日期</span>
            <input
              type="date"
              value={start}
              onChange={(e) => setStart(e.target.value)}
              data-testid="edit-goal-start"
            />
          </label>
          <label>
            <span>目标日期</span>
            <input
              type="date"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              data-testid="edit-goal-target"
            />
          </label>
          <label>
            <span>状态</span>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              data-testid="edit-goal-status"
            >
              {GOAL_STATUS_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>
          <EditActions
            saving={saving}
            error={saveError}
            saveDisabled={!title.trim()}
            onSave={saveGoal}
            onCancel={() => setEditing(false)}
          />
        </div>
      )}
    </>
  );
}

function EditActions({
  saving,
  error,
  saveDisabled,
  onSave,
  onCancel,
}: {
  saving: boolean;
  error: Error | null;
  saveDisabled: boolean;
  onSave: () => void;
  onCancel: () => void;
}) {
  return (
    <>
      {error && (
        <p className="starmap-edit-error" role="alert">
          {error.message}
        </p>
      )}
      <div className="starmap-edit-actions">
        <button
          type="button"
          className="starmap-save"
          disabled={saving || saveDisabled}
          onClick={onSave}
          data-testid="starmap-save"
        >
          {saving ? '落印中…' : '落印'}
        </button>
        <button type="button" className="starmap-cancel" disabled={saving} onClick={onCancel}>
          收起刻刀
        </button>
      </div>
    </>
  );
}

/** 联动跳转 (design §5): 北极星无跳转(重刻即全部); 恒星跳项目泳道;
 * 行星跳 /projects; 客星跳证据页; 星官跳技能树(只读卡). */
function DetailLink({ kind, profile }: { kind: StarmapSelection['kind']; profile: string }) {
  const base = `/p/${encodeURIComponent(profile)}`;
  const link =
    kind === 'goal'
      ? { to: `${base}/projects`, label: '前往项目泳道 →' }
      : kind === 'planet'
        ? { to: `${base}/projects`, label: '前往项目 →' }
        : kind === 'guest'
          ? { to: `${base}/evidence`, label: '前往证据 →' }
          : kind === 'skill'
            ? { to: `${base}/skill-tree`, label: '前往技能树 →' }
            : null;
  if (!link) return null;
  return (
    <Link className="starmap-detail-link" to={link.to}>
      {link.label}
    </Link>
  );
}
