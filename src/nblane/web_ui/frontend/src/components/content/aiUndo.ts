// Undo for AI-filled post fields (title / summary / tags / cover).
//
// The patch is applied immediately; a notification offers 撤销 for a while.
// Undo restores only the fields that still hold the AI value, so a hand edit
// made after accepting the suggestion is never overwritten.

import type { PostDraft } from './contentDraft';

export type AIField = 'title' | 'summary' | 'tags' | 'cover';
export type AIPatch = Partial<Pick<PostDraft, AIField>>;

const FIELD_LABEL: Record<AIField, string> = { title: '标题', summary: '摘要', tags: '标签', cover: '封面' };

function same(a: unknown, b: unknown): boolean {
  return JSON.stringify(a) === JSON.stringify(b);
}

/** Values to restore: the old value for every field still equal to the AI one. */
export function undoPatch(previous: AIPatch, applied: AIPatch, current: PostDraft): AIPatch {
  const restore: AIPatch = {};
  for (const key of Object.keys(applied) as AIField[]) {
    if (same(current[key], applied[key])) {
      (restore as Record<string, unknown>)[key] = previous[key];
    }
  }
  return restore;
}

/** Snapshot of the fields a patch will change, taken before applying it. */
export function previousOf(patch: AIPatch, draft: PostDraft): AIPatch {
  const before: AIPatch = {};
  for (const key of Object.keys(patch) as AIField[]) {
    (before as Record<string, unknown>)[key] = draft[key];
  }
  return before;
}

/** Changed fields only: skip a patch value equal to what is already there. */
export function changedFields(patch: AIPatch, draft: PostDraft): AIField[] {
  return (Object.keys(patch) as AIField[]).filter((key) => !same(draft[key], patch[key]));
}

export function fieldsLabel(fields: AIField[]): string {
  return fields.map((field) => FIELD_LABEL[field]).join('、');
}
