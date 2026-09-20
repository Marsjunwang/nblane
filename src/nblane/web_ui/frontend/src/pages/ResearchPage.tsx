import {
  Alert,
  Anchor,
  Badge,
  Button,
  Card,
  Center,
  Group,
  Loader,
  Stack,
  Table,
  Text,
  Title,
} from '@mantine/core';
import { IconExternalLink, IconPlayerPlay } from '@tabler/icons-react';
import { useState } from 'react';
import { useParams } from 'react-router-dom';

import { useResearch } from '../api/hooks';
import type { SidecarInfo } from '../api/types';
import { SidecarFrame } from '../components/SidecarFrame';

function sidecarOriginLabel(sidecar: SidecarInfo): string {
  if (!sidecar.base) {
    return '同源';
  }
  return sidecar.configured ? `已配置 · ${sidecar.base}` : `默认 · ${sidecar.base}`;
}

export function ResearchPage() {
  const { name = '' } = useParams();
  const research = useResearch(name);
  const [libraryEmbedded, setLibraryEmbedded] = useState(false);

  if (research.isPending) {
    return (
      <Center py="xl">
        <Loader />
      </Center>
    );
  }
  if (research.isError) {
    return (
      <Alert color="red" title="加载失败">
        {research.error.message}
      </Alert>
    );
  }

  const data = research.data;
  const summary = data.summary;
  const sidecar = data.sidecar;

  return (
    <Stack gap="md">
      <div>
        <Title order={2}>{data.profile} · 研究台</Title>
        {sidecar && (
          <Text c="dimmed" size="sm" mt={4}>
            论文库 / PDF 阅读器由 Reader API sidecar 承载({sidecarOriginLabel(sidecar)})
          </Text>
        )}
      </div>

      <Card withBorder radius="md" padding="lg" data-testid="research-summary">
        <Group gap="xs">
          <Badge variant="light" color="brand">
            来源 {summary?.total ?? 0}
          </Badge>
          <Badge variant="light" color="yellow">
            进行中 {summary?.active_total ?? 0}
          </Badge>
          <Badge variant="light" color="gray">
            断言 {summary?.claims_total ?? 0}
          </Badge>
          <Badge variant="light" color="gray">
            引用 {summary?.citations_total ?? 0}
          </Badge>
        </Group>
        <Group gap="xs" mt="sm">
          {Object.entries(summary?.status_counts ?? {}).map(([status, count]) => (
            <Badge key={status} variant="outline" color="gray">
              {status}: {count}
            </Badge>
          ))}
          {Object.entries(summary?.kind_counts ?? {}).map(([kind, count]) => (
            <Badge key={kind} variant="outline" color="blue">
              {kind}: {count}
            </Badge>
          ))}
        </Group>
      </Card>

      {sidecar && (
        <Card withBorder radius="md" padding="lg" data-testid="research-paper-library">
          <Group justify="space-between" mb="xs">
            <div>
              <Text fw={600}>Paper Library 工作台</Text>
              <Text size="xs" c="dimmed">
                搜论文、读 PDF、标注与引用都在 sidecar 工作台里完成。
              </Text>
            </div>
            <Group gap="xs">
              <Button
                component="a"
                href={sidecar.paper_library_url}
                target="_blank"
                rel="noreferrer"
                variant="default"
                size="compact-sm"
                leftSection={<IconExternalLink size={14} />}
              >
                新标签打开
              </Button>
              <Button
                variant="light"
                size="compact-sm"
                leftSection={<IconPlayerPlay size={14} />}
                onClick={() => setLibraryEmbedded((value) => !value)}
              >
                {libraryEmbedded ? '收起嵌入' : '嵌入显示'}
              </Button>
            </Group>
          </Group>
          {libraryEmbedded && (
            <SidecarFrame
              title="Paper Library"
              url={sidecar.paper_library_url}
              base={sidecar.base}
              handoffToken={sidecar.handoff_token}
            />
          )}
        </Card>
      )}

      <Card withBorder radius="md" padding="lg" data-testid="research-sources">
        <Text fw={600} mb="xs">
          最近来源
        </Text>
        {(data.sources ?? []).length === 0 ? (
          <Text c="dimmed" size="sm">
            研究收件箱还没有来源;在 Paper Library 工作台里添加第一篇论文。
          </Text>
        ) : (
          <Table.ScrollContainer minWidth={560}>
            <Table striped highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>标题</Table.Th>
                <Table.Th>类型</Table.Th>
                <Table.Th>状态</Table.Th>
                <Table.Th>捕获时间</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {(data.sources ?? []).map((source) => (
                <Table.Tr key={source.id}>
                  <Table.Td>
                    {source.url ? (
                      <Anchor href={source.url} target="_blank" rel="noreferrer">
                        {source.title || source.id}
                      </Anchor>
                    ) : (
                      source.title || source.id
                    )}
                  </Table.Td>
                  <Table.Td>{source.kind}</Table.Td>
                  <Table.Td>{source.status}</Table.Td>
                  <Table.Td>{source.captured_at}</Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
            </Table>
          </Table.ScrollContainer>
        )}
      </Card>
    </Stack>
  );
}
