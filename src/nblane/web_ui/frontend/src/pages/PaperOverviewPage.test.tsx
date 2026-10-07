import { act, fireEvent, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes, useLocation } from 'react-router-dom';

import { jsonResponse, renderWithProviders } from '../test/render';
import { PaperOverviewPage } from './PaperOverviewPage';

const REF = (ref: string, page: number) => ({ ref, page });

const OVERVIEW = {
  profile: 'alice',
  source: {
    id: 'source:paper:demo',
    title: 'Attention Is All You Need',
    status: 'reading',
    authors: ['Ashish Vaswani', 'Noam Shazeer'],
    venue: 'NeurIPS',
    year: '2017',
    published: '2017',
    doi: '',
    arxiv_id: '1706.03762',
    url: '',
    pdf_url: '',
    tags: ['nlp'],
    captured_at: '',
  },
  abstract: { text: 'The dominant sequence transduction models...', translation: '主流的序列转导模型……', translation_status: 'translated', page: 1, origin: 'structure' },
  pdf: { available: true, page_count: 15, download_status: 'downloaded', download_error: '', extraction_status: 'ready', structure_backend: 'grobid', segment_count: 119, structure_unit_count: 559, extracted_at: '' },
  progress: { last_page: 5, page_count: 15, last_read_at: '2026-10-05T10:00:00+08:00', mode: 'pdf' },
  translation: { total: 173, translated: 6, missing: 136, stale: 31, failed: 0, status: 'stale' },
  notes: {
    annotation_count: 1,
    chunk_count: 0,
    recent: [{ id: 'ann:1', page: 3, quote: 'scaled dot-product attention', note: '和项目对照', color: 'yellow', locator: 'p. 3', updated: '' }],
  },
  quick_analysis: {
    updated: '2026-10-01T10:38:58+00:00',
    status: 'ready',
    fallback: false,
    tldr: 'Transformer replaces recurrence with attention.',
    key_points: [{ text: 'Attention only.', label: '', refs: [REF('seg:5', 2), REF('seg:6', 2), REF('seg:9', 4)] }],
    method: [{ text: 'Encoder-decoder stacks.', label: '', refs: [REF('seg:14', 3)] }],
    experiments: [],
    limitations: [{ text: 'No long-sequence study.', label: '', refs: [] }],
    usefulness: [],
    project_relevance: [],
    reading_plan: [],
    open_questions: [],
    scores: { novelty: 5, overall: 4 },
    scores_evaluated: true,
    score_rationale: [],
    warnings: [],
    coverage: { cited_segments: 31, pages: [2, 3, 4], page_count: 3, sections: [] },
  },
  deep_read: null,
  reader_available: true,
  reader_unavailable_reason: '',
  active_jobs: [],
};

class FakeEventSource {
  static instances: FakeEventSource[] = [];
  url: string;
  listeners: Record<string, ((event: MessageEvent) => void)[]> = {};
  closed = false;
  constructor(url: string) {
    this.url = url;
    FakeEventSource.instances.push(this);
  }
  addEventListener(type: string, listener: (event: MessageEvent) => void) {
    (this.listeners[type] ??= []).push(listener);
  }
  close() {
    this.closed = true;
  }
  emit(type: string, data: unknown) {
    for (const listener of this.listeners[type] ?? []) {
      listener(new MessageEvent(type, { data: JSON.stringify(data) }));
    }
  }
}

function LocationProbe() {
  const location = useLocation();
  return <div data-testid="location">{`${location.pathname}${location.search}`}</div>;
}

function renderOverview(route = '/p/alice/research/papers/source%3Apaper%3Ademo', overview: unknown = OVERVIEW) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith('/analysis-jobs') && init?.method === 'POST') {
      return jsonResponse(202, { ok: true, job_id: 'job-1', job: { job_id: 'job-1', profile: 'alice', kind: 'paper-quick-analysis', status: 'queued' } });
    }
    if (url.includes('/research/papers/')) return jsonResponse(200, overview);
    return jsonResponse(404, { code: 'not_found', message: 'nope' });
  });
  vi.stubGlobal('fetch', fetchMock);
  renderWithProviders(
    <Routes>
      <Route path="/p/:name/research/papers/:sourceId" element={<PaperOverviewPage />} />
      <Route path="/p/:name/research/papers/:sourceId/read" element={<LocationProbe />} />
    </Routes>,
    route,
  );
  return fetchMock;
}

beforeEach(() => {
  FakeEventSource.instances = [];
  vi.stubGlobal('EventSource', FakeEventSource);
});

afterEach(() => vi.unstubAllGlobals());

describe('PaperOverviewPage', () => {
  it('shows metadata, abstract translation, progress and recent notes', async () => {
    renderOverview();

    expect(await screen.findByRole('heading', { name: 'Attention Is All You Need' })).toBeInTheDocument();
    expect(screen.getByText(/Ashish Vaswani, Noam Shazeer · NeurIPS 2017/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /arXiv 1706.03762/ })).toHaveAttribute('href', 'https://arxiv.org/abs/1706.03762');
    // Translated abstract is shown first, original one click away.
    expect(within(screen.getByTestId('paper-abstract')).getByText('主流的序列转导模型……')).toBeInTheDocument();
    expect(screen.getByTestId('paper-reading-progress')).toHaveTextContent('读到第 5 / 15 页');
    expect(screen.getByTestId('paper-translation-progress')).toHaveTextContent('已翻译 6 / 173 段');
    expect(screen.getByTestId('paper-translation-progress')).toHaveTextContent('过期 31');
    expect(screen.getByTestId('paper-notes')).toHaveTextContent('scaled dot-product attention');
    expect(screen.getByTestId('paper-notes')).toHaveTextContent('和项目对照');
    // No claim / evidence affordances on the reading surface.
    expect(screen.queryByText(/Evidence|证据|Claim|断言/)).toBeNull();
  });

  it('links primary actions and ref chips into the reader', async () => {
    renderOverview();
    await screen.findByRole('heading', { name: 'Attention Is All You Need' });

    expect(screen.getByRole('link', { name: /继续阅读 · 第 5 页/ })).toHaveAttribute(
      'href',
      '/p/alice/research/papers/source%3Apaper%3Ademo/read',
    );
    expect(screen.getByRole('link', { name: /对照阅读/ })).toHaveAttribute(
      'href',
      '/p/alice/research/papers/source%3Apaper%3Ademo/read?mode=compare',
    );
    expect(screen.getByRole('link', { name: /继续阅读 · 第 5 页/ })).toHaveAttribute('target', 'nblane-reader-source_paper_demo');
    const card = screen.getByTestId('paper-quick-analysis');
    expect(within(card).getByText('Transformer replaces recurrence with attention.')).toBeInTheDocument();
    // seg:5 + seg:6 both resolve to page 2 → one deduplicated chip.
    const chips = within(card).getAllByRole('link', { name: /在阅读器中打开第 \d+ 页/ });
    expect(chips.map((chip) => chip.getAttribute('href'))).toEqual([
      '/p/alice/research/papers/source%3Apaper%3Ademo/read?page=2',
      '/p/alice/research/papers/source%3Apaper%3Ademo/read?page=4',
      '/p/alice/research/papers/source%3Apaper%3Ademo/read?page=3',
    ]);
    expect(new Set(chips.map((chip) => chip.getAttribute('target')))).toEqual(new Set(['nblane-reader-source_paper_demo']));
    expect(within(card).getByText(/引用 3 \/ 15 页/)).toBeInTheDocument();
    expect(within(screen.getByTestId('paper-scores')).getByText('新颖性')).toBeInTheDocument();
    // Empty sections say so instead of disappearing.
    expect(within(card).getByText('项目相关性')).toBeInTheDocument();
  });

  it('shows not-started states for missing analysis and deep read', async () => {
    renderOverview(undefined, { ...OVERVIEW, quick_analysis: null, deep_read: null, progress: { ...OVERVIEW.progress, last_page: 0 } });
    await screen.findByRole('heading', { name: 'Attention Is All You Need' });
    expect(within(screen.getByTestId('paper-quick-analysis')).getByText(/尚未生成/)).toBeInTheDocument();
    expect(within(screen.getByTestId('paper-deep-read')).getByText(/尚未生成/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: '开始阅读' })).toBeInTheDocument();
  });

  it('runs quick analysis as a job and surfaces a retryable failure', async () => {
    const fetchMock = renderOverview(undefined, { ...OVERVIEW, quick_analysis: null });
    await screen.findByRole('heading', { name: 'Attention Is All You Need' });

    fireEvent.click(within(screen.getByTestId('paper-quick-analysis')).getByRole('button', { name: /快速分析/ }));
    await vi.waitFor(() => expect(FakeEventSource.instances).toHaveLength(1));
    const post = fetchMock.mock.calls.find(([url, init]) => String(url).endsWith('/analysis-jobs') && init?.method === 'POST');
    expect(JSON.parse(String(post?.[1]?.body))).toEqual({ kind: 'paper-quick-analysis' });
    expect(FakeEventSource.instances[0].url).toContain('/profiles/alice/jobs/job-1/stream');

    act(() => FakeEventSource.instances[0].emit('progress', { ok: true, event: { message: '模型正在生成 TL;DR、要点与评分…' } }));
    expect(await screen.findByTestId('paper-job-running')).toHaveTextContent('模型正在生成 TL;DR');

    act(() => FakeEventSource.instances[0].emit('error', { ok: false, error: { code: 'ai_not_configured', message: '快速分析需要 LLM 连接。' } }));
    const error = await screen.findByTestId('paper-job-error');
    expect(error).toHaveTextContent('快速分析需要 LLM 连接。');
    expect(within(error).getByRole('button', { name: '重试' })).toBeInTheDocument();
  });

  it('refetches the overview when the job finishes', async () => {
    const fetchMock = renderOverview();
    await screen.findByRole('heading', { name: 'Attention Is All You Need' });
    const overviewCalls = () => fetchMock.mock.calls.filter(([url, init]) => String(url).includes('/research/papers/') && !init?.method).length;
    const before = overviewCalls();

    fireEvent.click(within(screen.getByTestId('paper-deep-read')).getByRole('button', { name: /深度研读/ }));
    await vi.waitFor(() => expect(FakeEventSource.instances).toHaveLength(1));
    act(() => FakeEventSource.instances[0].emit('done', { ok: true, result: { source_id: 'source:paper:demo' } }));

    await vi.waitFor(() => expect(overviewCalls()).toBeGreaterThan(before));
  });

  it('re-attaches to an analysis job that is already running', async () => {
    renderOverview(undefined, {
      ...OVERVIEW,
      active_jobs: [{ job_id: 'job-9', kind: 'paper-deep-read', status: 'running', phase: 'reading', message: '' }],
    });
    await screen.findByRole('heading', { name: 'Attention Is All You Need' });
    await vi.waitFor(() => expect(FakeEventSource.instances.map((item) => item.url).join()).toContain('/jobs/job-9/stream'));
  });

  it('redirects legacy ?mode= deep links to the reader route', async () => {
    renderOverview('/p/alice/research/papers/source%3Apaper%3Ademo?mode=translation&page=3');
    expect(await screen.findByTestId('location')).toHaveTextContent(
      '/p/alice/research/papers/source%3Apaper%3Ademo/read?mode=translation&page=3',
    );
  });

  it('shows a retryable error when the overview fails to load', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse(404, { code: 'paper_not_found', message: 'Unknown paper: x' })));
    renderWithProviders(
      <Routes><Route path="/p/:name/research/papers/:sourceId" element={<PaperOverviewPage />} /></Routes>,
      '/p/alice/research/papers/x',
    );
    expect(await screen.findByText('Unknown paper: x')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '重试' })).toBeInTheDocument();
  });
});
