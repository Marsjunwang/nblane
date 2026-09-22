import { createTheme } from '@mantine/core';

// Brand palette generated around #21685b (nblane primary).
export const theme = createTheme({
  primaryColor: 'brand',
  colors: {
    brand: [
      '#e6f4f1',
      '#cbe7e1',
      '#a3d3c9',
      '#74bcae',
      '#4da593',
      '#35917e',
      '#21685b',
      '#1a5449',
      '#134138',
      '#0c2e28',
    ],
  },
});

// Inscription-card design tokens (铭文卡: 深底/细金边/文楷标题/明体正文).
// Shared by the evidence detail card and, from Phase 3 on, the home detail
// card — keep every consumer importing from here instead of hardcoding.
export const inscription = {
  background: '#16130d',
  borderColor: '#c9a22766',
  titleColor: '#e8d9a8',
  bodyColor: '#d7d0bd',
  dimColor: '#9a9178',
  titleFontFamily: '"Kaiti SC", "STKaiti", "KaiTi", "Noto Serif SC", serif',
  bodyFontFamily: '"Songti SC", "SimSun", "Noto Serif SC", serif',
} as const;
