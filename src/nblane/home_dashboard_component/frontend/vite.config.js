import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  base: "./",
  define: {
    "process.env.NODE_ENV": JSON.stringify("production"),
  },
  plugins: [react()],
  build: {
    outDir: "static",
    emptyOutDir: true,
    cssCodeSplit: false,
    // The Streamlit host loads a single entry chunk; raising the warning
    // threshold instead of forcing chunk splitting keeps the integration
    // simple. Adaptive rendering (galaxy_scene._adaptiveSkipBloom +
    // idle-throttled rAF) is the bigger lever for actual wall-clock perf
    // than transport size.
    chunkSizeWarningLimit: 1200,
    rollupOptions: {
      output: {
        // Content-hashed names so a redeploy always busts the browser cache
        // (the sidecar serves these with a 24h max-age and discovers the
        // current set by globbing the assets dir, so it picks up new hashes
        // automatically and stale ones just 404 harmlessly).
        entryFileNames: "assets/home-dashboard.[hash].js",
        assetFileNames: "assets/home-dashboard.[hash][extname]",
      },
    },
  },
});
