import {
  Alert,
  Anchor,
  Badge,
  Button,
  Card,
  Center,
  Group,
  Loader,
  SimpleGrid,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import {
  IconAutomation,
  IconExternalLink,
  IconPlugConnected,
  IconRefresh,
  IconRobot,
  IconRobotOff,
} from '@tabler/icons-react';

import { useAssistantStatus } from '../api/hooks';

/** Human-readable uptime from milliseconds. */
export function formatUptime(uptimeMs: number | null): string {
  if (uptimeMs === null) {
    return '未知';
  }
  const minutes = Math.floor(uptimeMs / 60_000);
  if (minutes < 1) {
    return '刚刚启动';
  }
  const days = Math.floor(minutes / 1440);
  const hours = Math.floor((minutes % 1440) / 60);
  const mins = minutes % 60;
  if (days > 0) {
    return `${days} 天 ${hours} 小时`;
  }
  if (hours > 0) {
    return `${hours} 小时 ${mins} 分`;
  }
  return `${mins} 分`;
}

function mcpLabel(registered: boolean | null): { text: string; color: string } {
  if (registered === null) {
    return { text: '未知', color: 'gray' };
  }
  return registered
    ? { text: '已注册', color: 'green' }
    : { text: '未注册', color: 'red' };
}

export function AssistantPage() {
  const status = useAssistantStatus();

  if (status.isPending) {
    return (
      <Center py="xl">
        <Loader />
      </Center>
    );
  }
  if (status.isError) {
    return (
      <Alert color="red" title="加载失败">
        {status.error.message}
      </Alert>
    );
  }

  const data = status.data;

  if (!data.available) {
    return (
      <Center py="xl">
        <Card withBorder radius="md" padding="xl" maw={480}>
          <Stack align="center" gap="sm">
            <IconRobotOff size={40} stroke={1.5} />
            <Title order={3}>本机未安装 OpenClaw</Title>
            <Text size="sm" c="dimmed" ta="center">
              助手状态依赖本机的 OpenClaw 网关。安装与接入步骤见仓库文档
              docs/zh/guides/openclaw-integration.md。
            </Text>
          </Stack>
        </Card>
      </Center>
    );
  }

  const mcp = mcpLabel(data.mcp_nblane_registered ?? null);
  return (
    <Stack gap="md">
      <Group justify="space-between">
        <Title order={2}>助手</Title>
        <Button
          component="a"
          href={data.console_url}
          target="_blank"
          rel="noopener noreferrer"
          size="md"
          leftSection={<IconExternalLink size={16} />}
        >
          打开控制台
        </Button>
      </Group>
      <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }}>
        <Card withBorder radius="md" padding="lg">
          <Group gap="xs" mb="sm">
            <IconRobot size={16} />
            <Text fw={500}>Gateway 状态</Text>
          </Group>
          <Stack gap={4}>
            <Badge
              color={data.gateway?.ready ? 'green' : 'red'}
              variant="light"
              w="fit-content"
            >
              {data.gateway?.ready ? '就绪' : '未就绪'}
            </Badge>
            <Text size="sm" c="dimmed">
              运行时长:{formatUptime(data.gateway?.uptime_ms ?? null)}
            </Text>
            <Text size="sm" c="dimmed">
              版本:{data.version ?? '未知'}
            </Text>
          </Stack>
        </Card>
        <Card withBorder radius="md" padding="lg">
          <Group gap="xs" mb="sm">
            <IconPlugConnected size={16} />
            <Text fw={500}>MCP nblane 注册</Text>
          </Group>
          <Badge color={mcp.color} variant="light" w="fit-content">
            {mcp.text}
          </Badge>
        </Card>
        <Card withBorder radius="md" padding="lg">
          <Group gap="xs" mb="sm">
            <IconAutomation size={16} />
            <Text fw={500}>自动化</Text>
          </Group>
          {data.automations ? (
            <Text size="sm" c="dimmed">
              共 {data.automations.total} 条,启用 {data.automations.enabled} 条
            </Text>
          ) : (
            <Text size="sm" c="dimmed">
              未知
            </Text>
          )}
        </Card>
        <Card withBorder radius="md" padding="lg">
          <Group gap="xs" mb="sm">
            <IconRefresh size={16} />
            <Text fw={500}>检查时间</Text>
          </Group>
          <Stack gap="xs">
            <Text size="sm" c="dimmed">
              {new Date(data.checked_at).toLocaleString()}
            </Text>
            <Button
              variant="light"
              size="compact-sm"
              w="fit-content"
              leftSection={<IconRefresh size={14} />}
              loading={status.isRefetching}
              onClick={() => status.refetch()}
            >
              刷新
            </Button>
          </Stack>
        </Card>
      </SimpleGrid>
      <Text size="xs" c="dimmed">
        控制台在新标签页打开;状态每 60 秒缓存一次。控制台地址来自
        NBLANE_OPENCLAW_CONSOLE_URL(生产环境为 Caddy /openclaw 反代路径)。
      </Text>
      <Anchor href={data.console_url} target="_blank" rel="noopener noreferrer" size="xs">
        {data.console_url}
      </Anchor>
    </Stack>
  );
}
