import { fireEvent, screen, waitFor, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';

import { jsonResponse, renderWithProviders } from '../test/render';
import { PublicBuildPage } from './PublicBuildPage';

const LIVE = {
  output_dir: '/data/dist/public/alice',
  exists: true,
  built_at: '2026-10-01T12:00:00',
  page_count: 4,
  has_previous: true,
  previous_built_at: '2026-09-30T12:00:00',
  added: [{ path: 'blog/new/index.html', title: 'New post' }],
  changed: [{ path: 'index.html', title: 'Home' }],
  removed: [{ path: 'projects/index.html', title: 'projects/index.html' }],
  pdf_live: false,
  pdf_pending: false,
  in_sync: false,
};

const OVERVIEW = {
  profile: 'alice',
  initialized: true,
  visibility: 'public',
  settings: {
    show_photo: true,
    show_email: false,
    show_phone: false,
    resume_pdf: false,
    show_projects: false,
    base_url: '',
  },
  intro: {
    name: 'Alice',
    english_name: 'Al',
    title: 'Robotics engineer',
    summary: 'Builds **robots**.',
    photo: '',
    photo_url: '',
    phone: '',
    email: 'a@example.com',
    has_resume: true,
  },
  posts: [
    { slug: 'new', title: 'New post', date: '2026-10-01', status: 'published', summary: '', library_hidden: false, public: true, live: false },
    { slug: 'draft-one', title: 'Draft one', date: '2026-09-01', status: 'draft', summary: '', library_hidden: false, public: false, live: false },
  ],
  works: [
    {
      id: 'demo',
      title: 'Demo video',
      type: 'video',
      year: '2026',
      summary: 'Arm demo',
      video: 'https://www.bilibili.com/video/BV1xx411c7mD',
      video_mode: 'embed',
      cover: '',
      links: [{ label: '论文', url: 'https://arxiv.org/abs/1' }],
      status: 'published',
      featured: true,
    },
  ],
  works_etag: 'works-sha',
  projects_count: 3,
  errors: [],
  warnings: [],
  live: LIVE,
  pdf_available: true,
};

const PREVIEW = {
  ok: true,
  include_drafts: false,
  pages: [
    { path: 'index.html', title: 'Home' },
    { path: 'blog/index.html', title: 'Blog' },
  ],
  warnings: [],
};

interface MockOptions {
  overview?: unknown;
  responses?: Record<string, Response>;
}

function mockApi(options: MockOptions = {}) {
  const calls: { url: string; method: string; init?: RequestInit }[] = [];
  const overview = options.overview ?? OVERVIEW;
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const method = init?.method ?? 'GET';
    calls.push({ url, method, init });
    const key = `${method} ${url.replace(/^.*\/public-site/, '').replace(/\?.*$/, '')}`;
    if (options.responses?.[key]) return options.responses[key].clone();
    if (url.includes('/public-site/preview')) return jsonResponse(200, PREVIEW);
    if (url.endsWith('/public-site/deploy') || url.endsWith('/public-site/rollback')) {
      return jsonResponse(200, { ok: true, page_count: 4, warnings: [] });
    }
    if (url.includes('/public-site')) return jsonResponse(200, overview);
    if (url.endsWith('/studio/init')) return jsonResponse(200, { ok: true, created_paths: [] });
    return jsonResponse(404, { code: 'not_found', message: `no mock for ${method} ${url}` });
  });
  vi.stubGlobal('fetch', fetchMock);
  return { calls };
}

afterEach(() => {
  vi.unstubAllGlobals();
});

function renderPage() {
  return renderWithProviders(
    <Routes>
      <Route path="/p/:name/public-build" element={<PublicBuildPage />} />
    </Routes>,
    '/p/alice/public-build',
  );
}

describe('PublicBuildPage (公开站点)', () => {
  it('shows intro, switches, posts, works, live diff and the preview', async () => {
    mockApi();
    renderPage();

    await screen.findByTestId('public-site-page');
    expect(screen.getByTestId('intro-card')).toHaveTextContent('Robotics engineer');
    expect(screen.getByTestId('intro-card')).toHaveTextContent('Builds robots.');
    expect(screen.getByTestId('setting-visibility')).toBeChecked();
    expect(screen.getByTestId('setting-show_email')).not.toBeChecked();
    expect(screen.getByTestId('setting-show_projects')).not.toBeChecked();
    expect(screen.getByTestId('post-public-new')).toBeChecked();
    expect(screen.getByTestId('post-public-draft-one')).not.toBeChecked();
    expect(screen.getByTestId('work-0')).toHaveTextContent('Demo video');
    expect(screen.getByTestId('live-summary')).toHaveTextContent('新增 1 页，更新 1 页，下线 1 页');
    expect(screen.getByTestId('deploy-button')).toBeEnabled();
    const frame = await screen.findByTestId('preview-frame');
    expect(frame.getAttribute('src')).toContain('/api/v1/profiles/alice/public-site/preview/page');
    expect(frame.getAttribute('src')).toContain('include_drafts=0');
  });

  it('patches one display switch', async () => {
    const { calls } = mockApi();
    renderPage();
    fireEvent.click(await screen.findByTestId('setting-show_email'));
    await waitFor(() => {
      const call = calls.find((c) => c.method === 'PATCH');
      expect(call?.url).toContain('/public-site/settings');
      expect(JSON.parse(String(call?.init?.body))).toEqual({ show_email: true });
    });
  });

  it('toggles a post public and surfaces a publish-gate error inline', async () => {
    const { calls } = mockApi({
      responses: {
        'PUT /posts/draft-one': jsonResponse(422, {
          code: 'post_not_publishable',
          message: '这篇还不能公开：文章「draft-one」缺少必填字段「summary」',
        }),
      },
    });
    renderPage();
    fireEvent.click(await screen.findByTestId('post-public-draft-one'));
    expect(await screen.findByTestId('post-error-draft-one')).toHaveTextContent('缺少必填字段');
    const call = calls.find((c) => c.method === 'PUT');
    expect(JSON.parse(String(call?.init?.body))).toEqual({ public: true });
  });

  it('saves edited works with the works etag', async () => {
    const { calls } = mockApi();
    renderPage();
    fireEvent.click(await screen.findByTestId('work-0-toggle'));
    fireEvent.change(screen.getByTestId('work-0-title'), { target: { value: 'Arm demo' } });
    fireEvent.click(screen.getByTestId('work-0-add-link'));
    fireEvent.click(screen.getByTestId('works-save'));
    await waitFor(() => {
      const call = calls.find((c) => c.method === 'PUT' && c.url.endsWith('/public-site/works'));
      expect(call).toBeDefined();
      expect((call?.init?.headers as Record<string, string>)['If-Match']).toBe('works-sha');
      const body = JSON.parse(String(call?.init?.body));
      expect(body.works[0].title).toBe('Arm demo');
      // The empty link row is dropped before sending.
      expect(body.works[0].links).toEqual([{ label: '论文', url: 'https://arxiv.org/abs/1' }]);
    });
  });

  it('marks unsupported video hosts as link-only', async () => {
    mockApi();
    renderPage();
    fireEvent.click(await screen.findByTestId('work-0-toggle'));
    expect(screen.getByTestId('work-0-video-hint')).toHaveTextContent('直接内嵌播放');
    fireEvent.change(screen.getByTestId('work-0-video'), { target: { value: 'https://example.com/watch' } });
    expect(screen.getByTestId('work-0-video-hint')).toHaveTextContent('不支持内嵌播放');
  });

  it('deploys only after confirmation', async () => {
    const { calls } = mockApi();
    renderPage();
    fireEvent.click(await screen.findByTestId('deploy-button'));
    const dialog = await screen.findByTestId('live-confirm');
    expect(within(dialog).getByText('New post')).toBeInTheDocument();
    expect(calls.some((c) => c.url.endsWith('/deploy'))).toBe(false);
    fireEvent.click(screen.getByTestId('live-confirm-button'));
    await waitFor(() => expect(calls.some((c) => c.method === 'POST' && c.url.endsWith('/public-site/deploy'))).toBe(true));
  });

  it('blocks deploy while validation errors exist', async () => {
    mockApi({ overview: { ...OVERVIEW, visibility: 'private', errors: ['网站还没有设为公开（打开「网站公开」开关）'] } });
    renderPage();
    expect(await screen.findByTestId('site-errors')).toHaveTextContent('网站还没有设为公开');
    expect(screen.getByTestId('deploy-button')).toBeDisabled();
  });

  it('disables deploy when the live site is in sync', async () => {
    mockApi({
      overview: { ...OVERVIEW, live: { ...LIVE, added: [], changed: [], removed: [], in_sync: true } },
    });
    renderPage();
    expect(await screen.findByTestId('live-summary')).toHaveTextContent('线上已是最新');
    expect(screen.getByTestId('deploy-button')).toBeDisabled();
  });

  it('shows the init gate on an uninitialized profile', async () => {
    const { calls } = mockApi({ overview: { profile: 'alice', initialized: false } });
    renderPage();
    await screen.findByTestId('init-needed');
    fireEvent.click(screen.getByRole('button', { name: '初始化' }));
    await waitFor(() => expect(calls.some((c) => c.url.endsWith('/studio/init'))).toBe(true));
  });
});
