export type EditorAction =
  | "markdown_changed"
  | "layout_state_changed"
  | "insert_media"
  | "delete_media"
  | "convert_media_video"
  | "insert_candidate"
  | "apply_candidate_meta"
  | "select_post"
  | "filter_posts"
  | "create_post"
  | "draft_from_evidence"
  | "draft_from_done"
  | "generate_ai_candidate"
  | "ai_inline_action"
  | "ai_stream_poll"
  | "cancel_ai_stream"
  | "apply_ai_patch"
  | "reject_ai_patch"
  | "upload_media"
  | "generate_visual_asset"
  | "generate_cover_image"
  | "save_visual_candidate"
  | "discard_visual_candidate"
  | "load_media_preview_detail"
  | "preview_post"
  | "run_check"
  | "request_reviewer_repair"
  | "save_post"
  | "publish_request";

export interface BlockNoteBlock {
  id?: string;
  type: string;
  props?: Record<string, unknown>;
  content?: unknown;
  children?: BlockNoteBlock[];
  [key: string]: unknown;
}

export interface EditorEventPayload {
  slug?: string;
  document_id?: string;
  markdown?: string;
  blocks_json?: BlockNoteBlock[];
  meta?: Record<string, unknown>;
  layout_state?: Record<string, unknown>;
  dirty?: boolean;
  selected_block?: Record<string, unknown> | null;
  patch_id?: string;
  patch?: Record<string, unknown>;
  finding_id?: string;
  finding?: Record<string, unknown>;
  event_id?: string;
  [key: string]: unknown;
}

export interface EditorEvent {
  action?: EditorAction | null;
  event_id?: string;
  payload?: EditorEventPayload;
  markdown?: string;
  blocks_json?: BlockNoteBlock[];
  dirty?: boolean;
  layout_state?: Record<string, unknown>;
  selected_block?: Record<string, unknown> | null;
  insert_event?: Record<string, unknown> | null;
  [key: string]: unknown;
}
