import {
  Alert,
  Button,
  Center,
  Container,
  Paper,
  PasswordInput,
  TextInput,
  Title,
} from '@mantine/core';
import { useState, type FormEvent } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';

import { useLogin, useMe } from '../api/hooks';

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const me = useMe();
  const login = useLogin();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  // In-app redirect target handed over by RequireAuth. Only same-site paths
  // are accepted — absolute URLs and protocol-relative "//host" fall back to
  // the profile list so the login page can't be used as an open redirector.
  const rawFrom = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname;
  const from =
    rawFrom && rawFrom.startsWith('/') && !rawFrom.startsWith('//') ? rawFrom : undefined;

  // Skip the login wall when auth is off, or when a session already exists.
  if (me.data) {
    return <Navigate to={from ?? '/'} replace />;
  }

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    login.mutate(
      { username: username.trim(), password },
      { onSuccess: () => navigate(from ?? '/', { replace: true }) },
    );
  };

  return (
    <Center h="100vh">
      <Container size="xs" w="100%">
        <Paper withBorder shadow="sm" p="xl" radius="md">
          <Title order={2} ta="center" mb="lg">
            nblane 登录
          </Title>
          <form onSubmit={onSubmit}>
            <TextInput
              label="用户名"
              value={username}
              onChange={(e) => setUsername(e.currentTarget.value)}
              autoComplete="username"
              required
              mb="sm"
            />
            <PasswordInput
              label="密码"
              value={password}
              onChange={(e) => setPassword(e.currentTarget.value)}
              autoComplete="current-password"
              required
              mb="md"
            />
            {login.isError && (
              <Alert color="red" mb="md" data-testid="login-error">
                {login.error.message}
              </Alert>
            )}
            <Button type="submit" fullWidth loading={login.isPending}>
              登录
            </Button>
          </form>
        </Paper>
      </Container>
    </Center>
  );
}
