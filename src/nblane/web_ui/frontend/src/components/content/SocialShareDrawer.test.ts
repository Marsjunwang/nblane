import { describe, expect, it } from 'vitest';

import { xLengthHint, xWeightedLength } from './SocialShareDrawer';

describe('xWeightedLength', () => {
  it('counts CJK as 2 and ASCII as 1', () => {
    expect(xWeightedLength('abc')).toBe(3);
    expect(xWeightedLength('三十岁')).toBe(6);
    expect(xWeightedLength('30岁，失业')).toBe(2 + 2 + 2 + 2 + 2);
  });

  it('treats general punctuation like an ASCII-width character', () => {
    expect(xWeightedLength('—')).toBe(1);
  });

  it('counts any link as 23, like t.co', () => {
    const url = 'https://example.com/blog/2026-10-11-a-very-long-slug-for-the-post';
    expect(xWeightedLength(`Hi\n${url}`)).toBe(2 + 1 + 23);
    expect(xWeightedLength('https://x.co')).toBe(23);
  });
});

describe('xLengthHint', () => {
  it('mentions the CJK rule only for Chinese text', () => {
    expect(xLengthHint('Reproducing VLA at home.', 24, false)).toBe('24 / 280');
    expect(xLengthHint('在家复现 VLA', 16, false)).toBe('16 / 280（汉字算 2）');
  });

  it('notes the attached link', () => {
    expect(xLengthHint('Hi\nhttps://example.com/p', 26, true)).toBe('26 / 280（含文章链接（按 23 计））');
    expect(xLengthHint('你好\nhttps://example.com/p', 28, true)).toBe('28 / 280（汉字算 2，含文章链接（按 23 计））');
  });
});
