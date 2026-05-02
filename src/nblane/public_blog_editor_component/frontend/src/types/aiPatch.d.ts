export type AIOperation =
  | "polish"
  | "rewrite"
  | "shorten"
  | "expand"
  | "continue"
  | "translate"
  | "tone"
  | "outline"
  | "expand_section"
  | "formula"
  | "visual"
  | "meta"
  | "check";

export interface AIPatch {
  patch_id?: string;
  ai_source_id?: string;
  operation: AIOperation;
  target?: Record<string, unknown>;
  meta_patch?: Record<string, unknown>;
  block_patches?: Array<Record<string, unknown>>;
  markdown_fallback?: string;
  assets?: Array<Record<string, unknown>>;
  warnings?: string[];
  citations?: Array<Record<string, unknown>>;
  provenance?: Record<string, unknown>;
  [key: string]: unknown;
}
