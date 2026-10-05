import { Alert, Box, Button, Group, Loader, Modal, ScrollArea, SegmentedControl, Stack, Text, Textarea } from '@mantine/core';
import { IconCheck, IconRefresh } from '@tabler/icons-react';
import DiffMatchPatch from 'diff-match-patch';
import { useMemo } from 'react';

export const REWRITE_LABELS: Record<string, string> = {
  polish: '润色',
  shorten: '精简',
  expand: '扩写',
  tone: '调整语气',
  translate: '翻译',
};

const dmp = new DiffMatchPatch();

/** Inline word-level diff: removed text struck through, added text highlighted. */
export function InlineDiff({ before, after }: { before: string; after: string }) {
  const parts = useMemo(() => {
    const diffs = dmp.diff_main(before, after);
    dmp.diff_cleanupSemantic(diffs);
    return diffs;
  }, [after, before]);
  return (
    <Text size="sm" style={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }} data-testid="content-ai-diff">
      {parts.map(([op, text], index) =>
        op === 0 ? (
          <span key={index}>{text}</span>
        ) : op < 0 ? (
          <span key={index} style={{ color: 'var(--mantine-color-red-4)', textDecoration: 'line-through', opacity: 0.75 }}>
            {text}
          </span>
        ) : (
          <span key={index} style={{ background: 'rgba(64, 192, 87, 0.18)', color: 'var(--mantine-color-green-3)' }}>
            {text}
          </span>
        ),
      )}
    </Text>
  );
}

export interface RewriteState {
  operation: string;
  original: string;
  status: 'running' | 'done' | 'error';
  progress?: string;
  text?: string;
  error?: string;
}

/**
 * Review dialog for a selection rewrite: shows the diff (or the plain
 * candidate), lets the writer tweak the candidate, and only replaces the
 * selection on 接受. Nothing is written while the dialog is open.
 */
export function AIRewriteDialog({
  state,
  view,
  onViewChange,
  onEditCandidate,
  onAccept,
  onRetry,
  onClose,
}: {
  state: RewriteState | null;
  view: 'diff' | 'edit';
  onViewChange: (view: 'diff' | 'edit') => void;
  onEditCandidate: (text: string) => void;
  onAccept: () => void;
  onRetry: () => void;
  onClose: () => void;
}) {
  const label = state ? REWRITE_LABELS[state.operation] ?? state.operation : '';
  return (
    <Modal
      opened={state !== null}
      onClose={onClose}
      title={`AI ${label}`}
      size="xl"
      centered
      data-testid="content-ai-rewrite"
    >
      {state && (
        <Stack gap="md">
          {state.status === 'running' && (
            <Group gap="xs" py="lg" justify="center">
              <Loader size="sm" />
              <Text size="sm" c="dimmed">
                {state.progress || 'AI 正在处理…'}
              </Text>
            </Group>
          )}
          {state.status === 'error' && (
            <Alert color="red" title="AI 改写失败">
              {state.error}
            </Alert>
          )}
          {state.status === 'done' && state.text !== undefined && (
            <>
              <Group justify="space-between">
                <Text size="xs" c="dimmed">
                  候选内容尚未写入正文。确认后替换选中的文字。
                </Text>
                <SegmentedControl
                  size="xs"
                  value={view}
                  onChange={(value) => onViewChange(value as 'diff' | 'edit')}
                  data={[
                    { value: 'diff', label: '对比' },
                    { value: 'edit', label: '编辑候选' },
                  ]}
                />
              </Group>
              {view === 'diff' ? (
                <ScrollArea.Autosize mah="55vh">
                  <Box p="sm" style={{ border: '1px solid var(--mantine-color-dark-5)', borderRadius: 8 }}>
                    <InlineDiff before={state.original} after={state.text} />
                  </Box>
                </ScrollArea.Autosize>
              ) : (
                <Textarea
                  aria-label="AI 候选"
                  autosize
                  minRows={6}
                  maxRows={20}
                  value={state.text}
                  onChange={(event) => onEditCandidate(event.currentTarget.value)}
                />
              )}
            </>
          )}
          <Group justify="space-between">
            <Button
              variant="subtle"
              leftSection={<IconRefresh size={14} />}
              onClick={onRetry}
              disabled={state.status === 'running'}
            >
              重新生成
            </Button>
            <Group gap="xs">
              <Button variant="default" onClick={onClose}>
                {state.status === 'done' ? '拒绝' : '取消'}
              </Button>
              <Button
                leftSection={<IconCheck size={15} />}
                onClick={onAccept}
                disabled={state.status !== 'done' || !state.text?.trim()}
                data-testid="content-ai-accept"
              >
                接受并替换
              </Button>
            </Group>
          </Group>
        </Stack>
      )}
    </Modal>
  );
}
