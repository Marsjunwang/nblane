// Paper overview (论文概览): the landing page of one paper.
//
// Answers "这篇论文做了什么、是否值得继续读" before the Reader opens:
// metadata + abstract, PDF / reading / translation state, recent notes, the
// quick analysis (快速分析) as a calm 铭文卡, and the deep study (深度研读)
// report. Every cited ref links into the Reader at its page. AI runs go
// through the SPA job registry (paper-quick-analysis / paper-deep-read) and
// stream progress over SSE. Claim / Evidence never appear here.

import {
  Accordion,
  Alert,
  Anchor,
  Badge,
  Box,
  Button,
  Card,
  Center,
  Divider,
  Grid,
  Group,
  Loader,
  Progress,
  SegmentedControl,
  Stack,
  Text,
  Title,
  Tooltip,
} from '@mantine/core';
import {
  IconArrowLeft,
  IconBook2,
  IconExternalLink,
  IconLayoutColumns,
  IconMicroscope,
  IconPlayerPlay,
  IconQuote,
  IconRefresh,
  IconSparkles,
} from '@tabler/icons-react';
import dayjs from 'dayjs';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { Link, Navigate, useParams, useSearchParams } from 'react-router-dom';

import {
  paperReaderPath,
  readerTabTarget,
  usePaperJob,
  usePaperOverview,
} from '../api/paperHooks';
import type {
  PaperAnalysisItem,
  PaperCoverage,
  PaperDeepRead,
  PaperJobKind,
  PaperOverview,
  PaperQuickAnalysis,
  PaperRef,
} from '../api/paperHooks';
import { chrome, inscription } from '../theme';

const BORDER = 'rgba(220, 174, 85, 0.16)';
const BORDER_STRONG = 'rgba(220, 174, 85, 0.24)';
// Old deep links (/research/papers/:id?mode=…) belonged to the Reader.
const READER_QUERY_KEYS = ['mode', 'page', 'anchor', 'section'];

const SCORE_LABELS: Record<string, string> = {
  novelty: '新颖性',
  technical_depth: '技术深度',
  evidence_quality: '实验支撑',
  reproducibility: '可复现性',
  relevance: '相关性',
  overall: '总评',
};

const STRUCTURE_LABELS: Record<string, string> = {
  grobid: 'GROBID 结构化',
  pymupdf_fallback: 'PyMuPDF 降级结构',
  pymupdf: 'PyMuPDF',
};

const EXTRACTION_LABELS: Record<string, string> = {
  ready: '结构已就绪',
  fallback: '降级结构',
  failed: '抽取失败',
  missing_pdf: '缺少 PDF',
};

function formatTime(value: string | undefined | null): string {
  if (!value) return '';
  const parsed = dayjs(value);
  return parsed.isValid() ? parsed.format('YYYY-MM-DD HH:mm') : value;
}

function pageRangeLabel(pages: number[]): string {
  if (!pages.length) return '';
  if (pages.length === 1) return `p.${pages[0]}`;
  return `p.${pages[0]}–${pages[pages.length - 1]}`;
}

function coverageLabel(coverage: PaperCoverage | undefined, pageCount: number): string {
  if (!coverage) return '';
  const parts: string[] = [];
  if (coverage.page_count) {
    parts.push(
      `引用 ${coverage.page_count}${pageCount ? ` / ${pageCount}` : ''} 页（${pageRangeLabel(coverage.pages)}）`,
    );
  }
  if (coverage.cited_segments) parts.push(`${coverage.cited_segments} 段原文`);
  if (coverage.sections?.length) parts.push(`覆盖章节：${coverage.sections.slice(0, 4).join('、')}`);
  return parts.join(' · ');
}

// --- Small building blocks ----------------------------------------------------

function RefChips({ refs, profile, sourceId }: { refs: PaperRef[]; profile: string; sourceId: string }) {
  const pages = [...new Set(refs.map((ref) => ref.page).filter((page) => page > 0))].sort((a, b) => a - b);
  if (!pages.length) return null;
  const shown = pages.slice(0, 4);
  return (
    <Group gap={4} component="span" style={{ display: 'inline-flex', marginInlineStart: 6, verticalAlign: 'baseline' }}>
      {shown.map((page) => (
        <Anchor
          key={page}
          component={Link}
          to={paperReaderPath(profile, sourceId, { page })}
          target={readerTabTarget(sourceId)}
          aria-label={`在阅读器中打开第 ${page} 页`}
          style={{
            fontFamily: 'inherit',
            fontSize: 11,
            lineHeight: '16px',
            padding: '0 6px',
            borderRadius: 4,
            border: `1px solid ${BORDER_STRONG}`,
            color: chrome.goldText,
            textDecoration: 'none',
          }}
        >
          p.{page}
        </Anchor>
      ))}
      {pages.length > shown.length && (
        <Text component="span" size="xs" c={chrome.dim}>+{pages.length - shown.length}</Text>
      )}
    </Group>
  );
}

/** Display-mode KaTeX for deep-read equations; falls back to the source on error. */
function LatexBlock({ latex }: { latex: string }) {
  const html = useMemo(() => {
    try {
      return katex.renderToString(latex, { displayMode: true, throwOnError: false, strict: false, trust: false });
    } catch {
      return '';
    }
  }, [latex]);
  if (!html) {
    return (
      <Text component="pre" size="xs" style={{ whiteSpace: 'pre-wrap', color: inscription.dimColor, margin: '4px 0' }}>
        {latex}
      </Text>
    );
  }
  return <Box my={4} style={{ overflowX: 'auto' }} dangerouslySetInnerHTML={{ __html: html }} />;
}

function ItemList({ items, profile, sourceId }: { items: PaperAnalysisItem[]; profile: string; sourceId: string }) {
  return (
    <Stack gap={6} component="ul" style={{ margin: 0, paddingInlineStart: 18 }}>
      {items.map((item, index) => (
        <li key={`${index}-${(item.label || item.text).slice(0, 24)}`} style={{ lineHeight: 1.65 }}>
          {item.badge && (
            <Badge size="xs" variant="light" color="yellow" mr={6} style={{ verticalAlign: 'baseline' }}>
              {item.badge}
            </Badge>
          )}
          {item.label && (
            <Text component="span" fw={600} style={{ color: inscription.titleColor }}>
              {item.label}
              {item.text ? '：' : ''}
            </Text>
          )}
          {item.latex && <LatexBlock latex={item.latex} />}
          {item.text}
          <RefChips refs={item.refs ?? []} profile={profile} sourceId={sourceId} />
        </li>
      ))}
    </Stack>
  );
}

function InscriptionSection({ label, children }: { label: string; children: ReactNode }) {
  return (
    <Box>
      <Text
        size="sm"
        fw={600}
        mb={6}
        style={{ color: inscription.accentColor, fontFamily: inscription.titleFontFamily, letterSpacing: 1 }}
      >
        {label}
      </Text>
      {children}
    </Box>
  );
}

/** 铭文卡 shell without the inner scroller (the page itself scrolls). */
function InscriptionPanel({
  title,
  icon,
  meta,
  aside,
  testId,
  children,
}: {
  title: string;
  icon: ReactNode;
  meta?: ReactNode;
  aside?: ReactNode;
  testId: string;
  children: ReactNode;
}) {
  return (
    <Box
      data-testid={testId}
      style={{
        background: inscription.background,
        border: `1px solid ${inscription.borderColor}`,
        borderRadius: 12,
        padding: '18px 22px',
        color: inscription.bodyColor,
        fontFamily: inscription.bodyFontFamily,
        fontSize: 14,
      }}
    >
      <Group justify="space-between" align="flex-start" wrap="nowrap" mb="sm" gap="md">
        <div style={{ minWidth: 0 }}>
          <Group gap={8} wrap="nowrap">
            {icon}
            <Title order={4} style={{ color: inscription.titleColor, fontFamily: inscription.titleFontFamily, fontWeight: 600 }}>
              {title}
            </Title>
          </Group>
          {meta && (
            <Text size="xs" mt={4} style={{ color: inscription.dimColor, fontFamily: 'var(--mantine-font-family)' }}>
              {meta}
            </Text>
          )}
        </div>
        {aside && <Box style={{ flexShrink: 0, fontFamily: 'var(--mantine-font-family)' }}>{aside}</Box>}
      </Group>
      {children}
    </Box>
  );
}

function ResultStatusBadge({ status, fallback }: { status: string; fallback: boolean }) {
  if (fallback) return <Badge variant="light" color="yellow" size="sm">降级结果 · 待核对</Badge>;
  if (status === 'needs_review') return <Badge variant="light" color="yellow" size="sm">待核对</Badge>;
  return <Badge variant="outline" color="gray" size="sm">已生成</Badge>;
}

function Warnings({ warnings }: { warnings: string[] }) {
  if (!warnings.length) return null;
  return (
    <Text size="xs" mt="sm" style={{ color: inscription.dimColor, fontFamily: 'var(--mantine-font-family)' }}>
      提示：{warnings.slice(0, 2).join('；')}
      {warnings.length > 2 ? `（另 ${warnings.length - 2} 条）` : ''}
    </Text>
  );
}

/** Start / re-run button plus its running and failed states. */
function JobControl({
  label,
  rerunLabel,
  hasResult,
  disabledReason,
  job,
}: {
  label: string;
  rerunLabel: string;
  hasResult: boolean;
  disabledReason: string;
  job: ReturnType<typeof usePaperJob>;
}) {
  const running = job.state.status === 'running';
  const button = (
    <Button
      size="compact-sm"
      variant={hasResult ? 'default' : 'light'}
      leftSection={hasResult ? <IconRefresh size={14} /> : <IconSparkles size={14} />}
      loading={running}
      disabled={Boolean(disabledReason)}
      onClick={job.run}
    >
      {hasResult ? rerunLabel : label}
    </Button>
  );
  return disabledReason ? <Tooltip label={disabledReason}><span>{button}</span></Tooltip> : button;
}

function JobFeedback({ job, label }: { job: ReturnType<typeof usePaperJob>; label: string }) {
  if (job.state.status === 'running') {
    return (
      <Group gap="xs" mt="sm" data-testid="paper-job-running">
        <Loader size={14} color="brand" />
        <Text size="xs" c={chrome.dim} style={{ fontFamily: 'var(--mantine-font-family)' }}>
          {label}进行中：{job.state.message || '处理中…'}
        </Text>
      </Group>
    );
  }
  if (job.state.status === 'failed' && job.state.error) {
    return (
      <Alert
        mt="sm"
        color="red"
        variant="light"
        title={`${label}未完成`}
        data-testid="paper-job-error"
        style={{ fontFamily: 'var(--mantine-font-family)' }}
      >
        <Text size="sm">{job.state.error.message}</Text>
        <Button mt="xs" size="compact-xs" variant="default" leftSection={<IconRefresh size={12} />} onClick={job.run}>
          重试
        </Button>
      </Alert>
    );
  }
  return null;
}

// --- Analysis cards -------------------------------------------------------------

function QuickAnalysisCard({
  analysis,
  data,
  profile,
  sourceId,
  job,
}: {
  analysis: PaperQuickAnalysis | null | undefined;
  data: PaperOverview;
  profile: string;
  sourceId: string;
  job: ReturnType<typeof usePaperJob>;
}) {
  const disabledReason = data.reader_available ? '' : data.reader_unavailable_reason || 'PDF 尚未就绪';
  const control = (
    <JobControl label="快速分析" rerunLabel="重新分析" hasResult={Boolean(analysis)} disabledReason={disabledReason} job={job} />
  );
  if (!analysis) {
    return (
      <InscriptionPanel title="快速分析" icon={<IconSparkles size={18} color={inscription.accentColor} />} aside={control} testId="paper-quick-analysis">
        <Text size="sm" style={{ color: inscription.dimColor }}>
          尚未生成。快速分析会给出 TL;DR、要点、方法、实验、局限、评分和阅读建议，每条结论都可跳回原文页码。
        </Text>
        <JobFeedback job={job} label="快速分析" />
      </InscriptionPanel>
    );
  }
  const pageCount = data.pdf.page_count;
  const meta = [
    analysis.updated ? `生成于 ${formatTime(analysis.updated)}` : '',
    coverageLabel(analysis.coverage, pageCount),
  ].filter(Boolean).join(' · ');
  const sections: { label: string; items: PaperAnalysisItem[] }[] = [
    { label: '要点', items: analysis.key_points ?? [] },
    { label: '方法', items: analysis.method ?? [] },
    { label: '实验', items: analysis.experiments ?? [] },
    { label: '局限', items: analysis.limitations ?? [] },
    { label: '项目相关性', items: [...(analysis.project_relevance ?? []), ...(analysis.usefulness ?? [])] },
    { label: '阅读建议', items: [...(analysis.reading_plan ?? []), ...(analysis.open_questions ?? [])] },
  ];
  const scores = Object.entries(analysis.scores ?? {}).filter(([key]) => key in SCORE_LABELS);
  return (
    <InscriptionPanel
      title="快速分析"
      icon={<IconSparkles size={18} color={inscription.accentColor} />}
      meta={meta}
      aside={
        <Group gap="xs" wrap="nowrap">
          <ResultStatusBadge status={analysis.status} fallback={analysis.fallback} />
          {control}
        </Group>
      }
      testId="paper-quick-analysis"
    >
      <Stack gap="md">
        {analysis.tldr && (
          <InscriptionSection label="TL;DR">
            <Text style={{ fontFamily: 'inherit', color: inscription.titleColor, lineHeight: 1.75 }}>{analysis.tldr}</Text>
          </InscriptionSection>
        )}
        {sections.map((section) =>
          section.items.length ? (
            <InscriptionSection key={section.label} label={section.label}>
              <ItemList items={section.items} profile={profile} sourceId={sourceId} />
            </InscriptionSection>
          ) : (
            section.label === '项目相关性' || section.label === '阅读建议' ? (
              <InscriptionSection key={section.label} label={section.label}>
                <Text size="sm" style={{ color: inscription.dimColor }}>本次分析未给出。</Text>
              </InscriptionSection>
            ) : null
          ),
        )}
        <InscriptionSection label="评分">
          {analysis.scores_evaluated && scores.length ? (
            <Group gap="sm" data-testid="paper-scores">
              {scores.map(([key, value]) => (
                <Box
                  key={key}
                  style={{
                    border: `1px solid ${BORDER}`,
                    borderRadius: 8,
                    padding: '6px 10px',
                    minWidth: 76,
                    fontFamily: 'var(--mantine-font-family)',
                  }}
                >
                  <Text size="xs" style={{ color: inscription.dimColor }}>{SCORE_LABELS[key]}</Text>
                  <Text fw={700} style={{ color: key === 'overall' ? inscription.accentColor : inscription.titleColor }}>
                    {value}<Text component="span" size="xs" style={{ color: inscription.dimColor }}> / 5</Text>
                  </Text>
                </Box>
              ))}
            </Group>
          ) : (
            <Text size="sm" style={{ color: inscription.dimColor }}>未评估（结果缺少可靠依据，不显示为零分）。</Text>
          )}
          {analysis.score_rationale?.length ? (
            <Accordion variant="default" chevronPosition="left" mt="xs" styles={{ control: { paddingInline: 0 }, content: { paddingInline: 0 } }}>
              <Accordion.Item value="rationale" style={{ borderBottom: 0 }}>
                <Accordion.Control>
                  <Text size="xs" style={{ color: inscription.dimColor }}>评分依据（{analysis.score_rationale.length}）</Text>
                </Accordion.Control>
                <Accordion.Panel>
                  <ItemList items={analysis.score_rationale} profile={profile} sourceId={sourceId} />
                </Accordion.Panel>
              </Accordion.Item>
            </Accordion>
          ) : null}
        </InscriptionSection>
      </Stack>
      <Warnings warnings={analysis.warnings ?? []} />
      <JobFeedback job={job} label="快速分析" />
    </InscriptionPanel>
  );
}

function DeepReadCard({
  deepRead,
  data,
  profile,
  sourceId,
  job,
}: {
  deepRead: PaperDeepRead | null | undefined;
  data: PaperOverview;
  profile: string;
  sourceId: string;
  job: ReturnType<typeof usePaperJob>;
}) {
  const disabledReason = data.reader_available ? '' : data.reader_unavailable_reason || 'PDF 尚未就绪';
  const control = (
    <JobControl label="深度研读" rerunLabel="重新研读" hasResult={Boolean(deepRead)} disabledReason={disabledReason} job={job} />
  );
  const icon = <IconMicroscope size={18} color={inscription.accentColor} />;
  if (!deepRead) {
    return (
      <InscriptionPanel title="深度研读" icon={icon} aside={control} testId="paper-deep-read">
        <Text size="sm" style={{ color: inscription.dimColor }}>
          尚未生成。深度研读由 Codex 读完整篇论文和图表截图，逐项拆解方法组件、关键公式、实验表格，并核对每个论点的支撑；耗时约十几分钟，可在快速分析后再决定是否启动。
        </Text>
        <JobFeedback job={job} label="深度研读" />
      </InscriptionPanel>
    );
  }
  const meta = [
    deepRead.updated ? `生成于 ${formatTime(deepRead.updated)}` : '',
    coverageLabel(deepRead.coverage, data.pdf.page_count),
    deepRead.batch_count ? `分 ${deepRead.batch_count} 批研读` : '',
  ].filter(Boolean).join(' · ');
  return (
    <InscriptionPanel
      title="深度研读"
      icon={icon}
      meta={meta}
      aside={
        <Group gap="xs" wrap="nowrap">
          <ResultStatusBadge status={deepRead.status} fallback={deepRead.fallback} />
          {control}
        </Group>
      }
      testId="paper-deep-read"
    >
      {deepRead.fallback && (
        <Text size="sm" mb="sm" style={{ color: inscription.dimColor }}>
          Codex 未返回完整研读，以下内容不完整，请重新研读或对照原文核对。
        </Text>
      )}
      {deepRead.takeaway && (
        <InscriptionSection label="研读结论">
          {(deepRead.worth_reading || deepRead.audience) && (
            <Group gap="xs" mb={6}>
              {deepRead.worth_reading && (
                <Badge size="sm" variant="light" color="yellow">{deepRead.worth_reading}</Badge>
              )}
              {deepRead.audience && (
                <Text size="xs" style={{ color: inscription.dimColor }}>适合：{deepRead.audience}</Text>
              )}
            </Group>
          )}
          <Text style={{ fontFamily: 'inherit', color: inscription.titleColor, lineHeight: 1.75 }}>
            {deepRead.takeaway}
            <RefChips refs={deepRead.takeaway_refs ?? []} profile={profile} sourceId={sourceId} />
          </Text>
        </InscriptionSection>
      )}
      {deepRead.sections.length > 0 && (
        <Accordion
          multiple
          mt="sm"
          chevronPosition="left"
          defaultValue={[deepRead.sections[0].key]}
          styles={{
            item: { borderColor: BORDER },
            control: { paddingInline: 0 },
            content: { paddingInline: 0 },
          }}
        >
          {deepRead.sections.map((section) => (
            <Accordion.Item key={section.key} value={section.key}>
              <Accordion.Control>
                <Text size="sm" fw={600} style={{ color: inscription.accentColor, fontFamily: inscription.titleFontFamily }}>
                  {section.label}
                  <Text component="span" size="xs" ml={6} style={{ color: inscription.dimColor, fontFamily: 'var(--mantine-font-family)' }}>
                    {section.items.length}
                  </Text>
                </Text>
              </Accordion.Control>
              <Accordion.Panel>
                <ItemList items={section.items} profile={profile} sourceId={sourceId} />
              </Accordion.Panel>
            </Accordion.Item>
          ))}
        </Accordion>
      )}
      <Warnings warnings={deepRead.warnings ?? []} />
      <JobFeedback job={job} label="深度研读" />
    </InscriptionPanel>
  );
}

// --- Side panels ------------------------------------------------------------------

function SideCard({ title, children, testId }: { title: string; children: ReactNode; testId?: string }) {
  return (
    <Card withBorder radius="md" p="md" data-testid={testId} style={{ background: chrome.panelBg, borderColor: BORDER }}>
      <Text size="xs" fw={700} c={chrome.goldText} mb="xs">{title}</Text>
      {children}
    </Card>
  );
}

function StatusRow({ label, value }: { label: string; value: ReactNode }) {
  return (
    <Group justify="space-between" gap="xs" wrap="nowrap" py={2}>
      <Text size="sm" c={chrome.dim}>{label}</Text>
      <Text size="sm" ta="right" style={{ minWidth: 0 }}>{value}</Text>
    </Group>
  );
}

function SidePanels({ data, profile, sourceId }: { data: PaperOverview; profile: string; sourceId: string }) {
  const { pdf, progress, translation, notes } = data;
  const readPct = progress.page_count && progress.last_page
    ? Math.min(100, Math.round((progress.last_page / progress.page_count) * 100))
    : 0;
  const translatedPct = translation.total ? Math.round((translation.translated / translation.total) * 100) : 0;
  return (
    <Stack gap="md">
      <SideCard title="PDF 与抽取" testId="paper-pdf-status">
        <StatusRow
          label="PDF"
          value={pdf.available
            ? <Badge size="sm" variant="light" color="green">已就绪</Badge>
            : <Badge size="sm" variant="light" color="gray">{pdf.download_status === 'failed' ? '下载失败' : '未就绪'}</Badge>}
        />
        {pdf.page_count > 0 && <StatusRow label="页数" value={`${pdf.page_count} 页`} />}
        {(pdf.extraction_status || pdf.structure_backend) && (
          <StatusRow
            label="结构"
            value={[EXTRACTION_LABELS[pdf.extraction_status] ?? pdf.extraction_status, STRUCTURE_LABELS[pdf.structure_backend] ?? pdf.structure_backend]
              .filter(Boolean)
              .join(' · ')}
          />
        )}
        {pdf.download_error && <Text size="xs" c="red.4" mt={4}>{pdf.download_error}</Text>}
      </SideCard>

      <SideCard title="阅读进度" testId="paper-reading-progress">
        <Text size="sm">
          {progress.last_page
            ? `读到第 ${progress.last_page}${progress.page_count ? ` / ${progress.page_count}` : ''} 页`
            : '尚未开始阅读'}
        </Text>
        {progress.page_count > 0 && <Progress value={readPct} size={4} mt="xs" color="brand" />}
        {progress.last_read_at && <Text size="xs" c={chrome.dim} mt={6}>上次阅读 {formatTime(progress.last_read_at)}</Text>}
      </SideCard>

      <SideCard title="翻译进度" testId="paper-translation-progress">
        {translation.total ? (
          <>
            <Text size="sm">已翻译 {translation.translated} / {translation.total} 段</Text>
            <Progress value={translatedPct} size={4} mt="xs" color={translation.status === 'translated' ? 'green' : 'brand'} />
            <Group gap={6} mt="xs">
              {translation.missing > 0 && <Badge size="xs" variant="outline" color="gray">缺失 {translation.missing}</Badge>}
              {translation.stale > 0 && <Badge size="xs" variant="outline" color="yellow">过期 {translation.stale}</Badge>}
              {translation.failed > 0 && <Badge size="xs" variant="outline" color="red">失败 {translation.failed}</Badge>}
            </Group>
          </>
        ) : (
          <Text size="sm" c={chrome.dim}>还没有可翻译的结构；打开阅读器后会自动准备。</Text>
        )}
      </SideCard>

      <SideCard title={`笔记 · ${notes.annotation_count}`} testId="paper-notes">
        {notes.recent.length ? (
          <Stack gap="sm">
            {notes.recent.map((note) => (
              <Box key={note.id} style={{ borderInlineStart: `2px solid ${BORDER_STRONG}`, paddingInlineStart: 10 }}>
                {note.quote && (
                  <Text size="sm" lineClamp={3} style={{ fontFamily: inscription.bodyFontFamily, color: inscription.bodyColor }}>
                    <IconQuote size={12} color={chrome.dim} style={{ marginInlineEnd: 4, verticalAlign: 'baseline' }} />
                    {note.quote}
                  </Text>
                )}
                {note.note && <Text size="xs" c={chrome.text} mt={4} lineClamp={2}>{note.note}</Text>}
                {note.page > 0 && (
                  <Anchor component={Link} to={paperReaderPath(profile, sourceId, { page: note.page })} target={readerTabTarget(sourceId)} size="xs" c={chrome.goldText}>
                    第 {note.page} 页
                  </Anchor>
                )}
              </Box>
            ))}
          </Stack>
        ) : (
          <Text size="sm" c={chrome.dim}>还没有笔记。在阅读器中选中文字即可高亮或记笔记。</Text>
        )}
        {notes.chunk_count > 0 && <Text size="xs" c={chrome.dim} mt="sm">另有 {notes.chunk_count} 条摘录</Text>}
      </SideCard>
    </Stack>
  );
}

// --- Page -----------------------------------------------------------------------

function AbstractBlock({ data }: { data: PaperOverview }) {
  const { abstract } = data;
  const hasTranslation = Boolean(abstract.translation);
  const [view, setView] = useState<'zh' | 'en'>(hasTranslation ? 'zh' : 'en');
  if (!abstract.text) {
    return <Text size="sm" c={chrome.dim}>暂无摘要。PDF 结构就绪后会从论文首页读取。</Text>;
  }
  return (
    <Box data-testid="paper-abstract">
      <Group justify="space-between" mb="xs">
        <Text size="xs" fw={700} c={chrome.goldText}>摘要</Text>
        {hasTranslation ? (
          <SegmentedControl
            size="xs"
            value={view}
            onChange={(value) => setView(value as 'zh' | 'en')}
            data={[{ value: 'zh', label: abstract.translation_status === 'partial' ? '中文（部分）' : '中文' }, { value: 'en', label: '原文' }]}
          />
        ) : (
          <Text size="xs" c={chrome.dim}>摘要尚未翻译</Text>
        )}
      </Group>
      <Text size="sm" style={{ lineHeight: 1.8, whiteSpace: 'pre-wrap' }} lang={view === 'zh' ? 'zh' : 'en'}>
        {view === 'zh' && hasTranslation ? abstract.translation : abstract.text}
      </Text>
    </Box>
  );
}

function SourceLinks({ data }: { data: PaperOverview }) {
  const { source } = data;
  const links: { label: string; href: string }[] = [];
  if (source.doi) links.push({ label: `DOI ${source.doi}`, href: `https://doi.org/${source.doi}` });
  if (source.arxiv_id) links.push({ label: `arXiv ${source.arxiv_id}`, href: `https://arxiv.org/abs/${source.arxiv_id}` });
  if (source.url && !links.some((link) => link.href === source.url)) links.push({ label: '原始链接', href: source.url });
  if (!links.length) return null;
  return (
    <Group gap="md">
      {links.map((link) => (
        <Anchor key={link.href} href={link.href} target="_blank" rel="noreferrer" size="sm" c={chrome.goldText}>
          {link.label} <IconExternalLink size={12} style={{ verticalAlign: 'middle' }} />
        </Anchor>
      ))}
    </Group>
  );
}

function jobIdFor(data: PaperOverview | undefined, kind: PaperJobKind): string | undefined {
  return data?.active_jobs?.find((job) => job.kind === kind)?.job_id;
}

export function PaperOverviewPage() {
  const { name = '', sourceId = '' } = useParams();
  const [searchParams] = useSearchParams();
  const overview = usePaperOverview(name, sourceId);
  const quickJob = usePaperJob(name, sourceId, 'paper-quick-analysis', jobIdFor(overview.data, 'paper-quick-analysis'));
  const deepJob = usePaperJob(name, sourceId, 'paper-deep-read', jobIdFor(overview.data, 'paper-deep-read'));

  if (READER_QUERY_KEYS.some((key) => searchParams.has(key))) {
    return <Navigate to={`${paperReaderPath(name, sourceId)}?${searchParams.toString()}`} replace />;
  }

  const backLink = (
    <Button component={Link} to={`/p/${encodeURIComponent(name)}/research`} variant="subtle" size="compact-sm" leftSection={<IconArrowLeft size={15} />}>
      研究台
    </Button>
  );

  if (overview.isPending) return <Center py="xl"><Loader /></Center>;
  if (overview.isError) {
    return (
      <Stack gap="md">
        <div>{backLink}</div>
        <Alert color="red" title="论文概览加载失败">
          <Text size="sm">{overview.error.message}</Text>
          <Button mt="sm" size="compact-sm" variant="default" leftSection={<IconRefresh size={14} />} onClick={() => void overview.refetch()}>
            重试
          </Button>
        </Alert>
      </Stack>
    );
  }

  const data = overview.data;
  const { source, progress } = data;
  const byline = [
    source.authors.length > 4 ? `${source.authors.slice(0, 4).join(', ')} 等` : source.authors.join(', '),
    [source.venue, source.year].filter(Boolean).join(' '),
  ].filter(Boolean).join(' · ');
  const readLabel = progress.last_page > 0 ? `继续阅读 · 第 ${progress.last_page} 页` : '开始阅读';
  const readerDisabled = !data.reader_available;

  return (
    <Stack gap="lg" pb="xl">
      <div>{backLink}</div>
      <Card withBorder radius="md" p="lg" style={{ background: `linear-gradient(135deg, ${chrome.panelBg}, ${chrome.cardBg})`, borderColor: BORDER_STRONG }}>
        <Text size="xs" fw={700} c={chrome.goldText}>论文概览</Text>
        <Title order={2} mt={4} lineClamp={3}>{source.title}</Title>
        {byline && <Text size="sm" c={chrome.dim} mt={6}>{byline}</Text>}
        <Group justify="space-between" align="flex-end" mt="md" gap="md">
          <Stack gap={6}>
            <SourceLinks data={data} />
            {source.tags.length > 0 && (
              <Group gap={6}>
                {source.tags.map((tag) => <Badge key={tag} size="sm" variant="dot" color="gray">{tag}</Badge>)}
              </Group>
            )}
          </Stack>
          <Group gap="sm">
            <Tooltip label={data.reader_unavailable_reason} disabled={!readerDisabled}>
              <Button
                component={Link}
                to={paperReaderPath(name, sourceId)}
                target={readerTabTarget(sourceId)}
                color="brand"
                leftSection={progress.last_page > 0 ? <IconPlayerPlay size={15} /> : <IconBook2 size={15} />}
                disabled={readerDisabled}
                onClick={(event) => { if (readerDisabled) event.preventDefault(); }}
              >
                {readLabel}
              </Button>
            </Tooltip>
            <Button
              component={Link}
              to={paperReaderPath(name, sourceId, { mode: 'compare' })}
              target={readerTabTarget(sourceId)}
              variant="default"
              leftSection={<IconLayoutColumns size={15} />}
              disabled={readerDisabled}
              onClick={(event) => { if (readerDisabled) event.preventDefault(); }}
            >
              对照阅读
            </Button>
          </Group>
        </Group>
        {readerDisabled && <Text size="xs" c={chrome.dim} mt="sm">{data.reader_unavailable_reason}</Text>}
      </Card>

      <Grid gutter="lg">
        <Grid.Col span={{ base: 12, md: 8 }}>
          <Stack gap="lg">
            <Card withBorder radius="md" p="lg" style={{ background: chrome.panelBg, borderColor: BORDER }}>
              <AbstractBlock data={data} />
            </Card>
            <QuickAnalysisCard analysis={data.quick_analysis} data={data} profile={name} sourceId={sourceId} job={quickJob} />
            <Divider color={BORDER} label={<Text size="xs" c={chrome.dim}>读完要点后，再决定是否深入</Text>} labelPosition="center" />
            <DeepReadCard deepRead={data.deep_read} data={data} profile={name} sourceId={sourceId} job={deepJob} />
          </Stack>
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: 4 }}>
          <SidePanels data={data} profile={name} sourceId={sourceId} />
        </Grid.Col>
      </Grid>
    </Stack>
  );
}
