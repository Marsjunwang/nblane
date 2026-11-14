import { cleanup, fireEvent, screen, waitFor } from '@testing-library/react';
import { Link, Outlet, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { jsonResponse, renderWithProviders } from '../../test/render';
import { RouteContent } from '../PageBoundary';
import { ResumeEditor } from './ResumeEditor';
import { TargetWorkspace } from './TargetWorkspace';

const RESUME = {
  profile: 'alice', visibility: 'private', summary: '', skills: [], skill_groups: [], experiences: [], projects: [],
  outputs: [], education: [], honors: [], extra_sections: [], section_titles: {},
  basics: { name: 'Alice', title: '', tagline: '', location: '', phone: '', email: '', links: [] },
};

beforeEach(() => {
  localStorage.clear();
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (init?.method === 'PUT') return jsonResponse(412, { code: 'etag_mismatch', message: 'Changed elsewhere' });
    if (url.endsWith('/career')) return jsonResponse(200, {
      profile: 'alice', ai_available: false, has_resume: true, pdf_available: false,
      resume: RESUME, resume_etag: 'e1', resume_markdown: '# Alice',
      drafts: [{ id: 'd1', target: 'Engineer', etag: 'e1', jd_text: 'Original JD', markdown: '# Alice', notes: '', updated_at: 1 }],
    });
    if (url.includes('/career/preview')) return jsonResponse(200, { html: '<p>Alice</p>' });
    return jsonResponse(404, {});
  }));
});

afterEach(async () => {
  cleanup();
  await Promise.resolve();
  localStorage.clear();
  vi.unstubAllGlobals();
});

describe('career navigation save prerequisite', () => {
  it('preserves edits across the route boundary when an exit request fails', async () => {
    renderWithProviders(
      <Routes>
        <Route element={<>
          <Link to="/edit?view=preview">更换视图</Link>
          <Link to="/other">其他页面</Link>
          <Link to="/edit">返回编辑器</Link>
          <RouteContent><Outlet /></RouteContent>
        </>}>
          <Route path="/edit" element={<ResumeEditor profile="alice" />} />
          <Route path="/other" element={<div>其他页面内容</div>} />
        </Route>
      </Routes>,
      '/edit',
    );
    await screen.findByTestId('resume-summary');
    await new Promise((resolve) => setTimeout(resolve, 0));
    fireEvent.change(screen.getByTestId('resume-summary'), { target: { value: '保留完整草稿' } });
    fireEvent.click(screen.getByRole('link', { name: '更换视图' }));
    expect(screen.getByTestId('resume-summary')).toHaveValue('保留完整草稿');
    expect(vi.mocked(fetch).mock.calls.some(([, init]) => init?.keepalive)).toBe(false);
    fireEvent.click(screen.getByRole('link', { name: '其他页面' }));
    await screen.findByText('其他页面内容');
    await waitFor(() => expect(vi.mocked(fetch).mock.calls.some(([, init]) => init?.keepalive)).toBe(true));
    fireEvent.click(screen.getByRole('link', { name: '返回编辑器' }));
    await screen.findByText('已恢复本地草稿');
    expect(screen.getByTestId('resume-summary')).toHaveValue('保留完整草稿');
    expect(localStorage.length).toBe(1);
  });

  it('keeps an empty draft open instead of marking the older server text as saved', async () => {
    renderWithProviders(
      <Routes>
        <Route path="/edit" element={<TargetWorkspace profile="alice" draftId="d1" />} />
        <Route path="/p/alice/career" element={<div>Career list destination</div>} />
      </Routes>,
      '/edit',
    );
    await screen.findByTestId('career-jd');
    await new Promise((resolve) => setTimeout(resolve, 0));
    fireEvent.click(screen.getByRole('tab', { name: '定制简历' }));
    fireEvent.click(screen.getByText('编辑 Markdown'));
    fireEvent.change(screen.getByTestId('career-draft-markdown'), { target: { value: '' } });
    fireEvent.click(screen.getByTestId('career-back'));
    expect(await screen.findByText('定制简历正文不能为空。请补充正文后再保存或导出。')).toBeInTheDocument();
    expect(screen.queryByText('Career list destination')).not.toBeInTheDocument();
    expect(vi.mocked(fetch).mock.calls.some(([, init]) => init?.method === 'PUT')).toBe(false);
    expect(localStorage.length).toBe(1);
  });

  it.each([
    { name: 'master resume', element: <ResumeEditor profile="alice" />, field: 'resume-summary', title: '简历已在别处修改' },
    { name: 'target draft', element: <TargetWorkspace profile="alice" draftId="d1" />, field: 'career-jd', title: '定制简历已在别处修改' },
  ])('keeps the $name open after a save conflict', async ({ element, field, title }) => {
    renderWithProviders(
      <Routes>
        <Route path="/edit" element={element} />
        <Route path="/p/alice/career" element={<div>Career list destination</div>} />
      </Routes>,
      '/edit',
    );
    await screen.findByTestId(field);
    // Mantine changes the initial wide layout after its media-query effect.
    await new Promise((resolve) => setTimeout(resolve, 0));
    fireEvent.change(screen.getByTestId(field), { target: { value: 'Unsaved changes' } });
    fireEvent.click(screen.getByTestId('career-back'));
    expect(await screen.findByText(title)).toBeInTheDocument();
    expect(screen.getByTestId(field)).toHaveValue('Unsaved changes');
    expect(screen.queryByText('Career list destination')).not.toBeInTheDocument();
    expect(localStorage.length).toBe(1);
  });
});
