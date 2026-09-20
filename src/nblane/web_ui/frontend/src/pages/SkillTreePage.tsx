import {
  ActionIcon,
  Alert,
  Badge,
  Box,
  Center,
  Group,
  Loader,
  Stack,
  Text,
  TextInput,
  Title,
} from '@mantine/core';
import { IconChevronDown, IconChevronRight, IconSearch } from '@tabler/icons-react';
import { useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';

import { useSkillTree } from '../api/hooks';
import type { SkillTreeNode } from '../api/types';

// Established status color semantics (also used by the summary chips):
// locked gray / learning blue / solid green / expert violet.
const STATUS_META: Record<string, { label: string; color: string }> = {
  learning: { label: '学习中', color: 'blue' },
  solid: { label: '扎实', color: 'green' },
  expert: { label: '精通', color: 'violet' },
  locked: { label: '锁定', color: 'gray' },
};

const STATUS_ORDER = ['learning', 'solid', 'expert', 'locked'];

function statusMeta(status: string): { label: string; color: string } {
  return STATUS_META[status] ?? { label: status || '未知', color: 'gray' };
}

/** Keep nodes whose title matches, plus the ancestors of matching nodes. */
function filterTree(nodes: SkillTreeNode[], query: string): SkillTreeNode[] {
  const q = query.trim().toLowerCase();
  if (!q) {
    return nodes;
  }
  const walk = (node: SkillTreeNode): SkillTreeNode | null => {
    const children = (node.children ?? [])
      .map(walk)
      .filter((child): child is SkillTreeNode => child !== null);
    if (node.title.toLowerCase().includes(q) || children.length > 0) {
      return { ...node, children };
    }
    return null;
  };
  return nodes
    .map(walk)
    .filter((node): node is SkillTreeNode => node !== null);
}

interface NodeRowProps {
  node: SkillTreeNode;
  depth: number;
  collapsed: ReadonlySet<string>;
  onToggle: (id: string) => void;
  /** While a filter is active every visible node is force-expanded. */
  forceExpanded: boolean;
}

function NodeRow({ node, depth, collapsed, onToggle, forceExpanded }: NodeRowProps) {
  const children = node.children ?? [];
  const isCollapsed = !forceExpanded && collapsed.has(node.id);
  const meta = statusMeta(node.status);
  return (
    <>
      <Group
        gap="xs"
        wrap="nowrap"
        py={4}
        pl={depth * 24}
        data-testid={`skill-node-${node.id}`}
      >
        {children.length > 0 ? (
          <ActionIcon
            variant="subtle"
            color="gray"
            size="sm"
            aria-label={isCollapsed ? `展开 ${node.title}` : `折叠 ${node.title}`}
            onClick={() => onToggle(node.id)}
          >
            {isCollapsed ? <IconChevronRight size={14} /> : <IconChevronDown size={14} />}
          </ActionIcon>
        ) : (
          <Box w={28} />
        )}
        <Badge color={meta.color} variant="light" size="sm">
          {meta.label}
        </Badge>
        <Text size="sm">{node.title}</Text>
        <Badge color="gray" variant="outline" size="sm">
          证据 {node.evidence_count ?? 0}
        </Badge>
      </Group>
      {!isCollapsed &&
        children.map((child) => (
          <NodeRow
            key={child.id}
            node={child}
            depth={depth + 1}
            collapsed={collapsed}
            onToggle={onToggle}
            forceExpanded={forceExpanded}
          />
        ))}
    </>
  );
}

export function SkillTreePage() {
  const { name = '' } = useParams();
  const tree = useSkillTree(name);
  const [query, setQuery] = useState('');
  const [collapsed, setCollapsed] = useState<ReadonlySet<string>>(new Set());

  const visibleNodes = useMemo(
    () => filterTree(tree.data?.nodes ?? [], query),
    [tree.data, query],
  );
  const filtering = query.trim().length > 0;

  const toggle = (id: string) => {
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  if (tree.isPending) {
    return (
      <Center py="xl">
        <Loader />
      </Center>
    );
  }
  if (tree.isError) {
    return (
      <Alert color="red" title="加载失败">
        {tree.error.message}
      </Alert>
    );
  }

  const data = tree.data;
  const counts = data.status_counts ?? {};
  return (
    <Stack gap="md">
      <Group justify="space-between" wrap="wrap">
        <Title order={2}>{data.profile} · 技能树</Title>
        <Group gap="xs" data-testid="status-summary">
          {STATUS_ORDER.map((status) => (
            <Badge
              key={status}
              color={STATUS_META[status].color}
              variant="light"
              data-testid={`status-chip-${status}`}
            >
              {STATUS_META[status].label} {counts[status] ?? 0}
            </Badge>
          ))}
          <Badge color="brand" variant="light" data-testid="status-chip-total">
            共 {counts.total ?? 0} 项
          </Badge>
        </Group>
      </Group>
      <Text size="sm" c="dimmed">
        schema: {data.schema_name || '—'} · 更新于 {data.updated || '—'}
      </Text>
      <TextInput
        placeholder="按标题筛选…"
        leftSection={<IconSearch size={14} />}
        value={query}
        onChange={(event) => setQuery(event.currentTarget.value)}
        aria-label="筛选技能节点"
      />
      {visibleNodes.length === 0 ? (
        <Text c="dimmed">
          {filtering ? '没有匹配的技能节点。' : '技能树为空,先在 skill-tree.yaml 中添加节点。'}
        </Text>
      ) : (
        <Box>
          {visibleNodes.map((node) => (
            <NodeRow
              key={node.id}
              node={node}
              depth={0}
              collapsed={collapsed}
              onToggle={toggle}
              forceExpanded={filtering}
            />
          ))}
        </Box>
      )}
    </Stack>
  );
}
