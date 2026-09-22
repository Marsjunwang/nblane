import { fileURLToPath } from "node:url";
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
      input: {
        main: fileURLToPath(new URL("./index.html", import.meta.url)),
        playground: fileURLToPath(new URL("./playground.html", import.meta.url)),
        specimen: fileURLToPath(new URL("./specimen.html", import.meta.url)),
        "title-seal": fileURLToPath(new URL("./title-seal.html", import.meta.url)),
        "title-v2": fileURLToPath(new URL("./title-v2.html", import.meta.url)),
      },
      output: {
        // Content-hashed names so a redeploy always busts the browser cache
        // (the sidecar serves these with a 24h max-age and discovers the
        // current set by globbing the assets dir, so it picks up new hashes
        // automatically and stale ones just 404 harmlessly).
        entryFileNames: (chunk) =>
          chunk.name === "main"
            ? "assets/home-dashboard.[hash].js"
            : "assets/[name].[hash].js",
        assetFileNames: "assets/home-dashboard.[hash][extname]",
      },
    },
  },
});
