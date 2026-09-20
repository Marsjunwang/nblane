import {
  Alert,
  Anchor,
  Badge,
  Button,
  Card,
  Center,
  Group,
  Loader,
  Modal,
  ScrollArea,
  Select,
  Stack,
  Table,
  Text,
  TextInput,
  Title,
} from '@mantine/core';
import { useDebouncedValue } from '@mantine/hooks';
import { IconExternalLink, IconSearch } from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';

import { useEvidenceEntry, useEvidenceList } from '../api/hooks';
import type { EvidenceEntryDetail } from '../api/types';

const PAGE_SIZE = 50;

const REVIEW_STATUS_META: Record<string, { label: string; color: string }> = {
  needs_review: { label: '待审核', color: 'yellow' },
  reviewed: { label: '已审核', color: 'green' },
};

const STATUS_OPTIONS = [
  { value: '', label: '全部(不含已废弃)' },
  { value: 'needs_review', label: '待审核' },
  { value: 'reviewed', label: '已审核' },
  { value: 'deprecated', label: '已废弃' },
  { value: 'all', label: '全部(含已废弃)' },
];

function reviewMeta(status: string): { label: string; color: string } {
  return REVIEW_STATUS_META[status] ?? { label: status || '待审核', color: 'gray' };
}

function DetailRow({ label, value }: { label: string; value?: string }) {
  if (!value) {
    return null;
  }
  return (
    <Group gap="xs" align="baseline" wrap="nowrap">
      <Text size="sm" c="dimmed" w={88} style={{ flexShrink: 0 }}>
        {label}
      </Text>
      <Text size="sm" style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
        {value}
      </Text>
    </Group>
  );
}

function RefChips({ label, refs }: { label: string; refs?: string[] }) {
  if (!refs || refs.length === 0) {
    return null;
  }
  return (
    <Group gap="xs" align="baseline">
      <Text size="sm" c="dimmed" w={88} style={{ flexShrink: 0 }}>
        {label}
      </Text>
      <Group gap={4}>
        {refs.map((ref) => (
          <Badge key={ref} color="blue" variant="outline" size="sm">
            {ref}
          </Badge>
        ))}
      </Group>
    </Group>
  );
}

function EvidenceDetailModal({
  profile,
  entryId,
  onClose,
}: {
  profile: string;
  entryId: string;
  onClose: () => void;
}) {
  const entry = useEvidenceEntry(profile, entryId);
  const detail: EvidenceEntryDetail | undefined = entry.data;
  return (
    <Modal
      opened={entryId.length > 0}
      onClose={onClose}
      title={detail?.title || '证据详情'}
      size="lg"
    >
      {entry.isPending && (
        <Center py="md">
          <Loader size="sm" />
        </Center>
      )}
      {entry.isError && (
        <Alert color="red" title="加载失败">
          {entry.error.message}
        </Alert>
      )}
      {detail && (
        <ScrollArea.Autosize mah="70vh">
          <Stack gap="xs" data-testid="evidence-detail">
            <Group gap="xs">
              <Badge color="brand" variant="light" size="sm">
                {detail.evidence_type}
              </Badge>
              <Badge
                color={reviewMeta(detail.review_status ?? '').color}
                variant="light"
                size="sm"
              >
                {reviewMeta(detail.review_status ?? '').label}
              </Badge>
              {detail.deprecated && (
                <Badge color="red" variant="light" size="sm">
                  已废弃
                </Badge>
              )}
            </Group>
            <DetailRow label="日期" value={detail.date} />
            {detail.url && (
              <Group gap="xs" align="baseline">
                <Text size="sm" c="dimmed" w={88} style={{ flexShrink: 0 }}>
                  链接
                </Text>
                <Anchor href={detail.url} target="_blank" rel="noreferrer" size="sm">
                  {detail.url}
                </Anchor>
              </Group>
            )}
            <DetailRow label="摘要" value={detail.summary} />
            <DetailRow label="强度" value={detail.strength} />
            <DetailRow label="置信度" value={detail.confidence} />
            <DetailRow label="公开就绪" value={detail.public_readiness} />
            <RefChips label="来源引用" refs={detail.source_refs} />
            <RefChips label="项目引用" refs={detail.project_refs} />
            <RefChips label="经历引用" refs={detail.experience_refs} />
            <RefChips label="看板引用" refs={detail.kanban_refs} />
            <DetailRow label="来源摘录" value={detail.source_excerpt} />
            <DetailRow label="来源" value={detail.origin} />
            <DetailRow label="来源标识" value={detail.origin_ref} />
            <DetailRow label="来源详情" value={detail.origin_detail} />
            <DetailRow label="语言" value={detail.language} />
            <DetailRow label="正文" value={detail.formatted_content} />
            <DetailRow label="原始内容" value={detail.original_content} />
            {detail.deprecated && detail.replaced_by && (
              <DetailRow label="替代条目" value={detail.replaced_by} />
            )}
          </Stack>
        </ScrollArea.Autosize>
      )}
    </Modal>
  );
}

export function EvidencePage() {
  const { name = '' } = useParams();
  const [query, setQuery] = useState('');
  const [debouncedQuery] = useDebouncedValue(query, 300);
  const [status, setStatus] = useState('');
  const [limit, setLimit] = useState(PAGE_SIZE);
  const [selectedId, setSelectedId] = useState('');

  useEffect(() => {
    setLimit(PAGE_SIZE);
  }, [debouncedQuery, status]);

  const list = useEvidenceList(name, { status, q: debouncedQuery, limit });

  if (list.isError) {
    return (
      <Alert color="red" title="加载失败">
        {list.error.message}
      </Alert>
    );
  }

  const data = list.data;
  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  return (
    <Stack gap="md">
      <Group justify="space-between" wrap="wrap">
        <Title order={2}>{name} · 证据池</Title>
        <Text size="xs" c="dimmed">
          编辑功能开发中
        </Text>
      </Group>
      <Group gap="sm" wrap="wrap">
        <TextInput
          placeholder="按标题搜索…"
          leftSection={<IconSearch size={14} />}
          value={query}
          onChange={(event) => setQuery(event.currentTarget.value)}
          aria-label="搜索证据"
          style={{ flex: 1, minWidth: 220 }}
        />
        <Select
          data={STATUS_OPTIONS}
          value={status}
          onChange={(value) => setStatus(value ?? '')}
          aria-label="审核状态"
          w={200}
        />
      </Group>
      {list.isPending ? (
        <Center py="xl">
          <Loader />
        </Center>
      ) : items.length === 0 ? (
        <Text c="dimmed">没有匹配的证据条目。</Text>
      ) : (
        <Card withBorder radius="md" p={0}>
          <Table.ScrollContainer minWidth={720}>
            <Table highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>标题</Table.Th>
                <Table.Th>类型</Table.Th>
                <Table.Th>日期</Table.Th>
                <Table.Th>审核状态</Table.Th>
                <Table.Th>来源</Table.Th>
                <Table.Th />
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {items.map((item) => (
                <Table.Tr
                  key={item.id}
                  onClick={() => setSelectedId(item.id)}
                  style={{ cursor: 'pointer' }}
                  data-testid={`evidence-row-${item.id}`}
                >
                  <Table.Td>
                    <Text size="sm">{item.title || item.id}</Text>
                  </Table.Td>
                  <Table.Td>
                    <Badge color="brand" variant="light" size="sm">
                      {item.evidence_type}
                    </Badge>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm" c="dimmed">
                      {item.date || '—'}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Badge
                      color={reviewMeta(item.review_status ?? '').color}
                      variant="light"
                      size="sm"
                    >
                      {reviewMeta(item.review_status ?? '').label}
                    </Badge>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm" c="dimmed">
                      {(item.source_refs ?? []).length}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    {item.url && (
                      <IconExternalLink size={14} aria-label="外部链接" />
                    )}
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
            </Table>
          </Table.ScrollContainer>
        </Card>
      )}
      {!list.isPending && (
        <Group justify="space-between">
          <Text size="sm" c="dimmed" data-testid="evidence-count">
            显示 {items.length} / 共 {total} 条
          </Text>
          {items.length < total && (
            <Button variant="light" size="sm" onClick={() => setLimit((n) => n + PAGE_SIZE)}>
              加载更多
            </Button>
          )}
        </Group>
      )}
      <EvidenceDetailModal
        profile={name}
        entryId={selectedId}
        onClose={() => setSelectedId('')}
      />
    </Stack>
  );
}
