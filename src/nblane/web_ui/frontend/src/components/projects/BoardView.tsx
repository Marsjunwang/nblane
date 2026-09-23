// 泳道看板视图 — the default /projects view. Renders the shared LaneGroup[]
// (goal or activity grouping), habit check-in lanes (linked habits inline
// after their project lane, unlinked ones in a trailing 习惯 section), the
// dashed-gold 未归属 lane, and a count-only archived-projects footer.

import { Badge, Group, Stack, Text } from '@mantine/core';
import { IconArchive } from '@tabler/icons-react';

import type {
  KanbanSection,
  ProjectsBoardHabit,
  ProjectsBoardProject,
  ProjectsBoardTask,
} from '../../api/types';
import { HabitLane } from './HabitLane';
import { ProjectLane, UnassignedLane } from './ProjectLane';
import type { LaneGroup } from './lanes';
import { boardPalette } from './palette';

export interface BoardViewProps {
  profile: string;
  groups: LaneGroup[];
  habits: ProjectsBoardHabit[];
  unassigned: ProjectsBoardTask[];
  archived: ProjectsBoardProject[];
  kanbanEtag: string;
  kanbanSections: KanbanSection[] | undefined;
  selectedTaskId: string;
  onSelectTask: (taskId: string) => void;
  onEditProject: (projectId: string) => void;
  onRefresh: () => void;
}

function GoalGroupHeader({ group }: { group: LaneGroup }) {
  return (
    <Group gap="sm" wrap="nowrap" data-testid={`lane-group-header-${group.id}`}>
      <Text fw={700} size="lg" style={{ color: boardPalette.titleText }}>
        {group.title}
      </Text>
      {group.target && (
        <Badge
          size="sm"
          variant="outline"
          style={{ borderColor: boardPalette.gold, color: boardPalette.goldText }}
        >
          {group.target}
        </Badge>
      )}
      {group.meta && (
        <Text size="sm" style={{ color: boardPalette.dim }} lineClamp={1}>
          {group.meta}
        </Text>
      )}
    </Group>
  );
}

export function BoardView({
  profile,
  groups,
  habits,
  unassigned,
  archived,
  kanbanEtag,
  kanbanSections,
  selectedTaskId,
  onSelectTask,
  onEditProject,
  onRefresh,
}: BoardViewProps) {
  const habitsByProject = new Map<string, ProjectsBoardHabit[]>();
  const unlinkedHabits: ProjectsBoardHabit[] = [];
  for (const habit of habits) {
    if (habit.project_id) {
      const rows = habitsByProject.get(habit.project_id) ?? [];
      rows.push(habit);
      habitsByProject.set(habit.project_id, rows);
    } else {
      unlinkedHabits.push(habit);
    }
  }

  return (
    <Stack gap="xl" data-testid="board-view">
      {groups.map((group) => (
        <Stack key={group.id} gap="sm" data-testid={`lane-group-${group.id}`}>
          <GoalGroupHeader group={group} />
          {group.projects.length === 0 && (
            <Text size="sm" style={{ color: boardPalette.dim }}>
              该分组下暂无项目。
            </Text>
          )}
          {group.projects.map((project) => (
            <Stack key={project.id} gap="xs">
              <ProjectLane
                profile={profile}
                project={project}
                kanbanEtag={kanbanEtag}
                kanbanSections={kanbanSections}
                selectedTaskId={selectedTaskId}
                onSelectTask={onSelectTask}
                onEditProject={onEditProject}
                onRefresh={onRefresh}
              />
              {(habitsByProject.get(project.id) ?? []).map((habit) => (
                <HabitLane key={habit.id} profile={profile} habit={habit} />
              ))}
            </Stack>
          ))}
        </Stack>
      ))}

      {unlinkedHabits.length > 0 && (
        <Stack gap="sm" data-testid="lane-group-habits">
          <GoalGroupHeader
            group={{ id: 'habits', title: '习惯', meta: '持续型打卡', target: '', projects: [] }}
          />
          {unlinkedHabits.map((habit) => (
            <HabitLane key={habit.id} profile={profile} habit={habit} />
          ))}
        </Stack>
      )}

      {unassigned.length > 0 && (
        <UnassignedLane
          profile={profile}
          tasks={unassigned}
          kanbanEtag={kanbanEtag}
          kanbanSections={kanbanSections}
          selectedTaskId={selectedTaskId}
          onSelectTask={onSelectTask}
          onRefresh={onRefresh}
        />
      )}

      {archived.length > 0 && (
        <Group
          gap="xs"
          p="sm"
          data-testid="archived-projects-footer"
          style={{
            border: `1px dashed ${boardPalette.border}`,
            borderRadius: 12,
            color: boardPalette.dim,
          }}
        >
          <IconArchive size={14} />
          <Text size="sm" style={{ color: boardPalette.dim }}>
            已归档项目 · {archived.length} ▸
          </Text>
          <Text size="xs" style={{ color: boardPalette.dim }}>
            {archived.map((project) => project.title || project.id).join(' / ')}
          </Text>
        </Group>
      )}
    </Stack>
  );
}
