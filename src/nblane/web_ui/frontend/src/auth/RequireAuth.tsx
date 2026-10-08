import { Alert, Center, Loader } from '@mantine/core';
import type { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';

import { ApiError } from '../api/client';
import { useMe } from '../api/hooks';

export const FORCED_PASSWORD_PATH = '/settings/account';

// Auth guard for protected routes: redirects to /login when the API rejects
// the session cookie with 401. When auth is off (NBLANE_AUTH_FILE unset) the
// backend answers /auth/me with a synthetic admin, so the guard passes
// through without a login wall.
export function RequireAuth({ children }: { children: ReactNode }) {
  const me = useMe();
  const location = useLocation();

  if (me.isPending) {
    return (
      <Center h="100vh">
        <Loader />
      </Center>
    );
  }
  if (me.isError) {
    if (me.error instanceof ApiError && me.error.status === 401) {
      return <Navigate to="/login" state={{ from: location }} replace />;
    }
    return (
      <Center h="100vh">
        <Alert color="red" title="API 不可用">
          {me.error.message}
        </Alert>
      </Center>
    );
  }
  // A new or reset account must pick its own password before anything else.
  if (me.data.auth_enabled && me.data.must_change_password && location.pathname !== FORCED_PASSWORD_PATH) {
    return <Navigate to={FORCED_PASSWORD_PATH} replace />;
  }
  return <>{children}</>;
}
