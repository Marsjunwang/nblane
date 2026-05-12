import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  base: "./",
  define: {
    "process.env.NODE_ENV": JSON.stringify("production"),
  },
  plugins: [react()],
  build: {
    outDir: "dist",
    emptyOutDir: true,
    cssCodeSplit: false,
    lib: {
      entry: "src/main.jsx",
      formats: ["es"],
      name: "GoalPresence",
    },
    rollupOptions: {
      output: {
        entryFileNames: "assets/goal-presence.js",
        assetFileNames: "assets/goal-presence.css",
      },
    },
  },
});
