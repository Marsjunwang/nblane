/* Divination: pure yao-row ordering + HexagramSymbol rendering + the serious
 * cast 化为任务 bridge (gap nodes → POST /gap/intake per node). */
import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { jsonResponse, renderWithProviders } from '../test/render';
import { DivinationPanel, HexagramSymbol, gapNodesOf, yaoRows } from './Divination';

describe('yaoRows (卦象爻序)', () => {
  it('renders bottom-up symbol_lines top-down (初爻在下)', () => {
    // 火天大有 lines bottom-up: 111101 → top-down display: 101111
    expect(yaoRows([1, 1, 1, 1, 0, 1])).toEqual([true, false, true, true, true, true]);
  });

  it('maps 1 → solid (阳) and 0 → broken (阴)', () => {
    expect(yaoRows([0, 0, 0, 0, 0, 0])).toEqual([false, false, false, false, false, false]);
    expect(yaoRows([1, 1, 1, 1, 1, 1])).toEqual([true, true, true, true, true, true]);
  });

  it('truncates defensively to 6 yao', () => {
    expect(yaoRows([1, 0, 1, 0, 1, 0, 1, 1])).toHaveLength(6);
  });
});

describe('HexagramSymbol', () => {
  it('renders 6 yao rows with solid/broken classes in display order', () => {
    render(<HexagramSymbol lines={[1, 1, 1, 1, 0, 1]} />);
    const sym = screen.getByTestId('hexagram-symbol');
    const rows = sym.querySelectorAll('.hex-yao');
    expect(rows).toHaveLength(6);
    expect(rows[0].className).toContain('solid'); // top yao = lines[5] = 1
    expect(rows[1].className).toContain('broken'); // lines[4] = 0
    expect(rows[5].className).toContain('solid'); // bottom yao = lines[0] = 1
  });

  it('supports the 摇卦 animated state', () => {
    render(<HexagramSymbol lines={[1, 1, 1, 1, 1, 1]} animated />);
    expect(screen.getByTestId('hexagram-symbol').className).toContain('casting');
  });
});

describe('gapNodesOf (化为任务 material)', () => {
  it('keeps only is_gap nodes from anchors.gap.closure', () => {
    const result = {
      anchors: {
        gap: {
          closure: [
            { id: 'n1', label: 'ROS2', status: 'locked', is_gap: true },
            { id: 'n2', label: '运动学', status: 'solid', is_gap: false },
            { id: 'n3', label: '强化学习', status: 'locked', is_gap: true },
          ],
        },
      },
    } as never;
    expect(gapNodesOf(result).map((n) => n.id)).toEqual(['n1', 'n3']);
  });

  it('is empty for play casts / missing anchors', () => {
    expect(gapNodesOf(null)).toEqual([]);
    expect(gapNodesOf({ anchors: {} } as never)).toEqual([]);
  });
});

describe('DivinationPanel 化为任务', () => {
  const PLAY_RESPONSE = {
    profile: 'alice',
    mode: 'play',
    question: '',
    hexagram: { name: '火天大有', symbol_lines: [1, 1, 1, 1, 0, 1], judgment: '元亨。' },
    reading: '戏占一卦。',
    anchors: {},
    source: 'rule',
    generated_on: '2026-09-24',
  };
  const SERIOUS_RESPONSE = {
    ...PLAY_RESPONSE,
    mode: 'serious',
    question: '三个月内接手机械臂项目',
    reading: '卦象所示,所缺 2 处。',
    anchors: {
      gap: {
        can_solve: false,
        gap_labels: ['ROS2', '运动控制'],
        strong_labels: ['Python'],
        closure: [
          { id: 'ros2', label: 'ROS2', status: 'locked', is_gap: true },
          { id: 'python', label: 'Python', status: 'solid', is_gap: false },
          { id: 'motion-control', label: '运动控制', status: 'locked', is_gap: true },
        ],
      },
    },
  };

  beforeEach(() => {
    // jsdom has no canvas/rAF; the RitualCanvas pixels are not under test.
    vi.stubGlobal('requestAnimationFrame', () => 1);
    vi.stubGlobal('cancelAnimationFrame', () => {});
    window.HTMLCanvasElement.prototype.getContext = (() =>
      new Proxy({}, { get: () => () => undefined, set: () => true })) as never;
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('serious cast turns each gap node into one kanban task via /gap/intake', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith('/profiles/alice/divination')) {
        const body = JSON.parse(String(init?.body));
        return jsonResponse(200, body.mode === 'serious' ? SERIOUS_RESPONSE : PLAY_RESPONSE);
      }
      if (url.endsWith('/profiles/alice/gap/intake')) {
        return jsonResponse(201, { ok: true, card: {}, section: 'Queue' });
      }
      return jsonResponse(404, { code: 'not_found', message: url });
    });
    vi.stubGlobal('fetch', fetchMock);
    renderWithProviders(<DivinationPanel profile="alice" open onClose={() => {}} />);

    // Opening the panel auto-casts 戏占; switch to 正占 and cast for real.
    await screen.findByTestId('divination-reading');
    fireEvent.click(screen.getByTestId('divination-mode-serious'));
    fireEvent.change(screen.getByTestId('divination-question'), {
      target: { value: '三个月内接手机械臂项目' },
    });
    fireEvent.click(screen.getByTestId('divination-cast'));

    const intakeBtn = await screen.findByTestId('divination-intake');
    expect(intakeBtn).toHaveTextContent('化为任务(2 处所缺)');
    fireEvent.click(intakeBtn);

    await screen.findByTestId('divination-intake-done');
    const intakes = fetchMock.mock.calls.filter(([url]) =>
      String(url).endsWith('/profiles/alice/gap/intake'),
    );
    expect(intakes).toHaveLength(2);
    const bodies = intakes.map(([, init]) => JSON.parse(String(init?.body)));
    expect(bodies).toEqual([
      {
        title: '学习 ROS2',
        node_id: 'ros2',
        why: '三个月内接手机械臂项目',
        section: 'Queue',
      },
      {
        title: '学习 运动控制',
        node_id: 'motion-control',
        why: '三个月内接手机械臂项目',
        section: 'Queue',
      },
    ]);
    // Success note carries the /projects deep link.
    const link = screen.getByTestId('divination-intake-link');
    expect(link).toHaveAttribute('href', '/p/alice/projects');
  });

  it('play casts show no 化为任务 action', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => jsonResponse(200, PLAY_RESPONSE)),
    );
    renderWithProviders(<DivinationPanel profile="alice" open onClose={() => {}} />);

    await screen.findByTestId('divination-reading');
    expect(screen.queryByTestId('divination-intake-zone')).not.toBeInTheDocument();
  });

  it('intake failure surfaces an inline error and stays retryable', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith('/profiles/alice/divination')) {
        return jsonResponse(200, SERIOUS_RESPONSE);
      }
      return jsonResponse(422, { code: 'invalid_gap_intake', message: 'empty title' });
    });
    vi.stubGlobal('fetch', fetchMock);
    renderWithProviders(<DivinationPanel profile="alice" open onClose={() => {}} />, '/p/alice/home');

    // Start already in serious mode: flip the tab and cast.
    fireEvent.click(await screen.findByTestId('divination-mode-serious'));
    fireEvent.change(screen.getByTestId('divination-question'), {
      target: { value: '三个月内接手机械臂项目' },
    });
    fireEvent.click(screen.getByTestId('divination-cast'));

    fireEvent.click(await screen.findByTestId('divination-intake'));
    await screen.findByTestId('divination-intake-error');
    // The button is back to its armed state (not stuck on 化为任务…).
    expect(screen.getByTestId('divination-intake')).toHaveTextContent('化为任务(2 处所缺)');
  });
});
