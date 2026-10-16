import { fireEvent, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';

import { jsonResponse, renderWithProviders } from '../test/render';
import { AppLayout } from './AppLayout';
import { BackToWorkButton, lastWorkHome, workPathLabel } from './BackToWork';

afterEach(() => {
  vi.unstubAllGlobals();
  window.sessionStorage.clear();
});

function stubMe() {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () =>
      jsonResponse(200, { id: 'u1', display_name: 'Admin', role: 'admin', auth_enabled: false }),
    ),
  );
}

function app(initial: string) {
  return renderWithProviders(
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<div>profile-list</div>} />
        <Route path="/p/:name/skill-tree" element={<div>skill-tree-page</div>} />
        <Route path="/p/:name/home" element={<div>home-page</div>} />
        <Route path="/settings" element={<BackToWorkButton />} />
      </Route>
    </Routes>,
    initial,
  );
}

describe('BackToWork', () => {
  it('labels known pages and falls back to the profile list', () => {
    expect(workPathLabel('/p/alice/skill-tree')).toBe('技能树');
    expect(workPathLabel('/p/alice/research/library?x=1')).toBe('研究台');
    expect(workPathLabel('/')).toBe('档案列表');
    expect(lastWorkHome()).toBe('/');
  });

  it('returns to the last business page in one click', async () => {
    stubMe();
    window.sessionStorage.setItem('nblane.nav.lastWorkPath', '/p/alice/skill-tree');
    app('/settings');
    const back = await screen.findByTestId('back-to-work');
    expect(back).toHaveTextContent('返回技能树');
    // Off-profile pages: the brand links to the remembered profile home.
    expect(screen.getByTestId('brand-home')).toHaveAttribute('href', '/p/alice/home');
    fireEvent.click(back);
    expect(await screen.findByText('skill-tree-page')).toBeInTheDocument();
  });

  it('remembers business pages as they are visited', async () => {
    stubMe();
    app('/p/bob/skill-tree');
    await screen.findByText('skill-tree-page');
    expect(window.sessionStorage.getItem('nblane.nav.lastWorkPath')).toBe('/p/bob/skill-tree');
    expect(screen.getByTestId('brand-home')).toHaveAttribute('href', '/p/bob/home');
  });

  it('goes to the profile list without a remembered page', async () => {
    stubMe();
    app('/settings');
    const back = await screen.findByTestId('back-to-work');
    expect(back).toHaveTextContent('返回档案列表');
    fireEvent.click(back);
    expect(await screen.findByText('profile-list')).toBeInTheDocument();
  });
});
