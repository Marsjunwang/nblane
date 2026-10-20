import { Button, Group, Text } from '@mantine/core';
import { notifications } from '@mantine/notifications';

import { fieldsLabel, type AIField } from './aiUndo';

/** How long the 撤销 offer stays on screen. */
export const AI_UNDO_MS = 8000;

/** Toast offering 撤销 after AI-filled fields were applied. */
export function showAIUndo(fields: AIField[], onUndo: () => void): void {
  const id = `ai-undo-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  notifications.show({
    id,
    color: 'blue',
    autoClose: AI_UNDO_MS,
    message: (
      <Group justify="space-between" wrap="nowrap" gap="xs">
        <Text size="sm">已用 AI 建议替换{fieldsLabel(fields)}。</Text>
        <Button
          size="compact-xs"
          variant="light"
          onClick={() => {
            notifications.hide(id);
            onUndo();
          }}
        >
          撤销
        </Button>
      </Group>
    ),
  });
}
