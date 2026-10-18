import { Fragment, Slice } from '@tiptap/pm/model';
import type { Transaction } from '@tiptap/pm/state';
import { blockToNode, contentNodeToInlineContent, filterSuggestionItems } from '@blocknote/core';
import { zh } from '@blocknote/core/locales';
import { BlockNoteView } from '@blocknote/mantine';
import {
  FormattingToolbar,
  FormattingToolbarController,
  getDefaultReactSlashMenuItems,
  getFormattingToolbarItems,
  SuggestionMenuController,
  useComponentsContext,
  useCreateBlockNote,
} from '@blocknote/react';
import '@blocknote/core/fonts/inter.css';
import '@blocknote/mantine/style.css';
import { Alert, Textarea } from '@mantine/core';
import { IconSparkles } from '@tabler/icons-react';
import { forwardRef, useCallback, useEffect, useImperativeHandle, useRef, useState } from 'react';

import {
  blocksToNblaneMarkdown,
  parseMarkdownToEditorBlocks,
} from '../blogBlocks/markdown.js';
import {
  blogSchema,
  getBlogSlashMenuItems,
} from '../blogBlocks/blogBlocks.jsx';
// Block-level styles only (no global selectors); blogEditor.css supplies the dark --nb-* variables they rely on
// and the dark BlockNote palette.
import '../blogBlocks/blocks.css';
import './blogEditor.css';
import { selectedImages, containsMedia } from './content/imageSelection';
import type { SelectedImage, ImageTarget } from './content/imageTypes';

export type EditorBlocks = Array<Record<string, unknown>>;

export interface BlogEditorChange {
  markdown: string;
  /** Empty in source mode: Markdown is then the only source of truth. */
  blocksJson: EditorBlocks;
}

export interface BlockNoteBlogEditorHandle {
  /** Insert a Markdown snippet (image, ::video, …) after the cursor block. */
  insertMarkdown: (snippet: string) => void;
  /** Move the caret to the start of the document (title → body handoff). */
  focusStart: () => void;
  /** Scroll a heading block into view and place the caret in it. */
  scrollToBlock: (id: string) => void;
  /**
   * Replace the selection captured by the last AI rewrite request with
   * *markdown*. Returns false when that text changed meanwhile (nothing is
   * written then).
   */
  replaceCapturedSelection: (markdown: string, parts?: string[]) => boolean;
  canReplaceImage: (target: ImageTarget) => boolean;
  retargetImage: (target: ImageTarget, appliedPath: string) => ImageTarget | null;
  replaceImage: (target: ImageTarget, path: string) => boolean;
}

/** One selection rewrite request raised from the formatting toolbar. */
export interface AIRewriteRequest {
  operation: string;
  /** Selected passage as Markdown (formatting preserved). */
  selection: string;
  /** Neighbouring paragraphs, for the model's context only. */
  context: string;
  parts?: string[];
}

export const AI_REWRITE_MENU: Array<{ operation: string; label: string }> = [
  { operation: 'polish', label: '润色' },
  { operation: 'shorten', label: '精简' },
  { operation: 'expand', label: '扩写' },
  { operation: 'tone', label: '调整为专业语气' },
  { operation: 'translate', label: '翻译' },
];

export interface BlockNoteBlogEditorProps {
  /** Initial content. The editor is uncontrolled: remount (key) to reload. */
  markdown: string;
  blocksJson?: EditorBlocks;
  sourceMode: boolean;
  readOnly?: boolean;
  /** Focus mode: dim everything but the block under the caret. */
  focusMode?: boolean;
  /** Map a stored media reference (media/blog/…) to a browser URL. */
  resolveMediaUrl: (path: string) => string;
  /** Store an uploaded file and return the media reference to keep. */
  uploadMedia: (file: File) => Promise<string>;
  onChange: (value: BlogEditorChange) => void;
  /** Latest H1–H3 outline (fires on content changes, visual mode only). */
  onOutlineChange?: (blocks: EditorBlocks) => void;
  /** data-id of the heading nearest the caret, for outline highlighting. */
  onActiveHeadingChange?: (id: string) => void;
  /** Show the toolbar AI menu; called with the selected passage. */
  onAIRewrite?: (request: AIRewriteRequest) => void;
  onAIImage?: (images: SelectedImage[]) => void;
}

const SLASH_LABELS = {
  formula_block: '公式',
  formula_block_help: 'LaTeX 公式块',
  video_block: '视频',
  video_block_help: '公开站点视频（填写 media 路径）',
  visual_block: '图示',
  visual_block_help: 'Mermaid 图或图片',
};

// BlockNote's own video/audio/file blocks do not round-trip through the
// nblane Markdown dialect; the blog video_block (::video directive) does.
const HIDDEN_DEFAULT_ITEMS = new Set(['video', 'audio', 'file']);

type AnyEditor = ReturnType<typeof useCreateBlockNote>;

function cloneBlocks(editor: AnyEditor): EditorBlocks {
  return JSON.parse(JSON.stringify(editor.document)) as EditorBlocks;
}

/** Id of the top-level block that contains block *id* (itself if top-level). */
function topLevelBlockId(blocks: EditorBlocks, id: string): string {
  const contains = (block: Record<string, unknown>): boolean =>
    block.id === id || ((block.children as EditorBlocks | undefined) ?? []).some(contains);
  const hit = blocks.find(contains);
  return hit ? String(hit.id) : id;
}

/** "AI" dropdown appended to BlockNote's formatting toolbar. */
function AIRewriteMenu({ onPick, imagesOnly, mixed, textEnabled, imageEnabled }: { onPick: (operation: string) => void; imagesOnly: boolean; mixed: boolean; textEnabled: boolean; imageEnabled: boolean }) {
  const Components = useComponentsContext();
  if (!Components) return null;
  const { Menu, Toolbar } = Components.Generic;
  return (
    <Menu.Root position="bottom-start">
      <Menu.Trigger>
        <Toolbar.Button
          mainTooltip={imagesOnly ? "AI 修改图片" : "AI 改写选中文字"}
          icon={<IconSparkles size={16} />}
          label="AI"
          className="nb-ai-toolbar-button"
        >
          AI
        </Toolbar.Button>
      </Menu.Trigger>
      <Menu.Dropdown className="bn-menu-dropdown">
        {imagesOnly ? <Menu.Item onClick={() => imageEnabled && onPick('image')}>
          {imageEnabled ? '修改图片' : '修改图片（未配置图像服务）'}
        </Menu.Item> : <>
        {mixed && <Menu.Item>仅改写文字，保留图片</Menu.Item>}
        {!textEnabled && <Menu.Item>未配置文字服务</Menu.Item>}
        {AI_REWRITE_MENU.map((item) => (
          <Menu.Item key={item.operation} onClick={() => textEnabled && onPick(item.operation)}>
            {item.label}
          </Menu.Item>
        ))}</>}
      </Menu.Dropdown>
    </Menu.Root>
  );
}

export const BlockNoteBlogEditor = forwardRef<BlockNoteBlogEditorHandle, BlockNoteBlogEditorProps>(
  function BlockNoteBlogEditor(
    {
      markdown,
      blocksJson = [],
      sourceMode,
      readOnly = false,
      focusMode = false,
      resolveMediaUrl,
      uploadMedia,
      onChange,
      onOutlineChange,
      onActiveHeadingChange,
      onAIRewrite,
      onAIImage,
    },
    ref,
  ) {
    const resolveRef = useRef(resolveMediaUrl);
    resolveRef.current = resolveMediaUrl;
    const uploadRef = useRef(uploadMedia);
    uploadRef.current = uploadMedia;
    const onChangeRef = useRef(onChange);
    onChangeRef.current = onChange;
    const onOutlineRef = useRef(onOutlineChange);
    onOutlineRef.current = onOutlineChange;
    const onActiveHeadingRef = useRef(onActiveHeadingChange);
    onActiveHeadingRef.current = onActiveHeadingChange;
    const onAIRewriteRef = useRef(onAIRewrite);
    onAIRewriteRef.current = onAIRewrite;
    const onAIImageRef = useRef(onAIImage);
    onAIImageRef.current = onAIImage;
    const [selectionKind, setSelectionKind] = useState({ imagesOnly: false, mixed: false });
    // ProseMirror range + plain text of the selection sent to the AI.
    const capturedRef = useRef<{ document: string; ranges: Array<{ from: number; to: number }> } | null>(null);

    const editor = useCreateBlockNote({
      schema: blogSchema as never,
      dictionary: zh,
      resolveFileUrl: async (url: string) => resolveRef.current(url),
      uploadFile: async (file: File) => uploadRef.current(file),
    }) as AnyEditor;

    // Hydration writes into the editor must not count as user edits.
    const hydratingRef = useRef(true);
    const [loadError, setLoadError] = useState('');
    const [source, setSource] = useState(markdown);
    const sourceRef = useRef(markdown);
    const prevSourceModeRef = useRef(sourceMode);

    const loadMarkdown = useCallback(
      (text: string, blocks: EditorBlocks) => {
        hydratingRef.current = true;
        // Loading a document is not an edit: keep it out of the undo history,
        // or Ctrl+Z right after opening a post undoes the load and the next
        // autosave writes an empty post.
        const replaceAll = (blocksToInsert: unknown[]) =>
          editor.transact((tr: { setMeta: (key: string, value: unknown) => unknown }) => {
            tr.setMeta('addToHistory', false);
            editor.replaceBlocks(editor.document, blocksToInsert as never);
          });
        try {
          let next: unknown[] = blocks;
          if (!next.length) next = parseMarkdownToEditorBlocks(editor, text || '');
          try {
            replaceAll(next);
          } catch (error) {
            // A stale/invalid sidecar must not block editing: fall back to
            // the Markdown, which is the publishing source of truth anyway.
            if (!blocks.length) throw error;
            replaceAll(parseMarkdownToEditorBlocks(editor, text || ''));
          }
          setLoadError('');
        } catch (error) {
          setLoadError(error instanceof Error ? error.message : String(error));
        } finally {
          hydratingRef.current = false;
        }
      },
      [editor],
    );

    // Initial load, once per mount. Deliberately ignores later prop changes:
    // the parent remounts with a new key to load another document.
    useEffect(() => {
      if (!sourceMode) loadMarkdown(markdown, blocksJson);
      else hydratingRef.current = false;
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Mode switches carry the current text across.
    useEffect(() => {
      if (prevSourceModeRef.current === sourceMode) return;
      prevSourceModeRef.current = sourceMode;
      if (sourceMode) {
        const text = blocksToNblaneMarkdown(editor, editor.document);
        sourceRef.current = text;
        setSource(text);
      } else {
        loadMarkdown(sourceRef.current, []);
        onChangeRef.current({ markdown: sourceRef.current, blocksJson: cloneBlocks(editor) });
      }
    }, [editor, loadMarkdown, sourceMode]);

    useImperativeHandle(
      ref,
      () => ({
        insertMarkdown: (snippet: string) => {
          const clean = snippet.trim();
          if (!clean) return;
          if (sourceMode) {
            const text = `${sourceRef.current.trimEnd()}\n\n${clean}\n`;
            sourceRef.current = text;
            setSource(text);
            onChangeRef.current({ markdown: text, blocksJson: [] });
            return;
          }
          const blocks = parseMarkdownToEditorBlocks(editor, clean);
          const anchor = editor.getTextCursorPosition().block;
          editor.insertBlocks(blocks as never, anchor, 'after');
        },
        focusStart: () => {
          if (sourceMode) return;
          const first = editor.document[0];
          if (first) editor.setTextCursorPosition(first, 'start');
          editor.focus();
        },
        canReplaceImage: (target: ImageTarget) => {
          if (sourceMode || !target.block_id) return false;
          const block = editor.getBlock(target.block_id);
          return !!block && JSON.stringify(block.props) === target.fingerprint;
        },
        retargetImage: (target: ImageTarget, appliedPath: string) => {
          if (sourceMode || !target.block_id || !target.fingerprint) return null;
          const block = editor.getBlock(target.block_id);
          if (!block) return null;
          try {
            const expected = { ...JSON.parse(target.fingerprint), [block.type === 'image' ? 'url' : 'src']: appliedPath };
            if (JSON.stringify(block.props) !== JSON.stringify(expected)) return null;
            return { ...target, source: appliedPath, fingerprint: JSON.stringify(block.props) };
          } catch { return null; }
        },
        replaceImage: (target: ImageTarget, path: string) => {
          if (sourceMode || !target.block_id) return false;
          const block = editor.getBlock(target.block_id);
          if (!block || JSON.stringify(block.props) !== target.fingerprint) return false;
          editor.updateBlock(block, { props: { [block.type === 'image' ? 'url' : 'src']: path } } as never);
          return true;
        },
        replaceCapturedSelection: (markdown: string, parts?: string[]) => {
          const captured = capturedRef.current;
          if (!captured || sourceMode || JSON.stringify(editor.prosemirrorState.doc.toJSON()) !== captured.document) return false;
          const replacements = parts ?? [markdown];
          if (replacements.length !== captured.ranges.length || replacements.some((text) => !text.trim())) return false;
          if (replacements.some((text) => containsMedia(parseMarkdownToEditorBlocks(editor, text) as never))) return false;
          const slices = replacements.map((text) => new Slice(Fragment.fromArray(
            parseMarkdownToEditorBlocks(editor, text.trim()).map((block) => blockToNode(block as never, editor.pmSchema)),
          ), 2, 2));
          editor.transact((tr: Transaction) => {
            for (let index = captured.ranges.length - 1; index >= 0; index--) {
              const { from, to } = captured.ranges[index];
              tr.replaceRange(from, to, slices[index]);
            }
          });
          capturedRef.current = null;
          return true;
        },
        scrollToBlock: (id: string) => {
          if (sourceMode || !id) return;
          const node = document.querySelector(`[data-id="${CSS.escape(id)}"]`);
          node?.scrollIntoView({ behavior: 'smooth', block: 'start' });
          try {
            editor.setTextCursorPosition(id, 'start');
          } catch {
            // Block may have been removed between render and click.
          }
        },
      }),
      [editor, sourceMode],
    );

    // Report the outline on load and after edits (visual mode only). The
    // outline only reads top-level heading blocks, so no deep clone here.
    useEffect(() => {
      if (sourceMode) return undefined;
      const emit = () => onOutlineRef.current?.(editor.document as unknown as EditorBlocks);
      emit();
      return editor.onChange(emit);
    }, [editor, sourceMode]);

    // Caret tracking: the top-level block under the caret drives focus mode,
    // and the nearest preceding heading drives outline highlighting.
    const [caretBlockId, setCaretBlockId] = useState('');
    useEffect(() => {
      if (sourceMode) return undefined;
      return editor.onSelectionChange(() => {
        const cut = editor.getSelectionCutBlocks();
        const images = selectedImages(cut.blocks as never);
        const text = editor.getSelectedText().trim();
        setSelectionKind({ imagesOnly: images.length > 0 && !text, mixed: images.length > 0 && !!text });
        const cursorId = editor.getTextCursorPosition().block.id;
        const topLevel = topLevelBlockId(editor.document as unknown as EditorBlocks, cursorId);
        setCaretBlockId(topLevel);
        let activeHeading = '';
        for (const block of editor.document) {
          if ((block as { type?: string }).type === 'heading') activeHeading = block.id;
          if (block.id === topLevel) break;
        }
        onActiveHeadingRef.current?.(activeHeading);
      });
    }, [editor, sourceMode]);

    const requestAIRewrite = useCallback(
      (operation: string) => {
        const { from, to } = editor.prosemirrorState.selection;
        if (from === to) return;
        const cut = editor.getSelectionCutBlocks();
        const images = selectedImages(cut.blocks as never);
        if (operation === 'image') {
          if (images.length) onAIImageRef.current?.(images);
          return;
        }
        const doc = editor.prosemirrorState.doc;
        const ranges: Array<{ from: number; to: number }> = [];
        const parts: string[] = [];
        // With media in the selection, only textblock interiors are editable.
        // Stable positional ranges preserve every non-text node and its props.
        const hasMedia = containsMedia(cut.blocks as never);
        if (hasMedia) {
          doc.nodesBetween(from, to, (node: { isTextblock: boolean; inlineContent: boolean; textContent: string; nodeSize: number }, pos: number) => {
            if (!node.isTextblock || !node.inlineContent || !node.textContent.trim()) return;
            const start = Math.max(from, pos + 1);
            const end = Math.min(to, pos + node.nodeSize - 1);
            if (end <= start) return;
            const text = doc.textBetween(start, end);
            if (!text.trim()) return;
            ranges.push({ from: start, to: end });
            const contentNode = doc.nodeAt(pos)!;
            const fragment = contentNode.cut(start - pos - 1, end - pos - 1);
            const content = contentNodeToInlineContent(fragment, editor.schema.inlineContentSchema, editor.schema.styleSchema);
            parts.push(editor.blocksToMarkdownLossy([{ type: 'paragraph', content }] as never).trim() || text);
          });
        } else {
          ranges.push({ from, to });
          parts.push((editor.blocksToMarkdownLossy(cut.blocks as never) || editor.getSelectedText()).trim());
        }
        if (!parts.length || !parts.some((text) => text.trim())) return;
        const selection = parts.join('\n\n');
        capturedRef.current = { document: JSON.stringify(doc.toJSON()), ranges };
        // Two top-level neighbours on each side give the model the local thread.
        const top = editor.document as unknown as EditorBlocks;
        const firstId = topLevelBlockId(top, String(cut.blocks[0]?.id ?? ''));
        const lastId = topLevelBlockId(top, String(cut.blocks[cut.blocks.length - 1]?.id ?? ''));
        const start = Math.max(0, top.findIndex((block) => block.id === firstId) - 2);
        const endIndex = top.findIndex((block) => block.id === lastId);
        const end = endIndex < 0 ? start : Math.min(top.length, endIndex + 3);
        const context = editor.blocksToMarkdownLossy(top.slice(start, end) as never);
        onAIRewriteRef.current?.({ operation, selection, context, parts: hasMedia ? parts : undefined });
      },
      [editor],
    );

    const aiToolbar = useCallback(
      () => (
        <FormattingToolbar>
          {[...getFormattingToolbarItems(), <AIRewriteMenu key="nb-ai" onPick={requestAIRewrite} {...selectionKind} textEnabled={!!onAIRewrite} imageEnabled={!!onAIImage} />]}
        </FormattingToolbar>
      ),
      [requestAIRewrite, selectionKind, onAIRewrite, onAIImage],
    );

    const getSlashItems = useCallback(
      async (query: string) =>
        filterSuggestionItems(
          [
            ...getDefaultReactSlashMenuItems(editor).filter(
              (item) => !HIDDEN_DEFAULT_ITEMS.has((item as { key?: string }).key ?? ''),
            ),
            ...(getBlogSlashMenuItems(editor, SLASH_LABELS) as never[]),
          ],
          query,
        ),
      [editor],
    );

    return (
      <div
        className={`nb-spa-editor${focusMode && !sourceMode ? ' nb-spa-editor--focus' : ''}`}
        data-testid="blocknote-editor"
      >
        {focusMode && !sourceMode && caretBlockId && (
          // Block ids are BlockNote-generated (uuid-like); escape anyway.
          <style>{`.nb-spa-editor--focus .bn-editor > .bn-block-group > .bn-block-outer[data-id="${CSS.escape(caretBlockId)}"]{opacity:1}`}</style>
        )}
        {loadError && (
          <Alert color="yellow" mb="sm" title="正文无法转为可视编辑">
            {loadError}。已保留原文，可切换到 Markdown 源码继续编辑。
          </Alert>
        )}
        {sourceMode ? (
          <Textarea
            aria-label="Markdown 源码"
            className="nb-spa-editor-source"
            autosize
            minRows={24}
            value={source}
            readOnly={readOnly}
            onChange={(event) => {
              const text = event.currentTarget.value;
              sourceRef.current = text;
              setSource(text);
              onChangeRef.current({ markdown: text, blocksJson: [] });
            }}
          />
        ) : (
          <BlockNoteView
            editor={editor}
            editable={!readOnly}
            theme="dark"
            slashMenu={false}
            formattingToolbar={!onAIRewrite && !onAIImage}
            onChange={() => {
              if (hydratingRef.current) return;
              onChangeRef.current({
                markdown: blocksToNblaneMarkdown(editor, editor.document),
                blocksJson: cloneBlocks(editor),
              });
            }}
          >
            <SuggestionMenuController triggerCharacter="/" getItems={getSlashItems} />
            {(onAIRewrite || onAIImage) && <FormattingToolbarController formattingToolbar={aiToolbar} />}
          </BlockNoteView>
        )}
      </div>
    );
  },
);
