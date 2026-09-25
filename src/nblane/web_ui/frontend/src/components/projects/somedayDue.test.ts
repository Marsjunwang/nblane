import { describe, expect, it } from 'vitest';

import { isSomedayDue } from './somedayDue';

describe('isSomedayDue (期望激活日)', () => {
  const today = '2026-09-25';

  it('is due when planned_start is in the past', () => {
    expect(isSomedayDue('2026-09-01', today)).toBe(true);
  });

  it('is due when planned_start is today (inclusive)', () => {
    expect(isSomedayDue(today, today)).toBe(true);
  });

  it('is not due when planned_start is in the future', () => {
    expect(isSomedayDue('2026-09-26', today)).toBe(false);
    expect(isSomedayDue('2027-01-01', today)).toBe(false);
  });

  it('is not due without a planned_start', () => {
    expect(isSomedayDue('', today)).toBe(false);
    expect(isSomedayDue(null, today)).toBe(false);
    expect(isSomedayDue(undefined, today)).toBe(false);
  });

  it('is not due when today is unknown', () => {
    expect(isSomedayDue('2026-09-01', '')).toBe(false);
  });

  it('is not due for malformed dates', () => {
    expect(isSomedayDue('not-a-date', today)).toBe(false);
    expect(isSomedayDue('2026-09-01', 'not-a-date')).toBe(false);
  });
});
