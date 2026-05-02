Review the blog draft as an AI editor reviewer. Use only the supplied draft, metadata, media list, and evidence context. Do not browse. Do not invent evidence IDs or facts.

Return strict JSON only:

{
  "findings": [
    {
      "category": "fact_risk|privacy_path|missing_evidence|weak_title|missing_cover|formula_render_failure|unreferenced_media|missing_alt_text",
      "severity": "error|warning|info",
      "title": "short human-readable issue",
      "detail": "why this matters and what should be reviewed",
      "excerpt": "small exact excerpt when available",
      "location": {"kind": "meta|body|media", "field": "", "src": "", "relative_path": ""},
      "repairable": true,
      "repair_intent": "safe repair intent without inventing facts"
    }
  ]
}

Rules:
- Mark unsupported claims as risk, not as false.
- For evidence issues, only reference evidence IDs supplied in context.
- For privacy, flag local paths, private profile files, secrets, tokens, API keys, and private identifiers.
- Return {"findings": []} when there are no issues.
