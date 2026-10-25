import { fireEvent, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { renderWithProviders } from '../../test/render';
import { QuickAddInput, useQuickAddController } from './QuickAddInput';
import type { QuickAddCallbacks } from './QuickAddInput';

function Harness({
  onSubmit,
}: {
  onSubmit: (title: string, callbacks: QuickAddCallbacks) => void;
}) {
  const controller = useQuickAddController();
  return (
    <>
      <QuickAddInput laneId="p1" pending={false} controller={controller} onSubmit={onSubmit} />
      <output data-testid="continuous-state">{String(controller.continuous)}</output>
    </>
  );
}

function openEditor(): HTMLInputElement {
  fireEvent.click(screen.getByTestId('quick-add-p1'));
  return screen.getByTestId('quick-add-input-p1') as HTMLInputElement;
}

describe('QuickAddInput', () => {
  afterEach(() => {
    window.localStorage.clear();
  });

  it('keeps the draft, focus and inline error when submission fails', () => {
    const onSubmit = vi.fn((_title: string, callbacks: QuickAddCallbacks) => {
      callbacks.onError('网络失败');
    });
    renderWithProviders(<Harness onSubmit={onSubmit} />);
    const input = openEditor();
    fireEvent.change(input, { target: { value: '保留这段草稿' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(input).toHaveValue('保留这段草稿');
    expect(input).toHaveFocus();
    expect(screen.getByText('网络失败')).toBeInTheDocument();
    expect(screen.getByTestId('quick-add-editor-p1')).toBeInTheDocument();
  });

  it('clears the title only after a successful submission', () => {
    const onSubmit = vi.fn((_title: string, callbacks: QuickAddCallbacks) => {
      callbacks.onSuccess();
    });
    renderWithProviders(<Harness onSubmit={onSubmit} />);
    const input = openEditor();
    fireEvent.change(input, { target: { value: '已创建' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    expect(onSubmit).toHaveBeenCalledWith('已创建', expect.objectContaining({
      onSuccess: expect.any(Function),
      onError: expect.any(Function),
    }));
    expect(input).toHaveValue('');
  });

  it('keeps the editor open when enabling continuous mode and after empty blur', () => {
    renderWithProviders(<Harness onSubmit={vi.fn()} />);
    const input = openEditor();
    const checkbox = screen.getByRole('checkbox', { name: '连续添加' });

    fireEvent.blur(input, { relatedTarget: checkbox });
    fireEvent.click(checkbox);
    expect(checkbox).toBeChecked();
    expect(screen.getByTestId('continuous-state')).toHaveTextContent('true');
    fireEvent.blur(input, { relatedTarget: null });
    expect(screen.getByTestId('quick-add-editor-p1')).toBeInTheDocument();
    expect(window.localStorage.getItem('nblane.projects.quickAdd.continuous')).toBe('true');
  });

  it('closes an empty editor when focus moves to another lane', () => {
    renderWithProviders(<Harness onSubmit={vi.fn()} />);
    const input = openEditor();
    const otherLane = document.createElement('div');
    otherLane.dataset.quickAddRoot = 'other-lane';
    document.body.append(otherLane);
    try {
      fireEvent.blur(input, { relatedTarget: otherLane });
      expect(screen.queryByTestId('quick-add-editor-p1')).not.toBeInTheDocument();
    } finally {
      otherLane.remove();
    }
  });
});
