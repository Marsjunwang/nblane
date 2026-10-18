import { defineConfig } from '@playwright/test';
import fs from 'node:fs';
const chromium = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || (fs.existsSync('/snap/bin/chromium') ? '/snap/bin/chromium' : '');
export default defineConfig({
  testDir: '.', testMatch: 'content-image-editor.spec.ts', timeout: 30_000,
  webServer: { command: 'npm run dev -- --host 127.0.0.1 --port 18517 --strictPort', cwd: '../../src/nblane/web_ui/frontend', url: 'http://127.0.0.1:18517/tests/image-editor.html', reuseExistingServer: !process.env.CI },
  use: { baseURL: 'http://127.0.0.1:18517', launchOptions: { ...(chromium ? { executablePath: chromium } : {}), args: ['--no-sandbox'] }, viewport: {width: 1100, height: 900}, trace: 'retain-on-failure' },
});
