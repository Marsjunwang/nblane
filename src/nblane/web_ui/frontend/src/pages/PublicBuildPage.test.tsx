import { fireEvent, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';

import { jsonResponse, renderWithProviders } from '../test/render';
import { PublicBuildPage } from './PublicBuildPage';

const PB_ETAG = 'W/"public-build-sha"';

const OVERVIEW = {
  profile: 'alice',
  initialized: true,
  validation: { ok: true, errors: [], warnings: [] },
  drafts: [{ slug: 'ready', title: 'Ready post', date: '2026-09-11' }],
  build: {
    output_dir: '/data/dist/public/alice',
    exists: false,
    built_at: '',
    total_files: 0,
    total_bytes: 0,
    artifacts_truncated: false,
    artifacts: [],
  },
};

const OVERVIEW_BUILT = {
  ...OVERVIEW,
  build: {
    output_dir: '/data/dist/public/alice',
    exists: true,
    built_at: '2026-09-21T12:00:00',
    total_files: 2,
    total_bytes: 4096,
    artifacts_truncated: false,
    artifacts: [
      { path: 'index.html', size: 3072, modified: '2026-09-21T12:00:00' },
      { path: 'assets/site.css', size: 1024, modified: '2026-09-21T12:00:00' },
    ],
  },
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

const BUILD_OK = {
  ok: true,
  output_dir: '/data/dist/public/alice',
  page_count: 5,
  pages: ['index.html'],
  published: [],
};

function withEtag(response: Response, etag: string): Response {
  return new Response(response.body, {
    status: response.status,
    headers: { 'Content-Type': 'application/json', ETag: etag },
  });
}

interface MockOptions {
  overview?: unknown;
  buildResponse?: Response;
  publishResponse?: Response;
}

function mockApi(options: MockOptions = {}) {
  const calls: { url: string; init?: RequestInit }[] = [];
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    calls.push({ url, init });
    const method = init?.method ?? 'GET';
    if (url.endsWith('/profiles/alice/public-build') && method === 'GET') {
      return withEtag(jsonResponse(200, options.overview ?? OVERVIEW), PB_ETAG);
    }
    if (url.includes('/public-build/preview?')) {
      return jsonResponse(200, PREVIEW);
    }
    if (url.endsWith('/public-build/build')) {
      return options.buildResponse ?? withEtag(jsonResponse(200, BUILD_OK), PB_ETAG);
    }
    if (url.endsWith('/public-build/publish-and-build')) {
      return (
        options.publishResponse ??
        withEtag(jsonResponse(200, { ...BUILD_OK, published: ['ready'] }), PB_ETAG)
      );
    }
    if (url.endsWith('/studio/init')) {
      return jsonResponse(200, { ok: true, created_paths: ['public-profile.yaml'] });
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
      <Route path="/p/:name/public-build" element={<PublicBuildPage />} />
    </Routes>,
    '/p/alice/public-build',
  );
}

describe('PublicBuildPage', () => {
  it('renders the status overview, drafts, and empty artifacts', async () => {
    mockApi();
    renderPage();

    const status = await screen.findByTestId('build-status');
    expect(status).toHaveTextContent('校验通过');
    expect(status).toHaveTextContent('尚未构建');
    expect(status).toHaveTextContent('/data/dist/public/alice');
    expect(screen.getByTestId('no-artifacts')).toBeVisible();
    expect(screen.getByTestId('draft-list')).toHaveTextContent('Ready post');
    // Publish is gated on a selection; the preview iframe points at the API.
    expect(screen.getByTestId('publish-build-button')).toBeDisabled();
    const frame = await screen.findByTestId('preview-frame');
    expect(frame.getAttribute('src')).toContain('/api/v1/profiles/alice/public-build/preview/page');
    expect(frame.getAttribute('src')).toContain('path=index.html');
  });

  it('shows the init gate on an uninitialized profile and calls studio init', async () => {
    const { calls } = mockApi({
      overview: { ...OVERVIEW, initialized: false, validation: null, drafts: [] },
    });
    renderPage();

    await screen.findByTestId('init-needed');
    fireEvent.click(screen.getByRole('button', { name: '初始化公开层' }));
    await waitFor(() => {
      const initCall = calls.find((call) => call.url.endsWith('/studio/init'));
      expect(initCall).toBeDefined();
      const headers = initCall?.init?.headers as Record<string, string>;
      expect(headers['If-Match']).toBe(PB_ETAG);
    });
  });

  it('builds with the overview ETag and shows the success feedback', async () => {
    const { calls } = mockApi();
    renderPage();
    await screen.findByTestId('build-status');

    fireEvent.click(screen.getByTestId('build-button'));
    await screen.findByTestId('build-success');

    const buildCall = calls.find((call) => call.url.endsWith('/public-build/build'));
    expect(buildCall).toBeDefined();
    const headers = buildCall?.init?.headers as Record<string, string>;
    expect(headers['If-Match']).toBe(PB_ETAG);
    expect(JSON.parse(String(buildCall?.init?.body))).toEqual({
      include_drafts: false,
      base_url: '',
    });
    expect(screen.getByTestId('build-success')).toHaveTextContent('已构建');
    expect(screen.getByTestId('build-success')).toHaveTextContent('5 页');
  });

  it('sends include_drafts after toggling the preview-mode switch', async () => {
    const { calls } = mockApi();
    renderPage();
    await screen.findByTestId('build-status');

    fireEvent.click(screen.getByRole('switch', { name: /包含草稿/ }));
    fireEvent.click(screen.getByTestId('build-button'));
    await screen.findByTestId('build-success');

    const buildCall = calls.find((call) => call.url.endsWith('/public-build/build'));
    expect(JSON.parse(String(buildCall?.init?.body))).toEqual({
      include_drafts: true,
      base_url: '',
    });
  });

  it('shows the validation gate message on a blocked build (422)', async () => {
    mockApi({
      buildResponse: jsonResponse(422, {
        code: 'public_build_blocked',
        message: "public-profile.yaml: missing required field 'public_name'",
      }),
    });
    renderPage();
    await screen.findByTestId('build-status');

    fireEvent.click(screen.getByTestId('build-button'));
    const error = await screen.findByTestId('mutation-error');
    expect(error).toHaveTextContent('构建失败');
    expect(error).toHaveTextContent('public_name');
  });

  it('shows the conflict alert on a stale ETag (412)', async () => {
    mockApi({
      buildResponse: withEtag(
        jsonResponse(412, { code: 'etag_mismatch', message: 'stale' }),
        'W/"fresh"',
      ),
    });
    renderPage();
    await screen.findByTestId('build-status');

    fireEvent.click(screen.getByTestId('build-button'));
    expect(await screen.findByTestId('conflict-alert')).toHaveTextContent(
      '数据已被他人修改',
    );
  });

  it('publishes the selected drafts and builds', async () => {
    const { calls } = mockApi();
    renderPage();
    await screen.findByTestId('draft-list');

    fireEvent.click(screen.getByRole('checkbox', { name: /Ready post/ }));
    const button = screen.getByTestId('publish-build-button');
    expect(button).toBeEnabled();
    fireEvent.click(button);
    await screen.findByTestId('publish-success');

    const publishCall = calls.find((call) => call.url.endsWith('/publish-and-build'));
    expect(publishCall).toBeDefined();
    const headers = publishCall?.init?.headers as Record<string, string>;
    expect(headers['If-Match']).toBe(PB_ETAG);
    expect(JSON.parse(String(publishCall?.init?.body))).toEqual({
      slugs: ['ready'],
      include_drafts: false,
      base_url: '',
    });
    expect(screen.getByTestId('publish-success')).toHaveTextContent('已发布 1 篇草稿并构建');
  });

  it('renders the artifact table with download links after a build', async () => {
    mockApi({ overview: OVERVIEW_BUILT });
    renderPage();

    const row = await screen.findByTestId('artifact-index.html');
    expect(row).toHaveTextContent('index.html');
    const link = row.querySelector('a');
    expect(link?.getAttribute('href')).toBe(
      '/api/v1/profiles/alice/public-build/artifacts/index.html',
    );
    expect(screen.getByTestId('artifact-assets/site.css')).toBeInTheDocument();
    expect(screen.getByTestId('build-exists')).toBeInTheDocument();
  });
});
