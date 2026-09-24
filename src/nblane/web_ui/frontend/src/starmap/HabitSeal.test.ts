import { describe, expect, it } from 'vitest';

import { sealGlyph, todayCheckinId } from './HabitSeal';

describe('sealGlyph (日课印面字)', () => {
  it('uses the curated map for common habits (炼/学/复/读/跑/坐/息)', () => {
    expect(sealGlyph({ id: 'exercise', title: 'Exercise' })).toBe('炼');
    expect(sealGlyph({ id: 'learning', title: 'Learning' })).toBe('学');
    expect(sealGlyph({ id: 'rehab', title: '康复训练' })).toBe('复');
    expect(sealGlyph({ id: 'reading', title: '读书' })).toBe('读');
    expect(sealGlyph({ id: 'running', title: '晨跑' })).toBe('跑');
    expect(sealGlyph({ id: 'meditation', title: '冥想' })).toBe('坐');
    expect(sealGlyph({ id: 'sleep', title: '作息' })).toBe('息');
  });

  it('matches on either id or title, case-insensitive', () => {
    expect(sealGlyph({ id: 'h1', title: '锻炼' })).toBe('炼');
    expect(sealGlyph({ id: 'LEARNING', title: '' })).toBe('学');
  });

  it('falls back to the first char of the title (or id)', () => {
    expect(sealGlyph({ id: 'h2', title: '写作练习' })).toBe('写');
    expect(sealGlyph({ id: 'calligraphy', title: '' })).toBe('c');
  });
});

describe('todayCheckinId (销印寻址)', () => {
  it('returns today\'s LATEST check-in id from recent_days', () => {
    const habit = {
      recent_days: [
        { date: '2026-09-22', count: 1, checkin_ids: ['ck_old'] },
        { date: '2026-09-23', count: 2, checkin_ids: ['ck_a', 'ck_b'] },
      ],
    };
    expect(todayCheckinId(habit, '2026-09-23')).toBe('ck_b');
  });

  it('returns "" when today has no row or no ids (legacy records)', () => {
    expect(todayCheckinId({ recent_days: [] }, '2026-09-23')).toBe('');
    expect(
      todayCheckinId({ recent_days: [{ date: '2026-09-23', count: 1 }] }, '2026-09-23'),
    ).toBe('');
    expect(
      todayCheckinId(
        { recent_days: [{ date: '2026-09-23', count: 1, checkin_ids: [] }] },
        '2026-09-23',
      ),
    ).toBe('');
    expect(todayCheckinId({}, '2026-09-23')).toBe('');
  });

  it('skips empty id strings', () => {
    const habit = {
      recent_days: [{ date: '2026-09-23', count: 2, checkin_ids: ['ck_a', ''] }],
    };
    expect(todayCheckinId(habit, '2026-09-23')).toBe('ck_a');
  });
});
