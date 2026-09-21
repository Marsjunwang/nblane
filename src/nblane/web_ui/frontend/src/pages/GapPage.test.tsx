import { act, fireEvent, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
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
  analysis_mode: 'rule',
  llm_router_error: null,
};

const LLM_RESULT = {
  ...RESULT,
  top_matches: [
    { id: 'manipulation', label: 'Manipulation', score: 3, source: 'rule' },
    { id: 'navigation', label: 'Navigation', score: 0, source: 'llm' },
  ],
  closure: [
    ...RESULT.closure,
    { id: 'navigation', label: 'Navigation', status: 'locked', is_gap: true, evidence_count: 0 },
  ],
  gaps: ['manipulation', 'grasp_planning', 'navigation'],
  coverage: 1 / 4,
  roots_from_llm: ['navigation'],
  learned_merged: true,
  analysis_mode: 'rule+llm',
  llm_router_error: null,
};

const CREATED_JOB = {
  ok: true,
  job_id: 'job-abc123',
  job: {
    job_id: 'job-abc123',
    profile: 'alice',
    kind: 'gap-analysis',
    status: 'queued',
    phase: 'queued',
    message: 'Queued gap deep analysis.',
    created_at: 1,
    started_at: 0,
    finished_at: 0,
    elapsed_ms: 0,
    error: null,
  },
};

type Listener = (event: Event) => void;

/** Minimal EventSource stand-in for jsdom (which has no EventSource). */
class MockEventSource {
  static instances: MockEventSource[] = [];

  readonly url: string;
  closed = false;
  private listeners = new Map<string, Listener[]>();

  constructor(url: string) {
    this.url = url;
    MockEventSource.instances.push(this);
  }

  addEventListener(type: string, listener: Listener) {
    const arr = this.listeners.get(type) ?? [];
    arr.push(listener);
    this.listeners.set(type, arr);
  }

  removeEventListener() {}

  close() {
    this.closed = true;
  }

  emit(type: string, data: unknown) {
    const event = new MessageEvent(type, { data: JSON.stringify(data) });
    for (const listener of this.listeners.get(type) ?? []) {
      listener(event);
    }
  }

  emitTransportError() {
    for (const listener of this.listeners.get('error') ?? []) {
      listener(new Event('error'));
    }
  }
}

beforeEach(() => {
  MockEventSource.instances = [];
  vi.stubGlobal('EventSource', MockEventSource);
});

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

function fillAndStartDeep() {
  fireEvent.change(screen.getByLabelText('任务描述'), {
    target: { value: '用机械臂完成抓取任务' },
  });
  fireEvent.click(screen.getByRole('button', { name: '深度分析(LLM)' }));
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

    // Rule results point at the deep-analysis button (no LLM badge yet).
    expect(screen.getByText(/以上为规则匹配结果/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '深度分析(LLM)' })).toBeInTheDocument();
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

  it('validates an empty task for the deep analysis without posting', async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);

    renderPage();
    fireEvent.click(screen.getByRole('button', { name: '深度分析(LLM)' }));

    expect(await screen.findByText('请先描述要分析的任务。')).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
    expect(MockEventSource.instances).toHaveLength(0);
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

describe('GapPage deep analysis (LLM job + SSE)', () => {
  function stubJobCreation() {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes('/profiles/alice/gap/analyze')) {
        expect(JSON.parse(String(init?.body))).toEqual({
          task: '用机械臂完成抓取任务',
          use_llm: true,
        });
        return jsonResponse(202, CREATED_JOB);
      }
      return jsonResponse(404, { code: 'not_found', message: 'not found' });
    });
    vi.stubGlobal('fetch', fetchMock);
    return fetchMock;
  }

  it('creates a job, streams progress phases, and renders the LLM result', async () => {
    stubJobCreation();
    renderPage();
    fillAndStartDeep();

    // Progress card appears with the queued phase; the stream opened.
    expect(await screen.findByTestId('gap-deep-progress')).toBeInTheDocument();
    expect(screen.getByText('排队中')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '深度分析(LLM)' })).toBeDisabled();
    expect(MockEventSource.instances).toHaveLength(1);
    const source = MockEventSource.instances[0];
    expect(source.url).toBe('/api/v1/profiles/alice/jobs/job-abc123/stream');

    act(() => {
      source.emit('progress', {
        ok: true,
        job: { ...CREATED_JOB.job, status: 'running', phase: 'routing' },
        event: { seq: 1, phase: 'routing', message: 'LLM is routing the task.' },
      });
    });
    expect(await screen.findByText('路由中')).toBeInTheDocument();

    act(() => {
      source.emit('progress', {
        ok: true,
        job: { ...CREATED_JOB.job, status: 'running', phase: 'merging' },
        event: { seq: 2, phase: 'merging', message: 'Merging matches.' },
      });
    });
    expect(await screen.findByText('合并中')).toBeInTheDocument();

    act(() => {
      source.emit('done', {
        ok: true,
        job: { ...CREATED_JOB.job, status: 'done', phase: 'done' },
        result: LLM_RESULT,
      });
    });

    // Result replaces progress; LLM origin is annotated on the same layout.
    expect(await screen.findByText('LLM 深度分析')).toBeInTheDocument();
    expect(screen.queryByTestId('gap-deep-progress')).not.toBeInTheDocument();
    expect(source.closed).toBe(true);
    const origins = screen.getByTestId('gap-root-origins');
    expect(origins).toHaveTextContent('根因来源:规则 1 项(manipulation) · LLM 1 项(navigation)');
    expect(origins).toHaveTextContent('LLM 关键词已并入学习库');
    const gapSection = screen.getByTestId('gap-missing-section');
    expect(gapSection).toHaveTextContent('能力差距 (3)');
    expect(gapSection).toHaveTextContent('Navigation');
    // The rule-only hint alert is gone for deep results.
    expect(screen.queryByText(/以上为规则匹配结果/)).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: '深度分析(LLM)' })).toBeEnabled();
  });

  it('renders the degraded alert when the LLM router failed', async () => {
    stubJobCreation();
    renderPage();
    fillAndStartDeep();
    expect(await screen.findByTestId('gap-deep-progress')).toBeInTheDocument();
    const source = MockEventSource.instances[0];

    act(() => {
      source.emit('done', {
        ok: true,
        job: { ...CREATED_JOB.job, status: 'done', phase: 'done' },
        result: {
          ...LLM_RESULT,
          roots_from_llm: [],
          learned_merged: false,
          llm_router_error: 'LLM not configured',
        },
      });
    });

    const degraded = await screen.findByTestId('gap-llm-degraded');
    expect(degraded).toHaveTextContent('LLM 不可用,已回退为规则分析');
    expect(degraded).toHaveTextContent('LLM not configured');
    // The rule-rooted result still renders.
    expect(screen.getByTestId('gap-missing-section')).toBeInTheDocument();
  });

  it('shows a failure alert when the job fails', async () => {
    stubJobCreation();
    renderPage();
    fillAndStartDeep();
    expect(await screen.findByTestId('gap-deep-progress')).toBeInTheDocument();
    const source = MockEventSource.instances[0];

    act(() => {
      source.emit('error', {
        ok: false,
        job: { ...CREATED_JOB.job, status: 'failed', phase: 'failed' },
        error: { code: 'no_roots', message: 'No skill nodes matched.' },
      });
    });

    const alert = await screen.findByTestId('gap-deep-error');
    expect(alert).toHaveTextContent('No skill nodes matched.');
    expect(screen.queryByTestId('gap-deep-progress')).not.toBeInTheDocument();
    expect(source.closed).toBe(true);
  });

  it('shows a stream-failure alert on transport errors', async () => {
    stubJobCreation();
    renderPage();
    fillAndStartDeep();
    expect(await screen.findByTestId('gap-deep-progress')).toBeInTheDocument();
    const source = MockEventSource.instances[0];

    act(() => {
      source.emitTransportError();
    });

    const alert = await screen.findByTestId('gap-deep-error');
    expect(alert).toHaveTextContent('进度流中断');
    expect(source.closed).toBe(true);
  });

  it('shows a creation error when the job cannot be created', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        jsonResponse(422, { code: 'empty_task', message: 'Empty task text.' }),
      ),
    );
    renderPage();
    fillAndStartDeep();

    expect(await screen.findByText('创建深度分析任务失败')).toBeInTheDocument();
    expect(screen.getByText('Empty task text.')).toBeInTheDocument();
    expect(MockEventSource.instances).toHaveLength(0);
  });

  it('unsubscribes the SSE stream on unmount', async () => {
    stubJobCreation();
    const view = renderPage();
    fillAndStartDeep();
    expect(await screen.findByTestId('gap-deep-progress')).toBeInTheDocument();
    const source = MockEventSource.instances[0];
    expect(source.closed).toBe(false);

    view.unmount();
    expect(source.closed).toBe(true);
  });
});
