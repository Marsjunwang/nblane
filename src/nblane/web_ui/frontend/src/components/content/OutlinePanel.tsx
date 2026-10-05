import { Box, ScrollArea, Text, UnstyledButton } from '@mantine/core';

import type { OutlineItem } from './contentDraft';

/**
 * Document outline (H1–H3). Clicking an entry scrolls the editor to that
 * heading; the entry nearest the caret is highlighted.
 */
export function OutlinePanel({
  items,
  activeId,
  onJump,
}: {
  items: OutlineItem[];
  activeId: string;
  onJump: (id: string) => void;
}) {
  if (!items.length) {
    return (
      <Text size="xs" c="dimmed" p="md" data-testid="content-outline-empty">
        用 # 标题分段后，这里会显示文档目录。
      </Text>
    );
  }
  return (
    <ScrollArea.Autosize mah="calc(100vh - 56px - 52px - 48px)" offsetScrollbars data-testid="content-outline">
      <Box py="xs">
        {items.map((item) => {
          const active = item.id === activeId;
          return (
            <UnstyledButton
              key={item.id}
              onClick={() => onJump(item.id)}
              data-testid="content-outline-item"
              data-active={active || undefined}
              style={{
                display: 'block',
                width: '100%',
                padding: '4px 10px',
                paddingLeft: 10 + (item.level - 1) * 14,
                borderLeft: `2px solid ${active ? 'var(--mantine-color-brand-5)' : 'transparent'}`,
                color: active ? 'var(--mantine-color-brand-4)' : 'var(--mantine-color-dark-1)',
              }}
            >
              <Text size="xs" lineClamp={2} fw={active ? 600 : 400}>
                {item.text}
              </Text>
            </UnstyledButton>
          );
        })}
      </Box>
    </ScrollArea.Autosize>
  );
}
