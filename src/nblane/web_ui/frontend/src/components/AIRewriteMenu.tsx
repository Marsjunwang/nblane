import { useComponentsContext } from '@blocknote/react';
import { IconSparkles } from '@tabler/icons-react';

import { AI_REWRITE_MENU } from './rewriteOperations';

/** "AI" dropdown appended to BlockNote's formatting toolbar. */
export function AIRewriteMenu({ onPick, imagesOnly, mixed, textEnabled, imageEnabled }: { onPick: (operation: string) => void; imagesOnly: boolean; mixed: boolean; textEnabled: boolean; imageEnabled: boolean }) {
  const Components = useComponentsContext();
  if (!Components) return null;
  const { Menu, Toolbar } = Components.Generic;
  return (
    <Menu.Root position="bottom-start">
      <Menu.Trigger>
        <Toolbar.Button
          mainTooltip={imagesOnly ? "AI 修改图片" : "AI 改写选中文字"}
          icon={<IconSparkles size={16} />}
          label="AI"
          className="nb-ai-toolbar-button"
        >
          AI
        </Toolbar.Button>
      </Menu.Trigger>
      <Menu.Dropdown className="bn-menu-dropdown">
        {/* Notes are Menu.Label (not clickable); actions that cannot run are
            not offered at all instead of silently doing nothing. */}
        {imagesOnly ? (
          imageEnabled ? (
            <Menu.Item onClick={() => onPick('image')}>修改图片</Menu.Item>
          ) : (
            <Menu.Label>未配置图像服务，无法修改图片</Menu.Label>
          )
        ) : !textEnabled ? (
          <Menu.Label>未配置文字服务，AI 改写不可用</Menu.Label>
        ) : (
          <>
            {mixed && <Menu.Label>仅改写文字，保留图片</Menu.Label>}
            {AI_REWRITE_MENU.map((item) => (
              <Menu.Item key={item.operation} onClick={() => onPick(item.operation)}>
                {item.label}
              </Menu.Item>
            ))}
          </>
        )}
      </Menu.Dropdown>
    </Menu.Root>
  );
}
