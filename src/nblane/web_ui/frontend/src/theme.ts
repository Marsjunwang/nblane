import { createTheme } from '@mantine/core';

/**
 * Global dark theme (2026-09-23 dark unification). The SPA is locked to the
 * dark scheme; all surfaces derive from the starmap indigo ladder:
 *
 *   page  #0f1930 — AppShell body background (darkest)
 *   panel #101d30 — header / icon rail (matches the projects board ground)
 *   card  #16263d — cards, inputs, dropdowns, modals, drawers
 *   chart #1d3450 — starmap canvas ground (home is full-bleed)
 *
 * Text is 月白 (#f2ede0 family), accents are 泥金 (#dcae55/#eac57e family).
 * Green stays semantic only (success / health) — Mantine's default `green`.
 */
export const chrome = {
  pageBg: '#0f1930',
  panelBg: '#101d30',
  cardBg: '#16263d',
  chartBg: '#1d3450',
  text: '#f2ede0',
  dim: '#b0a78c',
  gold: '#dcae55',
  goldText: '#eac57e',
} as const;

export const theme = createTheme({
  primaryColor: 'brand',
  // Gold reads light on the indigo ground: shade 5 filled, auto-contrast text.
  primaryShade: { light: 6, dark: 5 },
  autoContrast: true,
  white: chrome.text,
  black: '#0b1322',
  colors: {
    // 泥金 (clay gold) — chrome/nav highlights and primary actions.
    brand: [
      '#faf3de',
      '#f2e5bd',
      '#e9d093',
      '#e0ba6b',
      '#dcae55',
      '#d5a342',
      '#c99635',
      '#a67a2c',
      '#7d5c23',
      '#574017',
    ],
    // Starmap indigo ladder, mapped onto Mantine's dark-scheme slots:
    // [0] text · [2] dimmed · [4] border · [5] hover · [6] card · [7] body.
    dark: [
      '#f2ede0',
      '#d9d2c0',
      '#b0a78c',
      '#8d8570',
      '#3a4d6e',
      '#24374f',
      chrome.cardBg,
      chrome.pageBg,
      '#0c1526',
      '#080f1d',
    ],
  },
});

// Inscription-card design tokens (铭文卡: 深底/细金边/文楷标题/明体正文).
// Shared by the evidence detail card and the home detail card — keep every
// consumer importing from here instead of hardcoding.
export const inscription = {
  background: '#16130d',
  borderColor: '#c9a22766',
  titleColor: '#eeddab',
  bodyColor: '#e2dcc9',
  dimColor: chrome.dim,
  accentColor: chrome.goldText,
  titleFontFamily: '"Kaiti SC", "STKaiti", "KaiTi", "Noto Serif SC", serif',
  bodyFontFamily: '"Songti SC", "SimSun", "Noto Serif SC", serif',
} as const;

// Visual tokens for the unified /projects page (泳道看板 + 时间轴).
// Single source of truth lives here; components/projects/palette.ts is a
// backward-compatible re-export.
export const boardPalette = {
  /** Lane / card ground (alpha 0.85–0.92 per the mockups). */
  ground: 'rgba(16, 29, 48, 0.92)',
  groundSoft: 'rgba(16, 29, 48, 0.85)',
  /** Moon-white body text (v2 brightened). */
  text: chrome.text,
  /** Title-level moon-white. */
  titleText: '#faf5e6',
  /** Clay gold (borders, accents). */
  gold: chrome.gold,
  /** Brighter gold for small print. */
  goldText: chrome.goldText,
  /** Dimmed secondary text. */
  dim: chrome.dim,
  /** Default lane border. */
  border: 'rgba(220, 174, 85, 0.22)',
  /** Selected-card gold frame. */
  selectedBorder: chrome.goldText,
  /** Today line (dashed gold). */
  todayLine: chrome.goldText,
} as const;
