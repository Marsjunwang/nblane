import type { SelectedImage } from './imageTypes';

type Block = { id?: string; type?: string; props?: Record<string, unknown>; children?: Block[] };

export function selectedImages(blocks: Block[]): SelectedImage[] {
  return blocks.flatMap((block) => {
    const props = block.props ?? {};
    const source = block.type === 'image' ? String(props.url ?? '')
      : block.type === 'visual_block' && props.asset_type === 'image' ? String(props.src ?? '') : '';
    const own = source && block.id ? [{ id: block.id, source, fingerprint: JSON.stringify(props) }] : [];
    return [...own, ...selectedImages(block.children ?? [])];
  });
}

/** Reject media in text candidates before *any* editor transaction is applied. */
export function containsMedia(blocks: Block[]): boolean {
  return blocks.some((block) => ['image', 'visual_block', 'video_block', 'video', 'audio', 'file', 'ai_loading_block'].includes(block.type ?? '') || containsMedia(block.children ?? []));
}
