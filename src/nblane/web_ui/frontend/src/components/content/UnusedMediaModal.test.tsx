import { fireEvent, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { jsonResponse, renderWithProviders } from '../../test/render';
import { UnusedMediaModal, formatBytes } from './UnusedMediaModal';

const ITEMS = [
  { path: 'media/blog/a/x.png', name: 'x.png', post: 'a', kind: 'image', size: 2 * 1024 * 1024, modified: '' },
  { path: 'media/blog/b/y.png', name: 'y.png', post: 'b', kind: 'image', size: 512 * 1024, modified: '' },
];

afterEach(() => vi.unstubAllGlobals());

describe('unused media cleanup', () => {
  it('formats sizes', () => {
    expect(formatBytes(2 * 1024 * 1024)).toBe('2.0 MB');
    expect(formatBytes(2048)).toBe('2 KB');
    expect(formatBytes(10)).toBe('10 B');
  });

  it('preselects every unused file and deletes only the checked ones after confirming', async () => {
    const bodies: unknown[] = [];
    let left = ITEMS;
    vi.stubGlobal('fetch', vi.fn(async (_url: string, init?: RequestInit) => {
      if (init?.method === 'POST') {
        const body = JSON.parse(String(init.body)) as { paths: string[] };
        bodies.push(body);
        left = left.filter((item) => !body.paths.includes(item.path));
        return jsonResponse(200, { ok: true, removed: body.paths });
      }
      return jsonResponse(200, { items: left, total_size: left.reduce((sum, item) => sum + item.size, 0) });
    }));
    renderWithProviders(<UnusedMediaModal profile="alice" onClose={vi.fn()} />);
    expect(await screen.findByText('已选 2 个，共 2.5 MB')).toBeVisible();
    fireEvent.click(screen.getByLabelText('选择 y.png'));
    expect(screen.getByText('已选 1 个，共 2.0 MB')).toBeVisible();
    fireEvent.click(screen.getByTestId('content-unused-media-delete'));
    expect(bodies).toHaveLength(0);
    fireEvent.click(await screen.findByTestId('content-unused-media-confirm'));
    await waitFor(() => expect(bodies).toEqual([{ paths: ['media/blog/a/x.png'] }]));
    expect(await screen.findByText('y.png')).toBeVisible();
    await waitFor(() => expect(screen.queryByText('x.png')).not.toBeInTheDocument());
  });
});
