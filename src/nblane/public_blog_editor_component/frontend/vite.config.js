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
          if (!id.includes("node_modules")) {
            return undefined;
          }
          if (id.includes("mermaid") || id.includes("d3") || id.includes("dagre") || id.includes("graphlib")) {
            return "vendor-mermaid";
          }
          if (id.includes("elkjs") || id.includes("cytoscape")) {
            return "vendor-diagram-layout";
          }
          if (id.includes("katex")) {
            return "vendor-katex";
          }
          if (id.includes("diff-match-patch")) {
            return "vendor-diff";
          }
          if (id.includes("@blocknote") || id.includes("@tiptap")) {
            return "vendor-blocknote";
          }
          if (
            id.includes("react") ||
            id.includes("react-dom") ||
            id.includes("scheduler") ||
            id.includes("use-sync-external-store") ||
            id.includes("@mantine") ||
            id.includes("@floating-ui") ||
            id.includes("tabbable")
          ) {
            return "vendor-react-ui";
          }
          if (id.includes("streamlit-component-lib")) {
            return "vendor-streamlit";
          }
          if (id.includes("emoji-mart") || id.includes("@emoji-mart")) {
            return "vendor-emoji";
          }
          if (
            id.includes("prosemirror") ||
            id.includes("yjs") ||
            id.includes("lib0") ||
            id.includes("orderedmap") ||
            id.includes("rope-sequence") ||
            id.includes("w3c-keyname")
          ) {
            return "vendor-editor-core";
          }
          if (
            id.includes("unified") ||
            id.includes("remark") ||
            id.includes("rehype") ||
            id.includes("micromark") ||
            id.includes("mdast") ||
            id.includes("hast") ||
            id.includes("unist") ||
            id.includes("vfile") ||
            id.includes("parse5") ||
            id.includes("property-information") ||
            id.includes("character-entities") ||
            id.includes("decode-named-character-reference") ||
            id.includes("comma-separated-tokens") ||
            id.includes("space-separated-tokens") ||
            id.includes("html-void-elements") ||
            id.includes("web-namespaces") ||
            id.includes("zwitch") ||
            id.includes("bail") ||
            id.includes("ccount") ||
            id.includes("devlop") ||
            id.includes("trough") ||
            id.includes("trim-lines") ||
            id.includes("trim-trailing-lines") ||
            id.includes("longest-streak") ||
            id.includes("markdown-table") ||
            id.includes("stringify-entities")
          ) {
            return "vendor-markdown";
          }
          return "vendor-react-ui";
        },
      },
    },
  },
});
