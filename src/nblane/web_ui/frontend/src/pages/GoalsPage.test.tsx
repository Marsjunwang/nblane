import { screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';

import { jsonResponse, renderWithProviders } from '../test/render';
import { GoalsPage } from './GoalsPage';

const GOALS = {
  profile: 'alice',
  current_goal_id: 'goal_main',
  north_star: {
    visibility: 'discreet',
    is_set: true,
    full: 'Become a robotics generalist who ships real demos',
    brief: 'Ship real robot demos',
  },
  goals: [
    {
      id: 'goal_main',
      title: 'Ship the pick-and-place demo',
      label: '阶段目标',
      status: 'active',
      target: '2026-12-31',
      summary: 'Public demo summary',
      skill_links: [
        { node_id: 'moveit2', label: 'Motion planning', source: 'manual', score: 8 },
      ],
      success_criteria: ['Demo runs end to end'],
    },
    {
      id: 'goal_side',
      title: 'Learn Rust for robotics',
      status: 'paused',
      target_skills: ['rust_basics'],
    },
  ],
};

function stubFetch(body: unknown = GOALS, status = 200) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('/profiles/alice/goals')) {
        return jsonResponse(status, body);
      }
      return jsonResponse(404, { code: 'not_found', message: 'not found' });
    }),
  );
}

function renderPage() {
  renderWithProviders(
    <Routes>
      <Route path="/p/:name/goals" element={<GoalsPage />} />
    </Routes>,
    '/p/alice/goals',
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('GoalsPage', () => {
  it('renders the north star card and goal cards', async () => {
    stubFetch();
    renderPage();

    expect(await screen.findByText('alice · 目标')).toBeInTheDocument();
    // North Star card on top (owner view, no redaction).
    const northStar = screen.getByTestId('north-star-card');
    expect(
      within(northStar).getByText('Become a robotics generalist who ships real demos'),
    ).toBeInTheDocument();
    expect(within(northStar).getByText('Ship real robot demos')).toBeInTheDocument();
    expect(within(northStar).getByText('低调')).toBeInTheDocument();
    // Primary goal card with badges, target date and skill chips.
    const mainCard = screen.getByTestId('goal-card-goal_main');
    expect(within(mainCard).getByText('Ship the pick-and-place demo')).toBeInTheDocument();
    expect(within(mainCard).getByText('当前')).toBeInTheDocument();
    expect(within(mainCard).getByText('阶段目标')).toBeInTheDocument();
    expect(within(mainCard).getByText('进行中')).toBeInTheDocument();
    expect(within(mainCard).getByText('目标日期 2026-12-31')).toBeInTheDocument();
    expect(within(mainCard).getByText('Motion planning')).toBeInTheDocument();
    expect(
      within(mainCard).getByText('成功标准:Demo runs end to end'),
    ).toBeInTheDocument();
    // Non-primary goal falls back to target_skills chips.
    const sideCard = screen.getByTestId('goal-card-goal_side');
    expect(within(sideCard).getByText('已暂停')).toBeInTheDocument();
    expect(within(sideCard).getByText('rust_basics')).toBeInTheDocument();
    expect(within(sideCard).queryByText('当前')).not.toBeInTheDocument();
    // Read-only slice: the editor note is visible.
    expect(screen.getByText('编辑功能开发中')).toBeInTheDocument();
  });

  it('hides the north star card when it is not set', async () => {
    stubFetch({
      ...GOALS,
      north_star: { visibility: 'discreet', is_set: false, full: '', brief: '' },
    });
    renderPage();

    expect(await screen.findByText('alice · 目标')).toBeInTheDocument();
    expect(screen.queryByTestId('north-star-card')).not.toBeInTheDocument();
    expect(screen.getByTestId('goal-card-goal_main')).toBeInTheDocument();
  });

  it('shows the empty state when there are no goals', async () => {
    stubFetch({
      profile: 'alice',
      current_goal_id: '',
      north_star: { visibility: 'discreet', is_set: false, full: '', brief: '' },
      goals: [],
    });
    renderPage();

    expect(
      await screen.findByText('还没有目标,先在 goals.yaml 中添加。'),
    ).toBeInTheDocument();
  });
});
