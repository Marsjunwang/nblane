// SSE client for the async-job stream (GET /api/v1/profiles/{name}/jobs/{id}/stream).
//
// Thin EventSource wrapper: parses the backend's four frame types
// (job / progress / done / error, see web_api/jobs.py) into typed callbacks
// and returns an unsubscribe function. jsdom has no EventSource — tests stub
// the global (resolved at call time inside streamJob) or drive the handlers
// through a mock source.

import { apiBase } from './client';
import type { JobStreamFrame } from './types';

export interface JobStreamHandlers {
  /** Initial snapshot frame (also the first frame on reconnect). */
  onJob?: (frame: JobStreamFrame) => void;
  /** One frame per logged phase event (routing/merging/...). */
  onProgress?: (frame: JobStreamFrame) => void;
  /** Terminal success frame; carries the kind-specific result payload. */
  onDone?: (frame: JobStreamFrame) => void;
  /**
   * Terminal failure. `frame` is the server's structured error frame when
   * the job itself failed, or `null` when the SSE transport broke (the
   * EventSource 'error' event without data).
   */
  onError?: (frame: JobStreamFrame | null) => void;
}

function parseFrame(event: Event): JobStreamFrame | null {
  if (!(event instanceof MessageEvent) || typeof event.data !== 'string') {
    return null;
  }
  try {
    return JSON.parse(event.data) as JobStreamFrame;
  } catch {
    return null;
  }
}

/**
 * Subscribe to one job's SSE stream; returns the unsubscribe function.
 *
 * The stream is closed automatically on either terminal frame (done/error)
 * and on transport errors (EventSource would otherwise auto-reconnect into
 * a loop for a finished job). The caller must also invoke the returned
 * function on unmount / profile switch.
 */
export function streamJob(
  profile: string,
  jobId: string,
  handlers: JobStreamHandlers,
): () => void {
  const url =
    `${apiBase()}/profiles/${encodeURIComponent(profile)}` +
    `/jobs/${encodeURIComponent(jobId)}/stream`;
  const source = new EventSource(url);

  source.addEventListener('job', (event) => {
    const frame = parseFrame(event);
    if (frame) {
      handlers.onJob?.(frame);
    }
  });
  source.addEventListener('progress', (event) => {
    const frame = parseFrame(event);
    if (frame) {
      handlers.onProgress?.(frame);
    }
  });
  source.addEventListener('done', (event) => {
    const frame = parseFrame(event);
    source.close();
    if (frame) {
      handlers.onDone?.(frame);
    }
  });
  source.addEventListener('error', (event) => {
    const frame = parseFrame(event);
    source.close();
    handlers.onError?.(frame);
  });

  return () => source.close();
}
