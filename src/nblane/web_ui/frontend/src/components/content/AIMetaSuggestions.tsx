import { Alert, Button, Group, Loader, Paper, Stack, Text, UnstyledButton } from '@mantine/core';
import { IconSparkles } from '@tabler/icons-react';
import { useState } from 'react';

import type { ContentMetaResult } from '../../api/types';
import { runContentJob } from './contentJobs';
import { useContentJob } from './useContentJob';

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
  const job = useContentJob<ContentMetaResult>();
  const { running, error, progress } = job;

  const run = async () => {
    const outcome = await job.start((onProgress) =>
      runContentJob<ContentMetaResult>(
        profile,
        'content-meta',
        { title: draft.title, summary: draft.summary, tags: draft.tags, body: draft.body },
        onProgress,
      ),
    );
    if (outcome.status === 'done') setResult(outcome.value);
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
            onClick={() => void run()}
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
        {running && (
          <Text size="xs" c="dimmed" role="status" aria-live="polite">
            {progress || 'AI 正在读全文…'}
          </Text>
        )}
        {error && (
          <Alert color="red" p="xs">
            <Text size="xs">{error}</Text>
          </Alert>
        )}
        {result && (
          <>
            {result.truncated && (
              <Text size="xs" c="dimmed">
                文章较长，建议依据提纲、开头和结尾生成。
              </Text>
            )}
            {pick('点选替换摘要', result.summaries, (summary) => onApply({ summary }), 'content-ai-summary')}
            {!compact && pick('点选替换标题', result.titles, (title) => onApply({ title }), 'content-ai-title')}
            {!compact && newTags.length > 0 && (
              <Stack gap={4}>
                <Text size="xs" c="dimmed">
                  点选添加标签
                </Text>
                <Group gap={6}>
                  {newTags.map((tag) => (
                    <Button
                      key={tag}
                      size="compact-xs"
                      variant="outline"
                      radius="xl"
                      aria-label={`添加标签 ${tag}`}
                      onClick={() => onApply({ tags: [...draft.tags, tag] })}
                      data-testid="content-ai-tag"
                    >
                      + {tag}
                    </Button>
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
