import { useQueryClient } from '@tanstack/react-query';
import { act, fireEvent, screen, waitFor } from '@testing-library/react';
import { useState } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { usePublicSite } from '../../api/hooks';
import type { PublicSiteResponse, PublicSiteWork } from '../../api/types';
import { jsonResponse, renderWithProviders } from '../../test/render';
import { WorksEditor } from './WorksEditor';

const WORK: PublicSiteWork = {
  id: 'one', title: 'Original', type: 'project', year: '2026', summary: '', video: '', video_mode: 'link',
  cover: '', links: [], status: 'published', featured: false,
};
const overview = (title: string, etag: string) => ({ works: [{ ...WORK, title }], works_etag: etag } as PublicSiteResponse);

function Harness({ remote }: { remote?: PublicSiteResponse }) {
  const site = usePublicSite('alice');
  const client = useQueryClient();
  return (
    <>
      <button onClick={() => client.setQueryData(['profiles', 'alice', 'public-site'], remote)}>receive server overview</button>
      {site.data && <WorksEditor profile="alice" works={site.data.works ?? []} etag={site.data.works_etag} />}
    </>
  );
}

afterEach(() => vi.unstubAllGlobals());

describe('works editor concurrent changes', () => {
  it('does not carry dirty work from one profile into another cached profile', async () => {
    function ProfileSwitch() {
      const [profile, setProfile] = useState('alice');
      return <>
        <button onClick={() => setProfile('bob')}>switch profile</button>
        <WorksEditor profile={profile} works={[{ ...WORK, title: profile }]} etag={`${profile}-e1`} />
      </>;
    }
    renderWithProviders(<ProfileSwitch />);
    fireEvent.click(screen.getByTestId('work-0-toggle'));
    fireEvent.change(screen.getByTestId('work-0-title'), { target: { value: 'Alice unsaved' } });
    fireEvent.click(screen.getByText('switch profile'));
    fireEvent.click(screen.getByTestId('work-0-toggle'));
    expect(screen.getByTestId('work-0-title')).toHaveValue('bob');
    expect(screen.getByTestId('works-save')).toBeDisabled();
  });

  it('keeps the original ETag when another action refreshes the server overview', async () => {
    let server = overview('Original', 'e1');
    const requests: RequestInit[] = [];
    vi.stubGlobal('fetch', vi.fn(async (_url: string, init?: RequestInit) => {
      if (init?.method === 'PUT') {
        requests.push(init);
        return jsonResponse(412, { code: 'etag_mismatch', message: 'Changed' });
      }
      return jsonResponse(200, server);
    }));
    renderWithProviders(<Harness remote={overview('Other editor', 'e2')} />);
    fireEvent.click(await screen.findByTestId('work-0-toggle'));
    fireEvent.change(screen.getByTestId('work-0-title'), { target: { value: 'My edit' } });
    server = overview('Other editor', 'e2');
    fireEvent.click(screen.getByText('receive server overview'));
    fireEvent.click(screen.getByTestId('works-save'));
    await screen.findByTestId('works-conflict');
    expect((requests[0].headers as Record<string, string>)['If-Match']).toBe('e1');
    expect(screen.getByTestId('work-0-title')).toHaveValue('My edit');
    await waitFor(() => expect(screen.getByTestId('works-save')).toBeEnabled());
    fireEvent.click(screen.getByRole('button', { name: '放弃修改' }));
    await waitFor(() => expect(screen.getByTestId('work-0-title')).toHaveValue('Other editor'));
  });

  it('retains edits made during a save and advances only their baseline ETag', async () => {
    let resolveFirst!: (response: Response) => void;
    const requests: RequestInit[] = [];
    vi.stubGlobal('fetch', vi.fn(async (_url: string, init?: RequestInit) => {
      if (init?.method === 'PUT') {
        requests.push(init);
        if (requests.length === 1) return new Promise<Response>((resolve) => { resolveFirst = resolve; });
        return jsonResponse(200, overview('Typed while saving', 'e3'));
      }
      return jsonResponse(200, overview('Original', 'e1'));
    }));
    renderWithProviders(<Harness />);
    fireEvent.click(await screen.findByTestId('work-0-toggle'));
    fireEvent.change(screen.getByTestId('work-0-title'), { target: { value: 'Submitted' } });
    fireEvent.click(screen.getByTestId('works-save'));
    await waitFor(() => expect(requests).toHaveLength(1));
    fireEvent.change(screen.getByTestId('work-0-title'), { target: { value: 'Typed while saving' } });
    await act(async () => resolveFirst(jsonResponse(200, overview('Submitted', 'e2'))));
    await waitFor(() => expect(screen.getByTestId('works-save')).toBeEnabled());
    expect(screen.getByTestId('work-0-title')).toHaveValue('Typed while saving');
    fireEvent.click(screen.getByTestId('works-save'));
    await waitFor(() => expect(requests).toHaveLength(2));
    expect((requests[1].headers as Record<string, string>)['If-Match']).toBe('e2');
    expect(JSON.parse(String(requests[1].body)).works[0].title).toBe('Typed while saving');
    await waitFor(() => expect(screen.getByTestId('works-save')).toHaveTextContent('已保存'));
  });
});
