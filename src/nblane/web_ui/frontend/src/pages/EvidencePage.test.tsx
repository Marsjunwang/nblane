import { act, fireEvent, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';

import { jsonResponse, renderWithProviders } from '../test/render';
import { EvidencePage, EvidenceReviewRedirect } from './EvidencePage';

const STAGES = {
  profile: 'alice',
  pending_crystallize_count: 2,
  needs_review_count: 1,
  unlinked_count: 1,
  seated_count: 1,
  strengthen_count: 1,
  deprecated_count: 1,
  risks: [
    {
      skill_id: 'navigation',
      label: 'Navigation',
      status: 'expert',
      risk_level: 'missing_evidence',
      risk_reason: 'expert requires evidence, but none is linked.',
      required_strength: 'strong',
      highest_strength: 'unrated',
      evidence_refs: [],
      score: 0,
      threshold: 100,
      points_needed: 100,
    },
  ],
};

const CANDIDATES = {
  profile: 'alice',
  items: [
    {
      id: 'taskA',
      title: 'Tuned latency',
      completed_on: '2026-01-02',
      project_id: 'project:perf',
      tags: 'perf',
      context: 'perf sprint',
      why: 'cut frame time',
      outcome: '20fps',
      snapshot: '# Tuned latency\nid: taskA\ncontext: perf sprint\nwhy: cut frame time',
      blockers: [],
    },
  ],
};

const REVIEW_QUEUE = {
  profile: 'alice',
  status: 'needs_review',
  q: '',
  limit: 500,
  total: 1,
  items: [
    {
      id: 'ev_2',
      title: 'MoveIt2 workshop notes',
      evidence_type: 'learning',
      date: '2026-07-15',
      url: '',
      review_status: 'needs_review',
      strength: 'unrated',
      confidence: '',
      public_readiness: 'private',
      deprecated: false,
      breakthrough: false,
      usage_count: 0,
      skill_refs: [],
      review_reason: 'missing_strength, needs_review',
    },
  ],
  summary: {
    needs_review_count: 1,
    unlinked_count: 1,
    total_entries: 2,
    deprecated_count: 1,
  },
};

const DETAIL = {
  id: 'ev_2',
  title: 'MoveIt2 workshop notes',
  evidence_type: 'learning',
  review_status: 'needs_review',
  date: '2026-07-15',
  url: '',
  summary: 'Workshop recap',
  source_refs: [],
  strength: '',
  confidence: '',
  public_readiness: 'private',
  project_refs: ['project:perf'],
  experience_refs: [],
  kanban_refs: ['kanban:taskA', 'kanban:taskGone'],
  source_excerpt: '',
  origin: 'kanban_task',
  origin_ref: 'kanban:taskA',
  origin_detail: '',
  original_content: '# MoveIt2 workshop notes\nid: taskA',
  formatted_content: '',
  language: '',
  original_language: 'en',
  original_content_hash: 'sha256:abc',
  source_content_hash: '',
  deprecated: false,
  replaced_by: '',
  skill_refs: [],
  kanban_ref_details: [
    { ref: 'kanban:taskA', task_id: 'taskA', title: 'Tuned latency', status: 'linked' },
    { ref: 'kanban:taskGone', task_id: 'taskGone', title: '', status: 'archived' },
  ],
};

const DRAFT = {
  ok: true,
  profile: 'alice',
  backend: 'rule',
  patch: {
    evidence_entries: [
      {
        type: 'practice',
        title: 'Tuned latency',
        summary: 'Latency cut to 20fps by retuning the planner.',
        origin: 'kanban_task',
        kanban_refs: ['kanban:taskA'],
        original_content: '# Tuned latency\nid: taskA\nwhy: cut frame time',
        original_content_hash: 'sha256:def',
      },
    ],
    node_updates: [{ id: 'ros2_basics', evidence_refs: ['first_1'] }],
  },
  tasks: [
    {
      id: 'taskA',
      title: 'Tuned latency',
      kanban_ref: 'kanban:taskA',
      project_id: 'project:perf',
      completed_on: '2026-01-02',
    },
  ],
  missing: [],
};

const SKILL_TREE = {
  profile: 'alice',
  schema_name: 'robotics-engineer',
  updated: '2026-09-10',
  status_counts: {},
  nodes: [{ id: 'ros2_basics', title: 'ROS 2 Basics', status: 'solid', children: [] }],
};

const SUGGESTIONS = {
  profile: 'alice',
  entry_id: 'ev_2',
  backend: 'rule',
  suggestions: [
    { id: 'ros2_basics', label: 'ROS 2 Basics', category: 'middleware', level: 1, score: 3, source: 'rule' },
  ],
};

function stubFetch(
  intercept?: (url: string, init?: RequestInit) => Response | Promise<Response> | null,
) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const method = init?.method ?? 'GET';
    const intercepted = intercept?.(url, init);
    if (intercepted) {
      return intercepted;
    }
    if (url.includes('/evidence-stages')) {
      return jsonResponse(200, STAGES);
    }
    if (url.includes('/crystallize/candidates')) {
      return jsonResponse(200, CANDIDATES);
    }
    if (url.includes('/crystallize/draft')) {
      const body = JSON.parse(String(init?.body ?? '{}')) as { use_llm?: boolean };
      if (body.use_llm) {
        return jsonResponse(202, {
          ok: true,
          job_id: 'job-test1',
          job: { job_id: 'job-test1', profile: 'alice', kind: 'evidence-crystallize', status: 'queued' },
        });
      }
      return jsonResponse(200, DRAFT);
    }
    if (url.includes('/crystallize/apply')) {
      return jsonResponse(200, {
        ok: true,
        errors: [],
        warnings: [],
        new_evidence_ids: ['ev_new'],
        crystallized_count: 1,
      });
    }
    if (url.includes('/skill-suggestions')) {
      return jsonResponse(200, SUGGESTIONS);
    }
    if (url.includes('/skill-tree')) {
      return jsonResponse(200, SKILL_TREE);
    }
    if (url.includes('/evidence-review')) {
      return jsonResponse(200, REVIEW_QUEUE);
    }
    if (url.match(/\/evidence\/[^/]+$/)) {
      if (method === 'GET') {
        return jsonResponse(200, DETAIL);
      }
    }
    if (url.includes('/evidence/ev_2/review') || url.includes('/evidence/ev_2/edit')) {
      return jsonResponse(200, { ok: true, changed: 1, missing: [], warnings: [] });
    }
    return jsonResponse(404, { code: 'not_found', message: url });
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

function renderPage(route = '/p/alice/evidence') {
  renderWithProviders(
    <Routes>
      <Route path="/p/:name/evidence" element={<EvidencePage />} />
      <Route path="/p/:name/evidence-review" element={<EvidenceReviewRedirect />} />
    </Routes>,
    route,
  );
}

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

function controlledJobStream() {
  class JobEventSource {
    static instances: JobEventSource[] = [];
    listeners: Record<string, ((event: Event) => void)[]> = {};
    closed = false;
    constructor(public url: string) { JobEventSource.instances.push(this); }
    addEventListener(type: string, listener: (event: Event) => void) {
      (this.listeners[type] ??= []).push(listener);
    }
    emit(type: string, payload: unknown) {
      // Deliver even after close to model an already queued browser callback.
      const event = new MessageEvent(type, { data: JSON.stringify(payload) });
      for (const listener of this.listeners[type] ?? []) listener(event);
    }
    close() { this.closed = true; }
  }
  vi.stubGlobal('EventSource', JobEventSource);
  return JobEventSource;
}

async function openDraftStep(ids = ['taskA']) {
  fireEvent.click(await screen.findByTestId('open-crystallize-wizard'));
  for (const id of ids) fireEvent.click(await screen.findByTestId(`wizard-pick-${id}`));
  fireEvent.click(screen.getByRole('button', { name: /下一步/ }));
  await screen.findByTestId('wizard-ai-draft');
}

describe('EvidencePage', () => {
  // Fixture evidence is unrated, so accepting asks first; default to yes.
  beforeEach(() => {
    window.localStorage.clear();
    vi.spyOn(window, 'confirm').mockReturnValue(true);
  });

  it('renders the six stages with persistent counts', async () => {
    stubFetch();
    renderPage();

    expect(await screen.findByText('alice · 证据')).toBeInTheDocument();
    const nav = screen.getByTestId('stage-nav');
    await waitFor(() => {
      for (const [key, count] of [
        ['crystallize', '2'],
        ['review', '1'],
        ['unlinked', '1'],
        ['seated', '1'],
        ['strengthen', '1'],
        ['deprecated', '1'],
      ] as const) {
        const stage = within(nav).getByTestId(`stage-${key}`);
        expect(stage).toHaveTextContent(count);
      }
    });
  });

  it('lists the needs_review queue in the default stage', async () => {
    stubFetch();
    renderPage();

    const row = await screen.findByTestId('evidence-row-ev_2');
    expect(within(row).getByText('MoveIt2 workshop notes')).toBeInTheDocument();
  });

  it('opens the inscription detail card with provenance tombstone', async () => {
    stubFetch();
    renderPage();

    fireEvent.click(await screen.findByTestId('evidence-row-ev_2'));
    const detail = await screen.findByTestId('evidence-detail');
    expect(within(detail).getByText('Workshop recap')).toBeInTheDocument();
    // Missing refs retain a snapshot without falsely promising a task link.
    expect(within(detail).getByText(/Tuned latency/)).toBeInTheDocument();
    expect(within(detail).getByTestId('tombstone-taskGone')).toHaveTextContent('原任务已不可用');
    expect(within(detail).queryByTestId('skill-suggestions')).not.toBeInTheDocument();
    fireEvent.click(within(detail).getByRole('button', { name: '添加关联' }));
    // Rule-tier skill suggestions are offered on demand.
    expect(
      await within(detail).findByTestId('suggest-skill-ros2_basics'),
    ).toBeInTheDocument();
  });

  it.each(['live', 'archived', 'missing'])('opens the source task including %s records', async (location) => {
    const task = { id: 'taskA', title: 'Latest task title', done: true, context: 'Current context',
      outcome: 'Updated outcome', todos: [{ text: 'Verify output', done: true }],
      details: ['Additional detail'], project_id: 'project:perf' };
    const fetchMock = stubFetch((url) => url.endsWith('/kanban') ? jsonResponse(200, {
      profile: 'alice', sections: [{ name: 'Done', tasks: location === 'live' ? [task] : [] }],
      archive: location === 'archived' ? [task] : [],
    }) : null);
    renderPage();
    fireEvent.click(await screen.findByTestId('evidence-row-ev_2'));
    expect(fetchMock.mock.calls.some(([url]) => String(url).endsWith('/kanban'))).toBe(false);
    fireEvent.click(await screen.findByRole('button', { name: '打开原任务' }));
    if (location === 'missing') {
      expect((await screen.findAllByText('原任务已不可用，可切换到保存的原文快照。'))[0]).toBeVisible();
    } else {
      const preview = await screen.findByTestId('source-task-preview');
      expect(preview).toHaveTextContent('Updated outcome');
      expect(preview).toHaveTextContent('Verify output');
      expect(preview).toHaveTextContent(location === 'archived' ? '已归档任务记录' : '当前任务记录');
    }
    expect(fetchMock.mock.calls.every(([, init]) => !init?.method || init.method === 'GET')).toBe(true);
  });

  it('keeps the original snapshot separate from the refined evidence', async () => {
    stubFetch((url) => url.endsWith('/evidence/ev_2') ? jsonResponse(200, {
      ...DETAIL, formatted_content: 'Refined achievement',
    }) : null);
    renderPage();
    fireEvent.click(await screen.findByTestId('evidence-row-ev_2'));
    const detail = await screen.findByTestId('evidence-detail');
    expect(within(detail).getByText('Refined achievement')).toBeVisible();
    expect(within(detail).queryByText(/id: taskA/)).not.toBeInTheDocument();
    expect(within(detail).queryByTestId('skill-suggestions')).not.toBeInTheDocument();
    fireEvent.click(within(detail).getByRole('button', { name: '查看结晶时原文' }));
    const original = await screen.findByTestId('evidence-original-snapshot');
    expect(original).toHaveTextContent('id: taskA');
    expect(original).not.toHaveTextContent('Refined achievement');
  });

  it('keeps the inline original open when switching evidence and remembers the preference', async () => {
    stubFetch((url) => {
      if (url.includes('/evidence-review')) return jsonResponse(200, {
        ...REVIEW_QUEUE, items: [REVIEW_QUEUE.items[0], { ...REVIEW_QUEUE.items[0], id: 'ev_next', title: 'Next evidence' }],
      });
      if (url.endsWith('/evidence/ev_next')) return jsonResponse(200, {
        ...DETAIL, id: 'ev_next', title: 'Next evidence', original_content: 'Next original\ntodos:\n- [x] next TODO',
      });
      return null;
    });
    renderPage('/p/alice/evidence?focus=ev_2');
    fireEvent.click(await screen.findByTestId('evidence-row-ev_2'));
    fireEvent.click(await screen.findByRole('button', { name: '查看结晶时原文' }));
    expect(await screen.findByTestId('evidence-source-panel')).toBeVisible();
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(screen.getByTestId('evidence-original-snapshot')).toHaveTextContent('id: taskA');
    fireEvent.click(screen.getByTestId('evidence-row-ev_next'));
    await waitFor(() => expect(screen.getByTestId('evidence-original-snapshot')).toHaveTextContent('next TODO'));
    expect(screen.getByTestId('evidence-original-snapshot')).not.toHaveTextContent('id: taskA');
    expect(JSON.parse(localStorage.getItem('nblane-evidence-source-view:alice')!)).toBe('snapshot');
    fireEvent.click(within(screen.getByTestId('evidence-source-panel')).getByRole('button', { name: '收起' }));
    expect(screen.queryByTestId('evidence-source-panel')).not.toBeInTheDocument();
    fireEvent.click(screen.getByTestId('evidence-row-ev_2'));
    expect(screen.queryByTestId('evidence-source-panel')).not.toBeInTheDocument();
  });

  it('restores the inline reading mode saved before mounting', async () => {
    localStorage.setItem('nblane-evidence-source-view:alice', JSON.stringify('snapshot'));
    stubFetch();
    renderPage();
    fireEvent.click(await screen.findByTestId('evidence-row-ev_2'));
    expect(await screen.findByTestId('evidence-original-snapshot')).toHaveTextContent('id: taskA');
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('does not promise a snapshot when legacy evidence has none', async () => {
    stubFetch((url) => url.endsWith('/evidence/ev_2') ? jsonResponse(200, {
      ...DETAIL, original_content: '', kanban_ref_details: [],
    }) : null);
    renderPage();
    fireEvent.click(await screen.findByTestId('evidence-row-ev_2'));
    const detail = await screen.findByTestId('evidence-detail');
    expect(within(detail).getByText('此证据未保存原文快照。')).toBeVisible();
    expect(within(detail).queryByRole('button', { name: '查看结晶时原文' })).not.toBeInTheDocument();
  });

  it('accept action posts to the single-entry review endpoint', async () => {
    const fetchMock = stubFetch();
    renderPage();

    fireEvent.click(await screen.findByTestId('evidence-row-ev_2'));
    fireEvent.click(await screen.findByTestId('evidence-accept'));
    await waitFor(() => {
      const calls = fetchMock.mock.calls.map((call) => ({
        url: String(call[0]),
        init: call[1],
      }));
      const accept = calls.find(
        (call) => call.url.includes('/evidence/ev_2/review') && call.init?.method === 'POST',
      );
      expect(accept).toBeTruthy();
      expect(JSON.parse(String(accept!.init?.body))).toMatchObject({ action: 'accept' });
    });
  });

  it('quick review mode accepts with the a key', async () => {
    const fetchMock = stubFetch();
    renderPage();

    await screen.findByTestId('evidence-row-ev_2');
    fireEvent.click(screen.getByTestId('quick-review-toggle'));
    fireEvent.keyDown(window, { key: 'a' });
    await waitFor(() => {
      const urls = fetchMock.mock.calls.map((call) => String(call[0]));
      expect(urls.some((url) => url.includes('/evidence/ev_2/review'))).toBe(true);
    });
  });

  it('switches to the strengthen stage and shows the risk detail', async () => {
    stubFetch();
    renderPage();

    fireEvent.click(await screen.findByTestId('stage-strengthen'));
    fireEvent.click(await screen.findByTestId('risk-navigation'));
    const detail = await screen.findByTestId('risk-detail');
    expect(within(detail).getByText(/expert requires evidence/)).toBeInTheDocument();
    expect(within(detail).getByTestId('risk-score')).toHaveTextContent('0 / 100，还差 100 分');
    expect(within(detail).getByText('精通')).toBeInTheDocument();
    // Keep the target skill and open all reviewed evidence, including seated rows.
    fireEvent.click(within(detail).getByTestId('risk-goto-unlinked'));
    expect(await screen.findByRole('dialog', { name: '为「Navigation」挂证据' })).toBeVisible();
  });

  it.each([false, true])('links seated evidence while retaining fresh relations (conflict=%s)', async (conflict) => {
    const posts: { body: unknown; etag: string }[] = [];
    let detailGets = 0;
    const fetchMock = stubFetch((url, init) => {
      if (url.includes('/skill-tree')) return new Response(JSON.stringify(SKILL_TREE), {
        headers: { 'Content-Type': 'application/json', ETag: '"tree-fresh"' },
      });
      if (url.includes('/evidence-review') && url.includes('status=reviewed')) return jsonResponse(200, {
        ...REVIEW_QUEUE, status: 'reviewed', items: [
          { ...REVIEW_QUEUE.items[0], review_status: 'reviewed', usage_count: 1, skill_refs: ['old-skill'] },
          { ...REVIEW_QUEUE.items[0], id: 'ev_free', title: 'Unlinked', review_status: 'reviewed', usage_count: 0 },
        ],
      });
      if (url.endsWith('/evidence/ev_2') && (!init?.method || init.method === 'GET')) {
        detailGets += 1;
        return jsonResponse(200, { ...DETAIL, review_status: 'reviewed', skill_refs: ['old-skill', 'newly-added-elsewhere'] });
      }
      if (url.endsWith('/skill-links') && init?.method === 'POST') {
        posts.push({ body: JSON.parse(String(init.body)), etag: (init.headers as Record<string, string>)['If-Match'] });
        return conflict ? jsonResponse(412, { code: 'etag_mismatch', message: '关联已变化，请重新选择' })
          : jsonResponse(200, { ok: true, entry_id: 'ev_2', skill_ids: ['old-skill', 'newly-added-elsewhere', 'navigation'] });
      }
      return null;
    });
    renderPage('/p/alice/evidence?stage=strengthen');
    fireEvent.click(await screen.findByTestId('risk-navigation'));
    fireEvent.click(screen.getByTestId('risk-goto-unlinked'));
    const row = await screen.findByTestId('risk-evidence-ev_2');
    expect(row).toHaveTextContent('已入座');
    expect(await screen.findByTestId('risk-evidence-ev_free')).toHaveTextContent('待关联');
    const link = within(row).getByRole('button', { name: '挂到此技能' });
    await waitFor(() => expect(link).toBeEnabled());
    fireEvent.click(link);
    if (conflict) {
      expect(await screen.findByTestId('conflict-alert')).toHaveTextContent('数据已被他人修改');
    } else {
      expect(await within(row).findByRole('button', { name: '已关联此技能' })).toBeDisabled();
    }
    expect(posts).toEqual([{ body: { skill_ids: ['old-skill', 'newly-added-elsewhere', 'navigation'] }, etag: '"tree-fresh"' }]);
    expect(detailGets).toBe(1);
    const urls = fetchMock.mock.calls.map(([url]) => String(url));
    expect(urls.findIndex((url) => url.includes('/skill-tree'))).toBeLessThan(urls.findIndex((url) => url.endsWith('/evidence/ev_2')));
  });

  it('待关联 lists only reviewed rows without skill links', async () => {
    const reviewed = {
      ...REVIEW_QUEUE,
      status: 'reviewed',
      items: [
        { ...REVIEW_QUEUE.items[0], id: 'ev_free', title: 'Unlinked note', review_status: 'reviewed', usage_count: 0 },
        { ...REVIEW_QUEUE.items[0], id: 'ev_seat', title: 'Seated note', review_status: 'reviewed', usage_count: 2 },
      ],
    };
    stubFetch((url) =>
      url.includes('/evidence-review') && url.includes('status=reviewed') ? jsonResponse(200, reviewed) : null,
    );
    renderPage('/p/alice/evidence?stage=unlinked');

    expect(await screen.findByTestId('evidence-row-ev_free')).toBeInTheDocument();
    expect(screen.queryByTestId('evidence-row-ev_seat')).not.toBeInTheDocument();
  });

  it('asks before accepting unrated evidence and does nothing when declined', async () => {
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false);
    const fetchMock = stubFetch();
    renderPage();

    fireEvent.click(await screen.findByTestId('evidence-row-ev_2'));
    fireEvent.click(await screen.findByTestId('evidence-accept'));
    expect(confirm).toHaveBeenCalledWith(expect.stringContaining('还没评分量'));
    const posts = fetchMock.mock.calls.filter(
      (call) => String(call[0]).includes('/evidence/ev_2/review') && call[1]?.method === 'POST',
    );
    expect(posts).toHaveLength(0);
  });

  it('runs the rule crystallize wizard end-to-end', async () => {
    const fetchMock = stubFetch();
    renderPage();

    fireEvent.click(await screen.findByTestId('open-crystallize-wizard'));
    // Mantine Modal portals its content; query at screen level.
    fireEvent.click(await screen.findByTestId('wizard-pick-taskA'));
    fireEvent.click(screen.getByRole('button', { name: /下一步/ }));
    fireEvent.click(await screen.findByTestId('wizard-rule-draft'));

    const row = await screen.findByTestId('wizard-row-0');
    expect(within(row).getByText('Tuned latency')).toBeInTheDocument();
    // Bug-2 regression: summary, skill hint and snapshot preview all render.
    expect(within(row).getByTestId('wizard-row-summary-0')).toHaveTextContent(
      'Latency cut to 20fps',
    );
    expect(within(row).getByTestId('wizard-row-skills-0')).toHaveTextContent('ros2_basics');
    fireEvent.click(within(row).getByTestId('wizard-row-snapshot-0'));
    expect(within(row).getByTestId('wizard-row-snapshot-text-0')).toHaveTextContent(
      'cut frame time',
    );
    fireEvent.click(screen.getByTestId('wizard-apply'));

    await waitFor(() => {
      const calls = fetchMock.mock.calls.map((call) => ({
        url: String(call[0]),
        init: call[1],
      }));
      const applied = calls.find((call) => call.url.includes('/crystallize/apply'));
      expect(applied).toBeTruthy();
      expect(JSON.parse(String(applied!.init?.body))).toMatchObject({
        task_ids: ['taskA'],
        include_evidence: [true],
      });
    });
  });

  it('invalidates every crystallize read model after successful apply', async () => {
    const fetchMock = stubFetch();
    renderPage();

    fireEvent.click(await screen.findByTestId('open-crystallize-wizard'));
    fireEvent.click(await screen.findByTestId('wizard-pick-taskA'));
    fireEvent.click(screen.getByRole('button', { name: /下一步/ }));
    fireEvent.click(await screen.findByTestId('wizard-rule-draft'));
    await screen.findByTestId('wizard-row-0');
    fireEvent.click(screen.getByTestId('wizard-apply'));

    await waitFor(() => {
      const urls = fetchMock.mock.calls.map((call) => String(call[0]));
      expect(urls.some((url) => url.includes('/crystallize/apply'))).toBe(true);
      // Only queries mounted by the current page refetch immediately. The
      // hook also invalidates unmounted read models for the next visit.
      expect(urls.some((url) => url.includes('/kanban'))).toBe(false);
    });
  });

  it('AI draft failure shows a friendly error and degrades to rule draft', async () => {
    // Fake EventSource that fails the job with a server error frame. (A bare
    // transport error is a dropped connection: followJob re-attaches instead
    // of failing, see contentJobs.test.ts.)
    class FailingEventSource {
      static instance: FailingEventSource;
      listeners: Record<string, ((event: Event) => void)[]> = {};
      constructor(public url: string) {
        FailingEventSource.instance = this;
        setTimeout(
          () =>
            this.emit(
              'error',
              new MessageEvent('error', {
                data: JSON.stringify({ ok: false, error: { code: 'job_failed', message: '模型超时' } }),
              }),
            ),
          0,
        );
      }
      addEventListener(type: string, listener: (event: Event) => void) {
        (this.listeners[type] ??= []).push(listener);
      }
      emit(type: string, event: Event) {
        for (const listener of this.listeners[type] ?? []) listener(event);
      }
      close() {}
    }
    vi.stubGlobal('EventSource', FailingEventSource);
    stubFetch();
    renderPage();

    fireEvent.click(await screen.findByTestId('open-crystallize-wizard'));
    fireEvent.click(await screen.findByTestId('wizard-pick-taskA'));
    fireEvent.click(screen.getByRole('button', { name: /下一步/ }));
    fireEvent.click(await screen.findByTestId('wizard-ai-draft'));

    // The spinner must resolve into a visible error with a degrade action.
    const alert = await screen.findByTestId('wizard-ai-error');
    expect(alert).toHaveTextContent('规则草稿');
    expect(within(alert).getByText('模型超时', { exact: true })).toBeInTheDocument();
    expect(alert.textContent?.match(/AI 草稿失败/g)).toHaveLength(1);
    expect(screen.queryByTestId('wizard-progress')).not.toBeInTheDocument();

    fireEvent.click(within(alert).getByTestId('wizard-degrade-rule'));
    // Rule fallback lands on the grading step with the draft visible.
    expect(await screen.findByTestId('wizard-row-0')).toBeInTheDocument();
  });

  it('keeps successful AI entries reviewable and identifies failed tasks without marking them as evidence', async () => {
    const Stream = controlledJobStream();
    const failedTask = { ...DRAFT.tasks[0], id: 'taskB', title: 'Controller verification' };
    const fetchMock = stubFetch((url) => {
      if (url.includes('/crystallize/candidates')) return jsonResponse(200, {
        ...CANDIDATES,
        items: [...CANDIDATES.items, { ...CANDIDATES.items[0], ...failedTask }],
      });
      if (url.includes('/crystallize/apply')) return jsonResponse(200, {
        ok: true,
        items: [{ task_id: 'taskA', evidence_ids: ['ev_new'] }],
        errors: [], warnings: [], new_evidence_ids: ['ev_new'], crystallized_count: 1,
      });
      return null;
    });
    renderPage();
    await openDraftStep(['taskA', 'taskB']);
    fireEvent.click(screen.getByTestId('wizard-ai-draft'));
    await waitFor(() => expect(Stream.instances).toHaveLength(1));
    await act(async () => Stream.instances[0].emit('done', { result: {
      ...DRAFT,
      backend: 'llm',
      tasks: [...DRAFT.tasks, failedTask],
      failed_tasks: [{ task_id: 'taskB', title: failedTask.title, message: 'AI 生成超时（180 秒）' }],
    } }));

    const warning = screen.getByTestId('wizard-partial-draft');
    expect(warning).toHaveTextContent('部分任务未生成');
    expect(warning).toHaveTextContent('Controller verification：AI 生成超时（180 秒）');
    expect(warning).toHaveTextContent('未生成的任务会继续留在「待结晶」');
    expect(screen.getByTestId('wizard-row-0')).toHaveTextContent('Tuned latency');
    expect(screen.queryByTestId('wizard-row-1')).not.toBeInTheDocument();
    expect(screen.queryByTestId('wizard-ai-error')).not.toBeInTheDocument();
    expect(screen.queryByTestId('wizard-progress')).not.toBeInTheDocument();
    expect(screen.getByTestId('wizard-apply')).toBeEnabled();

    fireEvent.click(screen.getByTestId('wizard-apply'));
    await waitFor(() => {
      const applied = fetchMock.mock.calls.find(([url]) => String(url).includes('/crystallize/apply'));
      expect(applied).toBeTruthy();
      const body = JSON.parse(String(applied![1]?.body));
      expect(body.task_ids).toEqual(['taskA', 'taskB']);
      expect(body.patch.evidence_entries).toHaveLength(1);
      expect(body.patch.evidence_entries[0].kanban_refs).toEqual(['kanban:taskA']);
      expect(body.include_evidence).toEqual([true]);
    });
  });

  it('shows a polled server failure once without wrapping its retry advice', async () => {
    controlledJobStream();
    stubFetch((url) => url.endsWith('/jobs/job-test1') ? jsonResponse(200, {
      job: { status: 'failed', error: { code: 'crystallize_draft_failed', message: '任务 Controller：AI 生成超时（180 秒）' } },
    }) : null);
    renderPage();
    await openDraftStep();
    vi.useFakeTimers();
    fireEvent.click(screen.getByTestId('wizard-ai-draft'));
    await act(() => vi.advanceTimersByTimeAsync(150_000));
    const alert = screen.getByTestId('wizard-ai-error');
    expect(within(alert).getByText('任务 Controller：AI 生成超时（180 秒）', { exact: true })).toBeInTheDocument();
    expect(alert.textContent?.match(/AI 草稿失败/g)).toHaveLength(1);
    expect(screen.queryByTestId('wizard-progress')).not.toBeInTheDocument();
  });

  it.each([
    { budget: 300, finishAt: 250_000, label: 'server-advertised budget' },
    { budget: undefined, finishAt: 142_000, label: 'legacy per-task budget' },
  ])('keeps a multi-task AI draft alive past 130 seconds with $label', async ({ budget, finishAt }) => {
    const Stream = controlledJobStream();
    const fetchMock = stubFetch((url) => {
      if (url.includes('/crystallize/candidates')) return jsonResponse(200, {
        ...CANDIDATES,
        items: [...CANDIDATES.items, { ...CANDIDATES.items[0], id: 'taskB', title: 'Second task' }],
      });
      if (url.includes('/crystallize/draft')) return jsonResponse(202, {
        job_id: 'job-batch',
        job: { job_id: 'job-batch', status: 'queued', timeout_seconds: budget },
      });
      return null;
    });
    renderPage();
    await openDraftStep(['taskA', 'taskB']);
    vi.useFakeTimers();
    fireEvent.click(screen.getByTestId('wizard-ai-draft'));
    await act(() => vi.advanceTimersByTimeAsync(0));
    expect(Stream.instances).toHaveLength(1);
    await act(() => vi.advanceTimersByTimeAsync(78_000));
    act(() => Stream.instances[0].emit('progress', { event: { phase: 'drafting', message: 'AI 正在生成第 2/2 个任务' } }));
    await act(() => vi.advanceTimersByTimeAsync(finishAt - 78_000));
    expect(screen.getByTestId('wizard-progress')).toHaveTextContent('第 2/2');
    expect(screen.queryByTestId('wizard-ai-error')).not.toBeInTheDocument();
    expect(fetchMock.mock.calls.some(([, init]) => init?.method === 'DELETE')).toBe(false);
    await act(async () => Stream.instances[0].emit('done', { result: { ...DRAFT, backend: 'llm' } }));
    expect(screen.getByTestId('wizard-row-0')).toBeInTheDocument();
    expect(screen.queryByTestId('wizard-progress')).not.toBeInTheDocument();
  });

  it('recovers a completed draft by polling when the terminal stream frame is lost', async () => {
    const Stream = controlledJobStream();
    const fetchMock = stubFetch((url, init) => {
      if (url.endsWith('/jobs/job-test1') && (!init?.method || init.method === 'GET')) {
        return jsonResponse(200, { job: { job_id: 'job-test1', status: 'done' }, result: { ...DRAFT, backend: 'llm' } });
      }
      return null;
    });
    renderPage();
    await openDraftStep();
    vi.useFakeTimers();
    fireEvent.click(screen.getByTestId('wizard-ai-draft'));
    await act(() => vi.advanceTimersByTimeAsync(150_000));
    expect(screen.getByTestId('wizard-row-0')).toBeInTheDocument();
    expect(Stream.instances[0].closed).toBe(true);
    expect(fetchMock.mock.calls.some(([, init]) => init?.method === 'DELETE')).toBe(false);
  });

  it('does not revive a timed-out draft from late cancellation frames and allows retry', async () => {
    const Stream = controlledJobStream();
    const fetchMock = stubFetch((url, init) => {
      if (url.endsWith('/jobs/job-test1')) return jsonResponse(200, {
        job: { job_id: 'job-test1', status: init?.method === 'DELETE' ? 'failed' : 'running',
          error: init?.method === 'DELETE' ? { code: 'job_cancelled', message: '已取消。' } : null },
      });
      return null;
    });
    renderPage();
    await openDraftStep();
    vi.useFakeTimers();
    fireEvent.click(screen.getByTestId('wizard-ai-draft'));
    await act(() => vi.advanceTimersByTimeAsync(150_000));
    expect(screen.getByTestId('wizard-ai-error')).toHaveTextContent('等待超时');
    const oldStream = Stream.instances[0];
    expect(oldStream.closed).toBe(true);
    await act(async () => oldStream.emit('error', { error: { code: 'job_cancelled', message: '已取消。' } }));
    expect(screen.queryByTestId('wizard-progress')).not.toBeInTheDocument();
    expect(screen.getByTestId('wizard-retry-ai')).toBeEnabled();
    expect(fetchMock.mock.calls.filter(([, init]) => init?.method === 'DELETE')).toHaveLength(1);
    fireEvent.click(screen.getByTestId('wizard-retry-ai'));
    await act(() => vi.advanceTimersByTimeAsync(0));
    expect(Stream.instances).toHaveLength(2);
    await act(async () => oldStream.emit('done', { result: DRAFT }));
    expect(screen.queryByTestId('wizard-row-0')).not.toBeInTheDocument();
    await act(async () => Stream.instances[1].emit('done', { result: { ...DRAFT, backend: 'llm' } }));
    expect(screen.getByTestId('wizard-row-0')).toBeInTheDocument();
  });

  it('can switch to a rule draft during AI generation without late AI output replacing it', async () => {
    const Stream = controlledJobStream();
    const fetchMock = stubFetch((url) => url.endsWith('/jobs/job-test1')
      ? jsonResponse(200, { job: { job_id: 'job-test1', status: 'running', cancel_requested: true } }) : null);
    renderPage();
    await openDraftStep();
    fireEvent.click(screen.getByTestId('wizard-ai-draft'));
    await waitFor(() => expect(Stream.instances).toHaveLength(1));
    expect(screen.getByTestId('wizard-rule-draft')).toHaveTextContent('改用规则草稿');
    fireEvent.click(screen.getByTestId('wizard-rule-draft'));
    expect(await screen.findByTestId('wizard-row-0')).toBeInTheDocument();
    expect(Stream.instances[0].closed).toBe(true);
    await act(async () => Stream.instances[0].emit('done', { result: {
      ...DRAFT, patch: { evidence_entries: [{ title: 'Obsolete AI draft' }] },
    } }));
    expect(screen.queryByText('Obsolete AI draft')).not.toBeInTheDocument();
    expect(fetchMock.mock.calls.filter(([, init]) => init?.method === 'DELETE')).toHaveLength(1);
  });

  it.each(['success', 'failure'])('ignores a late AI creation %s after closing and reopening the wizard', async (outcome) => {
    const Stream = controlledJobStream();
    let resolveCreate!: (response: Response) => void;
    const pendingCreate = new Promise<Response>((resolve) => { resolveCreate = resolve; });
    const fetchMock = stubFetch((url, init) => {
      if (url.includes('/crystallize/draft') && JSON.parse(String(init?.body ?? '{}')).use_llm) return pendingCreate;
      if (url.endsWith('/jobs/late-job')) return jsonResponse(200, { job: { status: 'failed' } });
      return null;
    });
    renderPage();
    await openDraftStep();
    fireEvent.click(screen.getByTestId('wizard-ai-draft'));
    await waitFor(() => expect(fetchMock.mock.calls.some(([url]) => String(url).includes('/crystallize/draft'))).toBe(true));
    fireEvent.click(screen.getByRole('button', { name: '关闭结晶向导' }));
    await openDraftStep();
    await act(async () => resolveCreate(outcome === 'success'
      ? jsonResponse(202, { job_id: 'late-job', job: { job_id: 'late-job', status: 'queued' } })
      : jsonResponse(500, { message: 'Obsolete creation error' })));
    expect(Stream.instances).toHaveLength(0);
    expect(screen.queryByTestId('wizard-progress')).not.toBeInTheDocument();
    expect(screen.queryByText('Obsolete creation error')).not.toBeInTheDocument();
    expect(screen.getByTestId('wizard-ai-draft')).toBeEnabled();
    expect(fetchMock.mock.calls.filter(([url, init]) => String(url).endsWith('/jobs/late-job') && init?.method === 'DELETE'))
      .toHaveLength(outcome === 'success' ? 1 : 0);
  });

  it('stops waiting without letting cancellation progress restore the spinner', async () => {
    const Stream = controlledJobStream();
    stubFetch((url) => url.endsWith('/jobs/job-test1')
      ? jsonResponse(200, { job: { status: 'running', cancel_requested: true } }) : null);
    renderPage();
    await openDraftStep();
    fireEvent.click(screen.getByTestId('wizard-ai-draft'));
    await waitFor(() => expect(Stream.instances).toHaveLength(1));
    fireEvent.click(screen.getByTestId('wizard-stop-ai'));
    await act(async () => Stream.instances[0].emit('progress', { event: { phase: 'failed', message: '已取消。' } }));
    expect(screen.queryByTestId('wizard-progress')).not.toBeInTheDocument();
    expect(screen.getByText('已停止等待 AI 草稿。')).toBeInTheDocument();
    expect(screen.getByTestId('wizard-ai-draft')).toBeEnabled();
  });

  it('requests cancellation if stream recovery gives up before a batch finishes', async () => {
    const Stream = controlledJobStream();
    const fetchMock = stubFetch((url, init) => {
      if (url.includes('/crystallize/draft')) return jsonResponse(202, {
        job_id: 'job-test1', job: { job_id: 'job-test1', status: 'queued', timeout_seconds: 300 },
      });
      if (url.endsWith('/jobs/job-test1')) return init?.method === 'DELETE'
        ? jsonResponse(200, { job: { status: 'running', cancel_requested: true } })
        : jsonResponse(503, { message: 'Temporary network failure' });
      return null;
    });
    renderPage();
    await openDraftStep();
    vi.useFakeTimers();
    fireEvent.click(screen.getByTestId('wizard-ai-draft'));
    await act(() => vi.advanceTimersByTimeAsync(0));
    act(() => Stream.instances[0].emit('error', null));
    await act(() => vi.advanceTimersByTimeAsync(140_000));
    expect(screen.getByTestId('wizard-ai-error')).toHaveTextContent('连接中断');
    expect(screen.queryByTestId('wizard-progress')).not.toBeInTheDocument();
    expect(fetchMock.mock.calls.filter(([, init]) => init?.method === 'DELETE')).toHaveLength(1);
  });

  it('candidate cards open an inscription card with snapshot preview', async () => {
    stubFetch();
    renderPage('/p/alice/evidence?stage=crystallize');

    fireEvent.click(await screen.findByTestId('candidate-taskA'));
    const card = await screen.findByTestId('candidate-detail');
    expect(within(card).getByText('perf sprint')).toBeInTheDocument();
    expect(within(card).getByText('cut frame time')).toBeInTheDocument();
    expect(within(card).getByText('project:perf')).toBeInTheDocument();
    fireEvent.click(within(card).getByTestId('candidate-snapshot-toggle'));
    expect(within(card).getByTestId('candidate-snapshot')).toHaveTextContent(
      '# Tuned latency',
    );

    // 结晶此任务 opens the wizard with this task preselected.
    fireEvent.click(within(card).getByTestId('candidate-crystallize'));
    const pick = await screen.findByTestId('wizard-pick-taskA');
    expect((pick as HTMLInputElement).checked).toBe(true);
  });

  it('row hover shows a deprecate shortcut that fires without opening detail', async () => {
    const fetchMock = stubFetch();
    renderPage();

    const row = await screen.findByTestId('evidence-row-ev_2');
    fireEvent.mouseEnter(row);
    fireEvent.click(await screen.findByTestId('row-deprecate-ev_2'));
    await waitFor(() => {
      const posts = fetchMock.mock.calls.filter(
        (call) =>
          String(call[0]).includes('/evidence/ev_2/review') &&
          call[1]?.method === 'POST',
      );
      expect(posts).toHaveLength(1);
      expect(JSON.parse(String(posts[0][1]?.body))).toMatchObject({ action: 'reject' });
    });
    // The detail card did not open (shortcut, not selection).
    expect(screen.queryByTestId('evidence-detail')).not.toBeInTheDocument();
  });

  it('preselects the entry named by the focus query param (deep link)', async () => {
    stubFetch();
    renderPage('/p/alice/evidence?stage=review&focus=ev_2');

    // Same end state as clicking the row: the inscription detail opens.
    const detail = await screen.findByTestId('evidence-detail');
    expect(within(detail).getByText('MoveIt2 workshop notes')).toBeInTheDocument();
  });

  it('突破 toggle PATCHes the flag via the edit endpoint', async () => {
    const fetchMock = stubFetch();
    renderPage();

    fireEvent.click(await screen.findByTestId('evidence-row-ev_2'));
    const detail = await screen.findByTestId('evidence-detail');
    const toggle = within(detail).getByTestId('evidence-breakthrough-toggle');
    expect(toggle).toHaveAttribute('aria-pressed', 'false');
    fireEvent.click(toggle);

    await waitFor(() => {
      const calls = fetchMock.mock.calls.map((call) => ({
        url: String(call[0]),
        init: call[1],
      }));
      const edit = calls.find(
        (call) => call.url.includes('/evidence/ev_2/edit') && call.init?.method === 'POST',
      );
      expect(edit).toBeTruthy();
      expect(JSON.parse(String(edit!.init?.body))).toEqual({
        fields: { breakthrough: 'true' },
      });
    });
  });

  it('reviewed list rows show a small 突破 badge', async () => {
    stubFetch((url) => {
      if (url.includes('/evidence-review')) {
        return jsonResponse(200, {
          ...REVIEW_QUEUE,
          items: [{ ...REVIEW_QUEUE.items[0], breakthrough: true }],
        });
      }
      return null;
    });
    renderPage();

    const row = await screen.findByTestId('evidence-row-ev_2');
    expect(within(row).getByTestId('row-breakthrough-ev_2')).toHaveTextContent('突破');
  });

  it('review rows without the 突破 flag render no badge', async () => {
    // Default fixture carries breakthrough: false (the queue projection field).
    stubFetch();
    renderPage();

    const row = await screen.findByTestId('evidence-row-ev_2');
    expect(within(row).queryByTestId('row-breakthrough-ev_2')).not.toBeInTheDocument();
  });

  it('detail card shows only 分量; confidence/readiness live under 更多', async () => {
    stubFetch();
    renderPage();

    fireEvent.click(await screen.findByTestId('evidence-row-ev_2'));
    const detail = await screen.findByTestId('evidence-detail');
    // 主区只有「分量」一个评审维度。
    expect(within(detail).getByLabelText('分量')).toBeInTheDocument();
    // 置信度/公开就绪收进「更多」(默认折叠,不可见),可手改。
    const morePanel = within(detail).getByTestId('evidence-more');
    expect(morePanel).not.toBeVisible();
    expect(within(detail).getByLabelText('置信度')).not.toBeVisible();
    // 废弃按钮文案(原「拒绝」)。
    expect(within(detail).getByTestId('evidence-reject')).toHaveTextContent('废弃');
    fireEvent.click(within(detail).getByTestId('evidence-more-toggle'));
    await waitFor(() => expect(morePanel).toBeVisible());
    expect(within(morePanel).getByLabelText('置信度')).toBeVisible();
    expect(within(morePanel).getByLabelText('公开就绪')).toBeVisible();
  });

  it('wizard grading row is single-dimension (分量 only)', async () => {
    stubFetch();
    renderPage();

    fireEvent.click(await screen.findByTestId('open-crystallize-wizard'));
    fireEvent.click(await screen.findByTestId('wizard-pick-taskA'));
    fireEvent.click(screen.getByRole('button', { name: /下一步/ }));
    fireEvent.click(await screen.findByTestId('wizard-rule-draft'));

    const row = await screen.findByTestId('wizard-row-0');
    expect(within(row).getByLabelText('分量')).toBeInTheDocument();
    expect(within(row).queryByLabelText('置信度')).not.toBeInTheDocument();
  });

  it('consecutive skill-link mutations reuse the post-mutation ETag (no 412)', async () => {
    // Regression: before the fix the flat skill-tree query was never
    // invalidated/refreshed after a skill-links write, so the second click
    // re-sent the page-load ETag and the server answered 412. Now the
    // mutation response's fresh ETag is written back into the cache (and
    // the tree query is invalidated), so consecutive clicks just work.
    const posts: string[] = [];
    let treeEtag = 'W/"tree-v1"';
    stubFetch((url, init) => {
      const method = init?.method ?? 'GET';
      if (url.includes('/skill-links') && method === 'POST') {
        const headers = (init?.headers ?? {}) as Record<string, string>;
        const sent = headers['If-Match'] ?? '';
        posts.push(sent);
        // Server-side precondition: stale ETag would be a 412.
        if (sent !== treeEtag) {
          return jsonResponse(412, {
            code: 'etag_mismatch',
            message: '技能树已被其他改动更新,正在为你刷新;请重试。',
          });
        }
        // The write rotates the file fingerprint, like the real backend.
        treeEtag = 'W/"tree-v2"';
        return new Response(
          JSON.stringify({ ok: true, entry_id: 'ev_2', skill_ids: ['ros2_basics'], warnings: [] }),
          { status: 200, headers: { 'Content-Type': 'application/json', ETag: treeEtag } },
        );
      }
      if (url.includes('/skill-tree') && method === 'GET') {
        return new Response(JSON.stringify(SKILL_TREE), {
          status: 200,
          headers: { 'Content-Type': 'application/json', ETag: treeEtag },
        });
      }
      return null;
    });
    renderPage();

    fireEvent.click(await screen.findByTestId('evidence-row-ev_2'));
    fireEvent.click(await screen.findByRole('button', { name: '添加关联' }));
    const first = await screen.findByTestId('suggest-skill-ros2_basics');
    fireEvent.click(first);
    await waitFor(() => expect(posts).toHaveLength(1));
    expect(posts[0]).toBe('W/"tree-v1"');

    fireEvent.click(await screen.findByTestId('suggest-skill-ros2_basics'));
    await waitFor(() => expect(posts).toHaveLength(2));
    // Second mutation carried the fresh ETag — no 412 round-trip happened.
    expect(posts[1]).toBe('W/"tree-v2"');
  });

  it('a 412 (external writer) auto-refreshes the ETag and retries once', async () => {    const posts: string[] = [];
    let poolGets = 0;
    stubFetch((url, init) => {
      const method = init?.method ?? 'GET';
      if (url.includes('/evidence/ev_2/review') && method === 'POST') {
        const headers = (init?.headers ?? {}) as Record<string, string>;
        posts.push(headers['If-Match'] ?? '');
        if (posts.length === 1) {
          return jsonResponse(412, {
            code: 'etag_mismatch',
            message: '证据池已被其他改动更新,正在为你刷新;请重试。',
          });
        }
        return new Response(
          JSON.stringify({ ok: true, changed: 1, missing: [], warnings: [] }),
          { status: 200, headers: { 'Content-Type': 'application/json', ETag: 'W/"pool-v9"' } },
        );
      }
      if (url.includes('/evidence-review') && method === 'GET') {
        poolGets += 1;
        // The refresh fetch (status=all&limit=1) reports the fresh ETag.
        const etag = url.includes('limit=1') ? 'W/"pool-v8"' : 'W/"pool-v7"';
        return new Response(JSON.stringify(REVIEW_QUEUE), {
          status: 200,
          headers: { 'Content-Type': 'application/json', ETag: etag },
        });
      }
      return null;
    });
    renderPage();

    fireEvent.click(await screen.findByTestId('evidence-row-ev_2'));
    fireEvent.click(await screen.findByTestId('evidence-accept'));

    await waitFor(() => expect(posts).toHaveLength(2));
    expect(posts[0]).toBe('W/"pool-v7"');
    expect(posts[1]).toBe('W/"pool-v8"');
    expect(poolGets).toBeGreaterThanOrEqual(2);
  });
});

describe('EvidenceReviewRedirect', () => {
  it('redirects /evidence-review to /evidence?stage=review', async () => {
    stubFetch();
    renderPage('/p/alice/evidence-review');
    // The new page renders after the redirect (default review stage).
    expect(await screen.findByText('alice · 证据')).toBeInTheDocument();
    expect(await screen.findByTestId('evidence-row-ev_2')).toBeInTheDocument();
  });
});
