import {
  Alert,
  Anchor,
  Badge,
  Button,
  Card,
  Center,
  Group,
  Loader,
  Progress,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import { IconExternalLink, IconRefresh } from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { useHome } from '../api/hooks';
import { SidecarFrame } from '../components/SidecarFrame';

type SidecarStatus = 'pending' | 'up' | 'down';

// Probe the sidecar before embedding: an opaque no-cors fetch resolves when
// the origin answers (any status) and rejects when the connection is
// refused — the case that used to leave a browser "refused to connect" page
// inside the iframe. Same-origin ('' base, production single-port proxy) is
// trusted without probing.
function useSidecarStatus(base: string | undefined): {
  status: SidecarStatus;
  retry: () => void;
} {
  const [nonce, setNonce] = useState(0);
  const [status, setStatus] = useState<SidecarStatus>('pending');

  useEffect(() => {
    if (!base) {
      setStatus('up');
      return;
    }
    let cancelled = false;
    setStatus('pending');
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), 4000);
    fetch(`${base}/auth/session-ok`, {
      mode: 'no-cors',
      cache: 'no-store',
      signal: controller.signal,
    })
      .then(() => {
        if (!cancelled) {
          setStatus('up');
        }
      })
      .catch(() => {
        if (!cancelled) {
          setStatus('down');
        }
      })
      .finally(() => window.clearTimeout(timer));
    return () => {
      cancelled = true;
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [base, nonce]);

  return { status, retry: () => setNonce((value) => value + 1) };
}

// Metric chip floating over the galaxy; clicking dives into the owning page.
function MetricChip({
  to,
  label,
  testId,
}: {
  to: string;
  label: string;
  testId: string;
}) {
  return (
    <Button
      component={Link}
      to={to}
      size="compact-sm"
      variant="default"
      data-testid={testId}
      style={{ backdropFilter: 'blur(8px)', opacity: 0.92 }}
    >
      {label}
    </Button>
  );
}

export function HomePage() {
  const { name = '' } = useParams();
  const home = useHome(name);
  const sidecarBase = home.data?.sidecar?.base;
  const sidecarPort = (() => {
    if (!sidecarBase) return '';
    try {
      return new URL(sidecarBase).port || '443';
    } catch {
      return '';
    }
  })();
  const { status: sidecarStatus, retry: retrySidecar } = useSidecarStatus(sidecarBase);

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
  const activity = data.agent_activity;
  const sidecar = data.sidecar;
  const northStar = data.north_star;
  const primaryGoal = data.primary_goal;
  const doing = (kanban?.doing ?? []).slice(0, 3);
  const profilePath = (path: string) => `/p/${encodeURIComponent(name)}/${path}`;
  const litPercent = Math.round((skills?.lit_rate ?? 0) * 100);
  const todoEmpty =
    (activity?.pending_total ?? 0) === 0 &&
    (evidence?.needs_review_count ?? 0) === 0 &&
    doing.length === 0;

  return (
    <Stack gap="xl" py="md">
      <Stack gap={4}>
        <Title order={2}>{data.profile} · 首页</Title>
        {northStar?.is_set ? (
          <Text c="dimmed">{northStar.brief || northStar.full}</Text>
        ) : (
          <Text c="dimmed">尚未设置北极星。</Text>
        )}
      </Stack>

      <Card withBorder radius="lg" padding="xl" data-testid="home-focus-card">
        {primaryGoal ? (
          <Stack gap="sm">
            <Group justify="space-between" align="flex-start">
              <Text fw={600} size="lg">
                {primaryGoal.title}
              </Text>
              <Anchor component={Link} to={profilePath('goals')} size="sm">
                全部目标
              </Anchor>
            </Group>
            {primaryGoal.target && (
              <Text size="sm" c="dimmed">
                目标日期:{primaryGoal.target}
              </Text>
            )}
            {primaryGoal.progress !== null && primaryGoal.progress !== undefined ? (
              <Progress
                value={Math.round(primaryGoal.progress * 100)}
                aria-label="目标进度"
                size="lg"
                radius="xl"
              />
            ) : (
              <Text size="sm" c="dimmed">
                暂无关联项目,进度待项目推进后自动推导。
              </Text>
            )}
            <Group gap="xs">
              <Badge variant="light" color="gray">
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
          <Group justify="space-between">
            <Text c="dimmed">暂无主目标。</Text>
            <Anchor component={Link} to={profilePath('goals')} size="sm">
              去目标页设置
            </Anchor>
          </Group>
        )}
      </Card>

      {sidecar && (
        <Card
          withBorder
          radius="lg"
          padding="lg"
          data-testid="home-galaxy-hero"
        >
          <Group justify="space-between" mb="sm">
            <Text fw={600}>成长星系</Text>
            <Button
              component="a"
              href={sidecar.dashboard_url}
              target="_blank"
              rel="noreferrer"
              variant="subtle"
              size="compact-sm"
              leftSection={<IconExternalLink size={14} />}
            >
              新标签打开
            </Button>
          </Group>
          {sidecarStatus === 'pending' && (
            <Center py="xl" data-testid="home-galaxy-probing">
              <Loader size="sm" />
            </Center>
          )}
          {sidecarStatus === 'up' && (
            <div style={{ position: 'relative' }}>
              <SidecarFrame
                title="3D 成长仪表盘"
                url={sidecar.dashboard_url}
                base={sidecar.base}
                handoffToken={sidecar.handoff_token}
                // Viewport-relative with a floor/ceiling: the embedded
                // dashboard canvas needs ~600-900px to show the galaxy
                // without an internal scrollbar at laptop (800px-tall)
                // through large-monitor (1440px-tall) viewport heights.
                height="clamp(640px, calc(100vh - 180px), 900px)"
              />
              <Group
                gap="xs"
                style={{ position: 'absolute', top: 4, left: 4 }}
                data-testid="home-galaxy-metrics"
              >
                {skills?.has_tree && (
                  <MetricChip
                    to={profilePath('skill-tree')}
                    label={`技能点亮 ${skills.lit}/${skills.total} · ${litPercent}%`}
                    testId="home-metric-skills"
                  />
                )}
                {(kanban?.doing_total ?? 0) > 0 && (
                  <MetricChip
                    to={profilePath('kanban')}
                    label={`进行中 ${kanban?.doing_total}`}
                    testId="home-metric-kanban"
                  />
                )}
              </Group>
            </div>
          )}
          {sidecarStatus === 'down' && (
            <Stack gap="md" py="lg" data-testid="home-galaxy-fallback">
              <Group justify="space-around" wrap="wrap">
                {skills?.has_tree && (
                  <Stack gap={2} align="center">
                    <Text fw={700} size="xl">
                      {litPercent}%
                    </Text>
                    <Text size="sm" c="dimmed">
                      技能点亮 {skills.lit}/{skills.total}
                    </Text>
                  </Stack>
                )}
                <Stack gap={2} align="center">
                  <Text fw={700} size="xl">
                    {kanban?.doing_total ?? 0}
                  </Text>
                  <Text size="sm" c="dimmed">
                    进行中任务
                  </Text>
                </Stack>
                <Stack gap={2} align="center">
                  <Text fw={700} size="xl">
                    {evidence?.needs_review_count ?? 0}
                  </Text>
                  <Text size="sm" c="dimmed">
                    待评审证据
                  </Text>
                </Stack>
              </Group>
              <Group justify="center" gap="sm">
                <Text size="sm" c="dimmed">
                  3D 仪表盘服务暂时不可达,以上为静态指标。
                </Text>
                <Button
                  variant="light"
                  size="compact-sm"
                  leftSection={<IconRefresh size={14} />}
                  onClick={retrySidecar}
                >
                  重试
                </Button>
              </Group>
              <Text size="xs" c="dimmed" ta="center" data-testid="sidecar-down-hint">
                仪表盘由浏览器直连 {sidecarBase || 'sidecar'} ——若你通过 SSH 远程访问,请确认同时转发了该端口(如
                ssh -L {sidecarPort}:127.0.0.1:{sidecarPort} &lt;服务器&gt;);若服务未启动,先运行 scripts/dev-web.sh。
              </Text>
            </Stack>
          )}
        </Card>
      )}

      <Card withBorder radius="lg" padding="lg" data-testid="home-today-band">
        <Group justify="space-between" align="center" wrap="wrap" gap="md">
          <Text fw={600}>今日待办</Text>
          {todoEmpty ? (
            <Text size="sm" c="dimmed">
              没有待办,去 inbox 记一条灵感吧。
            </Text>
          ) : (
            <Group gap="lg" wrap="wrap">
              {(activity?.pending_total ?? 0) > 0 && (
                <Anchor
                  component={Link}
                  to={profilePath('activity')}
                  size="sm"
                  data-testid="home-todo-approvals"
                >
                  待审批 {activity?.pending_total}
                </Anchor>
              )}
              {(evidence?.needs_review_count ?? 0) > 0 && (
                <Anchor
                  component={Link}
                  to={profilePath('evidence-review')}
                  size="sm"
                  data-testid="home-todo-review"
                >
                  待评审 {evidence?.needs_review_count}
                </Anchor>
              )}
              {doing.map((task) => (
                <Anchor
                  key={task.id || task.title}
                  component={Link}
                  to={profilePath('kanban')}
                  size="sm"
                  c="dimmed"
                  data-testid="home-todo-doing"
                >
                  {task.title}
                </Anchor>
              ))}
            </Group>
          )}
        </Group>
      </Card>
    </Stack>
  );
}
