import { z } from "zod";

const AnyRecord = z.record(z.string(), z.unknown());

export const EditorEventSchema = z
  .object({
    action: z.string().nullable().optional(),
    event_id: z.string().optional(),
    payload: AnyRecord.optional(),
    markdown: z.string().optional(),
    blocks_json: z.array(AnyRecord).optional(),
    dirty: z.boolean().optional(),
    layout_state: AnyRecord.optional(),
    selected_block: z.unknown().optional(),
    insert_event: z.unknown().optional(),
  })
  .passthrough();

export function validateEditorEvent(value) {
  const result = EditorEventSchema.safeParse(value);
  if (result.success) {
    return result.data;
  }
  // Keep the editor usable if validation catches an unexpected extension.
  console.warn("Invalid nblane editor event", result.error.flatten());
  return value;
}
