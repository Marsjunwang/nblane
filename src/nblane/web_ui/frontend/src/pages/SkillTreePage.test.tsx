import { fireEvent, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';

import { jsonResponse, renderWithProviders } from '../test/render';
import { SkillTreePage } from './SkillTreePage';

const TREE = {
  profile: 'alice',
  schema_name: 'robotics-engineer',
  updated: '2026-09-10',
  status_counts: { expert: 1, solid: 1, learning: 2, locked: 1, total: 5 },
  nodes: [
    {
      id: 'python_core',
      title: 'Python (numpy, scipy)',
      status: 'solid',
      evidence_count: 3,
      children: [
        {
          id: 'object_detection',
          title: '2D Object Detection (YOLO)',
          status: 'expert',
          evidence_count: 1,
          children: [
            {
              id: 'pose_estimation',
              title: '6-DoF Pose Estimation',
              status: 'locked',
              evidence_count: 0,
              children: [],
            },
          ],
        },
        {
          id: 'point_cloud',
          title: 'Point Cloud Processing',
          status: 'learning',
          evidence_count: 2,
          children: [],
        },
      ],
    },
    {
      id: 'git_workflow',
      title: 'Git / GitHub workflow',
      status: 'learning',
      evidence_count: 0,
      children: [],
    },
  ],
};

function stubFetch(body: unknown = TREE, status = 200) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('/profiles/alice/skill-tree')) {
        return jsonResponse(status, body);
      }
      return jsonResponse(404, { code: 'not_found', message: 'not found' });
    }),
  );
}

function renderPage() {
  renderWithProviders(
    <Routes>
      <Route path="/p/:name/skill-tree" element={<SkillTreePage />} />
    </Routes>,
    '/p/alice/skill-tree',
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('SkillTreePage', () => {
  it('renders nested nodes with status badges and evidence chips', async () => {
    stubFetch();
    renderPage();

    expect(await screen.findByText('alice · 技能树')).toBeInTheDocument();
    // Nested nodes render (tree is expanded by default).
    expect(screen.getByText('Python (numpy, scipy)')).toBeInTheDocument();
    expect(screen.getByText('2D Object Detection (YOLO)')).toBeInTheDocument();
    expect(screen.getByText('6-DoF Pose Estimation')).toBeInTheDocument();
    // Status badge per node and the evidence count chip.
    const pythonRow = screen.getByTestId('skill-node-python_core');
    expect(within(pythonRow).getByText('扎实')).toBeInTheDocument();
    expect(within(pythonRow).getByText('证据 3')).toBeInTheDocument();
    const poseRow = screen.getByTestId('skill-node-pose_estimation');
    expect(within(poseRow).getByText('锁定')).toBeInTheDocument();
    expect(within(poseRow).getByText('证据 0')).toBeInTheDocument();
  });

  it('shows status summary chips with the tree-wide counts', async () => {
    stubFetch();
    renderPage();

    expect(await screen.findByText('alice · 技能树')).toBeInTheDocument();
    expect(screen.getByTestId('status-chip-learning')).toHaveTextContent('学习中 2');
    expect(screen.getByTestId('status-chip-solid')).toHaveTextContent('扎实 1');
    expect(screen.getByTestId('status-chip-expert')).toHaveTextContent('精通 1');
    expect(screen.getByTestId('status-chip-locked')).toHaveTextContent('锁定 1');
    expect(screen.getByTestId('status-chip-total')).toHaveTextContent('共 5 项');
  });

  it('collapses and re-expands a subtree', async () => {
    stubFetch();
    renderPage();

    expect(await screen.findByText('2D Object Detection (YOLO)')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '折叠 Python (numpy, scipy)' }));
    expect(screen.queryByText('2D Object Detection (YOLO)')).not.toBeInTheDocument();
    expect(screen.queryByText('6-DoF Pose Estimation')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '展开 Python (numpy, scipy)' }));
    expect(screen.getByText('2D Object Detection (YOLO)')).toBeInTheDocument();
  });

  it('filters by title substring and keeps matching ancestors', async () => {
    stubFetch();
    renderPage();

    expect(await screen.findByText('alice · 技能树')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('筛选技能节点'), { target: { value: 'pose' } });
    // The match stays, with its ancestor chain; unrelated branches hide.
    expect(screen.getByText('6-DoF Pose Estimation')).toBeInTheDocument();
    expect(screen.getByText('Python (numpy, scipy)')).toBeInTheDocument();
    expect(screen.getByText('2D Object Detection (YOLO)')).toBeInTheDocument();
    expect(screen.queryByText('Point Cloud Processing')).not.toBeInTheDocument();
    expect(screen.queryByText('Git / GitHub workflow')).not.toBeInTheDocument();
    // Summary chips still show tree-wide counts, not filtered counts.
    expect(screen.getByTestId('status-chip-total')).toHaveTextContent('共 5 项');
  });

  it('renders the empty state when the tree has no nodes', async () => {
    stubFetch({
      profile: 'alice',
      schema_name: '',
      updated: '',
      status_counts: { expert: 0, solid: 0, learning: 0, locked: 0, total: 0 },
      nodes: [],
    });
    renderPage();

    expect(
      await screen.findByText('技能树为空,先在 skill-tree.yaml 中添加节点。'),
    ).toBeInTheDocument();
    expect(screen.getByTestId('status-chip-total')).toHaveTextContent('共 0 项');
  });
});
