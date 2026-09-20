// Shared mutation-conflict (HTTP 412) handling for If-Match flows.
//
// Kanban/Inbox/Activity already surface conflicts as a yellow notification +
// auto refetch. Pages that render mutation errors inline instead share these
// components so every If-Match mutation gets the same recognition, copy and
// a manual refresh button: 数据已被他人修改，请刷新后重试。

import { Alert, Button, Group, Text } from '@mantine/core';
import { IconRefresh } from '@tabler/icons-react';

import { ApiError } from '../api/client';

export const CONFLICT_TITLE = '数据已被他人修改';
export const CONFLICT_HINT = '请刷新后重试。';

/** True when a mutation error is a stale-ETag conflict (HTTP 412). */
export function isConflictError(error: unknown): boolean {
  return error instanceof ApiError && error.status === 412;
}

/**
 * Yellow conflict alert with the unified copy and an optional refresh
 * button. Renders nothing when the error is not a 412 conflict.
 */
export function ConflictAlert({
  error,
  onRefetch,
}: {
  error: unknown;
  onRefetch?: () => void;
}) {
  if (!isConflictError(error)) {
    return null;
  }
  return (
    <Alert color="yellow" title={CONFLICT_TITLE} data-testid="conflict-alert">
      <Group justify="space-between" wrap="nowrap">
        <Text size="sm">{CONFLICT_HINT}</Text>
        {onRefetch && (
          <Button
            size="compact-sm"
            variant="default"
            leftSection={<IconRefresh size={14} />}
            onClick={onRefetch}
          >
            刷新
          </Button>
        )}
      </Group>
    </Alert>
  );
}

/**
 * Drop-in mutation error alert: a yellow conflict alert (with refresh
 * button) on 412, the usual red error alert otherwise. Renders nothing when
 * there is no error.
 */
export function MutationErrorAlert({
  error,
  title,
  onRefetch,
}: {
  error: unknown;
  title: string;
  onRefetch?: () => void;
}) {
  if (!error) {
    return null;
  }
  if (isConflictError(error)) {
    return <ConflictAlert error={error} onRefetch={onRefetch} />;
  }
  return (
    <Alert color="red" title={title} data-testid="mutation-error">
      {error instanceof Error ? error.message : String(error)}
    </Alert>
  );
}
