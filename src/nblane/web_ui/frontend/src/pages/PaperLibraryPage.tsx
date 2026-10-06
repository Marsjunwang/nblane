// In-SPA Paper Library (/research/library): the sidecar library embedded
// full-height. The embedded library posts `nblane.library.open_reader` when
// the user opens a paper; the SPA routes that to the paper overview so every
// paper lands on its 论文概览 first.

import { Alert, Box, Button, Center, Group, Loader, Text } from '@mantine/core';
import { IconArrowLeft, IconRefresh } from '@tabler/icons-react';
import { useEffect } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { useResearch } from '../api/hooks';
import { paperOverviewPath, sidecarOrigin } from '../api/paperHooks';
import { SidecarFrame } from '../components/SidecarFrame';
import { chrome } from '../theme';

// AppShell header (56) + AppShell.Main vertical padding (md = 16 × 2).
const SHELL_OFFSET_PX = 56 + 32;

function embedUrl(url: string): string {
  try {
    const parsed = new URL(url, window.location.href);
    parsed.searchParams.set('ui_lang', 'zh');
    parsed.searchParams.set('embed', '1');
    return parsed.toString();
  } catch {
    return `${url}${url.includes('?') ? '&' : '?'}ui_lang=zh&embed=1`;
  }
}

export function PaperLibraryPage() {
  const { name = '' } = useParams();
  const navigate = useNavigate();
  const research = useResearch(name);
  const sidecar = research.data?.sidecar;

  useEffect(() => {
    if (!sidecar) return undefined;
    const expectedOrigin = sidecarOrigin(sidecar.base);
    const onMessage = (event: MessageEvent) => {
      if (event.origin !== expectedOrigin) return;
      const data = event.data as { type?: string; source_id?: unknown; profile?: unknown } | null;
      if (!data || data.type !== 'nblane.library.open_reader') return;
      const sourceId = typeof data.source_id === 'string' ? data.source_id.trim() : '';
      if (!sourceId) return;
      // A library embedded for another profile must not steer this one.
      if (typeof data.profile === 'string' && data.profile && data.profile !== name) return;
      navigate(paperOverviewPath(name, sourceId));
    };
    window.addEventListener('message', onMessage);
    return () => window.removeEventListener('message', onMessage);
  }, [sidecar?.base, name, navigate]);

  const back = (
    <Button component={Link} to={`/p/${encodeURIComponent(name)}/research`} variant="subtle" size="compact-sm" leftSection={<IconArrowLeft size={15} />}>
      研究台
    </Button>
  );

  if (research.isPending) return <Center py="xl"><Loader /></Center>;
  if (research.isError || !sidecar?.paper_library_url) {
    return (
      <Box>
        {back}
        <Alert mt="md" color={research.isError ? 'red' : 'yellow'} title={research.isError ? '论文库加载失败' : '论文库不可用'}>
          <Text size="sm">{research.isError ? research.error.message : '当前环境没有配置 Reader API。'}</Text>
          <Button mt="sm" size="compact-sm" variant="default" leftSection={<IconRefresh size={14} />} onClick={() => void research.refetch()}>
            重试
          </Button>
        </Alert>
      </Box>
    );
  }

  return (
    <Box
      data-testid="paper-library-page"
      style={{
        height: `calc(100dvh - ${SHELL_OFFSET_PX}px)`,
        display: 'flex',
        flexDirection: 'column',
        gap: 6,
        overflow: 'hidden',
      }}
    >
      <Group h={32} gap="sm" wrap="nowrap" style={{ flexShrink: 0 }}>
        {back}
        <Text size="sm" c={chrome.dim}>/</Text>
        <Text size="sm" c={chrome.text}>论文库</Text>
        <Text size="xs" c={chrome.dim} ml="auto">打开论文会先进入论文概览</Text>
      </Group>
      <Box style={{ flex: 1, minHeight: 0 }}>
        <SidecarFrame
          title="论文库"
          url={embedUrl(sidecar.paper_library_url)}
          base={sidecar.base}
          handoffToken={sidecar.handoff_token}
          height="100%"
          hideReloadButton
        />
      </Box>
    </Box>
  );
}
