import React, { useEffect, useRef, useState } from "react";

let mermaidInitialized = false;
let renderCounter = 0;

function cleanText(value) {
  return value === null || value === undefined ? "" : String(value);
}

function nextRenderId() {
  renderCounter += 1;
  return `nb-mermaid-${Date.now()}-${renderCounter}`;
}

async function loadMermaid() {
  const module = await import("mermaid");
  return module.default || module;
}

export function MermaidRenderer({ source, title = "Mermaid diagram" }) {
  const [state, setState] = useState({ status: "idle", svg: "", error: "" });
  const sourceText = cleanText(source).trim();
  const idRef = useRef("");
  if (!idRef.current) {
    idRef.current = nextRenderId();
  }

  useEffect(() => {
    let cancelled = false;

    async function renderMermaid() {
      if (!sourceText) {
        setState({ status: "empty", svg: "", error: "" });
        return;
      }

      setState({ status: "loading", svg: "", error: "" });
      try {
        const mermaid = await loadMermaid();
        if (!mermaid || typeof mermaid.render !== "function") {
          throw new Error("Mermaid renderer is unavailable.");
        }
        if (!mermaidInitialized) {
          mermaid.initialize({
            startOnLoad: false,
            securityLevel: "strict",
            theme: "default",
          });
          mermaidInitialized = true;
        }
        const result = await mermaid.render(nextRenderId(), sourceText);
        const svg = typeof result === "string" ? result : cleanText(result?.svg);
        if (!cancelled) {
          setState({ status: "rendered", svg, error: "" });
        }
      } catch (err) {
        if (!cancelled) {
          setState({
            status: "fallback",
            svg: "",
            error: err instanceof Error ? err.message : String(err),
          });
        }
      }
    }

    renderMermaid();
    return () => {
      cancelled = true;
    };
  }, [sourceText]);

  if (state.svg) {
    return (
      <div
        className="nb-mermaid-renderer"
        data-render-id={idRef.current}
        dangerouslySetInnerHTML={{ __html: state.svg }}
      />
    );
  }

  return (
    <pre
      className="nb-mermaid-fallback"
      data-render-status={state.status}
      title={state.error || title}
    >
      {sourceText || title}
    </pre>
  );
}
