/// <reference lib="webworker" />

import { bypassesServiceWorker, isCacheableStaticAsset } from './cachePolicy';

export {};

interface PrecacheEntry {
  url: string;
  revision?: string | null;
}

declare const __PRECACHE_MANIFEST__: PrecacheEntry[];

const worker = self as unknown as ServiceWorkerGlobalScope;
const precacheManifest = __PRECACHE_MANIFEST__;
const precacheUrls = precacheManifest.map((entry) => entry.url);
const precacheUrlSet = new Set(precacheUrls.map((url) => new URL(url, worker.location.origin).href));
const offlineUrl = new URL('/offline.html', worker.location.origin).href;

function precacheVersion(entries: PrecacheEntry[]): string {
  const source = entries
    .map((entry) => `${entry.url}:${entry.revision ?? ''}`)
    .sort()
    .join('|');
  let hash = 2166136261;
  for (let index = 0; index < source.length; index += 1) {
    hash ^= source.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(36);
}

const cacheVersion = precacheVersion(precacheManifest);
const precacheCacheName = `nblane-shell-${cacheVersion}`;
const runtimeCacheName = `nblane-static-assets-${cacheVersion}`;

worker.addEventListener('install', (event) => {
  event.waitUntil(
    (async () => {
      const cache = await caches.open(precacheCacheName);
      await cache.addAll(precacheUrls.map((url) => new Request(url, { cache: 'reload' })));
    })(),
  );
});

worker.addEventListener('activate', (event) => {
  event.waitUntil(
    (async () => {
      const cacheNames = await caches.keys();
      await Promise.all(
        cacheNames
          .filter(
            (name) =>
              (name.startsWith('nblane-shell-') || name.startsWith('nblane-static-assets-')) &&
              name !== precacheCacheName &&
              name !== runtimeCacheName,
          )
          .map((name) => caches.delete(name)),
      );
      await worker.clients.claim();
    })(),
  );
});

worker.addEventListener('message', (event) => {
  if (event.data?.type === 'SKIP_WAITING') {
    void worker.skipWaiting();
  }
});

async function networkFirstNavigation(request: Request): Promise<Response> {
  try {
    return await fetch(request);
  } catch (error) {
    const cache = await caches.open(precacheCacheName);
    const offlineResponse = await cache.match(offlineUrl);
    if (offlineResponse) return offlineResponse;
    throw error;
  }
}

async function cacheFirstStaticAsset(request: Request): Promise<Response> {
  const precache = await caches.open(precacheCacheName);
  const precached = await precache.match(request);
  if (precached) return precached;

  const runtimeCache = await caches.open(runtimeCacheName);
  const cached = await runtimeCache.match(request);
  if (cached) return cached;

  const response = await fetch(request);
  if (response.status === 200 && response.type === 'basic') {
    try {
      await runtimeCache.put(request, response.clone());
    } catch {
      return response;
    }
  }
  return response;
}

async function precachedStaticFile(request: Request): Promise<Response> {
  const cache = await caches.open(precacheCacheName);
  return (await cache.match(request)) ?? fetch(request);
}

worker.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== worker.location.origin) return;
  if (
    bypassesServiceWorker(
      url.pathname,
      request.headers.get('accept') ?? '',
      request.headers.get('upgrade') ?? '',
    )
  ) {
    return;
  }

  if (request.mode === 'navigate') {
    event.respondWith(networkFirstNavigation(request));
  } else if (isCacheableStaticAsset(url, worker.location.origin, request.method)) {
    event.respondWith(cacheFirstStaticAsset(request));
  } else if (precacheUrlSet.has(url.href)) {
    event.respondWith(precachedStaticFile(request));
  }
});
