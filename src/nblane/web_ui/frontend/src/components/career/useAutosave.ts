// Debounced, conflict-safe autosave for one document (resume or draft).
//
// Same contract as the blog editor: edits schedule a save after idle,
// autosaves skip the server's Git backup commit, an explicit flush (⌘S,
// leaving the page) commits, a 412 freezes saving until the user reloads,
// and a keepalive request covers tab close / in-app navigation.

import { useCallback, useEffect, useRef, useState } from 'react';

import { isConflictError } from '../ConflictAlert';

export type SaveState = 'saved' | 'dirty' | 'saving' | 'error' | 'conflict';

const DEFAULT_DELAY_MS = 1500;
/** keepalive fetch bodies are capped at 64 KiB by browsers. */
const KEEPALIVE_MAX_BYTES = 60_000;

export interface AutosaveOptions<T> {
  initial: T;
  etag: string;
  save: (value: T, etag: string, autosave: boolean) => Promise<string>;
  /** Request used for the last-chance save on unload/unmount. */
  keepalive?: (value: T, etag: string) => { url: string; method: string; body: string } | null;
  delayMs?: number;
}

export function useAutosave<T>({ initial, etag, save, keepalive, delayMs = DEFAULT_DELAY_MS }: AutosaveOptions<T>) {
  const [value, setValue] = useState<T>(initial);
  const [state, setState] = useState<SaveState>('saved');
  const [error, setError] = useState('');
  const [savedAt, setSavedAt] = useState<Date | null>(null);

  const valueRef = useRef<T>(initial);
  const etagRef = useRef(etag);
  const revisionRef = useRef(0);
  const savedRevisionRef = useRef(0);
  const uncommittedRef = useRef(false);
  const conflictRef = useRef(false);
  const inFlightRef = useRef<Promise<boolean> | null>(null);
  const timerRef = useRef<number | undefined>(undefined);
  const saveRef = useRef(save);
  saveRef.current = save;
  const keepaliveRef = useRef(keepalive);
  keepaliveRef.current = keepalive;

  const isDirty = () => revisionRef.current !== savedRevisionRef.current;

  const run = useCallback(
    async (autosave: boolean): Promise<boolean> => {
      window.clearTimeout(timerRef.current);
      if (conflictRef.current) return false;
      if (inFlightRef.current) {
        if (autosave) return inFlightRef.current;
        await inFlightRef.current;
        if (conflictRef.current) return false;
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
          setSavedAt(new Date());
          setError('');
          if (isDirty()) {
            setState('dirty');
            timerRef.current = window.setTimeout(() => void run(true), delayMs);
          } else {
            setState('saved');
          }
          return true;
        })
        .catch((err: unknown) => {
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
    [delayMs],
  );

  const edit = useCallback(
    (update: T | ((previous: T) => T)) => {
      const next = typeof update === 'function' ? (update as (previous: T) => T)(valueRef.current) : update;
      valueRef.current = next;
      setValue(next);
      revisionRef.current += 1;
      if (conflictRef.current) return;
      setState('dirty');
      window.clearTimeout(timerRef.current);
      timerRef.current = window.setTimeout(() => void run(true), delayMs);
    },
    [delayMs, run],
  );

  const flush = useCallback(() => run(false), [run]);

  const flushOnExit = useCallback(() => {
    window.clearTimeout(timerRef.current);
    if (conflictRef.current || (!isDirty() && !uncommittedRef.current)) return;
    const request = keepaliveRef.current?.(valueRef.current, etagRef.current);
    if (!request || request.body.length > KEEPALIVE_MAX_BYTES) return;
    void fetch(request.url, {
      method: request.method,
      keepalive: true,
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', ...(etagRef.current ? { 'If-Match': etagRef.current } : {}) },
      body: request.body,
    }).catch(() => undefined);
    savedRevisionRef.current = revisionRef.current;
    uncommittedRef.current = false;
  }, []);

  useEffect(() => {
    const onBeforeUnload = (event: BeforeUnloadEvent) => {
      if (conflictRef.current) {
        event.preventDefault();
        return;
      }
      flushOnExit();
    };
    window.addEventListener('beforeunload', onBeforeUnload);
    return () => window.removeEventListener('beforeunload', onBeforeUnload);
  }, [flushOnExit]);

  useEffect(() => () => flushOnExit(), [flushOnExit]);

  return { value, edit, state, error, savedAt, flush, etag: () => etagRef.current };
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
