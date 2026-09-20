import { fireEvent, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { ApiError } from '../api/client';
import { renderWithProviders } from '../test/render';
import {
  ConflictAlert,
  isConflictError,
  MutationErrorAlert,
} from './ConflictAlert';

describe('isConflictError', () => {
  it('recognizes only ApiError with status 412', () => {
    expect(isConflictError(new ApiError(412, 'stale', 'etag_mismatch'))).toBe(true);
    expect(isConflictError(new ApiError(422, 'ambiguous', 'kanban_card_ambiguous'))).toBe(false);
    expect(isConflictError(new ApiError(500, 'boom'))).toBe(false);
    expect(isConflictError(new Error('412'))).toBe(false);
    expect(isConflictError(null)).toBe(false);
    expect(isConflictError(undefined)).toBe(false);
  });
});

describe('ConflictAlert', () => {
  it('renders nothing for non-412 errors', () => {
    renderWithProviders(<ConflictAlert error={new ApiError(500, 'boom')} />);
    expect(screen.queryByTestId('conflict-alert')).not.toBeInTheDocument();
  });

  it('shows the unified copy and refresh button for a 412 conflict', () => {
    const onRefetch = vi.fn();
    renderWithProviders(
      <ConflictAlert error={new ApiError(412, 'stale', 'etag_mismatch')} onRefetch={onRefetch} />,
    );

    const alert = screen.getByTestId('conflict-alert');
    expect(alert).toHaveTextContent('数据已被他人修改');
    expect(alert).toHaveTextContent('请刷新后重试');
    // The raw server message is replaced by the unified copy.
    expect(alert).not.toHaveTextContent('stale');

    fireEvent.click(screen.getByRole('button', { name: '刷新' }));
    expect(onRefetch).toHaveBeenCalledTimes(1);
  });

  it('omits the refresh button when no refetch callback is given', () => {
    renderWithProviders(<ConflictAlert error={new ApiError(412, 'stale')} />);
    expect(screen.getByTestId('conflict-alert')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '刷新' })).not.toBeInTheDocument();
  });
});

describe('MutationErrorAlert', () => {
  it('renders nothing when there is no error', () => {
    renderWithProviders(<MutationErrorAlert error={null} title="操作失败" />);
    expect(screen.queryByTestId('mutation-error')).not.toBeInTheDocument();
    expect(screen.queryByTestId('conflict-alert')).not.toBeInTheDocument();
  });

  it('renders the fallback red alert for generic errors', () => {
    renderWithProviders(<MutationErrorAlert error={new Error('broken')} title="操作失败" />);
    const alert = screen.getByTestId('mutation-error');
    expect(alert).toHaveTextContent('操作失败');
    expect(alert).toHaveTextContent('broken');
    expect(screen.queryByRole('button', { name: '刷新' })).not.toBeInTheDocument();
  });

  it('upgrades 412 errors to the conflict alert with refresh', () => {
    const onRefetch = vi.fn();
    renderWithProviders(
      <MutationErrorAlert
        error={new ApiError(412, 'stale', 'etag_mismatch')}
        title="操作失败"
        onRefetch={onRefetch}
      />,
    );
    expect(screen.getByTestId('conflict-alert')).toBeInTheDocument();
    expect(screen.queryByTestId('mutation-error')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '刷新' }));
    expect(onRefetch).toHaveBeenCalledTimes(1);
  });
});
