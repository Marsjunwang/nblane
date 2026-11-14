// Debounced, conflict-safe autosave for one document (resume or draft).
//
// Same contract as the blog editor: edits schedule a save after idle,
// autosaves skip the server's Git backup commit, an explicit flush (⌘S,
// leaving the page) commits, a 412 freezes saving until the user reloads,
// and a local backup survives failed exit requests and in-app navigation.

import { useCallback, useEffect, useRef, useState } from 'react';

import { isConflictError } from '../ConflictAlert';
import { careerDraftKey, clearCareerDraft, readCareerDraft, writeCareerDraft } from './localDraft';

export type SaveState = 'saved' | 'dirty' | 'saving' | 'error' | 'conflict';

const DEFAULT_DELAY_MS = 1500;
/** keepalive fetch bodies are capped at 64 KiB by browsers. */
const KEEPALIVE_MAX_BYTES = 60_000;

export interface AutosaveOptions<T> {
  /** Stable profile + document identity; editors remount when this changes. */
  storageKey: string;
  initial: T;
  etag: string;
  save: (value: T, etag: string, autosave: boolean) => Promise<string>;
  /** Request used for the last-chance save on unload/unmount. */
  keepalive?: (value: T, etag: string) => { url: string; method: string; body: string } | null;
  delayMs?: number;
}

export function useAutosave<T>({ storageKey, initial, etag, save, keepalive, delayMs = DEFAULT_DELAY_MS }: AutosaveOptions<T>) {
  const [restored] = useState(() => readCareerDraft(storageKey, initial));
  const [localKey] = useState(() => careerDraftKey(storageKey));
  const [value, setValue] = useState<T>(restored?.value ?? initial);
  const [state, setState] = useState<SaveState>(restored ? (restored.etag === etag ? 'dirty' : 'conflict') : 'saved');
  const [error, setError] = useState('');
  const [savedAt, setSavedAt] = useState<Date | null>(null);

  const valueRef = useRef<T>(restored?.value ?? initial);
  const etagRef = useRef(restored?.etag ?? etag);
  const revisionRef = useRef(restored ? 1 : 0);
  const savedRevisionRef = useRef(0);
  const uncommittedRef = useRef(false);
  const conflictRef = useRef(Boolean(restored && restored.etag !== etag));
  const failedRef = useRef(false);
  const discardedRef = useRef(false);
  const mountedRef = useRef(true);
  const localRawRef = useRef<string | null>(null);
  const inFlightRef = useRef<Promise<boolean> | null>(null);
  const timerRef = useRef<number | undefined>(undefined);
  const saveRef = useRef(save);
  saveRef.current = save;
  const keepaliveRef = useRef(keepalive);
  keepaliveRef.current = keepalive;

  const isDirty = () => revisionRef.current !== savedRevisionRef.current;

  const backup = useCallback(() => {
    if (!isDirty() || discardedRef.current) return true;
    const raw = writeCareerDraft(localKey, valueRef.current, etagRef.current);
    if (raw) {
      localRawRef.current = raw;
      // Transfer this recovered snapshot only after the new backup exists.
      // Repeated failed visits must not leave older recoveries behind.
      if (restored) clearCareerDraft(restored.key, restored.raw);
    }
    return raw !== null;
  }, [localKey, restored]);

  const clearBackup = useCallback(() => {
    clearCareerDraft(localKey, localRawRef.current);
    if (restored) clearCareerDraft(restored.key, restored.raw);
  }, [localKey, restored]);

  const run = useCallback(
    async (autosave: boolean): Promise<boolean> => {
      window.clearTimeout(timerRef.current);
      if (conflictRef.current || discardedRef.current) return false;
      while (inFlightRef.current) {
        if (autosave) return inFlightRef.current;
        if (!(await inFlightRef.current)) return false;
        if (conflictRef.current || discardedRef.current) return false;
      }
      if (!isDirty() && !(uncommittedRef.current && !autosave)) return true;
      const atRevision = revisionRef.current;
      setState('saving');
      const promise = saveRef
        .current(valueRef.current, etagRef.current, autosave)
        .then((nextEtag) => {
          etagRef.current = nextEtag;
          savedRevisionRef.current = atRevision;
          uncommittedRef.current = autosave;
          failedRef.current = false;
          setSavedAt(new Date());
          setError('');
          if (isDirty()) {
            backup();
            setState('dirty');
            if (mountedRef.current) timerRef.current = window.setTimeout(() => void run(true), delayMs);
          } else {
            clearBackup();
            setState('saved');
          }
          return true;
        })
        .catch((err: unknown) => {
          failedRef.current = true;
          backup();
          if (isConflictError(err)) {
            conflictRef.current = true;
            setState('conflict');
          } else {
            setState('error');
            setError(err instanceof Error ? err.message : String(err));
          }
          return false;
        })
        .finally(() => {
          inFlightRef.current = null;
        });
      inFlightRef.current = promise;
      return promise;
    },
    [backup, clearBackup, delayMs],
  );

  const edit = useCallback(
    (update: T | ((previous: T) => T)) => {
      const next = typeof update === 'function' ? (update as (previous: T) => T)(valueRef.current) : update;
      valueRef.current = next;
      setValue(next);
      revisionRef.current += 1;
      backup();
      if (conflictRef.current) return;
      setState('dirty');
      window.clearTimeout(timerRef.current);
      timerRef.current = window.setTimeout(() => void run(true), delayMs);
    },
    [backup, delayMs, run],
  );

  const flush = useCallback(async (): Promise<boolean> => {
    do {
      if (!(await run(false))) return false;
    } while (isDirty() || uncommittedRef.current);
    return true;
  }, [run]);

  const flushOnExit = useCallback(() => {
    window.clearTimeout(timerRef.current);
    backup();
    // A second request would use the ETag from before the in-flight save.
    if (discardedRef.current || conflictRef.current || inFlightRef.current || (!isDirty() && !uncommittedRef.current)) return;
    const request = keepaliveRef.current?.(valueRef.current, etagRef.current);
    if (!request || new TextEncoder().encode(request.body).byteLength > KEEPALIVE_MAX_BYTES) return;
    void fetch(request.url, {
      method: request.method,
      keepalive: true,
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', ...(etagRef.current ? { 'If-Match': etagRef.current } : {}) },
      body: request.body,
    }).catch(() => undefined);
    // Keep the backup until a normal save acknowledges it, or a later mount
    // finds the same content on the server. Dispatch alone is not success.
  }, [backup]);

  useEffect(() => {
    const onBeforeUnload = (event: BeforeUnloadEvent) => {
      if (discardedRef.current) return;
      const backedUp = backup();
      if (isDirty() && (conflictRef.current || failedRef.current || !backedUp)) {
        event.preventDefault();
        event.returnValue = '';
        return;
      }
      flushOnExit();
    };
    window.addEventListener('beforeunload', onBeforeUnload);
    return () => window.removeEventListener('beforeunload', onBeforeUnload);
  }, [backup, flushOnExit]);

  useEffect(() => {
    mountedRef.current = true;
    if (restored && !conflictRef.current) timerRef.current = window.setTimeout(() => void run(true), delayMs);
    return () => {
      mountedRef.current = false;
      window.clearTimeout(timerRef.current);
      backup();
      queueMicrotask(() => {
        if (!mountedRef.current) flushOnExit();
      });
    };
  }, [backup, delayMs, flushOnExit, restored, run]);

  const discard = useCallback(() => {
    discardedRef.current = true;
    window.clearTimeout(timerRef.current);
    clearBackup();
  }, [clearBackup]);

  return { value, edit, state, error, savedAt, flush, discard, recovered: Boolean(restored), etag: () => etagRef.current };
}

export function saveStateLabel(state: SaveState, savedAt: Date | null): string {
  switch (state) {
    case 'dirty':
      return '编辑中';
    case 'saving':
      return '保存中…';
    case 'error':
      return '保存失败';
    case 'conflict':
      return '已在别处修改';
    default:
      return savedAt
        ? `已保存 ${savedAt.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}`
        : '已保存';
  }
}
