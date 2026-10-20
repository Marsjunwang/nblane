import {
  Alert,
  Box,
  Button,
  Checkbox,
  CopyButton,
  Drawer,
  Group,
  Image,
  Loader,
  SegmentedControl,
  SimpleGrid,
  Stack,
  Switch,
  Text,
  TextInput,
  Textarea,
  Title,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconCopy, IconDownload, IconPhoto, IconShare, IconSparkles } from '@tabler/icons-react';
import { useEffect, useRef, useState } from 'react';

import { ApiError } from '../../api/client';
import { useRenderSocialCards, useSocialCardSettings } from '../../api/hooks';
import type { SocialCardRenderResponse, SocialCardSettings } from '../../api/types';
import { runContentJob, type ContentJobHandle } from './contentJobs';

interface SocialCopyResult {
  cover_titles: string[];
  cover_subtitles: string[];
  xhs_title: string;
  xhs_body: string;
  x_text: string;
  truncated?: boolean;
}

const THEME_OPTIONS = [
  { value: 'paper', label: '纸感' },
  { value: 'warm', label: '暖色手帐' },
  { value: 'night', label: '深色' },
];

const SIGNATURE_OPTIONS = [
  { value: 'site', label: '网站域名' },
  { value: 'custom', label: '自定义' },
  { value: 'none', label: '不显示' },
];

const END_OPTIONS = [
  { value: 'thanks', label: '致谢' },
  { value: 'thanks_url', label: '致谢 + 网址' },
  { value: 'none', label: '不要末页' },
];

/** X counts CJK characters double; 280 weighted ≈ 140 汉字. */
export function xWeightedLength(text: string): number {
  let total = 0;
  for (const ch of text) total += /[ᄀ-￿]/.test(ch) && !/[ -⁯]/.test(ch) ? 2 : 1;
  return total;
}

function errorText(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

/**
 * Share a post on Xiaohongshu / X: pick a theme, write the cover text, render
 * 3:4 cards on the server, then share the images (phone) or download a zip.
 * Nothing is posted automatically; the owner publishes by hand.
 */
export function SocialShareDrawer({
  profile,
  slug,
  title,
  body,
  opened,
  onClose,
  aiText,
  mobile,
}: {
  profile: string;
  slug: string;
  title: string;
  body: string;
  opened: boolean;
  onClose: () => void;
  aiText: boolean;
  mobile: boolean;
}) {
  const info = useSocialCardSettings(profile, slug, opened);
  const render = useRenderSocialCards(profile);
  const [settings, setSettings] = useState<SocialCardSettings | null>(null);
  const [result, setResult] = useState<SocialCardRenderResponse | null>(null);
  const [allowDraft, setAllowDraft] = useState(false);
  const [suggesting, setSuggesting] = useState(false);
  const [suggestions, setSuggestions] = useState<SocialCopyResult | null>(null);
  const [sharing, setSharing] = useState(false);
  const suggestJob = useRef<ContentJobHandle<SocialCopyResult> | null>(null);

  // A late result must not land after the drawer closed or unmounted.
  useEffect(() => () => suggestJob.current?.cancel(), []);

  useEffect(() => {
    if (opened && info.data && !settings) setSettings(info.data.settings);
  }, [info.data, opened, settings]);

  useEffect(() => {
    if (!opened) {
      suggestJob.current?.cancel();
      suggestJob.current = null;
      setSuggesting(false);
      setSettings(null);
      setResult(null);
      setSuggestions(null);
      setAllowDraft(false);
    }
  }, [opened]);

  const set = (patch: Partial<SocialCardSettings>) => setSettings((current) => (current ? { ...current, ...patch } : current));
  const published = info.data?.published ?? false;
  const maxImages = info.data?.max_images ?? 18;

  const generate = () => {
    if (!settings) return;
    render.mutate(
      { slug, settings, allow_draft: allowDraft },
      {
        onSuccess: (data) => {
          setResult(data);
          setSettings(data.settings);
        },
        onError: (error) =>
          notifications.show({ color: 'red', title: '生成卡片失败', message: errorText(error) }),
      },
    );
  };

  const suggest = () => {
    suggestJob.current?.cancel();
    setSuggesting(true);
    const job = runContentJob<SocialCopyResult>(profile, 'content-social', { title, body });
    suggestJob.current = job;
    job.result
      .then((data) => {
        if (suggestJob.current !== job) return;
        setSuggestions(data);
        // Fill empty fields only; the owner's own text is never overwritten.
        setSettings((current) =>
          current
            ? {
                ...current,
                cover_title: current.cover_title || data.cover_titles[0] || '',
                cover_subtitle: current.cover_subtitle || data.cover_subtitles[0] || '',
                xhs_title: current.xhs_title || data.xhs_title,
                xhs_body: current.xhs_body || data.xhs_body,
                x_text: current.x_text || data.x_text,
              }
            : current,
        );
      })
      .catch((error: unknown) => {
        if (suggestJob.current === job) notifications.show({ color: 'red', title: 'AI 文案失败', message: errorText(error) });
      })
      .finally(() => {
        if (suggestJob.current === job) {
          suggestJob.current = null;
          setSuggesting(false);
        }
      });
  };

  const shareImages = async () => {
    if (!result) return;
    setSharing(true);
    try {
      const files = await Promise.all(
        (result.images ?? []).map(async (url, index) => {
          const response = await fetch(url, { credentials: 'include' });
          if (!response.ok) throw new ApiError(response.status, '卡片已过期，请重新生成。');
          return new File([await response.blob()], `card-${String(index + 1).padStart(2, '0')}.png`, { type: 'image/png' });
        }),
      );
      if (navigator.canShare?.({ files })) {
        await navigator.share({ files, title: settings?.xhs_title || title });
      } else {
        window.location.href = result.pack_url;
      }
    } catch (error) {
      // AbortError = the owner closed the share sheet.
      if (!(error instanceof DOMException && error.name === 'AbortError')) {
        notifications.show({ color: 'red', title: '分享失败', message: errorText(error) });
      }
    } finally {
      setSharing(false);
    }
  };

  const xLength = xWeightedLength(
    settings?.end_card === 'thanks_url' && info.data?.post_url
      ? `${settings.x_text}\n${info.data.post_url}`
      : settings?.x_text ?? '',
  );

  return (
    <Drawer
      opened={opened}
      onClose={onClose}
      position="right"
      size={mobile ? '100%' : 760}
      title={<Title order={4}>发到小红书 / X</Title>}
      data-testid="social-share-drawer"
    >
      {!settings ? (
        <Group justify="center" py="xl">
          <Loader />
        </Group>
      ) : (
        <Stack gap="md">
          {!published && (
            <Alert color="yellow" variant="light">
              这篇还是草稿。卡片建议在发布后再导出。
              <Checkbox mt="xs" label="仍然导出草稿" checked={allowDraft} onChange={(e) => setAllowDraft(e.currentTarget.checked)} />
            </Alert>
          )}

          <Box>
            <Text size="sm" fw={500} mb={6}>
              卡片风格
            </Text>
            <SegmentedControl fullWidth data={THEME_OPTIONS} value={settings.theme} onChange={(value) => set({ theme: value as SocialCardSettings['theme'] })} />
          </Box>

          <Group justify="space-between" align="center">
            <Text size="sm" fw={500}>
              封面
            </Text>
            {aiText && (
              <Button size="compact-sm" variant="light" leftSection={<IconSparkles size={14} />} loading={suggesting} onClick={suggest}>
                AI 写标题和文案
              </Button>
            )}
          </Group>
          <Textarea
            label="封面大标题"
            description="留空用文章标题；回车换行"
            autosize
            minRows={2}
            maxLength={80}
            value={settings.cover_title}
            placeholder={title}
            onChange={(e) => set({ cover_title: e.currentTarget.value })}
          />
          {suggestions?.truncated && (
            <Text size="xs" c="dimmed">
              文章较长，文案依据提纲、开头和结尾生成。
            </Text>
          )}
          {suggestions && suggestions.cover_titles.length > 0 && (
            <Group gap={6}>
              {suggestions.cover_titles.map((item) => (
                <Button key={item} size="compact-xs" variant="default" onClick={() => set({ cover_title: item })}>
                  {item.replace(/\n/g, ' / ')}
                </Button>
              ))}
            </Group>
          )}
          <Textarea
            label="封面引文"
            autosize
            minRows={1}
            maxLength={200}
            value={settings.cover_subtitle}
            onChange={(e) => set({ cover_subtitle: e.currentTarget.value })}
          />
          {suggestions && suggestions.cover_subtitles.length > 0 && (
            <Group gap={6}>
              {suggestions.cover_subtitles.map((item) => (
                <Button key={item} size="compact-xs" variant="default" onClick={() => set({ cover_subtitle: item })}>
                  {item}
                </Button>
              ))}
            </Group>
          )}
          <SimpleGrid cols={mobile ? 1 : 2}>
            <TextInput label="小标签" placeholder="例如：随笔 · 2026.10" maxLength={40} value={settings.kicker} onChange={(e) => set({ kicker: e.currentTarget.value })} />
            <Switch
              mt={mobile ? 0 : 28}
              label="封面放文章配图"
              disabled={!info.data?.has_cover}
              checked={settings.cover_image && Boolean(info.data?.has_cover)}
              onChange={(e) => set({ cover_image: e.currentTarget.checked })}
            />
          </SimpleGrid>

          <Box>
            <Text size="sm" fw={500} mb={6}>
              每页底部署名
            </Text>
            <SegmentedControl fullWidth data={SIGNATURE_OPTIONS} value={settings.signature} onChange={(value) => set({ signature: value as SocialCardSettings['signature'] })} />
            {settings.signature === 'custom' && (
              <TextInput mt="xs" placeholder="例如小红书昵称" maxLength={60} value={settings.signature_text} onChange={(e) => set({ signature_text: e.currentTarget.value })} />
            )}
          </Box>
          <Box>
            <Text size="sm" fw={500} mb={6}>
              末页
            </Text>
            <SegmentedControl fullWidth data={END_OPTIONS} value={settings.end_card} onChange={(value) => set({ end_card: value as SocialCardSettings['end_card'] })} />
            {(settings.end_card === 'thanks_url' || settings.signature === 'site') && (
              <TextInput mt="xs" label="网站地址" placeholder="例如 yourname.example.com" maxLength={200} value={settings.site_url} onChange={(e) => set({ site_url: e.currentTarget.value })} />
            )}
            <Text size="xs" c="dimmed" mt={4}>
              不放网址、署名不显示，别人就不容易从这些图找到你的网站。
            </Text>
          </Box>

          <Group>
            <Button leftSection={<IconPhoto size={16} />} loading={render.isPending} disabled={!published && !allowDraft} onClick={generate} data-testid="social-render">
              {result ? '重新生成卡片' : '生成卡片'}
            </Button>
          </Group>

          {result && (
            <Stack gap="xs">
              <Text size="sm" c="dimmed">
                共 {result.count} 张（小红书最多 {maxImages} 张）
              </Text>
              {(result.warnings ?? []).map((warning) => (
                <Alert key={warning} color="yellow" variant="light">
                  {warning}
                </Alert>
              ))}
              <SimpleGrid cols={mobile ? 3 : 4} spacing="xs" data-testid="social-card-grid">
                {(result.images ?? []).map((url, index) => (
                  <a key={url} href={url} target="_blank" rel="noreferrer">
                    <Image src={url} alt={`第 ${index + 1} 张卡片`} radius="sm" />
                  </a>
                ))}
              </SimpleGrid>
              <Group>
                <Button leftSection={<IconShare size={16} />} loading={sharing} onClick={() => void shareImages()}>
                  {mobile ? '分享 / 存到相册' : '分享图片'}
                </Button>
                <Button component="a" href={result.pack_url} variant="default" leftSection={<IconDownload size={16} />}>
                  下载 zip（含文案）
                </Button>
              </Group>
            </Stack>
          )}

          <Title order={5} mt="sm">
            发帖文案
          </Title>
          <TextInput
            label="小红书标题"
            maxLength={40}
            value={settings.xhs_title}
            onChange={(e) => set({ xhs_title: e.currentTarget.value })}
            description={`${[...settings.xhs_title].length} / 20`}
            error={[...settings.xhs_title].length > 20 ? '小红书标题最多 20 字' : undefined}
          />
          <Textarea
            label="小红书正文"
            autosize
            minRows={4}
            maxLength={2000}
            value={settings.xhs_body}
            onChange={(e) => set({ xhs_body: e.currentTarget.value })}
            description={`${[...settings.xhs_body].length} / 1000`}
            error={[...settings.xhs_body].length > 1000 ? '小红书正文最多 1000 字' : undefined}
          />
          <CopyButton value={`${settings.xhs_title}\n\n${settings.xhs_body}`.trim()}>
            {({ copied, copy }) => (
              <Button size="compact-sm" variant="light" leftSection={<IconCopy size={14} />} onClick={copy} w="fit-content">
                {copied ? '已复制' : '复制小红书文案'}
              </Button>
            )}
          </CopyButton>
          <Textarea
            label="X 推文"
            autosize
            minRows={2}
            maxLength={1000}
            value={settings.x_text}
            onChange={(e) => set({ x_text: e.currentTarget.value })}
            description={`${xLength} / 280（汉字算 2）${settings.end_card === 'thanks_url' && info.data?.post_url ? '，含文章链接' : ''}`}
            error={xLength > 280 ? '超过 X 单条推文上限' : undefined}
          />
          <CopyButton
            value={
              settings.end_card === 'thanks_url' && info.data?.post_url
                ? `${settings.x_text}\n${info.data.post_url}`.trim()
                : settings.x_text
            }
          >
            {({ copied, copy }) => (
              <Button size="compact-sm" variant="light" leftSection={<IconCopy size={14} />} onClick={copy} w="fit-content">
                {copied ? '已复制' : '复制 X 文案'}
              </Button>
            )}
          </CopyButton>
          <Text size="xs" c="dimmed">
            文案在点「生成卡片」时一起保存。X 建议发文字 + 封面图{settings.end_card === 'thanks_url' ? ' + 链接' : ''}。
          </Text>
        </Stack>
      )}
    </Drawer>
  );
}
