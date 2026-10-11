import { Alert, Button, Modal, PasswordInput, Stack, Text, TextInput } from '@mantine/core';
import { useQueryClient } from '@tanstack/react-query';
import { useState, type FormEvent } from 'react';

import { useLogin, useMe } from '../api/hooks';
import { markSessionRestored, useSessionExpired } from '../api/session';

/**
 * Re-login over the current page when the session expires mid-use.
 *
 * The page underneath stays mounted (RequireAuth keeps the cached user), so
 * an open editor keeps its unsaved text; after login it retries its save on
 * SESSION_RESTORED_EVENT.
 */
export function SessionExpiredModal() {
  const expired = useSessionExpired();
  const me = useMe();
  const login = useLogin();
  const queryClient = useQueryClient();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const knownUser = me.data?.id ?? '';

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    login.mutate(
      { username: (username || knownUser).trim(), password },
      {
        onSuccess: () => {
          setPassword('');
          markSessionRestored();
          void queryClient.invalidateQueries();
        },
      },
    );
  };

  return (
    <Modal
      opened={expired}
      onClose={() => undefined}
      withCloseButton={false}
      closeOnClickOutside={false}
      closeOnEscape={false}
      centered
      title="登录已过期"
      data-testid="session-expired-modal"
    >
      <form onSubmit={onSubmit}>
        <Stack gap="sm">
          <Text size="sm" c="dimmed">
            重新登录后继续，当前页面和没保存的修改都还在。
          </Text>
          <TextInput
            label="用户名"
            value={username || knownUser}
            onChange={(e) => setUsername(e.currentTarget.value)}
            autoComplete="username"
            required
          />
          <PasswordInput
            label="密码"
            value={password}
            onChange={(e) => setPassword(e.currentTarget.value)}
            autoComplete="current-password"
            data-autofocus
            required
          />
          {login.isError && (
            <Alert color="red" data-testid="session-login-error">
              {login.error.message}
            </Alert>
          )}
          <Button type="submit" loading={login.isPending}>
            登录并继续
          </Button>
        </Stack>
      </form>
    </Modal>
  );
}
