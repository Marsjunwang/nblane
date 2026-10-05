import {
  Alert,
  Badge,
  Box,
  Button,
  Center,
  Group,
  List,
  Loader,
  Modal,
  Paper,
  Progress,
  ScrollArea,
  SegmentedControl,
  Stack,
  Switch,
  Table,
  Tabs,
  Text,
  Textarea,
  Tooltip,
} from '@mantine/core';
import { useHotkeys, useMediaQuery } from '@mantine/hooks';
import { IconArrowLeft, IconCheck, IconRefresh, IconSparkles, IconTarget, IconTrash } from '@tabler/icons-react';
import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { apiBase } from '../../api/client';
import { deleteCareerDraft, updateCareerDraft, useCareerWorkspace } from '../../api/hooks';
import type { CareerDraft, CareerMatchResult, CareerTailorResult, CareerWorkspaceResponse } from '../../api/types';
import { InlineDiff } from '../content/AIRewriteDialog';
import { runContentJob, type ContentJobHandle } from '../content/contentJobs';
import { ExportMenu, ResumePreview, SaveBadge } from './CareerShared';
import { careerHomePath } from './resumeModel';
import { useAutosave } from './useAutosave';

const TOP_BAR_HEIGHT = 52;

const VERDICT: Record<string, { label: string; color: string }> = {
  match: { label: '符合', color: 'teal' },
  partial: { label: '部分', color: 'yellow' },
  missing: { label: '缺失', color: 'red' },
};

interface TargetState {
  markdown: string;
  jd_text: string;
  notes: string;
  analysis: CareerMatchResult | null;
}

function MatchReport({ analysis }: { analysis: CareerMatchResult }) {
  const evidence = new Map(analysis.evidence.map((item) => [item.id, item]));
  const color = analysis.score >= 75 ? 'teal' : analysis.score >= 50 ? 'yellow' : 'red';
  const list = (title: string, items: string[], testid?: string) =>
    items.length > 0 && (
      <Box data-testid={testid}>
        <Text size="sm" fw={600} mb={4}>
          {title}
        </Text>
        <List size="sm" spacing={4}>
          {items.map((item) => (
            <List.Item key={item}>{item}</List.Item>
          ))}
        </List>
      </Box>
    );
  return (
    <Stack gap="md" data-testid="career-match-report">
      <Group gap="md" align="center" wrap="nowrap">
        <Text fz={34} fw={700} c={color} data-testid="career-match-score">
          {analysis.score}
        </Text>
        <Stack gap={4} style={{ flex: 1 }}>
          <Progress value={analysis.score} color={color} size="sm" />
          <Text size="sm">{analysis.summary}</Text>
          <Text size="xs" c="dimmed">
            {analysis.evidence_used > 0 ? `参考了 ${analysis.evidence_used} 条证据` : '未使用证据库'}
          </Text>
        </Stack>
      </Group>
      <Table verticalSpacing={6} data-testid="career-requirements">
        <Table.Thead>
          <Table.Tr>
            <Table.Th>JD 要求</Table.Th>
            <Table.Th w={70}>判定</Table.Th>
            <Table.Th>依据</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {analysis.requirements.map((row) => (
            <Table.Tr key={row.requirement}>
              <Table.Td>
                <Text size="sm">{row.requirement}</Text>
              </Table.Td>
              <Table.Td>
                <Badge size="sm" variant="light" color={VERDICT[row.verdict]?.color ?? 'gray'}>
                  {VERDICT[row.verdict]?.label ?? row.verdict}
                </Badge>
              </Table.Td>
              <Table.Td>
                <Text size="xs">{row.basis}</Text>
                {row.evidence_refs.map((ref) => (
                  <Tooltip key={ref} label={evidence.get(ref)?.summary || ref} multiline w={320} withinPortal>
                    <Badge size="xs" variant="outline" color="indigo" mt={4} mr={4} style={{ textTransform: 'none' }}>
                      证据 · {evidence.get(ref)?.title ?? ref}
                    </Badge>
                  </Tooltip>
                ))}
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
      {list('建议加强', analysis.strengthen, 'career-strengthen')}
      {list('真实缺口', analysis.gaps)}
      {analysis.keywords.length > 0 && (
        <Box>
          <Text size="sm" fw={600} mb={4}>
            关键词
          </Text>
          <Group gap={6}>
            {analysis.keywords.map((word) => (
              <Badge key={word} variant="outline" style={{ textTransform: 'none' }}>
                {word}
              </Badge>
            ))}
          </Group>
        </Box>
      )}
      {list('可以弱化', analysis.de_emphasize)}
      {analysis.interview_questions.length > 0 && (
        <Box>
          <Text size="sm" fw={600} mb={4}>
            可能的面试问题
          </Text>
          <Stack gap={6}>
            {analysis.interview_questions.map((item) => (
              <Paper key={item.question} withBorder p="xs" radius="sm">
                <Text size="sm" fw={600}>
                  {item.question}
                </Text>
                {item.answer_hint && (
                  <Text size="xs" c="dimmed" mt={2}>
                    {item.answer_hint}
                  </Text>
                )}
              </Paper>
            ))}
          </Stack>
        </Box>
      )}
    </Stack>
  );
}

function TargetInner({ profile, draft, data }: { profile: string; draft: CareerDraft; data: CareerWorkspaceResponse }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const wide = useMediaQuery('(min-width: 1200px)', true);
  const [pane, setPane] = useState<'jd' | 'resume'>('jd');
  const [draftView, setDraftView] = useState<'edit' | 'preview' | 'diff'>('preview');
  const [useEvidence, setUseEvidence] = useState(true);
  const [matching, setMatching] = useState(false);
  const [matchProgress, setMatchProgress] = useState('');
  const [matchError, setMatchError] = useState('');
  const [tailoring, setTailoring] = useState(false);
  const [tailorProgress, setTailorProgress] = useState('');
  const [tailorError, setTailorError] = useState('');
  const [candidate, setCandidate] = useState<string | null>(null);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const matchJob = useRef<ContentJobHandle<CareerMatchResult> | null>(null);
  const tailorJob = useRef<ContentJobHandle<CareerTailorResult> | null>(null);

  const draftUrl = `${apiBase()}/profiles/${encodeURIComponent(profile)}/career/drafts/${encodeURIComponent(draft.id)}`;
  const autosave = useAutosave<TargetState>({
    initial: { markdown: draft.markdown, jd_text: draft.jd_text, notes: draft.notes, analysis: draft.analysis ?? null },
    etag: draft.etag,
    save: async (value, etag, isAutosave) => {
      const saved = await updateCareerDraft(
        profile,
        draft.id,
        { ...value, markdown: value.markdown.trim() ? value.markdown : undefined },
        etag,
        isAutosave,
      );
      void queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'career'], refetchType: 'none' });
      return saved.etag;
    },
    keepalive: (value) => ({
      url: draftUrl,
      method: 'PUT',
      body: JSON.stringify({ ...value, markdown: value.markdown.trim() ? value.markdown : undefined }),
    }),
  });
  const state = autosave.value;
  const set = (patch: Partial<TargetState>) => autosave.edit((previous) => ({ ...previous, ...patch }));

  useEffect(
    () => () => {
      matchJob.current?.cancel();
      tailorJob.current?.cancel();
    },
    [],
  );
  useHotkeys([['mod+S', () => void autosave.flush()]], []);

  const jobInput = () => ({
    resume_md: data.resume_markdown,
    jd_text: state.jd_text,
    notes: state.notes,
    use_evidence: useEvidence,
  });

  const runMatch = () => {
    matchJob.current?.cancel();
    setMatching(true);
    setMatchError('');
    const job = runContentJob<CareerMatchResult>(profile, 'career-match', jobInput(), setMatchProgress);
    matchJob.current = job;
    job.result
      .then((analysis) => set({ analysis }))
      .catch((err: unknown) => setMatchError(err instanceof Error ? err.message : String(err)))
      .finally(() => setMatching(false));
  };

  const runTailor = () => {
    tailorJob.current?.cancel();
    setTailoring(true);
    setTailorError('');
    const edited = state.markdown.trim() && state.markdown.trim() !== data.resume_markdown.trim();
    const job = runContentJob<CareerTailorResult>(
      profile,
      'career-tailor',
      { ...jobInput(), analysis: state.analysis, current_draft: edited ? state.markdown : '' },
      setTailorProgress,
    );
    tailorJob.current = job;
    job.result
      .then((result) => setCandidate(result.markdown))
      .catch((err: unknown) => setTailorError(err instanceof Error ? err.message : String(err)))
      .finally(() => setTailoring(false));
  };

  const back = async () => {
    await autosave.flush();
    navigate(careerHomePath(profile));
  };

  const remove = async () => {
    await deleteCareerDraft(profile, draft.id);
    await queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'career'] });
    navigate(careerHomePath(profile));
  };

  const aiHint = !data.ai_available ? '未配置 LLM（LLM_API_KEY），AI 匹配与定制不可用。' : '';

  const jdPane = (
    <Stack gap="md">
      <Textarea
        label="职位描述（JD）"
        placeholder="粘贴完整 JD：职责、任职要求、加分项"
        autosize
        minRows={8}
        maxRows={18}
        value={state.jd_text}
        onChange={(event) => set({ jd_text: event.currentTarget.value })}
        data-testid="career-jd"
      />
      <Textarea
        label="补充说明（可选）"
        description="简历和证据里没写、但真实存在的经历；或希望突出 / 回避的方向"
        autosize
        minRows={2}
        maxRows={6}
        value={state.notes}
        onChange={(event) => set({ notes: event.currentTarget.value })}
      />
      <Group justify="space-between">
        <Tooltip label="把证据库里已审阅的事实作为补充依据（不读断言、技能树、看板）" withinPortal multiline w={280}>
          <div>
            <Switch size="xs" label="参考证据库" checked={useEvidence} onChange={(event) => setUseEvidence(event.currentTarget.checked)} />
          </div>
        </Tooltip>
        <Button
          leftSection={matching ? <Loader size={14} /> : <IconTarget size={16} />}
          onClick={runMatch}
          disabled={!state.jd_text.trim() || matching || !data.ai_available}
          data-testid="career-match"
        >
          {matching ? matchProgress || '分析中…' : state.analysis ? '重新匹配' : '匹配分析'}
        </Button>
      </Group>
      {aiHint && (
        <Text size="xs" c="dimmed">
          {aiHint}
        </Text>
      )}
      {matchError && (
        <Alert color="red" p="xs" title="匹配失败">
          <Text size="xs">{matchError}</Text>
        </Alert>
      )}
      {state.analysis && <MatchReport analysis={state.analysis} />}
    </Stack>
  );

  const resumePane = (
    <Stack gap="sm" style={{ height: '100%' }}>
      <Group justify="space-between" wrap="nowrap">
        <SegmentedControl
          size="xs"
          value={draftView}
          onChange={(value) => setDraftView(value as 'edit' | 'preview' | 'diff')}
          data={[
            { value: 'preview', label: '预览' },
            { value: 'edit', label: '编辑 Markdown' },
            { value: 'diff', label: '对比主简历' },
          ]}
        />
        <Button
          size="xs"
          variant="light"
          leftSection={tailoring ? <Loader size={12} /> : <IconSparkles size={15} />}
          onClick={runTailor}
          disabled={!state.jd_text.trim() || tailoring || !data.ai_available}
          data-testid="career-tailor"
        >
          {tailoring ? tailorProgress || '生成中…' : 'AI 生成定制版'}
        </Button>
      </Group>
      {tailorError && (
        <Alert color="red" p="xs">
          <Text size="xs">{tailorError}</Text>
        </Alert>
      )}
      <Box style={{ flex: 1, minHeight: 480 }}>
        {draftView === 'edit' && (
          <Textarea
            aria-label="定制简历 Markdown"
            value={state.markdown}
            onChange={(event) => set({ markdown: event.currentTarget.value })}
            styles={{ input: { fontFamily: 'var(--mantine-font-family-monospace)', fontSize: 13, height: '100%' }, wrapper: { height: '100%' } }}
            style={{ height: '100%' }}
            data-testid="career-draft-markdown"
          />
        )}
        {draftView === 'preview' && <ResumePreview profile={profile} markdown={state.markdown} height="100%" />}
        {draftView === 'diff' && (
          <ScrollArea h="100%">
            <Paper withBorder p="sm">
              <InlineDiff before={data.resume_markdown} after={state.markdown} />
            </Paper>
          </ScrollArea>
        )}
      </Box>
    </Stack>
  );

  return (
    <Box data-testid="career-target" style={{ minHeight: 'calc(100vh - 56px)' }}>
      <Group
        justify="space-between"
        wrap="nowrap"
        gap="sm"
        px="md"
        h={TOP_BAR_HEIGHT}
        style={{
          position: 'sticky',
          top: 'var(--app-shell-header-height, 56px)',
          zIndex: 20,
          background: 'var(--mantine-color-body)',
          borderBottom: '1px solid var(--mantine-color-dark-5)',
        }}
      >
        <Group gap="xs" wrap="nowrap" style={{ minWidth: 0 }}>
          <Button size="xs" variant="subtle" color="gray" leftSection={<IconArrowLeft size={15} />} onClick={() => void back()} data-testid="career-back">
            求职工作台
          </Button>
          <Text fw={600} size="sm" truncate data-testid="career-target-name">
            {draft.target}
          </Text>
          <SaveBadge state={autosave.state} savedAt={autosave.savedAt} testid="career-save-state" />
        </Group>
        <Group gap="xs" wrap="nowrap">
          <ExportMenu profile={profile} pdfAvailable={data.pdf_available} source={{ draft_id: draft.id }} beforeExport={autosave.flush} />
          <Button size="xs" variant="subtle" color="red" leftSection={<IconTrash size={14} />} onClick={() => setDeleteOpen(true)}>
            删除
          </Button>
        </Group>
      </Group>
      {autosave.state === 'conflict' && (
        <Alert color="orange" m="md" title="定制简历已在别处修改">
          <Group justify="space-between">
            <Text size="sm">已暂停自动保存。刷新会载入最新版本。</Text>
            <Button size="xs" variant="default" leftSection={<IconRefresh size={14} />} onClick={() => window.location.reload()}>
              刷新
            </Button>
          </Group>
        </Alert>
      )}
      {autosave.state === 'error' && (
        <Alert color="red" m="md" title="保存失败">
          {autosave.error}
        </Alert>
      )}
      {wide ? (
        <Group align="flex-start" wrap="nowrap" gap={0}>
          <Box p="md" style={{ width: 560, flexShrink: 0 }}>
            {jdPane}
          </Box>
          <Box
            p="md"
            style={{
              flex: 1,
              minWidth: 0,
              position: 'sticky',
              top: `calc(var(--app-shell-header-height, 56px) + ${TOP_BAR_HEIGHT}px)`,
              height: `calc(100vh - 56px - ${TOP_BAR_HEIGHT}px)`,
            }}
          >
            {resumePane}
          </Box>
        </Group>
      ) : (
        <Tabs value={pane} onChange={(value) => setPane((value as 'jd' | 'resume') ?? 'jd')} p="md">
          <Tabs.List mb="md">
            <Tabs.Tab value="jd">JD 与匹配</Tabs.Tab>
            <Tabs.Tab value="resume">定制简历</Tabs.Tab>
          </Tabs.List>
          <Tabs.Panel value="jd">{jdPane}</Tabs.Panel>
          <Tabs.Panel value="resume" h={720}>
            {resumePane}
          </Tabs.Panel>
        </Tabs>
      )}

      <Modal opened={candidate !== null} onClose={() => setCandidate(null)} title="AI 定制简历（候选）" size="xl" centered>
        {candidate !== null && (
          <Stack gap="md">
            <Text size="xs" c="dimmed">
              对比当前定制稿。候选尚未写入，接受后替换定制稿（主简历不变）。请核对每条事实。
            </Text>
            <ScrollArea.Autosize mah="60vh">
              <Paper withBorder p="sm" data-testid="career-tailor-diff">
                <InlineDiff before={state.markdown} after={candidate} />
              </Paper>
            </ScrollArea.Autosize>
            <Group justify="space-between">
              <Button variant="subtle" leftSection={<IconRefresh size={14} />} onClick={runTailor} disabled={tailoring}>
                重新生成
              </Button>
              <Group gap="xs">
                <Button variant="default" onClick={() => setCandidate(null)}>
                  放弃
                </Button>
                <Button
                  leftSection={<IconCheck size={15} />}
                  onClick={() => {
                    set({ markdown: candidate });
                    setCandidate(null);
                    setDraftView('preview');
                  }}
                  data-testid="career-tailor-accept"
                >
                  接受
                </Button>
              </Group>
            </Group>
          </Stack>
        )}
      </Modal>

      <Modal opened={deleteOpen} onClose={() => setDeleteOpen(false)} title="删除目标岗位" centered>
        <Stack gap="md">
          <Text size="sm">删除「{draft.target}」的 JD、匹配结果和定制简历？主简历不受影响，可从 Git 备份找回。</Text>
          <Group justify="flex-end">
            <Button variant="default" onClick={() => setDeleteOpen(false)}>
              取消
            </Button>
            <Button color="red" onClick={() => void remove()} data-testid="career-delete-confirm">
              删除
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Box>
  );
}

/** One target job: JD, structured match report and the tailored resume draft. */
export function TargetWorkspace({ profile, draftId }: { profile: string; draftId: string }) {
  const career = useCareerWorkspace(profile);
  if (career.isPending) {
    return (
      <Center py="xl">
        <Loader />
      </Center>
    );
  }
  const draft = career.data?.drafts.find((item) => item.id === draftId);
  if (career.isError || !career.data || !draft) {
    return (
      <Alert color="red" m="md" title="找不到这个岗位">
        {career.error?.message ?? '它可能已被删除。'}
      </Alert>
    );
  }
  return <TargetInner key={draft.id} profile={profile} draft={draft} data={career.data} />;
}
