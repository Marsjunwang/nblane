import { act, fireEvent, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { renderWithProviders } from '../test/render';
import { SidecarFrame } from './SidecarFrame';

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe('SidecarFrame', () => {
  it('loads directly without a handoff token and hides the loading veil on onLoad', () => {
    renderWithProviders(
      <SidecarFrame title="Paper Library" url="http://127.0.0.1:8502/library" base="" />,
    );

    const frame = screen.getByTestId('sidecar-frame');
    expect(frame).toHaveAttribute('src', 'http://127.0.0.1:8502/library');
    // Until the frame fires onLoad, a loading veil covers it (no blank pane).
    expect(screen.getByTestId('sidecar-loading')).toBeInTheDocument();

    fireEvent.load(frame);
    expect(screen.queryByTestId('sidecar-loading')).not.toBeInTheDocument();
  });

  it('remounts the content iframe when 重新加载 is clicked', () => {
    renderWithProviders(
      <SidecarFrame title="Paper Library" url="http://127.0.0.1:8502/library" base="" />,
    );

    const before = screen.getByTestId('sidecar-frame');
    fireEvent.load(before);
    expect(screen.queryByTestId('sidecar-loading')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: '重新加载' }));

    const after = screen.getByTestId('sidecar-frame');
    // A keyed remount: the DOM node is replaced, forcing a real reload.
    expect(after).not.toBe(before);
    expect(after).toHaveAttribute('src', 'http://127.0.0.1:8502/library');
    // The loading veil is back until the new frame fires onLoad.
    expect(screen.getByTestId('sidecar-loading')).toBeInTheDocument();
  });

  it('bootstraps the session before loading content and re-bootstraps on reload', () => {
    vi.useFakeTimers();
    renderWithProviders(
      <SidecarFrame
        title="Paper Library"
        url="http://127.0.0.1:8502/library"
        base="http://127.0.0.1:8502"
        handoffToken="handoff-token-123"
      />,
    );

    // Content iframe waits for the bootstrap timer; the hidden form posts the
    // token to the sidecar /auth/session endpoint.
    expect(screen.queryByTestId('sidecar-frame')).not.toBeInTheDocument();
    expect(screen.getByTestId('sidecar-loading')).toBeInTheDocument();
    const form = document.querySelector('form');
    expect(form?.getAttribute('action')).toBe('http://127.0.0.1:8502/auth/session');

    act(() => {
      vi.advanceTimersByTime(900);
    });
    expect(screen.getByTestId('sidecar-frame')).toBeInTheDocument();

    // Reload re-runs the whole bootstrap: the content frame is pulled until
    // the head start elapses again, then comes back with a fresh load.
    fireEvent.click(screen.getByRole('button', { name: '重新加载' }));
    expect(screen.queryByTestId('sidecar-frame')).not.toBeInTheDocument();
    act(() => {
      vi.advanceTimersByTime(900);
    });
    expect(screen.getByTestId('sidecar-frame')).toBeInTheDocument();
    expect(screen.getByTestId('sidecar-loading')).toBeInTheDocument();
  });
});
