import { ActionIcon, Tooltip } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconPictureInPictureOn } from '@tabler/icons-react';

/** Size of the always-on-top window (CSS px). */
export const MINI_WINDOW_SIZE = { width: 340, height: 460 };

interface DocumentPictureInPicture {
  requestWindow(options: { width: number; height: number }): Promise<Window>;
}

function pipApi(): DocumentPictureInPicture | undefined {
  return (window as unknown as { documentPictureInPicture?: DocumentPictureInPicture }).documentPictureInPicture;
}

export function miniPath(profile: string): string {
  return `/p/${encodeURIComponent(profile)}/mini`;
}

/**
 * Open the compact 「小窗」 view. Chrome / Edge 116+ get a real always-on-top
 * window (Document Picture-in-Picture) holding the mini page in a same-origin
 * iframe, so it shares the login cookie. Other browsers fall back to a small
 * popup, which the OS will not keep on top.
 */
export async function openMiniWindow(profile: string): Promise<'pip' | 'popup' | 'blocked'> {
  const url = miniPath(profile);
  const api = pipApi();
  if (api) {
    try {
      const pip = await api.requestWindow(MINI_WINDOW_SIZE);
      pip.document.title = 'nblane 小窗';
      pip.document.body.style.margin = '0';
      pip.document.body.style.background = '#1a1b1e';
      const frame = pip.document.createElement('iframe');
      // The PiP document is about:blank; resolve against the app origin.
      frame.src = new URL(url, window.location.origin).href;
      frame.title = 'nblane 小窗';
      frame.style.cssText = 'border:0;width:100vw;height:100vh;display:block';
      pip.document.body.append(frame);
      return 'pip';
    } catch {
      // Fall through to a popup (e.g. requestWindow rejected).
    }
  }
  const popup = window.open(
    url,
    'nblane-mini',
    `popup=yes,width=${MINI_WINDOW_SIZE.width},height=${MINI_WINDOW_SIZE.height}`,
  );
  return popup ? 'popup' : 'blocked';
}

export function MiniWindowButton({ profile }: { profile: string }) {
  const open = async () => {
    const outcome = await openMiniWindow(profile);
    if (outcome === 'popup') {
      notifications.show({
        color: 'yellow',
        title: '已用普通小窗打开',
        message: '当前浏览器不支持置顶小窗。用 Chrome 或 Edge 可以让它一直浮在最上层。',
      });
    } else if (outcome === 'blocked') {
      notifications.show({ color: 'red', title: '小窗被拦截', message: '请允许本站弹出窗口后再试。' });
    }
  };
  return (
    <Tooltip label="小窗（置顶显示今日任务和日课）" withArrow>
      <ActionIcon variant="subtle" aria-label="打开小窗" onClick={() => void open()} data-testid="mini-window-button">
        <IconPictureInPictureOn size={18} />
      </ActionIcon>
    </Tooltip>
  );
}
