import {
  Button,
  Group,
  Loader,
  Modal,
  Stack,
  Text,
  Textarea,
} from '@mantine/core';
import {
  IconChecklist,
  IconCircleCheck,
  IconCircleX,
  IconRefresh,
  IconRocket,
} from '@tabler/icons-react';

import type { StudioValidationResponse } from '../../api/types';
import { AIMetaSuggestions } from './AIMetaSuggestions';
import { checkMessage, isMissingSummary, type PostDraft } from './contentDraft';

export function PublishDialog({
  opened,
  profile,
  aiText,
  draft,
  result,
  checking,
  stale,
  publishing,
  blocked,
  onClose,
  onRecheck,
  onEditSummary,
  onApplySummary,
  onConfirm,
}: {
  opened: boolean;
  profile: string;
  aiText: boolean;
  draft: PostDraft;
  result: StudioValidationResponse | null;
  checking: boolean;
  stale: boolean;
  publishing: boolean;
  blocked: boolean;
  onClose: () => void;
  onRecheck: () => void;
  onEditSummary: (value: string) => void;
  onApplySummary: (value: string) => void;
  onConfirm: () => void;
}) {
  const errors = result?.errors ?? [];
  const warnings = result?.warnings ?? [];
  const needsSummary = errors.some(isMissingSummary);
  const ready = !!result?.ok && !stale && !checking;
  return (
    <Modal opened={opened} onClose={onClose} title="发布文章" centered size="lg" data-testid="content-publish-dialog">
      <Stack gap="md">
        <Text size="sm" c="dimmed">
          发布后文章进入公开层；在「公开站点」发布到线上后才会出现在网站上。
        </Text>
        {checking || !result ? (
          <Group gap="xs">
            <Loader size="xs" />
            <Text size="sm">正在检查…</Text>
          </Group>
        ) : (
          <Stack gap={6} data-testid="content-check-result">
            {errors.map((item) => (
              <Group key={item} gap="xs" wrap="nowrap" align="flex-start">
                <IconCircleX size={18} color="var(--mantine-color-red-5)" style={{ flexShrink: 0 }} />
                <Text size="sm">{checkMessage(item)}</Text>
              </Group>
            ))}
            {warnings.map((item) => (
              <Group key={item} gap="xs" wrap="nowrap" align="flex-start">
                <IconChecklist size={18} color="var(--mantine-color-yellow-5)" style={{ flexShrink: 0 }} />
                <Text size="sm" c="dimmed">
                  {checkMessage(item)}
                </Text>
              </Group>
            ))}
            {result.ok && (
              <Group gap="xs">
                <IconCircleCheck size={18} color="var(--mantine-color-green-5)" />
                <Text size="sm">{stale ? '内容有改动，请重新检查。' : '检查通过，可以发布。'}</Text>
              </Group>
            )}
          </Stack>
        )}
        {needsSummary && (
          <Textarea
            label="摘要"
            description="一两句话说明这篇文章讲什么"
            autosize
            minRows={2}
            value={draft.summary}
            onChange={(event) => onEditSummary(event.currentTarget.value)}
            data-autofocus
          />
        )}
        {needsSummary && (
          <AIMetaSuggestions
            profile={profile}
            enabled={aiText}
            draft={draft}
            compact
            onApply={(patch) => patch.summary && onApplySummary(patch.summary)}
          />
        )}
        <Group justify="space-between">
          <Button variant="subtle" leftSection={<IconRefresh size={14} />} onClick={onRecheck} loading={checking}>
            重新检查
          </Button>
          <Group gap="xs">
            <Button variant="default" onClick={onClose}>
              取消
            </Button>
            <Button
              color="green"
              leftSection={<IconRocket size={15} />}
              disabled={!ready || blocked}
              loading={publishing}
              onClick={onConfirm}
              data-testid="content-publish-confirm"
            >
              确认发布
            </Button>
          </Group>
        </Group>
      </Stack>
    </Modal>
  );
}
