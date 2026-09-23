import { screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';

import { jsonResponse, renderWithProviders } from '../test/render';
import { HomePage } from './HomePage';

const STARMAP = {
  profile: 'alice',
  generated_on: '2026-09-23',
  schema_name: 'robotics-engineer',
  north_star: '成为能独立交付机器人 demo 的工程师',
  goals: [
    {
      id: 'goal_main',
      title: 'Ship the pick-and-place demo',
      status: 'active',
      summary: 'Deliver the demo end to end',
      start: '2026-01-01',
      target: '2026-12-31',
    },
  ],
  categories: [
    { id: 'foundations', name: '基础', count: 2, lit_count: 1, learning_count: 1 },
  ],
  skills: [
    { id: 'root_a', label: 'Root A', category: 'foundations', status: 'solid', lit: true },
    { id: 'child_a1', label: 'Child A1', category: 'foundations', status: 'learning', lit: false },
  ],
  projects: [
    {
      id: 'proj_demo',
      title: 'Pick-and-place demo',
      status: 'active',
      kind: 'work',
      goal_ids: ['goal_main'],
      progress: 0.5,
      task_count: 4,
      time_range: '2026-08 ~ 2026-12',
    },
  ],
  evidence: [
    {
      id: 'ev_one',
      type: 'project',
      title: 'First grasping run',
      date: '2026-09-20',
      strength: 'medium',
      review_status: 'needs_review',
      summary: 'Ran the grasping pipeline on the desk setup.',
      skill_ids: ['root_a'],
      project_refs: ['proj_demo'],
      flying: true,
    },
  ],
  counts: {
    evidence: 1,
    evidence_needs_review: 1,
    evidence_flying: 1,
    projects_active: 1,
    skills_lit: 1,
  },
};

function mockFetch(body: Record<string, unknown> = {}) {
  return vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.includes('/starmap')) return jsonResponse(200, STARMAP);
    return jsonResponse(404, { code: 'not_found', message: `unexpected: ${url}`, ...body });
  });
}

function renderPage(fetchImpl?: typeof fetch) {
  vi.stubGlobal('fetch', vi.fn(fetchImpl ?? mockFetch()));
  return renderWithProviders(
    <Routes>
      <Route path="/p/:name/home" element={<HomePage />} />
    </Routes>,
    '/p/alice/home',
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('HomePage (starmap)', () => {
  it('renders the starmap frame with cartouche and briefing', async () => {
    renderPage();
    expect(await screen.findByTestId('starmap-root')).toBeInTheDocument();
    expect(screen.getByTestId('starmap-briefing')).toHaveTextContent('客星待评审');
  });

  it('degrades to the static briefing when WebGL is unavailable (jsdom)', async () => {
    renderPage();
    const fallback = await screen.findByTestId('starmap-fallback');
    expect(fallback).toHaveTextContent('成为能独立交付机器人 demo 的工程师');
    expect(fallback).toHaveTextContent('1 条客星待评审，1 颗行星在轨');
  });

  it('shows an error alert when the starmap API fails', async () => {
    renderPage(async () => jsonResponse(500, { code: 'boom', message: 'starmap exploded' }));
    expect(await screen.findByTestId('starmap-error')).toBeInTheDocument();
  });
});
