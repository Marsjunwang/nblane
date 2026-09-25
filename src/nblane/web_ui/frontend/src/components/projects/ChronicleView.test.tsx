// ChronicleView 键盘导航 + inspector: 阅读顺序首选中、j/k 遍历边界(含
// chip 成员可达)、选中滚动、画布就近选中、邻居跳选、Enter 铭文卡、Esc 取消。

import { fireEvent, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type {
  KanbanSection,
  KanbanTask,
  ProjectsBoardProject,
  ProjectsBoardResponse,
} from '../../api/types';
import { renderWithProviders } from '../../test/render';
import type { LaneGroup } from './lanes';
import { ChronicleView } from './ChronicleView';

const TODAY = '2026-09-25';

const PROJECT = {
  id: 'p1',
  title: 'VLA 攻坚',
  status: 'active',
  kind: 'internal',
  queue: [
    {
      id: 'q1',
      title: '排期任务',
      column: 'queue',
      planned_start: '2026-10-01',
      planned_end: '2026-10-05',
    },
  ],
  doing: [],
  someday: [],
} as unknown as ProjectsBoardProject;

const BOARD = {
  today: TODAY,
  north_star: '',
  goals: [],
  habits: [],
  ungrouped_projects: [PROJECT],
  unassigned_tasks: [],
} as unknown as ProjectsBoardResponse;

const GROUPS: LaneGroup[] = [
  { id: '__ungrouped__', title: '未分组', meta: '', target: '', projects: [PROJECT] },
];

function doneTask(id: string, completed: string, started: string | null): KanbanTask {
  return {
    id,
    title: `任务${id}`,
    done: true,
    project_id: 'p1',
    completed_on: completed,
    started_on: started,
  } as unknown as KanbanTask;
}

// 6 个同日完成(标签四层放不下 → 必有 chip 成员)+ 一个独立完成日 + queue。
const SECTIONS = [
  {
    name: 'Done',
    tasks: [
      doneTask('d1', '2026-09-10', '2026-09-01'),
      doneTask('d2', '2026-09-10', '2026-09-02'),
      doneTask('d3', '2026-09-10', '2026-09-03'),
      doneTask('d4', '2026-09-10', '2026-09-04'),
      doneTask('d5', '2026-09-10', '2026-09-05'),
      doneTask('d6', '2026-09-10', null),
      doneTask('solo', '2026-09-20', '2026-09-15'),
    ],
  },
] as unknown as KanbanSection[];

// 蛇形阅读顺序: queue(最新) → solo → 同日 6 个按 started_on → d6(无 started_on 排尾)。
const EXPECTED_ORDER = ['q1', 'solo', 'd1', 'd2', 'd3', 'd4', 'd5', 'd6'];

function renderView() {
  return renderWithProviders(
    <ChronicleView
      board={BOARD}
      groups={GROUPS}
      archivedProjects={[]}
      unassigned={[]}
      kanbanSections={SECTIONS}
      kanbanArchive={[]}
      onEditTask={() => undefined}
    />,
  );
}

function scrollport(): HTMLElement {
  return screen.getByTestId('chronicle-scrollport');
}

function selectedId(): string | null {
  const element = document.querySelector('[data-selected]');
  return element?.getAttribute('data-testid')?.replace('chronicle-event-', '') ?? null;
}

describe('ChronicleView 键盘导航', () => {
  it('无选中时按方向键选中阅读顺序第一个(最新),并自动滚动到可见', () => {
    const scrollSpy = vi.spyOn(window.HTMLElement.prototype, 'scrollIntoView');
    scrollSpy.mockClear();
    renderView();
    expect(selectedId()).toBeNull();
    fireEvent.keyDown(scrollport(), { key: 'j' });
    expect(selectedId()).toBe('q1');
    expect(scrollSpy).toHaveBeenCalled();
  });

  it('j/k 沿蛇形序遍历全部事件(含 chip 成员),首尾钳制', () => {
    renderView();
    // 同日 6 个刻点必有标签挤不进四层 → 存在 chip,其成员也在序列里。
    expect(document.querySelector('[data-testid^="chronicle-chip-"]')).not.toBeNull();
    const walked: string[] = [];
    for (let i = 0; i < EXPECTED_ORDER.length + 2; i += 1) {
      fireEvent.keyDown(scrollport(), { key: 'j' });
      const id = selectedId();
      if (id && walked[walked.length - 1] !== id) {
        walked.push(id);
      }
    }
    expect(walked).toEqual(EXPECTED_ORDER); // 尾端钳制在 d6
    fireEvent.keyDown(scrollport(), { key: 'ArrowRight' });
    expect(selectedId()).toBe('d6');
    for (let i = 0; i < EXPECTED_ORDER.length + 2; i += 1) {
      fireEvent.keyDown(scrollport(), { key: 'k' });
    }
    expect(selectedId()).toBe('q1'); // 首端钳制
    fireEvent.keyDown(scrollport(), { key: 'ArrowLeft' });
    expect(selectedId()).toBe('q1');
  });

  it('点击画布空白处选中最近事件并接管键盘焦点', () => {
    renderView();
    fireEvent.click(scrollport(), { clientX: 220, clientY: 60 });
    expect(selectedId()).not.toBeNull();
    expect(document.activeElement).toBe(scrollport());
  });

  it('inspector 邻居窗口 + 跳选 + Enter 铭文卡 + Esc 取消', async () => {
    renderView();
    // 第一下 j 选中第一个(不移动),所以到 d3 需要 5 下。
    for (let i = 0; i < 5; i += 1) {
      fireEvent.keyDown(scrollport(), { key: 'j' });
    }
    expect(selectedId()).toBe('d3');
    // Inspector: 提示行 + 前 3 / 后 3 邻居,当前行高亮。
    expect(screen.getByTestId('chronicle-inspector-hint')).toHaveTextContent(
      '←/→ 或 j/k 移动 · Enter 详情 · Esc 关闭',
    );
    const rows = document.querySelectorAll('[data-testid^="chronicle-inspector-row-"]');
    expect(rows).toHaveLength(7);
    expect(screen.getByTestId('chronicle-inspector-row-d3')).toHaveAttribute('data-current');
    // 点邻居行跳选。
    fireEvent.click(screen.getByTestId('chronicle-inspector-row-d1'));
    expect(selectedId()).toBe('d1');
    // Enter 打开铭文卡(与点击同卡片;浮层异步挂载,等待出现)。
    fireEvent.keyDown(scrollport(), { key: 'Enter' });
    expect(await screen.findByTestId('chronicle-card-d1')).toBeInTheDocument();
    // Esc 关卡 + 取消选中 + inspector 收起。
    fireEvent.keyDown(scrollport(), { key: 'Escape' });
    expect(selectedId()).toBeNull();
    expect(screen.queryByTestId('chronicle-inspector')).toBeNull();
    await waitFor(() =>
      expect(screen.queryByTestId('chronicle-card-d1')).not.toBeInTheDocument(),
    );
  });
});
