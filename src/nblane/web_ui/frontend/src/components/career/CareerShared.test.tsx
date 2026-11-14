import { fireEvent, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { downloadCareerExport } from '../../api/hooks';
import { renderWithProviders } from '../../test/render';
import { ExportMenu } from './CareerShared';

vi.mock('../../api/hooks', () => ({ downloadCareerExport: vi.fn().mockResolvedValue(undefined), previewCareer: vi.fn() }));
afterEach(() => vi.clearAllMocks());

describe('career export save prerequisite', () => {
  it('does not export an older server document when flushing failed', async () => {
    renderWithProviders(<ExportMenu profile="alice" pdfAvailable source={{}} beforeExport={async () => false} />);
    fireEvent.click(screen.getByTestId('career-export'));
    fireEvent.click(await screen.findByTestId('career-export-md'));
    expect(await screen.findByText('修改尚未保存，导出已暂停。请先处理保存错误或冲突。')).toBeInTheDocument();
    expect(downloadCareerExport).not.toHaveBeenCalled();
  });

  it('exports after the latest edit is acknowledged', async () => {
    renderWithProviders(<ExportMenu profile="alice" pdfAvailable source={{ draft_id: 'd1' }} beforeExport={async () => true} />);
    fireEvent.click(screen.getByTestId('career-export'));
    fireEvent.click(await screen.findByTestId('career-export-md'));
    await waitFor(() => expect(downloadCareerExport).toHaveBeenCalledWith('alice', { format: 'md', draft_id: 'd1' }));
  });
});
