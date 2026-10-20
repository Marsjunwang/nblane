import { fireEvent, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { renderWithProviders } from '../../test/render';
import { AIMetaSuggestions } from './AIMetaSuggestions';

const result = vi.hoisted(() => ({ current: {} as Record<string, unknown> }));
vi.mock('./contentJobs', () => ({
  runContentJob: () => ({ result: Promise.resolve(result.current), cancel: () => undefined }),
}));

const draft = { title: 'T', summary: '', tags: [], body: '正文' };

describe('AIMetaSuggestions', () => {
  it('says when the suggestions came from an excerpt of a long post', async () => {
    result.current = { titles: ['新标题'], summaries: ['新摘要'], tags: [], truncated: true };
    renderWithProviders(<AIMetaSuggestions profile="alice" enabled draft={draft} onApply={() => undefined} />);
    fireEvent.click(screen.getByRole('button', { name: '生成' }));
    expect(await screen.findByText('文章较长，建议依据提纲、开头和结尾生成。')).toBeInTheDocument();
  });

  it('passes a picked summary to onApply and shows no hint for short posts', async () => {
    result.current = { titles: [], summaries: ['新摘要'], tags: [], truncated: false };
    const onApply = vi.fn();
    renderWithProviders(<AIMetaSuggestions profile="alice" enabled draft={draft} onApply={onApply} />);
    fireEvent.click(screen.getByRole('button', { name: '生成' }));
    fireEvent.click(await screen.findByText('新摘要'));
    expect(onApply).toHaveBeenCalledWith({ summary: '新摘要' });
    expect(screen.queryByText(/文章较长/)).toBeNull();
  });
});
