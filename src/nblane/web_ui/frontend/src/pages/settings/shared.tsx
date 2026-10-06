// Shared building blocks for the Settings sections.

import { Alert, Button, Card, Group, Paper, Stack, Text, Title } from '@mantine/core';
import { IconDeviceFloppy } from '@tabler/icons-react';
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';

import { chrome } from '../../theme';

export function ErrorAlert({ error }: { error: Error | null | undefined }) {
  if (!error) return null;
  return <Alert color="red" title="操作失败">{error.message}</Alert>;
}

/** One settings card: icon + title + one-line description, then content. */
export function SettingsCard({ icon, title, description, children }: { icon: ReactNode; title: string; description: string; children: ReactNode }) {
  return (
    <Card withBorder radius="md" padding="lg">
      <Stack gap="md">
        <Group gap="sm" align="flex-start" wrap="nowrap">
          {icon}
          <div>
            <Title order={3}>{title}</Title>
            <Text size="sm" c="dimmed">{description}</Text>
          </div>
        </Group>
        {children}
      </Stack>
    </Card>
  );
}

export function formatGb(bytes: number): string {
  return `${(bytes / 1e9).toFixed(2)} GB`;
}

export function formatMb(mb: number): string {
  return mb >= 1024 ? `${(mb / 1024).toFixed(1)} GB` : `${mb} MB`;
}

export function settingString(settings: Record<string, unknown> | undefined, key: string): string {
  const value = settings?.[key];
  return value === undefined || value === null ? '' : String(value);
}

export function preferenceString(preferences: Record<string, unknown> | undefined, ...path: string[]): string {
  let value: unknown = preferences;
  for (const segment of path) {
    if (!value || typeof value !== 'object') return '';
    value = (value as Record<string, unknown>)[segment];
  }
  return value === undefined || value === null ? '' : String(value);
}

/**
 * Local edit buffer for one settings form. The draft resets whenever the
 * server value changes (load, save, profile switch); `dirty` drives the
 * save bar and the leave-page guard.
 */
export function useDraft<T>(source: T) {
  const key = JSON.stringify(source);
  const [draft, setDraft] = useState<T>(source);
  useEffect(() => {
    setDraft(JSON.parse(key) as T);
  }, [key]);
  return {
    draft,
    setDraft,
    dirty: JSON.stringify(draft) !== key,
    reset: () => setDraft(JSON.parse(key) as T),
  };
}

/** The Settings shell listens for unsaved edits to guard navigation. */
export const SettingsDirtyContext = createContext<(dirty: boolean) => void>(() => {});

export function useReportDirty(dirty: boolean) {
  const report = useContext(SettingsDirtyContext);
  useEffect(() => {
    report(dirty);
    return () => report(false);
  }, [dirty, report]);
}

export function SaveBar({ dirty, saving, error, onSave, onDiscard }: { dirty: boolean; saving: boolean; error?: Error | null; onSave: () => void; onDiscard: () => void }) {
  if (!dirty) return null;
  return (
    <Paper withBorder radius="md" p="sm" role="region" aria-label="未保存的修改" style={{ position: 'sticky', bottom: 16, zIndex: 5, background: chrome.panelBg, borderColor: chrome.gold }}>
      <Group justify="space-between" wrap="nowrap">
        <Text size="sm">有未保存的修改</Text>
        <Group gap="xs" wrap="nowrap">
          <Button size="xs" variant="default" disabled={saving} onClick={onDiscard}>放弃</Button>
          <Button size="xs" leftSection={<IconDeviceFloppy size={14} />} loading={saving} onClick={onSave}>保存</Button>
        </Group>
      </Group>
      {error && <Text size="xs" c="red" mt={6}>{error.message}</Text>}
    </Paper>
  );
}
