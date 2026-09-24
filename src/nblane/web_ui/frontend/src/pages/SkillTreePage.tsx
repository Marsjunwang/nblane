import {
  ActionIcon,
  Alert,
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
import { chrome, inscription } from '../theme';

// Node states echo the home starmap 三态 vocabulary (layout.ts: locked=空圈
// core0/ring1, learning=实点 core1/ring0, lit=点套圈 core1/ring1) — flat 2D
// glyphs here, same shape/color semantics, no 3D scene. The tree carries a
// fourth rung the starmap folds into "lit": 精通 gets the 泥金 ring (the
// chart's label ladder reserves 泥金 for its highest tier too).
type StateShape = 'ring' | 'dot' | 'dot-ring';

const STATUS_META: Record<string, { label: string; shape: StateShape; color: string }> = {
  learning: { label: '学习中', shape: 'dot', color: 'rgba(245, 234, 210, 0.55)' },
  solid: { label: '扎实', shape: 'dot-ring', color: '#f5ead2' },
  expert: { label: '精通', shape: 'dot-ring', color: '#dcae55' },
  locked: { label: '锁定', shape: 'ring', color: 'rgba(232, 226, 210, 0.35)' },
};

const STATUS_ORDER = ['learning', 'solid', 'expert', 'locked'];

function statusMeta(status: string): { label: string; shape: StateShape; color: string } {
  return STATUS_META[status] ?? { label: status || '未知', shape: 'ring', color: chrome.dim };
}

/** 三态 glyph: 空圈 (hollow ring) / 实点 (filled dot) / 点套圈 (dot in ring). */
function StateGlyph({ shape, color }: { shape: StateShape; color: string }) {
  const ring = shape !== 'dot';
  const dot = shape !== 'ring';
  return (
    <span
      aria-hidden="true"
      style={{
        display: 'inline-flex',
        width: 14,
        height: 14,
        flexShrink: 0,
        alignItems: 'center',
        justifyContent: 'center',
        borderRadius: '50%',
        border: ring ? `1.5px solid ${color}` : 'none',
        boxSizing: 'border-box',
      }}
    >
      {dot && (
        <span
          style={{
            display: 'inline-block',
            width: shape === 'dot-ring' ? 5 : 8,
            height: shape === 'dot-ring' ? 5 : 8,
            borderRadius: '50%',
            background: color,
          }}
        />
      )}
    </span>
  );
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
  const locked = node.status === 'locked';
  const evidenceCount = node.evidence_count ?? 0;
  return (
    <>
      <Group
        gap="xs"
        wrap="nowrap"
        py={6}
        pl={depth * 22}
        data-testid={`skill-node-${node.id}`}
        style={{ borderBottom: '1px solid rgba(220, 174, 85, 0.08)' }}
      >
        {children.length > 0 ? (
          <ActionIcon
            variant="subtle"
            color="brand"
            size="sm"
            aria-label={isCollapsed ? `展开 ${node.title}` : `折叠 ${node.title}`}
            onClick={() => onToggle(node.id)}
          >
            {isCollapsed ? <IconChevronRight size={14} /> : <IconChevronDown size={14} />}
          </ActionIcon>
        ) : (
          <Box w={28} style={{ flexShrink: 0 }} />
        )}
        <StateGlyph shape={meta.shape} color={meta.color} />
        <Text
          size="sm"
          lineClamp={1}
          style={{
            minWidth: 0,
            color: locked ? chrome.dim : meta.shape === 'dot-ring' && node.status === 'expert'
              ? inscription.titleColor
              : chrome.text,
          }}
        >
          {node.title}
        </Text>
        <Text
          size="xs"
          style={{ flexShrink: 0, color: locked ? '#8d8570' : chrome.dim }}
        >
          {meta.label}
        </Text>
        <Text
          size="xs"
          style={{
            flexShrink: 0,
            marginLeft: 'auto',
            color: evidenceCount > 0 ? chrome.goldText : chrome.dim,
            fontVariantNumeric: 'tabular-nums',
          }}
        >
          证据 {evidenceCount}
        </Text>
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

/** Summary chip: state glyph + label + count, hairline gold frame. */
function StatusChip({ status, count, testId }: { status: string; count: number; testId: string }) {
  const meta = statusMeta(status);
  return (
    <Group
      gap={6}
      wrap="nowrap"
      px={10}
      py={4}
      data-testid={testId}
      style={{
        border: '1px solid rgba(220, 174, 85, 0.22)',
        borderRadius: 999,
        fontSize: 12,
        color: status === 'locked' ? chrome.dim : chrome.text,
        fontVariantNumeric: 'tabular-nums',
      }}
    >
      <StateGlyph shape={meta.shape} color={meta.color} />
      <span>{`${meta.label} ${count}`}</span>
    </Group>
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
        <Title
          order={2}
          style={{ fontFamily: inscription.bodyFontFamily, color: '#faf5e6' }}
        >
          {data.profile} · 技能树
        </Title>
        <Group gap="xs" data-testid="status-summary">
          {STATUS_ORDER.map((status) => (
            <StatusChip
              key={status}
              status={status}
              count={counts[status] ?? 0}
              testId={`status-chip-${status}`}
            />
          ))}
          <Group
            gap={6}
            wrap="nowrap"
            px={10}
            py={4}
            data-testid="status-chip-total"
            style={{
              border: `1px solid ${chrome.gold}`,
              borderRadius: 999,
              fontSize: 12,
              color: chrome.goldText,
              fontVariantNumeric: 'tabular-nums',
            }}
          >
            共 {`${counts.total ?? 0}`} 项
          </Group>
        </Group>
      </Group>
      <TextInput
        placeholder="按标题筛选…"
        leftSection={<IconSearch size={14} />}
        value={query}
        onChange={(event) => setQuery(event.currentTarget.value)}
        aria-label="筛选技能节点"
      />
      <Box
        px="md"
        py="sm"
        style={{
          background: 'rgba(22, 38, 61, 0.55)',
          border: '1px solid rgba(220, 174, 85, 0.22)',
          borderRadius: 12,
          fontFamily: inscription.bodyFontFamily,
        }}
      >
        <Text size="xs" pb="xs" style={{ color: chrome.dim, letterSpacing: 0.5 }}>
          schema: {data.schema_name || '—'} · 更新于 {data.updated || '—'}
        </Text>
        {visibleNodes.length === 0 ? (
          <Text c="dimmed" py="sm">
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
      </Box>
    </Stack>
  );
}
