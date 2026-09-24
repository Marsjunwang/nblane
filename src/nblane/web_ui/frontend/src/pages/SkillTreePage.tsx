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
import { IconChevronDown, IconChevronRight, IconSearch, IconX } from '@tabler/icons-react';
import { useMemo, useState } from 'react';
import type { CSSProperties } from 'react';
import { Link, useParams } from 'react-router-dom';

import { usePatchSkillNodeStatus, useSkillEvidence, useSkillTree } from '../api/hooks';
import type { SkillTreeCategory, SkillTreeNode } from '../api/types';
import { InscriptionCard } from '../starmap/InscriptionCard';
import { SECTOR_ASTERISM_TABLE, asterismById } from '../starmap/layout';
import type { StarmapSelection } from '../starmap/StarmapScene';
import type { StarmapSnapshot } from '../starmap/snapshot';
import { chrome, inscription } from '../theme';

import '../starmap/starmap.css';

// Node states echo the home starmap 三态 vocabulary (layout.ts: locked=空圈
// core0/ring1, learning=实点 core1/ring0, lit=点套圈 core1/ring1) — flat 2D
// glyphs here, same shape/color semantics, no 3D scene. The tree carries a
// fourth rung the starmap folds into "lit": 精通 gets the 泥金 ring (the
// chart's label ladder reserves 泥金 for its highest tier too).
type StateShape = 'ring' | 'dot' | 'dot-ring';

const GOLD = '#dcae55';

const STATUS_META: Record<string, { label: string; shape: StateShape; color: string }> = {
  learning: { label: '学习中', shape: 'dot', color: 'rgba(245, 234, 210, 0.55)' },
  solid: { label: '扎实', shape: 'dot-ring', color: '#f5ead2' },
  expert: { label: '精通', shape: 'dot-ring', color: GOLD },
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

/** 星官小像: the domain asterism's real line shape (asterisms.json) etched
 * in 泥金 as a small inline SVG — same source the starmap carves at sector
 * scale. */
function AsterismFigure({ id }: { id: string }) {
  const aster = asterismById(id);
  if (!aster || aster.stars.length === 0) {
    return null;
  }
  const xs = aster.stars.map((s) => s.x);
  const ys = aster.stars.map((s) => -s.y);
  const minX = Math.min(...xs);
  const minY = Math.min(...ys);
  const spanX = Math.max(...xs) - minX || 1;
  const spanY = Math.max(...ys) - minY || 1;
  const span = Math.max(spanX, spanY);
  const pad = span * 0.14;
  const stroke = span * 0.022;
  return (
    <svg
      viewBox={`${minX - pad} ${minY - pad} ${spanX + 2 * pad} ${spanY + 2 * pad}`}
      width={46}
      height={46}
      aria-hidden="true"
      data-testid={`asterism-figure-${id}`}
      style={{ flexShrink: 0, opacity: 0.92 }}
    >
      {aster.lines.map(([a, b], i) =>
        a < aster.stars.length && b < aster.stars.length ? (
          <line
            key={`l${i}`}
            x1={aster.stars[a].x}
            y1={-aster.stars[a].y}
            x2={aster.stars[b].x}
            y2={-aster.stars[b].y}
            stroke={GOLD}
            strokeOpacity={0.5}
            strokeWidth={stroke}
          />
        ) : null,
      )}
      {aster.stars.map((s, i) => {
        const mag = s.mag ?? 5;
        const r = stroke * (1.1 + Math.min(3, Math.max(0, 5.6 - mag)) * 0.55);
        return (
          <circle
            key={`s${i}`}
            cx={s.x}
            cy={-s.y}
            r={r}
            fill={GOLD}
            fillOpacity={0.85}
          />
        );
      })}
    </svg>
  );
}

/** 类目头星官化 banner: asterism mini-figure + 官名 + 三态统计 + 小传.
 * SECTOR_ASTERISM (starmap/layout.ts) is the domain→asterism source of
 * truth; the six domains whose real shapes are not in asterisms.json yet
 * (翼/房/箕/轸/轩辕/虚) carry a 拟形 marker instead of a figure. */
function CategoryBanner({ category }: { category: SkillTreeCategory }) {
  const zhName = category.name || category.id || '';
  const mapping = SECTOR_ASTERISM_TABLE[zhName];
  const aster = mapping ? asterismById(mapping.id) : undefined;
  const locked = Math.max(
    0,
    (category.count ?? 0) - (category.lit_count ?? 0) - (category.learning_count ?? 0),
  );
  return (
    <Box
      px="sm"
      py="sm"
      mb={2}
      data-testid={`category-banner-${category.id}`}
      style={{
        background: 'rgba(14, 24, 40, 0.5)',
        border: '1px solid rgba(220, 174, 85, 0.3)',
        borderRadius: 10,
      }}
    >
      <Group gap="sm" wrap="nowrap" align="flex-start">
        {aster && <AsterismFigure id={aster.id} />}
        <Stack gap={4} style={{ minWidth: 0, flex: 1 }}>
          <Group gap="xs" wrap="wrap" align="baseline">
            <Text
              fw={600}
              style={{ color: '#faf5e6', fontFamily: inscription.titleFontFamily }}
            >
              {zhName}
            </Text>
            {mapping && (
              <Text size="sm" style={{ color: GOLD, letterSpacing: 1 }}>
                {mapping.name}
              </Text>
            )}
            {mapping && !aster && (
              <Text
                size="xs"
                px={6}
                data-testid={`template-note-${category.id}`}
                style={{
                  border: '1px solid rgba(220, 174, 85, 0.35)',
                  borderRadius: 999,
                  color: chrome.dim,
                }}
              >
                拟形·模板
              </Text>
            )}
          </Group>
          <Group gap="md" wrap="nowrap" data-testid={`tri-count-${category.id}`}>
            <Group gap={5} wrap="nowrap" title={`锁定 ${locked}`}>
              <StateGlyph shape="ring" color={STATUS_META.locked.color} />
              <Text size="xs" style={{ color: chrome.dim, fontVariantNumeric: 'tabular-nums' }}>
                {locked}
              </Text>
            </Group>
            <Group gap={5} wrap="nowrap" title={`在学 ${category.learning_count ?? 0}`}>
              <StateGlyph shape="dot" color={STATUS_META.learning.color} />
              <Text size="xs" style={{ color: chrome.dim, fontVariantNumeric: 'tabular-nums' }}>
                {category.learning_count ?? 0}
              </Text>
            </Group>
            <Group gap={5} wrap="nowrap" title={`点亮 ${category.lit_count ?? 0}`}>
              <StateGlyph shape="dot-ring" color={STATUS_META.solid.color} />
              <Text size="xs" style={{ color: chrome.dim, fontVariantNumeric: 'tabular-nums' }}>
                {category.lit_count ?? 0}
              </Text>
            </Group>
          </Group>
          {aster?.lore && (
            <Text size="xs" lineClamp={1} style={{ color: chrome.dim }} title={aster.lore}>
              {aster.lore}
            </Text>
          )}
        </Stack>
      </Group>
    </Box>
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
    if ((node.title ?? '').toLowerCase().includes(q) || children.length > 0) {
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
  selectedId: string;
  onSelect: (id: string) => void;
}

function NodeRow({ node, depth, collapsed, onToggle, forceExpanded, selectedId, onSelect }: NodeRowProps) {
  const children = node.children ?? [];
  const isCollapsed = !forceExpanded && collapsed.has(node.id);
  const meta = statusMeta(node.status ?? 'locked');
  const locked = node.status === 'locked';
  const evidenceCount = node.evidence_count ?? 0;
  const selected = selectedId === node.id;
  return (
    <>
      <Group
        gap="xs"
        wrap="nowrap"
        py={6}
        pl={depth * 22}
        data-testid={`skill-node-${node.id}`}
        onClick={() => onSelect(node.id)}
        style={{
          cursor: 'pointer',
          borderBottom: '1px solid rgba(220, 174, 85, 0.08)',
          background: selected ? 'rgba(220, 174, 85, 0.1)' : undefined,
        }}
      >
        {children.length > 0 ? (
          <ActionIcon
            variant="subtle"
            color="brand"
            size="sm"
            aria-label={isCollapsed ? `展开 ${node.title}` : `折叠 ${node.title}`}
            onClick={(event) => {
              event.stopPropagation();
              onToggle(node.id);
            }}
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
            selectedId={selectedId}
            onSelect={onSelect}
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

// --- 节点铭文卡 (b/c) ---------------------------------------------------------

/** The starmap InscriptionCard needs a snapshot for its north/goal edit
 * paths; a skill selection never touches them, so a structural stub does. */
const STUB_SNAPSHOT: StarmapSnapshot = {
  north_star: '',
  north: { is_set: false, full: '', brief: '', visibility: 'private' },
  goals: [],
  categories: [],
  skills: [],
  projects: [],
  evidence: [],
  counts: {
    evidence: 0,
    evidence_needs_review: 0,
    evidence_flying: 0,
    projects_active: 0,
    skills_lit: 0,
  },
};

/** 三态 stepper rungs (锁定 → 在学 → 点亮); the PATCH endpoint maps 点亮
 * onto the YAML status solid (expert stays review-earned, not settable). */
const STATUS_STEPS: { key: string; label: string; shape: StateShape }[] = [
  { key: 'locked', label: '锁定', shape: 'ring' },
  { key: 'learning', label: '在学', shape: 'dot' },
  { key: 'lit', label: '点亮', shape: 'dot-ring' },
];

function stepIndexOf(status: string): number {
  if (status === 'learning') return 1;
  if (status === 'solid' || status === 'expert') return 2;
  return 0;
}

/** Deep-link stage on the Evidence page for one linked row (the page also
 * honors focus=<id> to preselect the entry). */
function evidenceStageFor(item: { review_status?: string }): string {
  if (item.review_status === 'reviewed') return 'seated';
  if (item.review_status === 'deprecated') return 'deprecated';
  return 'review';
}

function SkillInscriptionCard({
  profile,
  node,
  category,
  etag,
  onClose,
}: {
  profile: string;
  node: SkillTreeNode;
  category: SkillTreeCategory | null;
  etag: string;
  onClose: () => void;
}) {
  const evidence = useSkillEvidence(profile, node.id);
  const patchStatus = usePatchSkillNodeStatus(profile);
  const meta = statusMeta(node.status ?? 'locked');
  const mapping = category ? SECTOR_ASTERISM_TABLE[category.name || category.id || ''] : undefined;
  const activeStep = stepIndexOf(node.status ?? 'locked');

  const selection: StarmapSelection = {
    kind: 'skill',
    id: node.id,
    title: node.title || node.id,
    rows: [
      ['状态', meta.label],
      [
        '类目',
        category
          ? `${category.name || category.id}${mapping ? ` · ${mapping.name}` : ''}`
          : '—',
      ],
      ['证据', `${node.evidence_count ?? 0}`],
    ],
  };

  const evidenceItems = evidence.data?.items ?? [];
  return (
    <Box
      component="aside"
      w={320}
      data-testid="skill-inscription"
      style={{ flexShrink: 0, position: 'sticky', top: 72 }}
    >
      <div
        className="starmap-detail open"
        style={{
          position: 'relative',
          transform: 'none',
          width: 'auto',
          maxHeight: 'none',
          overflow: 'visible',
        }}
      >
        <ActionIcon
          variant="subtle"
          color="brand"
          size="sm"
          aria-label="收起铭文卡"
          onClick={onClose}
          style={{ position: 'absolute', top: 10, right: 10, zIndex: 1 }}
        >
          <IconX size={14} />
        </ActionIcon>
        <InscriptionCard
          selection={selection}
          snapshot={STUB_SNAPSHOT}
          profile={profile}
          onSaved={() => undefined}
        />
        <div data-testid="status-stepper" role="group" aria-label="技能状态">
          <p className="starmap-detail-hint" style={hintStyle}>
            境界
          </p>
          <Group gap={6} wrap="nowrap">
            {STATUS_STEPS.map((step, index) => {
              const active = index === activeStep;
              return (
                <button
                  key={step.key}
                  type="button"
                  data-testid={`stepper-${step.key}`}
                  aria-pressed={active}
                  disabled={active || patchStatus.isPending}
                  onClick={() => {
                    if (!active) {
                      patchStatus.mutate({ nodeId: node.id, status: step.key, etag });
                    }
                  }}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 5,
                    padding: '4px 10px',
                    borderRadius: 999,
                    border: `1px solid ${active ? GOLD : 'rgba(220, 174, 85, 0.28)'}`,
                    background: active ? 'rgba(220, 174, 85, 0.16)' : 'transparent',
                    color: active ? '#f0cd7f' : 'rgba(245, 234, 210, 0.6)',
                    fontSize: 12,
                    cursor: patchStatus.isPending ? 'wait' : 'pointer',
                    fontFamily: 'inherit',
                  }}
                >
                  <StateGlyph shape={step.shape} color={active ? GOLD : 'rgba(232, 226, 210, 0.4)'} />
                  {step.label}
                </button>
              );
            })}
          </Group>
          {node.status === 'expert' && (
            <p style={{ ...hintStyle, marginTop: 6 }}>精通为评审所得;点亮记作扎实。</p>
          )}
          {patchStatus.isError && (
            <p role="alert" style={{ ...hintStyle, color: '#e3968b', marginTop: 6 }}>
              {patchStatus.error.message}
            </p>
          )}
        </div>
        <div data-testid="skill-evidence" style={{ marginTop: 14 }}>
          <p style={hintStyle}>关联证据</p>
          {evidence.isPending && <Loader size="xs" />}
          {evidence.isError && (
            <p style={{ ...hintStyle, color: '#e3968b' }}>{evidence.error.message}</p>
          )}
          {!evidence.isPending && !evidence.isError && evidenceItems.length === 0 && (
            <p style={hintStyle}>尚无关联证据。</p>
          )}
          {evidenceItems.map((item) => (
            <div key={item.id} style={{ paddingBlock: 4 }}>
              <Link
                className="starmap-detail-link"
                data-testid={`skill-evidence-link-${item.id}`}
                style={{ marginTop: 0 }}
                to={`/p/${encodeURIComponent(profile)}/evidence?stage=${evidenceStageFor(item)}&focus=${encodeURIComponent(item.id)}`}
              >
                {item.title || item.id}
              </Link>
              <div style={{ ...hintStyle, marginTop: 0 }}>
                {[item.date, item.evidence_type].filter(Boolean).join(' · ') || '—'}
              </div>
            </div>
          ))}
        </div>
      </div>
    </Box>
  );
}

const hintStyle: CSSProperties = {
  fontSize: 12,
  color: 'rgba(220, 174, 85, 0.65)',
  letterSpacing: 2,
  margin: '12px 0 4px',
};

// --- Page ----------------------------------------------------------------------

export function SkillTreePage() {
  const { name = '' } = useParams();
  const tree = useSkillTree(name);
  const [query, setQuery] = useState('');
  const [collapsed, setCollapsed] = useState<ReadonlySet<string>>(new Set());
  const [selectedId, setSelectedId] = useState('');

  const data = tree.data?.tree;
  const etag = tree.data?.etag ?? '';

  const visibleNodes = useMemo(
    () => filterTree(data?.nodes ?? [], query),
    [data, query],
  );
  const filtering = query.trim().length > 0;

  const nodeById = useMemo(() => {
    const map = new Map<string, SkillTreeNode>();
    const walk = (nodes: SkillTreeNode[] | undefined) => {
      for (const node of nodes ?? []) {
        map.set(node.id, node);
        walk(node.children ?? []);
      }
    };
    walk(data?.nodes);
    return map;
  }, [data]);

  // Category sections: banner order follows the server rollup; top-level
  // nodes group under their own category, leftovers render bannerless last.
  const sections = useMemo(() => {
    const categories = data?.categories ?? [];
    const byCat = new Map<string, SkillTreeNode[]>();
    for (const node of visibleNodes) {
      const key = node.category ?? '';
      if (!byCat.has(key)) byCat.set(key, []);
      byCat.get(key)!.push(node);
    }
    const out: { category: SkillTreeCategory | null; nodes: SkillTreeNode[] }[] = [];
    const seen = new Set<string>();
    for (const cat of categories) {
      const key = cat.id ?? '';
      const nodes = byCat.get(key);
      if (nodes?.length) {
        out.push({ category: cat, nodes });
        seen.add(key);
      }
    }
    for (const [key, nodes] of byCat) {
      if (!seen.has(key)) {
        out.push({
          category: categories.find((cat) => (cat.id ?? '') === key) ?? null,
          nodes,
        });
      }
    }
    return out;
  }, [data, visibleNodes]);

  const selectedNode = selectedId ? nodeById.get(selectedId) : undefined;
  const selectedCategory = selectedNode
    ? (data?.categories ?? []).find((cat) => (cat.id ?? '') === (selectedNode.category ?? '')) ?? null
    : null;

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

  const counts = data?.status_counts ?? {};
  return (
    <Stack gap="md">
      <Group justify="space-between" wrap="wrap">
        <Title
          order={2}
          style={{ fontFamily: inscription.bodyFontFamily, color: '#faf5e6' }}
        >
          {data?.profile} · 技能树
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
      <Group align="flex-start" wrap="nowrap" gap="md">
        <Box
          px="md"
          py="sm"
          style={{
            flex: 1,
            minWidth: 0,
            background: 'rgba(22, 38, 61, 0.55)',
            border: '1px solid rgba(220, 174, 85, 0.22)',
            borderRadius: 12,
            fontFamily: inscription.bodyFontFamily,
          }}
        >
          <Text size="xs" pb="xs" style={{ color: chrome.dim, letterSpacing: 0.5 }}>
            schema: {data?.schema_name || '—'} · 更新于 {data?.updated || '—'}
          </Text>
          {visibleNodes.length === 0 ? (
            <Text c="dimmed" py="sm">
              {filtering ? '没有匹配的技能节点。' : '技能树为空,先在 skill-tree.yaml 中添加节点。'}
            </Text>
          ) : (
            <Stack gap="sm">
              {sections.map((section, index) => (
                <Box key={section.category?.id ?? `uncat-${index}`}>
                  {section.category && section.category.id && (
                    <CategoryBanner category={section.category} />
                  )}
                  <Box>
                    {section.nodes.map((node) => (
                      <NodeRow
                        key={node.id}
                        node={node}
                        depth={0}
                        collapsed={collapsed}
                        onToggle={toggle}
                        forceExpanded={filtering}
                        selectedId={selectedId}
                        onSelect={(id) =>
                          setSelectedId((prev) => (prev === id ? '' : id))
                        }
                      />
                    ))}
                  </Box>
                </Box>
              ))}
            </Stack>
          )}
        </Box>
        {selectedNode && (
          <SkillInscriptionCard
            profile={name}
            node={selectedNode}
            category={selectedCategory}
            etag={etag}
            onClose={() => setSelectedId('')}
          />
        )}
      </Group>
    </Stack>
  );
}
