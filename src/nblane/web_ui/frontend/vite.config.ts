/// <reference types="vitest/config" />
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// Dev-server proxy target for the FastAPI backend
// (uvicorn nblane.web_api:app --port 8511). Override with VITE_API_PROXY_TARGET.
const apiProxyTarget = process.env.VITE_API_PROXY_TARGET ?? 'http://127.0.0.1:8511';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: apiProxyTarget,
        changeOrigin: true,
      },
    },
  },
  build: {
    // Output lands in src/nblane/web_ui/static/ — committed and shipped as
    // package data (same convention as the *_component frontends).
    outDir: '../static',
    emptyOutDir: true,
  },
  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    css: false,
  },
});
