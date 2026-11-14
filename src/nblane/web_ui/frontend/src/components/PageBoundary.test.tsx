import { fireEvent, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Link, Outlet, Route, Routes } from 'react-router-dom';

import { renderWithProviders } from '../test/render';
import { PageBoundary, retryableLazy, RouteContent } from './PageBoundary';

afterEach(() => vi.restoreAllMocks());

describe('PageBoundary', () => {
  it('retries a rejected lazy import with a fresh loader', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
    const loader = vi.fn().mockRejectedValueOnce(new Error('chunk unavailable')).mockResolvedValue({ default: () => <div>页面内容</div> });
    const Page = retryableLazy(loader);
    renderWithProviders(<PageBoundary><Page /></PageBoundary>);
    expect(await screen.findByText('页面暂时无法打开')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '重新加载页面' }));
    expect(await screen.findByText('页面内容')).toBeInTheDocument();
    expect(loader).toHaveBeenCalledTimes(2);
  });

  it('keeps navigation available after a page throws', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
    function Broken(): never { throw new Error('render failed'); }
    renderWithProviders(
      <Routes>
        <Route element={<><Link to="/other">项目</Link><RouteContent><Outlet /></RouteContent></>}>
          <Route path="/" element={<Broken />} />
          <Route path="/other" element={<div>项目内容</div>} />
        </Route>
      </Routes>,
    );
    expect(await screen.findByText('页面暂时无法打开')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('link', { name: '项目' }));
    expect(await screen.findByText('项目内容')).toBeInTheDocument();
  });
});
