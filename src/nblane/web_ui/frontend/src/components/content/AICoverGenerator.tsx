import { Button, Paper, Stack, Text } from '@mantine/core';
import type { ImageEditRequest } from './imageTypes';

/** Entry point only; the article-level workspace owns tasks and candidates. */
export function AICoverGenerator({ enabled, cover, onOpen }: {
  enabled: boolean; cover: string; onOpen: (request: ImageEditRequest | null) => void;
}) {
  return <Paper withBorder p="sm" radius="md" data-testid="content-ai-cover">
    <Stack gap="sm">
      <Text size="sm" fw={600}>AI 图片</Text>
      {!enabled && <Text size="xs" c="dimmed">未配置图像服务，可查看已有候选。</Text>}
      <Button mih={44} variant="light" disabled={!enabled} onClick={() => onOpen({ mode: 'cover', reference: '', target: { kind: 'cover', source: cover } })} data-testid="content-ai-cover-run">生成封面</Button>
      {cover && <Button mih={44} variant="default" disabled={!enabled} onClick={() => onOpen({ mode: 'edit', reference: cover, target: { kind: 'cover', source: cover } })}>修改当前封面</Button>}
    </Stack>
  </Paper>;
}
