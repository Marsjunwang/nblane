import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  base: "./",
  plugins: [react()],
  build: {
    outDir: "static",
    emptyOutDir: true,
    chunkSizeWarningLimit: 800,
    rollupOptions: {
      output: {
        manualChunks(id) {
          const normalizedId = id.replace(/\\/g, "/");
          if (!normalizedId.includes("node_modules")) {
            return undefined;
          }
          if (normalizedId.includes("/node_modules/mermaid/")) {
            return undefined;
          }
          if (normalizedId.includes("/node_modules/d3") || normalizedId.includes("/node_modules/internmap/")) {
            return "vendor-d3";
          }
          if (
            normalizedId.includes("/node_modules/dagre-d3-es/") ||
            normalizedId.includes("/node_modules/graphlib/")
          ) {
            return "vendor-dagre";
          }
          if (normalizedId.includes("/node_modules/elkjs/")) {
            return "vendor-elk";
          }
          if (
            normalizedId.includes("/node_modules/cytoscape/") ||
            normalizedId.includes("/node_modules/cytoscape-cose-bilkent/") ||
            normalizedId.includes("/node_modules/cose-base/")
          ) {
            return "vendor-cytoscape";
          }
          if (normalizedId.includes("katex")) {
            return "vendor-katex";
          }
          if (normalizedId.includes("diff-match-patch")) {
            return "vendor-diff";
          }
          if (normalizedId.includes("@blocknote") || normalizedId.includes("@tiptap")) {
            return "vendor-blocknote";
          }
          if (
            normalizedId.includes("react") ||
            normalizedId.includes("react-dom") ||
            normalizedId.includes("scheduler") ||
            normalizedId.includes("use-sync-external-store") ||
            normalizedId.includes("@mantine") ||
            normalizedId.includes("@floating-ui") ||
            normalizedId.includes("tabbable")
          ) {
            return "vendor-react-ui";
          }
          if (normalizedId.includes("streamlit-component-lib")) {
            return "vendor-streamlit";
          }
          if (normalizedId.includes("emoji-mart") || normalizedId.includes("@emoji-mart")) {
            return "vendor-emoji";
          }
          if (
            normalizedId.includes("prosemirror") ||
            normalizedId.includes("yjs") ||
            normalizedId.includes("lib0") ||
            normalizedId.includes("orderedmap") ||
            normalizedId.includes("rope-sequence") ||
            normalizedId.includes("w3c-keyname")
          ) {
            return "vendor-editor-core";
          }
          if (
            normalizedId.includes("unified") ||
            normalizedId.includes("remark") ||
            normalizedId.includes("rehype") ||
            normalizedId.includes("micromark") ||
            normalizedId.includes("mdast") ||
            normalizedId.includes("hast") ||
            normalizedId.includes("unist") ||
            normalizedId.includes("vfile") ||
            normalizedId.includes("parse5") ||
            normalizedId.includes("property-information") ||
            normalizedId.includes("character-entities") ||
            normalizedId.includes("decode-named-character-reference") ||
            normalizedId.includes("comma-separated-tokens") ||
            normalizedId.includes("space-separated-tokens") ||
            normalizedId.includes("html-void-elements") ||
            normalizedId.includes("web-namespaces") ||
            normalizedId.includes("zwitch") ||
            normalizedId.includes("bail") ||
            normalizedId.includes("ccount") ||
            normalizedId.includes("devlop") ||
            normalizedId.includes("trough") ||
            normalizedId.includes("trim-lines") ||
            normalizedId.includes("trim-trailing-lines") ||
            normalizedId.includes("longest-streak") ||
            normalizedId.includes("markdown-table") ||
            normalizedId.includes("stringify-entities")
          ) {
            return "vendor-markdown";
          }
          return "vendor-react-ui";
        },
      },
    },
  },
});
