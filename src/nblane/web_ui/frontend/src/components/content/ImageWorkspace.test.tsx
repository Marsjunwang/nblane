import { fireEvent, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { jsonResponse, renderWithProviders } from '../../test/render';
import { ImageWorkspace } from './ImageWorkspace';

const RUN = {
  id: 'image-' + 'a'.repeat(32),
  slug: 'post',
  status: 'done',
  created_at: 1,
  reference: '',
  error: '',
  request: { mode: 'cover', reference: '', target: { kind: 'cover', source: '' }, instruction: '夜景' },
  candidates: [{ candidate_path: 'blog/.candidates/image-x/cover.png', filename: 'cover.png', applied_path: '' }],
};

function mount() {
  const calls: Array<{ url: string; method: string }> = [];
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const method = init?.method ?? 'GET';
      calls.push({ url, method });
      if (url.includes('/content/images?') && method === 'GET') return jsonResponse(200, { runs: [RUN] });
      if (url.endsWith('/content/images/discard')) return jsonResponse(200, { ok: true });
      return jsonResponse(404, { code: 'not_found', message: url });
    }),
  );
  renderWithProviders(
    <ImageWorkspace
      profile="alice"
      slug="post"
      opened
      request={null}
      enabled
      media={[]}
      draft={{ title: 'T', summary: '', tags: [], body: '' }}
      onClose={() => undefined}
      onApply={() => true}
      canApply={() => true}
    />,
  );
  return calls;
}

const discards = (calls: Array<{ url: string }>) => calls.filter((call) => call.url.endsWith('/discard'));

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('ImageWorkspace discard', () => {
  it('asks before deleting a candidate and does nothing when cancelled', async () => {
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false);
    const calls = mount();
    fireEvent.click(await screen.findByRole('button', { name: '丢弃候选' }));
    expect(confirm).toHaveBeenCalledWith(expect.stringContaining('无法找回'));
    expect(discards(calls)).toHaveLength(0);
  });

  it('deletes the candidate once confirmed', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    const calls = mount();
    fireEvent.click(await screen.findByRole('button', { name: '丢弃候选' }));
    await waitFor(() => expect(discards(calls)).toHaveLength(1));
  });
});
