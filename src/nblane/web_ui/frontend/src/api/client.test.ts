import { QueryClient } from '@tanstack/react-query';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { jsonResponse } from '../test/render';
import {
  ApiError,
  apiGet,
  apiPost,
  ifMatch,
  installUnauthorizedHandler,
  setUnauthorizedHandler,
} from './client';

afterEach(() => {
  setUnauthorizedHandler(undefined);
  vi.unstubAllGlobals();
});

describe('api client', () => {
  it('maps FastAPI HTTPException {detail} bodies into ApiError', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => jsonResponse(401, { detail: 'Authentication required' })),
    );
    const error = await apiGet('/auth/me').catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    const apiError = error as ApiError;
    expect(apiError.status).toBe(401);
    expect(apiError.message).toBe('Authentication required');
  });

  it('maps structured {code, message} error bodies', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        jsonResponse(404, { code: 'profile_not_found', message: 'Profile not found.' }),
      ),
    );
    const error = await apiGet('/profiles/nope/health').catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    const apiError = error as ApiError;
    expect(apiError.status).toBe(404);
    expect(apiError.code).toBe('profile_not_found');
    expect(apiError.message).toBe('Profile not found.');
  });

  it('sends cookies and JSON, and parses success bodies', async () => {
    const fetchMock = vi.fn(async () => jsonResponse(200, { ok: true }));
    vi.stubGlobal('fetch', fetchMock);
    const data = await apiPost<{ ok: boolean }>('/auth/logout');
    expect(data.ok).toBe(true);
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/auth/logout',
      expect.objectContaining({
        method: 'POST',
        credentials: 'include',
        headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
      }),
    );
  });

  it('falls back to a generic message for non-JSON error bodies', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response('bad gateway', { status: 502 })),
    );
    const error = await apiGet('/health').catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).message).toBe('Request failed with status 502');
  });

  it('invokes the registered handler on 401, but not on other errors', async () => {
    const handler = vi.fn();
    setUnauthorizedHandler(handler);
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => jsonResponse(401, { detail: 'Authentication required' })),
    );
    await apiGet('/profiles').catch(() => undefined);
    expect(handler).toHaveBeenCalledTimes(1);

    handler.mockClear();
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => jsonResponse(500, { detail: 'boom' })),
    );
    await apiGet('/profiles').catch(() => undefined);
    expect(handler).not.toHaveBeenCalled();
  });

  it('installUnauthorizedHandler resets a cached session exactly once per expiry', async () => {
    const queryClient = new QueryClient();
    queryClient.setQueryData(['auth', 'me'], { id: 'u1', display_name: 'Admin' });
    installUnauthorizedHandler(queryClient);
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => jsonResponse(401, { detail: 'Authentication required' })),
    );

    await apiGet('/profiles').catch(() => undefined);
    // The stale session was dropped so RequireAuth refetches and redirects.
    expect(queryClient.getQueryData(['auth', 'me'])).toBeUndefined();

    // A second 401 (the guard's refetch, or a failed login attempt) must not
    // retrigger the reset — otherwise the handler would loop on itself.
    queryClient.setQueryData(['auth', 'me'], undefined);
    await apiGet('/profiles').catch(() => undefined);
    expect(queryClient.getQueryState(['auth', 'me'])?.status).not.toBe('success');
  });

  it('keeps Content-Type: application/json when init carries extra headers (If-Match)', async () => {
    // Regression: spreading `init` after `headers` used to drop Content-Type
    // whenever a mutation passed ifMatch(etag); fetch then defaulted the
    // string body to text/plain and FastAPI 422'd every write.
    const fetchMock = vi.fn(async () => jsonResponse(200, { ok: true }));
    vi.stubGlobal('fetch', fetchMock);
    await apiPost<{ ok: boolean }>('/profiles/dev/kanban/cards', { title: 'x' }, {
      headers: ifMatch('W/"abc"'),
    });
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/profiles/dev/kanban/cards',
      expect.objectContaining({
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json', 'If-Match': 'W/"abc"' },
        body: JSON.stringify({ title: 'x' }),
      }),
    );
  });

  it('ifMatch omits the header for an empty ETag and sets it otherwise', () => {
    expect(ifMatch('')).toEqual({});
    expect(ifMatch('W/"abc"')).toEqual({ 'If-Match': 'W/"abc"' });
  });
});
