// Thin fetch wrapper for the nblane FastAPI backend.
//
// All requests go to the same origin under /api/v1 (the Vite dev server
// proxies /api → the uvicorn sidecar) and carry the httpOnly session cookie
// via `credentials: 'include'`.

import type { QueryClient } from '@tanstack/react-query';

const API_BASE = '/api/v1';

/** Base path of the JSON API (same origin). Used by the SSE job stream. */
export function apiBase(): string {
  return API_BASE;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, message: string, code = '') {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

async function errorMessage(res: Response): Promise<{ message: string; code: string }> {
  const fallback = `Request failed with status ${res.status}`;
  try {
    const body: unknown = await res.json();
    if (body && typeof body === 'object') {
      // Structured ApiError body: {code, message}
      if ('message' in body && typeof (body as { message: unknown }).message === 'string') {
        const { message } = body as { message: string };
        const code = 'code' in body ? String((body as { code: unknown }).code) : '';
        return { message, code };
      }
      // FastAPI HTTPException body: {detail: "..."} (also 422 arrays)
      if ('detail' in body) {
        const detail = (body as { detail: unknown }).detail;
        return { message: typeof detail === 'string' ? detail : JSON.stringify(detail), code: '' };
      }
    }
  } catch {
    // Non-JSON error body — fall through to the generic message.
  }
  return { message: fallback, code: '' };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const { data } = await requestWithHeaders<T>(path, init);
  return data;
}

let unauthorizedHandler: (() => void) | undefined;

/** Replace the 401 callback (main.tsx installs one; tests may clear it). */
export function setUnauthorizedHandler(handler: (() => void) | undefined): void {
  unauthorizedHandler = handler;
}

/**
 * Drop the cached session on any 401 so the RequireAuth guard refetches,
 * sees the 401 itself, and redirects to /login. Guarded on a *successful*
 * cached session: without it the refetch's own 401 (or a failed login
 * attempt on /login) would retrigger this handler in a loop.
 */
export function installUnauthorizedHandler(queryClient: QueryClient): void {
  setUnauthorizedHandler(() => {
    if (queryClient.getQueryState(['auth', 'me'])?.status === 'success') {
      void queryClient.resetQueries({ queryKey: ['auth', 'me'], exact: true });
    }
  });
}

/**
 * Build an If-Match header only when the ETag is known. Sending an empty
 * If-Match would fail the server's precondition check unconditionally (412).
 */
export function ifMatch(etag: string): Record<string, string> {
  return etag ? { 'If-Match': etag } : {};
}

async function requestWithHeaders<T>(
  path: string,
  init?: RequestInit,
): Promise<{ data: T; headers: Headers }> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  });
  if (!res.ok) {
    if (res.status === 401) {
      unauthorizedHandler?.();
    }
    const { message, code } = await errorMessage(res);
    throw new ApiError(res.status, message, code);
  }
  if (res.status === 204) {
    return { data: undefined as T, headers: res.headers };
  }
  return { data: (await res.json()) as T, headers: res.headers };
}

export function apiGet<T>(path: string): Promise<T> {
  return request<T>(path);
}

/** GET that also exposes response headers (e.g. ETag for If-Match flows). */
export function apiGetWithHeaders<T>(path: string): Promise<{ data: T; headers: Headers }> {
  return requestWithHeaders<T>(path);
}

export function apiPost<T>(path: string, body?: unknown, init?: RequestInit): Promise<T> {
  return request<T>(path, {
    ...init,
    method: 'POST',
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

/** POST that also exposes response headers (fresh ETag after a mutation). */
export function apiPostWithHeaders<T>(
  path: string,
  body?: unknown,
  init?: RequestInit,
): Promise<{ data: T; headers: Headers }> {
  return requestWithHeaders<T>(path, {
    ...init,
    method: 'POST',
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

export function apiPatch<T>(path: string, body?: unknown, init?: RequestInit): Promise<T> {
  return request<T>(path, {
    ...init,
    method: 'PATCH',
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

/** DELETE with an optional JSON body (e.g. the project-delete confirm). */
export function apiDelete<T>(path: string, body?: unknown, init?: RequestInit): Promise<T> {
  return request<T>(path, {
    ...init,
    method: 'DELETE',
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

/** PATCH that also exposes response headers (fresh ETag after a mutation). */
export function apiPatchWithHeaders<T>(
  path: string,
  body?: unknown,
  init?: RequestInit,
): Promise<{ data: T; headers: Headers }> {
  return requestWithHeaders<T>(path, {
    ...init,
    method: 'PATCH',
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}
