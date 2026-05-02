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

function splitOneLineFlowchart(body) {
  const statements = [];
  let start = 0;
  let quote = "";
  let square = 0;
  let curly = 0;
  let paren = 0;
  for (let index = 0; index < body.length; index += 1) {
    const char = body[index];
    if (quote) {
      if (char === quote) {
        quote = "";
      }
      continue;
    }
    if (char === "'" || char === '"' || char === "`") {
      quote = char;
      continue;
    }
    if (char === "[") {
      square += 1;
      continue;
    }
    if (char === "]" && square > 0) {
      square -= 1;
      continue;
    }
    if (char === "{") {
      curly += 1;
      continue;
    }
    if (char === "}" && curly > 0) {
      curly -= 1;
      continue;
    }
    if (char === "(") {
      paren += 1;
      continue;
    }
    if (char === ")" && paren > 0) {
      paren -= 1;
      continue;
    }
    if (!/\s/u.test(char) || square || curly || paren) {
      continue;
    }
    const previous = index > 0 ? body[index - 1] : "";
    if (!/[\w\]\})]/iu.test(previous)) {
      continue;
    }
    const rest = body.slice(index).trimStart();
    if (
      /^[A-Za-z_][\w-]*(?:\s*(?:\[[^\]]*\]|\{[^}]*\}|\([^)]*\)))?\s*(?:-->|---|--|==>|-\.->|-\.)/u.test(
        rest,
      )
    ) {
      const statement = body.slice(start, index).trim().replace(/;$/u, "");
      if (statement) {
        statements.push(statement);
      }
      start = index + body.slice(index).length - rest.length;
    }
  }
  const tail = body.slice(start).trim().replace(/;$/u, "");
  if (tail) {
    statements.push(tail);
  }
  if (statements.length === 1 && statements[0].includes(";")) {
    return statements[0].split(";").map((part) => part.trim()).filter(Boolean);
  }
  return statements;
}

function normalizeMermaidSource(value) {
  const source = cleanText(value)
    .replace(/\\r\\n/g, "\n")
    .replace(/\\n/g, "\n")
    .replace(/\\u002d/g, "-")
    .trim()
    .replace(/[，。]+$/u, "");
  if (!source || source.includes("\n")) {
    return source;
  }
  const match = source.match(/^(?<header>(?:flowchart|graph)\s+(?:TB|TD|BT|LR|RL))\s+(?<body>.+)$/iu);
  if (!match?.groups?.header || !match.groups.body) {
    return source;
  }
  const statements = splitOneLineFlowchart(match.groups.body.trim());
  if (!statements.length) {
    return source;
  }
  return [match.groups.header, ...statements.map((statement) => `  ${statement}`)].join("\n");
}

async function loadMermaid() {
  const module = await import("mermaid");
  return module.default || module;
}

export function MermaidRenderer({ source, title = "Mermaid diagram" }) {
  const [state, setState] = useState({ status: "idle", svg: "", error: "" });
  const sourceText = normalizeMermaidSource(source);
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
