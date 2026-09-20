import {
  Alert,
  Badge,
  Button,
  Card,
  Center,
  Checkbox,
  Group,
  Loader,
  Menu,
  Select,
  Stack,
  Table,
  Text,
  TextInput,
  Title,
} from '@mantine/core';
import { useDebouncedValue } from '@mantine/hooks';
import {
  IconCheck,
  IconChevronDown,
  IconSearch,
  IconTag,
  IconTrash,
  IconRestore,
} from '@tabler/icons-react';
import { useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';

import {
  useEvidenceReviewBulk,
  useEvidenceReviewDeprecate,
  useEvidenceReviewList,
} from '../api/hooks';
import { MutationErrorAlert } from '../components/ConflictAlert';
import type { EvidenceReviewItem } from '../api/types';

const REVIEW_STATUS_META: Record<string, { label: string; color: string }> = {
  needs_review: { label: '待审核', color: 'yellow' },
  reviewed: { label: '已审核', color: 'green' },
};

const STATUS_OPTIONS = [
  { value: 'needs_review', label: '待审核' },
  { value: 'reviewed', label: '已审核' },
  { value: 'deprecated', label: '已废弃' },
  { value: 'all', label: '全部' },
];

const STRENGTH_OPTIONS = ['weak', 'medium', 'strong', 'high_trust'];
const CONFIDENCE_OPTIONS = ['low', 'medium', 'high'];
const READINESS_OPTIONS = ['private', 'draftable', 'public_ready', 'published'];

const STRENGTH_LABELS: Record<string, string> = {
  unrated: '未评级',
  weak: '弱',
  medium: '中',
  strong: '强',
  high_trust: '高可信',
};

function reviewMeta(status: string): { label: string; color: string } {
  return REVIEW_STATUS_META[status] ?? { label: status || '待审核', color: 'gray' };
}

function ReviewRow({
  item,
  selected,
  onToggle,
}: {
  item: EvidenceReviewItem;
  selected: boolean;
  onToggle: (id: string, checked: boolean) => void;
}) {
  const meta = reviewMeta(item.review_status ?? 'needs_review');
  return (
    <Table.Tr data-testid={`review-row-${item.id}`}>
      <Table.Td>
        <Checkbox
          aria-label={`选择 ${item.title || item.id}`}
          checked={selected}
          onChange={(event) => onToggle(item.id, event.currentTarget.checked)}
        />
      </Table.Td>
      <Table.Td>
        <Text size="sm">
          {item.title || item.id}
          {item.deprecated && (
            <Badge color="red" variant="light" size="sm" ml="xs">
              已废弃
            </Badge>
          )}
        </Text>
        <Text size="xs" c="dimmed">
          {item.id}
        </Text>
      </Table.Td>
      <Table.Td>
        <Badge color="brand" variant="light" size="sm">
          {item.evidence_type}
        </Badge>
      </Table.Td>
      <Table.Td>
        <Text size="sm">{STRENGTH_LABELS[item.strength ?? 'unrated'] ?? item.strength}</Text>
      </Table.Td>
      <Table.Td>
        <Text size="sm">{item.confidence || '—'}</Text>
      </Table.Td>
      <Table.Td>
        <Badge color={meta.color} variant="light" size="sm">
          {meta.label}
        </Badge>
      </Table.Td>
      <Table.Td>
        <Text size="sm" c="dimmed">
          {item.public_readiness || 'private'}
        </Text>
      </Table.Td>
      <Table.Td>
        <Text size="sm" c="dimmed">
          {item.usage_count}
        </Text>
      </Table.Td>
      <Table.Td>
        <Text size="xs" c="dimmed">
          {item.review_reason || '—'}
        </Text>
      </Table.Td>
    </Table.Tr>
  );
}

export function EvidenceReviewPage() {
  const { name = '' } = useParams();
  const [query, setQuery] = useState('');
  const [debouncedQuery] = useDebouncedValue(query, 300);
  const [status, setStatus] = useState('needs_review');
  const [selected, setSelected] = useState<ReadonlySet<string>>(new Set());

  const list = useEvidenceReviewList(name, { status, q: debouncedQuery });
  const bulk = useEvidenceReviewBulk(name);
  const deprecate = useEvidenceReviewDeprecate(name);

  // The green success banner must not outlive the context it confirms: any
  // new selection or filter change resets the mutation state.
  const resetMutations = () => {
    bulk.reset();
    deprecate.reset();
  };

  const items = useMemo(() => list.data?.data.items ?? [], [list.data]);
  const etag = list.data?.etag ?? '';
  const summary = list.data?.data.summary;
  const mutationError = bulk.error ?? deprecate.error;
  const pending = bulk.isPending || deprecate.isPending;

  const toggle = (id: string, checked: boolean) => {
    resetMutations();
    setSelected((prev) => {
      const next = new Set(prev);
      if (checked) {
        next.add(id);
      } else {
        next.delete(id);
      }
      return next;
    });
  };

  const pickAll = () => {
    resetMutations();
    setSelected(new Set(items.map((item) => item.id)));
  };
  const pickNeedsReview = () => {
    resetMutations();
    setSelected(
      new Set(
        items
          .filter((item) => (item.review_status ?? 'needs_review') !== 'reviewed')
          .map((item) => item.id),
      ),
    );
  };
  const clearSelection = () => setSelected(new Set());

  const pickedIds = items.filter((item) => selected.has(item.id)).map((item) => item.id);
  const selectedCount = pickedIds.length;

  const runBulk = (field: string, value: string) => {
    bulk.mutate(
      { body: { ids: pickedIds, field, value }, etag },
      { onSuccess: clearSelection },
    );
  };

  const runDeprecate = (deprecated: boolean) => {
    deprecate.mutate(
      { body: { ids: pickedIds, deprecated }, etag },
      { onSuccess: clearSelection },
    );
  };

  if (list.isError) {
    return (
      <Alert color="red" title="加载失败">
        {list.error.message}
      </Alert>
    );
  }

  return (
    <Stack gap="md">
      <Group justify="space-between" wrap="wrap">
        <Title order={2}>{name} · 证据评审</Title>
        {summary && (
          <Group gap="xs" data-testid="review-summary">
            <Badge color="yellow" variant="light">
              待审核 {summary.needs_review_count}
            </Badge>
            <Badge color="gray" variant="light">
              未关联 {summary.unlinked_count}
            </Badge>
            <Badge color="brand" variant="light">
              活跃条目 {summary.total_entries}
            </Badge>
          </Group>
        )}
      </Group>

      <Group gap="sm" wrap="wrap">
        <TextInput
          placeholder="按标题或 ID 搜索…"
          leftSection={<IconSearch size={14} />}
          value={query}
          onChange={(event) => {
            setQuery(event.currentTarget.value);
            resetMutations();
          }}
          aria-label="搜索证据"
          style={{ flex: 1, minWidth: 220 }}
        />
        <Select
          data={STATUS_OPTIONS}
          value={status}
          onChange={(value) => {
            setStatus(value ?? 'needs_review');
            clearSelection();
            resetMutations();
          }}
          aria-label="审核状态"
          w={160}
        />
      </Group>

      <Group gap="xs" wrap="wrap" data-testid="bulk-bar">
        <Button size="compact-sm" variant="default" onClick={pickAll}>
          全选
        </Button>
        <Button size="compact-sm" variant="default" onClick={pickNeedsReview}>
          选待审核
        </Button>
        <Button size="compact-sm" variant="default" onClick={clearSelection}>
          清除选择
        </Button>
        <Text size="sm" c="dimmed" data-testid="selection-count">
          已选 {selectedCount} 条
        </Text>
        <Button
          size="compact-sm"
          color="green"
          leftSection={<IconCheck size={14} />}
          disabled={selectedCount === 0}
          loading={pending}
          onClick={() => runBulk('review_status', 'reviewed')}
        >
          接受 ({selectedCount})
        </Button>
        <Menu shadow="md" width={200}>
          <Menu.Target>
            <Button
              size="compact-sm"
              variant="light"
              leftSection={<IconTag size={14} />}
              rightSection={<IconChevronDown size={14} />}
              disabled={selectedCount === 0}
            >
              打标
            </Button>
          </Menu.Target>
          <Menu.Dropdown>
            <Menu.Sub>
              <Menu.Sub.Target>
                <Menu.Sub.Item>强度</Menu.Sub.Item>
              </Menu.Sub.Target>
              <Menu.Sub.Dropdown>
                {STRENGTH_OPTIONS.map((value) => (
                  <Menu.Item key={value} onClick={() => runBulk('strength', value)}>
                    {STRENGTH_LABELS[value] ?? value}
                  </Menu.Item>
                ))}
              </Menu.Sub.Dropdown>
            </Menu.Sub>
            <Menu.Sub>
              <Menu.Sub.Target>
                <Menu.Sub.Item>置信度</Menu.Sub.Item>
              </Menu.Sub.Target>
              <Menu.Sub.Dropdown>
                {CONFIDENCE_OPTIONS.map((value) => (
                  <Menu.Item key={value} onClick={() => runBulk('confidence', value)}>
                    {value}
                  </Menu.Item>
                ))}
              </Menu.Sub.Dropdown>
            </Menu.Sub>
            <Menu.Sub>
              <Menu.Sub.Target>
                <Menu.Sub.Item>公开就绪</Menu.Sub.Item>
              </Menu.Sub.Target>
              <Menu.Sub.Dropdown>
                {READINESS_OPTIONS.map((value) => (
                  <Menu.Item key={value} onClick={() => runBulk('public_readiness', value)}>
                    {value}
                  </Menu.Item>
                ))}
              </Menu.Sub.Dropdown>
            </Menu.Sub>
          </Menu.Dropdown>
        </Menu>
        {status === 'deprecated' ? (
          <Button
            size="compact-sm"
            color="gray"
            leftSection={<IconRestore size={14} />}
            disabled={selectedCount === 0}
            loading={pending}
            onClick={() => runDeprecate(false)}
          >
            恢复 ({selectedCount})
          </Button>
        ) : (
          <Button
            size="compact-sm"
            color="red"
            variant="light"
            leftSection={<IconTrash size={14} />}
            disabled={selectedCount === 0}
            loading={pending}
            onClick={() => runDeprecate(true)}
          >
            拒绝 ({selectedCount})
          </Button>
        )}
      </Group>

      <MutationErrorAlert
        error={mutationError}
        title="操作失败"
        onRefetch={() => void list.refetch()}
      />
      {(bulk.isSuccess || deprecate.isSuccess) && !mutationError && (
        <Alert color="green" title="已保存" data-testid="mutation-success">
          证据池已更新。
        </Alert>
      )}

      {list.isPending ? (
        <Center py="xl">
          <Loader />
        </Center>
      ) : items.length === 0 ? (
        <Text c="dimmed">当前过滤条件下没有待处理的证据。</Text>
      ) : (
        <Card withBorder radius="md" p={0}>
          <Table.ScrollContainer minWidth={1000}>
            <Table highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th />
                <Table.Th>标题</Table.Th>
                <Table.Th>类型</Table.Th>
                <Table.Th>强度</Table.Th>
                <Table.Th>置信度</Table.Th>
                <Table.Th>状态</Table.Th>
                <Table.Th>公开就绪</Table.Th>
                <Table.Th>关联</Table.Th>
                <Table.Th>评审原因</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {items.map((item) => (
                <ReviewRow
                  key={item.id}
                  item={item}
                  selected={selected.has(item.id)}
                  onToggle={toggle}
                />
              ))}
            </Table.Tbody>
            </Table>
          </Table.ScrollContainer>
        </Card>
      )}
    </Stack>
  );
}
