import { fireEvent, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { jsonResponse, renderWithProviders } from '../../test/render';
import { DesktopStickerSection } from './DesktopStickerSection';

const ARM_URL = 'https://www.nblane.cloud/downloads/sticker/0.1.3/nblane-sticker-mac-arm64.zip';
const INTEL_URL = 'https://www.nblane.cloud/downloads/sticker/0.1.3/nblane-sticker-mac-x64.zip';
const RELEASE = {
  version: '0.1.3', macosMinVersion: '13', publishedAt: '2026-11-15T03:00:00Z', signing: 'ad-hoc',
  files: { arm64: { url: ARM_URL, sha256: 'a'.repeat(64), size: 120_000_000 } },
};

afterEach(() => vi.unstubAllGlobals());

describe('DesktopStickerSection', () => {
  it('offers a direct Apple silicon download without guessing the machine architecture', async () => {
    const fetchMock = vi.fn(async () => jsonResponse(200, RELEASE));
    vi.stubGlobal('fetch', fetchMock);
    renderWithProviders(<DesktopStickerSection />);
    expect(await screen.findByRole('link', { name: '下载 Mac 版 · Apple 芯片' })).toHaveAttribute('href', ARM_URL);
    expect(screen.getByRole('link', { name: '下载 Mac 版 · Apple 芯片' })).toHaveAttribute('download');
    expect(screen.queryByRole('link', { name: '下载 Mac 版 · Intel' })).not.toBeInTheDocument();
    expect(screen.getByText(/Intel 版暂未提供/)).toBeInTheDocument();
    expect(screen.getByText(/当前安装包尚未经过 Apple 公证/)).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith('https://www.nblane.cloud/downloads/sticker/latest.json', expect.objectContaining({ credentials: 'omit', redirect: 'error' }));
  });

  it('offers Intel separately when the release includes that archive', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse(200, {
      ...RELEASE, files: { ...RELEASE.files, x64: { url: INTEL_URL, sha256: 'b'.repeat(64), size: 130_000_000 } },
    })));
    renderWithProviders(<DesktopStickerSection />);
    expect(await screen.findByRole('link', { name: '下载 Mac 版 · Intel' })).toHaveAttribute('href', INTEL_URL);
    expect(screen.getByRole('link', { name: '下载 Mac 版 · Apple 芯片' })).toHaveAttribute('href', ARM_URL);
  });

  it.each([
    ['an external archive', { ...RELEASE, files: { arm64: { ...RELEASE.files.arm64, url: 'https://example.test/file.zip' } } }],
    ['a file outside the release path', { ...RELEASE, files: { arm64: { ...RELEASE.files.arm64, url: 'https://www.nblane.cloud/api/export.zip' } } }],
    ['an invalid checksum', { ...RELEASE, files: { arm64: { ...RELEASE.files.arm64, sha256: 'missing' } } }],
    ['an invalid size', { ...RELEASE, files: { arm64: { ...RELEASE.files.arm64, size: -1 } } }],
    ['an invalid version', { ...RELEASE, version: '' }],
  ])('does not expose downloads for %s', async (_label, manifest) => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse(200, manifest)));
    renderWithProviders(<DesktopStickerSection />);
    expect(await screen.findByRole('alert')).toHaveTextContent('暂时无法获取下载信息');
    expect(screen.queryByRole('link', { name: /下载 Mac 版/ })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: '重新获取' })).toBeEnabled();
  });

  it('recovers through retry when the release manifest was unavailable', async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(jsonResponse(404, {})).mockResolvedValueOnce(jsonResponse(200, RELEASE));
    vi.stubGlobal('fetch', fetchMock);
    renderWithProviders(<DesktopStickerSection />);
    fireEvent.click(await screen.findByRole('button', { name: '重新获取' }));
    expect(await screen.findByRole('link', { name: '下载 Mac 版 · Apple 芯片' })).toHaveAttribute('href', ARM_URL);
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
});
