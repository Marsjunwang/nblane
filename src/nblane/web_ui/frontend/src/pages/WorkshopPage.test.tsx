import { screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { jsonResponse, renderWithProviders } from '../test/render';
import { WorkshopPage } from './WorkshopPage';

const REACHABLE_PAYLOAD = {
  url: '/terminal/',
  reachable: true,
  checked_at: '2026-09-22T10:00:00+00:00',
};

const DOWN_PAYLOAD = {
  url: '/terminal/',
  reachable: false,
  checked_at: '2026-09-22T10:00:00+00:00',
};

function stubFetch(payload: unknown, status = 200) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => jsonResponse(status, payload)),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('WorkshopPage', () => {
  it('embeds the terminal iframe at the configured url when reachable', async () => {
    stubFetch(REACHABLE_PAYLOAD);
    renderWithProviders(<WorkshopPage />, '/workshop');

    expect(await screen.findByText('车间')).toBeInTheDocument();
    const frame = await screen.findByTestId('sidecar-frame');
    expect(frame).toHaveAttribute('src', '/terminal/');
    const link = screen.getByRole('link', { name: '新标签页打开' });
    expect(link).toHaveAttribute('href', '/terminal/');
    expect(link).toHaveAttribute('target', '_blank');
  });

  it('shows start instructions instead of the iframe when ttyd is down', async () => {
    stubFetch(DOWN_PAYLOAD);
    renderWithProviders(<WorkshopPage />, '/workshop');

    expect(await screen.findByText('车间终端未运行')).toBeInTheDocument();
    expect(screen.getByText(/nblane-workshop\.service/)).toBeInTheDocument();
    expect(screen.getByText(/phase0\.5-remote-terminal\.md/)).toBeInTheDocument();
    expect(screen.queryByTestId('sidecar-frame')).not.toBeInTheDocument();
  });

  it('shows an error alert when the request fails', async () => {
    stubFetch({ detail: 'boom' }, 500);
    renderWithProviders(<WorkshopPage />, '/workshop');

    expect(await screen.findByText('加载失败')).toBeInTheDocument();
  });
});
