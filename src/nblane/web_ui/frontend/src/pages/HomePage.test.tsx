import { fireEvent, screen, waitFor, within } from '@testing-library/react';
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

function renderPage(homeBody: unknown = HOME, fetchImpl?: typeof fetch) {
  vi.stubGlobal(
    'fetch',
    vi.fn(
      fetchImpl ??
        (async (input: RequestInfo | URL) => {
          const url = String(input);
          if (url.includes('/profiles/alice/home')) {
            return jsonResponse(200, homeBody);
          }
          // Sidecar probe and anything else resolves — sidecar "reachable".
          return jsonResponse(404, { code: 'not_found', message: 'not found' });
        }),
    ),
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
  it('renders the focus card (north star + primary goal) without the old flat grid', async () => {
    renderPage();

    expect(await screen.findByText('alice · 首页')).toBeInTheDocument();
    expect(screen.getByText(/Ship real robot demos/)).toBeInTheDocument();
    const focus = screen.getByTestId('home-focus-card');
    expect(within(focus).getByText('Ship the pick-and-place demo')).toBeInTheDocument();
    expect(within(focus).getByText('目标日期:2026-12-31')).toBeInTheDocument();
    expect(within(focus).getByText('项目 2')).toBeInTheDocument();
    expect(within(focus).getByRole('link', { name: '全部目标' })).toHaveAttribute(
      'href',
      '/p/alice/goals',
    );
    // The removed flat card grid and quick-entry bar stay gone.
    for (const testId of [
      'home-skills-card',
      'home-kanban-card',
      'home-evidence-card',
      'home-research-card',
      'home-activity-card',
      'home-projects-card',
      'home-health-card',
      'home-dashboard-card',
    ]) {
      expect(screen.queryByTestId(testId)).toBeNull();
    }
  });

  it('aggregates approvals, reviews and doing tasks into the today band', async () => {
    renderPage();

    const band = await screen.findByTestId('home-today-band');
    expect(within(band).getByTestId('home-todo-approvals')).toHaveAttribute(
      'href',
      '/p/alice/activity',
    );
    expect(within(band).getByTestId('home-todo-approvals')).toHaveTextContent('待审批 1');
    expect(within(band).getByTestId('home-todo-review')).toHaveAttribute(
      'href',
      '/p/alice/evidence-review',
    );
    expect(within(band).getByTestId('home-todo-review')).toHaveTextContent('待评审 3');
    const doing = within(band).getAllByTestId('home-todo-doing');
    expect(doing).toHaveLength(1);
    expect(doing[0]).toHaveTextContent('Build robot arm');
    expect(doing[0]).toHaveAttribute('href', '/p/alice/kanban');
  });

  it('shows the calm empty state when there is nothing to do', async () => {
    renderPage({
      ...HOME,
      agent_activity: { total: 0, pending_total: 0, pending_titles: [] },
      evidence: { ...HOME.evidence, needs_review_count: 0 },
      kanban: { ...HOME.kanban, doing: [], doing_total: 0 },
    });

    const band = await screen.findByTestId('home-today-band');
    expect(within(band).getByText(/没有待办/)).toBeInTheDocument();
  });

  it('embeds the 3D galaxy full-width with clickable metric chips when the sidecar answers', async () => {
    renderPage();

    const frame = await screen.findByTestId('sidecar-frame');
    expect(frame).toHaveAttribute(
      'src',
      'http://127.0.0.1:8502/dashboard?profile=alice&embed=1',
    );
    const metrics = screen.getByTestId('home-galaxy-metrics');
    expect(within(metrics).getByTestId('home-metric-skills')).toHaveAttribute(
      'href',
      '/p/alice/skill-tree',
    );
    expect(within(metrics).getByTestId('home-metric-skills')).toHaveTextContent(
      '技能点亮 4/10 · 40%',
    );
    expect(within(metrics).getByTestId('home-metric-kanban')).toHaveAttribute(
      'href',
      '/p/alice/kanban',
    );
    expect(screen.queryByTestId('home-galaxy-fallback')).toBeNull();
  });

  it('degrades to a static metrics band (no iframe) when the sidecar is unreachable', async () => {
    let sidecarUp = false;
    renderPage(HOME, async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('/profiles/alice/home')) {
        return jsonResponse(200, HOME);
      }
      if (!sidecarUp) {
        throw new TypeError('Failed to fetch');
      }
      return jsonResponse(200, {});
    });

    const fallback = await screen.findByTestId('home-galaxy-fallback');
    expect(screen.queryByTestId('sidecar-frame')).toBeNull();
    expect(within(fallback).getByText('40%')).toBeInTheDocument();
    expect(within(fallback).getByText(/3D 仪表盘服务暂时不可达/)).toBeInTheDocument();
    const hint = within(fallback).getByTestId('sidecar-down-hint');
    expect(hint.textContent).toContain('127.0.0.1:8502');
    expect(hint.textContent).toContain('转发了该端口');

    // Retry re-probes; once the sidecar answers, the galaxy takes over.
    sidecarUp = true;
    fireEvent.click(within(fallback).getByText('重试'));
    expect(await screen.findByTestId('sidecar-frame')).toBeInTheDocument();
    expect(screen.queryByTestId('home-galaxy-fallback')).toBeNull();
  });

  it('bootstraps the sidecar session before embedding when a handoff token exists', async () => {
    renderPage({
      ...HOME,
      sidecar: {
        ...HOME.sidecar,
        auth_enabled: true,
        handoff_token: 'handoff-token-123',
      },
    });

    // The hidden bootstrap form (token POST to the sidecar /auth/session)
    // mounts first; the content iframe only follows after the cookie
    // bootstrap head start (~800ms), so it must not exist yet at this point.
    await waitFor(() => expect(document.querySelector('form')).not.toBeNull());
    const form = document.querySelector('form');
    expect(form?.getAttribute('action')).toBe('http://127.0.0.1:8502/auth/session');
    expect(screen.queryByTestId('sidecar-frame')).toBeNull();
    expect(
      await screen.findByTestId('sidecar-frame', undefined, { timeout: 3000 }),
    ).toBeInTheDocument();
  });

  it('shows degradation hints when the profile has no goal or north star', async () => {
    renderPage({
      ...HOME,
      primary_goal: null,
      north_star: { visibility: 'discreet', is_set: false, full: '', brief: '' },
    });

    expect(await screen.findByText('暂无主目标。')).toBeInTheDocument();
    expect(screen.getByText('尚未设置北极星。')).toBeInTheDocument();
  });
});
