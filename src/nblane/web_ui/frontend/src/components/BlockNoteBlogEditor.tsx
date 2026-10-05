import { filterSuggestionItems } from '@blocknote/core';
import { zh } from '@blocknote/core/locales';
import { BlockNoteView } from '@blocknote/mantine';
import {
  getDefaultReactSlashMenuItems,
  SuggestionMenuController,
  useCreateBlockNote,
} from '@blocknote/react';
import '@blocknote/core/fonts/inter.css';
import '@blocknote/mantine/style.css';
import { Alert, Textarea } from '@mantine/core';
import { forwardRef, useCallback, useEffect, useImperativeHandle, useRef, useState } from 'react';

import {
  blocksToNblaneMarkdown,
  parseMarkdownToEditorBlocks,
} from '../../../../public_blog_editor_component/frontend/src/blocks/markdown.js';
import {
  blogSchema,
  getBlogSlashMenuItems,
} from '../../../../public_blog_editor_component/frontend/src/blocks/blogBlocks.jsx';
// Block-level styles only (no global selectors), shared with the Streamlit
// component; blogEditor.css supplies the --nb-* variables they rely on.
import '../../../../public_blog_editor_component/frontend/src/blocks/blocks.css';
import './blogEditor.css';

export type EditorBlocks = Array<Record<string, unknown>>;

export interface BlogEditorChange {
  markdown: string;
  /** Empty in source mode: Markdown is then the only source of truth. */
  blocksJson: EditorBlocks;
}

export interface BlockNoteBlogEditorHandle {
  /** Insert a Markdown snippet (image, ::video, …) after the cursor block. */
  insertMarkdown: (snippet: string) => void;
}

export interface BlockNoteBlogEditorProps {
  /** Initial content. The editor is uncontrolled: remount (key) to reload. */
  markdown: string;
  blocksJson?: EditorBlocks;
  sourceMode: boolean;
  readOnly?: boolean;
  /** Map a stored media reference (media/blog/…) to a browser URL. */
  resolveMediaUrl: (path: string) => string;
  /** Store an uploaded file and return the media reference to keep. */
  uploadMedia: (file: File) => Promise<string>;
  onChange: (value: BlogEditorChange) => void;
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

export const BlockNoteBlogEditor = forwardRef<BlockNoteBlogEditorHandle, BlockNoteBlogEditorProps>(
  function BlockNoteBlogEditor(
    { markdown, blocksJson = [], sourceMode, readOnly = false, resolveMediaUrl, uploadMedia, onChange },
    ref,
  ) {
    const resolveRef = useRef(resolveMediaUrl);
    resolveRef.current = resolveMediaUrl;
    const uploadRef = useRef(uploadMedia);
    uploadRef.current = uploadMedia;
    const onChangeRef = useRef(onChange);
    onChangeRef.current = onChange;

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
        try {
          let next: unknown[] = blocks;
          if (!next.length) next = parseMarkdownToEditorBlocks(editor, text || '');
          try {
            editor.replaceBlocks(editor.document, next as never);
          } catch (error) {
            // A stale/invalid sidecar must not block editing: fall back to
            // the Markdown, which is the publishing source of truth anyway.
            if (!blocks.length) throw error;
            editor.replaceBlocks(editor.document, parseMarkdownToEditorBlocks(editor, text || '') as never);
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
      }),
      [editor, sourceMode],
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
      <div className="nb-spa-editor" data-testid="blocknote-editor">
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
            theme="light"
            slashMenu={false}
            onChange={() => {
              if (hydratingRef.current) return;
              onChangeRef.current({
                markdown: blocksToNblaneMarkdown(editor, editor.document),
                blocksJson: cloneBlocks(editor),
              });
            }}
          >
            <SuggestionMenuController triggerCharacter="/" getItems={getSlashItems} />
          </BlockNoteView>
        )}
      </div>
    );
  },
);
