/* StarCatalog interaction tests (design home-starmap-enhancements §2):
 * the panel stays open when a row is selected, ↑/↓ (j/k) moves the row
 * highlight with wrap-around, Enter opens the card, chart clicks sync the
 * highlight back to the matching row, and the one-time hint bar fades. */
import { fireEvent, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { renderWithProviders } from '../test/render';
import { catalogRows, StarCatalog, wrapIndex } from './StarCatalog';
import type { StarmapSelection } from './StarmapScene';
import type { StarmapSnapshot } from './snapshot';

function snapshotFixture(): StarmapSnapshot {
  return {
    north_star: '北极星铭文',
    north: { is_set: true, full: '北极星铭文', brief: '北极', visibility: 'private' },
    goals: [
      { id: 'g1', title: '目标一', status: 'active', summary: '', start: '2026-09-23', target: '2026-12-31' },
      { id: 'g2', title: '目标二', status: 'paused', summary: '', start: '', target: '' },
      { id: 'g3', title: '目标三', status: 'completed', summary: '', start: '', target: '' },
    ],
    categories: [],
    skills: [],
    projects: [],
    evidence: [],
    counts: {
      evidence: 0,
      evidence_needs_review: 0,
      evidence_flying: 0,
      projects_active: 0,
      skills_lit: 0,
    },
  };
}

function renderCatalog(opts: { selection?: StarmapSelection | null; onFocus?: (id: string) => void } = {}) {
  const onFocus = opts.onFocus ?? vi.fn();
  renderWithProviders(
    <StarCatalog
      open
      snapshot={snapshotFixture()}
      profile="alice"
      selection={opts.selection ?? null}
      onFocus={onFocus}
    />,
  );
  return { onFocus };
}

describe('catalogRows / wrapIndex', () => {
  it('flattens 帝星 + goals in section order', () => {
    expect(catalogRows(snapshotFixture()).map((r) => r.id)).toEqual(['north', 'g1', 'g2', 'g3']);
  });

  it('wraps in both directions', () => {
    expect(wrapIndex(4, 0, -1)).toBe(3);
    expect(wrapIndex(4, 3, 1)).toBe(0);
    expect(wrapIndex(4, 1, 1)).toBe(2);
    expect(wrapIndex(0, 0, 1)).toBe(-1);
  });
});

describe('StarCatalog interaction', () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it('stays open when a row is selected (no auto-collapse)', () => {
    const { onFocus } = renderCatalog();
    fireEvent.click(screen.getByTestId('catalog-row-g1'));
    expect(onFocus).toHaveBeenCalledWith('g1');
    // The panel still renders its rows (aria-hidden stays false).
    expect(screen.getByTestId('starmap-catalog').getAttribute('aria-hidden')).toBe('false');
    expect(screen.getByTestId('catalog-row-g1').className).toContain('active');
  });

  it('↑/↓ (and j/k) moves the highlight with wrap-around', () => {
    renderCatalog();
    // Default highlight is 帝星.
    expect(screen.getByTestId('catalog-row-north').className).toContain('active');
    fireEvent.keyDown(window, { key: 'ArrowDown' });
    expect(screen.getByTestId('catalog-row-g1').className).toContain('active');
    fireEvent.keyDown(window, { key: 'j' });
    expect(screen.getByTestId('catalog-row-g2').className).toContain('active');
    fireEvent.keyDown(window, { key: 'k' });
    expect(screen.getByTestId('catalog-row-g1').className).toContain('active');
    // Wrap upward from 帝星 lands on the last goal.
    fireEvent.keyDown(window, { key: 'ArrowUp' });
    fireEvent.keyDown(window, { key: 'ArrowUp' });
    expect(screen.getByTestId('catalog-row-g3').className).toContain('active');
  });

  it('Enter opens the highlighted row card', () => {
    const { onFocus } = renderCatalog();
    fireEvent.keyDown(window, { key: 'ArrowDown' });
    fireEvent.keyDown(window, { key: 'ArrowDown' });
    fireEvent.keyDown(window, { key: 'Enter' });
    expect(onFocus).toHaveBeenCalledWith('g2');
  });

  it('chart → catalog: selection prop highlights the matching row', () => {
    renderCatalog({ selection: { kind: 'goal', id: 'g2', title: '目标二', rows: [] } });
    expect(screen.getByTestId('catalog-row-g2').className).toContain('active');
  });

  it('ignores non-catalog selections (planet/guest/skill)', () => {
    renderCatalog({ selection: { kind: 'planet', id: 'p1', title: 'P', rows: [] } });
    expect(screen.getByTestId('catalog-row-north').className).toContain('active');
  });

  it('shows the fading hint bar once per session', () => {
    renderCatalog();
    expect(screen.getByTestId('catalog-hintbar')).toBeTruthy();
    renderCatalog();
    // Second mount in the same session: the hint is already seen.
    expect(screen.queryAllByTestId('catalog-hintbar')).toHaveLength(1);
  });

  it('keyboard nav pauses while the create form is open', () => {
    const { onFocus } = renderCatalog();
    fireEvent.click(screen.getByTestId('catalog-add-goal'));
    fireEvent.keyDown(window, { key: 'ArrowDown' });
    expect(screen.getByTestId('catalog-row-north').className).toContain('active');
    fireEvent.keyDown(window, { key: 'Enter' });
    expect(onFocus).not.toHaveBeenCalled();
  });
});
