// 泳道看板视图 — the default /projects view. Top-down: 日课栏 habit band
// (one row per habit, 裱边 hairline separation), the shared LaneGroup[]
// (goal or activity grouping), the dashed-gold 未归属 lane, and the
// expandable 已归档 strip (L3: 月白 40% read-only lanes with 恢复).
//
// Dedupe invariant (裁决2): a habit appears EXACTLY ONCE, in the band.
// Habit-plan projects (kind 'habit' with a resolved habit link) are filtered
// out of the lane groups by buildLaneGroups, so no empty Queue/Doing lanes
// and no 未分组 doppelgängers.

import { Badge, Group, Stack, Text } from '@mantine/core';

import type {
  KanbanSection,
  ProjectsBoardProject,
  ProjectsBoardTask,
} from '../../api/types';
import { ArchivedStrip } from './ArchivedStrip';
import { HabitBand } from './HabitBand';
import { ProjectLane, UnassignedLane } from './ProjectLane';
import type { HabitRow, LaneGroup } from './lanes';
import { boardPalette } from './palette';

export interface BoardViewProps {
  profile: string;
  groups: LaneGroup[];
  habitRows: HabitRow[];
  today: string;
  unassigned: ProjectsBoardTask[];
  archived: ProjectsBoardProject[];
  kanbanEtag: string;
  kanbanSections: KanbanSection[] | undefined;
  projectBoardEtag: string;
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
  habitRows,
  today,
  unassigned,
  archived,
  kanbanEtag,
  kanbanSections,
  projectBoardEtag,
  selectedTaskId,
  onSelectTask,
  onEditProject,
  onRefresh,
}: BoardViewProps) {
  return (
    <Stack gap="xl" data-testid="board-view">
      <HabitBand profile={profile} rows={habitRows} today={today} />

      {groups.map((group) => (
        <Stack key={group.id} gap="sm" data-testid={`lane-group-${group.id}`}>
          <GoalGroupHeader group={group} />
          {group.projects.length === 0 && (
            <Text size="sm" style={{ color: boardPalette.dim }}>
              该分组下暂无项目。
            </Text>
          )}
          {group.projects.map((project) => (
            <ProjectLane
              key={project.id}
              profile={profile}
              project={project}
              kanbanEtag={kanbanEtag}
              kanbanSections={kanbanSections}
              projectBoardEtag={projectBoardEtag}
              selectedTaskId={selectedTaskId}
              onSelectTask={onSelectTask}
              onEditProject={onEditProject}
              onRefresh={onRefresh}
            />
          ))}
        </Stack>
      ))}

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

      <ArchivedStrip
        profile={profile}
        archived={archived}
        selectedTaskId={selectedTaskId}
        onSelectTask={onSelectTask}
        onEditProject={onEditProject}
        onRefresh={onRefresh}
      />
    </Stack>
  );
}
