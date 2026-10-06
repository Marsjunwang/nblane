// Pure-logic tests for the project edit drawer's field-level save body and
// 3-way rebase (only changed fields are sent; a concurrent edit to an
// untouched field is followed, never overwritten).

import { describe, expect, it } from 'vitest';

import { caseDraftChanges, rebaseCaseDraft } from './ProjectEditDrawer';

type Draft = Parameters<typeof caseDraftChanges>[0];

const BASE: Draft = {
  title: 'Demo',
  status: 'active',
  kind: 'research',
  visibility: 'private',
  time_range: '',
  summary: '旧摘要',
  notes: '',
  goal_refs: ['g1'],
  task_refs: [],
  evidence_refs: [],
  source_refs: [],
  experience_refs: [],
  output_refs: [],
};

describe('caseDraftChanges', () => {
  it('returns only the fields that differ from the baseline', () => {
    expect(caseDraftChanges(BASE, { ...BASE, title: '新标题', goal_refs: ['g1', 'g2'] })).toEqual({
      title: '新标题',
      goal_refs: ['g1', 'g2'],
    });
  });

  it('is empty for an untouched draft, and compares arrays by value', () => {
    expect(caseDraftChanges(BASE, { ...BASE, goal_refs: ['g1'] })).toEqual({});
  });
});

describe('rebaseCaseDraft', () => {
  it('follows the server on untouched fields and keeps user edits', () => {
    const draft = { ...BASE, title: '我的标题' };
    const server = { ...BASE, summary: '对方改的摘要' };
    const { draft: next, conflicts } = rebaseCaseDraft(BASE, draft, server);
    expect(next.title).toBe('我的标题');
    expect(next.summary).toBe('对方改的摘要');
    expect(conflicts).toEqual([]);
    // The follow-up save then carries only the user's field.
    expect(caseDraftChanges(server, next)).toEqual({ title: '我的标题' });
  });

  it('names a field both sides changed differently as a conflict', () => {
    const { conflicts } = rebaseCaseDraft(
      BASE,
      { ...BASE, summary: '我的摘要' },
      { ...BASE, summary: '对方摘要' },
    );
    expect(conflicts).toEqual(['summary']);
  });

  it('does not flag both sides converging on the same value', () => {
    const { conflicts } = rebaseCaseDraft(
      BASE,
      { ...BASE, status: 'paused' },
      { ...BASE, status: 'paused' },
    );
    expect(conflicts).toEqual([]);
  });
});
