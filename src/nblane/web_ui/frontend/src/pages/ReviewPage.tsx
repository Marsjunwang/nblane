import {
  Alert,
  Badge,
  Button,
  Card,
  Center,
  Checkbox,
  Group,
  List,
  Loader,
  Select,
  Stack,
  Table,
  Tabs,
  Text,
  TextInput,
  Title,
} from '@mantine/core';
import { IconCalendarWeek, IconCheck, IconDeviceFloppy, IconRobot } from '@tabler/icons-react';
import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import {
  useReviewApplyCandidates,
  useReviewSaveCandidates,
  useWeeklyReview,
} from '../api/hooks';
import { MutationErrorAlert } from '../components/ConflictAlert';
import type { ReviewCandidate, ReviewResponse } from '../api/types';

type CandidateType = 'evidence' | 'next_action' | 'public_draft';

interface ReviewWindow {
  start: string;
  end: string;
}

function isoDate(d: Date): string {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/** Client mirror of core review_window_for_preset. */
function windowForPreset(preset: string, today = new Date()): ReviewWindow {
  const weekday = (today.getDay() + 6) % 7; // Monday = 0
  const monday = new Date(today);
  monday.setDate(today.getDate() - weekday);
  if (preset === 'previous_week') {
    const start = new Date(monday);
    start.setDate(monday.getDate() - 7);
    const end = new Date(start);
    end.setDate(start.getDate() + 6);
    return { start: isoDate(start), end: isoDate(end) };
  }
  if (preset === 'last_30_days') {
    const start = new Date(today);
    start.setDate(today.getDate() - 29);
    return { start: isoDate(start), end: isoDate(today) };
  }
  return { start: isoDate(monday), end: isoDate(today) };
}

const PRESET_OPTIONS = [
  { value: 'current_week', label: '本周' },
  { value: 'previous_week', label: '上周' },
  { value: 'last_30_days', label: '近 30 天' },
  { value: 'custom', label: '自定义' },
];

function candidateRef(candidate: ReviewCandidate): string {
  return String(candidate.task_id || candidate.resource_id || '');
}

function CandidateTable({
  tabId,
  candidates,
  selected,
  onToggle,
}: {
  tabId: string;
  candidates: ReviewCandidate[];
  selected: ReadonlySet<number>;
  onToggle: (index: number, checked: boolean) => void;
}) {
  return (
    <Card withBorder radius="md" p={0}>
      <Table.ScrollContainer minWidth={640}>
        <Table highlightOnHover>
        <Table.Thead>
          <Table.Tr>
            <Table.Th />
            <Table.Th>来源</Table.Th>
            <Table.Th>标题</Table.Th>
            <Table.Th>摘要</Table.Th>
            <Table.Th>引用</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {candidates.map((candidate, index) => (
            <Table.Tr key={index} data-testid={`review-candidate-${tabId}-${index}`}>
              <Table.Td>
                <Checkbox
                  aria-label={`选择 ${candidate.title || index}`}
                  checked={selected.has(index)}
                  onChange={(event) => onToggle(index, event.currentTarget.checked)}
                />
              </Table.Td>
              <Table.Td>
                <Badge color="brand" variant="light" size="sm">
                  {candidate.source || '—'}
                </Badge>
              </Table.Td>
              <Table.Td>
                <Text size="sm">{candidate.title || '—'}</Text>
              </Table.Td>
              <Table.Td>
                <Text size="sm" c="dimmed" lineClamp={2}>
                  {candidate.summary || (candidate.notes ?? []).join('；') || '—'}
                </Text>
              </Table.Td>
              <Table.Td>
                <Text size="xs" c="dimmed">
                  {candidateRef(candidate) || '—'}
                </Text>
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
        </Table>
      </Table.ScrollContainer>
    </Card>
  );
}

function CandidateTab({
  profile,
  window,
  etag,
  tabId,
  candidateType,
  candidates,
  applyLabel,
  showCrystallized = false,
}: {
  profile: string;
  window: ReviewWindow;
  etag: string;
  tabId: string;
  candidateType: CandidateType;
  candidates: ReviewCandidate[];
  applyLabel: string;
  showCrystallized?: boolean;
}) {
  const [selected, setSelected] = useState<ReadonlySet<number>>(new Set());
  const [markCrystallized, setMarkCrystallized] = useState(true);
  const save = useReviewSaveCandidates(profile);
  const apply = useReviewApplyCandidates(profile);
  const queryClient = useQueryClient();
  const refetchReview = () =>
    void queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'review'] });

  // The success banners must not outlive the context they confirm: a new
  // selection or a window change resets the mutation state.
  const resetMutations = () => {
    save.reset();
    apply.reset();
  };
  useEffect(() => {
    resetMutations();
  }, [window.start, window.end]);

  const toggle = (index: number, checked: boolean) => {
    resetMutations();
    setSelected((prev) => {
      const next = new Set(prev);
      if (checked) {
        next.add(index);
      } else {
        next.delete(index);
      }
      return next;
    });
  };

  const picked = candidates.filter((_, index) => selected.has(index));
  const clearSelection = () => setSelected(new Set());
  const mutationError = save.error ?? apply.error;

  if (candidates.length === 0) {
    return <Text c="dimmed">当前窗口内没有候选。</Text>;
  }

  const runSave = () =>
    save.mutate(
      {
        body: {
          start: window.start,
          end: window.end,
          candidate_type: candidateType,
          candidates: picked,
        },
        etag,
      },
      { onSuccess: clearSelection },
    );

  const runApply = () =>
    apply.mutate(
      {
        body: {
          start: window.start,
          end: window.end,
          candidate_type: candidateType,
          candidates: picked,
          mark_crystallized: markCrystallized,
        },
        etag,
      },
      { onSuccess: clearSelection },
    );

  return (
    <Stack gap="sm">
      <Group gap="sm" wrap="wrap" data-testid={`candidate-actions-${tabId}`}>
        <Text size="sm" c="dimmed" data-testid={`selection-count-${tabId}`}>
          已选 {picked.length} 条
        </Text>
        {showCrystallized && (
          <Checkbox
            label="应用后将 Done 卡片标记为已结晶"
            checked={markCrystallized}
            onChange={(event) => setMarkCrystallized(event.currentTarget.checked)}
            aria-label="标记已结晶"
          />
        )}
        <Button
          size="compact-sm"
          variant="default"
          leftSection={<IconDeviceFloppy size={14} />}
          disabled={picked.length === 0}
          loading={save.isPending}
          onClick={runSave}
        >
          保存到活动 ({picked.length})
        </Button>
        <Button
          size="compact-sm"
          color="green"
          leftSection={<IconCheck size={14} />}
          disabled={picked.length === 0}
          loading={apply.isPending}
          onClick={runApply}
        >
          {applyLabel} ({picked.length})
        </Button>
      </Group>

      <MutationErrorAlert error={mutationError} title="操作失败" onRefetch={refetchReview} />
      {save.isSuccess && (
        <Alert color="green" title="已保存" data-testid={`save-success-${tabId}`}>
          已把 {save.data.saved} 条候选保存到代理活动。
        </Alert>
      )}
      {apply.isSuccess && (
        <Alert
          color={apply.data.ok ? 'green' : 'yellow'}
          title={apply.data.ok ? '已应用' : '部分失败'}
          data-testid={`apply-result-${tabId}`}
        >
          成功 {apply.data.applied} 条,失败 {apply.data.failed} 条。
          {apply.data.results
            ?.filter((result) => !result.ok)
            .map((result) => (
              <Text key={result.title} size="sm">
                {result.title}: {(result.errors ?? []).join('; ')}
              </Text>
            ))}
        </Alert>
      )}

      <CandidateTable
        tabId={tabId}
        candidates={candidates}
        selected={selected}
        onToggle={toggle}
      />
    </Stack>
  );
}

function MethodNotes({ candidates }: { candidates: ReviewCandidate[] }) {
  if (candidates.length === 0) {
    return <Text c="dimmed">当前窗口内没有方法笔记候选。</Text>;
  }
  return (
    <Stack gap="sm">
      {candidates.map((candidate, index) => (
        <Card key={index} withBorder radius="md" data-testid={`method-note-${index}`}>
          <Text fw={500}>{candidate.title || '—'}</Text>
          <Text size="xs" c="dimmed" mb="xs">
            {candidate.source} · {candidateRef(candidate)}
          </Text>
          <List size="sm">
            {(candidate.notes ?? []).map((note, noteIndex) => (
              <List.Item key={noteIndex}>{note}</List.Item>
            ))}
          </List>
        </Card>
      ))}
    </Stack>
  );
}

function ReviewBody({
  profile,
  window,
  review,
  etag,
}: {
  profile: string;
  window: ReviewWindow;
  review: ReviewResponse;
  etag: string;
}) {
  const summary = review.summary;
  return (
    <Stack gap="md">
      <Group gap="xs" wrap="wrap" data-testid="review-summary">
        <Badge color="brand" variant="light">
          已完成任务 {summary?.done_tasks ?? 0}
        </Badge>
        <Badge color="yellow" variant="light">
          证据候选 {summary?.evidence_candidates ?? 0}
        </Badge>
        <Badge color="blue" variant="light">
          下一步候选 {summary?.next_action_candidates ?? 0}
        </Badge>
        <Badge color="grape" variant="light">
          公开草稿候选 {summary?.public_draft_candidates ?? 0}
        </Badge>
      </Group>

      <Tabs defaultValue="evidence">
        <Tabs.List>
          <Tabs.Tab value="evidence">证据候选</Tabs.Tab>
          <Tabs.Tab value="next_action">下一步候选</Tabs.Tab>
          <Tabs.Tab value="public_draft">公开草稿候选</Tabs.Tab>
          <Tabs.Tab value="method">方法笔记</Tabs.Tab>
        </Tabs.List>
        <Tabs.Panel value="evidence" pt="md">
          <CandidateTab
            profile={profile}
            window={window}
            etag={etag}
            tabId="evidence"
            candidateType="evidence"
            candidates={review.evidence_candidates ?? []}
            applyLabel="应用所选"
            showCrystallized
          />
        </Tabs.Panel>
        <Tabs.Panel value="next_action" pt="md">
          <CandidateTab
            profile={profile}
            window={window}
            etag={etag}
            tabId="next_action"
            candidateType="next_action"
            candidates={review.next_queue_candidates ?? []}
            applyLabel="应用所选"
          />
        </Tabs.Panel>
        <Tabs.Panel value="public_draft" pt="md">
          <Stack gap="sm">
            <Text size="sm" c="dimmed">
              公开草稿只创建 draft 状态的博客文件,发布前请人工核对隐私细节与数据。
            </Text>
            <CandidateTab
              profile={profile}
              window={window}
              etag={etag}
              tabId="public_draft"
              candidateType="public_draft"
              candidates={review.public_candidates ?? []}
              applyLabel="创建公开草稿"
            />
          </Stack>
        </Tabs.Panel>
        <Tabs.Panel value="method" pt="md">
          <MethodNotes candidates={review.method_candidates ?? []} />
        </Tabs.Panel>
      </Tabs>
    </Stack>
  );
}

export function ReviewPage() {
  const { name = '' } = useParams();
  const [preset, setPreset] = useState('current_week');
  const [window, setWindow] = useState<ReviewWindow>(() => windowForPreset('current_week'));
  const review = useWeeklyReview(name, window);

  const changePreset = (value: string | null) => {
    const next = value ?? 'current_week';
    setPreset(next);
    if (next !== 'custom') {
      setWindow(windowForPreset(next));
    }
  };

  const changeDate = (field: 'start' | 'end', value: string) => {
    setPreset('custom');
    setWindow((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <Stack gap="md">
      <Group justify="space-between" wrap="wrap">
        <Title order={2}>{name} · 周回顾</Title>
        <Button
          component={Link}
          to={`/p/${encodeURIComponent(name)}/activity`}
          variant="subtle"
          size="compact-sm"
          leftSection={<IconRobot size={14} />}
        >
          打开代理活动
        </Button>
      </Group>
      <Text size="sm" c="dimmed">
        聚合一个时间窗口内的看板 Done 卡片与学习日志,生成证据、下一步行动与公开草稿候选;确认后再写回。
      </Text>

      <Group gap="sm" wrap="wrap" data-testid="window-controls">
        <Select
          data={PRESET_OPTIONS}
          value={preset}
          onChange={changePreset}
          aria-label="时间窗口预设"
          leftSection={<IconCalendarWeek size={14} />}
          w={160}
        />
        <TextInput
          type="date"
          label="开始日期"
          value={window.start}
          onChange={(event) => changeDate('start', event.currentTarget.value)}
          aria-label="开始日期"
        />
        <TextInput
          type="date"
          label="结束日期"
          value={window.end}
          onChange={(event) => changeDate('end', event.currentTarget.value)}
          aria-label="结束日期"
        />
      </Group>

      {review.isError && (
        <Alert color="red" title="加载失败">
          {review.error.message}
        </Alert>
      )}
      {review.isPending ? (
        <Center py="xl">
          <Loader />
        </Center>
      ) : (
        review.data && (
          <ReviewBody
            profile={name}
            window={{ start: review.data.data.week_start, end: review.data.data.week_end }}
            review={review.data.data}
            etag={review.data.etag}
          />
        )
      )}
    </Stack>
  );
}
