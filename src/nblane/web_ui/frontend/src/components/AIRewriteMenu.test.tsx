import { ComponentsContext } from '@blocknote/react';
import { fireEvent, render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { describe, expect, it, vi } from 'vitest';

import { AIRewriteMenu } from './AIRewriteMenu';

// Minimal stand-in for BlockNote's Generic components: items are buttons,
// labels are plain text, so tests can tell clickable actions from notes.
const Generic = {
  Menu: {
    Root: ({ children }: { children?: ReactNode }) => <div>{children}</div>,
    Trigger: ({ children }: { children?: ReactNode }) => <div>{children}</div>,
    Dropdown: ({ children }: { children?: ReactNode }) => <div role="menu">{children}</div>,
    Item: ({ children, onClick }: { children?: ReactNode; onClick?: () => void }) => (
      <button type="button" role="menuitem" onClick={onClick}>
        {children}
      </button>
    ),
    Label: ({ children }: { children?: ReactNode }) => <div data-testid="menu-label">{children}</div>,
  },
  Toolbar: {
    Button: ({ children }: { children?: ReactNode }) => <button type="button">{children}</button>,
  },
};

function renderMenu(props: Partial<Parameters<typeof AIRewriteMenu>[0]> = {}) {
  const onPick = vi.fn();
  render(
    <ComponentsContext.Provider value={{ Generic } as never}>
      <AIRewriteMenu onPick={onPick} imagesOnly={false} mixed={false} textEnabled imageEnabled {...props} />
    </ComponentsContext.Provider>,
  );
  return onPick;
}

const items = () => screen.queryAllByRole('menuitem').map((item) => item.textContent);
const labels = () => screen.queryAllByTestId('menu-label').map((label) => label.textContent);

describe('AIRewriteMenu', () => {
  it('lists the rewrite operations and picks one', () => {
    const onPick = renderMenu();
    expect(items()).toEqual(['润色', '精简', '扩写', '调整为专业语气', '翻译']);
    expect(labels()).toEqual([]);
    fireEvent.click(screen.getByRole('menuitem', { name: '翻译' }));
    expect(onPick).toHaveBeenCalledWith('translate');
  });

  it('shows the mixed-selection note as a label, not a clickable item', () => {
    renderMenu({ mixed: true });
    expect(labels()).toEqual(['仅改写文字，保留图片']);
    expect(items()).not.toContain('仅改写文字，保留图片');
  });

  it('offers no dead actions when the text service is not configured', () => {
    renderMenu({ textEnabled: false });
    expect(items()).toEqual([]);
    expect(labels()).toEqual(['未配置文字服务，AI 改写不可用']);
  });

  it('offers image editing for an image-only selection', () => {
    const onPick = renderMenu({ imagesOnly: true });
    expect(items()).toEqual(['修改图片']);
    fireEvent.click(screen.getByRole('menuitem', { name: '修改图片' }));
    expect(onPick).toHaveBeenCalledWith('image');
  });

  it('explains instead of offering image editing when no image service is configured', () => {
    renderMenu({ imagesOnly: true, imageEnabled: false });
    expect(items()).toEqual([]);
    expect(labels()).toEqual(['未配置图像服务，无法修改图片']);
  });
});
