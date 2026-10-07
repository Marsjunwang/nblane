import {
  Alert,
  Anchor,
  Badge,
  Box,
  Button,
  Card,
  Center,
  Group,
  Loader,
  Select,
  SimpleGrid,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import {
  IconArrowBackUp,
  IconAutomation,
  IconBook,
  IconExternalLink,
  IconRoute,
  IconWorld,
  IconHistory,
  IconRefresh,
  IconRobot,
  IconRobotOff,
} from '@tabler/icons-react';

import { useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';

import { useAgentJournal, useAssistantStatus, useProfiles, useUndoAgentJournal } from '../api/hooks';
import type { AgentJournalEntry, AssistantStatus } from '../api/types';

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

type SyncState = 'synced' | 'outdated' | 'missing' | null | undefined;

function syncLabel(state: SyncState): { text: string; color: string } {
  if (state === 'synced') return { text: '已是最新', color: 'green' };
  if (state === 'outdated') return { text: '需更新', color: 'orange' };
  if (state === 'missing') return { text: '未安装', color: 'red' };
  return { text: '未知', color: 'gray' };
}

/** 接入方式: how the assistant reaches nblane — the skill and the HTTP client. */
export function AgentChannels({ status }: { status: AssistantStatus }) {
  const skill = syncLabel(status.channels?.skill);
  const http = syncLabel(status.channels?.http_client);
  const needsConnect =
    status.channels?.skill !== 'synced' || status.channels?.http_client !== 'synced';
  const rows = [
    {
      key: 'skill',
      icon: <IconBook size={16} />,
      name: 'nblane 技能',
      role: '说明书：告诉助手怎么调用 nblane、哪些事先问你、怎么撤销。',
      badge: skill,
    },
    {
      key: 'http',
      icon: <IconWorld size={16} />,
      name: 'HTTP 接口',
      role: '唯一通道：打卡、任务、计划、占卜等读写都走这里，以 openclaw 账号登录，按账号权限检查。',
      badge: http,
    },
  ];
  return (
    <Card withBorder radius="md" padding="lg">
      <Group gap="xs" mb="sm">
        <IconRoute size={16} />
        <Text fw={500}>接入方式</Text>
      </Group>
      <Stack gap="sm">
        {rows.map((row) => (
          <Group key={row.key} justify="space-between" wrap="nowrap" gap="sm" align="flex-start">
            <Group gap="xs" wrap="nowrap" align="flex-start" style={{ minWidth: 0 }}>
              <Box mt={2}>{row.icon}</Box>
              <Stack gap={0} style={{ minWidth: 0 }}>
                <Text size="sm" fw={500}>
                  {row.name}
                </Text>
                <Text size="xs" c="dimmed">
                  {row.role}
                </Text>
              </Stack>
            </Group>
            <Badge color={row.badge.color} variant="light" style={{ flexShrink: 0 }}>
              {row.badge.text}
            </Badge>
          </Group>
        ))}
      </Stack>
      <Text size="xs" c="dimmed" mt="sm">
        助手的写入都记在下面的「最近操作」里。MCP 只留给 Cursor 这类本机客户端，助手不用。
        {needsConnect && (
          <>
            {' '}有一项不是最新：到{' '}
            <Anchor component={RouterLink} to="/settings/agents" size="xs">
              设置 → 助手与备份
            </Anchor>{' '}
            点一次「接入 nblane」。
          </>
        )}
      </Text>
    </Card>
  );
}

const JOURNAL_STATUS: Record<AgentJournalEntry['status'], { text: string; color: string }> = {
  undoable: { text: '可撤销', color: 'blue' },
  conflict: { text: '已被改动', color: 'orange' },
  undone: { text: '已撤销', color: 'gray' },
};

/** 最近操作: the agent's journaled writes for one profile, each undoable. */
export function RecentAgentOps() {
  const profiles = useProfiles();
  const names = (profiles.data ?? []).map((item) => item.name);
  const [picked, setPicked] = useState<string | null>(null);
  const profile = picked ?? names[0] ?? '';
  const journal = useAgentJournal(profile);
  const undo = useUndoAgentJournal(profile);
  const entries = journal.data?.entries ?? [];

  return (
    <Card withBorder radius="md" padding="lg">
      <Group justify="space-between" mb="sm">
        <Group gap="xs">
          <IconHistory size={16} />
          <Text fw={500}>最近操作</Text>
        </Group>
        {names.length > 1 && (
          <Select
            aria-label="档案"
            size="xs"
            data={names}
            value={profile}
            onChange={(value) => setPicked(value)}
            allowDeselect={false}
            w={160}
          />
        )}
      </Group>
      <Text size="xs" c="dimmed" mb="sm">
        助手在聊天里做的写入。日常操作直接执行，删除和批量操作会先在聊天里确认；每一条都能在这里撤销，保留{' '}
        {journal.data?.retention_days ?? 30} 天。
      </Text>
      {undo.isError && (
        <Alert color="red" mb="sm" title="撤销失败">
          {undo.error.message}
        </Alert>
      )}
      {journal.isPending && profile ? (
        <Loader size="sm" />
      ) : journal.isError ? (
        <Alert color="red" title="加载失败">
          {journal.error.message}
        </Alert>
      ) : entries.length === 0 ? (
        <Text size="sm" c="dimmed">
          还没有助手操作记录。
        </Text>
      ) : (
        <Stack gap="xs">
          {entries.map((entry) => {
            const meta = JOURNAL_STATUS[entry.status ?? 'undoable'];
            return (
              <Group key={entry.id} justify="space-between" wrap="nowrap" gap="sm">
                <Stack gap={0} style={{ minWidth: 0 }}>
                  <Text size="sm" truncate>
                    {entry.summary || entry.action}
                  </Text>
                  <Text size="xs" c="dimmed">
                    {new Date(entry.at).toLocaleString()} · {entry.actor}
                    {entry.tier === 'T2' ? ' · 聊天确认' : ''}
                  </Text>
                </Stack>
                <Group gap="xs" wrap="nowrap">
                  <Badge color={meta.color} variant="light">
                    {meta.text}
                  </Badge>
                  {entry.status === 'undoable' && (
                    <Button
                      variant="subtle"
                      size="compact-sm"
                      leftSection={<IconArrowBackUp size={14} />}
                      loading={undo.isPending && undo.variables === entry.id}
                      onClick={() => undo.mutate(entry.id)}
                      aria-label={`撤销：${entry.summary || entry.action}`}
                    >
                      撤销
                    </Button>
                  )}
                </Group>
              </Group>
            );
          })}
        </Stack>
      )}
    </Card>
  );
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
              docs/zh/guides/assistant.md。
            </Text>
          </Stack>
        </Card>
      </Center>
    );
  }

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
      <SimpleGrid cols={{ base: 1, sm: 3 }}>
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
      <AgentChannels status={data} />
      <RecentAgentOps />
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
