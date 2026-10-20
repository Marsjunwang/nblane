import { notifications } from '@mantine/notifications';
import { act, fireEvent, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { renderWithProviders } from '../../test/render';
import { showAIUndo } from './aiUndoNotice';

beforeEach(() => {
  notifications.clean();
  notifications.cleanQueue();
});

describe('showAIUndo', () => {
  it('names the replaced fields and calls undo once when 撤销 is clicked', async () => {
    renderWithProviders(<div />);
    const onUndo = vi.fn();
    act(() => showAIUndo(['title', 'summary'], onUndo));
    expect(await screen.findByText('已用 AI 建议替换标题、摘要。')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '撤销' }));
    expect(onUndo).toHaveBeenCalledOnce();
    await waitFor(() => expect(screen.queryByText('已用 AI 建议替换标题、摘要。')).toBeNull());
  });
});
