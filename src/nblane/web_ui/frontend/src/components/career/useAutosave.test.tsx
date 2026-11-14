import { act, cleanup, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiError } from '../../api/client';
import { useAutosave } from './useAutosave';

const initial = { text: 'server' };
const keepalive = (value: typeof initial) => ({ url: '/resume', method: 'PUT', body: JSON.stringify(value) });

function options(save = vi.fn().mockResolvedValue('e2')) {
  return { storageKey: 'alice/resume', initial, etag: 'e1', save, keepalive };
}

beforeEach(() => {
  vi.useFakeTimers();
  window.localStorage.clear();
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}', { status: 500 })));
});

afterEach(async () => {
  cleanup();
  await Promise.resolve();
  vi.useRealTimers();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  window.localStorage.clear();
});

describe('career autosave recovery', () => {
  it('returns false on a conflict and keeps the draft through navigation', async () => {
    const save = vi.fn().mockRejectedValue(new ApiError(412, 'changed'));
    const editor = renderHook(() => useAutosave(options(save)));
    act(() => editor.result.current.edit({ text: 'my changes' }));
    await act(async () => expect(await editor.result.current.flush()).toBe(false));
    expect(editor.result.current.state).toBe('conflict');
    editor.unmount();
    await Promise.resolve();
    expect(fetch).not.toHaveBeenCalled();

    const reopened = renderHook(() => useAutosave({ ...options(), etag: 'other-edit' }));
    expect(reopened.result.current.value.text).toBe('my changes');
    expect(reopened.result.current.state).toBe('conflict');
    await act(async () => expect(await reopened.result.current.flush()).toBe(false));
  });

  it('does not treat a failed keepalive as saved and restores on the next visit', async () => {
    const editor = renderHook(() => useAutosave(options()));
    act(() => editor.result.current.edit({ text: 'offline edit' }));
    editor.unmount();
    await Promise.resolve();
    expect(fetch).toHaveBeenCalledOnce();
    expect(window.localStorage.length).toBe(1);

    const save = vi.fn().mockResolvedValue('e2');
    const reopened = renderHook(() => useAutosave(options(save)));
    expect(reopened.result.current.value.text).toBe('offline edit');
    await act(async () => expect(await reopened.result.current.flush()).toBe(true));
    expect(save).toHaveBeenCalledWith({ text: 'offline edit' }, 'e1', false);
    expect(window.localStorage.length).toBe(0);
  });

  it('keeps two open editors backups independent when one saves', async () => {
    const first = renderHook(() => useAutosave(options()));
    const second = renderHook(() => useAutosave(options()));
    act(() => {
      first.result.current.edit({ text: 'first tab' });
      second.result.current.edit({ text: 'second tab' });
    });
    expect(window.localStorage.length).toBe(2);
    await act(async () => expect(await first.result.current.flush()).toBe(true));
    expect(window.localStorage.length).toBe(1);
    expect(JSON.parse(window.localStorage.getItem(window.localStorage.key(0)!)!).value.text).toBe('second tab');
  });

  it('does not accumulate stale drafts over repeated failed visits', async () => {
    for (const text of ['first', 'second', 'third']) {
      const editor = renderHook(() => useAutosave(options()));
      act(() => editor.result.current.edit({ text }));
      editor.unmount();
      await Promise.resolve();
      expect(window.localStorage.length).toBe(1);
    }
    const reopened = renderHook(() => useAutosave(options()));
    expect(reopened.result.current.value.text).toBe('third');
    await act(async () => expect(await reopened.result.current.flush()).toBe(true));
    expect(window.localStorage.length).toBe(0);
  });

  it('does not clear a newer version of the backup it originally recovered', async () => {
    const first = renderHook(() => useAutosave(options()));
    act(() => first.result.current.edit({ text: 'recovered snapshot' }));
    const second = renderHook(() => useAutosave(options()));
    act(() => first.result.current.edit({ text: 'newer in first tab' }));
    await act(async () => expect(await second.result.current.flush()).toBe(true));
    expect(window.localStorage.length).toBe(1);
    expect(JSON.parse(window.localStorage.getItem(window.localStorage.key(0)!)!).value.text).toBe('newer in first tab');
  });

  it('waits for edits made during an explicit flush before allowing navigation or export', async () => {
    let finish!: (etag: string) => void;
    const save = vi.fn()
      .mockImplementationOnce(() => new Promise<string>((resolve) => { finish = resolve; }))
      .mockResolvedValue('e3');
    const editor = renderHook(() => useAutosave(options(save)));
    act(() => editor.result.current.edit({ text: 'first' }));
    let flushing!: Promise<boolean>;
    act(() => { flushing = editor.result.current.flush(); });
    act(() => editor.result.current.edit({ text: 'latest' }));
    await act(async () => {
      finish('e2');
      expect(await flushing).toBe(true);
    });
    expect(save).toHaveBeenLastCalledWith({ text: 'latest' }, 'e2', false);
    expect(editor.result.current.state).toBe('saved');
    expect(window.localStorage.length).toBe(0);
  });

  it('retains edits made during an autosave and does not race it with an exit save', async () => {
    let finish!: (etag: string) => void;
    const save = vi.fn(() => new Promise<string>((resolve) => { finish = resolve; }));
    const editor = renderHook(() => useAutosave(options(save)));
    act(() => editor.result.current.edit({ text: 'first' }));
    act(() => vi.advanceTimersByTime(1500));
    act(() => editor.result.current.edit({ text: 'newer' }));
    editor.unmount();
    await Promise.resolve();
    expect(fetch).not.toHaveBeenCalled();
    await act(async () => finish('e2'));
    const reopened = renderHook(() => useAutosave({ ...options(), initial: { text: 'first' }, etag: 'e2' }));
    expect(reopened.result.current.value.text).toBe('newer');
    expect(reopened.result.current.state).toBe('dirty');
  });

  it('counts UTF-8 bytes for keepalive limits while preserving the full draft', async () => {
    const editor = renderHook(() => useAutosave(options()));
    act(() => editor.result.current.edit({ text: '中'.repeat(30_000) }));
    editor.unmount();
    await Promise.resolve();
    expect(fetch).not.toHaveBeenCalled();
    const reopened = renderHook(() => useAutosave(options()));
    expect(reopened.result.current.value.text).toHaveLength(30_000);
  });

  it('cleans an exit backup already present on the server instead of restoring it later', async () => {
    const editor = renderHook(() => useAutosave(options()));
    act(() => editor.result.current.edit({ text: 'reached server' }));
    editor.unmount();
    const reopened = renderHook(() => useAutosave({ ...options(), initial: { text: 'reached server' }, etag: 'e2' }));
    expect(reopened.result.current.recovered).toBe(false);
    expect(window.localStorage.length).toBe(0);
  });

  it('guards browser exit when saving failed and local storage is unavailable', async () => {
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('quota'); });
    const editor = renderHook(() => useAutosave(options(vi.fn().mockRejectedValue(new Error('offline')))));
    act(() => editor.result.current.edit({ text: 'keep me' }));
    await act(async () => expect(await editor.result.current.flush()).toBe(false));
    const event = new Event('beforeunload', { cancelable: true });
    window.dispatchEvent(event);
    expect(event.defaultPrevented).toBe(true);
  });
});
