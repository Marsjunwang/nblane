import { describe, expect, it } from 'vitest';

import { xWeightedLength } from './SocialShareDrawer';

describe('xWeightedLength', () => {
  it('counts CJK as 2 and ASCII as 1', () => {
    expect(xWeightedLength('abc')).toBe(3);
    expect(xWeightedLength('三十岁')).toBe(6);
    expect(xWeightedLength('30岁，失业')).toBe(2 + 2 + 2 + 2 + 2);
  });

  it('treats general punctuation like an ASCII-width character', () => {
    expect(xWeightedLength('—')).toBe(1);
  });
});
