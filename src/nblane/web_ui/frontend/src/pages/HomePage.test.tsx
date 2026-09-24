import { fireEvent, screen, waitFor } from '@testing-library/react';
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

const GOALS = {
  profile: 'alice',
  current_goal_id: 'goal_main',
  north_star: {
    is_set: true,
    full: '成为能独立交付机器人 demo 的工程师',
    brief: '',
    visibility: 'private',
  },
  goals: STARMAP.goals,
};

const CHRONICLE = { profile: 'alice', total: 0, entries: [] };

const PROJECTS_BOARD = {
  profile: 'alice',
  today: '2026-09-23',
  north_star: '',
  goals: [],
  ungrouped_projects: [],
  unassigned_tasks: [],
  habits: [
    {
      id: 'exercise',
      title: '锻炼',
      kind: 'health',
      cadence: 'daily',
      project_id: '',
      week: [{ date: '2026-09-23', done: false, future: false }],
      recent_days: [],
      streak: 3,
      total_checkins: 12,
      last_checkin: '2026-09-22',
    },
    {
      id: 'study',
      title: '学习',
      kind: 'learning',
      cadence: 'daily',
      project_id: '',
      week: [{ date: '2026-09-23', done: true, future: false }],
      recent_days: [{ date: '2026-09-23', count: 2, checkin_ids: ['ck_study_1', 'ck_study_2'] }],
      streak: 5,
      total_checkins: 40,
      last_checkin: '2026-09-23',
    },
  ],
  stats: {},
};

function mockFetch(body: Record<string, unknown> = {}) {
  return vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.includes('/starmap')) return jsonResponse(200, STARMAP);
    if (url.includes('/goals')) return jsonResponse(200, GOALS);
    if (url.includes('/chronicle')) return jsonResponse(200, CHRONICLE);
    if (url.includes('/projects-board')) return jsonResponse(200, PROJECTS_BOARD);
    if (url.includes('/checkins') && init?.method === 'POST') {
      return jsonResponse(201, { ok: true, checkin: { id: 'c1' } });
    }
    if (url.includes('/checkins/') && init?.method === 'DELETE') {
      return jsonResponse(200, { ok: true, deleted_id: 'ck_study_2' });
    }
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

  it('日课印: bottom-left seal cluster renders 白文/朱文 stamps and clicking checks in', async () => {
    const fetchMock = mockFetch();
    renderPage(fetchMock);
    const seal = await screen.findByTestId('habit-seal');
    expect(seal).toHaveTextContent('日课');
    // round-3 印章化: one 44px stamp per habit with an auto-picked glyph —
    // 锻炼/Exercise → 炼 (unchecked = 白文), 学习 → 学 (checked = 朱文).
    expect(screen.getByTestId('habit-seal-exercise')).toHaveTextContent('炼');
    expect(screen.getByTestId('habit-seal-exercise')).toHaveAttribute('data-done', 'false');
    expect(screen.getByTestId('habit-seal-study')).toHaveTextContent('学');
    expect(screen.getByTestId('habit-seal-study')).toHaveAttribute('data-done', 'true');

    fireEvent.click(screen.getByTestId('habit-seal-exercise'));
    await waitFor(() => {
      const call = fetchMock.mock.calls.find(
        ([input, init]) => String(input).includes('/checkins') && init?.method === 'POST',
      );
      expect(call).toBeDefined();
      expect(JSON.parse(String(call?.[1]?.body))).toMatchObject({ habit: 'exercise' });
    });
  });

  it('日课印销印: right-click a 朱文 seal → inline confirm → DELETE today\'s latest check-in', async () => {
    const fetchMock = mockFetch();
    renderPage(fetchMock);
    const seal = await screen.findByTestId('habit-seal-study');
    expect(seal).toHaveAttribute('data-done', 'true');

    // Right-click (contextmenu) opens the inline 销印 confirm strip.
    fireEvent.contextMenu(seal);
    const confirm = await screen.findByTestId('seal-unseal-study');
    expect(confirm).toHaveTextContent('销印「学习」今日最近一次打卡?');

    // Confirm → DELETE the day's LATEST check-in row (ck_study_2).
    fireEvent.click(screen.getByTestId('seal-unseal-yes-study'));
    await waitFor(() => {
      const call = fetchMock.mock.calls.find(
        ([input, init]) => String(input).includes('/checkins/') && init?.method === 'DELETE',
      );
      expect(call).toBeDefined();
      expect(String(call?.[0])).toContain('/checkins/ck_study_2');
    });
    // The strip closes once the mutation settles.
    await waitFor(() => {
      expect(screen.queryByTestId('seal-unseal-study')).not.toBeInTheDocument();
    });
  });

  it('日课印销印: cancel closes the confirm without a DELETE; right-click on 白文 is a no-op', async () => {
    const fetchMock = mockFetch();
    renderPage(fetchMock);
    const seal = await screen.findByTestId('habit-seal-study');

    fireEvent.contextMenu(seal);
    await screen.findByTestId('seal-unseal-study');
    fireEvent.click(screen.getByTestId('seal-unseal-no-study'));
    expect(screen.queryByTestId('seal-unseal-study')).not.toBeInTheDocument();

    // Unchecked (白文) seals never open the confirm.
    fireEvent.contextMenu(screen.getByTestId('habit-seal-exercise'));
    expect(screen.queryByTestId('seal-unseal-exercise')).not.toBeInTheDocument();
    expect(
      fetchMock.mock.calls.some(([, init]) => init?.method === 'DELETE'),
    ).toBe(false);
  });
});
