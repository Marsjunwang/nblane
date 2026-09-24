/* 占卜 (design home-starmap-enhancements §5 + 王军 rulings 2026-09-23/24):
 * the 卜 seal sits in the right-bottom L-cluster (left of 真/境). Clicking it
 * starts the 起卦仪式 — 微光一滞 (the chart dims), star-dust gathers FROM the
 * disc into a small hexagram in the LEFT disc area, then the 卦辞 card slides
 * in from the left edge and docks at far left with the hexagram resting at
 * the card's head-left (卦旗). Esc returns to the pure chart (global rule).
 *
 * 戏占 (play, default) casts immediately; 正占 (serious) reveals a question
 * input and anchors on the real gap analysis. While the LLM cast is in flight
 * the ritual stays alive (摇卦 — the yao lines keep shuffling; no dead
 * spinner, however long it takes). `source: "rule"` shows a 「离线卦」 note.
 *
 * 正占 readings whose gap analysis found missing nodes carry a 「化为任务」
 * action: each gap node becomes one kanban learning task via the existing
 * POST /profiles/{name}/gap/intake endpoint (same contract as the retired
 * GapPage 加入看板 button), then kanban/projects-board queries invalidate.
 *
 * Backend: POST /api/v1/profiles/{name}/divination (single-consumption,
 * nothing persisted; 60s LLM timeout with deterministic rule fallback).
 */
import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';

import { apiPost } from '../api/client';
import type { DivinationRequest, DivinationResponse } from '../api/types';

/** One node of the serious-cast gap closure (anchors.gap.closure). */
export interface DivinationGapNode {
  id: string;
  label: string;
  status: string;
  is_gap: boolean;
}

/** Gap (is_gap) nodes of a serious cast — the 化为任务 material. Pure. */
export function gapNodesOf(result: DivinationResponse | null): DivinationGapNode[] {
  const gap = result?.anchors?.gap as { closure?: DivinationGapNode[] } | undefined;
  return (gap?.closure ?? []).filter((node) => node.is_gap);
}

/** Yao rows for display: symbol_lines are bottom-up (初爻 first); the symbol
 * renders top-down. Pure — vitest-covered. */
export function yaoRows(symbolLines: number[]): boolean[] {
  return symbolLines.slice(0, 6).reverse().map((y) => y === 1);
}

export function HexagramSymbol({
  lines,
  size = 44,
  animated = false,
}: {
  lines: number[];
  size?: number;
  animated?: boolean;
}) {
  const rows = yaoRows(lines);
  const w = size;
  const h = size * 0.72;
  const rowH = h / 6;
  return (
    <div
      className={`hexagram-symbol${animated ? ' casting' : ''}`}
      style={{ width: w, height: h }}
      data-testid="hexagram-symbol"
      aria-hidden="true"
    >
      {rows.map((solid, i) => (
        <div
          key={i}
          className={`hex-yao${solid ? ' solid' : ' broken'}`}
          style={{ height: rowH * 0.52, top: i * rowH + rowH * 0.24 }}
        >
          {!solid && <span className="hex-yao-gap" />}
        </div>
      ))}
    </div>
  );
}

type Phase = 'gather' | 'casting' | 'done' | 'error';

interface Particle {
  sx: number;
  sy: number;
  tx: number;
  ty: number;
  delay: number;
  size: number;
  gold: boolean;
  seed: number;
}

/** Star-dust gather + 摇卦 canvas over the 画心. Dust converges from the disc
 * into the hexagram target zone (left disc area); while the cast is in flight
 * the dust keeps breathing and the yao slots flicker — the ritual never dies. */
function RitualCanvas({
  phase,
  lines,
  reduced,
}: {
  phase: Phase;
  lines: number[];
  reduced: boolean;
}) {
  const ref = useRef<HTMLCanvasElement>(null);
  const stateRef = useRef({ phase, lines });
  stateRef.current = { phase, lines };

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const parent = canvas.parentElement!;
    const W = parent.clientWidth;
    const H = parent.clientHeight;
    const dpr = Math.min(window.devicePixelRatio, 2);
    canvas.width = W * dpr;
    canvas.height = H * dpr;
    const ctx = canvas.getContext('2d')!;
    ctx.scale(dpr, dpr);

    // hexagram target zone: left disc area
    const cx = W * 0.3;
    const cy = H * 0.48;
    const hexW = Math.min(96, W * 0.16);
    const hexRowH = (hexW * 0.72) / 6;
    const yaoY = (rowTopDown: number) => cy - hexW * 0.36 + rowTopDown * hexRowH + hexRowH / 2;

    // dust particles: start scattered over the disc, converge to yao slots
    const rnd = (() => {
      let s = 20260924;
      return () => {
        s = (s * 1664525 + 1013904223) >>> 0;
        return s / 2 ** 32;
      };
    })();
    const particles: Particle[] = [];
    for (let i = 0; i < 130; i++) {
      const row = Math.floor(rnd() * 6);
      const broken = rnd() < 0.45;
      const gap = broken ? (rnd() < 0.5 ? -1 : 1) * (0.12 + rnd() * 0.06) : 0;
      const tx = cx + (rnd() - 0.5) * hexW * (broken ? 0.76 : 0.96) + gap * hexW;
      const ty = yaoY(row) + (rnd() - 0.5) * hexRowH * 0.5;
      const a = rnd() * Math.PI * 2;
      const rr = (0.25 + rnd() * 0.45) * Math.min(W, H) * 0.5;
      particles.push({
        sx: W / 2 + Math.cos(a) * rr * 1.25,
        sy: H / 2 + Math.sin(a) * rr,
        tx,
        ty,
        delay: rnd() * 0.45,
        size: 0.8 + rnd() * 1.2,
        gold: rnd() < 0.22,
        seed: rnd() * 1000,
      });
    }

    let raf = 0;
    const t0 = performance.now();
    const draw = (now: number) => {
      raf = requestAnimationFrame(draw);
      const el = (now - t0) / 1000;
      const { phase: ph, lines: ls } = stateRef.current;
      ctx.clearRect(0, 0, W, H);
      ctx.globalCompositeOperation = 'lighter';
      const gather = Math.min(1, el / 1.6); // gather completes in 1.6s
      const casting = ph === 'casting';
      for (const p of particles) {
        const lp = Math.min(1, Math.max(0, (gather - p.delay) / (1 - p.delay || 1)));
        const e = lp * lp * (3 - 2 * lp); // smoothstep
        // while casting the dust keeps breathing around its slot (摇卦, alive)
        const jitter = casting && !reduced ? 2.2 : 0.6;
        const jx = Math.sin(el * 1.7 + p.seed) * jitter;
        const jy = Math.cos(el * 1.3 + p.seed * 1.7) * jitter;
        const x = p.sx + (p.tx - p.sx) * e + jx * e;
        const y = p.sy + (p.ty - p.sy) * e + jy * e;
        const tw = 0.55 + 0.45 * Math.sin(el * 2.1 + p.seed * 3);
        ctx.beginPath();
        ctx.arc(x, y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = p.gold
          ? `rgba(240, 205, 127, ${0.5 * tw * e})`
          : `rgba(232, 226, 210, ${0.4 * tw * e})`;
        ctx.fill();
      }
      // yao lines: while casting they shuffle (摇卦); once the cast lands they
      // settle to the real hexagram. Never a dead spinner.
      const settled = ph === 'done' || ph === 'error';
      const rows = settled ? yaoRows(ls) : null;
      const cycle = Math.floor(el / 0.12);
      for (let row = 0; row < 6; row++) {
        const y = yaoY(row);
        const solid = rows ? rows[row] : (row * 7 + cycle) % 3 !== 0;
        const lineAlpha =
          ph === 'gather'
            ? Math.max(0, gather - 0.55) * 0.6
            : casting
              ? 0.3 + 0.25 * Math.sin(el * 4 + row)
              : 0.85;
        if (lineAlpha <= 0.01) continue;
        ctx.fillStyle = `rgba(240, 205, 127, ${lineAlpha})`;
        const lh = Math.max(2, hexRowH * 0.34);
        if (solid) {
          ctx.fillRect(cx - hexW / 2, y - lh / 2, hexW, lh);
        } else {
          const seg = (hexW / 2) * 0.76;
          ctx.fillRect(cx - hexW / 2, y - lh / 2, seg, lh);
          ctx.fillRect(cx + hexW / 2 - seg, y - lh / 2, seg, lh);
        }
      }
      ctx.globalCompositeOperation = 'source-over';
    };
    raf = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(raf);
  }, [reduced]);

  return <canvas ref={ref} className="starmap-div-ritual-canvas" />;
}

export function DivinationPanel({
  profile,
  open,
  onClose,
}: {
  profile: string;
  open: boolean;
  onClose: () => void;
}) {
  const reduced = useMemo(
    () => typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches,
    [],
  );
  const [phase, setPhase] = useState<Phase>('gather');
  const [mode, setMode] = useState<'play' | 'serious'>('play');
  const [question, setQuestion] = useState('');
  const [result, setResult] = useState<DivinationResponse | null>(null);
  const [error, setError] = useState('');
  const [cardIn, setCardIn] = useState(false);
  // 化为任务: idle → working → done (count) | error.
  const [intake, setIntake] = useState<{ state: 'idle' | 'working' | 'done' | 'error'; count: number; error: string }>({
    state: 'idle',
    count: 0,
    error: '',
  });
  const genRef = useRef(0);
  const queryClient = useQueryClient();

  const cast = async (m: 'play' | 'serious', q: string) => {
    const gen = ++genRef.current;
    setPhase('casting');
    setResult(null); // never show a stale reading under 摇卦
    setError('');
    setIntake({ state: 'idle', count: 0, error: '' });
    try {
      const body: DivinationRequest = { mode: m, question: q };
      const res = await apiPost<DivinationResponse>(
        `/profiles/${encodeURIComponent(profile)}/divination`,
        body,
      );
      if (gen !== genRef.current) return; // a newer cast superseded
      setResult(res);
      setPhase('done');
      window.setTimeout(() => setCardIn(true), reduced ? 0 : 500);
    } catch (e) {
      if (gen !== genRef.current) return;
      setError(e instanceof Error ? e.message : String(e));
      setPhase('error');
      window.setTimeout(() => setCardIn(true), reduced ? 0 : 500);
    }
  };

  // 化为任务: one kanban learning task per gap node. Sequential — every
  // intake writes kanban.md under a file lock, so no parallel fan-out.
  const runIntake = async (nodes: DivinationGapNode[], q: string) => {
    if (intake.state === 'working' || intake.state === 'done') return;
    setIntake({ state: 'working', count: 0, error: '' });
    try {
      for (const node of nodes) {
        await apiPost(`/profiles/${encodeURIComponent(profile)}/gap/intake`, {
          title: `学习 ${node.label || node.id}`,
          node_id: node.id,
          why: q,
          section: 'Queue',
        });
      }
      queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'kanban'] });
      queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'projects-board'] });
      setIntake({ state: 'done', count: nodes.length, error: '' });
    } catch (e) {
      setIntake({
        state: 'error',
        count: 0,
        error: e instanceof Error ? e.message : String(e),
      });
    }
  };

  // opening the panel starts the ritual + a 戏占 cast
  useEffect(() => {
    if (!open) return;
    setPhase('gather');
    setResult(null);
    setError('');
    setCardIn(false);
    setMode('play');
    setQuestion('');
    cast('play', '');
    // gather → casting handoff (the cast itself decides `done`)
    const t = window.setTimeout(() => setPhase((p) => (p === 'gather' ? 'casting' : p)), 1650);
    return () => window.clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  if (!open) return null;

  const hx = result?.hexagram;
  const lines = hx?.symbol_lines ?? [1, 1, 1, 1, 1, 1];
  const gapNodes = gapNodesOf(result);

  return (
    <div
      className={`starmap-div-root${cardIn ? ' docked' : ''}`}
      data-starmap-ui
      data-testid="divination-root"
    >
      <div className="starmap-div-overlay">
        <RitualCanvas phase={phase} lines={lines} reduced={reduced} />
      </div>
      <div
        className={`starmap-div-card${cardIn ? ' open' : ''}`}
        data-testid="divination-card"
        role="dialog"
        aria-label="占卜"
      >
        <div className="div-card-head">
          {/* 卦旗: the hexagram rests at the card's head-left */}
          <HexagramSymbol lines={lines} size={44} animated={phase === 'casting'} />
          <div className="div-card-title">
            {phase === 'casting' || phase === 'gather' ? (
              <span className="div-casting-label">摇卦…</span>
            ) : phase === 'error' ? (
              <span className="div-error-label">占问未果</span>
            ) : (
              <>
                <span className="div-hx-name">{hx?.name}</span>
                {result?.source === 'rule' && <span className="div-offline-note">离线卦</span>}
              </>
            )}
          </div>
          <button
            type="button"
            className="div-close"
            onClick={onClose}
            aria-label="收起卦辞 (Esc)"
            data-testid="divination-close"
          >
            ×
          </button>
        </div>
        {phase === 'error' ? (
          <p className="div-error" role="alert">
            {error}
          </p>
        ) : (
          result && (
            <>
              <p className="div-judgment" data-testid="divination-judgment">
                {hx?.judgment}
              </p>
              <p className="div-reading" data-testid="divination-reading">
                {result.reading}
              </p>
              {result.mode === 'serious' && gapNodes.length > 0 && (
                <div className="div-intake" data-testid="divination-intake-zone">
                  {intake.state === 'done' ? (
                    <p className="div-intake-done" data-testid="divination-intake-done">
                      已将 {intake.count} 处缺口化为看板任务(Queue)。
                      <Link
                        to={`/p/${encodeURIComponent(profile)}/projects`}
                        className="div-intake-link"
                        data-testid="divination-intake-link"
                      >
                        去项目页看看 →
                      </Link>
                    </p>
                  ) : (
                    <>
                      <button
                        type="button"
                        className="div-cast-btn div-intake-btn"
                        disabled={intake.state === 'working'}
                        data-testid="divination-intake"
                        onClick={() => runIntake(gapNodes, result.question)}
                      >
                        {intake.state === 'working'
                          ? '化为任务…'
                          : `化为任务(${gapNodes.length} 处所缺)`}
                      </button>
                      {intake.state === 'error' && (
                        <p className="div-error" role="alert" data-testid="divination-intake-error">
                          化为任务未果:{intake.error}
                        </p>
                      )}
                    </>
                  )}
                </div>
              )}
            </>
          )
        )}
        <div className="div-chips" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={mode === 'play'}
            className={`div-chip${mode === 'play' ? ' active' : ''}`}
            data-testid="divination-mode-play"
            onClick={() => {
              setMode('play');
              cast('play', '');
            }}
          >
            戏占
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={mode === 'serious'}
            className={`div-chip${mode === 'serious' ? ' active' : ''}`}
            data-testid="divination-mode-serious"
            onClick={() => setMode('serious')}
          >
            正占
          </button>
        </div>
        {mode === 'serious' && (
          <div className="div-question">
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              rows={2}
              placeholder="所问何事?(接真实差距分析)"
              data-testid="divination-question"
            />
            <button
              type="button"
              className="div-cast-btn"
              disabled={!question.trim()}
              data-testid="divination-cast"
              onClick={() => cast('serious', question.trim())}
            >
              起卦
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
