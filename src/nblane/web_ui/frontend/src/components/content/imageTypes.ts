export interface ImageTarget {
  kind: 'block' | 'cover' | 'media';
  block_id?: string;
  source?: string;
  fingerprint?: string;
}
export interface ImageEditRequest {
  mode: 'edit' | 'cover';
  reference: string;
  target: ImageTarget;
  instruction?: string;
  quality?: 'standard' | 'high' | 'ultra';
  aspect?: 'original' | '16:9' | '1:1' | '4:3' | '3:4' | '9:16';
}
export interface ImageRun {
  id: string;
  slug: string;
  request: ImageEditRequest & { title?: string; summary?: string; tags?: string[]; body?: string };
  status: 'running' | 'done' | 'failed';
  created_at: number;
  reference: string;
  error: string;
  output_size?: string;
  candidates: Array<{ candidate_path: string; filename: string; applied_path: string }>;
}
export interface SelectedImage { id: string; source: string; fingerprint: string }
