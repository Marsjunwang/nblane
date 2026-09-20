import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach, vi } from 'vitest';

// Vitest globals are off, so @testing-library/react's auto-cleanup does not
// run — unmount each render explicitly between tests.
afterEach(() => {
  cleanup();
});

// jsdom does not implement matchMedia / ResizeObserver; Mantine's
// color-scheme handling and layout hooks need them.
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

window.ResizeObserver = window.ResizeObserver ?? ResizeObserverMock;

// jsdom does not implement scrollIntoView; Mantine Combobox calls it when a
// Select/MultiSelect dropdown opens.
window.HTMLElement.prototype.scrollIntoView =
  window.HTMLElement.prototype.scrollIntoView ?? vi.fn();
