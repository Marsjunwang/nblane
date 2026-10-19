import { afterEach, describe, expect, it, vi } from 'vitest';

import { MINI_WINDOW_SIZE, openMiniWindow } from './MiniWindowButton';

afterEach(() => {
  vi.unstubAllGlobals();
  delete (window as unknown as { documentPictureInPicture?: unknown }).documentPictureInPicture;
});

describe('openMiniWindow', () => {
  it('opens an always-on-top window holding the mini page when supported', async () => {
    const pipDoc = document.implementation.createHTMLDocument('pip');
    const requestWindow = vi.fn(async () => ({ document: pipDoc }) as unknown as Window);
    (window as unknown as { documentPictureInPicture: unknown }).documentPictureInPicture = { requestWindow };
    const popup = vi.fn();
    vi.stubGlobal('open', popup);

    await expect(openMiniWindow('王军')).resolves.toBe('pip');

    expect(requestWindow).toHaveBeenCalledWith(MINI_WINDOW_SIZE);
    const frame = pipDoc.querySelector('iframe');
    expect(frame?.src).toBe(new URL('/p/%E7%8E%8B%E5%86%9B/mini', window.location.origin).href);
    expect(popup).not.toHaveBeenCalled();
  });

  it('falls back to a popup when the browser has no Document PiP', async () => {
    const popup = vi.fn(() => ({}) as Window);
    vi.stubGlobal('open', popup);
    await expect(openMiniWindow('alice')).resolves.toBe('popup');
    expect(popup).toHaveBeenCalledWith('/p/alice/mini', 'nblane-mini', expect.stringContaining('popup=yes'));
  });

  it('reports a blocked popup', async () => {
    vi.stubGlobal('open', vi.fn(() => null));
    await expect(openMiniWindow('alice')).resolves.toBe('blocked');
  });
});
