import { act, fireEvent, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';

import { jsonResponse, renderWithProviders } from '../test/render';
import { ResearchSourcesPage } from './ResearchSourcesPage';

const SOURCE_A = {
  id: 'src:001',
  title: 'SLAM survey',
  kind: 'paper',
  status: 'reading',
  url: 'https://example.org/slam',
  captured_at: '2026-09-18',
  authors: [],
  published: '',
  tags: ['robotics'],
  summary: 'A survey.',
  notes: '',
  visibility: 'private',
  origin: 'manual',
  library_node_refs: [],
  provider: '',
  pdf_available: false,
  etag: 'W/"src-a"',
};

const SOURCES = {
  profile: 'alice',
  total: 1,
  status_counts: { reading: 1 },
  kind_counts: { paper: 1 },
  sources: [SOURCE_A],
  options: {
    kinds: ['web', 'paper'],
    statuses: ['inbox', 'reading', 'summarized', 'candidate_ready', 'archived', 'discarded'],
    visibilities: ['private', 'public'],
  },
};

const CONNECTORS = {
  profile: 'alice',
  providers: ['arxiv', 'semantic_scholar', 'github', 'x_twitter', 'xiaohongshu'],
  auto_providers: ['arxiv', 'github', 'semantic_scholar'],
  connectors: [
    {
      id: 'arxiv:vla',
      provider: 'arxiv',
      enabled: true,
      query: 'vla',
      privacy_default: 'private',
      status: 'idle',
      last_run: '',
      options: {},
      rate_limit: {},
      last_result: {},
    },
  ],
  library_nodes: [],
};

const AI_CONFIG = {
  profile: 'alice',
  actions: [
    { action: 'research.paper_translate', default_backend: 'llm', backend: '', llm_model: '', codex_model: '' },
    { action: 'research.paper_qa', default_backend: 'codex', backend: '', llm_model: '', codex_model: '' },
  ],
  llm_default_model: 'qwen-plus',
  codex_default_model: '',
  codex_model_suggestions: ['gpt-5.5'],
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
    this.listeners.set(type, [...(this.listeners.get(type) ?? []), listener]);
  }

  removeEventListener() {}

  close() {
    this.closed = true;
  }

  emit(type: string, data: unknown) {
    const event = new MessageEvent(type, { data: JSON.stringify(data) });
    for (const listener of this.listeners.get(type) ?? []) listener(event);
  }
}

type Call = { url: string; method: string; body: unknown; headers: Record<string, string> };

function mockApi(overrides: { sourcesStatus?: number; createStatus?: number } = {}) {
  const calls: Call[] = [];
  let sourcesFailures = overrides.sourcesStatus ? 1 : 0;
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const method = init?.method ?? 'GET';
      const body = init?.body ? JSON.parse(String(init.body)) : undefined;
      calls.push({ url, method, body, headers: (init?.headers ?? {}) as Record<string, string> });
      if (url.includes('/research/sources') && method === 'GET') {
        if (sourcesFailures > 0) {
          sourcesFailures -= 1;
          return jsonResponse(overrides.sourcesStatus ?? 500, { code: 'boom', message: '服务暂时不可用' });
        }
        return jsonResponse(200, SOURCES);
      }
      if (url.endsWith('/research/sources') && method === 'POST') {
        if (overrides.createStatus === 409) {
          return jsonResponse(409, { code: 'duplicate_research_source', message: 'dup', duplicate_source_id: 'src:001' });
        }
        return jsonResponse(201, { ok: true, source: { ...SOURCE_A, id: 'src:new', title: body.title } });
      }
      if (url.includes('/research/sources/') && method === 'PATCH') {
        return jsonResponse(200, { ok: true, source: { ...SOURCE_A, ...body } });
      }
      if (url.endsWith('/research/connectors') && method === 'GET') return jsonResponse(200, CONNECTORS);
      if (url.endsWith('/connectors/arxiv%3Avla/preview') && method === 'POST') {
        return jsonResponse(202, {
          ok: true,
          job_id: 'job-1',
          job: { job_id: 'job-1', profile: 'alice', kind: 'research-connector-preview', status: 'queued', phase: 'queued', message: '' },
        });
      }
      if (url.endsWith('/research/ai-config') && method === 'GET') return jsonResponse(200, AI_CONFIG);
      if (url.endsWith('/research/ai-config') && method === 'PUT') return jsonResponse(200, AI_CONFIG);
      return jsonResponse(404, { code: 'not_found', message: `unmocked ${method} ${url}` });
    }),
  );
  return calls;
}

function renderPage(route = '/p/alice/research/sources') {
  return renderWithProviders(
    <Routes>
      <Route path="/p/:name/research/sources" element={<ResearchSourcesPage />} />
    </Routes>,
    route,
  );
}

beforeEach(() => {
  MockEventSource.instances = [];
  vi.stubGlobal('EventSource', MockEventSource);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('ResearchSourcesPage', () => {
  it('lists inbox sources with status and tags, without claim/evidence affordances', async () => {
    mockApi();
    renderPage();

    expect(await screen.findByText('alice · 研究来源')).toBeInTheDocument();
    expect(await screen.findByText('SLAM survey')).toBeInTheDocument();
    expect(screen.getByText('robotics')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '修改状态：SLAM survey' })).toHaveTextContent('阅读中');
    expect(screen.queryByText(/证据候选|晋升为证据|claim/i)).toBeNull();
  });

  it('changes a source status with If-Match', async () => {
    const calls = mockApi();
    renderPage();

    fireEvent.click(await screen.findByRole('button', { name: '修改状态：SLAM survey' }));
    fireEvent.click(await screen.findByRole('menuitem', { name: '已总结' }));

    await waitFor(() => expect(calls.some((call) => call.method === 'PATCH')).toBe(true));
    const patch = calls.find((call) => call.method === 'PATCH')!;
    expect(patch.url).toContain('/research/sources/src%3A001');
    expect(patch.body).toEqual({ status: 'summarized' });
    expect(patch.headers['If-Match']).toBe('W/"src-a"');
    expect(await screen.findByText('已保存')).toBeInTheDocument();
  });

  it('offers retry when the inbox fails to load', async () => {
    const calls = mockApi({ sourcesStatus: 500 });
    renderPage();

    expect(await screen.findByText('来源加载失败')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '重试' }));
    expect(await screen.findByText('SLAM survey')).toBeInTheDocument();
    expect(calls.filter((call) => call.url.includes('/research/sources') && call.method === 'GET').length).toBeGreaterThanOrEqual(2);
  });

  it('adds a source manually and reports duplicates', async () => {
    const calls = mockApi();
    renderPage('/p/alice/research/sources?tab=add');

    fireEvent.change(await screen.findByLabelText(/标题/), { target: { value: 'Diffusion Policy' } });
    fireEvent.change(screen.getByLabelText('链接'), { target: { value: 'https://arxiv.org/abs/2303.04137' } });
    fireEvent.change(screen.getAllByLabelText(/标签/)[0], { target: { value: 'policy, diffusion' } });
    fireEvent.click(screen.getByRole('button', { name: '收录来源' }));

    await waitFor(() => expect(calls.some((call) => call.method === 'POST' && call.url.endsWith('/research/sources'))).toBe(true));
    const create = calls.find((call) => call.method === 'POST')!;
    expect(create.body).toMatchObject({ title: 'Diffusion Policy', url: 'https://arxiv.org/abs/2303.04137', tags: ['policy', 'diffusion'], kind: 'web', status: 'inbox' });
    expect(await screen.findByText('已收录')).toBeInTheDocument();
  });

  it('shows a duplicate notice when the URL already exists', async () => {
    mockApi({ createStatus: 409 });
    renderPage('/p/alice/research/sources?tab=add');

    fireEvent.change(await screen.findByLabelText(/标题/), { target: { value: 'Again' } });
    fireEvent.click(screen.getByRole('button', { name: '收录来源' }));
    expect(await screen.findByText('来源已存在')).toBeInTheDocument();
  });

  it('previews connector candidates through the job stream and surfaces failures with retry', async () => {
    mockApi();
    renderPage('/p/alice/research/sources?tab=connectors');

    fireEvent.click(await screen.findByRole('button', { name: /预览候选/ }));
    await waitFor(() => expect(MockEventSource.instances.length).toBe(1));
    expect(MockEventSource.instances[0].url).toContain('/profiles/alice/jobs/job-1/stream');
    expect(await screen.findByText('正在预览候选')).toBeInTheDocument();

    act(() => {
      MockEventSource.instances[0].emit('error', {
        ok: false,
        error: { code: 'connector_unreachable', message: '连接器请求失败（网络不可用或服务无响应）' },
      });
    });
    expect(await screen.findByText('连接器任务失败')).toBeInTheDocument();
    expect(screen.getByText(/网络不可用/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '重试' })).toBeInTheDocument();
  });

  it('renders preview candidates from a finished job', async () => {
    mockApi();
    renderPage('/p/alice/research/sources?tab=connectors');

    fireEvent.click(await screen.findByRole('button', { name: /预览候选/ }));
    await waitFor(() => expect(MockEventSource.instances.length).toBe(1));
    act(() => {
      MockEventSource.instances[0].emit('done', {
        ok: true,
        result: {
          connector_id: 'arxiv:vla',
          provider: 'arxiv',
          discovered: 2,
          importable: 1,
          skipped: 1,
          warnings: [],
          candidates: [
            { fingerprint: 'fp-new', canonical_url: '', selected: true, duplicate: { is_duplicate: false }, item: { title: 'New VLA paper', kind: 'paper' } },
            { fingerprint: 'fp-dup', canonical_url: '', selected: false, duplicate: { is_duplicate: true, existing_source_id: 'src:001' }, item: { title: 'SLAM survey dup', kind: 'paper' } },
          ],
        },
      });
    });
    expect(await screen.findByText('New VLA paper')).toBeInTheDocument();
    expect(screen.getByText('已在收件箱：src:001')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /导入选中 1/ })).toBeEnabled();
  });

  it('points the old research AI tab at Settings', async () => {
    mockApi();
    renderPage('/p/alice/research/sources?tab=ai');
    const link = await screen.findByRole('link', { name: /打开研究与阅读设置/ });
    expect(link).toHaveAttribute('href', '/settings/research?profile=alice');
  });
});
