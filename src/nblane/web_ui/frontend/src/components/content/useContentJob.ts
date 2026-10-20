// One AI job slot for a panel: running / progress / error, cancel on
// unmount, and stale-result guarding, so each panel does not re-implement
// them (and drift apart, as they had).

import { useCallback, useEffect, useRef, useState } from 'react';

import type { ContentJobHandle } from './contentJobs';

export type JobOutcome<T> =
  | { status: 'done'; value: T }
  | { status: 'error'; error: string }
  /** Superseded by a newer start, cancelled, or the panel unmounted. */
  | { status: 'stale' };

function errorText(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

/**
 * Combine several handles into one: cancel stops all of them, and the first
 * failure cancels the rest so nothing keeps running (and billing) for a
 * result that will be thrown away.
 */
export function combineJobs<T>(handles: ContentJobHandle<T>[]): ContentJobHandle<T[]> {
  const cancel = () => handles.forEach((handle) => handle.cancel());
  const result = Promise.all(handles.map((handle) => handle.result)).catch((error: unknown) => {
    cancel();
    throw error;
  });
  return { result, cancel };
}

export function useContentJob<T>() {
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState('');
  const [error, setError] = useState('');
  const current = useRef<ContentJobHandle<T> | null>(null);

  useEffect(
    () => () => {
      current.current?.cancel();
      current.current = null;
    },
    [],
  );

  const cancel = useCallback(() => {
    current.current?.cancel();
    current.current = null;
    setRunning(false);
    setProgress('');
  }, []);

  /**
   * Start a job, cancelling any previous one. *launch* gets a progress
   * callback; only the latest job may update state or resolve as done/error.
   */
  const start = useCallback(
    async (launch: (onProgress: (message: string) => void) => ContentJobHandle<T>): Promise<JobOutcome<T>> => {
      current.current?.cancel();
      setRunning(true);
      setError('');
      setProgress('');
      let handle: ContentJobHandle<T> | null = null;
      const isCurrent = () => handle !== null && current.current === handle;
      handle = launch((message) => {
        if (isCurrent()) setProgress(message);
      });
      current.current = handle;
      try {
        const value = await handle.result;
        if (!isCurrent()) return { status: 'stale' };
        return { status: 'done', value };
      } catch (err: unknown) {
        if (!isCurrent()) return { status: 'stale' };
        const message = errorText(err);
        setError(message);
        return { status: 'error', error: message };
      } finally {
        if (isCurrent()) {
          current.current = null;
          setRunning(false);
          setProgress('');
        }
      }
    },
    [],
  );

  return { running, progress, error, setError, start, cancel };
}
