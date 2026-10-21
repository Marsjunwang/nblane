import { ActionIcon, Alert, Box, Button, Card, Center, Code, Group, Loader, Stack, Text, Textarea, Title, Tooltip } from '@mantine/core';
import { useLocalStorage, useMediaQuery } from '@mantine/hooks';
import { notifications } from '@mantine/notifications';
import { IconKeyboard, IconRefresh, IconSend, IconSettings, IconTerminal, IconTerminal2 } from '@tabler/icons-react';
import { useEffect, useState, type MouseEvent } from 'react';
import { Link } from 'react-router-dom';

import { useWorkshopInput, useWorkshopKeys, useWorkshopStatus } from '../api/hooks';
import { SidecarFrame } from '../components/SidecarFrame';

/**
 * 车间 — the remote workshop terminal: ttyd (tmux session "workshop") embedded
 * through the authenticated same-origin /terminal/ proxy, admin only.
 *
 * Phones lack Esc/Ctrl/arrow keys and xterm.js handles CJK IMEs poorly, so a
 * key bar and an input box sit under the terminal: keys and text go to the
 * active tmux pane server-side (tmux send-keys / paste-buffer), independent of
 * ttyd's frontend. The bar is on by default for touch devices, keeps Enter and
 * the arrow keys always visible, and the input box sends on Enter (Shift+Enter
 * inserts a newline) so the phone IME works end to end. History is scrolled by
 * swiping inside the terminal (tmux mouse off + no alternate screen); ⇊ snaps
 * back to the latest output, as does sending any key or text.
 */

// Key bar groups: `main` and `nav` stay visible at all times — Enter and the
// arrow keys must be reachable on a phone without horizontal scrolling. The
// rarer `extra` keys sit behind the 更多 toggle. Terminal history itself is
// scrolled by swiping inside the terminal (native xterm scroll), so PgUp/PgDn
// are only in-app paging keys (less / man / vim) and live in `extra`.
const KEY_BAR: Array<{ key: string; label: string; hint: string; group: 'main' | 'nav' | 'extra' }> = [
  { key: 'esc', label: 'Esc', hint: '中断 / 关闭菜单', group: 'main' },
  { key: 'ctrl_c', label: '^C', hint: 'Ctrl-C', group: 'main' },
  { key: 'shift_tab', label: '⇧Tab', hint: '切换模式（Claude Code）', group: 'main' },
  { key: 'tab', label: 'Tab', hint: 'Tab 补全', group: 'main' },
  { key: 'enter', label: '⏎', hint: '回车', group: 'main' },
  { key: 'left', label: '←', hint: '左', group: 'nav' },
  { key: 'up', label: '↑', hint: '上', group: 'nav' },
  { key: 'down', label: '↓', hint: '下', group: 'nav' },
  { key: 'right', label: '→', hint: '右', group: 'nav' },
  { key: 'esc2', label: 'Esc×2', hint: '回退到上一条消息（Claude Code）', group: 'extra' },
  { key: 'ctrl_o', label: '^O', hint: 'Ctrl-O：展开完整记录（Claude Code）', group: 'extra' },
  { key: 'ctrl_r', label: '^R', hint: 'Ctrl-R：搜索历史', group: 'extra' },
  { key: 'ctrl_t', label: '^T', hint: 'Ctrl-T：任务列表（Claude Code）', group: 'extra' },
  { key: 'ctrl_l', label: '^L', hint: 'Ctrl-L：清屏 / 重绘', group: 'extra' },
  { key: 'ctrl_d', label: '^D', hint: 'Ctrl-D：退出', group: 'extra' },
  { key: 'ctrl_z', label: '^Z', hint: 'Ctrl-Z：挂起', group: 'extra' },
  { key: 'page_up', label: 'PgUp', hint: '程序内上翻页（less / man）', group: 'extra' },
  { key: 'page_down', label: 'PgDn', hint: '程序内下翻页（less / man）', group: 'extra' },
];

// Keep focus where it is (the terminal or the input box) so tapping a key
// does not close the phone's soft keyboard.
const keepFocus = (event: MouseEvent) => event.preventDefault();

/** Visible viewport height: shrinks when the phone keyboard opens. */
function useVisualViewportHeight(): number {
  const read = () => Math.round(window.visualViewport?.height ?? window.innerHeight);
  const [height, setHeight] = useState(read);
  useEffect(() => {
    const viewport = window.visualViewport;
    const update = () => setHeight(read());
    viewport?.addEventListener('resize', update);
    window.addEventListener('resize', update);
    return () => {
      viewport?.removeEventListener('resize', update);
      window.removeEventListener('resize', update);
    };
  }, []);
  return height;
}

export function terminalUrl(url: string, fontSize: number): string {
  try {
    const parsed = new URL(url, window.location.href);
    parsed.searchParams.set('fontSize', String(fontSize));
    return /^https?:\/\//.test(url) ? parsed.toString() : `${parsed.pathname}${parsed.search}`;
  } catch {
    return url;
  }
}

/** Snap the embedded xterm viewport to the latest output (same-origin iframe). */
function scrollTerminalToBottom() {
  try {
    const frame = document.querySelector<HTMLIFrameElement>('[data-testid="sidecar-frame"]');
    const viewport = frame?.contentDocument?.querySelector('.xterm-viewport');
    if (viewport) viewport.scrollTop = viewport.scrollHeight;
  } catch {
    // Terminal not ready or cross-origin: nothing to scroll.
  }
}

function KeyBar() {
  const send = useWorkshopKeys();
  const [pressed, setPressed] = useState<string | null>(null);
  const [showExtra, setShowExtra] = useState(false);
  const press = (key: string) => {
    // Keys go server-side with no local echo, so flash a pressed state (and a
    // short vibration on phones) — otherwise a tap has no visible effect.
    setPressed(key);
    window.setTimeout(() => setPressed((current) => (current === key ? null : current)), 180);
    navigator.vibrate?.(10);
    // Typing snaps a real terminal to the prompt; mirror that here.
    send.mutate([key], {
      onSuccess: scrollTerminalToBottom,
      onError: (error) => notifications.show({ title: '按键发送失败', message: error.message, color: 'red' }),
    });
  };
  const renderKey = (item: (typeof KEY_BAR)[number]) => (
    <Tooltip key={item.key} label={item.hint} openDelay={400} events={{ hover: true, focus: false, touch: true }}>
      <Button
        size="compact-md"
        variant={pressed === item.key ? 'light' : 'default'}
        data-pressed={pressed === item.key || undefined}
        ff="monospace"
        aria-label={item.hint}
        onMouseDown={keepFocus}
        onClick={() => press(item.key)}
        style={{ flexShrink: 0, minWidth: 48, minHeight: 44 }}
      >
        {item.label}
      </Button>
    </Tooltip>
  );
  return (
    <Stack gap={6} role="toolbar" aria-label="终端快捷键">
      <Group gap={6} wrap="wrap">
        {KEY_BAR.filter((item) => item.group === 'main').map(renderKey)}
        <Button
          size="compact-md"
          variant="subtle"
          aria-expanded={showExtra}
          aria-label={showExtra ? '收起不常用按键' : '显示更多按键'}
          onMouseDown={keepFocus}
          onClick={() => setShowExtra((value) => !value)}
          style={{ flexShrink: 0, minHeight: 44 }}
        >
          {showExtra ? '收起' : '更多'}
        </Button>
      </Group>
      <Group gap={6} wrap="wrap">
        {KEY_BAR.filter((item) => item.group === 'nav').map(renderKey)}
        <Tooltip label="滚动到最新输出" openDelay={400} events={{ hover: true, focus: false, touch: true }}>
          <Button
            size="compact-md"
            variant="default"
            ff="monospace"
            aria-label="滚动到最新输出"
            onMouseDown={keepFocus}
            onClick={scrollTerminalToBottom}
            style={{ flexShrink: 0, minWidth: 48, minHeight: 44 }}
          >
            ⇊
          </Button>
        </Tooltip>
      </Group>
      {showExtra && (
        <Group gap={6} wrap="wrap">
          {KEY_BAR.filter((item) => item.group === 'extra').map(renderKey)}
        </Group>
      )}
    </Stack>
  );
}

function InputBox() {
  const send = useWorkshopInput();
  const [text, setText] = useState('');
  const submit = (withEnter: boolean) =>
    send.mutate(
      { text, submit: withEnter },
      {
        onSuccess: () => {
          setText('');
          scrollTerminalToBottom();
        },
        onError: (error) => notifications.show({ title: '发送失败', message: error.message, color: 'red' }),
      },
    );
  return (
    <Group gap={6} wrap="nowrap" align="flex-end">
      <Textarea
        aria-label="发送到终端的文字"
        placeholder="回车发送，Shift+回车换行"
        autosize
        minRows={1}
        maxRows={4}
        value={text}
        onChange={(event) => setText(event.currentTarget.value)}
        onKeyDown={(event) => {
          // Enter sends. Composition Enter (confirming an IME candidate) and
          // Shift+Enter (explicit newline) are left to the default behavior.
          if (event.key !== 'Enter' || event.nativeEvent.isComposing || event.shiftKey) return;
          event.preventDefault();
          submit(true);
        }}
        style={{ flex: 1 }}
      />
      <Tooltip label="只输入，不回车" events={{ hover: true, focus: false, touch: true }}>
        <Button
          size="sm"
          variant="default"
          disabled={!text}
          loading={send.isPending && !send.variables?.submit}
          onMouseDown={keepFocus}
          onClick={() => submit(false)}
          style={{ minHeight: 44 }}
        >
          输入
        </Button>
      </Tooltip>
      <Button
        size="sm"
        leftSection={<IconSend size={14} />}
        loading={send.isPending && send.variables?.submit}
        onMouseDown={keepFocus}
        onClick={() => submit(true)}
        style={{ minHeight: 44 }}
      >
        发送
      </Button>
    </Group>
  );
}

export function WorkshopPage() {
  const status = useWorkshopStatus();
  const touch = useMediaQuery('(pointer: coarse)') ?? false;
  const [barPref, setBarPref] = useLocalStorage<'auto' | 'on' | 'off'>({ key: 'nblane.workshop.keybar', defaultValue: 'auto' });
  const [reloadSignal, setReloadSignal] = useState(0);
  const viewportHeight = useVisualViewportHeight();

  if (status.isPending) {
    return (
      <Center py="xl">
        <Loader />
      </Center>
    );
  }
  if (status.isError) {
    return (
      <Alert color="red" title="加载失败">
        {status.error.message}
      </Alert>
    );
  }

  const data = status.data;

  if (!data.admin) {
    return (
      <Alert color="gray" title="车间终端仅管理员可用" icon={<IconTerminal size={18} />}>
        车间是服务器上的完整终端，只对管理员账号开放。
      </Alert>
    );
  }

  if (!data.reachable) {
    return (
      <Center py="xl">
        <Card withBorder radius="md" padding="xl" maw={560}>
          <Stack align="center" gap="sm">
            <IconTerminal size={40} stroke={1.5} />
            <Title order={3}>车间终端未运行</Title>
            <Text size="sm" c="dimmed" ta="center">
              网页终端由 ttyd + tmux 提供。在「设置 → 车间终端」里一键安装或启动；也可以在服务器上运行：
            </Text>
            <Code block w="100%">systemctl --user start nblane-workshop.service</Code>
            <Group gap="xs">
              <Button component={Link} to="/settings/workshop" size="compact-sm" leftSection={<IconSettings size={14} />}>
                打开车间设置
              </Button>
              <Button variant="light" size="compact-sm" loading={status.isRefetching} onClick={() => status.refetch()}>
                重新检测
              </Button>
            </Group>
          </Stack>
        </Card>
      </Center>
    );
  }

  const showBar = barPref === 'on' || (barPref === 'auto' && touch);
  const fontSize = touch ? data.font_size_mobile : data.font_size_desktop;
  // 56px app header + the AppShell's vertical padding.
  const height = `calc(${viewportHeight}px - 56px - 2 * var(--mantine-spacing-md))`;

  return (
    <Stack gap={6} style={{ height }}>
      <Group justify="space-between" wrap="nowrap">
        <Group gap="xs" wrap="nowrap">
          <IconTerminal2 size={20} />
          <Title order={3}>车间</Title>
          <Text size="xs" c="dimmed" visibleFrom="sm">tmux 会话 workshop：锁屏、断线、关页面后重进，内容都还在。</Text>
        </Group>
        <Group gap={4} wrap="nowrap">
          <Tooltip label={showBar ? '隐藏快捷输入' : '显示快捷输入'}>
            <ActionIcon size="lg" variant={showBar ? 'light' : 'subtle'} aria-label="快捷输入" aria-pressed={showBar} onClick={() => setBarPref(showBar ? 'off' : 'on')}>
              <IconKeyboard size={18} />
            </ActionIcon>
          </Tooltip>
          <Tooltip label="重新连接">
            <ActionIcon size="lg" variant="subtle" aria-label="重新连接" onClick={() => setReloadSignal((value) => value + 1)}>
              <IconRefresh size={18} />
            </ActionIcon>
          </Tooltip>
          <Tooltip label="车间设置">
            <ActionIcon size="lg" component={Link} to="/settings/workshop" variant="subtle" aria-label="车间设置">
              <IconSettings size={18} />
            </ActionIcon>
          </Tooltip>
        </Group>
      </Group>
      <Box style={{ position: 'relative', flex: 1, minHeight: 120 }}>
        <Box style={{ position: 'absolute', inset: 0 }}>
          <SidecarFrame title="车间终端" url={terminalUrl(data.url, fontSize)} base="" height="100%" hideReloadButton reloadSignal={reloadSignal} />
        </Box>
      </Box>
      {showBar && (
        <Stack gap={6}>
          <KeyBar />
          <InputBox />
        </Stack>
      )}
    </Stack>
  );
}
