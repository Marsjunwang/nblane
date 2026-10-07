import {
  Alert,
  Badge,
  Button,
  Center,
  Drawer,
  Group,
  Loader,
  Paper,
  Stack,
  Text,
  Checkbox,
} from '@mantine/core';
import { IconAlertTriangle, IconExternalLink, IconRefresh } from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';

import { useAIExceptions, useDismissAIExceptions } from '../api/hooks';

interface AIExceptionDrawerProps {
  profile: string;
  opened: boolean;
  onClose: () => void;
}

export function AIExceptionDrawer({ profile, opened, onClose }: AIExceptionDrawerProps) {
  const exceptions = useAIExceptions(profile);
  const items = exceptions.data?.items ?? [];
  const [selected, setSelected] = useState<string[]>([]);
  const dismiss = useDismissAIExceptions(profile);
  const selectableIds = items.filter((item) => item.id.startsWith('activity:')).map((item) => item.id);
  const allSelected = selectableIds.length > 0 && selectableIds.every((id) => selected.includes(id));

  useEffect(() => {
    setSelected((current) => current.filter((id) => selectableIds.includes(id)));
  }, [exceptions.data, selectableIds.join('|')]);

  const toggle = (id: string, checked: boolean) => {
    setSelected((current) => checked ? [...new Set([...current, id])] : current.filter((item) => item !== id));
  };

  const dismissSelected = async () => {
    if (!selected.length) return;
    try {
      await dismiss.mutateAsync(selected);
      setSelected([]);
    } catch {
      // The mutation error is exposed by the hook and the list remains selected
      // so the owner can retry without losing the batch.
    }
  };

  return (
    <Drawer
      opened={opened}
      onClose={onClose}
      position="right"
      size="md"
      title="AI 异常"
      overlayProps={{ backgroundOpacity: 0.35, blur: 2 }}
    >
      {exceptions.isPending ? (
        <Center py="xl">
          <Loader />
        </Center>
      ) : exceptions.isError ? (
        <Alert color="red" title="异常列表加载失败">
          {exceptions.error.message}
        </Alert>
      ) : items.length === 0 ? (
        <Stack align="center" gap="sm" py="xl">
          <IconAlertTriangle size={28} opacity={0.45} />
          <Text c="dimmed">当前没有需要处理的 AI 异常。</Text>
        </Stack>
      ) : (
        <Stack gap="sm">
          <Group justify="space-between" align="flex-start">
            <Text size="sm" c="dimmed">
              仅显示失败、冲突或被阻止的 AI 操作。
            </Text>
            <Group gap="xs">
              <Button
                variant="light"
                color="gray"
                size="compact-sm"
                disabled={!selected.length}
                loading={dismiss.isPending}
                onClick={() => void dismissSelected()}
              >
                忽略选中 ({selected.length})
              </Button>
              <Button
                variant="subtle"
                size="compact-sm"
                leftSection={<IconRefresh size={14} />}
                loading={exceptions.isFetching}
                onClick={() => void exceptions.refetch()}
              >
                刷新
              </Button>
            </Group>
          </Group>
          {selectableIds.length > 0 && (
            <Checkbox
              label="全选可忽略的异常"
              checked={allSelected}
              indeterminate={selected.length > 0 && !allSelected}
              onChange={(event) => setSelected(event.currentTarget.checked ? selectableIds : [])}
            />
          )}
          {items.map((item) => (
            <Paper key={item.id} withBorder p="sm" radius="sm">
              <Stack gap="xs">
                <Group justify="space-between" align="flex-start" wrap="nowrap">
                  {item.id.startsWith('activity:') && (
                    <Checkbox
                      aria-label={`选择 ${item.title}`}
                      checked={selected.includes(item.id)}
                      onChange={(event) => toggle(item.id, event.currentTarget.checked)}
                    />
                  )}
                  <div>
                    <Text fw={600}>{item.title}</Text>
                    <Group gap="xs" mt={4}>
                      <Badge size="sm" variant="light" color={item.severity === 'warning' ? 'orange' : 'red'}>
                        {item.source || 'AI'}
                      </Badge>
                      {item.action && (
                        <Text size="xs" c="dimmed" lineClamp={1}>
                          {item.action}
                        </Text>
                      )}
                    </Group>
                  </div>
                  <Text size="xs" c="dimmed" ta="right" style={{ whiteSpace: 'nowrap' }}>
                    {formatExceptionTime(item.created)}
                  </Text>
                </Group>
                <Text size="sm" style={{ whiteSpace: 'pre-wrap' }}>
                  {item.message}
                </Text>
                {item.href && (
                  <Group justify="flex-end" mt={2}>
                    <Button
                      component={RouterLink}
                      to={item.href}
                      variant="light"
                      size="compact-sm"
                      leftSection={<IconExternalLink size={14} />}
                      onClick={onClose}
                    >
                      打开来源
                    </Button>
                  </Group>
                )}
              </Stack>
            </Paper>
          ))}
        </Stack>
      )}
    </Drawer>
  );
}

function formatExceptionTime(value: string): string {
  if (!value) {
    return '';
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}
