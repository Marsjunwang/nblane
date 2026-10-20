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
  it('marks removed and added text for screen readers, not by colour alone', async () => {
    renderDialog({ operation: 'polish', original: '旧的句子。', status: 'done', text: '新的句子。' });
    const diff = await screen.findByTestId('content-ai-diff');
    expect(diff.querySelector('del')).toHaveTextContent('删除：旧');
    expect(diff.querySelector('ins')).toHaveTextContent('新增：新');
  });

  it('titles the dialog with the same label as the toolbar menu', async () => {
    renderDialog({ ...done, operation: 'tone' });
    expect(await screen.findByText('AI 调整为专业语气')).toBeInTheDocument();
  });

  it('announces progress while running', async () => {
    renderDialog({ operation: 'polish', original: '原文。', status: 'running', progress: 'AI 正在改写选中内容。' });
    expect(await screen.findByRole('status')).toHaveTextContent('AI 正在改写选中内容。');
  });

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

describe('AIRewriteDialog on a phone', () => {
  it('goes full screen so 接受并替换 stays reachable', async () => {
    const matchMedia = window.matchMedia;
    window.matchMedia = ((query: string) => ({ ...matchMedia(query), matches: query.includes('max-width: 48em') })) as typeof window.matchMedia;
    try {
      renderDialog(done);
      const accept = await screen.findByTestId('content-ai-accept');
      expect(accept.closest('.mantine-Modal-content')).toHaveAttribute('data-full-screen', 'true');
    } finally {
      window.matchMedia = matchMedia;
    }
  });
});
