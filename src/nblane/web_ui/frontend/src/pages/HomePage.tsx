import {
  Alert,
  Anchor,
  Badge,
  Button,
  Card,
  Center,
  Group,
  List,
  Loader,
  Progress,
  RingProgress,
  SimpleGrid,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import { IconExternalLink, IconPlayerPlay } from '@tabler/icons-react';
import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { useHome } from '../api/hooks';
import type { SidecarInfo } from '../api/types';
import { SidecarFrame } from '../components/SidecarFrame';

const SKILL_STATUS_COLORS: Record<string, string> = {
  expert: 'green',
  solid: 'teal',
  learning: 'yellow',
  locked: 'gray',
};

const QUICK_LINKS = [
  { label: '看板', path: 'kanban' },
  { label: '技能树', path: 'skill-tree' },
  { label: '目标', path: 'goals' },
  { label: '证据评审', path: 'evidence-review' },
  { label: '周回顾', path: 'review' },
  { label: '研究台', path: 'research' },
  { label: '输出工作室', path: 'studio' },
];

function sidecarOriginLabel(sidecar: SidecarInfo): string {
  if (!sidecar.base) {
    return '同源';
  }
  return sidecar.configured ? `已配置 · ${sidecar.base}` : `默认 · ${sidecar.base}`;
}

export function HomePage() {
  const { name = '' } = useParams();
  const home = useHome(name);
  const [dashboardEmbedded, setDashboardEmbedded] = useState(false);

  if (home.isPending) {
    return (
      <Center py="xl">
        <Loader />
      </Center>
    );
  }
  if (home.isError) {
    return (
      <Alert color="red" title="加载失败">
        {home.error.message}
      </Alert>
    );
  }

  const data = home.data;
  const skills = data.skills;
  const kanban = data.kanban;
  const evidence = data.evidence;
  const sidecar = data.sidecar;
  const skillCounts = skills?.counts ?? {};
  const skillTotal = skills?.total ?? 0;
  const northStar = data.north_star;
  const primaryGoal = data.primary_goal;

  return (
    <Stack gap="md">
      <Group justify="space-between" align="flex-start">
        <div>
          <Title order={2}>{data.profile} · 首页</Title>
          {northStar?.is_set ? (
            <Text c="dimmed" size="sm" mt={4}>
              北极星:{northStar.brief || northStar.full}
            </Text>
          ) : (
            <Text c="dimmed" size="sm" mt={4}>
              尚未设置北极星。
            </Text>
          )}
        </div>
        <Group gap="xs">
          {QUICK_LINKS.map((link) => (
            <Button
              key={link.path}
              component={Link}
              to={`/p/${encodeURIComponent(name)}/${link.path}`}
              variant="default"
              size="compact-sm"
            >
              {link.label}
            </Button>
          ))}
        </Group>
      </Group>

      <SimpleGrid cols={{ base: 1, sm: 2, lg: 3 }}>
        <Card withBorder radius="md" padding="lg" data-testid="home-goal-card">
          <Group justify="space-between" mb="xs">
            <Anchor component={Link} to={`/p/${encodeURIComponent(name)}/goals`} fw={600}>
              当前目标
            </Anchor>
            <Badge variant="light" color="brand">
              活跃 {data.goal_counts?.active ?? 0} / 共 {data.goal_counts?.total ?? 0}
            </Badge>
          </Group>
          {primaryGoal ? (
            <Stack gap="xs">
              <Text fw={500}>{primaryGoal.title}</Text>
              {primaryGoal.target && (
                <Text size="sm" c="dimmed">
                  目标日期:{primaryGoal.target}
                </Text>
              )}
              {primaryGoal.progress !== null && primaryGoal.progress !== undefined ? (
                <Progress
                  value={Math.round(primaryGoal.progress * 100)}
                  aria-label="目标进度"
                />
              ) : (
                <Text size="sm" c="dimmed">
                  暂无关联项目,进度待项目推进后自动推导。
                </Text>
              )}
              <Group gap="xs">
                <Badge variant="outline" color="gray">
                  项目 {primaryGoal.project_count}
                </Badge>
                {primaryGoal.stalled && (
                  <Badge variant="light" color="orange">
                    超过 30 天无任务活动
                  </Badge>
                )}
              </Group>
            </Stack>
          ) : (
            <Text c="dimmed" size="sm">
              暂无主目标。
            </Text>
          )}
        </Card>

        <Card withBorder radius="md" padding="lg" data-testid="home-skills-card">
          <Group justify="space-between" mb="xs">
            <Anchor
              component={Link}
              to={`/p/${encodeURIComponent(name)}/skill-tree`}
              fw={600}
            >
              技能树
            </Anchor>
            {(skills?.evidence_risk_count ?? 0) > 0 && (
              <Badge variant="light" color="red">
                证据风险 {skills?.evidence_risk_count}
              </Badge>
            )}
          </Group>
          {skills?.has_tree ? (
            <Group wrap="nowrap">
              <RingProgress
                size={96}
                thickness={10}
                label={
                  <Text ta="center" size="xs" fw={600}>
                    {Math.round((skills.lit_rate ?? 0) * 100)}%
                  </Text>
                }
                sections={Object.entries(skillCounts)
                  .filter(([, count]) => count > 0)
                  .map(([status, count]) => ({
                    value: skillTotal ? (count / skillTotal) * 100 : 0,
                    color: SKILL_STATUS_COLORS[status] ?? 'gray',
                    tooltip: `${status}: ${count}`,
                  }))}
              />
              <Stack gap={4}>
                <Text size="sm">
                  点亮 {skills.lit} / {skillTotal}
                </Text>
                {Object.entries(skillCounts).map(([status, count]) => (
                  <Badge key={status} variant="light" color={SKILL_STATUS_COLORS[status] ?? 'gray'}>
                    {status}: {count}
                  </Badge>
                ))}
              </Stack>
            </Group>
          ) : (
            <Text c="dimmed" size="sm">
              尚未建立技能树。
            </Text>
          )}
        </Card>

        <Card withBorder radius="md" padding="lg" data-testid="home-kanban-card">
          <Group justify="space-between" mb="xs">
            <Anchor component={Link} to={`/p/${encodeURIComponent(name)}/kanban`} fw={600}>
              看板
            </Anchor>
            <Group gap="xs">
              {Object.entries(kanban?.counts ?? {}).map(([section, count]) => (
                <Badge key={section} variant="light" color="gray">
                  {section}: {count}
                </Badge>
              ))}
            </Group>
          </Group>
          {(kanban?.doing ?? []).length > 0 ? (
            <List size="sm" spacing={4}>
              {(kanban?.doing ?? []).map((task) => (
                <List.Item key={task.id || task.title}>
                  {task.title}
                  {task.started_on && (
                    <Text span size="xs" c="dimmed">
                      {' '}
                      · {task.started_on}
                    </Text>
                  )}
                </List.Item>
              ))}
            </List>
          ) : (
            <Text c="dimmed" size="sm">
              Doing 列为空。
            </Text>
          )}
          {(kanban?.done_uncrystallized_count ?? 0) > 0 && (
            <Text size="xs" c="dimmed" mt="xs">
              {kanban?.done_uncrystallized_count} 张已完成卡片待结晶。
            </Text>
          )}
        </Card>

        <Card withBorder radius="md" padding="lg" data-testid="home-evidence-card">
          <Group justify="space-between" mb="xs">
            <Anchor
              component={Link}
              to={`/p/${encodeURIComponent(name)}/evidence-review`}
              fw={600}
            >
              证据待办
            </Anchor>
            <Badge variant="light" color="gray">
              共 {evidence?.total_entries ?? 0}
            </Badge>
          </Group>
          <Group gap="xs">
            <Badge variant="light" color="yellow">
              待评审 {evidence?.needs_review_count ?? 0}
            </Badge>
            <Badge variant="light" color="gray">
              未挂链 {evidence?.unlinked_count ?? 0}
            </Badge>
            <Badge variant="light" color="red">
              状态风险 {evidence?.status_risk_count ?? 0}
            </Badge>
            <Badge variant="light" color="orange">
              待结晶 {evidence?.done_uncrystallized_count ?? 0}
            </Badge>
          </Group>
        </Card>

        <Card withBorder radius="md" padding="lg" data-testid="home-research-card">
          <Group justify="space-between" mb="xs">
            <Anchor component={Link} to={`/p/${encodeURIComponent(name)}/research`} fw={600}>
              研究
            </Anchor>
            <Badge variant="light" color="gray">
              共 {data.sources?.total ?? 0}
            </Badge>
          </Group>
          <Text size="sm">进行中来源 {data.sources?.active_total ?? 0}</Text>
          {(data.sources?.active_titles ?? []).length > 0 && (
            <Text size="xs" c="dimmed" mt={4} lineClamp={2}>
              {(data.sources?.active_titles ?? []).join(' · ')}
            </Text>
          )}
        </Card>

        <Card withBorder radius="md" padding="lg" data-testid="home-activity-card">
          <Group justify="space-between" mb="xs">
            <Anchor component={Link} to={`/p/${encodeURIComponent(name)}/activity`} fw={600}>
              代理活动
            </Anchor>
            <Badge variant="light" color="gray">
              共 {data.agent_activity?.total ?? 0}
            </Badge>
          </Group>
          <Text size="sm">待审批 {data.agent_activity?.pending_total ?? 0}</Text>
          {(data.agent_activity?.pending_titles ?? []).map((title) => (
            <Text key={title} size="xs" c="dimmed" lineClamp={1}>
              {title}
            </Text>
          ))}
        </Card>

        <Card withBorder radius="md" padding="lg" data-testid="home-projects-card">
          <Group justify="space-between" mb="xs">
            <Anchor
              component={Link}
              to={`/p/${encodeURIComponent(name)}/project-board`}
              fw={600}
            >
              项目
            </Anchor>
            <Badge variant="light" color="gray">
              共 {data.projects?.total ?? 0}
            </Badge>
          </Group>
          <Group gap="xs">
            {Object.entries(data.projects?.status_counts ?? {}).map(([status, count]) => (
              <Badge key={status} variant="light" color="gray">
                {status}: {count}
              </Badge>
            ))}
          </Group>
        </Card>

        <Card withBorder radius="md" padding="lg" data-testid="home-health-card">
          <Group justify="space-between" mb="xs">
            <Anchor component={Link} to={`/p/${encodeURIComponent(name)}/health`} fw={600}>
              健康
            </Anchor>
            <Badge variant="light" color={data.health?.context_ready ? 'green' : 'yellow'}>
              {data.health?.context_ready ? '上下文可发布' : '上下文暂不可发布'}
            </Badge>
          </Group>
          <Group gap="xs">
            {Object.entries(data.health?.counts ?? {}).map(([severity, count]) => (
              <Badge key={severity} variant="light" color="gray">
                {severity}: {count}
              </Badge>
            ))}
          </Group>
        </Card>
      </SimpleGrid>

      {sidecar && (
        <Card withBorder radius="md" padding="lg" data-testid="home-dashboard-card">
          <Group justify="space-between" mb="xs">
            <div>
              <Text fw={600}>3D 成长仪表盘</Text>
              <Text size="xs" c="dimmed">
                由 Reader API sidecar 承载({sidecarOriginLabel(sidecar)})
              </Text>
            </div>
            <Group gap="xs">
              <Button
                component="a"
                href={sidecar.dashboard_url}
                target="_blank"
                rel="noreferrer"
                variant="default"
                size="compact-sm"
                leftSection={<IconExternalLink size={14} />}
              >
                新标签打开
              </Button>
              <Button
                variant="light"
                size="compact-sm"
                leftSection={<IconPlayerPlay size={14} />}
                onClick={() => setDashboardEmbedded((value) => !value)}
              >
                {dashboardEmbedded ? '收起嵌入' : '嵌入显示'}
              </Button>
            </Group>
          </Group>
          {dashboardEmbedded && (
            <SidecarFrame
              title="3D 成长仪表盘"
              url={sidecar.dashboard_url}
              base={sidecar.base}
              handoffToken={sidecar.handoff_token}
            />
          )}
        </Card>
      )}
    </Stack>
  );
}
