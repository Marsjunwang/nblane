import { Box, Group, ScrollArea, Text } from '@mantine/core';
import type { ReactNode } from 'react';

import { inscription } from '../theme';

/**
 * 铭文卡 — shared detail-card shell (evidence detail now; home detail card
 * from Phase 3). Visual language: deep ground, thin gold edge, Kai-style
 * serif title, Ming-style serif body. Tool pages stay efficiency-first, so
 * the shell is deliberately restrained: header row + scrollable body.
 */
export function InscriptionCard({
  title,
  aside,
  children,
  testId,
}: {
  title: string;
  /** Badges/actions rendered at the right of the title row. */
  aside?: ReactNode;
  children: ReactNode;
  testId?: string;
}) {
  return (
    <Box
      data-testid={testId ?? 'inscription-card'}
      style={{
        background: inscription.background,
        border: `1px solid ${inscription.borderColor}`,
        borderRadius: 12,
        padding: '16px 20px',
        color: inscription.bodyColor,
        fontFamily: inscription.bodyFontFamily,
      }}
    >
      <Group justify="space-between" align="flex-start" wrap="nowrap" mb="sm">
        <Text
          fw={600}
          size="lg"
          style={{
            color: inscription.titleColor,
            fontFamily: inscription.titleFontFamily,
            wordBreak: 'break-word',
            minWidth: 0,
          }}
        >
          {title}
        </Text>
        {aside && <Box style={{ flexShrink: 0 }}>{aside}</Box>}
      </Group>
      <ScrollArea.Autosize mah="70vh">{children}</ScrollArea.Autosize>
    </Box>
  );
}

/** One labelled row inside an inscription card (label in dim, value body). */
export function InscriptionRow({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <Group gap="xs" align="baseline" wrap="nowrap" py={2}>
      <Text
        size="sm"
        w={72}
        style={{ flexShrink: 0, color: inscription.dimColor }}
      >
        {label}
      </Text>
      <Box
        style={{
          flex: 1,
          minWidth: 0,
          fontSize: 14,
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
        }}
      >
        {children}
      </Box>
    </Group>
  );
}
