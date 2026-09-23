// 项目编辑 Drawer — the ProjectBoardPage case-detail capability (基本信息 /
// 里程碑 / 任务 tabs) re-homed onto the /projects lane header「编辑」button.
// Data still comes from useProjectBoard (full case + ref pickers + board
// ETag); projects-board is invalidated alongside so lanes refresh too.

import {
  Accordion,
  Alert,
  Badge,
  Button,
  Card,
  Drawer,
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
  Center,
} from '@mantine/core';
import { IconArchive, IconBulb, IconDeviceFloppy, IconPlus } from '@tabler/icons-react';
import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef, useState } from 'react';

import { MutationErrorAlert } from '../ConflictAlert';
import {
  useAddProjectMilestone,
  useAddProjectTask,
  useArchiveProjectCase,
  useCreateJob,
  useDeleteProjectMilestone,
  useMoveProjectTask,
  useProjectBoard,
  useSaveProjectCase,
  useSaveProjectMilestone,
} from '../../api/hooks';
import { streamJob } from '../../api/jobs';
import type {
  ProjectBoard,
  ProjectCase,
  ProjectMilestone,
  ProjectRefOption,
  ProjectSuggestRefsResponse,
} from '../../api/types';
import { KIND_LABELS, PROJECT_STATUS_LABELS } from './lanes';

const PROJECT_STATUSES = Object.keys(PROJECT_STATUS_LABELS);

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

/** Refetch the project board (and the /projects aggregation) after a 412. */
function useRefreshBoards(profile: string) {
  const queryClient = useQueryClient();
  return () => {
    void queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'project-board'] });
    void queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'projects-board'] });
  };
}

function BasicsTab({
  profile,
  projectCase,
  board,
  etag,
}: {
  profile: string;
  projectCase: ProjectCase;
  board: ProjectBoard;
  etag: string;
}) {
  const [draft, setDraft] = useState<CaseDraft>(() => draftFromCase(projectCase));
  const [dirty, setDirty] = useState(false);
  const [suggestions, setSuggestions] = useState<ProjectSuggestRefsResponse | null>(null);
  const [suggestJob, setSuggestJob] = useState<SuggestJobProgress | null>(null);
  const [suggestError, setSuggestError] = useState<{ code: string; message: string } | null>(
    null,
  );
  const save = useSaveProjectCase(profile);
  const archive = useArchiveProjectCase(profile);
  const createJob = useCreateJob(profile);
  const refreshBoard = useRefreshBoards(profile);
  const stopStreamRef = useRef<(() => void) | null>(null);

  // Follow server-side changes only while the local draft is untouched; a
  // dirty draft always wins.
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

  // Cancel the SSE subscription on unmount and whenever the case changes.
  useEffect(() => {
    setSuggestJob(null);
    setSuggestions(null);
    setSuggestError(null);
    return stopStream;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profile, projectCase.id]);

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
          stopStreamRef.current = streamJob(profile, jobId, {
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
  profile,
  projectCase,
  milestone,
  etag,
}: {
  profile: string;
  projectCase: ProjectCase;
  milestone: ProjectMilestone;
  etag: string;
}) {
  const [title, setTitle] = useState(milestone.title ?? '');
  const [status, setStatus] = useState(milestone.status ?? 'planned');
  const [target, setTarget] = useState(milestone.target ?? '');
  const [date, setDate] = useState(milestone.date ?? '');
  const [summary, setSummary] = useState(milestone.summary ?? '');
  const save = useSaveProjectMilestone(profile);
  const remove = useDeleteProjectMilestone(profile);
  const refreshBoard = useRefreshBoards(profile);

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
  profile,
  projectCase,
  etag,
}: {
  profile: string;
  projectCase: ProjectCase;
  etag: string;
}) {
  const [title, setTitle] = useState('');
  const [target, setTarget] = useState('');
  const [date, setDate] = useState('');
  const add = useAddProjectMilestone(profile);
  const refreshBoard = useRefreshBoards(profile);

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
                  {MILESTONE_STATUS_LABELS[milestone.status ?? ''] ?? milestone.status}
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
                profile={profile}
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
  profile,
  projectCase,
  etag,
}: {
  profile: string;
  projectCase: ProjectCase;
  etag: string;
}) {
  const [title, setTitle] = useState('');
  const [section, setSection] = useState('Queue');
  const [milestoneId, setMilestoneId] = useState('');
  const add = useAddProjectTask(profile);
  const move = useMoveProjectTask(profile);
  const refreshBoard = useRefreshBoards(profile);

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

/** Lane-header「编辑」drawer: basics + milestones + tasks for one case. */
export function ProjectEditDrawer({
  profile,
  projectId,
  onClose,
}: {
  profile: string;
  /** null = closed. */
  projectId: string | null;
  onClose: () => void;
}) {
  const board = useProjectBoard(profile);
  const projectCase = (board.data?.data.cases ?? []).find((item) => item.id === projectId);

  return (
    <Drawer
      opened={projectId !== null}
      onClose={onClose}
      position="right"
      size="xl"
      title={projectCase ? `编辑项目 · ${projectCase.title || projectCase.id}` : '编辑项目'}
      data-testid="project-edit-drawer"
    >
      {board.isPending ? (
        <Center py="xl">
          <Loader />
        </Center>
      ) : !projectCase ? (
        <Alert color="yellow" title="项目不存在">
          未在项目看板中找到该项目;可能已删除。
        </Alert>
      ) : (
        <div data-testid="case-detail">
        <Tabs defaultValue="basics" key={projectCase.id}>
          <Tabs.List>
            <Tabs.Tab value="basics">基本信息</Tabs.Tab>
            <Tabs.Tab value="milestones">里程碑</Tabs.Tab>
            <Tabs.Tab value="tasks">任务</Tabs.Tab>
          </Tabs.List>
          <Tabs.Panel value="basics" pt="md">
            <BasicsTab
              profile={profile}
              projectCase={projectCase}
              board={board.data!.data}
              etag={board.data!.etag}
            />
          </Tabs.Panel>
          <Tabs.Panel value="milestones" pt="md">
            <MilestonesTab profile={profile} projectCase={projectCase} etag={board.data!.etag} />
          </Tabs.Panel>
          <Tabs.Panel value="tasks" pt="md">
            <TasksTab profile={profile} projectCase={projectCase} etag={board.data!.etag} />
          </Tabs.Panel>
        </Tabs>
        </div>
      )}
    </Drawer>
  );
}
