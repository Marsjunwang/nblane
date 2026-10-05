// Pure helpers for the content workspace (library + editor). Kept free of
// React so they are unit-testable.

import type { StudioPostDetail, StudioPostSaveRequest } from '../../api/types';

export type EditorBlocks = Array<Record<string, unknown>>;

export const STATUS_LABELS: Record<string, string> = {
  draft: '草稿',
  published: '已发布',
  archived: '已归档',
};

export const STATUS_COLORS: Record<string, string> = {
  draft: 'yellow',
  published: 'green',
  archived: 'gray',
};

export interface PostDraft {
  title: string;
  date: string;
  status: string;
  summary: string;
  cover: string;
  tags: string[];
  body: string;
  blocksJson: EditorBlocks;
}

/** Library / editor URL for one post (slugs may contain "/"). */
export function contentEditorPath(profile: string, slug: string): string {
  const encoded = slug.split('/').map(encodeURIComponent).join('/');
  return `/p/${encodeURIComponent(profile)}/content/${encoded}`;
}

export function contentLibraryPath(profile: string): string {
  return `/p/${encodeURIComponent(profile)}/content`;
}

function normalizeTitle(text: string): string {
  return text.replace(/\s+/g, ' ').trim().toLowerCase();
}

/**
 * Drop a leading `# <title>` that merely repeats the post title.
 *
 * The title is edited on the canvas and rendered by the public template, so
 * a body H1 with the same text shows the title twice (editor and site).
 * Returns the body unchanged when the first heading differs.
 */
export function stripDuplicateTitle(body: string, title: string): { body: string; stripped: boolean } {
  const wanted = normalizeTitle(title);
  if (!wanted) return { body, stripped: false };
  const match = /^\s*#[ \t]+([^\n]+)\n?/.exec(body);
  if (!match || normalizeTitle(match[1]) !== wanted) return { body, stripped: false };
  return { body: body.slice(match[0].length).replace(/^\s*\n/, ''), stripped: true };
}

export function draftFromPost(post: StudioPostDetail): PostDraft {
  const title = post.title ?? '';
  const { body, stripped } = stripDuplicateTitle(post.body ?? '', title);
  return {
    title,
    date: post.date ?? '',
    status: post.status ?? 'draft',
    summary: post.summary ?? '',
    cover: post.cover ?? '',
    tags: post.tags ?? [],
    body,
    // The sidecar still holds the duplicate heading block: reparse from the
    // cleaned Markdown instead (custom blocks round-trip through Markdown).
    blocksJson: stripped ? [] : ((post.blocks_json ?? []) as EditorBlocks),
  };
}

export function draftToSaveRequest(draft: PostDraft): StudioPostSaveRequest {
  return {
    title: draft.title,
    date: draft.date,
    status: draft.status,
    summary: draft.summary,
    cover: draft.cover,
    tags: draft.tags,
    body: draft.body,
    // Source-mode edits clear the blocks: the server must not keep a sidecar
    // that no longer matches the Markdown it is saving.
    blocks_json: draft.blocksJson,
  };
}

/** Markdown snippet for one media file; alt text defaults to the file name. */
export function mediaSnippet(kind: string, path: string, name: string): string {
  const label = name.replace(/\.[^.]+$/, '').replace(/[[\]]/g, '');
  return kind === 'video' ? `::video[${label}](${path})` : `![${label}](${path})`;
}

const CHECK_MESSAGE_LABELS: Array<[RegExp, string]> = [
  [/missing required field 'summary'/, '缺少摘要'],
  [/missing required field 'title'/, '缺少标题'],
  [/missing required field 'date'/, '缺少日期'],
];

/** Drop the "blog/<slug>.md: " prefix and translate the common gate messages. */
export function checkMessage(raw: string): string {
  const text = raw.replace(/^blog\/[^:]+\.md:\s*/, '');
  for (const [pattern, label] of CHECK_MESSAGE_LABELS) {
    if (pattern.test(text)) return label;
  }
  return text;
}

/** True when a gate error is the missing-summary rule (fixable inline). */
export function isMissingSummary(raw: string): boolean {
  return /missing required field 'summary'/.test(raw);
}

export interface OutlineItem {
  id: string;
  level: number;
  text: string;
}

/** Extract an H1–H3 outline from editor blocks (ids match the DOM data-id). */
export function outlineFromBlocks(blocks: EditorBlocks): OutlineItem[] {
  const items: OutlineItem[] = [];
  for (const block of blocks) {
    if ((block as { type?: string }).type !== 'heading') continue;
    const level = Number((block as { props?: { level?: number } }).props?.level ?? 1);
    if (level > 3) continue;
    const content = (block as { content?: Array<{ text?: string }> }).content ?? [];
    const text = content
      .map((part) => (typeof part?.text === 'string' ? part.text : ''))
      .join('')
      .trim();
    const id = String((block as { id?: string }).id ?? '');
    if (text && id) items.push({ id, level, text });
  }
  return items;
}

/** Rough reading stats: CJK characters count as words, plus Latin words. */
export function wordCount(markdown: string): number {
  const text = markdown
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/<!--[\s\S]*?-->/g, ' ')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, ' ')
    .replace(/::video\[[^\]]*\]\([^)]*\)/g, ' ');
  const cjk = text.match(/[㐀-鿿豈-﫿]/g)?.length ?? 0;
  const latin = text.replace(/[㐀-鿿豈-﫿]/g, ' ').match(/[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*/g)?.length ?? 0;
  return cjk + latin;
}
