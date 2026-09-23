import { Alert, Anchor, Button, Card, Center, Group, List, Loader, Stack, Text, Title } from '@mantine/core';
import { IconExternalLink, IconTerminal2, IconTerminal } from '@tabler/icons-react';

import { useWorkshopStatus } from '../api/hooks';
import { SidecarFrame } from '../components/SidecarFrame';

/**
 * 车间 — the remote workshop terminal (Phase 0.5 Step 2): the machine's ttyd
 * web terminal (tmux session "workshop", cwd = repo root) embedded in an
 * iframe. The iframe URL comes from the backend (NBLANE_WORKSHOP_URL, default
 * same-origin /terminal/ which the production Caddy proxies with basic_auth).
 * When the server-side probe says ttyd is down, the page shows start
 * instructions instead of a dead frame.
 */
export function WorkshopPage() {
  const status = useWorkshopStatus();

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

  if (!data.reachable) {
    return (
      <Center py="xl">
        <Card withBorder radius="md" padding="xl" maw={560}>
          <Stack align="center" gap="sm">
            <IconTerminal size={40} stroke={1.5} />
            <Title order={3}>车间终端未运行</Title>
            <Text size="sm" c="dimmed" ta="center">
              网页终端由 ttyd 提供(tmux 会话 workshop,工作目录为仓库根)。在服务器上启动:
            </Text>
            <Card withBorder radius="sm" padding="sm" w="100%">
              <Stack gap={4}>
                <Text size="sm" ff="monospace">
                  systemctl --user start nblane-workshop.service
                </Text>
                <Text size="xs" c="dimmed" ff="monospace">
                  # 或直接运行:~/.local/bin/nblane-workshop-ttyd.sh
                </Text>
              </Stack>
            </Card>
            <List size="sm" c="dimmed" spacing={4}>
              <List.Item>本服务只绑定 127.0.0.1:7668,公网经 Caddy /terminal/ 入口(basic_auth)。</List.Item>
              <List.Item>详见 docs/zh/dev/phase0.5-remote-terminal.md。</List.Item>
            </List>
            <Button
              variant="light"
              size="compact-sm"
              loading={status.isRefetching}
              onClick={() => status.refetch()}
            >
              重新检测
            </Button>
          </Stack>
        </Card>
      </Center>
    );
  }

  return (
    <Stack gap="xs">
      <Group justify="space-between">
        <Group gap="xs">
          <IconTerminal2 size={20} />
          <Title order={2}>车间</Title>
        </Group>
        <Button
          component="a"
          href={data.url}
          target="_blank"
          rel="noopener noreferrer"
          size="compact-sm"
          variant="default"
          leftSection={<IconExternalLink size={14} />}
        >
          新标签页打开
        </Button>
      </Group>
      <SidecarFrame
        title="车间终端"
        url={data.url}
        base=""
        height="calc(100vh - 240px)"
      />
      <Group justify="space-between">
        <Text size="xs" c="dimmed">
          会话持久化于 tmux(workshop):锁屏/断线重进内容仍在。公网入口有独立 basic_auth(用户名 workshop)。
        </Text>
        <Anchor href={data.url} target="_blank" rel="noopener noreferrer" size="xs">
          {data.url}
        </Anchor>
      </Group>
    </Stack>
  );
}
