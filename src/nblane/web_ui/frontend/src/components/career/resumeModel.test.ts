import { describe, expect, it } from 'vitest';

import type { ResumeDoc } from '../../api/types';
import { cleanDraftId, emptyRecord, mergeImported, moveItem, resumeStats } from './resumeModel';

const doc = (patch: Partial<ResumeDoc> = {}): ResumeDoc => ({
  profile: 'alice',
  visibility: 'private',
  basics: { name: 'Alice', title: '', tagline: '', location: '', phone: '', email: '', website: '', photo: 'media/resume/p.jpg' },
  summary: '',
  skills: [],
  skill_groups: [],
  experiences: [],
  projects: [],
  outputs: [],
  education: [],
  honors: [],
  extra_sections: [],
  section_titles: {},
  ...patch,
});

describe('resumeModel', () => {
  it('moves items within bounds', () => {
    expect(moveItem([1, 2, 3], 0, 1)).toEqual([2, 1, 3]);
    expect(moveItem([1, 2, 3], 0, -1)).toEqual([1, 2, 3]);
  });

  it('builds empty records with section-specific fields', () => {
    expect(emptyRecord('education')).toMatchObject({ school: '', degree: '' });
    expect(emptyRecord('experiences')).toMatchObject({ company: '', role: '' });
  });

  it('keeps identity, visibility and photo when merging an import', () => {
    const imported = doc({ profile: 'x', visibility: 'public', summary: 'new' });
    imported.basics = { ...imported.basics, name: '张三', photo: '' };
    const merged = mergeImported(doc({ visibility: 'public' }), imported);
    expect(merged.profile).toBe('alice');
    expect(merged.summary).toBe('new');
    expect(merged.basics.name).toBe('张三');
    expect(merged.basics.photo).toBe('media/resume/p.jpg');
  });

  it('summarizes and cleans ids like the server', () => {
    expect(resumeStats(doc())).toBe('只有基本信息');
    expect(resumeStats(doc({ experiences: [emptyRecord('experiences')] }))).toBe('经历 1 段');
    expect(cleanDraftId(' VLA 算法/工程师 ')).toBe('VLA-算法-工程师');
  });
});
