import { describe, expect, it } from 'vitest';

import type { PostDraft } from './contentDraft';
import { changedFields, fieldsLabel, previousOf, undoPatch } from './aiUndo';

const draft = (patch: Partial<PostDraft> = {}): PostDraft => ({
  title: '原标题', date: '2026-10-20', status: 'draft', summary: '原摘要', cover: 'media/blog/x/a.png',
  tags: ['a'], body: '正文', blocksJson: [], ...patch,
});

describe('aiUndo', () => {
  it('restores the previous value of a field still holding the AI value', () => {
    const before = draft();
    const patch = { summary: 'AI 摘要' };
    const previous = previousOf(patch, before);
    expect(undoPatch(previous, patch, draft({ summary: 'AI 摘要' }))).toEqual({ summary: '原摘要' });
  });

  it('leaves a field alone once the writer edited it after accepting', () => {
    const patch = { summary: 'AI 摘要' };
    const previous = previousOf(patch, draft());
    expect(undoPatch(previous, patch, draft({ summary: 'AI 摘要，又手改了' }))).toEqual({});
  });

  it('handles list fields and covers', () => {
    const patch = { tags: ['a', 'VLA'], cover: 'media/blog/x/ai.png' };
    const previous = previousOf(patch, draft());
    const now = draft({ tags: ['a', 'VLA'], cover: 'media/blog/x/ai.png' });
    expect(undoPatch(previous, patch, now)).toEqual({ tags: ['a'], cover: 'media/blog/x/a.png' });
  });

  it('skips no-op patches and names fields in Chinese', () => {
    expect(changedFields({ title: '原标题' }, draft())).toEqual([]);
    expect(fieldsLabel(changedFields({ title: '新', summary: '新' }, draft()))).toBe('标题、摘要');
  });
});
