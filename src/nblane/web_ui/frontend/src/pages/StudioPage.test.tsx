import { fireEvent, screen, waitFor, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';

import { jsonResponse, renderWithProviders } from '../test/render';
import { StudioPage } from './StudioPage';

const STUDIO_ETAG = 'W/"studio-sha"';
const POST_ETAG = 'W/"post-sha"';

const STUDIO = {
  profile: 'alice',
  initialized: true,
  summary: { status_counts: { draft: 1, published: 1 }, total_posts: 2 },
  posts: [
    {
      slug: 'hello',
      title: 'First post',
      date: '2026-09-10',
      status: 'draft',
      summary: '',
      cover: '',
      tags: ['robotics'],
      category_path: [],
    },
    {
      slug: 'ready',
      title: 'Ready post',
      date: '2026-09-11',
      status: 'published',
      summary: 'A publishable summary.',
      cover: '',
      tags: [],
      category_path: [],
    },
  ],
  options: {
    claims: [{ id: 'claim-1', label: 'claim-1 - Reproduced the piper stack' }],
    evidence: [{ id: 'ev-1', label: 'ev-1 - Arm demo video' }],
    projects: [{ id: 'proj-1', label: 'proj-1 - Robot Arm' }],
  },
};

const POST_DETAIL = {
  slug: 'hello',
  title: 'First post',
  date: '2026-09-10',
  status: 'draft',
  summary: '',
  cover: '',
  tags: ['robotics'],
  category_path: [],
  meta: { title: 'First post', date: '2026-09-10', status: 'draft' },
  body: 'Hello **world**.\n',
  has_math: false,
  related_evidence: [],
  related_kanban: [],
  related_claims: ['claim-1'],
  related_sources: [],
  related_research_claims: [],
  related_citations: [],
};

function withEtag(response: Response, etag: string): Response {
  return new Response(response.body, {
    status: response.status,
    headers: { 'Content-Type': 'application/json', ETag: etag },
  });
}

interface MockOptions {
  saveResponse?: Response;
  publishResponse?: Response;
  checkResponse?: Response;
  previewResponse?: Response;
  draftResponse?: Response;
  jdResponse?: Response;
}

function mockApi(options: MockOptions = {}) {
  const calls: { url: string; init?: RequestInit }[] = [];
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    calls.push({ url, init });
    const method = init?.method ?? 'GET';
    if (url.endsWith('/profiles/alice/studio') && method === 'GET') {
      return withEtag(jsonResponse(200, STUDIO), STUDIO_ETAG);
    }
    if (url.endsWith('/studio/blog/hello') && method === 'GET') {
      return withEtag(jsonResponse(200, POST_DETAIL), POST_ETAG);
    }
    if (url.endsWith('/studio/blog/hello/save')) {
      return options.saveResponse ?? jsonResponse(200, { ok: true, post: POST_DETAIL });
    }
    if (url.endsWith('/studio/blog/hello/check')) {
      return (
        options.checkResponse ??
        jsonResponse(200, { ok: false, errors: ["blog/hello.md: missing required field 'summary'"], warnings: [] })
      );
    }
    if (url.endsWith('/studio/blog/hello/publish')) {
      return (
        options.publishResponse ??
        jsonResponse(422, {
          code: 'blog_publish_blocked',
          message: "blog/hello.md: missing required field 'summary'",
        })
      );
    }
    if (url.endsWith('/studio/candidates/preview')) {
      return (
        options.previewResponse ??
        jsonResponse(200, {
          ok: true,
          kind: 'blog',
          candidate: {
            title: 'Reproduced the piper stack',
            summary: '',
            body: '## What happened\n\nFallback body.\n',
            related_claims: ['claim-1'],
            warnings: [],
          },
        })
      );
    }
    if (url.endsWith('/studio/candidates/create')) {
      return (
        options.draftResponse ??
        jsonResponse(201, {
          ok: true,
          kind: 'blog',
          path: 'profiles/alice/blog/2026-09-20-claim.md',
          slug: '2026-09-20-claim',
          warnings: [],
        })
      );
    }
    if (url.endsWith('/studio/jd-match')) {
      return (
        options.jdResponse ??
        jsonResponse(422, {
          code: 'studio_jd_match_unavailable',
          message: 'JD match analysis requires a configured LLM backend',
        })
      );
    }
    return jsonResponse(404, { code: 'not_found', message: `no mock for ${method} ${url}` });
  });
  vi.stubGlobal('fetch', fetchMock);
  return { fetchMock, calls };
}

afterEach(() => {
  vi.unstubAllGlobals();
});

function renderPage() {
  return renderWithProviders(
    <Routes>
      <Route path="/p/:name/studio" element={<StudioPage />} />
    </Routes>,
    '/p/alice/studio',
  );
}

async function openEditor() {
  const row = await screen.findByTestId('post-row-hello');
  fireEvent.click(within(row).getByRole('button', { name: '编辑' }));
  return screen.findByTestId('post-editor');
}

describe('StudioPage', () => {
  it('renders the status counters and post list', async () => {
    mockApi();
    renderPage();

    const summary = await screen.findByTestId('studio-summary');
    expect(summary).toHaveTextContent('草稿 1');
    expect(summary).toHaveTextContent('已发布 1');
    const row = await screen.findByTestId('post-row-hello');
    expect(row).toHaveTextContent('First post');
    expect(row).toHaveTextContent('草稿');
  });

  it('opens the editor and saves with the post ETag', async () => {
    const { calls } = mockApi();
    renderPage();
    await openEditor();

    const titleInput = await screen.findByDisplayValue('First post');
    fireEvent.change(titleInput, { target: { value: 'Renamed post' } });
    const body = screen.getByTestId('post-body');
    expect(body).toHaveValue('Hello **world**.\n');

    fireEvent.click(screen.getByRole('button', { name: '保存' }));
    await waitFor(() => {
      const saveCall = calls.find((call) => call.url.endsWith('/studio/blog/hello/save'));
      expect(saveCall).toBeDefined();
      const headers = saveCall?.init?.headers as Record<string, string>;
      expect(headers['If-Match']).toBe(POST_ETAG);
      const payload = JSON.parse(String(saveCall?.init?.body));
      expect(payload.title).toBe('Renamed post');
      expect(payload.related_claims).toEqual(['claim-1']);
    });
  });

  it('runs the publish check and shows the findings', async () => {
    mockApi();
    renderPage();
    await openEditor();

    fireEvent.click(screen.getByRole('button', { name: '发布检查' }));
    const result = await screen.findByTestId('check-result');
    expect(result).toHaveTextContent('发布前检查未通过');
    expect(result).toHaveTextContent("missing required field 'summary'");
  });

  it('shows the publish-blocked error on validation failure', async () => {
    mockApi();
    renderPage();
    await openEditor();

    fireEvent.click(screen.getByTestId('publish-button'));
    const error = await screen.findByTestId('mutation-error');
    expect(error).toHaveTextContent("missing required field 'summary'");
  });

  it('flags stale writes as conflicts with a refresh button that refetches', async () => {
    const { calls } = mockApi({
      saveResponse: jsonResponse(412, {
        code: 'etag_mismatch',
        message: 'This blog post changed since it was loaded; reload before saving.',
      }),
    });
    renderPage();
    await openEditor();

    fireEvent.click(screen.getByRole('button', { name: '保存' }));
    const conflict = await screen.findByTestId('conflict-alert');
    expect(conflict).toHaveTextContent('数据已被他人修改');
    expect(conflict).toHaveTextContent('请刷新后重试');

    const overviewGets = () =>
      calls.filter(
        (call) =>
          call.url.endsWith('/profiles/alice/studio') && (call.init?.method ?? 'GET') === 'GET',
      ).length;
    const before = overviewGets();
    fireEvent.click(screen.getByRole('button', { name: '刷新' }));
    await waitFor(() => expect(overviewGets()).toBeGreaterThan(before));
  });

  it('generates a candidate preview and confirms the draft', async () => {
    const { calls } = mockApi();
    renderPage();

    fireEvent.click(await screen.findByRole('tab', { name: '从证据生成' }));
    const createButton = await screen.findByTestId('create-draft-button');
    expect(createButton).toBeDisabled();

    fireEvent.click(screen.getByRole('button', { name: '生成预览' }));
    const preview = await screen.findByTestId('candidate-preview');
    expect(preview).toHaveTextContent('Reproduced the piper stack');
    expect(preview).toHaveTextContent('Fallback body.');
    expect(createButton).toBeEnabled();

    fireEvent.click(createButton);
    await waitFor(() => {
      const createCall = calls.find((call) => call.url.endsWith('/candidates/create'));
      expect(createCall).toBeDefined();
      const headers = createCall?.init?.headers as Record<string, string>;
      expect(headers['If-Match']).toBe(STUDIO_ETAG);
    });
    const created = await screen.findByTestId('draft-created');
    expect(created).toHaveTextContent('2026-09-20-claim');
  });

  it('shows the LLM degradation card when JD match is unavailable', async () => {
    mockApi();
    renderPage();

    fireEvent.click(await screen.findByRole('tab', { name: 'JD 匹配' }));
    const resumeInput = await screen.findByLabelText('简历内容');
    const jdInput = screen.getByLabelText(/目标 JD/);
    fireEvent.change(resumeInput, { target: { value: '# Resume' } });
    fireEvent.change(jdInput, { target: { value: 'Robotics engineer' } });
    fireEvent.click(screen.getByRole('button', { name: '分析 JD 匹配' }));

    const degraded = await screen.findByTestId('jd-degraded');
    expect(degraded).toHaveTextContent('AI 分析不可用');
    expect(degraded).toHaveTextContent('其余功能不受影响');
  });

  it('keeps an unsaved editor draft when a studio mutation refetches the post', async () => {
    let postReads = 0;
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const method = init?.method ?? 'GET';
      if (url.endsWith('/profiles/alice/studio') && method === 'GET') {
        return withEtag(jsonResponse(200, STUDIO), STUDIO_ETAG);
      }
      if (url.endsWith('/studio/blog/hello') && method === 'GET') {
        postReads += 1;
        // The refetch after the create carries a fresh ETag — the old key
        // scheme would remount PostEditorForm here and wipe the draft.
        if (postReads === 1) {
          return withEtag(jsonResponse(200, POST_DETAIL), POST_ETAG);
        }
        return withEtag(
          jsonResponse(200, { ...POST_DETAIL, body: 'Server rewrite.\n' }),
          'W/"post-sha-2"',
        );
      }
      if (url.endsWith('/studio/blog') && method === 'POST') {
        // Create returns the same slug so the editor stays on 'hello'.
        return jsonResponse(201, { ok: true, post: { ...POST_DETAIL, meta: undefined } });
      }
      return jsonResponse(404, { code: 'not_found', message: `no mock for ${method} ${url}` });
    });
    vi.stubGlobal('fetch', fetchMock);

    renderPage();
    await openEditor();
    fireEvent.change(await screen.findByDisplayValue('First post'), {
      target: { value: 'Renamed post' },
    });

    // Trigger a studio-wide invalidation without saving the draft.
    const form = screen.getByTestId('create-post-form');
    fireEvent.change(within(form).getByLabelText('新建博客草稿'), {
      target: { value: 'Another post' },
    });
    fireEvent.click(within(form).getByRole('button', { name: '创建' }));
    await waitFor(() => expect(postReads).toBeGreaterThanOrEqual(2));

    expect(screen.getByDisplayValue('Renamed post')).toBeInTheDocument();
    expect(screen.getByTestId('post-body')).toHaveValue('Hello **world**.\n');
  });
});
