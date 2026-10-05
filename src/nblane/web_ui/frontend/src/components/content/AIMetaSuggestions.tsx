import { Alert, Badge, Button, Group, Loader, Paper, Stack, Text, UnstyledButton } from '@mantine/core';
import { IconSparkles } from '@tabler/icons-react';
import { useEffect, useRef, useState } from 'react';

import type { ContentMetaResult } from '../../api/types';
import { runContentJob, type ContentJobHandle } from './contentJobs';

/**
 * AI title / summary / tag candidates. Each candidate is a click-to-apply
 * chip; nothing is written until the writer picks one (then autosave runs).
 */
export function AIMetaSuggestions({
  profile,
  enabled,
  draft,
  onApply,
  compact = false,
}: {
  profile: string;
  enabled: boolean;
  draft: { title: string; summary: string; tags: string[]; body: string };
  onApply: (patch: { title?: string; summary?: string; tags?: string[] }) => void;
  /** Summary-only variant for the publish dialog. */
  compact?: boolean;
}) {
  const [result, setResult] = useState<ContentMetaResult | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState('');
  const jobRef = useRef<ContentJobHandle<ContentMetaResult> | null>(null);

  useEffect(() => () => jobRef.current?.cancel(), []);

  const run = () => {
    jobRef.current?.cancel();
    setRunning(true);
    setError('');
    const job = runContentJob<ContentMetaResult>(profile, 'content-meta', {
      title: draft.title,
      summary: draft.summary,
      tags: draft.tags,
      body: draft.body,
    });
    jobRef.current = job;
    job.result
      .then(setResult)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setRunning(false));
  };

  const pick = (label: string, values: string[], apply: (value: string) => void, testid: string) =>
    values.length > 0 && (
      <Stack gap={4}>
        <Text size="xs" c="dimmed">
          {label}
        </Text>
        {values.map((value) => (
          <UnstyledButton
            key={value}
            onClick={() => apply(value)}
            data-testid={testid}
            style={{
              padding: '6px 10px',
              borderRadius: 6,
              border: '1px solid var(--mantine-color-dark-4)',
              fontSize: 13,
              lineHeight: 1.5,
            }}
          >
            {value}
          </UnstyledButton>
        ))}
      </Stack>
    );

  const newTags = result ? result.tags.filter((tag) => !draft.tags.includes(tag)) : [];

  return (
    <Paper withBorder p="sm" radius="md" data-testid="content-ai-meta">
      <Stack gap="sm">
        <Group justify="space-between" wrap="nowrap">
          <Text size="sm" fw={600}>
            {compact ? 'AI 写摘要' : 'AI 标题与摘要建议'}
          </Text>
          <Button
            size="compact-xs"
            variant="light"
            leftSection={running ? <Loader size={10} /> : <IconSparkles size={13} />}
            onClick={run}
            disabled={!enabled || running}
            data-testid="content-ai-meta-run"
          >
            {result ? '重新生成' : '生成'}
          </Button>
        </Group>
        {!enabled && (
          <Text size="xs" c="dimmed">
            未配置 LLM，AI 建议不可用。
          </Text>
        )}
        {error && (
          <Alert color="red" p="xs">
            <Text size="xs">{error}</Text>
          </Alert>
        )}
        {result && (
          <>
            {pick('点选替换摘要', result.summaries, (summary) => onApply({ summary }), 'content-ai-summary')}
            {!compact && pick('点选替换标题', result.titles, (title) => onApply({ title }), 'content-ai-title')}
            {!compact && newTags.length > 0 && (
              <Stack gap={4}>
                <Text size="xs" c="dimmed">
                  点选添加标签
                </Text>
                <Group gap={6}>
                  {newTags.map((tag) => (
                    <Badge
                      key={tag}
                      variant="outline"
                      style={{ cursor: 'pointer', textTransform: 'none' }}
                      onClick={() => onApply({ tags: [...draft.tags, tag] })}
                      data-testid="content-ai-tag"
                    >
                      + {tag}
                    </Badge>
                  ))}
                </Group>
              </Stack>
            )}
          </>
        )}
      </Stack>
    </Paper>
  );
}
