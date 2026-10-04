import { Alert, Badge, Button, Center, Group, Loader, Progress, Stack, Text, Title } from '@mantine/core';
import { IconArrowLeft, IconExternalLink } from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { useResearch, useResearchReader } from '../api/hooks';
import { SidecarFrame } from '../components/SidecarFrame';

export function PaperReaderPage() {
  const { name = '', sourceId = '' } = useParams();
  const [searchParams] = useSearchParams();
  const research = useResearch(name);
  const reader = useResearchReader(name, sourceId);
  const sidecarInfo = research.data?.sidecar;
  const requestedMode = searchParams.get('mode') ?? 'pdf';
  const mode = ['pdf', 'translation', 'compare'].includes(requestedMode) ? requestedMode : 'pdf';
  const paper = (research.data?.papers ?? []).find((item) => item.id === sourceId);
  const [readerState, setReaderState] = useState({ mode, page: paper?.last_page ?? 0, totalPages: paper?.page_count ?? 0 });

  useEffect(() => setReaderState((state) => ({ ...state, mode })), [mode]);

  useEffect(() => {
    if (!sidecarInfo) return undefined;
    const expectedOrigin = sidecarInfo.base
      ? new URL(sidecarInfo.base, window.location.href).origin
      : window.location.origin;
    const onReaderMessage = (event: MessageEvent) => {
      if (event.origin !== expectedOrigin) return;
      const data = event.data as { type?: string; source_id?: string; mode?: string; page?: number; total_pages?: number } | null;
      if (!data || data.type !== 'nblane.reader.state' || data.source_id !== sourceId) return;
      const nextMode = data.mode;
      if (!nextMode || !['pdf', 'translation', 'compare'].includes(nextMode)) return;
      setReaderState((state) => ({
        mode: nextMode,
        page: Number(data.page || state.page || 0),
        totalPages: Number(data.total_pages || state.totalPages || 0),
      }));
      if (searchParams.get('mode') === nextMode) return;
      const next = new URLSearchParams(window.location.search);
      next.set('mode', nextMode);
      window.history.replaceState(window.history.state, '', `${window.location.pathname}?${next.toString()}`);
    };
    window.addEventListener('message', onReaderMessage);
    return () => window.removeEventListener('message', onReaderMessage);
  }, [searchParams, sidecarInfo?.base, sourceId]);

  if (research.isPending || reader.isPending) return <Center py="xl"><Loader /></Center>;
  if (research.isError) return <Alert color="red" title="加载失败">{research.error.message}</Alert>;
  if (reader.isError) return <Alert color="red" title="Reader 打开失败">{reader.error.message}</Alert>;
  if (!reader.data) return <Alert color="red" title="Reader 打开失败">未能获取 Reader 会话。</Alert>;

  const sidecar = sidecarInfo;
  if (!sidecar) return <Alert color="yellow" title="Reader 不可用">当前环境没有配置 Reader API。</Alert>;

  const query = new URLSearchParams(searchParams);
  query.set('profile', name);
  if (sourceId) query.set('source_id', sourceId);
  query.set('mode', mode);
  query.set('ui_lang', 'zh');
  const readerUrl = `${reader.data.reader_url}${query.toString() ? `&${query.toString()}` : ''}`;
  const externalQuery = new URLSearchParams(query);
  externalQuery.set('mode', readerState.mode);
  const externalReaderUrl = `${reader.data.reader_url}${externalQuery.toString() ? `&${externalQuery.toString()}` : ''}`;
  const progress = readerState.totalPages > 0 && readerState.page > 0
    ? Math.min(100, Math.round((readerState.page / readerState.totalPages) * 100))
    : 0;


  return (
    <Stack gap="md">
      <Group justify="space-between" align="flex-start" wrap="nowrap">
        <div>
          <Button component={Link} to={`/p/${encodeURIComponent(name)}/research`} variant="subtle" size="compact-sm" leftSection={<IconArrowLeft size={15} />}>
            返回研究台
          </Button>
          <Text size="xs" tt="uppercase" fw={700} c="brand" mt="md">Reading session</Text>
          <Title order={2} mt={4} lineClamp={2}>{paper?.title || sourceId}</Title>
          <Group gap="xs" mt="xs">
            <Badge variant="light" color="yellow">{paper?.status === 'reading' ? '阅读中' : '待读'}</Badge>
            <Badge variant="light" color={paper?.pdf_available ? 'green' : 'gray'}>{paper?.pdf_available ? 'PDF 已就绪' : 'PDF 不可用'}</Badge>
            <Badge variant="outline">{readerState.page > 0 ? `第 ${readerState.page} / ${readerState.totalPages || paper?.page_count || '?'} 页` : '尚未开始'}</Badge>
          </Group>
        </div>
        <Stack align="flex-end" gap="xs">
          <Button component="a" href={externalReaderUrl} target="_blank" rel="noreferrer" variant="default" size="compact-sm" leftSection={<IconExternalLink size={14} />}>新标签打开</Button>
          <Text size="xs" c="dimmed">Reader 会自动保存阅读位置</Text>
        </Stack>
      </Group>
      <Group gap="sm" align="center">
        <Progress value={progress} flex={1} size={5} color="brand" />
        <Text size="xs" c="dimmed" w={42} ta="right">{progress ? `${progress}%` : '—'}</Text>
      </Group>
      <SidecarFrame
        title={paper?.title || 'Paper Reader'}
        url={readerUrl}
        base={sidecar.base}
        handoffToken={sidecar.handoff_token}
        readyMessageType="nblane.reader.ready"
        height="calc(100vh - 220px)"
      />
    </Stack>
  );
}
