import { useEffect, useRef } from "react";

function cleanText(value) {
  return value === null || value === undefined ? "" : String(value);
}

function asObject(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : {};
}

export function normalizeAIStream(value) {
  const stream = asObject(value);
  const taskId = cleanText(stream.task_id || stream.stream_id || stream.id).trim();
  if (!taskId) {
    return null;
  }
  return {
    task_id: taskId,
    operation: cleanText(stream.operation || "AI"),
    status: cleanText(stream.status || "running"),
    text: cleanText(stream.text),
    error: cleanText(stream.error),
    patch: asObject(stream.patch),
    started_at: Number(stream.started_at || 0),
    updated_at: Number(stream.updated_at || 0),
  };
}

export function useAIStream({
  stream,
  poll,
  onFlush,
  onComplete,
  intervalMs = 120,
  pollIntervalMs = 800,
}) {
  const latestStreamRef = useRef(null);
  const flushTimerRef = useRef(null);
  const completedRef = useRef(new Set());

  useEffect(() => {
    latestStreamRef.current = stream;
    if (!stream) {
      return undefined;
    }
    if (flushTimerRef.current !== null) {
      return undefined;
    }
    flushTimerRef.current = window.setTimeout(() => {
      flushTimerRef.current = null;
      const latest = latestStreamRef.current;
      if (latest) {
        onFlush?.(latest);
      }
    }, intervalMs);
    return undefined;
  }, [intervalMs, onFlush, stream]);

  useEffect(() => {
    if (!stream || stream.status !== "running") {
      return undefined;
    }
    const timer = window.setInterval(() => {
      poll?.(stream.task_id);
    }, pollIntervalMs);
    return () => window.clearInterval(timer);
  }, [poll, pollIntervalMs, stream?.status, stream?.task_id]);

  useEffect(() => {
    if (!stream || stream.status === "running") {
      return;
    }
    const doneKey = `${stream.task_id}:${stream.status}:${stream.updated_at}`;
    if (completedRef.current.has(doneKey)) {
      return;
    }
    completedRef.current.add(doneKey);
    if (flushTimerRef.current !== null) {
      window.clearTimeout(flushTimerRef.current);
      flushTimerRef.current = null;
    }
    onFlush?.(stream);
    onComplete?.(stream);
  }, [onComplete, onFlush, stream]);

  useEffect(() => {
    return () => {
      if (flushTimerRef.current !== null) {
        window.clearTimeout(flushTimerRef.current);
      }
    };
  }, []);
}
