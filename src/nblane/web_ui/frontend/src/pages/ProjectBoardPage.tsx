import {
  Accordion,
  Alert,
  Badge,
  Button,
  Card,
  Center,
  Group,
  Loader,
  MultiSelect,
  NativeSelect,
  Progress,
  Select,
  Stack,
  Table,
  Tabs,
  Text,
  Textarea,
  TextInput,
  Title,
} from '@mantine/core';
import {
  IconArchive,
  IconBulb,
  IconDeviceFloppy,
  IconPlus,
} from '@tabler/icons-react';
import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';

import { MutationErrorAlert } from '../components/ConflictAlert';
import {
  useAddProjectMilestone,
  useAddProjectTask,
  useArchiveProjectCase,
  useCreateJob,
  useCreateProjectCase,
  useDeleteProjectMilestone,
  useMoveProjectTask,
  useProjectBoard,
  useSaveProjectCase,
  useSaveProjectMilestone,
} from '../api/hooks';
import { streamJob } from '../api/jobs';
import type {
  ProjectBoard,
  ProjectCase,
  ProjectMilestone,
  ProjectRefOption,
  ProjectSuggestRefsResponse,
} from '../api/types';

const PROJECT_STATUS_LABELS: Record<string, string> = {
  active: '进行中',
  paused: '已暂停',
  completed: '已完成',
  archived: '已归档',
};
const PROJECT_STATUSES = Object.keys(PROJECT_STATUS_LABELS);

const KIND_LABELS: Record<string, string> = {
  internal: '内部',
  research: '研究',
  work: '工作',
  side_project: '副业',
  learning: '学习',
};

const VISIBILITY_LABELS: Record<string, string> = {
  private: '私有',
  public: '公开',
};

const MILESTONE_STATUS_LABELS: Record<string, string> = {
  planned: '计划中',
  active: '进行中',
  completed: '已完成',
  archived: '已归档',
};
const MILESTONE_STATUSES = Object.keys(MILESTONE_STATUS_LABELS);

const SECTION_LABELS: Record<string, string> = {
  Queue: '队列',
  Doing: '进行中',
  Done: '已完成',
  'Someday / Maybe': '以后再说',
};
const KANBAN_SECTIONS = Object.keys(SECTION_LABELS);

function labeledData(labels: Record<string, string>, keys: string[]) {
  return keys.map((key) => ({ value: key, label: labels[key] ?? key }));
}

/** MultiSelect rows: options (tasks filtered by owner) + missing selected ids. */
function refSelectData(
  options: ProjectRefOption[],
  selected: string[],
  caseId?: string,
): { value: string; label: string }[] {
  const rows = caseId
    ? options.filter((option) => !option.owner || option.owner === caseId)
    : options;
  const data = rows.map((option) => ({
    value: option.id,
    label: option.label || option.id,
  }));
  for (const ref of selected) {
    if (ref && !data.some((row) => row.value === ref)) {
      data.push({ value: ref, label: `${ref}（缺失引用）` });
    }
  }
  return data;
}

interface CaseDraft {
  title: string;
  status: string;
  kind: string;
  visibility: string;
  time_range: string;
  summary: string;
  notes: string;
  goal_refs: string[];
  task_refs: string[];
  evidence_refs: string[];
  source_refs: string[];
  experience_refs: string[];
  output_refs: string[];
}

function draftFromCase(projectCase: ProjectCase): CaseDraft {
  return {
    title: projectCase.title ?? '',
    status: projectCase.status ?? 'active',
    kind: projectCase.kind ?? 'internal',
    visibility: projectCase.visibility ?? 'private',
    time_range: projectCase.time_range ?? '',
    summary: projectCase.summary ?? '',
    notes: projectCase.notes ?? '',
    goal_refs: [...(projectCase.goal_refs ?? [])],
    task_refs: [...(projectCase.task_refs ?? [])],
    evidence_refs: [...(projectCase.evidence_refs ?? [])],
    source_refs: [...(projectCase.source_refs ?? [])],
    experience_refs: [...(projectCase.experience_refs ?? [])],
    output_refs: [...(projectCase.output_refs ?? [])],
  };
}

const SUGGEST_FIELD_LABELS: Record<string, string> = {
  goal_refs: '目标',
  task_refs: '任务',
  evidence_refs: '证据',
  source_refs: '资料',
  output_refs: '输出',
};

/** Backend suggest-refs job phases -> Chinese label + coarse progress percentage. */
const SUGGEST_PHASES: Record<string, { label: string; pct: number }> = {
  queued: { label: '排队中', pct: 10 },
  starting: { label: '启动中', pct: 20 },
  collecting: { label: '收集候选', pct: 45 },
  suggesting: { label: '生成建议', pct: 80 },
  done: { label: '完成', pct: 100 },
};

function suggestPhase(phase: string): { label: string; pct: number } {
  return SUGGEST_PHASES[phase] ?? { label: phase || '进行中', pct: 40 };
}

interface SuggestJobProgress {
  jobId: string;
  phase: string;
  message: string;
}

/** Refetch the project board after a 412 conflict. */
function useRefreshBoard() {
  const { name = '' } = useParams();
  const queryClient = useQueryClient();
  return () =>
    void queryClient.invalidateQueries({ queryKey: ['profiles', name, 'project-board'] });
}

function CreateCaseCard({
  board,
  etag,
  onCreated,
}: {
  board: ProjectBoard;
  etag: string;
  onCreated: (caseId: string) => void;
}) {
  const { name = '' } = useParams();
  const [opened, setOpened] = useState((board.cases ?? []).length === 0);
  const [title, setTitle] = useState('');
  const [caseId, setCaseId] = useState('');
  const [kind, setKind] = useState('internal');
  const [visibility, setVisibility] = useState('private');
  const [summary, setSummary] = useState('');
  const [goalRefs, setGoalRefs] = useState<string[]>([]);
  const create = useCreateProjectCase(name);
  const refreshBoard = useRefreshBoard();

  const submit = () => {
    if (!title.trim()) {
      return;
    }
    create.mutate(
      {
        body: {
          title: title.trim(),
          id: caseId.trim(),
          status: 'active',
          kind,
          visibility,
          summary: summary.trim(),
          goal_refs: goalRefs,
          evidence_refs: [],
        },
        etag,
      },
      {
        onSuccess: (result) => {
          setTitle('');
          setCaseId('');
          setSummary('');
          setGoalRefs([]);
          onCreated(result.case.id);
        },
      },
    );
  };

  return (
    <Card withBorder radius="md" data-testid="create-case-form">
      <Group justify="space-between">
        <Text fw={500}>新建项目</Text>
        <Button
          size="compact-sm"
          variant="subtle"
          onClick={() => setOpened((value) => !value)}
          aria-expanded={opened}
        >
          {opened ? '收起' : '展开'}
        </Button>
      </Group>
      {opened && (
        <Stack gap="sm" mt="sm">
          <Group grow align="flex-start">
            <TextInput
              label="标题"
              value={title}
              onChange={(event) => setTitle(event.currentTarget.value)}
              required
            />
            <TextInput
              label="ID（留空自动生成）"
              value={caseId}
              onChange={(event) => setCaseId(event.currentTarget.value)}
            />
          </Group>
          <Group grow align="flex-start">
            <Select
              label="类型"
              data={labeledData(KIND_LABELS, Object.keys(KIND_LABELS))}
              value={kind}
              onChange={(value) => setKind(value ?? 'internal')}
            />
            <Select
              label="可见性"
              data={labeledData(VISIBILITY_LABELS, Object.keys(VISIBILITY_LABELS))}
              value={visibility}
              onChange={(value) => setVisibility(value ?? 'private')}
            />
          </Group>
          <Textarea
            label="摘要"
            value={summary}
            onChange={(event) => setSummary(event.currentTarget.value)}
            minRows={2}
          />
          <MultiSelect
            label="关联目标"
            data={refSelectData(board.options?.goals ?? [], goalRefs)}
            value={goalRefs}
            onChange={setGoalRefs}
          />
          <MutationErrorAlert error={create.error} title="创建失败" onRefetch={refreshBoard} />
          <Group>
            <Button
              leftSection={<IconPlus size={14} />}
              onClick={submit}
              loading={create.isPending}
              disabled={!title.trim()}
            >
              创建项目
            </Button>
          </Group>
        </Stack>
      )}
    </Card>
  );
}

function BasicsTab({
  projectCase,
  board,
  etag,
}: {
  projectCase: ProjectCase;
  board: ProjectBoard;
  etag: string;
}) {
  const { name = '' } = useParams();
  const [draft, setDraft] = useState<CaseDraft>(() => draftFromCase(projectCase));
  const [dirty, setDirty] = useState(false);
  const [suggestions, setSuggestions] = useState<ProjectSuggestRefsResponse | null>(null);
  const [suggestJob, setSuggestJob] = useState<SuggestJobProgress | null>(null);
  const [suggestError, setSuggestError] = useState<{ code: string; message: string } | null>(
    null,
  );
  const save = useSaveProjectCase(name);
  const archive = useArchiveProjectCase(name);
  const createJob = useCreateJob(name);
  const refreshBoard = useRefreshBoard();
  const stopStreamRef = useRef<(() => void) | null>(null);

  // CaseDetail is keyed by case id only, so board-level refetches re-render
  // this tab instead of remounting it. Follow server-side changes only while
  // the local draft is untouched; a dirty draft always wins.
  const lastSynced = useRef(projectCase);
  useEffect(() => {
    if (!dirty && projectCase !== lastSynced.current) {
      lastSynced.current = projectCase;
      setDraft(draftFromCase(projectCase));
    }
  }, [projectCase, dirty]);

  const stopStream = () => {
    stopStreamRef.current?.();
    stopStreamRef.current = null;
  };

  // Cancel the SSE subscription on unmount and whenever the profile or case
  // changes; a stale stream must never write another case's state.
  useEffect(() => {
    setSuggestJob(null);
    setSuggestions(null);
    setSuggestError(null);
    return stopStream;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [name, projectCase.id]);

  const set = <K extends keyof CaseDraft>(field: K, value: CaseDraft[K]) => {
    setDirty(true);
    setDraft((prev) => ({ ...prev, [field]: value }));
  };

  const runSave = () =>
    save.mutate(
      { caseId: projectCase.id, body: { ...draft }, etag },
      { onSuccess: () => setDirty(false) },
    );

  const runSuggest = () => {
    stopStream();
    setSuggestJob(null);
    setSuggestions(null);
    setSuggestError(null);
    createJob.mutate(
      { kind: 'project-suggest-refs', input: { case_id: projectCase.id } },
      {
        onSuccess: (created) => {
          const jobId = created.job_id;
          setSuggestJob({ jobId, phase: created.job.phase || 'queued', message: '' });
          stopStreamRef.current = streamJob(name, jobId, {
            onProgress: (frame) => {
              setSuggestJob((prev) =>
                prev && prev.jobId === jobId
                  ? {
                      jobId,
                      phase: frame.event?.phase || frame.job?.phase || prev.phase,
                      message: frame.event?.message || prev.message,
                    }
                  : prev,
              );
            },
            onDone: (frame) => {
              stopStream();
              setSuggestJob(null);
              if (frame.result) {
                setSuggestions(frame.result as unknown as ProjectSuggestRefsResponse);
              } else {
                setSuggestError({
                  code: 'empty_result',
                  message: '任务完成但未返回结果,请重试。',
                });
              }
            },
            onError: (frame) => {
              stopStream();
              setSuggestJob(null);
              setSuggestError(
                frame?.error ?? {
                  code: 'stream_error',
                  message: '进度流中断,请稍后重试。',
                },
              );
            },
          });
        },
      },
    );
  };

  const mergeSuggestions = () => {
    if (!suggestions) {
      return;
    }
    setDirty(true);
    setDraft((prev) => {
      const next = { ...prev };
      for (const field of Object.keys(SUGGEST_FIELD_LABELS) as (keyof CaseDraft)[]) {
        const proposed = suggestions.suggestions?.[field] ?? [];
        const merged = [...(prev[field] as string[])];
        for (const ref of proposed) {
          if (!merged.includes(ref)) {
            merged.push(ref);
          }
        }
        (next[field] as string[]) = merged;
      }
      return next;
    });
    setSuggestions(null);
  };

  const suggestionCount = suggestions
    ? Object.values(suggestions.suggestions ?? {}).reduce((sum, list) => sum + list.length, 0)
    : 0;
  const suggestUnavailable = suggestError?.code === 'project_suggest_refs_failed';

  return (
    <Stack gap="sm">
      <Group grow align="flex-start">
        <TextInput
          label="标题"
          value={draft.title}
          onChange={(event) => set('title', event.currentTarget.value)}
          required
        />
        <TextInput label="ID" value={projectCase.id} disabled />
      </Group>
      <Group grow align="flex-start">
        <Select
          label="状态"
          data={labeledData(PROJECT_STATUS_LABELS, PROJECT_STATUSES)}
          value={draft.status}
          onChange={(value) => set('status', value ?? projectCase.status ?? 'active')}
        />
        <Select
          label="类型"
          data={labeledData(KIND_LABELS, Object.keys(KIND_LABELS))}
          value={draft.kind}
          onChange={(value) => set('kind', value ?? 'internal')}
        />
        <Select
          label="可见性"
          data={labeledData(VISIBILITY_LABELS, Object.keys(VISIBILITY_LABELS))}
          value={draft.visibility}
          onChange={(value) => set('visibility', value ?? 'private')}
        />
      </Group>
      <TextInput
        label="时间范围"
        description="格式如 2026-09-01/2026-12-31;留空时由任务日期推导"
        placeholder={projectCase.derived_time_range || '未设置'}
        value={draft.time_range}
        onChange={(event) => set('time_range', event.currentTarget.value)}
      />
      <Textarea
        label="摘要"
        value={draft.summary}
        onChange={(event) => set('summary', event.currentTarget.value)}
        minRows={2}
      />
      <Textarea
        label="备注"
        value={draft.notes}
        onChange={(event) => set('notes', event.currentTarget.value)}
        minRows={2}
      />
      <MultiSelect
        label="关联目标"
        data={refSelectData(board.options?.goals ?? [], draft.goal_refs)}
        value={draft.goal_refs}
        onChange={(value) => set('goal_refs', value)}
      />
      <MultiSelect
        label="关联任务"
        description="只列出未归属其他项目的看板任务"
        data={refSelectData(board.options?.tasks ?? [], draft.task_refs, projectCase.id)}
        value={draft.task_refs}
        onChange={(value) => set('task_refs', value)}
      />
      <MultiSelect
        label="关联证据"
        data={refSelectData(board.options?.evidence ?? [], draft.evidence_refs)}
        value={draft.evidence_refs}
        onChange={(value) => set('evidence_refs', value)}
      />
      <MultiSelect
        label="关联资料"
        data={refSelectData(board.options?.sources ?? [], draft.source_refs)}
        value={draft.source_refs}
        onChange={(value) => set('source_refs', value)}
      />
      <MultiSelect
        label="关联经历"
        data={refSelectData(board.options?.experiences ?? [], draft.experience_refs)}
        value={draft.experience_refs}
        onChange={(value) => set('experience_refs', value)}
      />
      <MultiSelect
        label="关联输出"
        data={refSelectData(board.options?.outputs ?? [], draft.output_refs)}
        value={draft.output_refs}
        onChange={(value) => set('output_refs', value)}
      />

      <MutationErrorAlert
        error={save.error ?? archive.error}
        title="保存失败"
        onRefetch={refreshBoard}
      />

      <Group gap="sm" wrap="wrap">
        <Button
          leftSection={<IconDeviceFloppy size={14} />}
          onClick={runSave}
          loading={save.isPending}
          disabled={!draft.title.trim()}
        >
          保存项目
        </Button>
        <Button
          variant="default"
          leftSection={<IconBulb size={14} />}
          onClick={runSuggest}
          loading={createJob.isPending}
          disabled={Boolean(suggestJob)}
          data-testid="suggest-refs-button"
        >
          AI 建议引用
        </Button>
        {projectCase.status !== 'archived' && (
          <Button
            variant="outline"
            color="gray"
            leftSection={<IconArchive size={14} />}
            onClick={() => archive.mutate({ caseId: projectCase.id, etag })}
            loading={archive.isPending}
          >
            归档项目
          </Button>
        )}
      </Group>

      {createJob.isError && (
        <Alert color="red" title="创建建议任务失败" data-testid="suggest-create-error">
          {createJob.error.message}
        </Alert>
      )}
      {suggestJob && (
        <Card withBorder radius="md" padding="sm" data-testid="suggest-progress">
          <Group justify="space-between" align="center">
            <Text fw={500} size="sm">
              AI 建议引用进行中
            </Text>
            <Badge color="violet" variant="light">
              {suggestPhase(suggestJob.phase).label}
            </Badge>
          </Group>
          <Progress
            value={suggestPhase(suggestJob.phase).pct}
            color="violet"
            animated
            mt="xs"
            aria-label="AI 建议进度"
          />
          <Text size="xs" c="dimmed" mt="xs">
            {suggestJob.message || 'AI 正在分析项目与候选引用,通常需要十几秒。'}
          </Text>
        </Card>
      )}
      {suggestUnavailable && suggestError && (
        <Alert color="yellow" title="AI 建议不可用" data-testid="suggest-error">
          {suggestError.message}。配置 LLM 后重试;其余功能不受影响。
        </Alert>
      )}
      {suggestError && !suggestUnavailable && (
        <Alert color="red" title="AI 建议失败" data-testid="suggest-failed">
          {suggestError.message}
        </Alert>
      )}
      {suggestions && (
        <Alert color="blue" title="AI 引用建议" data-testid="suggest-result">
          <Stack gap="xs">
            <Text size="sm">
              共 {suggestionCount} 条建议
              {suggestions.rationale ? `;理由:${suggestions.rationale}` : ''}
            </Text>
            <Text size="xs" c="dimmed">
              {Object.entries(suggestions.suggestions ?? {})
                .filter(([, list]) => list.length > 0)
                .map(
                  ([field, list]) =>
                    `${SUGGEST_FIELD_LABELS[field] ?? field}: ${list.join(', ')}`,
                )
                .join(' · ') || '无新增建议'}
            </Text>
            <Group>
              <Button size="compact-sm" onClick={mergeSuggestions}>
                合并到表单
              </Button>
              <Button size="compact-sm" variant="subtle" onClick={() => setSuggestions(null)}>
                忽略
              </Button>
            </Group>
          </Stack>
        </Alert>
      )}
    </Stack>
  );
}

function MilestoneEditor({
  projectCase,
  milestone,
  etag,
}: {
  projectCase: ProjectCase;
  milestone: ProjectMilestone;
  etag: string;
}) {
  const { name = '' } = useParams();
  const [title, setTitle] = useState(milestone.title ?? '');
  const [status, setStatus] = useState(milestone.status ?? 'planned');
  const [target, setTarget] = useState(milestone.target ?? '');
  const [date, setDate] = useState(milestone.date ?? '');
  const [summary, setSummary] = useState(milestone.summary ?? '');
  const save = useSaveProjectMilestone(name);
  const remove = useDeleteProjectMilestone(name);
  const refreshBoard = useRefreshBoard();

  return (
    <Stack gap="xs">
      <Group grow align="flex-start">
        <TextInput
          label="标题"
          value={title}
          onChange={(event) => setTitle(event.currentTarget.value)}
        />
        <Select
          label="状态"
          data={labeledData(MILESTONE_STATUS_LABELS, MILESTONE_STATUSES)}
          value={status}
          onChange={(value) => setStatus(value ?? 'planned')}
        />
      </Group>
      <Group grow align="flex-start">
        <TextInput
          label="目标"
          value={target}
          onChange={(event) => setTarget(event.currentTarget.value)}
        />
        <TextInput
          label="日期"
          type="date"
          value={date}
          onChange={(event) => setDate(event.currentTarget.value)}
        />
      </Group>
      <Textarea
        label="摘要"
        value={summary}
        onChange={(event) => setSummary(event.currentTarget.value)}
        minRows={2}
      />
      <MutationErrorAlert
        error={save.error ?? remove.error}
        title="操作失败"
        onRefetch={refreshBoard}
      />
      <Group>
        <Button
          size="compact-sm"
          leftSection={<IconDeviceFloppy size={14} />}
          disabled={!title.trim()}
          loading={save.isPending}
          onClick={() =>
            save.mutate({
              caseId: projectCase.id,
              milestoneId: milestone.id,
              body: { title, status, target, date, summary },
              etag,
            })
          }
        >
          保存里程碑
        </Button>
        <Button
          size="compact-sm"
          variant="outline"
          color="red"
          loading={remove.isPending}
          onClick={() =>
            remove.mutate({ caseId: projectCase.id, milestoneId: milestone.id, etag })
          }
        >
          删除
        </Button>
      </Group>
    </Stack>
  );
}

function MilestonesTab({
  projectCase,
  etag,
}: {
  projectCase: ProjectCase;
  etag: string;
}) {
  const { name = '' } = useParams();
  const [title, setTitle] = useState('');
  const [target, setTarget] = useState('');
  const [date, setDate] = useState('');
  const add = useAddProjectMilestone(name);
  const refreshBoard = useRefreshBoard();

  const submit = () => {
    if (!title.trim()) {
      return;
    }
    add.mutate(
      {
        caseId: projectCase.id,
        body: { title: title.trim(), id: '', target: target.trim(), date, summary: '' },
        etag,
      },
      {
        onSuccess: () => {
          setTitle('');
          setTarget('');
          setDate('');
        },
      },
    );
  };

  return (
    <Stack gap="sm">
      {(projectCase.milestones ?? []).length === 0 && (
        <Text c="dimmed" size="sm">
          还没有里程碑。
        </Text>
      )}
      <Accordion variant="separated">
        {(projectCase.milestones ?? []).map((milestone) => (
          <Accordion.Item key={milestone.id} value={milestone.id}>
            <Accordion.Control>
              <Group gap="sm">
                <Text size="sm" fw={500}>
                  {milestone.title || milestone.id}
                </Text>
                <Badge size="sm" variant="light">
                  {MILESTONE_STATUS_LABELS[milestone.status ?? ''] ??
                    milestone.status}
                </Badge>
                {(milestone.total_count ?? 0) > 0 && (
                  <Badge size="sm" variant="light" color="green">
                    {milestone.done_count}/{milestone.total_count} 完成
                  </Badge>
                )}
              </Group>
            </Accordion.Control>
            <Accordion.Panel>
              <MilestoneEditor
                projectCase={projectCase}
                milestone={milestone}
                etag={etag}
              />
            </Accordion.Panel>
          </Accordion.Item>
        ))}
      </Accordion>

      <Card withBorder radius="md" data-testid="add-milestone-form">
        <Stack gap="sm">
          <Text fw={500} size="sm">
            添加里程碑
          </Text>
          <Group grow align="flex-start">
            <TextInput
              label="标题"
              value={title}
              onChange={(event) => setTitle(event.currentTarget.value)}
            />
            <TextInput
              label="目标"
              value={target}
              onChange={(event) => setTarget(event.currentTarget.value)}
            />
            <TextInput
              label="日期"
              type="date"
              value={date}
              onChange={(event) => setDate(event.currentTarget.value)}
            />
          </Group>
          <MutationErrorAlert error={add.error} title="添加失败" onRefetch={refreshBoard} />
          <Group>
            <Button
              size="compact-sm"
              leftSection={<IconPlus size={14} />}
              disabled={!title.trim()}
              loading={add.isPending}
              onClick={submit}
            >
              添加里程碑
            </Button>
          </Group>
        </Stack>
      </Card>
    </Stack>
  );
}

function TasksTab({
  projectCase,
  etag,
}: {
  projectCase: ProjectCase;
  etag: string;
}) {
  const { name = '' } = useParams();
  const [title, setTitle] = useState('');
  const [section, setSection] = useState('Queue');
  const [milestoneId, setMilestoneId] = useState('');
  const add = useAddProjectTask(name);
  const move = useMoveProjectTask(name);
  const refreshBoard = useRefreshBoard();

  const milestoneOptions = [
    { value: '', label: '无里程碑' },
    ...(projectCase.milestones ?? [])
      .filter((milestone) => milestone.id)
      .map((milestone) => ({
        value: milestone.id,
        label: milestone.title || milestone.id,
      })),
  ];

  const submit = () => {
    if (!title.trim()) {
      return;
    }
    add.mutate(
      {
        caseId: projectCase.id,
        body: {
          title: title.trim(),
          section,
          milestone_id: milestoneId,
          context: '',
          date: '',
        },
        etag,
      },
      { onSuccess: () => setTitle('') },
    );
  };

  const tasks = projectCase.tasks ?? [];
  return (
    <Stack gap="sm">
      {tasks.length === 0 ? (
        <Text c="dimmed" size="sm">
          还没有关联任务。
        </Text>
      ) : (
        <Card withBorder radius="md" p={0}>
          <Table.ScrollContainer minWidth={420}>
            <Table highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>任务</Table.Th>
                <Table.Th>看板列</Table.Th>
                <Table.Th>日期</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {tasks.map((task) => (
                <Table.Tr key={task.id} data-testid={`project-task-${task.id}`}>
                  <Table.Td>
                    <Text size="sm">
                      {task.title || task.id}
                      {task.archived ? '(已归档)' : ''}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <NativeSelect
                      size="xs"
                      data={labeledData(SECTION_LABELS, KANBAN_SECTIONS)}
                      value={task.section ?? 'Queue'}
                      onChange={(event) => {
                        const value = event.currentTarget.value;
                        if (value && value !== task.section) {
                          move.mutate({ taskId: task.id, targetSection: value, etag });
                        }
                      }}
                      aria-label={`移动 ${task.title || task.id}`}
                    />
                  </Table.Td>
                  <Table.Td>
                    <Text size="xs" c="dimmed">
                      {task.completed_on || task.started_on || '—'}
                    </Text>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
            </Table>
          </Table.ScrollContainer>
        </Card>
      )}

      <Card withBorder radius="md" data-testid="add-task-form">
        <Stack gap="sm">
          <Text fw={500} size="sm">
            新建项目任务
          </Text>
          <Group grow align="flex-start">
            <TextInput
              label="标题"
              value={title}
              onChange={(event) => setTitle(event.currentTarget.value)}
            />
            <Select
              label="看板列"
              data={labeledData(SECTION_LABELS, ['Queue', 'Doing'])}
              value={section}
              onChange={(value) => setSection(value ?? 'Queue')}
            />
            <Select
              label="里程碑"
              data={milestoneOptions}
              value={milestoneId}
              onChange={(value) => setMilestoneId(value ?? '')}
            />
          </Group>
          <MutationErrorAlert
            error={add.error ?? move.error}
            title="操作失败"
            onRefetch={refreshBoard}
          />
          <Group>
            <Button
              size="compact-sm"
              leftSection={<IconPlus size={14} />}
              disabled={!title.trim()}
              loading={add.isPending}
              onClick={submit}
            >
              新建任务
            </Button>
          </Group>
        </Stack>
      </Card>
    </Stack>
  );
}

function CaseDetail({
  projectCase,
  board,
  etag,
}: {
  projectCase: ProjectCase;
  board: ProjectBoard;
  etag: string;
}) {
  return (
    <Card withBorder radius="md" data-testid="case-detail">
      <Stack gap="sm">
        <Group gap="sm">
          <Title order={3}>{projectCase.title || projectCase.id}</Title>
          <Badge variant="light">
            {PROJECT_STATUS_LABELS[projectCase.status ?? ''] ?? projectCase.status}
          </Badge>
          <Badge variant="light" color="gray">
            {KIND_LABELS[projectCase.kind ?? ''] ?? projectCase.kind}
          </Badge>
        </Group>
        <Text size="xs" c="dimmed">
          {[
            projectCase.id,
            projectCase.time_range || projectCase.derived_time_range,
          ]
            .filter(Boolean)
            .join(' · ')}
        </Text>
        <Tabs defaultValue="basics">
          <Tabs.List>
            <Tabs.Tab value="basics">基本信息</Tabs.Tab>
            <Tabs.Tab value="milestones">里程碑</Tabs.Tab>
            <Tabs.Tab value="tasks">任务</Tabs.Tab>
          </Tabs.List>
          <Tabs.Panel value="basics" pt="md">
            <BasicsTab projectCase={projectCase} board={board} etag={etag} />
          </Tabs.Panel>
          <Tabs.Panel value="milestones" pt="md">
            <MilestonesTab projectCase={projectCase} etag={etag} />
          </Tabs.Panel>
          <Tabs.Panel value="tasks" pt="md">
            <TasksTab projectCase={projectCase} etag={etag} />
          </Tabs.Panel>
        </Tabs>
      </Stack>
    </Card>
  );
}

export function ProjectBoardPage() {
  const { name = '' } = useParams();
  const board = useProjectBoard(name);
  const [selectedId, setSelectedId] = useState('');

  if (board.isPending) {
    return (
      <Center py="xl">
        <Loader />
      </Center>
    );
  }
  if (board.isError || !board.data) {
    return (
      <Alert color="red" title="加载失败">
        {board.error?.message ?? '无法加载项目看板。'}
      </Alert>
    );
  }

  const data = board.data.data;
  const etag = board.data.etag;
  const cases = data.cases ?? [];
  const summary = data.summary;
  const selected = cases.find((item) => item.id === selectedId) ?? null;

  return (
    <Stack gap="md">
      <Title order={2}>{name} · 项目看板</Title>
      <Text size="sm" c="dimmed">
        内部项目案例:把目标、看板任务、证据与资料串成可执行的项目档案。
      </Text>

      {summary && (
        <Group gap="xs" wrap="wrap" data-testid="board-summary">
          {PROJECT_STATUSES.map((status) => (
            <Badge key={status} color="brand" variant="light">
              {PROJECT_STATUS_LABELS[status]} {summary.status_counts?.[status] ?? 0}
            </Badge>
          ))}
          <Badge
            color={summary.unassigned_tasks ? 'orange' : 'gray'}
            variant="light"
          >
            未归属任务 {summary.unassigned_tasks ?? 0}
          </Badge>
          <Badge
            color={summary.unassigned_evidence ? 'orange' : 'gray'}
            variant="light"
          >
            未归属证据 {summary.unassigned_evidence ?? 0}
          </Badge>
          <Badge color="blue" variant="light">
            当前目标项目 {summary.current_goal_projects ?? 0}
          </Badge>
        </Group>
      )}

      <CreateCaseCard board={data} etag={etag} onCreated={setSelectedId} />

      {cases.length === 0 ? (
        <Alert color="blue" title="空看板">
          还没有项目案例,先用上方表单创建一个。
        </Alert>
      ) : (
        <Tabs defaultValue="active">
          <Tabs.List>
            {PROJECT_STATUSES.map((status) => (
              <Tabs.Tab key={status} value={status}>
                {PROJECT_STATUS_LABELS[status]}
              </Tabs.Tab>
            ))}
          </Tabs.List>
          {PROJECT_STATUSES.map((status) => (
            <Tabs.Panel key={status} value={status} pt="md">
              <Stack gap="sm">
                {cases.filter((item) => item.status === status).length === 0 && (
                  <Text c="dimmed" size="sm">
                    该状态下暂无项目。
                  </Text>
                )}
                {cases
                  .filter((item) => item.status === status)
                  .map((item) => (
                    <Card
                      key={item.id}
                      withBorder
                      radius="md"
                      data-testid={`case-card-${item.id}`}
                    >
                      <Group justify="space-between" wrap="wrap">
                        <Stack gap={2}>
                          <Text fw={500}>{item.title || item.id}</Text>
                          <Text size="xs" c="dimmed">
                            {[
                              item.id,
                              KIND_LABELS[item.kind ?? ''] ?? item.kind,
                              item.time_range || item.derived_time_range,
                            ]
                              .filter(Boolean)
                              .join(' · ')}
                          </Text>
                          <Text size="xs" c="dimmed">
                            目标 {item.goal_refs?.length ?? 0} · 任务{' '}
                            {item.task_refs?.length ?? 0} · 证据{' '}
                            {item.evidence_refs?.length ?? 0} · 里程碑{' '}
                            {item.milestones?.length ?? 0}
                          </Text>
                        </Stack>
                        <Button
                          size="compact-sm"
                          variant={selectedId === item.id ? 'filled' : 'default'}
                          disabled={selectedId === item.id}
                          onClick={() => setSelectedId(item.id)}
                        >
                          {selectedId === item.id ? '已选中' : '选择'}
                        </Button>
                      </Group>
                    </Card>
                  ))}
              </Stack>
            </Tabs.Panel>
          ))}
        </Tabs>
      )}

      {selected ? (
        <CaseDetail
          key={selected.id}
          projectCase={selected}
          board={data}
          etag={etag}
        />
      ) : (
        cases.length > 0 && (
          <Text c="dimmed" size="sm">
            选择一个项目查看与编辑详情。
          </Text>
        )
      )}
    </Stack>
  );
}
