import { Accordion, Alert, Anchor, Badge, Button, Group, List, Loader, Paper, SimpleGrid, Stack, Text } from '@mantine/core';
import { IconAdjustmentsHorizontal, IconDeviceDesktop, IconDownload, IconPin, IconRefresh } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';

import { chrome } from '../../theme';
import { SettingsCard } from './shared';

const RELEASE_ORIGIN = 'https://www.nblane.cloud';
const MANIFEST_URL = `${RELEASE_ORIGIN}/downloads/sticker/latest.json`;

type Download = { url: string; sha256: string; size: number };
type Release = {
  version: string;
  macosMinVersion: string;
  publishedAt: string;
  signing: 'ad-hoc';
  files: { arm64: Download; x64?: Download };
};

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function download(value: unknown): Download {
  if (!record(value) || typeof value.url !== 'string' || typeof value.sha256 !== 'string'
    || !/^[a-fA-F0-9]{64}$/.test(value.sha256)
    || typeof value.size !== 'number' || !Number.isSafeInteger(value.size) || value.size <= 0) {
    throw new Error('安装包信息不完整，请稍后重试。');
  }
  const url = new URL(value.url);
  if (url.origin !== RELEASE_ORIGIN || url.username || url.password || url.search || url.hash
    || !/^\/downloads\/sticker\/[a-zA-Z0-9_./-]+\.zip$/.test(url.pathname)) {
    throw new Error('安装包地址无效，请稍后重试。');
  }
  return { url: url.href, sha256: value.sha256.toLowerCase(), size: value.size };
}

function release(value: unknown): Release {
  if (!record(value) || typeof value.version !== 'string'
    || !/^\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?$/.test(value.version) || value.version.length > 80
    || typeof value.macosMinVersion !== 'string' || !/^\d{1,2}(?:\.\d{1,2}){0,2}$/.test(value.macosMinVersion)
    || typeof value.publishedAt !== 'string' || !/^\d{4}-\d{2}-\d{2}T/.test(value.publishedAt)
    || !Number.isFinite(Date.parse(value.publishedAt)) || value.signing !== 'ad-hoc' || !record(value.files)) {
    throw new Error('版本信息暂不可用，请稍后重试。');
  }
  return {
    version: value.version,
    macosMinVersion: value.macosMinVersion,
    publishedAt: value.publishedAt,
    signing: value.signing,
    files: { arm64: download(value.files.arm64), ...(value.files.x64 === undefined ? {} : { x64: download(value.files.x64) }) },
  };
}

async function fetchRelease(signal: AbortSignal): Promise<Release> {
  const controller = new AbortController();
  const abort = () => controller.abort();
  if (signal.aborted) abort();
  signal.addEventListener('abort', abort, { once: true });
  const timeout = setTimeout(abort, 10_000);
  try {
    const response = await fetch(MANIFEST_URL, { signal: controller.signal, credentials: 'omit', cache: 'no-cache', redirect: 'error' });
    if (!response.ok) throw new Error('暂时无法获取安装包，请检查网络后重试。');
    return release(await response.json());
  } finally {
    clearTimeout(timeout);
    signal.removeEventListener('abort', abort);
  }
}

const megabytes = (size: number) => `${(size / 1_000_000).toFixed(0)} MB`;

export function DesktopStickerSection() {
  const latest = useQuery({
    queryKey: ['desktop-sticker-release'],
    queryFn: ({ signal }) => fetchRelease(signal),
    staleTime: 5 * 60_000,
    retry: false,
    refetchOnWindowFocus: false,
  });
  const data = latest.data;

  return (
    <Stack gap="md">
      <SettingsCard icon={<IconDeviceDesktop size={22} color={chrome.gold} />} title="nblane 桌面贴纸" description="把正在做的事留在桌面。关闭浏览器，任务依然在身边。">
        <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="sm">
          <Paper p="md" radius="md" bg={chrome.panelBg}>
            <Group gap="xs" mb={6}><IconPin size={17} color={chrome.gold} /><Text fw={600} size="sm">始终置顶</Text></Group>
            <Text size="sm" c="dimmed">浮在其他普通应用窗口上方，切换应用时仍能看到当前任务。</Text>
          </Paper>
          <Paper p="md" radius="md" bg={chrome.panelBg}>
            <Group gap="xs" mb={6}><IconAdjustmentsHorizontal size={17} color={chrome.gold} /><Text fw={600} size="sm">随手调节透明度</Text></Group>
            <Text size="sm" c="dimmed">按桌面背景调整窗口不透明度，记住你的窗口位置和偏好。</Text>
          </Paper>
        </SimpleGrid>
        <Text size="sm" c="dimmed">置顶与透明度在安装后的贴纸里调整，并保存在这台 Mac 上。</Text>
        {latest.isPending && <Group role="status" gap="xs"><Loader size="sm" /><Text size="sm">正在获取 Mac 安装包…</Text></Group>}
        {latest.isError && (
          <Alert color="gray" title="暂时无法获取下载信息">
            <Stack gap="xs">
              <Text size="sm">请检查网络后重试；安装包就绪后会在这里显示。</Text>
              <Button w="fit-content" size="xs" variant="default" leftSection={<IconRefresh size={14} />} loading={latest.isFetching} onClick={() => void latest.refetch()}>重新获取</Button>
            </Stack>
          </Alert>
        )}
        {data && !latest.isError && (
          <Stack gap="sm">
            <Group gap="xs">
              <Badge variant="light" color="brand">v{data.version}</Badge>
              <Text size="xs" c="dimmed">macOS {data.macosMinVersion} 或更新版本 · {data.publishedAt.slice(0, 10)}</Text>
            </Group>
            <Group gap="sm">
              <Button component="a" href={data.files.arm64.url} download leftSection={<IconDownload size={17} />}>
                下载 Mac 版 · Apple 芯片
              </Button>
              {data.files.x64 && <Button component="a" href={data.files.x64.url} download variant="default" leftSection={<IconDownload size={17} />}>下载 Mac 版 · Intel</Button>}
            </Group>
            <Text size="xs" c="dimmed">Apple 芯片版 {megabytes(data.files.arm64.size)}{data.files.x64 ? ` · Intel 版 ${megabytes(data.files.x64.size)}` : ' · Intel 版暂未提供'}。在苹果菜单「关于本机」查看芯片类型。</Text>
            <Accordion variant="default">
              <Accordion.Item value="checksums">
                <Accordion.Control><Text size="xs" c="dimmed">安装包校验信息</Text></Accordion.Control>
                <Accordion.Panel>
                  <Stack gap="xs">
                    {Object.entries(data.files).map(([arch, file]) => (
                      <div key={arch}>
                        <Text size="xs" fw={600}>{arch === 'arm64' ? 'Apple 芯片' : 'Intel'} · SHA256</Text>
                        <Text size="xs" ff="monospace" style={{ overflowWrap: 'anywhere' }}>{file.sha256}</Text>
                      </div>
                    ))}
                  </Stack>
                </Accordion.Panel>
              </Accordion.Item>
            </Accordion>
          </Stack>
        )}
      </SettingsCard>
      <SettingsCard icon={<IconDownload size={22} color={chrome.gold} />} title="下载后，只需三步" description="不需要安装开发工具，也不需要自己编译。">
        <List type="ordered" size="sm" spacing="sm">
          <List.Item>双击 ZIP 解压，将 nblane Sticker 拖入「应用程序」。</List.Item>
          <List.Item>打开贴纸，填写网站地址与档案名。本站生产地址是 https://www.nblane.cloud。</List.Item>
          <List.Item>使用该网站的原有账号和密码登录。贴纸独立保存登录状态，首次需要重新登录。</List.Item>
        </List>
        <Text size="sm" c="dimmed">当前安装包尚未经过 Apple 公证。首次若提示无法验证开发者，请在「系统设置 → 隐私与安全」选择「仍要打开」。<Anchor size="sm" href="https://support.apple.com/zh-cn/102445" target="_blank" rel="noreferrer">查看 Apple 说明</Anchor></Text>
      </SettingsCard>
    </Stack>
  );
}
