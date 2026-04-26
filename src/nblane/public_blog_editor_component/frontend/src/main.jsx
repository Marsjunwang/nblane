import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { Streamlit } from "streamlit-component-lib";
import { BlockNoteView } from "@blocknote/mantine";
import { useCreateBlockNote } from "@blocknote/react";
import "@blocknote/core/fonts/inter.css";
import "@blocknote/mantine/style.css";
import "./style.css";

function markdownFromValue(value) {
  return typeof value === "string" ? value : "";
}

function BlockNoteMarkdownEditor(props) {
  const args = props.args || {};
  const documentId = String(args.document_id || "blog");
  const initialMarkdown = markdownFromValue(args.initial_markdown);
  const height = Number(args.height || 560);
  const editable = args.editable !== false;
  const editor = useCreateBlockNote({});
  const [error, setError] = useState("");
  const [ready, setReady] = useState(false);
  const latestMarkdownRef = useRef(initialMarkdown);
  const loadedDocumentRef = useRef("");
  const loadedInitialMarkdownRef = useRef(null);
  const sendTimerRef = useRef(null);

  useEffect(() => {
    Streamlit.setFrameHeight(height + 34);
  }, [height]);

  useEffect(() => {
    let cancelled = false;
    async function loadMarkdown() {
      if (
        loadedDocumentRef.current === documentId &&
        loadedInitialMarkdownRef.current === initialMarkdown
      ) {
        return;
      }
      setReady(false);
      setError("");
      try {
        const blocks = await editor.tryParseMarkdownToBlocks(initialMarkdown || "");
        if (cancelled) {
          return;
        }
        editor.replaceBlocks(editor.document, blocks);
        latestMarkdownRef.current = initialMarkdown || "";
        loadedDocumentRef.current = documentId;
        loadedInitialMarkdownRef.current = initialMarkdown;
        Streamlit.setComponentValue({
          markdown: latestMarkdownRef.current,
          dirty: false,
          selected_block: null,
          insert_event: null,
        });
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
        }
      } finally {
        if (!cancelled) {
          setReady(true);
          Streamlit.setFrameHeight(height + 34);
        }
      }
    }
    loadMarkdown();
    return () => {
      cancelled = true;
    };
  }, [documentId, editor, height, initialMarkdown]);

  useEffect(() => {
    return () => {
      if (sendTimerRef.current !== null) {
        window.clearTimeout(sendTimerRef.current);
      }
    };
  }, []);

  async function syncMarkdown(immediate = false) {
    if (!ready) {
      return;
    }
    try {
      const markdown = await editor.blocksToMarkdownLossy(editor.document);
      latestMarkdownRef.current = markdown;
      const send = () => {
        Streamlit.setComponentValue({
          markdown,
          dirty: markdown !== (initialMarkdown || ""),
          selected_block: null,
          insert_event: null,
        });
      };
      if (sendTimerRef.current !== null) {
        window.clearTimeout(sendTimerRef.current);
      }
      if (immediate) {
        send();
        return;
      }
      sendTimerRef.current = window.setTimeout(send, 700);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  return (
    <main className="nb-editor-shell" style={{ minHeight: `${height}px` }}>
      {error ? <div className="nb-editor-error">{error}</div> : null}
      <BlockNoteView
        editor={editor}
        editable={editable}
        theme="light"
        onChange={() => syncMarkdown(false)}
        onBlur={() => syncMarkdown(true)}
      />
    </main>
  );
}

function ConnectedEditor() {
  const [args, setArgs] = useState({});

  useEffect(() => {
    Streamlit.setComponentReady();
    const onRender = (event) => {
      setArgs(event.detail.args || {});
    };
    Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender);
    Streamlit.setFrameHeight();
    return () => {
      Streamlit.events.removeEventListener(Streamlit.RENDER_EVENT, onRender);
    };
  }, []);

  return <BlockNoteMarkdownEditor args={args} />;
}

const root = createRoot(document.getElementById("root"));
root.render(<ConnectedEditor />);
