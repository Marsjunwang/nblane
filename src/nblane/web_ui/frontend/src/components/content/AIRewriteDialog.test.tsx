import { fireEvent, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { renderWithProviders } from '../../test/render';
import { AIRewriteDialog, type RewriteState } from './AIRewriteDialog';

function renderDialog(state: RewriteState, handlers: { onAccept?: () => void; onCopy?: () => void } = {}) {
  return renderWithProviders(
    <AIRewriteDialog
      state={state}
      view="diff"
      onViewChange={() => undefined}
      onEditCandidate={() => undefined}
      onAccept={handlers.onAccept ?? (() => undefined)}
      onRetry={() => undefined}
      onClose={() => undefined}
      onCopy={handlers.onCopy}
    />,
  );
}

const done: RewriteState = { operation: 'polish', original: '原文。', status: 'done', text: '改后。' };

describe('AIRewriteDialog', () => {
  it('keeps the candidate and explains why a replace wrote nothing', async () => {
    renderDialog({ ...done, acceptError: '源码模式下无法按选区替换。' });
    expect(await screen.findByTestId('content-ai-accept-error')).toHaveTextContent('源码模式下无法按选区替换。');
    expect(screen.getByTestId('content-ai-diff')).toHaveTextContent('改后。');
    expect(screen.getByTestId('content-ai-accept')).toBeEnabled();
  });

  it('offers copy for a finished candidate', async () => {
    const onCopy = vi.fn();
    renderDialog(done, { onCopy });
    fireEvent.click(await screen.findByRole('button', { name: '复制候选' }));
    expect(onCopy).toHaveBeenCalledOnce();
  });

  it('shows no copy or warning while running', async () => {
    renderDialog({ operation: 'polish', original: '原文。', status: 'running' }, { onCopy: vi.fn() });
    expect(await screen.findByText('AI 正在处理…')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '复制候选' })).toBeNull();
    expect(screen.queryByTestId('content-ai-accept-error')).toBeNull();
  });
});
