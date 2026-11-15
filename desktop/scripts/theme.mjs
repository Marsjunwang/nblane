import { mkdir, readFile, writeFile } from 'node:fs/promises';

const themePath = new URL('../../src/nblane/web_ui/frontend/src/theme.ts', import.meta.url);
const source = await readFile(themePath, 'utf8');
const chrome = source.match(/export const chrome = \{([\s\S]*?)\} as const;/)?.[1];
if (!chrome) throw new Error('Cannot find shared chrome theme tokens.');
const tokens = {
  bg: 'pageBg', panel: 'panelBg', card: 'cardBg', text: 'text',
  dim: 'dim', gold: 'gold', 'gold-text': 'goldText',
};
const colors = {};
const lines = Object.entries(tokens).map(([name, key]) => {
  const value = chrome.match(new RegExp(`${key}:\\s*'([^']+)'`))?.[1];
  if (!value || !/^#[\da-f]{6}$/i.test(value)) throw new Error(`Missing color: ${key}`);
  colors[key] = value;
  return `  --sticker-${name}: ${value};`;
});
await mkdir(new URL('../renderer/', import.meta.url), { recursive: true });
await writeFile(new URL('../renderer/theme.css', import.meta.url),
  `/* Generated from web_ui/frontend/src/theme.ts by npm run prepare:theme. */\n:root {\n${lines.join('\n')}\n}\n`);
await mkdir(new URL('../lib/', import.meta.url), { recursive: true });
await writeFile(new URL('../lib/theme.cjs', import.meta.url),
  `// Generated from web_ui/frontend/src/theme.ts by npm run prepare:theme.\nmodule.exports = Object.freeze(${JSON.stringify(colors, null, 2)});\n`);
