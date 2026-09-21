import {
  Alert,
  Badge,
  Button,
  Card,
  Center,
  Checkbox,
  Group,
  List,
  Loader,
  Select,
  Stack,
  Switch,
  Table,
  Text,
  TextInput,
  Title,
} from '@mantine/core';
import {
  IconBuildingStore,
  IconChecklist,
  IconExternalLink,
  IconEye,
  IconUpload,
} from '@tabler/icons-react';
import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';

import { MutationErrorAlert } from '../components/ConflictAlert';
import {
  publicBuildArtifactUrl,
  publicBuildPreviewPageUrl,
  useBuildPublicSite,
  useInitStudio,
  usePublicBuild,
  usePublicBuildPreview,
  usePublishAndBuildPublicSite,
} from '../api/hooks';
import type { PublicBuildResponse, PublicBuildState } from '../api/types';

function formatKb(size: number): string {
  return `${(size / 1024).toFixed(1)} KB`;
}

/** Refetch every public-build query (overview + preview) after a 412. */
function useRefreshPublicBuild() {
  const { name = '' } = useParams();
  const queryClient = useQueryClient();
  return () =>
    void queryClient.invalidateQueries({ queryKey: ['profiles', name, 'public-build'] });
}

function StatusCard({ data }: { data: PublicBuildResponse }) {
  const validation = data.validation;
  const build = data.build;
  return (
    <Card withBorder radius="md" data-testid="build-status">
      <Stack gap="sm">
        <Group gap="sm" wrap="wrap">
          <Title order={3}>状态总览</Title>
          {validation?.ok ? (
            <Badge color="green" variant="light" data-testid="validation-ok">
              校验通过
            </Badge>
          ) : (
            <Badge color="red" variant="light" data-testid="validation-errors">
              校验错误 {validation?.errors?.length ?? 0}
            </Badge>
          )}
          {(validation?.warnings?.length ?? 0) > 0 && (
            <Badge color="yellow" variant="light">
              警告 {validation?.warnings?.length}
            </Badge>
          )}
          {build.exists ? (
            <Badge color="blue" variant="light" data-testid="build-exists">
              已有产物
            </Badge>
          ) : (
            <Badge color="gray" variant="light" data-testid="build-empty">
              尚未构建
            </Badge>
          )}
        </Group>
        {!!validation && !validation.ok && (
          <Alert color="red" title="公开层校验错误" data-testid="validation-error-list">
            <List size="sm">
              {(validation.errors ?? []).map((error) => (
                <List.Item key={error}>{error}</List.Item>
              ))}
            </List>
          </Alert>
        )}
        {!!validation && (validation.warnings?.length ?? 0) > 0 && (
          <Alert color="yellow" title="校验警告">
            <List size="sm">
              {(validation.warnings ?? []).map((warning) => (
                <List.Item key={warning}>{warning}</List.Item>
              ))}
            </List>
          </Alert>
        )}
        <Group gap="xl" wrap="wrap">
          <Text size="sm">
            最近构建：
            <Text span c={build.exists ? undefined : 'dimmed'}>
              {build.exists ? build.built_at : '—'}
            </Text>
          </Text>
          <Text size="sm">
            产物：
            <Text span c={build.exists ? undefined : 'dimmed'}>
              {build.exists
                ? `${build.total_files} 个文件 · ${formatKb(build.total_bytes ?? 0)}`
                : '—'}
            </Text>
          </Text>
        </Group>
        <Text size="xs" c="dimmed" style={{ fontFamily: 'monospace' }}>
          输出目录：{build.output_dir}
        </Text>
      </Stack>
    </Card>
  );
}

function BuildCard({
  etag,
  includeDrafts,
  onIncludeDraftsChange,
  baseUrl,
  onBaseUrlChange,
}: {
  etag: string;
  includeDrafts: boolean;
  onIncludeDraftsChange: (value: boolean) => void;
  baseUrl: string;
  onBaseUrlChange: (value: string) => void;
}) {
  const { name = '' } = useParams();
  const build = useBuildPublicSite(name);
  const refresh = useRefreshPublicBuild();

  const submit = () =>
    build.mutate({
      body: { include_drafts: includeDrafts, base_url: baseUrl.trim() },
      etag,
    });

  return (
    <Card withBorder radius="md" data-testid="build-card">
      <Stack gap="sm">
        <Group gap="sm">
          <IconBuildingStore size={16} />
          <Title order={3}>构建静态站</Title>
        </Group>
        <Group grow align="flex-start">
          <TextInput
            label="基准 URL"
            placeholder="https://www.example.com/site"
            description="生产部署域名，可包含子路径；留空则站内链接用根路径。"
            value={baseUrl}
            onChange={(event) => onBaseUrlChange(event.currentTarget.value)}
          />
          <Switch
            label="包含草稿 / 私有内容（预览模式）"
            description="档案为 private 时必须开启才能构建"
            checked={includeDrafts}
            onChange={(event) => onIncludeDraftsChange(event.currentTarget.checked)}
            mt="lg"
            data-testid="include-drafts"
          />
        </Group>
        <MutationErrorAlert error={build.error} title="构建失败" onRefetch={refresh} />
        {build.isSuccess && build.data && (
          <Alert color="green" title="构建成功" data-testid="build-success">
            已构建：{build.data.output_dir}（{build.data.page_count} 页）
          </Alert>
        )}
        <Group>
          <Button
            leftSection={<IconChecklist size={14} />}
            onClick={submit}
            loading={build.isPending}
            data-testid="build-button"
          >
            构建静态站
          </Button>
        </Group>
      </Stack>
    </Card>
  );
}

function PublishCard({
  data,
  etag,
  includeDrafts,
  baseUrl,
}: {
  data: PublicBuildResponse;
  etag: string;
  includeDrafts: boolean;
  baseUrl: string;
}) {
  const { name = '' } = useParams();
  const [selected, setSelected] = useState<string[]>([]);
  const publish = usePublishAndBuildPublicSite(name);
  const refresh = useRefreshPublicBuild();
  const drafts = data.drafts ?? [];

  const toggle = (slug: string, checked: boolean) =>
    setSelected((prev) =>
      checked ? [...prev, slug] : prev.filter((item) => item !== slug),
    );

  return (
    <Card withBorder radius="md" data-testid="publish-card">
      <Stack gap="sm">
        <Group gap="sm">
          <IconUpload size={16} />
          <Title order={3}>发布草稿并构建</Title>
        </Group>
        <Text size="sm" c="dimmed">
          勾选要发布的草稿，一键发布后立即构建静态站。
        </Text>
        {drafts.length === 0 ? (
          <Text size="sm" c="dimmed" data-testid="no-drafts">
            没有待发布的草稿。
          </Text>
        ) : (
          <Stack gap={4} data-testid="draft-list">
            {drafts.map((draft) => (
              <Checkbox
                key={draft.slug}
                label={`${draft.title || draft.slug}（${draft.slug}）`}
                checked={selected.includes(draft.slug)}
                onChange={(event) => toggle(draft.slug, event.currentTarget.checked)}
              />
            ))}
          </Stack>
        )}
        <MutationErrorAlert error={publish.error} title="发布失败" onRefetch={refresh} />
        {publish.isSuccess && publish.data && (
          <Alert color="green" title="发布并构建完成" data-testid="publish-success">
            已发布 {publish.data.published?.length ?? 0} 篇草稿并构建：
            {publish.data.output_dir}
          </Alert>
        )}
        {drafts.length > 0 && (
          <Group>
            <Button
              onClick={() =>
                publish.mutate(
                  {
                    body: {
                      slugs: selected,
                      include_drafts: includeDrafts,
                      base_url: baseUrl.trim(),
                    },
                    etag,
                  },
                  { onSuccess: () => setSelected([]) },
                )
              }
              loading={publish.isPending}
              disabled={selected.length === 0}
              data-testid="publish-build-button"
            >
              发布并构建
            </Button>
          </Group>
        )}
      </Stack>
    </Card>
  );
}

function ArtifactsCard({ build, profile }: { build: PublicBuildState; profile: string }) {
  return (
    <Card withBorder radius="md" data-testid="artifacts-card">
      <Stack gap="sm">
        <Group gap="sm">
          <IconExternalLink size={16} />
          <Title order={3}>构建产物</Title>
        </Group>
        {!build.exists ? (
          <Text size="sm" c="dimmed" data-testid="no-artifacts">
            尚无构建产物——先运行一次构建。
          </Text>
        ) : (
          <>
            <Table.ScrollContainer minWidth={640}>
              <Table highlightOnHover>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>文件</Table.Th>
                    <Table.Th>大小</Table.Th>
                    <Table.Th>修改时间</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {(build.artifacts ?? []).map((artifact) => (
                    <Table.Tr key={artifact.path} data-testid={`artifact-${artifact.path}`}>
                      <Table.Td>
                        <Text
                          component="a"
                          href={publicBuildArtifactUrl(profile, artifact.path)}
                          target="_blank"
                          rel="noreferrer"
                          size="sm"
                          style={{ fontFamily: 'monospace' }}
                        >
                          {artifact.path}
                        </Text>
                      </Table.Td>
                      <Table.Td>
                        <Text size="xs" c="dimmed">
                          {formatKb(artifact.size ?? 0)}
                        </Text>
                      </Table.Td>
                      <Table.Td>
                        <Text size="xs" c="dimmed">
                          {artifact.modified || '—'}
                        </Text>
                      </Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </Table.ScrollContainer>
            {build.artifacts_truncated && (
              <Text size="xs" c="dimmed">
                仅列出前 {(build.artifacts ?? []).length} 个文件，共 {build.total_files} 个。
              </Text>
            )}
          </>
        )}
      </Stack>
    </Card>
  );
}

function PreviewCard({
  profile,
  includeDrafts,
}: {
  profile: string;
  includeDrafts: boolean;
}) {
  const preview = usePublicBuildPreview(profile, includeDrafts);
  const [selected, setSelected] = useState('');
  const pages = preview.data?.pages ?? [];

  // Follow the loaded page list: keep the selection while it still exists,
  // otherwise fall back to the site index.
  useEffect(() => {
    if (!pages.length) {
      return;
    }
    if (!selected || !pages.some((page) => page.path === selected)) {
      const index = pages.find((page) => page.path === 'index.html');
      setSelected((index ?? pages[0]).path);
    }
  }, [pages, selected]);

  return (
    <Card withBorder radius="md" data-testid="preview-card">
      <Stack gap="sm">
        <Group gap="sm">
          <IconEye size={16} />
          <Title order={3}>整站预览</Title>
        </Group>
        {preview.isPending && (
          <Center py="md">
            <Loader size="sm" />
          </Center>
        )}
        {preview.isError && (
          <Alert color="red" title="预览加载失败">
            {preview.error?.message ?? '无法加载站点预览。'}
          </Alert>
        )}
        {preview.isSuccess && preview.data && (
          <>
            {(preview.data.warnings?.length ?? 0) > 0 && (
              <Alert color="yellow" title="预览提示" data-testid="preview-warnings">
                <List size="sm">
                  {(preview.data.warnings ?? []).slice(0, 20).map((warning) => (
                    <List.Item key={warning}>{warning}</List.Item>
                  ))}
                </List>
              </Alert>
            )}
            {pages.length === 0 ? (
              <Text size="sm" c="dimmed">
                没有可预览的页面。
              </Text>
            ) : (
              <>
                <Select
                  label="预览页面"
                  data={pages.map((page) => ({
                    value: page.path,
                    label: `${page.title || page.path} /${page.path.replace(/index\.html$/, '')}`,
                  }))}
                  value={selected}
                  onChange={(value) => setSelected(value ?? '')}
                  data-testid="preview-select"
                />
                {selected && (
                  <iframe
                    title="整站预览"
                    data-testid="preview-frame"
                    src={publicBuildPreviewPageUrl(profile, selected, includeDrafts)}
                    style={{
                      width: '100%',
                      height: 720,
                      border: '1px solid var(--mantine-color-default-border)',
                      borderRadius: 'var(--mantine-radius-md)',
                      background: 'white',
                    }}
                  />
                )}
              </>
            )}
          </>
        )}
      </Stack>
    </Card>
  );
}

export function PublicBuildPage() {
  const { name = '' } = useParams();
  const overview = usePublicBuild(name);
  const init = useInitStudio(name);
  const queryClient = useQueryClient();
  const [includeDrafts, setIncludeDrafts] = useState(false);
  const [baseUrl, setBaseUrl] = useState('');

  if (overview.isPending) {
    return (
      <Center py="xl">
        <Loader />
      </Center>
    );
  }
  if (overview.isError || !overview.data) {
    return (
      <Alert color="red" title="加载失败">
        {overview.error?.message ?? '无法加载公开构建。'}
      </Alert>
    );
  }

  const data = overview.data.data;
  const etag = overview.data.etag;

  if (!data.initialized) {
    return (
      <Stack gap="md">
        <Title order={2}>{name} · 公开构建</Title>
        <Alert color="yellow" title="公开层未初始化" data-testid="init-needed">
          <Group justify="space-between">
            <Text size="sm">此档案尚未初始化公开层。</Text>
            <Button
              size="compact-sm"
              onClick={() =>
                init.mutate(
                  { etag },
                  {
                    onSuccess: () =>
                      queryClient.invalidateQueries({
                        queryKey: ['profiles', name, 'public-build'],
                      }),
                  },
                )
              }
              loading={init.isPending}
            >
              初始化公开层
            </Button>
          </Group>
        </Alert>
        {init.isError && (
          <MutationErrorAlert
            error={init.error}
            title="初始化失败"
            onRefetch={() =>
              void queryClient.invalidateQueries({
                queryKey: ['profiles', name, 'public-build'],
              })
            }
          />
        )}
      </Stack>
    );
  }

  return (
    <Stack gap="md">
      <Stack gap={4}>
        <Title order={2}>{name} · 公开构建</Title>
        <Text size="sm" c="dimmed">
          校验、预览并构建静态公开站点；本页是发布闸门，不负责生成新内容。
        </Text>
      </Stack>

      <StatusCard data={data} />
      <BuildCard
        etag={etag}
        includeDrafts={includeDrafts}
        onIncludeDraftsChange={setIncludeDrafts}
        baseUrl={baseUrl}
        onBaseUrlChange={setBaseUrl}
      />
      <PublishCard
        data={data}
        etag={etag}
        includeDrafts={includeDrafts}
        baseUrl={baseUrl}
      />
      <ArtifactsCard build={data.build} profile={name} />
      <PreviewCard profile={name} includeDrafts={includeDrafts} />

      <Alert color="blue" title="说明" data-testid="build-notes">
        <List size="sm">
          <List.Item>构建为同步规则渲染（无 LLM、无网络调用），点击即得结果。</List.Item>
          <List.Item>
            输出目录由服务端固定为 dist/public/{name}（Streamlit 页可自定义路径，
            SPA 为路径安全不开放）。
          </List.Item>
          <List.Item>部署到生产由外部脚本 / Caddy 完成，本页不发布任何内容。</List.Item>
          <List.Item>AI 内容生成在「输出工作室」；博客单篇编辑与发布也在那里。</List.Item>
        </List>
      </Alert>
    </Stack>
  );
}
