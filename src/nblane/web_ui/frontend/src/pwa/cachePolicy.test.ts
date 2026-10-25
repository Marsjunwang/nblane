import { describe, expect, it } from 'vitest';

import { bypassesServiceWorker, isCacheableStaticAsset } from './cachePolicy';

const ORIGIN = 'https://nblane.test';

describe('isCacheableStaticAsset', () => {
  it('allows same-origin GET requests for content-hashed Vite assets', () => {
    expect(
      isCacheableStaticAsset(new URL('/assets/index-DfB7VAyo.js', ORIGIN), ORIGIN, 'GET'),
    ).toBe(true);
    expect(
      isCacheableStaticAsset(new URL('/assets/index--QW0nyyA.css', ORIGIN), ORIGIN, 'GET'),
    ).toBe(true);
  });

  it('rejects unhashed paths, business paths, other origins, and non-GET requests', () => {
    expect(isCacheableStaticAsset(new URL('/assets/app.js', ORIGIN), ORIGIN, 'GET')).toBe(false);
    expect(isCacheableStaticAsset(new URL('/api/v1/health', ORIGIN), ORIGIN, 'GET')).toBe(false);
    expect(
      isCacheableStaticAsset(new URL('https://other.test/assets/index-DfB7VAyo.js'), ORIGIN, 'GET'),
    ).toBe(false);
    expect(
      isCacheableStaticAsset(new URL('/assets/index-DfB7VAyo.js', ORIGIN), ORIGIN, 'POST'),
    ).toBe(false);
  });
});

describe('bypassesServiceWorker', () => {
  it.each([
    '/api',
    '/api/v1/jobs/job-1/stream',
    '/auth/me',
    '/reader/paper.pdf',
    '/paper-library/',
    '/terminal/ws',
    '/openclaw',
    '/sse',
    '/ws',
    '/websocket',
  ])('bypasses dynamic or realtime path %s', (pathname) => {
    expect(bypassesServiceWorker(pathname)).toBe(true);
  });

  it('bypasses SSE and WebSocket requests by their headers', () => {
    expect(bypassesServiceWorker('/events', 'text/event-stream')).toBe(true);
    expect(bypassesServiceWorker('/socket', '', 'WebSocket')).toBe(true);
  });

  it('keeps ordinary SPA routes eligible for online-first navigation', () => {
    expect(bypassesServiceWorker('/')).toBe(false);
    expect(bypassesServiceWorker('/p/alice/home', 'text/html')).toBe(false);
    expect(bypassesServiceWorker('/apiary')).toBe(false);
  });
});
