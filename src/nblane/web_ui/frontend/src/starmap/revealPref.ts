/**
 * 显真 preference (design 四轮 替换制): one global switch shared by the
 * starmap home (chart naming layer) and the projects page (北极星 badge).
 * '1' = true names (朱文), missing/'0' = ancient names (白文, the default).
 */
export const REVEAL_PREF_KEY = 'nblane.starmap.reveal';

export function readRevealPref(): boolean {
  return localStorage.getItem(REVEAL_PREF_KEY) === '1';
}
