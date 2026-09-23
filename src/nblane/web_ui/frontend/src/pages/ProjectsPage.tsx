// /projects — the unified Phase 2 page: one board, two views (泳道看板 +
// 时间轴) over the projects-board aggregation, sharing the `?task=` selection.
//
// URL state: `view=kanban|timeline` (default kanban), `group=goal|activity`
// (default goal), `task=<task.id>` (cross-view selection; mutations address
// cards by TITLE, selection is by id). View/group switches use
// `replace: true` and preserve `task`; closing the detail card drops only
// the task param.

import {
  Alert,
  Badge,
  Button,
  Center,
  Group,
  Loader,
  Paper,
  SegmentedControl,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import { IconPlus, IconRefresh } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';
import { Navigate, useParams, useSearchParams } from 'react-router-dom';

import { useKanbanBoard, useProjectsBoard } from '../api/hooks';
import { BoardView } from '../components/projects/BoardView';
import { NewPlanModal } from '../components/projects/NewPlanModal';
import { NewProjectModal } from '../components/projects/NewProjectModal';
import { ProjectEditDrawer } from '../components/projects/ProjectEditDrawer';
import { TaskDetailCard } from '../components/projects/TaskDetailCard';
import { TimelineView } from '../components/projects/TimelineView';
import { handleLaneMutationError } from '../components/projects/ProjectLane';
import {
  buildLaneGroups,
  collectArchivedProjects,
  collectProjects,
  findBoardTask,
} from '../components/projects/lanes';
import type { ProjectsGroupBy } from '../components/projects/lanes';
import { boardPalette } from '../components/projects/palette';

export type ProjectsView = 'kanban' | 'timeline';

const STATS_LABELS: Record<string, string> = {
  tasks_total: '任务',
  tasks_unassigned: '未归属',
  done_total: '已完成',
  projects_total: '项目',
  habits_total: '习惯',
};

function parseView(raw: string | null): ProjectsView {
  return raw === 'timeline' ? 'timeline' : 'kanban';
}

function parseGroup(raw: string | null): ProjectsGroupBy {
  return raw === 'activity' ? 'activity' : 'goal';
}

/** Legacy-route redirect preserving the query string. */
function ProjectsRedirect({ name }: { name: string }) {
  const [searchParams] = useSearchParams();
  const search = searchParams.toString();
  return (
    <Navigate
      to={`/p/${encodeURIComponent(name)}/projects${search ? `?${search}` : ''}`}
      replace
    />
  );
}

/** /kanban → /projects(旧链接不破坏,保留 query 串)。 */
export function KanbanRedirect() {
  const { name = '' } = useParams();
  return <ProjectsRedirect name={name} />;
}

/** /project-board → /projects(旧链接不破坏,保留 query 串)。 */
export function ProjectBoardRedirect() {
  const { name = '' } = useParams();
  return <ProjectsRedirect name={name} />;
}

export function ProjectsPage() {
  const { name = '' } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const view = parseView(searchParams.get('view'));
  const group = parseGroup(searchParams.get('group'));
  const taskId = searchParams.get('task') ?? '';

  const board = useProjectsBoard(name);
  const kanban = useKanbanBoard(name);
  const [planOpen, setPlanOpen] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [editProjectId, setEditProjectId] = useState<string | null>(null);

  // View/group switches preserve the shared task selection; closing the
  // detail card drops only the task param. All switches replace history.
  const updateParams = useCallback(
    (updates: Record<string, string | null>) => {
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          for (const [key, value] of Object.entries(updates)) {
            if (value === null || value === '') {
              next.delete(key);
            } else {
              next.set(key, value);
            }
          }
          return next;
        },
        { replace: true },
      );
    },
    [setSearchParams],
  );

  const data = board.data?.board;
  const groups = useMemo(
    () => (data ? buildLaneGroups(data, group) : []),
    [data, group],
  );
  const archived = useMemo(() => (data ? collectArchivedProjects(data) : []), [data]);
  const allProjects = useMemo(() => (data ? collectProjects(data) : []), [data]);
  // Stable identity: Mantine Select re-syncs its display when `data` churns.
  const activeProjects = useMemo(
    () => allProjects.filter((project) => project.status !== 'archived'),
    [allProjects],
  );
  const selected = useMemo(
    () => (data && taskId ? findBoardTask(data, taskId) : null),
    [data, taskId],
  );

  const onRefresh = useCallback(() => void board.refetch(), [board]);

  if (board.isPending) {
    return (
      <Center py="xl">
        <Loader />
      </Center>
    );
  }
  if (board.isError || !data) {
    return (
      <Alert color="red" title="加载失败">
        {board.error?.message ?? '无法加载项目面板。'}
      </Alert>
    );
  }

  return (
    // Full indigo page ground (concept mockup base #1d3450): the light
    // AppShell main padding is negated so lanes, group headers and the
    // timeline axis all sit on the dark field their tokens assume.
    <Stack
      gap="md"
      data-testid="projects-page"
      m={-16}
      p="md"
      mih="calc(100vh - 56px)"
      style={{ background: '#1d3450', borderRadius: 4 }}
    >
      <Paper
        p="sm"
        data-testid="projects-toolbar"
        style={{
          position: 'sticky',
          top: 0,
          // Above the detail-card modal overlay (200) while a card is open —
          // the mockup keeps the topbar (and its shared-selection chip)
          // reachable so the view/group switch never loses `?task=`. At the
          // default zIndex the AppShell navbar (also 200) stays on top.
          zIndex: selected ? 210 : 10,
          background: boardPalette.ground,
          border: `1px solid ${boardPalette.border}`,
          borderRadius: 12,
        }}
      >
        <Group justify="space-between" wrap="wrap" gap="sm">
          <Group gap="sm" wrap="nowrap">
            <Title order={2} style={{ color: boardPalette.titleText }}>
              {name} · 项目
            </Title>
            {data.north_star && (
              <Badge
                variant="outline"
                size="lg"
                style={{ borderColor: boardPalette.gold, color: boardPalette.goldText }}
                data-testid="north-star"
              >
                {data.north_star}
              </Badge>
            )}
          </Group>
          <Group gap="sm" wrap="wrap">
            <SegmentedControl
              value={view}
              onChange={(value) => updateParams({ view: value })}
              data={[
                { label: '泳道看板', value: 'kanban' },
                { label: '时间轴', value: 'timeline' },
              ]}
              data-testid="view-switch"
            />
            <SegmentedControl
              value={group}
              onChange={(value) => updateParams({ group: value })}
              data={[
                { label: '按目标', value: 'goal' },
                { label: '按活动', value: 'activity' },
              ]}
              data-testid="group-switch"
            />
            <Button
              variant="light"
              size="compact-sm"
              leftSection={<IconPlus size={14} />}
              onClick={() => setCreateOpen(true)}
              data-testid="new-project-button"
            >
              新建项目
            </Button>
            <Button
              variant="light"
              size="compact-sm"
              leftSection={<IconPlus size={14} />}
              onClick={() => setPlanOpen(true)}
              data-testid="new-plan-button"
            >
              新建计划
            </Button>
            <Button
              variant="subtle"
              size="compact-sm"
              leftSection={<IconRefresh size={14} />}
              loading={board.isFetching}
              onClick={onRefresh}
              aria-label="刷新"
            >
              刷新
            </Button>
          </Group>
        </Group>
      </Paper>

      {data.stats && (
        <Group gap="xs" wrap="wrap" data-testid="projects-stats">
          <Text size="sm" style={{ color: boardPalette.dim }}>
            今天 {data.today}
          </Text>
          {Object.entries(data.stats).map(([key, value]) => (
            <Badge
              key={key}
              size="sm"
              variant="outline"
              style={{ borderColor: boardPalette.border, color: boardPalette.dim }}
            >
              {STATS_LABELS[key] ?? key} {value}
            </Badge>
          ))}
        </Group>
      )}

      {view === 'kanban' ? (
        <BoardView
          profile={name}
          groups={groups}
          habits={data.habits ?? []}
          unassigned={data.unassigned_tasks ?? []}
          archived={archived}
          kanbanEtag={kanban.data?.etag ?? ''}
          kanbanSections={kanban.data?.board.sections}
          selectedTaskId={taskId}
          onSelectTask={(id) => updateParams({ task: id })}
          onEditProject={setEditProjectId}
          onRefresh={onRefresh}
        />
      ) : (
        <TimelineView
          profile={name}
          board={data}
          groups={groups}
          habits={data.habits ?? []}
          unassigned={data.unassigned_tasks ?? []}
          kanbanEtag={kanban.data?.etag ?? ''}
          selectedTaskId={taskId}
          onSelectTask={(id) => updateParams({ task: id })}
          onDragError={(error) => handleLaneMutationError(error, '排期失败', onRefresh)}
        />
      )}

      <TaskDetailCard
        profile={name}
        task={selected?.task ?? null}
        project={selected?.project ?? null}
        projects={activeProjects}
        habits={data.habits ?? []}
        today={data.today ?? ''}
        kanbanEtag={kanban.data?.etag ?? ''}
        onClose={() => updateParams({ task: null })}
        onRefresh={onRefresh}
      />
      <NewPlanModal profile={name} opened={planOpen} onClose={() => setPlanOpen(false)} />
      <NewProjectModal
        profile={name}
        opened={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={(caseId) => setEditProjectId(caseId || null)}
      />
      <ProjectEditDrawer
        profile={name}
        projectId={editProjectId}
        onClose={() => setEditProjectId(null)}
      />
    </Stack>
  );
}
