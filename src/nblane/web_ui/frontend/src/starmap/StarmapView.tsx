import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { StarmapScene, type StarmapSelection } from './StarmapScene';
import type { StarmapSnapshot } from './snapshot';
import titleV2Url from './assets/title-v2-b.svg?url';
import './starmap.css';

const DETAIL_LINK: Record<StarmapSelection['kind'], { path: string; label: string }> = {
  north: { path: 'goals', label: '前往目标 →' },
  goal: { path: 'goals', label: '前往目标 →' },
  planet: { path: 'projects', label: '前往项目 →' },
  guest: { path: 'evidence-review', label: '前往评审 →' },
  skill: { path: 'skill-tree', label: '前往技能树 →' },
};

/**
 * Growth starmap home view: mounts the ported playground scene with real
 * profile data. All chrome (cartouche / briefing / toggle / inscription
 * detail card) is React-owned; the scene drives their opacity/text through
 * refs during the morph, exactly like the playground drove its own DOM.
 */
export function StarmapView({ snapshot }: { snapshot: StarmapSnapshot }) {
  const { name = '' } = useParams();
  const rootRef = useRef<HTMLDivElement>(null);
  const heartRef = useRef<HTMLDivElement>(null);
  const cartoucheRef = useRef<HTMLImageElement>(null);
  const briefingRef = useRef<HTMLDivElement>(null);
  const toggleRef = useRef<HTMLButtonElement>(null);
  const sceneRef = useRef<StarmapScene | null>(null);
  const [selection, setSelection] = useState<StarmapSelection | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    const root = rootRef.current;
    const heart = heartRef.current;
    if (!root || !heart) return;
    let scene: StarmapScene | null = null;
    try {
      scene = new StarmapScene(root, heart, snapshot, {
        onSelect: setSelection,
        domRefs: {
          cartouche: cartoucheRef.current,
          briefing: briefingRef.current,
          toggle: toggleRef.current,
        },
      });
    } catch {
      // No WebGL (or a driver failure): the caller still gets the fallback.
      setFailed(true);
      return;
    }
    sceneRef.current = scene;
    return () => {
      scene?.dispose();
      sceneRef.current = null;
    };
  }, [snapshot]);

  const briefing = useMemo(
    () =>
      `「${snapshot.counts.evidence_needs_review} 条客星待评审，${snapshot.counts.projects_active} 颗行星在轨。」`,
    [snapshot],
  );

  const link = selection ? DETAIL_LINK[selection.kind] : null;

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
        <button
          type="button"
          className="starmap-toggle"
          ref={toggleRef}
          data-starmap-ui
          data-testid="starmap-toggle"
          onClick={() => sceneRef.current?.toggle()}
        >
          → 境态
        </button>
      )}
      <div
        className={`starmap-detail${selection ? ' open' : ''}`}
        data-starmap-ui
        data-testid="starmap-detail"
      >
        {selection && (
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
            {link && (
              <Link
                className="starmap-detail-link"
                to={`/p/${encodeURIComponent(name)}/${link.path}`}
              >
                {link.label}
              </Link>
            )}
          </>
        )}
      </div>
      {failed && (
        <div className="starmap-fallback" data-testid="starmap-fallback">
          <div className="fb-title">成长星图</div>
          <div className="fb-line">{snapshot.north_star || '尚未设置北极星。'}</div>
          <div className="fb-line">{briefing}</div>
          <div className="fb-line">此浏览器不支持 WebGL，以上为静态简报。</div>
        </div>
      )}
    </div>
  );
}
