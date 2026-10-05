import { describe, expect, it } from 'vitest';

import { cleanWorks, emptyWork, liveSummary, videoKind, worksIssues } from './publicSiteModel';

describe('publicSiteModel', () => {
  it('classifies videos like the static renderer', () => {
    expect(videoKind('')).toBe('');
    expect(videoKind('https://www.bilibili.com/video/BV1xx411c7mD')).toBe('embed');
    expect(videoKind('https://player.bilibili.com/player.html?bvid=BV1xx411c7mD')).toBe('embed');
    expect(videoKind('https://youtu.be/abc')).toBe('embed');
    expect(videoKind('https://cdn.example.com/a.mp4')).toBe('direct');
    expect(videoKind('media/works/a-123.mp4')).toBe('local');
    expect(videoKind('https://example.com/watch')).toBe('link');
  });

  it('flags missing titles and unsafe link schemes, drops empty links', () => {
    const work = { ...emptyWork(), links: [{ label: 'x', url: 'javascript:alert(1)' }, { label: '', url: ' ' }] };
    const issues = worksIssues([work]);
    expect(issues.some((issue) => issue.includes('缺少标题'))).toBe(true);
    expect(issues.some((issue) => issue.includes('javascript'))).toBe(true);
    expect(worksIssues([{ ...emptyWork(), title: 'ok', links: [{ label: '', url: 'arxiv.org/abs/1' }] }])).toEqual([]);
    expect(cleanWorks([work])[0].links).toHaveLength(1);
  });

  it('summarizes the live diff', () => {
    expect(liveSummary(null)).toBe('');
    const base = {
      output_dir: '/x',
      exists: true,
      built_at: '',
      page_count: 1,
      has_previous: false,
      previous_built_at: '',
      pdf_live: false,
      in_sync: false,
      added: [],
      changed: [{ path: 'index.html', title: 'Home' }],
      removed: [],
      pdf_pending: true,
    };
    expect(liveSummary(base)).toBe('待发布：更新 1 页，简历 PDF 有变化');
    expect(liveSummary({ ...base, exists: false })).toContain('首次上线');
    expect(liveSummary({ ...base, in_sync: true })).toBe('线上已是最新。');
  });
});
