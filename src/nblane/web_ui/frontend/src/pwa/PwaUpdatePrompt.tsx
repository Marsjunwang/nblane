import { Alert, Button, Group, Stack, Text } from '@mantine/core';
import { useRegisterSW } from 'virtual:pwa-register/react';

export function PwaUpdatePrompt() {
  const {
    needRefresh: [needRefresh, setNeedRefresh],
    updateServiceWorker,
  } = useRegisterSW();

  if (!needRefresh) return null;

  return (
    <Alert
      color="yellow"
      variant="light"
      title="发现新版本"
      data-testid="pwa-update-prompt"
      style={{
        position: 'fixed',
        right: 16,
        bottom: 16,
        width: 'min(420px, calc(100vw - 32px))',
        zIndex: 1000,
      }}
    >
      <Stack gap="sm">
        <Text size="sm">请先保存正在编辑的内容；确认更新后页面会重新加载。</Text>
        <Group justify="flex-end" gap="xs">
          <Button variant="default" size="compact-sm" onClick={() => setNeedRefresh(false)}>
            稍后
          </Button>
          <Button
            size="compact-sm"
            onClick={() => {
              void updateServiceWorker(true);
            }}
          >
            立即更新
          </Button>
        </Group>
      </Stack>
    </Alert>
  );
}
