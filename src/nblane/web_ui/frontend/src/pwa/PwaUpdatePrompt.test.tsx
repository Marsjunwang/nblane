import { fireEvent, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { renderWithProviders } from '../test/render';
import { PwaUpdatePrompt } from './PwaUpdatePrompt';

const pwa = vi.hoisted(() => ({
  needRefresh: false,
  setNeedRefresh: vi.fn((_value: boolean) => undefined),
  updateServiceWorker: vi.fn(async (_reloadPage?: boolean) => undefined),
}));

vi.mock('virtual:pwa-register/react', () => ({
  useRegisterSW: () => ({
    needRefresh: [pwa.needRefresh, pwa.setNeedRefresh],
    updateServiceWorker: pwa.updateServiceWorker,
  }),
}));

beforeEach(() => {
  pwa.needRefresh = false;
  pwa.setNeedRefresh.mockClear();
  pwa.updateServiceWorker.mockClear();
});

describe('PwaUpdatePrompt', () => {
  it('stays hidden and does not update when no worker is waiting', () => {
    renderWithProviders(<PwaUpdatePrompt />);

    expect(screen.queryByTestId('pwa-update-prompt')).not.toBeInTheDocument();
    expect(pwa.updateServiceWorker).not.toHaveBeenCalled();
  });

  it('dismisses the prompt without reloading or activating the worker', () => {
    pwa.needRefresh = true;
    renderWithProviders(<PwaUpdatePrompt />);

    expect(screen.getByTestId('pwa-update-prompt')).toHaveTextContent('请先保存正在编辑的内容');
    expect(pwa.updateServiceWorker).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: '稍后' }));
    expect(pwa.setNeedRefresh).toHaveBeenCalledWith(false);
    expect(pwa.updateServiceWorker).not.toHaveBeenCalled();
  });

  it('activates the waiting worker only after explicit confirmation', () => {
    pwa.needRefresh = true;
    renderWithProviders(<PwaUpdatePrompt />);

    fireEvent.click(screen.getByRole('button', { name: '立即更新' }));
    expect(pwa.updateServiceWorker).toHaveBeenCalledTimes(1);
    expect(pwa.updateServiceWorker).toHaveBeenCalledWith(true);
  });
});
