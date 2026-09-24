import { fireEvent, screen, waitFor, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';

import { asterismById } from '../starmap/layout';
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

const TREE_WITH_CATEGORIES = {
  profile: 'alice',
  schema_name: 'robotics-engineer',
  updated: '2026-09-10',
  status_counts: { expert: 0, solid: 1, learning: 1, locked: 1, total: 3 },
  categories: [
    { id: 'foundations', name: '基础', count: 2, lit_count: 1, learning_count: 1 },
    { id: 'navigation', name: '导航', count: 1, lit_count: 0, learning_count: 0 },
  ],
  nodes: [
    {
      id: 'python_core',
      title: 'Python (numpy, scipy)',
      status: 'solid',
      category: 'foundations',
      evidence_count: 0,
      children: [
        {
          id: 'numpy',
          title: 'NumPy internals',
          status: 'learning',
          category: 'foundations',
          evidence_count: 0,
          children: [],
        },
      ],
    },
    {
      id: 'slam_basics',
      title: 'SLAM Basics',
      status: 'locked',
      category: 'navigation',
      evidence_count: 0,
      children: [],
    },
  ],
};

const SKILL_EVIDENCE = {
  profile: 'alice',
  status: '',
  q: '',
  skill_id: 'python_core',
  limit: 200,
  total: 1,
  items: [
    {
      id: 'ev_9',
      title: 'Built ROS2 pick demo',
      evidence_type: 'project',
      review_status: 'reviewed',
      date: '2026-08-20',
    },
  ],
};

function stubRichFetch() {
  const calls: { url: string; init?: RequestInit }[] = [];
  // The stub keeps server state: after a PATCH the tree read serves the
  // post-write status (lit maps to YAML solid server-side).
  let patched = false;
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      calls.push({ url, init });
      if (url.includes('/skill-tree/nodes/') && init?.method === 'PATCH') {
        patched = true;
        return new Response(
          JSON.stringify({
            ok: true,
            node_id: 'numpy',
            status: 'solid',
            previous_status: 'learning',
            changed: true,
          }),
          {
            status: 200,
            headers: { 'Content-Type': 'application/json', ETag: 'W/"tree-etag-2"' },
          },
        );
      }
      if (url.includes('/profiles/alice/skill-tree')) {
        const tree = patched
          ? {
              ...TREE_WITH_CATEGORIES,
              nodes: TREE_WITH_CATEGORIES.nodes.map((node) =>
                node.id === 'python_core'
                  ? {
                      ...node,
                      children: node.children.map((child) =>
                        child.id === 'numpy' ? { ...child, status: 'solid' } : child,
                      ),
                    }
                  : node,
              ),
            }
          : TREE_WITH_CATEGORIES;
        return new Response(JSON.stringify(tree), {
          status: 200,
          headers: {
            'Content-Type': 'application/json',
            ETag: patched ? 'W/"tree-etag-2"' : 'W/"tree-etag-1"',
          },
        });
      }
      if (url.includes('/profiles/alice/evidence') && url.includes('skill_id=')) {
        return jsonResponse(200, SKILL_EVIDENCE);
      }
      return jsonResponse(404, { code: 'not_found', message: 'not found' });
    }),
  );
  return calls;
}

describe('SkillTreePage 进阶进度', () => {
  const TREE_WITH_PROGRESS = {
    ...TREE,
    nodes: [
      {
        id: 'point_cloud',
        title: 'Point Cloud Processing',
        status: 'learning',
        evidence_count: 2,
        children: [],
        progress: {
          score: 12,
          next_rung: 'solid',
          threshold_next: 30,
          breakthrough_count: 1,
          eligible: false,
        },
      },
      {
        id: 'git_workflow',
        title: 'Git / GitHub workflow',
        status: 'learning',
        evidence_count: 0,
        children: [],
        progress: {
          score: 35,
          next_rung: 'solid',
          threshold_next: 30,
          breakthrough_count: 0,
          eligible: true,
        },
      },
    ],
  };

  it('inscription card shows rung ladder, 泥金 score bar and breakthrough count', async () => {
    stubFetch(TREE_WITH_PROGRESS);
    renderPage();

    fireEvent.click(await screen.findByText('Point Cloud Processing'));
    const card = await screen.findByTestId('skill-inscription');
    const block = within(card).getByTestId('skill-progress');
    expect(block).toHaveTextContent('学习中 → 扎实');
    expect(block).toHaveTextContent('12 / 30');
    // 12/30 → 40% 泥金 fill.
    expect(within(card).getByTestId('skill-progress-fill').style.width).toBe('40%');
    expect(within(card).getByTestId('skill-breakthroughs')).toHaveTextContent('突破 ×1');
    // Not eligible: no suggested-upgrade state on the stepper.
    expect(within(card).queryByTestId('stepper-upgrade-lit')).not.toBeInTheDocument();
    expect(within(card).getByTestId('stepper-lit')).not.toHaveClass('nblane-eligible-pulse');
  });

  it('eligible nodes pulse in the list and the stepper marks the next rung 可进阶', async () => {
    stubFetch(TREE_WITH_PROGRESS);
    renderPage();

    // Node list glyph carries the pulse class; the ineligible one does not.
    const row = await screen.findByTestId('skill-node-git_workflow');
    expect(row).toHaveAttribute('data-eligible', 'true');
    expect(
      screen.getByTestId('skill-node-point_cloud'),
    ).not.toHaveAttribute('data-eligible');

    fireEvent.click(row);
    const card = await screen.findByTestId('skill-inscription');
    expect(within(card).getByTestId('skill-eligible-hint')).toHaveTextContent(
      '已达进阶门槛',
    );
    const lit = within(card).getByTestId('stepper-lit');
    expect(lit).toHaveAttribute('data-suggested', 'true');
    expect(lit).toHaveClass('nblane-eligible-pulse');
    expect(within(card).getByTestId('stepper-upgrade-lit')).toHaveTextContent('可进阶');
    // breakthrough_count 0 → no breakthrough line.
    expect(within(card).queryByTestId('skill-breakthroughs')).not.toBeInTheDocument();
  });
});

describe('SkillTreePage category banners (星官化)', () => {
  it('renders asterism figure, 官名, 三态统计 and lore per mapped category', async () => {
    stubRichFetch();
    renderPage();

    const banner = await screen.findByTestId('category-banner-foundations');
    // 官名 from the SECTOR_ASTERISM mapping (基础 → 华盖).
    expect(within(banner).getByText('华盖')).toBeInTheDocument();
    expect(within(banner).getByText('基础')).toBeInTheDocument();
    // Real line shape etched from asterisms.json.
    expect(within(banner).getByTestId('asterism-figure-huagai')).toBeInTheDocument();
    // One-line 小传 from the asterism lore field.
    const lore = asterismById('huagai')?.lore ?? '';
    expect(lore).not.toBe('');
    expect(within(banner).getByText(lore)).toBeInTheDocument();
    // 三态统计: locked = count − lit − learning = 0, 在学 1, 点亮 1.
    expect(within(banner).getByTitle('在学 1')).toBeInTheDocument();
    expect(within(banner).getByTitle('点亮 1')).toBeInTheDocument();
    expect(within(banner).getByTitle('锁定 0')).toBeInTheDocument();
    // Nodes still render under their banner.
    expect(screen.getByText('Python (numpy, scipy)')).toBeInTheDocument();
  });

  it('notes the template status for domains without a real line shape', async () => {
    stubRichFetch();
    renderPage();

    const banner = await screen.findByTestId('category-banner-navigation');
    // 导航 → 翼宿: real shape not in asterisms.json yet (template fallback).
    expect(within(banner).getByText('翼宿')).toBeInTheDocument();
    expect(within(banner).getByText('拟形·模板')).toBeInTheDocument();
    expect(within(banner).queryByTestId('asterism-figure-yi')).not.toBeInTheDocument();
  });
});

describe('SkillTreePage node inscription card', () => {
  it('opens on node click and lists linked evidence with deep links', async () => {
    stubRichFetch();
    renderPage();

    fireEvent.click(await screen.findByText('Python (numpy, scipy)'));
    const card = await screen.findByTestId('skill-inscription');
    expect(within(card).getByText('Python (numpy, scipy)')).toBeInTheDocument();
    expect(within(card).getByText('扎实')).toBeInTheDocument();
    // 关联证据 from GET /evidence?skill_id=python_core, deep-linked to the
    // seated stage with the focus param.
    const link = await within(card).findByTestId('skill-evidence-link-ev_9');
    expect(link).toHaveTextContent('Built ROS2 pick demo');
    expect(link).toHaveAttribute(
      'href',
      '/p/alice/evidence?stage=seated&focus=ev_9',
    );
    // Clicking the row again closes the card.
    fireEvent.click(screen.getAllByText('Python (numpy, scipy)')[0]);
    await waitFor(() =>
      expect(screen.queryByTestId('skill-inscription')).not.toBeInTheDocument(),
    );
  });

  it('sends the 三态 PATCH with If-Match when the stepper moves a node', async () => {
    const calls = stubRichFetch();
    renderPage();

    fireEvent.click(await screen.findByText('NumPy internals'));
    const card = await screen.findByTestId('skill-inscription');
    // 在学 is the current step (disabled); 点亮 and 锁定 are actionable.
    expect(within(card).getByTestId('stepper-learning')).toBeDisabled();
    fireEvent.click(within(card).getByTestId('stepper-lit'));

    await waitFor(() => {
      const patch = calls.find(
        (c) => c.url.includes('/skill-tree/nodes/numpy') && c.init?.method === 'PATCH',
      );
      expect(patch).toBeDefined();
      expect(JSON.parse(String(patch!.init?.body))).toEqual({ status: 'lit' });
      expect(new Headers(patch!.init?.headers).get('If-Match')).toBe('W/"tree-etag-1"');
    });
    // Optimistic update: the row flips to 扎实 before the refetch lands.
    expect(await within(card).findByText('扎实')).toBeInTheDocument();
  });
});
