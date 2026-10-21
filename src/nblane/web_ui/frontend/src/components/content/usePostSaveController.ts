import { notifications } from '@mantine/notifications';
import { useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useRef, useState } from 'react';

import { ApiError, ifMatch } from '../../api/client';
import { SESSION_RESTORED_EVENT, isSessionExpired } from '../../api/session';
import { contentBlogApiUrl, fetchContentPost, useSaveContentPost } from '../../api/hooks';
import { isConflictError } from '../ConflictAlert';
import {
  clearLocalDraft,
  draftFromPost,
  draftToSaveRequest,
  erasesBody,
  errorText,
  readLocalDraft,
  sameDraftContent,
  writeLocalDraft,
  type LocalDraft,
  type PostDraft,
} from './contentDraft';

export type SaveState = 'saved' | 'dirty' | 'saving' | 'error' | 'conflict' | 'empty';

/** Idle time after the last keystroke before the draft is written. */
export const AUTOSAVE_DELAY_MS = 1500;
/** Idle time before the draft is mirrored into localStorage. */
const LOCAL_DRAFT_DELAY_MS = 500;
/** keepalive fetch bodies are capped at 64 KiB by browsers. */
const KEEPALIVE_MAX_BYTES = 60_000;

/**
 * The content editor's save state machine: draft state + mirror refs,
 * debounced autosave, the localStorage draft, the keepalive flush on exit,
 * and conflict / empty-body / lost-response recovery. UI resets after a
 * (re)load go through ``onApplyPost``; navigation stays with the caller.
 */
export function usePostSaveController({
  profile,
  slug,
  onApplyPost,
}: {
  profile: string;
  slug: string;
  /** UI reset after (re)loading a draft: remount the editor, refresh mode/outline. */
  onApplyPost: (draft: PostDraft, options: { resetOutline: boolean }) => void;
}) {
  const queryClient = useQueryClient();
  const save = useSaveContentPost(profile);

  const [draft, setDraft] = useState<PostDraft | null>(null);
  const [saveState, setSaveState] = useState<SaveState>('saved');
  const [savedAt, setSavedAt] = useState<Date | null>(null);
  const [saveError, setSaveError] = useState('');
  const [localCandidate, setLocalCandidate] = useState<LocalDraft | null>(null);
  const [revision, setRevision] = useState(0);
  const [previewNonce, setPreviewNonce] = useState(0);

  // Refs mirror the latest state for timers, unload handlers and async saves.
  const draftRef = useRef<PostDraft | null>(null);
  const etagRef = useRef('');
  const revisionRef = useRef(0);
  const savedRevisionRef = useRef(0);
  const uncommittedRef = useRef(false);
  const conflictRef = useRef(false);
  const inFlightRef = useRef<Promise<boolean> | null>(null);
  const timerRef = useRef<number | undefined>(undefined);
  const loadedSlugRef = useRef('');
  // Body the server holds now: an edit that would erase it waits for consent.
  const serverBodyRef = useRef('');
  const emptyPendingRef = useRef(false);
  const localTimerRef = useRef<number | undefined>(undefined);
  // Draft of a save whose response never arrived: it may have landed.
  const unknownSaveRef = useRef<PostDraft | null>(null);
  const deletingRef = useRef(false);

  const isDirty = () => revisionRef.current !== savedRevisionRef.current;

  const applyServerPost = useCallback(
    (result: { post: Parameters<typeof draftFromPost>[0]; etag: string }) => {
      loadedSlugRef.current = slug;
      const next = draftFromPost(result.post);
      draftRef.current = next;
      etagRef.current = result.etag;
      serverBodyRef.current = next.body;
      emptyPendingRef.current = false;
      unknownSaveRef.current = null;
      setDraft(next);
      const local = readLocalDraft(window.localStorage, profile, slug);
      if (local && !sameDraftContent(local.draft, next)) setLocalCandidate(local);
      else {
        if (local) clearLocalDraft(window.localStorage, profile, slug);
        setLocalCandidate(null);
      }
      onApplyPost(next, { resetOutline: true });
    },
    [profile, slug, onApplyPost],
  );

  const markSaved = (atRevision: number, autosave: boolean, etag: string, body: string) => {
    etagRef.current = etag;
    serverBodyRef.current = body;
    savedRevisionRef.current = atRevision;
    uncommittedRef.current = autosave;
    setSavedAt(new Date());
    setSaveError('');
    setPreviewNonce((value) => value + 1);
    if (!isDirty()) clearLocalDraft(window.localStorage, profile, slug);
  };

  const runSave = useCallback(
    async (autosave: boolean, options: { allowEmpty?: boolean } = {}): Promise<boolean> => {
      window.clearTimeout(timerRef.current);
      if (deletingRef.current || conflictRef.current || !draftRef.current) return false;
      // Saves run one at a time. Autosaves coalesce into the running one (it
      // reschedules itself when edits are pending); explicit saves wait in
      // turn, so a burst of Ctrl+S never sends parallel PUTs with one ETag.
      while (inFlightRef.current) {
        if (autosave) return inFlightRef.current;
        await inFlightRef.current;
        if (deletingRef.current || conflictRef.current) return false;
      }
      if (!isDirty() && !(uncommittedRef.current && !autosave)) return true;
      if (isSessionExpired()) {
        setSaveState('error');
        setSaveError('登录已过期，重新登录后会自动保存。');
        return false;
      }
      const current = draftRef.current!;
      if (!options.allowEmpty && erasesBody(current, serverBodyRef.current)) {
        emptyPendingRef.current = true;
        setSaveState('empty');
        return false;
      }
      emptyPendingRef.current = false;
      const atRevision = revisionRef.current;
      setSaveState('saving');
      const promise = save
        .mutateAsync({
          slug,
          body: draftToSaveRequest(current),
          etag: etagRef.current,
          autosave,
          allowEmpty: options.allowEmpty,
        })
        .then(
          (result) => {
            unknownSaveRef.current = null;
            // Autosave responses omit the post echo: the server then holds
            // exactly the body this save sent.
            markSaved(atRevision, autosave, result.etag, result.post ? draftFromPost(result.post).body : current.body);
            if (result.post) {
              queryClient.setQueryData(['profiles', profile, 'content', 'post', slug], { post: result.post, etag: result.etag });
            }
            return true;
          },
          async (error: unknown) => {
            if (isConflictError(error)) {
              // The response to an earlier save may have been lost (dropped
              // connection): if the server already holds exactly this draft,
              // adopt its ETag and carry on instead of reporting a conflict.
              try {
                const server = await fetchContentPost(profile, slug);
                const onServer = draftFromPost(server.post);
                if (sameDraftContent(onServer, current)) {
                  markSaved(atRevision, autosave, server.etag, onServer.body);
                  queryClient.setQueryData(['profiles', profile, 'content', 'post', slug], server);
                  return true;
                }
                const lost = unknownSaveRef.current;
                if (lost && sameDraftContent(onServer, lost)) {
                  // Our earlier save did land; newer edits are still pending.
                  // Rebase on its ETag and save again (marked dirty, so the
                  // follow-up below reschedules the autosave).
                  unknownSaveRef.current = null;
                  etagRef.current = server.etag;
                  serverBodyRef.current = onServer.body;
                  queryClient.setQueryData(['profiles', profile, 'content', 'post', slug], server);
                  return true;
                }
              } catch {
                // fall through to the conflict state
              }
              conflictRef.current = true;
              setSaveState('conflict');
              return false;
            }
            if (error instanceof ApiError && error.code === 'empty_body_requires_confirm') {
              emptyPendingRef.current = true;
              setSaveState('empty');
              return false;
            }
            if (!(error instanceof ApiError)) unknownSaveRef.current = current;
            setSaveState('error');
            setSaveError(
              error instanceof ApiError && error.status === 401 ? '登录已过期，重新登录后会自动保存。' : errorText(error),
            );
            return false;
          },
        )
        .then((ok) => {
          if (ok) {
            if (isDirty()) {
              setSaveState('dirty');
              timerRef.current = window.setTimeout(() => void runSave(true), AUTOSAVE_DELAY_MS);
            } else {
              setSaveState('saved');
            }
          }
          return ok;
        })
        .finally(() => {
          inFlightRef.current = null;
        });
      inFlightRef.current = promise;
      return promise;
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [profile, queryClient, slug],
  );

  // After re-login in the session modal, push what piled up meanwhile.
  useEffect(() => {
    const onRestored = () => {
      if (isDirty() || uncommittedRef.current) void runSave(false);
    };
    window.addEventListener(SESSION_RESTORED_EVENT, onRestored);
    return () => window.removeEventListener(SESSION_RESTORED_EVENT, onRestored);
  }, [runSave]);

  const edit = useCallback(
    (patch: Partial<PostDraft>) => {
      if (deletingRef.current || !draftRef.current) return;
      draftRef.current = { ...draftRef.current, ...patch };
      setDraft(draftRef.current);
      revisionRef.current += 1;
      setRevision(revisionRef.current);
      window.clearTimeout(localTimerRef.current);
      localTimerRef.current = window.setTimeout(() => {
        if (draftRef.current && isDirty()) {
          writeLocalDraft(window.localStorage, profile, slug, draftRef.current, etagRef.current);
        }
      }, LOCAL_DRAFT_DELAY_MS);
      if (emptyPendingRef.current && draftRef.current.body.trim()) emptyPendingRef.current = false;
      if (conflictRef.current) return;
      setSaveState('dirty');
      window.clearTimeout(timerRef.current);
      timerRef.current = window.setTimeout(() => void runSave(true), AUTOSAVE_DELAY_MS);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [profile, runSave, slug],
  );

  // Last-chance save when the tab closes or the user navigates elsewhere in
  // the app (rail links). keepalive lets the request outlive the page.
  const flushOnExit = useCallback(() => {
    window.clearTimeout(timerRef.current);
    window.clearTimeout(localTimerRef.current);
    if (deletingRef.current) return;
    const current = draftRef.current;
    if (!current || (!isDirty() && !uncommittedRef.current)) return;
    if (isDirty()) writeLocalDraft(window.localStorage, profile, slug, current, etagRef.current);
    if (conflictRef.current || isSessionExpired() || erasesBody(current, serverBodyRef.current)) return;
    let body = draftToSaveRequest(current);
    let payload = JSON.stringify(body);
    if (payload.length > KEEPALIVE_MAX_BYTES) {
      // Drop the blocks sidecar; it is rebuilt from the Markdown on next open.
      body = { ...body, blocks_json: [] };
      payload = JSON.stringify(body);
    }
    if (payload.length > KEEPALIVE_MAX_BYTES) return;
    void fetch(contentBlogApiUrl(profile, slug), {
      method: 'PUT',
      keepalive: true,
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', ...ifMatch(etagRef.current) },
      body: payload,
    }).catch(() => undefined);
    savedRevisionRef.current = revisionRef.current;
    uncommittedRef.current = false;
  }, [profile, slug]);

  useEffect(() => {
    const onBeforeUnload = (event: BeforeUnloadEvent) => {
      if (conflictRef.current || (saveState === 'error' && isDirty())) {
        event.preventDefault();
        return;
      }
      flushOnExit();
    };
    window.addEventListener('beforeunload', onBeforeUnload);
    return () => window.removeEventListener('beforeunload', onBeforeUnload);
  }, [flushOnExit, saveState]);

  useEffect(() => () => flushOnExit(), [flushOnExit]);

  const reloadFromServer = async () => {
    window.clearTimeout(timerRef.current);
    window.clearTimeout(localTimerRef.current);
    let result;
    try {
      result = await fetchContentPost(profile, slug);
    } catch (error) {
      notifications.show({ color: 'red', title: '加载最新版本失败', message: errorText(error) });
      return;
    }
    conflictRef.current = false;
    clearLocalDraft(window.localStorage, profile, slug);
    revisionRef.current = 0;
    savedRevisionRef.current = 0;
    setRevision(0);
    uncommittedRef.current = false;
    queryClient.setQueryData(['profiles', profile, 'content', 'post', slug], result);
    applyServerPost(result);
    setSaveState('saved');
  };

  // Conflict: keep this editor's text and overwrite the server copy.
  const keepMine = async () => {
    try {
      const server = await fetchContentPost(profile, slug);
      etagRef.current = server.etag;
      serverBodyRef.current = draftFromPost(server.post).body;
    } catch (error) {
      notifications.show({ color: 'red', title: '无法读取最新版本', message: errorText(error) });
      return;
    }
    conflictRef.current = false;
    savedRevisionRef.current = -1;
    await runSave(false);
  };

  const restoreLocalDraft = () => {
    if (!localCandidate) return;
    draftRef.current = localCandidate.draft;
    setDraft(localCandidate.draft);
    onApplyPost(localCandidate.draft, { resetOutline: false });
    revisionRef.current += 1;
    setRevision(revisionRef.current);
    setLocalCandidate(null);
    setSaveState('dirty');
    window.clearTimeout(timerRef.current);
    timerRef.current = window.setTimeout(() => void runSave(true), AUTOSAVE_DELAY_MS);
  };

  const discardLocalDraft = () => {
    clearLocalDraft(window.localStorage, profile, slug);
    setLocalCandidate(null);
  };

  return {
    draft,
    setDraft,
    saveState,
    setSaveState,
    savedAt,
    setSavedAt,
    saveError,
    localCandidate,
    revision,
    previewNonce,
    setPreviewNonce,
    draftRef,
    etagRef,
    revisionRef,
    savedRevisionRef,
    uncommittedRef,
    conflictRef,
    inFlightRef,
    timerRef,
    localTimerRef,
    loadedSlugRef,
    serverBodyRef,
    deletingRef,
    isDirty,
    applyServerPost,
    runSave,
    edit,
    reloadFromServer,
    keepMine,
    restoreLocalDraft,
    discardLocalDraft,
  };
}
