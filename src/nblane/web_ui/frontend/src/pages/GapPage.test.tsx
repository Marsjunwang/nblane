import { fireEvent, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';

import { jsonResponse, renderWithProviders } from '../test/render';
import { GapPage } from './GapPage';

const RESULT = {
  profile: 'alice',
  task: '用机械臂完成抓取任务',
  top_matches: [{ id: 'manipulation', label: 'Manipulation', score: 3, source: 'rule' }],
  closure: [
    { id: 'robotics', label: 'Robotics', status: 'solid', is_gap: false, evidence_count: 2 },
    {
      id: 'manipulation',
      label: 'Manipulation',
      status: 'learning',
      is_gap: true,
      evidence_count: 0,
    },
    { id: 'grasp_planning', label: 'Grasp Planning', status: 'locked', is_gap: true, evidence_count: 0 },
  ],
  gaps: ['manipulation', 'grasp_planning'],
  strong: ['robotics'],
  can_solve: false,
  coverage: 1 / 3,
  next_steps: [
    "Advance 'manipulation' (Manipulation) from learning -> learning/solid",
  ],
  roots_from_rule: ['manipulation'],
  roots_from_llm: [],
  learned_merged: false,
};

afterEach(() => {
  vi.unstubAllGlobals();
});

function renderPage() {
  return renderWithProviders(
    <Routes>
      <Route path="/p/:name/gap" element={<GapPage />} />
    </Routes>,
    '/p/alice/gap',
  );
}

describe('GapPage', () => {
  it('posts the task and renders matched and gap sections', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes('/profiles/alice/gap/analyze')) {
        expect(init?.method).toBe('POST');
        expect(JSON.parse(String(init?.body))).toEqual({
          task: '用机械臂完成抓取任务',
          use_llm: false,
        });
        return jsonResponse(200, RESULT);
      }
      return jsonResponse(404, { code: 'not_found', message: 'not found' });
    });
    vi.stubGlobal('fetch', fetchMock);

    renderPage();
    fireEvent.change(screen.getByLabelText('任务描述'), {
      target: { value: '用机械臂完成抓取任务' },
    });
    fireEvent.click(screen.getByRole('button', { name: '分析' }));

    // Summary: task echo, verdict badge, coverage.
    expect(await screen.findByText('alice · 差距分析')).toBeInTheDocument();
    expect(await screen.findByText('存在差距')).toBeInTheDocument();
    expect(screen.getByText('技能覆盖率 33%')).toBeInTheDocument();

    // Matched/strong section.
    const strongSection = screen.getByTestId('gap-strong-section');
    expect(strongSection).toHaveTextContent('已具备的技能 (1)');
    expect(strongSection).toHaveTextContent('Robotics');
    expect(strongSection).toHaveTextContent('solid');

    // Gap section with status badges and suggested actions.
    const gapSection = screen.getByTestId('gap-missing-section');
    expect(gapSection).toHaveTextContent('能力差距 (2)');
    expect(gapSection).toHaveTextContent('Manipulation');
    expect(gapSection).toHaveTextContent('Grasp Planning');
    expect(screen.getByText('建议行动')).toBeInTheDocument();
    expect(screen.getByText(/Advance 'manipulation'/)).toBeInTheDocument();

    // LLM hint card.
    expect(screen.getByText(/LLM 深度分析需要后续异步任务支持/)).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('validates an empty task client-side without posting', async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);

    renderPage();
    fireEvent.click(screen.getByRole('button', { name: '分析' }));

    expect(await screen.findByText('请先描述要分析的任务。')).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('shows an error alert when the analysis request fails', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        jsonResponse(422, {
          code: 'no_roots',
          message: 'No skill nodes matched. Enable rule or AI matching, or pick a node manually.',
        }),
      ),
    );

    renderPage();
    fireEvent.change(screen.getByLabelText('任务描述'), {
      target: { value: 'zzqq nothing' },
    });
    fireEvent.click(screen.getByRole('button', { name: '分析' }));

    expect(await screen.findByText('分析失败')).toBeInTheDocument();
    expect(screen.getByText(/No skill nodes matched/)).toBeInTheDocument();
  });

  it('creates a kanban learning task from a gap node', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes('/profiles/alice/gap/analyze')) {
        return jsonResponse(200, RESULT);
      }
      if (url.includes('/profiles/alice/gap/intake')) {
        expect(JSON.parse(String(init?.body))).toEqual({
          title: '学习 Manipulation',
          node_id: 'manipulation',
          why: '用机械臂完成抓取任务',
          section: 'Queue',
        });
        return jsonResponse(201, {
          ok: true,
          card: { title: '学习 Manipulation', done: false },
          section: 'Queue',
        });
      }
      return jsonResponse(404, { code: 'not_found', message: 'not found' });
    });
    vi.stubGlobal('fetch', fetchMock);

    renderPage();
    fireEvent.change(screen.getByLabelText('任务描述'), {
      target: { value: '用机械臂完成抓取任务' },
    });
    fireEvent.click(screen.getByRole('button', { name: '分析' }));
    const gapSection = await screen.findByTestId('gap-missing-section');
    await waitFor(() => expect(gapSection).toHaveTextContent('Manipulation'));

    const buttons = screen.getAllByRole('button', { name: '加入看板' });
    fireEvent.click(buttons[0]);

    expect(await screen.findByText('已创建')).toBeInTheDocument();
    expect(screen.getByText('学习任务已加入看板 Queue。')).toBeInTheDocument();
  });
});
