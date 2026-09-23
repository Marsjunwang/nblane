/* asterisms.json contract test — keeps the 星官 data asset honest:
 * valid shape, unique ids, line indices in range, unit-circle
 * normalization (centroid ≈ origin, max radius ≈ 1), and the dipper's
 * seven stars individually named 天枢…摇光 (the goal-dipper naming
 * feature addresses them by name). */
import { describe, expect, it } from 'vitest';

import data from './asterisms.json';

interface AsterismStar {
  x: number;
  y: number;
  mag?: number;
  name?: string;
}
interface Asterism {
  id: string;
  name_zh: string;
  lore: string;
  stars: AsterismStar[];
  lines: [number, number][];
}

const asterisms = data.asterisms as Asterism[];

describe('asterisms.json', () => {
  it('has ~20 entries with unique ascii ids, 中文名, and lore', () => {
    expect(asterisms.length).toBeGreaterThanOrEqual(20);
    const ids = asterisms.map((a) => a.id);
    expect(new Set(ids).size).toBe(ids.length);
    for (const a of asterisms) {
      expect(a.id).toMatch(/^[a-z0-9_]+$/);
      expect(a.name_zh.length).toBeGreaterThan(0);
      expect(a.lore.length).toBeGreaterThan(0);
    }
  });

  it('every entry has stars, finite coords, and in-range line indices', () => {
    for (const a of asterisms) {
      expect(a.stars.length).toBeGreaterThanOrEqual(2);
      expect(a.lines.length).toBeGreaterThanOrEqual(1);
      for (const s of a.stars) {
        expect(Number.isFinite(s.x)).toBe(true);
        expect(Number.isFinite(s.y)).toBe(true);
        if (s.mag !== undefined) expect(s.mag).toBeLessThan(7); // naked-eye figures
      }
      for (const [i, j] of a.lines) {
        expect(i).toBeGreaterThanOrEqual(0);
        expect(j).toBeGreaterThanOrEqual(0);
        expect(i).toBeLessThan(a.stars.length);
        expect(j).toBeLessThan(a.stars.length);
        expect(i).not.toBe(j);
      }
    }
  });

  it('is normalized: centroid at origin, max radius 1 (aspect preserved)', () => {
    for (const a of asterisms) {
      const cx = a.stars.reduce((s, p) => s + p.x, 0) / a.stars.length;
      const cy = a.stars.reduce((s, p) => s + p.y, 0) / a.stars.length;
      expect(Math.hypot(cx, cy)).toBeLessThan(0.02);
      const rmax = Math.max(...a.stars.map((p) => Math.hypot(p.x, p.y)));
      expect(rmax).toBeGreaterThan(0.98);
      expect(rmax).toBeLessThanOrEqual(1.001);
    }
  });

  it('北斗 has exactly 7 stars named 天枢…摇光 along the line path', () => {
    const dipper = asterisms.find((a) => a.id === 'beidou');
    expect(dipper).toBeDefined();
    expect(dipper!.stars).toHaveLength(7);
    // the single polyline visits all seven stars in order
    const path = [dipper!.lines[0][0], ...dipper!.lines.map(([, b]) => b)];
    expect(path).toHaveLength(7);
    expect(new Set(path).size).toBe(7);
    expect(path.map((i) => dipper!.stars[i].name)).toEqual([
      '天枢', '天璇', '天玑', '天权', '玉衡', '开阳', '摇光',
    ]);
  });
});
