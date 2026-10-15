import { fireEvent, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { jsonResponse, renderWithProviders } from '../../test/render';
import { ContentLibrary } from './ContentLibrary';
import { ContentTrashModal } from './ContentTrashModal';
import { DeleteContentPostDialog } from './DeleteContentPostDialog';
import { localDraftKey } from './contentDraft';

const POST = { slug: 'notes/hello', title: '文章 A', body: '正文', status: 'draft', summary: '', date: '2026-10-14', tags: [] };

function detail(title = POST.title, etag = 'W/"v1"') {
  const response = jsonResponse(200, { ...POST, title });
  response.headers.set('ETag', etag);
  return response;
}

afterEach(() => {
  vi.unstubAllGlobals();
  window.localStorage.clear();
});

describe('article deletion', () => {
  it('requires the exact title, sends the post ETag, and clears the browser draft only on success', async () => {
    const deleted = vi.fn();
    const requests: RequestInit[] = [];
    vi.stubGlobal('fetch', vi.fn(async (_url: string, init?: RequestInit) => {
      if (init?.method !== 'DELETE') return detail();
      requests.push(init);
      return jsonResponse(200, { ok: true, deleted_slug: POST.slug });
    }));
    window.localStorage.setItem(localDraftKey('alice', POST.slug), 'draft');
    renderWithProviders(<DeleteContentPostDialog profile="alice" slug={POST.slug} onClose={vi.fn()} onDeleted={deleted} />);
    const title = await screen.findByTestId('content-delete-title');
    const confirm = screen.getByTestId('content-delete-confirm');
    expect(confirm).toBeDisabled();
    expect(screen.getByTestId('content-delete-chronicle')).not.toBeChecked();
    fireEvent.change(title, { target: { value: '文章 A ' } });
    expect(confirm).toBeDisabled();
    fireEvent.change(title, { target: { value: POST.title } });
    fireEvent.click(confirm);
    await waitFor(() => expect(deleted).toHaveBeenCalledOnce());
    expect(requests).toHaveLength(1);
    expect(requests[0].headers).toMatchObject({ 'If-Match': 'W/"v1"' });
    expect(JSON.parse(String(requests[0].body))).toEqual({ confirm_title: POST.title, record_chronicle: false });
    expect(window.localStorage.getItem(localDraftKey('alice', POST.slug))).toBeNull();
  });

  it('requires a fresh confirmation after another writer changes the post', async () => {
    let gets = 0;
    let deletes = 0;
    const deleted = vi.fn();
    const bodies: unknown[] = [];
    vi.stubGlobal('fetch', vi.fn(async (_url: string, init?: RequestInit) => {
      if (init?.method !== 'DELETE') return ++gets === 1 ? detail() : detail('新标题', 'W/"v2"');
      bodies.push(JSON.parse(String(init.body)));
      return ++deletes === 1
        ? jsonResponse(412, { code: 'etag_mismatch', message: 'Changed' })
        : jsonResponse(200, { ok: true, deleted_slug: POST.slug });
    }));
    renderWithProviders(<DeleteContentPostDialog profile="alice" slug={POST.slug} onClose={vi.fn()} onDeleted={deleted} />);
    fireEvent.change(await screen.findByTestId('content-delete-title'), { target: { value: POST.title } });
    fireEvent.click(screen.getByTestId('content-delete-confirm'));
    expect(await screen.findByText('文章已在别处被修改，请加载最新文章后重新确认。')).toBeVisible();
    expect(deleted).not.toHaveBeenCalled();
    expect(screen.getByTestId('content-delete-confirm')).toBeDisabled();
    fireEvent.click(screen.getByRole('button', { name: '加载最新文章' }));
    const title = await screen.findByTestId('content-delete-title');
    expect(title).toHaveValue('');
    fireEvent.change(title, { target: { value: '新标题' } });
    fireEvent.click(screen.getByTestId('content-delete-chronicle'));
    fireEvent.click(screen.getByTestId('content-delete-confirm'));
    await waitFor(() => expect(deleted).toHaveBeenCalledOnce());
    expect(bodies[1]).toEqual({ confirm_title: '新标题', record_chronicle: true });
  });

  it('canceling preserves the local draft and never issues a DELETE', async () => {
    const fetch = vi.fn(async () => detail());
    vi.stubGlobal('fetch', fetch);
    const close = vi.fn();
    window.localStorage.setItem('keep', 'draft');
    renderWithProviders(<DeleteContentPostDialog profile="alice" slug={POST.slug} onClose={close} onDeleted={vi.fn()} />);
    await screen.findByTestId('content-delete-title');
    fireEvent.click(screen.getByRole('button', { name: '取消' }));
    expect(close).toHaveBeenCalledOnce();
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(window.localStorage.getItem('keep')).toBe('draft');
  });

  it('the library delete button opens confirmation without opening the editor and refreshes the list', async () => {
    let removed = false;
    vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
      if (init?.method === 'DELETE') {
        removed = true;
        return jsonResponse(200, { ok: true, deleted_slug: POST.slug });
      }
      if (url.endsWith('/content')) return jsonResponse(200, { posts: removed ? [] : [POST], summary: {} });
      return detail();
    }));
    renderWithProviders(<ContentLibrary profile="alice" />);
    fireEvent.click(await screen.findByRole('button', { name: `删除文章 ${POST.title}` }));
    fireEvent.change(await screen.findByTestId('content-delete-title'), { target: { value: POST.title } });
    fireEvent.click(screen.getByTestId('content-delete-confirm'));
    expect(await screen.findByText('还没有文章。')).toBeVisible();
    await waitFor(() => expect(screen.queryByTestId('content-delete-dialog')).not.toBeInTheDocument());
  });

  it('reminds that a published post stays online after deletion', async () => {
    vi.stubGlobal('fetch', vi.fn(async (_url: string, init?: RequestInit) => {
      if (init?.method !== 'DELETE') return detail();
      return jsonResponse(200, { ok: true, deleted_slug: POST.slug, was_published: true });
    }));
    renderWithProviders(<DeleteContentPostDialog profile="alice" slug={POST.slug} onClose={vi.fn()} onDeleted={vi.fn()} />);
    fireEvent.change(await screen.findByTestId('content-delete-title'), { target: { value: POST.title } });
    fireEvent.click(screen.getByTestId('content-delete-confirm'));
    expect(await screen.findByText(/还在网站上，到「公开站点」重新发布才会下线/)).toBeVisible();
  });
});

describe('content trash', () => {
  const ITEM = { id: '20261015T010203000000-abcdef', route: POST.slug, title: POST.title, status: 'published', deleted_at: '2026-10-15T01:02:03+00:00' };

  it('lists deleted posts and restores one', async () => {
    const calls: string[] = [];
    vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
      calls.push(`${init?.method ?? 'GET'} ${url}`);
      if (url.endsWith('/restore')) return jsonResponse(200, { ok: true, slug: POST.slug });
      return jsonResponse(200, { items: [ITEM] });
    }));
    const close = vi.fn();
    renderWithProviders(<ContentTrashModal profile="alice" onClose={close} />);
    expect(await screen.findByText(POST.title)).toBeVisible();
    fireEvent.click(screen.getByTestId('content-trash-restore'));
    await waitFor(() => expect(close).toHaveBeenCalledOnce());
    expect(calls.some((call) => call.startsWith('POST') && call.endsWith(`/content/trash/${ITEM.id}/restore`))).toBe(true);
  });

  it('asks again before deleting for good', async () => {
    let purged = false;
    vi.stubGlobal('fetch', vi.fn(async (_url: string, init?: RequestInit) => {
      if (init?.method === 'DELETE') {
        purged = true;
        return jsonResponse(200, { ok: true });
      }
      return jsonResponse(200, { items: purged ? [] : [ITEM] });
    }));
    renderWithProviders(<ContentTrashModal profile="alice" onClose={vi.fn()} />);
    fireEvent.click(await screen.findByTestId('content-trash-purge'));
    expect(purged).toBe(false);
    fireEvent.click(await screen.findByTestId('content-trash-purge-confirm'));
    expect(await screen.findByText('回收站是空的。')).toBeVisible();
    expect(purged).toBe(true);
  });
});
