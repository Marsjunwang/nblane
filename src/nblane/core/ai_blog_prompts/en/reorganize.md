Reorganize the formatting and structure of the WHOLE document so it reads clearly and is ready to publish. This is the case where loosely-pasted content migrated from elsewhere needs to be shaped into a clean blog post.

Strict rules:
- NEVER delete, summarize, or omit any substantive content, facts, data, code, formulas, or links. All information must be preserved.
- Only adjust formatting and structure: assign sensible heading levels (# / ## / ###), tidy paragraphs and line breaks, turn parallel items into ordered/unordered lists, normalize code blocks (label the language), normalize math (inline `$...$`, display `$$...$$`), clean up tables, and unify punctuation and spacing.
- Treat fenced code blocks (```` ``` ````), including ```` ```mermaid ```` diagrams, as VERBATIM: copy them through exactly, preserving every internal line break. NEVER collapse a multi-line code or mermaid block onto one line, and NEVER turn its real newlines into literal `\n`. Keep each mermaid statement (nodes, edges, `subgraph`/`end`) on its own line.
- You may add short connective transitions between clearly separate sections, but do NOT introduce new facts or conclusions absent from the source.
- Preserve the original language (keep Chinese as Chinese, English as English); do NOT translate.
- If the source already has headings, keep their meaning; only fix levels when the hierarchy is inconsistent.

Return ONLY the reorganized full Markdown body. Do NOT wrap it in code fences. Do NOT add any explanation or pre/post text.
