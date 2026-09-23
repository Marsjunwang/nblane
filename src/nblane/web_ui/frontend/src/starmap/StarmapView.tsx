import { useEffect, useMemo, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';

import { useChronicle } from '../api/hooks';
import { chronicleFlavor, withChronicleFlavor } from './briefing';
import { HabitSeal } from './HabitSeal';
import { InscriptionCard } from './InscriptionCard';
import { StarCatalog } from './StarCatalog';
import { StarmapScene, type StarmapSelection } from './StarmapScene';
import { goalRows, type StarmapSnapshot } from './snapshot';
import titleV2Url from './assets/title-v2-b.svg?url';
import './starmap.css';

/**
 * Growth starmap home view: mounts the ported playground scene with real
 * profile data. All chrome (cartouche / briefing / toggle / inscription
 * detail card / 星表 catalog) is React-owned; the scene drives their
 * opacity/text through refs during the morph, exactly like the playground
 * drove its own DOM.
 *
 * Home-editing slice (design docs/zh/dev/home-editing-starmap-design.md):
 * the inscription card gains 重刻 edit mode (pole star + goal stars), a
 * pale-gold「+」seal button opens the 星表 catalog (locate → focusStar →
 * card), and the briefing line appends a chronicle coda (本月新立目标 N).
 */
export function StarmapView({ snapshot }: { snapshot: StarmapSnapshot }) {
  const { name = '' } = useParams();
  const rootRef = useRef<HTMLDivElement>(null);
  const heartRef = useRef<HTMLDivElement>(null);
  const cartoucheRef = useRef<HTMLImageElement>(null);
  const briefingRef = useRef<HTMLDivElement>(null);
  const toggleRef = useRef<HTMLButtonElement>(null);
  const sceneRef = useRef<StarmapScene | null>(null);
  /** Focus intent that survives scene rebuilds (a mutation invalidates the
   * starmap/goals queries mid-focus; each refreshed scene replays the
   * locate while the intent is fresh). Cleared on any selection change. */
  const pendingFocusRef = useRef<{ id: string; at: number } | null>(null);
  const [selection, setSelection] = useState<StarmapSelection | null>(null);
  const [catalogOpen, setCatalogOpen] = useState(false);
  const [failed, setFailed] = useState(false);
  // 显真 (design 四轮): remembered global preference — true names primary
  // (泥金) with ancient-name notes when on; ancient names only when off.
  const [reveal, setReveal] = useState(
    () => localStorage.getItem('nblane.starmap.reveal') === '1',
  );
  const revealRef = useRef(reveal);
  revealRef.current = reveal;
  const chronicle = useChronicle(name);

  useEffect(() => {
    const root = rootRef.current;
    const heart = heartRef.current;
    if (!root || !heart) return;
    let scene: StarmapScene | null = null;
    try {
      scene = new StarmapScene(root, heart, snapshot, {
        onSelect: (sel) => {
          pendingFocusRef.current = null;
          setSelection(sel);
        },
        domRefs: {
          cartouche: cartoucheRef.current,
          briefing: briefingRef.current,
          toggle: toggleRef.current,
        },
        reveal: revealRef.current,
      });
    } catch {
      // No WebGL (or a driver failure): the caller still gets the fallback.
      setFailed(true);
      return;
    }
    sceneRef.current = scene;
    // Replay a focus interrupted by a data refresh (post-mutation rebuild).
    const pending = pendingFocusRef.current;
    if (pending && performance.now() - pending.at < 6000) {
      if (!scene.focusStar(pending.id)) {
        // Not on the disc (goal beyond the seat cap): card without locate.
        pendingFocusRef.current = null;
        const g = snapshot.goals.find((x) => x.id === pending.id);
        if (g) setSelection({ kind: 'goal', id: g.id, title: g.title, rows: goalRows(g) });
      }
    } else {
      pendingFocusRef.current = null;
    }
    return () => {
      scene?.dispose();
      sceneRef.current = null;
    };
  }, [snapshot]);

  const briefing = useMemo(() => {
    const base = `「${snapshot.counts.evidence_needs_review} 条客星待评审，${snapshot.counts.projects_active} 颗行星在轨。」`;
    return withChronicleFlavor(base, chronicleFlavor(chronicle.data?.entries ?? []));
  }, [snapshot, chronicle.data]);

  // Esc = 一键回纯图, no layering (design home-starmap-enhancements §2):
  // any open card / catalog / edit mode closes back to the bare chart. The
  // scene has its own Esc listener for disc selections; this one also covers
  // the catalog and fallback cards the scene never owned.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return;
      setCatalogOpen(false);
      setSelection(null);
      pendingFocusRef.current = null;
      sceneRef.current?.deselect();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  return (
    <div className="starmap-root" ref={rootRef} data-testid="starmap-root">
      <div className="starmap-layout">
        <div className="starmap-mount-top">
          <img
            className="starmap-cartouche"
            ref={cartoucheRef}
            src={titleV2Url}
            alt="成长星图"
          />
        </div>
        <div className="starmap-heart" ref={heartRef} data-testid="starmap-heart" />
        <div className="starmap-mount-bottom">
          <div className="starmap-briefing" ref={briefingRef} data-testid="starmap-briefing">
            {briefing}
          </div>
        </div>
      </div>
      {!failed && (
        <>
          <button
            type="button"
            className="starmap-toggle"
            ref={toggleRef}
            data-starmap-ui
            data-testid="starmap-toggle"
            aria-label="切换 境态/图态"
            title="境态 ⇄ 图态"
            onClick={() => sceneRef.current?.toggle()}
          >
            境
          </button>
          <button
            type="button"
            className="starmap-reveal-toggle"
            data-starmap-ui
            data-testid="starmap-reveal-toggle"
            aria-pressed={reveal}
            aria-label="显真"
            title={reveal ? '显真·朱文 — 点击钤回古名' : '显真·白文 — 点击显现真名（已记住此偏好）'}
            onClick={() => {
              const v = !reveal;
              setReveal(v);
              localStorage.setItem('nblane.starmap.reveal', v ? '1' : '0');
              sceneRef.current?.setReveal(v);
            }}
          >
            <span aria-hidden="true">显</span>
            <span aria-hidden="true">真</span>
          </button>
          <button
            type="button"
            className="starmap-catalog-btn"
            data-starmap-ui
            data-testid="starmap-catalog-btn"
            aria-label="星表"
            aria-expanded={catalogOpen}
            onClick={() => setCatalogOpen((v) => !v)}
          >
            ＋
          </button>
        </>
      )}
      {/* 日课印 (裁决2): data-only 裱边层 — renders with or without WebGL. */}
      <HabitSeal profile={name} />
      <StarCatalog
        open={catalogOpen}
        snapshot={snapshot}
        profile={name}
        selection={selection}
        onFocus={(id) => {
          const ok = sceneRef.current?.focusStar(id) ?? false;
          if (ok) {
            pendingFocusRef.current = { id, at: performance.now() };
            return;
          }
          // Goal beyond the disc's seat cap: the catalog still opens its
          // card (完备、可靠), just without the locate animation.
          pendingFocusRef.current = null;
          const g = snapshot.goals.find((x) => x.id === id);
          if (g) setSelection({ kind: 'goal', id: g.id, title: g.title, rows: goalRows(g) });
        }}
      />
      <div
        className={`starmap-detail${selection ? ' open' : ''}`}
        data-starmap-ui
        data-testid="starmap-detail"
      >
        {selection && (
          <InscriptionCard
            key={`${selection.kind}:${selection.id}`}
            selection={selection}
            snapshot={snapshot}
            profile={name}
            onSaved={setSelection}
          />
        )}
      </div>
      {failed && (
        <div className="starmap-fallback" data-testid="starmap-fallback">
          <div className="fb-title">成长星图</div>
          <div className="fb-line">
            {snapshot.north.is_set ? snapshot.north_star : '尚未设置北极星 — 北极星虚位以待。'}
          </div>
          <div className="fb-line">{briefing}</div>
          <div className="fb-line">此浏览器不支持 WebGL，以上为静态简报。</div>
        </div>
      )}
    </div>
  );
}
