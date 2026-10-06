// Reader page (/research/papers/:sourceId/read): one slim bar + the sidecar
// Reader iframe. The sidecar toolbar already shows the paper title and the
// reading controls, so the SPA keeps only navigation (back to the overview),
// a truncated breadcrumb, page progress and "open in new tab". The page is
// sized to the viewport so the iframe is the only scroller.

import { ActionIcon, Alert, Anchor, Box, Button, Center, Group, Loader, Stack, Text, Tooltip } from '@mantine/core';
import { IconArrowLeft, IconExternalLink, IconRefresh } from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';

import { useResearch, useResearchReader } from '../api/hooks';
import { paperOverviewPath, paperReaderPath, sidecarOrigin } from '../api/paperHooks';
import { SidecarFrame } from '../components/SidecarFrame';
import { chrome } from '../theme';

const READER_MODES = ['pdf', 'translation', 'compare'];
const MODE_LABELS: Record<string, string> = { pdf: '原文', translation: '仅译文', compare: '对照' };
// AppShell header (56) + AppShell.Main vertical padding (md = 16 × 2).
const SHELL_OFFSET_PX = 56 + 32;
const BAR_HEIGHT_PX = 40;

export function PaperReaderPage() {
  const { name = '', sourceId = '' } = useParams();
  const [searchParams] = useSearchParams();
  const research = useResearch(name);
  const reader = useResearchReader(name, sourceId);
  const sidecarInfo = research.data?.sidecar;
  const requestedMode = searchParams.get('mode') ?? 'pdf';
  const mode = READER_MODES.includes(requestedMode) ? requestedMode : 'pdf';
  const paper = (research.data?.papers ?? []).find((item) => item.id === sourceId);
  const initialPage = Number(searchParams.get('page') || 0) || paper?.last_page || 0;
  const [readerState, setReaderState] = useState({ mode, page: initialPage, totalPages: paper?.page_count ?? 0 });
  const [reloadSignal, setReloadSignal] = useState(0);

  useEffect(() => setReaderState((state) => ({ ...state, mode })), [mode]);
  useEffect(() => {
    if (!paper) return;
    setReaderState((state) => ({
      ...state,
      page: state.page || paper.last_page || 0,
      totalPages: state.totalPages || paper.page_count || 0,
    }));
  }, [paper?.last_page, paper?.page_count]);

  useEffect(() => {
    if (!sidecarInfo) return undefined;
    const expectedOrigin = sidecarOrigin(sidecarInfo.base);
    const onReaderMessage = (event: MessageEvent) => {
      if (event.origin !== expectedOrigin) return;
      const data = event.data as { type?: string; source_id?: string; mode?: string; page?: number; total_pages?: number } | null;
      if (!data || data.type !== 'nblane.reader.state' || data.source_id !== sourceId) return;
      const nextMode = data.mode;
      if (!nextMode || !READER_MODES.includes(nextMode)) return;
      const nextPage = Number(data.page || 0);
      setReaderState((state) => ({
        mode: nextMode,
        page: nextPage || state.page || 0,
        totalPages: Number(data.total_pages || state.totalPages || 0),
      }));
      // Mirror mode/page into the address bar without a router navigation
      // (which would rebuild the iframe URL and reload the Reader).
      const next = new URLSearchParams(window.location.search);
      const before = next.toString();
      next.set('mode', nextMode);
      if (nextPage > 0) next.set('page', String(nextPage));
      if (next.toString() === before) return;
      window.history.replaceState(window.history.state, '', `${window.location.pathname}?${next.toString()}`);
    };
    window.addEventListener('message', onReaderMessage);
    return () => window.removeEventListener('message', onReaderMessage);
  }, [sidecarInfo?.base, sourceId]);

  const overviewLink = (
    <Button
      component={Link}
      to={paperOverviewPath(name, sourceId)}
      variant="subtle"
      size="compact-sm"
      leftSection={<IconArrowLeft size={15} />}
      style={{ flexShrink: 0 }}
    >
      论文概览
    </Button>
  );

  if (research.isPending || reader.isPending) return <Center py="xl"><Loader /></Center>;
  const failure = research.isError
    ? { title: '加载失败', message: research.error.message, retry: () => void research.refetch() }
    : reader.isError
      ? { title: '阅读器打开失败', message: reader.error.message, retry: () => void reader.refetch() }
      : !sidecarInfo
        ? { title: '阅读器不可用', message: '当前环境没有配置 Reader API。', retry: () => void research.refetch() }
        : null;
  if (failure || !reader.data || !sidecarInfo) {
    return (
      <Stack gap="md">
        <div>{overviewLink}</div>
        <Alert color={failure?.title === '阅读器不可用' ? 'yellow' : 'red'} title={failure?.title}>
          <Text size="sm">{failure?.message}</Text>
          <Button mt="sm" size="compact-sm" variant="default" leftSection={<IconRefresh size={14} />} onClick={failure?.retry}>
            重试
          </Button>
        </Alert>
      </Stack>
    );
  }

  const query = new URLSearchParams(searchParams);
  query.set('profile', name);
  if (sourceId) query.set('source_id', sourceId);
  query.set('mode', mode);
  query.set('ui_lang', 'zh');
  const readerUrl = `${reader.data.reader_url}&${query.toString()}`;
  const externalPath = paperReaderPath(name, sourceId, { mode: readerState.mode, page: readerState.page });
  const totalPages = readerState.totalPages || paper?.page_count || 0;
  const pageText = readerState.page > 0
    ? `第 ${readerState.page}${totalPages ? ` / ${totalPages}` : ''} 页`
    : totalPages ? `共 ${totalPages} 页` : '';
  const title = paper?.title || sourceId;

  return (
    <Box
      data-testid="paper-reader-page"
      style={{
        height: `calc(100dvh - ${SHELL_OFFSET_PX}px)`,
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
        overflow: 'hidden',
      }}
    >
      <Group
        data-testid="paper-reader-bar"
        h={BAR_HEIGHT_PX}
        gap="sm"
        wrap="nowrap"
        px={4}
        style={{ flexShrink: 0, borderBottom: '1px solid rgba(220, 174, 85, 0.14)' }}
      >
        {overviewLink}
        <Text size="sm" c={chrome.dim} style={{ flexShrink: 0 }}>/</Text>
        <Text size="sm" c={chrome.text} truncate="end" title={title} style={{ minWidth: 0, flex: 1 }}>
          {title}
        </Text>
        {pageText && (
          <Text size="xs" c={chrome.dim} style={{ flexShrink: 0 }} data-testid="paper-reader-progress">
            {MODE_LABELS[readerState.mode] ? `${MODE_LABELS[readerState.mode]} · ` : ''}{pageText}
          </Text>
        )}
        <Tooltip label="重新加载阅读器">
          <ActionIcon variant="subtle" color="gray" aria-label="重新加载阅读器" onClick={() => setReloadSignal((value) => value + 1)}>
            <IconRefresh size={15} />
          </ActionIcon>
        </Tooltip>
        <Anchor
          href={externalPath}
          target="_blank"
          rel="noreferrer"
          size="sm"
          c={chrome.goldText}
          style={{ flexShrink: 0, whiteSpace: 'nowrap' }}
        >
          <IconExternalLink size={14} style={{ verticalAlign: 'middle', marginInlineEnd: 4 }} />
          新标签打开
        </Anchor>
      </Group>
      <Box style={{ flex: 1, minHeight: 0 }}>
        <SidecarFrame
          title={title || 'Paper Reader'}
          url={readerUrl}
          base={sidecarInfo.base}
          handoffToken={sidecarInfo.handoff_token}
          readyMessageType="nblane.reader.ready"
          height="100%"
          hideReloadButton
          reloadSignal={reloadSignal}
        />
      </Box>
    </Box>
  );
}
