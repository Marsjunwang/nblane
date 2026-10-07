import {
  Alert,
  Anchor,
  Badge,
  Button,
  Card,
  Divider,
  Group,
  NativeSelect,
  Paper,
  Progress,
  SimpleGrid,
  Stack,
  Text,
  TextInput,
  ThemeIcon,
  Title,
} from '@mantine/core';
import {
  IconBook2,
  IconCheck,
  IconChevronRight,
  IconClock,
  IconFileText,
  IconInbox,
  IconLibrary,
  IconPlayerPlay,
  IconRefresh,
  IconSearch,
  IconSparkles,
} from '@tabler/icons-react';
import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { useResearch } from '../api/hooks';
import { paperLibraryPath, paperOverviewPath, paperReaderPath, readerTabTarget, researchSourcesPath } from '../api/paperHooks';
import type { ResearchPaperItem } from '../api/types';
import { chrome } from '../theme';

const STATUS_LABELS: Record<string, string> = {
  inbox: '待读',
  reading: '阅读中',
  summarized: '已读',
  finished: '已读',
  archived: '归档',
  discarded: '已丢弃',
  candidate_ready: '待读',
};

function statusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status.replaceAll('_', ' ');
}

function progressFor(paper: ResearchPaperItem): number {
  if (!paper.page_count || !paper.last_page) return 0;
  return Math.min(100, Math.round((paper.last_page / paper.page_count) * 100));
}

function pageLabel(paper: ResearchPaperItem): string {
  if (!paper.page_count && !paper.last_page) return '尚未开始';
  if (!paper.last_page) return `${paper.page_count} 页`;
  return `第 ${paper.last_page} / ${paper.page_count} 页`;
}

function hasQuickAnalysis(paper: ResearchPaperItem): boolean {
  const analysis = (paper.analysis ?? {}) as { tldr?: unknown; key_points?: unknown };
  return Boolean(
    (typeof analysis.tldr === 'string' && analysis.tldr.trim()) ||
      (Array.isArray(analysis.key_points) && analysis.key_points.length),
  );
}

function TranslationBadge({ paper }: { paper: ResearchPaperItem }) {
  if (!paper.segment_count) return null;
  const done = paper.translation_status === 'translated';
  const color = done ? 'green' : paper.stale_count || paper.failed_count ? 'yellow' : 'gray';
  const extra = [
    paper.stale_count ? `过期 ${paper.stale_count}` : '',
    paper.failed_count ? `失败 ${paper.failed_count}` : '',
  ].filter(Boolean).join(' · ');
  return (
    <Badge size="sm" variant="outline" color={color} data-testid="paper-translation-badge">
      {done ? '已全部翻译' : `译 ${paper.translated_count} / ${paper.segment_count}`}{extra ? ` · ${extra}` : ''}
    </Badge>
  );
}

function PaperRow({ paper, profile }: { paper: ResearchPaperItem; profile: string }) {
  const progress = progressFor(paper);
  const canRead = paper.pdf_available;
  const analyzed = hasQuickAnalysis(paper);
  const card = (
    <Paper
      component="div"
      withBorder
      radius="md"
      p="md"
      style={{
        display: 'block',
        borderColor: 'rgba(220, 174, 85, 0.16)',
        background: chrome.cardBg,
        color: chrome.text,
        textDecoration: 'none',
        opacity: canRead ? 1 : 0.72,
      }}
    >
      <Group justify="space-between" align="flex-start" wrap="nowrap">
        <Group gap="sm" wrap="nowrap" style={{ minWidth: 0 }}>
          <ThemeIcon variant="light" color="brand" size={34} radius="sm">
            {paper.status === 'reading' ? <IconPlayerPlay size={17} /> : <IconFileText size={17} />}
          </ThemeIcon>
          <div style={{ minWidth: 0 }}>
            <Text fw={650} lineClamp={1}>{paper.title || paper.id}</Text>
            <Text size="xs" c={chrome.dim} mt={3}>{pageLabel(paper)}</Text>
          </div>
        </Group>
        <Badge variant="light" color={paper.status === 'reading' ? 'yellow' : 'gray'}>
          {statusLabel(paper.status)}
        </Badge>
      </Group>
      <Group gap="xs" mt="sm">
        <Badge size="sm" variant="outline" color={paper.pdf_available ? 'green' : 'gray'}>
          {paper.pdf_available ? 'PDF 已就绪' : '等待 PDF'}
        </Badge>
        <TranslationBadge paper={paper} />
        <Badge
          size="sm"
          variant={analyzed ? 'light' : 'outline'}
          color={analyzed ? 'brand' : 'gray'}
          leftSection={analyzed ? <IconSparkles size={11} /> : undefined}
        >
          {analyzed ? '已快速分析' : '未分析'}
        </Badge>
        {paper.tags?.slice(0, 2).map((tag) => <Badge key={tag} size="sm" variant="dot" color="gray">{tag}</Badge>)}
      </Group>
      {paper.page_count > 0 && <Progress value={progress} size={3} mt="md" color={paper.status === 'reading' ? 'brand' : 'gray'} />}
      <Group justify="space-between" mt="xs">
        <Text size="xs" c={chrome.dim} lineClamp={1}>{paper.summary || '还没有阅读摘要'}</Text>
        <IconChevronRight size={16} color={chrome.goldText} />
      </Group>
    </Paper>
  );
  // Every paper lands on its overview first (metadata, quick analysis,
  // continue reading); the Reader is one click further.
  return (
    <Link
      to={paperOverviewPath(profile, paper.id)}
      aria-label={`${paper.title || paper.id} · 论文概览`}
      style={{ display: 'block', color: 'inherit', textDecoration: 'none' }}
    >
      {card}
    </Link>
  );
}

export function ResearchPage() {
  const { name = '' } = useParams();
  const research = useResearch(name);
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState('all');

  if (research.isPending) return <Text c="dimmed">正在打开研究台…</Text>;
  if (research.isError) {
    return (
      <Alert color="red" title="研究台加载失败">
        <Text size="sm">{research.error.message}</Text>
        <Button mt="sm" size="compact-sm" variant="default" leftSection={<IconRefresh size={14} />} onClick={() => void research.refetch()}>
          重试
        </Button>
      </Alert>
    );
  }

  const data = research.data;
  const papers = data.papers ?? [];
  const reading = papers.filter((paper) => paper.status === 'reading' && paper.pdf_available);
  const queued = papers.filter((paper) => ['inbox', 'candidate_ready'].includes(paper.status));
  const finished = papers.filter((paper) => ['summarized', 'finished'].includes(paper.status));
  const visible = papers.filter((paper) => {
    const haystack = `${paper.title} ${paper.summary} ${(paper.tags ?? []).join(' ')}`.toLowerCase();
    return (!query.trim() || haystack.includes(query.trim().toLowerCase())) && (status === 'all' || paper.status === status);
  });
  const nextPaper = reading[0] ?? queued.find((paper) => paper.pdf_available);

  return (
    <Stack gap="lg" pb="xl">
      <Group justify="space-between" align="flex-end">
        <div>
          <Text size="xs" fw={700} c={chrome.goldText}>研究 · 阅读节奏</Text>
          <Title order={2} mt={4}>{data.profile} · 研究台</Title>
          <Text size="sm" c={chrome.dim} mt={5}>从待读到读完，只管理阅读节奏，不把阅读强行变成证据。</Text>
        </div>
        {data.sidecar?.paper_library_url && (
          <Button component={Link} to={paperLibraryPath(name)} variant="light" leftSection={<IconLibrary size={15} />}>
            打开论文库
          </Button>
        )}
      </Group>

      <Card withBorder radius="md" p="lg" style={{ background: `linear-gradient(135deg, ${chrome.panelBg}, ${chrome.cardBg})`, borderColor: 'rgba(220, 174, 85, 0.24)' }}>
        <Group justify="space-between" align="flex-start" wrap="nowrap">
          <Group gap="sm" wrap="nowrap" style={{ minWidth: 0 }}>
            <ThemeIcon size={42} radius="sm" color="brand" variant="light"><IconBook2 size={21} /></ThemeIcon>
            <div style={{ minWidth: 0 }}>
              <Text size="xs" fw={700} c={chrome.goldText}>继续阅读</Text>
              <Title order={3} mt={3} lineClamp={1}>{nextPaper?.title ?? '今天还没有正在阅读的论文'}</Title>
              <Text size="sm" c={chrome.dim} mt={4}>{nextPaper ? `${pageLabel(nextPaper)} · ${statusLabel(nextPaper.status)}` : '从论文库导入一篇，建立你的阅读队列。'}</Text>
            </div>
          </Group>
          {nextPaper?.pdf_available ? (
            <Group gap="xs" wrap="nowrap">
              <Button component={Link} to={paperOverviewPath(name, nextPaper.id)} variant="default">论文概览</Button>
              <Button component={Link} to={paperReaderPath(name, nextPaper.id)} target={readerTabTarget(nextPaper.id)} color="brand" leftSection={<IconPlayerPlay size={15} />}>继续阅读</Button>
            </Group>
          ) : data.sidecar?.paper_library_url ? (
            <Button component={Link} to={paperLibraryPath(name)} variant="default" leftSection={<IconLibrary size={15} />}>选择论文</Button>
          ) : null}
        </Group>
        {nextPaper?.page_count ? <Progress value={progressFor(nextPaper)} size={5} mt="lg" color="brand" /> : null}
      </Card>

      <SimpleGrid cols={{ base: 2, sm: 4 }} spacing="sm">
        {[
          { label: '论文总数', value: papers.length, icon: IconLibrary },
          { label: '阅读中', value: reading.length, icon: IconPlayerPlay },
          { label: '待读', value: queued.length, icon: IconInbox },
          { label: '已读', value: finished.length, icon: IconCheck },
        ].map((item) => (
          <Paper key={item.label} withBorder p="md" radius="md" style={{ background: chrome.panelBg, borderColor: 'rgba(220, 174, 85, 0.14)' }}>
            <Group gap="xs"><item.icon size={15} color={chrome.goldText} /><Text size="xs" c={chrome.dim}>{item.label}</Text></Group>
            <Text fw={750} fz={28} mt={5}>{item.value}</Text>
          </Paper>
        ))}
      </SimpleGrid>

      <SimpleGrid cols={{ base: 1, md: 2 }} spacing="lg">
        <Card withBorder radius="md" p="lg" style={{ background: chrome.panelBg }}>
          <Group justify="space-between" mb="md"><div><Text fw={700}>阅读队列</Text><Text size="xs" c={chrome.dim} mt={3}>优先处理正在读和已准备好 PDF 的论文。</Text></div><Badge variant="light" color="yellow">{reading.length + queued.length}</Badge></Group>
          <Stack gap="sm">
            {(reading.length ? reading : queued).slice(0, 3).map((paper) => <PaperRow key={paper.id} paper={paper} profile={name} />)}
            {!reading.length && !queued.length && <Text size="sm" c={chrome.dim}>队列为空。打开论文库添加第一篇论文。</Text>}
          </Stack>
        </Card>
        <Card withBorder radius="md" p="lg" style={{ background: chrome.panelBg }}>
          <Group justify="space-between" mb="md"><div><Text fw={700}>最近读过</Text><Text size="xs" c={chrome.dim} mt={3}>阅读位置会在 Reader 中自动保存。</Text></div><IconClock size={17} color={chrome.goldText} /></Group>
          <Stack gap="sm">
            {(finished.length ? finished : papers.filter((paper) => paper.last_page > 0)).slice(0, 3).map((paper) => <PaperRow key={paper.id} paper={paper} profile={name} />)}
            {!finished.length && !papers.some((paper) => paper.last_page > 0) && <Text size="sm" c={chrome.dim}>还没有阅读记录。</Text>}
          </Stack>
        </Card>
      </SimpleGrid>

      <Card withBorder radius="md" p="lg" style={{ background: chrome.panelBg }}>
        <Group justify="space-between" align="flex-end" mb="md">
          <div><Text fw={700}>论文索引</Text><Text size="xs" c={chrome.dim} mt={3}>这里只是当前 profile 的论文入口，完整整理在论文库。</Text></div>
          <Group gap="xs">
            <TextInput value={query} onChange={(event) => setQuery(event.currentTarget.value)} placeholder="搜索标题、摘要或标签" leftSection={<IconSearch size={14} />} />
            <NativeSelect value={status} onChange={(event) => setStatus(event.currentTarget.value)} data={[{ value: 'all', label: '全部状态' }, ...Object.keys(data.summary?.status_counts ?? {}).map((value) => ({ value, label: statusLabel(value) }))]} />
          </Group>
        </Group>
        <Divider color="rgba(220,174,85,.14)" mb="md" />
        <Stack gap="sm">
          {visible.map((paper) => <PaperRow key={paper.id} paper={paper} profile={name} />)}
          {!visible.length && <Text size="sm" c={chrome.dim}>没有符合条件的论文。</Text>}
        </Stack>
      </Card>

      <Group justify="flex-end"><Anchor component={Link} to={researchSourcesPath(name)} size="sm" c={chrome.goldText}>查看研究收件箱 <IconChevronRight size={14} style={{ verticalAlign: 'middle' }} /></Anchor></Group>
    </Stack>
  );
}
