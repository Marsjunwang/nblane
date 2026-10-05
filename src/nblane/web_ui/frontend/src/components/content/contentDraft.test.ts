import { describe, expect, it } from 'vitest';

import {
  checkMessage,
  contentEditorPath,
  draftFromPost,
  mediaSnippet,
  outlineFromBlocks,
  stripDuplicateTitle,
  wordCount,
} from './contentDraft';
import type { StudioPostDetail } from '../../api/types';

function post(overrides: Partial<StudioPostDetail>): StudioPostDetail {
  return {
    slug: 'p',
    title: 'Title',
    date: '2026-10-05',
    status: 'draft',
    summary: '',
    cover: '',
    tags: [],
    body: '',
    ...overrides,
  } as StudioPostDetail;
}

describe('stripDuplicateTitle', () => {
  it('drops a leading H1 that repeats the title', () => {
    expect(stripDuplicateTitle('# My Post\n\nBody.', 'My Post')).toEqual({ body: 'Body.', stripped: true });
  });

  it('ignores case and whitespace differences', () => {
    expect(stripDuplicateTitle('#   my  post \nBody', 'My Post').stripped).toBe(true);
  });

  it('keeps a different first heading', () => {
    expect(stripDuplicateTitle('# Intro\n\nBody', 'My Post')).toEqual({ body: '# Intro\n\nBody', stripped: false });
  });

  it('keeps H2 headings even when they match', () => {
    expect(stripDuplicateTitle('## My Post\n', 'My Post').stripped).toBe(false);
  });
});

describe('draftFromPost', () => {
  it('drops the sidecar blocks when the duplicate title was stripped', () => {
    const draft = draftFromPost(post({ title: 'T', body: '# T\n\nx', blocks_json: [{ type: 'heading' }] }));
    expect(draft.body).toBe('x');
    expect(draft.blocksJson).toEqual([]);
  });

  it('keeps the sidecar blocks otherwise', () => {
    const blocks = [{ type: 'paragraph' }];
    expect(draftFromPost(post({ body: 'x', blocks_json: blocks })).blocksJson).toEqual(blocks);
  });
});

describe('helpers', () => {
  it('encodes each slug segment in editor paths', () => {
    expect(contentEditorPath('王 军', 'cat/a b')).toBe('/p/%E7%8E%8B%20%E5%86%9B/content/cat/a%20b');
  });

  it('builds image and video snippets from the file name', () => {
    expect(mediaSnippet('image', 'media/blog/p/a.png', 'shot [1].png')).toBe('![shot 1](media/blog/p/a.png)');
    expect(mediaSnippet('video', 'media/blog/p/c.mp4', 'clip.mp4')).toBe('::video[clip](media/blog/p/c.mp4)');
  });

  it('translates the summary gate message', () => {
    expect(checkMessage("blog/x.md: missing required field 'summary'")).toBe('缺少摘要');
    expect(checkMessage('blog/x.md: something else')).toBe('something else');
  });

  it('counts CJK characters and Latin words, ignoring code and media', () => {
    expect(wordCount('你好 world\n\n```\ncode here\n```\n![a](b.png)')).toBe(3);
  });
});

describe('outlineFromBlocks', () => {
  it('keeps H1-H3 headings with text, in order', () => {
    const blocks = [
      { id: 'a', type: 'heading', props: { level: 1 }, content: [{ type: 'text', text: 'Intro' }] },
      { id: 'b', type: 'paragraph', content: [{ type: 'text', text: 'x' }] },
      { id: 'c', type: 'heading', props: { level: 2 }, content: [{ type: 'text', text: 'Part ' }, { type: 'text', text: 'A' }] },
      { id: 'd', type: 'heading', props: { level: 4 }, content: [{ type: 'text', text: 'Deep' }] },
      { id: 'e', type: 'heading', props: { level: 3 }, content: [] },
    ];
    expect(outlineFromBlocks(blocks)).toEqual([
      { id: 'a', level: 1, text: 'Intro' },
      { id: 'c', level: 2, text: 'Part A' },
    ]);
  });
});
