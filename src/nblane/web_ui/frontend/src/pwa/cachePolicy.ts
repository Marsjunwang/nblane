const EXCLUDED_PATH = /^\/(?:api|auth|reader|paper-library|terminal|openclaw)(?:\/|$)/;
const REALTIME_PATH = /^\/(?:sse|ws|websocket)(?:\/|$)/;
const HASHED_ASSET_PATH = /^\/assets\/[^/]+-[A-Za-z0-9_-]{8,64}\.[A-Za-z0-9]+$/;

export function bypassesServiceWorker(pathname: string, accept = '', upgrade = ''): boolean {
  return (
    EXCLUDED_PATH.test(pathname) ||
    REALTIME_PATH.test(pathname) ||
    accept.toLowerCase().includes('text/event-stream') ||
    upgrade.toLowerCase() === 'websocket'
  );
}

export function isCacheableStaticAsset(url: URL, origin: string, method: string): boolean {
  return method === 'GET' && url.origin === origin && HASHED_ASSET_PATH.test(url.pathname);
}
