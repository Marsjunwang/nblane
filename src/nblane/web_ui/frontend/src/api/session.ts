// Session-expiry state shared by the API client and the UI.
//
// When a session dies while the app is in use (cookie expired, "logout
// all" on another device) the client flags it here instead of dropping the
// cached user: RequireAuth keeps the page mounted, a login modal opens on
// top, and unsaved editor state survives. After a successful re-login the
// flag clears and SESSION_RESTORED_EVENT lets pages retry failed writes.

import { useSyncExternalStore } from 'react';

export const SESSION_RESTORED_EVENT = 'nblane:session-restored';

let expired = false;
const listeners = new Set<() => void>();

function emit(): void {
  for (const listener of listeners) listener();
}

export function isSessionExpired(): boolean {
  return expired;
}

export function markSessionExpired(): void {
  if (expired) return;
  expired = true;
  emit();
}

export function markSessionRestored(): void {
  if (!expired) return;
  expired = false;
  emit();
  window.dispatchEvent(new Event(SESSION_RESTORED_EVENT));
}

export function subscribeSession(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function useSessionExpired(): boolean {
  return useSyncExternalStore(subscribeSession, isSessionExpired, isSessionExpired);
}
