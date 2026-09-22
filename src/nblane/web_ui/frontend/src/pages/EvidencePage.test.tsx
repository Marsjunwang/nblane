import { fireEvent, screen, waitFor, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';

import { jsonResponse, renderWithProviders } from '../test/render';
import { EvidencePage, EvidenceReviewRedirect } from './EvidencePage';

const STAGES = {
  profile: 'alice',
  pending_crystallize_count: 2,
  needs_review_count: 1,
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
  intercept?: (url: string, init?: RequestInit) => Response | null,
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
  vi.unstubAllGlobals();
});

describe('EvidencePage', () => {
  it('renders the five stages with persistent counts', async () => {
    stubFetch();
    renderPage();

    expect(await screen.findByText('alice · 证据')).toBeInTheDocument();
    const nav = screen.getByTestId('stage-nav');
    await waitFor(() => {
      for (const [key, count] of [
        ['crystallize', '2'],
        ['review', '1'],
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
    // Live ref renders title; dead ref renders an 已归档 tombstone.
    expect(within(detail).getByText(/Tuned latency/)).toBeInTheDocument();
    expect(within(detail).getByTestId('tombstone-taskGone')).toHaveTextContent('已归档');
    // Rule-tier skill suggestion chip is offered.
    expect(
      await within(detail).findByTestId('suggest-skill-ros2_basics'),
    ).toBeInTheDocument();
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

  it('AI draft failure shows a friendly error and degrades to rule draft', async () => {
    // Fake EventSource that fails the job stream immediately (error frame
    // without data -> parseFrame yields null -> generic failure path).
    class FailingEventSource {
      static instance: FailingEventSource;
      listeners: Record<string, ((event: Event) => void)[]> = {};
      constructor(public url: string) {
        FailingEventSource.instance = this;
        setTimeout(() => this.emit('error', new Event('error')), 0);
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
    expect(screen.queryByTestId('wizard-progress')).not.toBeInTheDocument();

    fireEvent.click(within(alert).getByTestId('wizard-degrade-rule'));
    // Rule fallback lands on the grading step with the draft visible.
    expect(await screen.findByTestId('wizard-row-0')).toBeInTheDocument();
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
