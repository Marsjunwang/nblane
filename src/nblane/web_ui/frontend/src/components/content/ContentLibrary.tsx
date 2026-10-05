import {
  Alert,
  Badge,
  Box,
  Button,
  Center,
  Group,
  Image,
  Loader,
  Modal,
  SegmentedControl,
  Stack,
  Switch,
  Table,
  Text,
  TextInput,
  Title,
} from '@mantine/core';
import { useLocalStorage } from '@mantine/hooks';
import { IconBook2, IconPhoto, IconPlus, IconRocket, IconSearch } from '@tabler/icons-react';
import { useQueryClient } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { contentMediaUrl, useContentWorkspace, useCreateContentPost } from '../../api/hooks';
import type { StudioPost } from '../../api/types';
import { STATUS_COLORS, STATUS_LABELS, contentEditorPath } from './contentDraft';

type SortKey = 'date' | 'title';

// Test/automation fixtures share the dev profile; hide them by default so
// the library reads like the writer's own list.
const FIXTURE_RE = /^(e2e|spa-e2e|browser|浏览器验收|内容工作台验收|渲染验收)/i;

function isFixture(post: StudioPost): boolean {
  return FIXTURE_RE.test(post.slug.replace(/^\d{4}-\d{2}-\d{2}-/, '')) || FIXTURE_RE.test(post.title);
}

export function ContentLibrary({ profile }: { profile: string }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const content = useContentWorkspace(profile);
  const create = useCreateContentPost(profile);
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState('');
  const [sort, setSort] = useState<SortKey>('date');
  const [showFixtures, setShowFixtures] = useLocalStorage({ key: 'nblane.content.showFixtures', defaultValue: false });
  const [createOpen, setCreateOpen] = useState(false);
  const [newTitle, setNewTitle] = useState('');

  const posts = useMemo(() => content.data?.data.posts ?? [], [content.data]);
  const fixtureCount = useMemo(() => posts.filter(isFixture).length, [posts]);
  const visible = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const rows = posts.filter(
      (post) =>
        (showFixtures || !isFixture(post)) &&
        (!status || post.status === status) &&
        (!needle ||
          `${post.title} ${post.slug} ${post.summary} ${(post.tags ?? []).join(' ')}`.toLowerCase().includes(needle)),
    );
    if (sort === 'title') rows.sort((a, b) => (a.title || a.slug).localeCompare(b.title || b.slug, 'zh'));
    return rows;
  }, [posts, query, showFixtures, sort, status]);

  const counted = posts.filter((post) => showFixtures || !isFixture(post));

  const createPost = () => {
    const title = newTitle.trim();
    if (!title) return;
    create.mutate(
      // No If-Match: creating never overwrites (the core picks a free slug).
      { body: { title, summary: '', tags: [], body: '' }, etag: '' },
      {
        onSuccess: (result) => {
          queryClient.setQueryData(['profiles', profile, 'content', 'post', result.post.slug], result);
          navigate(contentEditorPath(profile, result.post.slug), { state: { focusBody: true } });
        },
      },
    );
  };

  if (content.isPending) {
    return (
      <Center py="xl">
        <Loader />
      </Center>
    );
  }
  if (content.isError) {
    return (
      <Alert color="red" title="内容工作台加载失败">
        {content.error.message}
      </Alert>
    );
  }

  return (
    <Stack gap="lg" data-testid="content-workspace">
      <Group justify="space-between" align="flex-end" wrap="wrap">
        <div>
          <Group gap="xs">
            <IconBook2 size={24} />
            <Title order={2}>内容工作台</Title>
          </Group>
          <Text size="sm" c="dimmed" mt={4}>
            {counted.length} 篇文章 · 写作、检查并发布博客；发布到网站在公开站点完成。
          </Text>
        </div>
        <Group gap="xs">
          <Button
            component={Link}
            to={`/p/${encodeURIComponent(profile)}/public-build`}
            variant="default"
            leftSection={<IconRocket size={15} />}
          >
            公开站点
          </Button>
          <Button leftSection={<IconPlus size={15} />} onClick={() => setCreateOpen(true)} data-testid="content-create">
            新建文章
          </Button>
        </Group>
      </Group>

      <Group gap="sm" wrap="wrap">
        <TextInput
          placeholder="搜索标题、摘要、标签"
          aria-label="搜索文章"
          leftSection={<IconSearch size={15} />}
          value={query}
          onChange={(event) => setQuery(event.currentTarget.value)}
          style={{ flex: '1 1 280px', maxWidth: 420 }}
        />
        <SegmentedControl
          value={status}
          onChange={setStatus}
          data={[
            { value: '', label: `全部 ${counted.length}` },
            ...Object.entries(STATUS_LABELS).map(([value, label]) => ({
              value,
              label: `${label} ${counted.filter((post) => post.status === value).length}`,
            })),
          ]}
        />
        <SegmentedControl
          value={sort}
          onChange={(value) => setSort(value as SortKey)}
          data={[
            { value: 'date', label: '按日期' },
            { value: 'title', label: '按标题' },
          ]}
        />
        {fixtureCount > 0 && (
          <Switch
            size="xs"
            label={`显示测试数据（${fixtureCount}）`}
            checked={showFixtures}
            onChange={(event) => setShowFixtures(event.currentTarget.checked)}
          />
        )}
      </Group>

      {visible.length ? (
        <Table highlightOnHover verticalSpacing="sm" data-testid="content-post-table">
          <Table.Thead>
            <Table.Tr>
              <Table.Th w={72} />
              <Table.Th>标题</Table.Th>
              <Table.Th w={110}>状态</Table.Th>
              <Table.Th w={130}>日期</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {visible.map((post) => (
              <Table.Tr
                key={post.slug}
                data-testid="content-post-item"
                style={{ cursor: 'pointer' }}
                onClick={() => navigate(contentEditorPath(profile, post.slug))}
              >
                <Table.Td>
                  {post.cover ? (
                    <Image src={contentMediaUrl(profile, post.cover)} w={56} h={40} radius="sm" fit="cover" alt="" />
                  ) : (
                    <Center w={56} h={40} bg="dark.5" style={{ borderRadius: 4 }}>
                      <IconPhoto size={16} opacity={0.35} />
                    </Center>
                  )}
                </Table.Td>
                <Table.Td>
                  <Link
                    to={contentEditorPath(profile, post.slug)}
                    onClick={(event) => event.stopPropagation()}
                    style={{ color: 'inherit', textDecoration: 'none' }}
                  >
                    <Text fw={600} lineClamp={1}>
                      {post.title || post.slug}
                    </Text>
                  </Link>
                  <Text size="xs" c="dimmed" lineClamp={1} mt={2}>
                    {post.summary || '（无摘要）'}
                  </Text>
                  {!!post.tags?.length && (
                    <Group gap={4} mt={4}>
                      {post.tags.slice(0, 4).map((tag) => (
                        <Badge key={tag} size="xs" variant="outline" color="gray">
                          {tag}
                        </Badge>
                      ))}
                    </Group>
                  )}
                </Table.Td>
                <Table.Td>
                  <Badge variant="light" color={STATUS_COLORS[post.status] ?? 'gray'}>
                    {STATUS_LABELS[post.status] ?? post.status}
                  </Badge>
                </Table.Td>
                <Table.Td>
                  <Text size="sm" c="dimmed">
                    {post.date}
                  </Text>
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      ) : (
        <Box py={60}>
          <Stack align="center" gap="sm">
            <IconBook2 size={40} opacity={0.35} />
            <Text c="dimmed">{posts.length ? '没有符合条件的文章。' : '还没有文章。'}</Text>
            {!posts.length && (
              <Button leftSection={<IconPlus size={15} />} onClick={() => setCreateOpen(true)}>
                写第一篇
              </Button>
            )}
          </Stack>
        </Box>
      )}

      <Modal opened={createOpen} onClose={() => setCreateOpen(false)} title="新建文章" centered>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            createPost();
          }}
        >
          <Stack>
            <TextInput
              label="标题"
              description="用于生成文章地址；之后仍可修改标题"
              value={newTitle}
              onChange={(event) => setNewTitle(event.currentTarget.value)}
              data-autofocus
              data-testid="content-new-title"
            />
            {create.isError && <Alert color="red">{create.error.message}</Alert>}
            <Group justify="flex-end">
              <Button variant="default" onClick={() => setCreateOpen(false)}>
                取消
              </Button>
              <Button type="submit" loading={create.isPending} disabled={!newTitle.trim()} data-testid="content-create-confirm">
                创建并开始写作
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>
    </Stack>
  );
}
