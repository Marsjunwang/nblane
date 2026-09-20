import {
  Alert,
  Badge,
  Card,
  Center,
  Group,
  Loader,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import { IconFlag, IconTarget } from '@tabler/icons-react';
import { useParams } from 'react-router-dom';

import { useGoals } from '../api/hooks';
import type { Goal, NorthStar } from '../api/types';

const STATUS_META: Record<string, { label: string; color: string }> = {
  active: { label: '进行中', color: 'green' },
  paused: { label: '已暂停', color: 'yellow' },
  completed: { label: '已完成', color: 'blue' },
  archived: { label: '已归档', color: 'gray' },
};

const VISIBILITY_LABELS: Record<string, string> = {
  visible: '公开',
  discreet: '低调',
  hidden: '隐藏',
  private: '私密',
};

function statusMeta(status: string): { label: string; color: string } {
  return STATUS_META[status] ?? { label: status || '未知', color: 'gray' };
}

function NorthStarCard({ northStar }: { northStar: NorthStar }) {
  const text = northStar.full || northStar.brief || '';
  return (
    <Card withBorder radius="md" data-testid="north-star-card">
      <Stack gap="xs">
        <Group gap="xs">
          <IconFlag size={16} />
          <Text fw={600}>北极星</Text>
          {northStar.visibility && (
            <Badge color="gray" variant="outline" size="sm">
              {VISIBILITY_LABELS[northStar.visibility] ?? northStar.visibility}
            </Badge>
          )}
        </Group>
        <Text>{text}</Text>
        {northStar.brief && northStar.brief !== text && (
          <Text size="sm" c="dimmed">
            {northStar.brief}
          </Text>
        )}
      </Stack>
    </Card>
  );
}

function GoalCard({ goal, isPrimary }: { goal: Goal; isPrimary: boolean }) {
  const meta = statusMeta(goal.status ?? '');
  const skills =
    (goal.skill_links ?? []).length > 0
      ? goal.skill_links!.map((link) => link.label || link.node_id)
      : (goal.target_skills ?? []);
  return (
    <Card withBorder radius="md" data-testid={`goal-card-${goal.id}`}>
      <Stack gap="xs">
        <Group gap="xs">
          <IconTarget size={16} />
          <Text fw={600}>{goal.title || goal.id}</Text>
          {isPrimary && (
            <Badge color="brand" variant="filled" size="sm">
              当前
            </Badge>
          )}
          {goal.label && (
            <Badge color="grape" variant="light" size="sm">
              {goal.label}
            </Badge>
          )}
          <Badge color={meta.color} variant="light" size="sm">
            {meta.label}
          </Badge>
        </Group>
        {goal.target && (
          <Text size="sm" c="dimmed">
            目标日期 {goal.target}
          </Text>
        )}
        {goal.summary && <Text size="sm">{goal.summary}</Text>}
        {skills.length > 0 && (
          <Group gap={4}>
            {skills.map((skill) => (
              <Badge key={skill} color="blue" variant="outline" size="sm">
                {skill}
              </Badge>
            ))}
          </Group>
        )}
        {(goal.success_criteria ?? []).length > 0 && (
          <Text size="xs" c="dimmed">
            成功标准:{goal.success_criteria!.join(' · ')}
          </Text>
        )}
      </Stack>
    </Card>
  );
}

export function GoalsPage() {
  const { name = '' } = useParams();
  const goals = useGoals(name);

  if (goals.isPending) {
    return (
      <Center py="xl">
        <Loader />
      </Center>
    );
  }
  if (goals.isError) {
    return (
      <Alert color="red" title="加载失败">
        {goals.error.message}
      </Alert>
    );
  }

  const data = goals.data;
  return (
    <Stack gap="md">
      <Group justify="space-between" wrap="wrap">
        <Title order={2}>{data.profile} · 目标</Title>
        <Text size="xs" c="dimmed">
          编辑功能开发中
        </Text>
      </Group>
      {data.north_star?.is_set && <NorthStarCard northStar={data.north_star} />}
      {(data.goals ?? []).length === 0 ? (
        <Text c="dimmed">还没有目标,先在 goals.yaml 中添加。</Text>
      ) : (
        <Stack gap="sm">
          {data.goals!.map((goal) => (
            <GoalCard
              key={goal.id}
              goal={goal}
              isPrimary={goal.id === data.current_goal_id}
            />
          ))}
        </Stack>
      )}
    </Stack>
  );
}
