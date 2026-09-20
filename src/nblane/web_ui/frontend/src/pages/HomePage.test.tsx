import { act, fireEvent, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';

import { jsonResponse, renderWithProviders } from '../test/render';
import { HomePage } from './HomePage';

const HOME = {
  profile: 'alice',
  north_star: {
    visibility: 'discreet',
    is_set: true,
    full: 'Become a robotics generalist who ships real demos',
    brief: 'Ship real robot demos',
  },
  primary_goal: {
    id: 'goal_main',
    title: 'Ship the pick-and-place demo',
    label: 'Stage goal',
    status: 'active',
    target: '2026-12-31',
    progress: 0.5,
    stalled: false,
    project_count: 2,
  },
  goal_counts: { active: 1, total: 2 },
  skills: {
    has_tree: true,
    schema_name: 'robotics-engineer',
    total: 10,
    lit: 4,
    lit_rate: 0.4,
    counts: { expert: 1, solid: 3, learning: 2, locked: 4 },
    evidence_risk_count: 1,
  },
  kanban: {
    counts: { Doing: 1, Done: 2, Queue: 0 },
    doing_total: 1,
    done_uncrystallized_count: 1,
    doing: [{ id: 'kb_doing1', title: 'Build robot arm', started_on: '2026-09-01' }],
  },
  evidence: {
    total_entries: 5,
    unlinked_count: 2,
    needs_review_count: 3,
    status_risk_count: 1,
    done_uncrystallized_count: 1,
  },
  sources: {
    implemented: true,
    total: 3,
    active_total: 2,
    status_counts: { reading: 1, inbox: 1, archived: 1 },
    active_titles: ['SLAM survey', 'grasp tooling post'],
  },
  projects: { total: 2, status_counts: { active: 1, completed: 1 } },
  claims: { total: 4, accepted_count: 2, draft_count: 2, needs_refresh_count: 0 },
  agent_activity: { total: 3, pending_total: 1, pending_titles: ['Pending candidate'] },
  health: { counts: { warning: 1 }, context_ready: true },
  sidecar: {
    base: 'http://127.0.0.1:8502',
    configured: false,
    auth_enabled: false,
    handoff_token: '',
    paper_library_url: 'http://127.0.0.1:8502/paper-library?profile=alice',
    dashboard_url: 'http://127.0.0.1:8502/dashboard?profile=alice&embed=1',
  },
};

function renderPage(homeBody: unknown = HOME) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('/profiles/alice/home')) {
        return jsonResponse(200, homeBody);
      }
      return jsonResponse(404, { code: 'not_found', message: 'not found' });
    }),
  );
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

describe('HomePage', () => {
  it('renders the overview cards from the aggregated home payload', async () => {
    renderPage();

    expect(await screen.findByText('alice · 首页')).toBeInTheDocument();
    // North Star brief.
    expect(screen.getByText(/Ship real robot demos/)).toBeInTheDocument();
    // Primary goal card with progress + project count.
    expect(screen.getByText('Ship the pick-and-place demo')).toBeInTheDocument();
    expect(screen.getByText('目标日期:2026-12-31')).toBeInTheDocument();
    expect(screen.getByText('项目 2')).toBeInTheDocument();
    // Skills ring + counts (badge text also appears in the ring tooltips).
    expect(screen.getByText('点亮 4 / 10')).toBeInTheDocument();
    expect(screen.getAllByText('expert: 1').length).toBeGreaterThan(0);
    // Kanban Doing strip.
    expect(screen.getByText('Build robot arm')).toBeInTheDocument();
    // Evidence attention badges.
    expect(screen.getByText('待评审 3')).toBeInTheDocument();
    expect(screen.getByText('未挂链 2')).toBeInTheDocument();
    // Research + activity counters.
    expect(screen.getByText('进行中来源 2')).toBeInTheDocument();
    expect(screen.getByText('待审批 1')).toBeInTheDocument();
    expect(screen.getByText('Pending candidate')).toBeInTheDocument();
    // Quick links route into the profile pages (the card titles also link).
    const kanbanLinks = screen.getAllByRole('link', { name: '看板' });
    expect(kanbanLinks.some((el) => el.getAttribute('href') === '/p/alice/kanban')).toBe(true);
  });

  it('embeds the sidecar 3D dashboard on toggle (fireEvent)', async () => {
    renderPage();
    await screen.findByText('alice · 首页');

    expect(screen.queryByTestId('sidecar-frame')).toBeNull();
    fireEvent.click(screen.getByText('嵌入显示'));
    const frame = screen.getByTestId('sidecar-frame');
    expect(frame).toHaveAttribute(
      'src',
      'http://127.0.0.1:8502/dashboard?profile=alice&embed=1',
    );
    fireEvent.click(screen.getByText('收起嵌入'));
    expect(screen.queryByTestId('sidecar-frame')).toBeNull();
  });

  it('bootstraps the sidecar session before embedding when a handoff token exists', async () => {
    vi.useRealTimers();
    renderPage({
      ...HOME,
      sidecar: {
        ...HOME.sidecar,
        auth_enabled: true,
        handoff_token: 'handoff-token-123',
      },
    });
    await screen.findByText('alice · 首页');

    vi.useFakeTimers();
    try {
      fireEvent.click(screen.getByText('嵌入显示'));
      // The content iframe waits for the auth bootstrap timer; the hidden
      // bootstrap form posts the token to the sidecar /auth/session.
      expect(screen.queryByTestId('sidecar-frame')).toBeNull();
      const form = document.querySelector('form');
      expect(form).not.toBeNull();
      expect(form?.getAttribute('action')).toBe('http://127.0.0.1:8502/auth/session');
      act(() => {
        vi.advanceTimersByTime(900);
      });
      expect(screen.getByTestId('sidecar-frame')).toBeInTheDocument();
    } finally {
      vi.useRealTimers();
    }
  });

  it('shows a degradation hint when the profile has no skill tree or goal', async () => {
    renderPage({
      ...HOME,
      primary_goal: null,
      north_star: { visibility: 'discreet', is_set: false, full: '', brief: '' },
      skills: { ...HOME.skills, has_tree: false, total: 0, lit: 0, lit_rate: 0, counts: {} },
    });

    expect(await screen.findByText('暂无主目标。')).toBeInTheDocument();
    expect(screen.getByText('尚未设置北极星。')).toBeInTheDocument();
    expect(screen.getByText('尚未建立技能树。')).toBeInTheDocument();
  });
});
