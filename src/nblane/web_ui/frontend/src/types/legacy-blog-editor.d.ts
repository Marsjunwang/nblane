declare module '*public_blog_editor_component/frontend/src/blocks/markdown.js' {
  export function blocksToNblaneMarkdown(editor: unknown, blocks?: unknown[]): string;
  export function parseMarkdownToEditorBlocks(editor: unknown, markdown: string): unknown[];
  export function containsDisplayMathBlock(markdown: string): boolean;
}

declare module '*public_blog_editor_component/frontend/src/blocks/blogBlocks.jsx' {
  export const blogSchema: unknown;
  export function getBlogSlashMenuItems(
    editor: unknown,
    labels?: Record<string, string>,
  ): Array<{ title: string; aliases?: string[]; onItemClick: () => void; [key: string]: unknown }>;
}
