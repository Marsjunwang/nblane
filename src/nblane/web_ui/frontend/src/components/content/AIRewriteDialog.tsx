import { Alert, Box, Button, Group, Loader, Modal, ScrollArea, SegmentedControl, Stack, Text, Textarea, VisuallyHidden } from '@mantine/core';
import { useMediaQuery } from '@mantine/hooks';
import { IconCheck, IconCopy, IconRefresh } from '@tabler/icons-react';
import DiffMatchPatch from 'diff-match-patch';
import { useMemo } from 'react';

import { AI_REWRITE_MENU } from '../rewriteOperations';

/** Dialog titles follow the toolbar menu, so the two never disagree. */
export const REWRITE_LABELS: Record<string, string> = Object.fromEntries(
  AI_REWRITE_MENU.map((item) => [item.operation, item.label]),
);

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
          <del key={index} style={{ color: 'var(--mantine-color-red-4)', textDecoration: 'line-through', opacity: 0.75 }}>
            <VisuallyHidden>删除：</VisuallyHidden>
            {text}
          </del>
        ) : (
          <ins
            key={index}
            style={{ background: 'rgba(64, 192, 87, 0.18)', color: 'var(--mantine-color-green-3)', textDecoration: 'underline' }}
          >
            <VisuallyHidden>新增：</VisuallyHidden>
            {text}
          </ins>
        ),
      )}
    </Text>
  );
}

export interface RewriteState {
  parts?: string[];
  originals?: string[];
  operation: string;
  original: string;
  status: 'running' | 'done' | 'error';
  progress?: string;
  text?: string;
  error?: string;
  /** Why the last 接受并替换 wrote nothing; the candidate stays for copy/retry. */
  acceptError?: string;
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
  onEditPart,
  onAccept,
  onRetry,
  onClose,
  onCopy,
}: {
  state: RewriteState | null;
  view: 'diff' | 'edit';
  onViewChange: (view: 'diff' | 'edit') => void;
  onEditCandidate: (text: string) => void;
  onEditPart?: (index: number, text: string) => void;
  onAccept: () => void;
  onRetry: () => void;
  onClose: () => void;
  onCopy?: () => void;
}) {
  const label = state ? REWRITE_LABELS[state.operation] ?? state.operation : '';
  // On a phone the xl dialog pushed 接受并替换 off screen: go full screen with
  // a scrolling body and a footer that stays put.
  const mobile = useMediaQuery('(max-width: 48em)') ?? false;
  return (
    <Modal
      opened={state !== null}
      onClose={onClose}
      title={`AI ${label}`}
      size="xl"
      centered={!mobile}
      fullScreen={mobile}
      data-testid="content-ai-rewrite"
    >
      {state && (
        <Stack gap="md">
          {state.status === 'running' && (
            <Group gap="xs" py="lg" justify="center" role="status" aria-live="polite">
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
              {state.parts ? <ScrollArea.Autosize mah={mobile ? 'calc(100dvh - 220px)' : '55vh'}><Stack>
                <Text size="xs" c="dimmed">仅改写文字；图片及顺序保持不变。各文字区域分别确认。</Text>
                {state.parts.map((part, index) => <Box key={index}>
                  <Text size="xs" c="dimmed">文字区域 {index + 1}</Text>
                  {view === 'diff' ? <InlineDiff before={state.originals?.[index] ?? ''} after={part} /> : <Textarea aria-label={`AI 候选区域 ${index + 1}`} value={part} onChange={(event) => onEditPart?.(index, event.currentTarget.value)} autosize minRows={2} />}
                </Box>)}
              </Stack></ScrollArea.Autosize> : view === 'diff' ? (
                <ScrollArea.Autosize mah={mobile ? 'calc(100dvh - 220px)' : '55vh'}>
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
          {state.status === 'done' && state.acceptError && (
            <Alert color="yellow" title="未替换，候选已保留" role="alert" data-testid="content-ai-accept-error">
              {state.acceptError}
            </Alert>
          )}
          <Group
            justify="space-between"
            gap="xs"
            style={
              mobile
                ? { position: 'sticky', bottom: 0, background: 'var(--mantine-color-body)', paddingBlock: 8, zIndex: 1 }
                : undefined
            }
          >
            <Button
              variant="subtle"
              leftSection={<IconRefresh size={14} />}
              onClick={onRetry}
              disabled={state.status === 'running'}
            >
              重新生成
            </Button>
            <Group gap="xs" wrap="wrap" justify="flex-end">
              {state.status === 'done' && onCopy && (
                <Button variant="default" leftSection={<IconCopy size={14} />} onClick={onCopy} disabled={!state.text?.trim()}>
                  复制候选
                </Button>
              )}
              <Button variant="default" onClick={onClose}>
                {state.status === 'done' ? '拒绝' : '取消'}
              </Button>
              <Button
                leftSection={<IconCheck size={15} />}
                onClick={onAccept}
                disabled={state.status !== 'done' || !state.text?.trim() || state.parts?.some((part) => !part.trim())}
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
