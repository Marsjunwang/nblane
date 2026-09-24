import {
  Alert,
  Badge,
  Box,
  Button,
  Card,
  Center,
  Checkbox,
  Chip,
  Collapse,
  Group,
  Loader,
  Modal,
  Select,
  Stack,
  Stepper,
  Text,
  TextInput,
  Title,
  Tooltip,
} from '@mantine/core';
import { useDebouncedValue, useMediaQuery } from '@mantine/hooks';
import {
  IconArchive,
  IconCheck,
  IconKeyboard,
  IconLink,
  IconPlus,
  IconRestore,
  IconSearch,
  IconSparkles,
  IconTrash,
} from '@tabler/icons-react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import { Navigate, useParams, useSearchParams } from 'react-router-dom';

import {
  useCrystallizeApply,
  useCrystallizeCandidates,
  useCrystallizeDraft,
  useEditEvidenceEntry,
  useEvidenceEntry,
  useEvidenceReviewList,
  useEvidenceSkillSuggestions,
  useEvidenceStages,
  useReviewEvidenceEntry,
  useSetEvidenceSkillLinks,
  useSkillTreeFlat,
} from '../api/hooks';
import { streamJob } from '../api/jobs';
import { MutationErrorAlert } from '../components/ConflictAlert';
import { InscriptionCard, InscriptionRow } from '../components/InscriptionCard';
import { inscription, chrome } from '../theme';
import type {
  CrystallizeCandidate,
  CrystallizeDraftResponse,
  EvidenceEntryDetail,
  EvidenceReviewItem,
  EvidenceStageRisk,
  JobCreateResponse,
} from '../api/types';

type Stage = 'crystallize' | 'review' | 'seated' | 'strengthen' | 'deprecated';

const STAGES: { key: Stage; label: string }[] = [
  { key: 'crystallize', label: '待结晶' },
  { key: 'review', label: '待评审' },
  { key: 'seated', label: '已入座' },
  { key: 'strengthen', label: '待补强' },
  { key: 'deprecated', label: '已废弃' },
];

const STAGE_TO_LIST_STATUS: Record<Stage, string> = {
  crystallize: 'all',
  review: 'needs_review',
  seated: 'reviewed',
  strengthen: 'all',
  deprecated: 'deprecated',
};

// 证据类型枚举 → 中文(数据层枚举不动,仅展示层映射)。
const TYPE_LABELS: Record<string, string> = {
  practice: '实践',
  paper: '论文',
  course: '课程',
  project: '项目',
  output: '输出',
  learning: '学习',
};

function typeLabel(value: string): string {
  return TYPE_LABELS[value] ?? value;
}

const STRENGTH_LABELS: Record<string, string> = {
  unrated: '未评级',
  weak: '弱',
  medium: '中',
  strong: '强',
  high_trust: '高可信',
};

const STRENGTH_OPTIONS = [
  { value: '', label: '清除评级' },
  { value: 'weak', label: '弱' },
  { value: 'medium', label: '中' },
  { value: 'strong', label: '强' },
  { value: 'high_trust', label: '高可信' },
];

const CONFIDENCE_OPTIONS = [
  { value: '', label: '清除' },
  { value: 'low', label: 'low' },
  { value: 'medium', label: 'medium' },
  { value: 'high', label: 'high' },
];

const READINESS_OPTIONS = [
  { value: '', label: '清除' },
  { value: 'private', label: 'private' },
  { value: 'draftable', label: 'draftable' },
  { value: 'public_ready', label: 'public_ready' },
  { value: 'published', label: 'published' },
];

function reviewBody(action: 'accept' | 'reject' | 'restore') {
  return { action, strength: '', confidence: '', public_readiness: '' };
}

function stageCount(
  stages: ReturnType<typeof useEvidenceStages>['data'],
  stage: Stage,
): number {
  if (!stages) return 0;
  switch (stage) {
    case 'crystallize':
      return stages.pending_crystallize_count ?? 0;
    case 'review':
      return stages.needs_review_count ?? 0;
    case 'seated':
      return stages.seated_count ?? 0;
    case 'strengthen':
      return stages.strengthen_count ?? 0;
    case 'deprecated':
      return stages.deprecated_count ?? 0;
  }
}

// --- Left column: five-stage nav --------------------------------------------

// Inscription-adjacent nav rows (深底/细金边/明体): active = hairline gold
// frame + gold-tinted ground; inactive = quiet 月白 row with a gold hover
// wash. Counts are dim tabular numerals, gold only on the active stage.
function StageNav({
  stages,
  active,
  onSelect,
}: {
  stages: ReturnType<typeof useEvidenceStages>['data'];
  active: Stage;
  onSelect: (stage: Stage) => void;
}) {
  return (
    <Stack gap={4} data-testid="stage-nav">
      {STAGES.map((stage) => {
        const isActive = active === stage.key;
        return (
          <Box
            key={stage.key}
            component="button"
            type="button"
            onClick={() => onSelect(stage.key)}
            data-testid={`stage-${stage.key}`}
            style={{
              display: 'flex',
              width: '100%',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 8,
              padding: '8px 12px',
              borderRadius: 6,
              cursor: 'pointer',
              textAlign: 'left',
              fontFamily: inscription.bodyFontFamily,
              fontSize: 14,
              color: isActive
                ? chrome.goldText
                : stage.key === 'deprecated'
                  ? chrome.dim
                  : chrome.text,
              background: isActive ? 'rgba(220, 174, 85, 0.10)' : 'transparent',
              border: `1px solid ${isActive ? 'rgba(220, 174, 85, 0.45)' : 'transparent'}`,
              transition: 'background 0.15s, border-color 0.15s, color 0.15s',
            }}
            onMouseEnter={(event) => {
              if (!isActive) {
                event.currentTarget.style.background = 'rgba(220, 174, 85, 0.06)';
              }
            }}
            onMouseLeave={(event) => {
              if (!isActive) {
                event.currentTarget.style.background = 'transparent';
              }
            }}
          >
            <span>{stage.label}</span>
            <span
              style={{
                fontSize: 12,
                fontVariantNumeric: 'tabular-nums',
                color: isActive ? chrome.goldText : chrome.dim,
              }}
            >
              {stageCount(stages, stage.key)}
            </span>
          </Box>
        );
      })}
    </Stack>
  );
}

// --- Middle column: list rows ------------------------------------------------

function EvidenceRow({
  item,
  active,
  cursor,
  onSelect,
  onDeprecate,
  onRestore,
}: {
  item: EvidenceReviewItem;
  active: boolean;
  cursor: boolean;
  onSelect: () => void;
  /** Hover shortcuts: deprecate (active rows) / restore (deprecated rows). */
  onDeprecate?: () => void;
  onRestore?: () => void;
}) {
  const [hovered, setHovered] = useState(false);
  const deprecated = Boolean(item.deprecated);
  return (
    <Card
      withBorder
      radius="md"
      p="xs"
      onClick={onSelect}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      data-testid={`evidence-row-${item.id}`}
      style={{
        cursor: 'pointer',
        // Inscription-adjacent row: deep ground, hairline gold edge; selected
        // = solid gold, quick-review cursor = dashed gold (not Mantine yellow).
        background: 'rgba(22, 38, 61, 0.55)',
        borderColor: active
          ? 'var(--mantine-color-brand-5)'
          : cursor
            ? chrome.goldText
            : 'rgba(220, 174, 85, 0.16)',
        borderStyle: cursor && !active ? 'dashed' : 'solid',
        opacity: deprecated ? 0.72 : 1,
      }}
    >
      <Group justify="space-between" wrap="nowrap">
        <Stack gap={2} style={{ minWidth: 0 }}>
          <Text
            size="sm"
            lineClamp={1}
            td={deprecated ? 'line-through' : undefined}
            c={deprecated ? 'dimmed' : undefined}
          >
            {item.title || item.id}
          </Text>
          <Text size="xs" c="dimmed">
            {typeLabel(item.evidence_type)} · {item.date || '无日期'} · 关联 {item.usage_count}
          </Text>
        </Stack>
        <Group gap={4} wrap="nowrap" style={{ flexShrink: 0 }}>
          {hovered && !deprecated && onDeprecate && (
            <Tooltip label="废弃这条证据" withinPortal>
              <Button
                size="compact-xs"
                variant="subtle"
                color="red"
                onClick={(event) => {
                  event.stopPropagation();
                  onDeprecate();
                }}
                data-testid={`row-deprecate-${item.id}`}
              >
                废弃
              </Button>
            </Tooltip>
          )}
          {hovered && deprecated && onRestore && (
            <Tooltip label="恢复到证据池" withinPortal>
              <Button
                size="compact-xs"
                variant="subtle"
                color="gray"
                onClick={(event) => {
                  event.stopPropagation();
                  onRestore();
                }}
                data-testid={`row-restore-${item.id}`}
              >
                恢复
              </Button>
            </Tooltip>
          )}
          {deprecated ? (
            <Badge size="sm" variant="light" color="red">
              已废弃
            </Badge>
          ) : (
            <>
              {item.breakthrough && (
                <Badge
                  size="sm"
                  variant="outline"
                  color="brand"
                  data-testid={`row-breakthrough-${item.id}`}
                >
                  突破
                </Badge>
              )}
              <Badge
                size="sm"
                variant={item.review_status === 'reviewed' ? 'light' : 'outline'}
                color={item.review_status === 'reviewed' ? 'brand' : 'gray'}
              >
                {STRENGTH_LABELS[item.strength ?? 'unrated'] ?? item.strength}
              </Badge>
            </>
          )}
        </Group>
      </Group>
    </Card>
  );
}

// --- Right column: inscription detail card -----------------------------------

function ProvenanceSection({ detail }: { detail: EvidenceEntryDetail }) {
  const kanbanRefs = detail.kanban_ref_details ?? [];
  const projectRefs = detail.project_refs ?? [];
  const hasOrigin = Boolean(detail.origin);
  if (!kanbanRefs.length && !projectRefs.length && !hasOrigin) {
    return null;
  }
  return (
    <Stack gap={2} mt="xs">
      <Text size="sm" style={{ color: inscription.titleColor }}>
        出处
      </Text>
      {kanbanRefs.map((ref) => (
        <InscriptionRow key={ref.ref} label="看板">
          {ref.status === 'linked' ? (
            <span>
              {ref.title || ref.task_id}{' '}
              <Text span size="xs" style={{ color: inscription.dimColor }}>
                ({ref.task_id})
              </Text>
            </span>
          ) : (
            <Tooltip label="任务已归档或删除;原文已快照在下方" withinPortal>
              <Badge
                size="sm"
                variant="outline"
                color="gray"
                leftSection={<IconArchive size={12} />}
                data-testid={`tombstone-${ref.task_id}`}
              >
                已归档 · {ref.task_id || ref.ref}
              </Badge>
            </Tooltip>
          )}
        </InscriptionRow>
      ))}
      {projectRefs.length > 0 && (
        <InscriptionRow label="项目">
          {projectRefs.join('、')}
        </InscriptionRow>
      )}
      {hasOrigin && (
        <InscriptionRow label="来源">
          {detail.origin}
          {detail.origin_ref ? ` · ${detail.origin_ref}` : ''}
        </InscriptionRow>
      )}
    </Stack>
  );
}

function SkillLinkEditor({
  profile,
  entryId,
  linked,
}: {
  profile: string;
  entryId: string;
  linked: string[];
}) {
  const tree = useSkillTreeFlat(profile);
  const suggestions = useEvidenceSkillSuggestions(profile, entryId);
  const setLinks = useSetEvidenceSkillLinks(profile);
  const labels = useMemo(() => {
    const map: Record<string, string> = {};
    for (const node of tree.data?.nodes ?? []) {
      map[node.id] = node.title;
    }
    for (const item of suggestions.data?.suggestions ?? []) {
      map[item.id] = item.label;
    }
    return map;
  }, [tree.data, suggestions.data]);

  const save = (next: string[]) =>
    setLinks.mutate({ entryId, skillIds: next, etag: tree.data?.etag ?? '' });

  return (
    <Stack gap={4} mt="xs">
      <Group gap="xs">
        <Text size="sm" style={{ color: inscription.titleColor }}>
          技能关联
        </Text>
        {suggestions.data && suggestions.data.backend !== 'none' && (
          <Badge size="xs" variant="outline" color="gray">
            建议:{({ rule: '规则', embedding: '嵌入', llm: 'AI' } as Record<string, string>)[
              suggestions.data.backend ?? ''
            ] ?? suggestions.data.backend}
          </Badge>
        )}
      </Group>
      <Group gap={4} wrap="wrap">
        {linked.map((id) => (
          <Chip
            key={id}
            checked
            onChange={() => save(linked.filter((item) => item !== id))}
            size="xs"
            variant="outline"
            data-testid={`linked-skill-${id}`}
          >
            {labels[id] ?? id} ✕
          </Chip>
        ))}
        {linked.length === 0 && (
          <Text size="xs" style={{ color: inscription.dimColor }}>
            尚未入座任何技能节点
          </Text>
        )}
      </Group>
      {(suggestions.data?.suggestions?.length ?? 0) > 0 && (
        <Group gap={4} wrap="wrap" data-testid="skill-suggestions">
          {(suggestions.data?.suggestions ?? []).map((item) => (
            <Button
              key={item.id}
              size="compact-xs"
              variant="outline"
              color="brand"
              leftSection={<IconPlus size={12} />}
              onClick={() => save([...linked, item.id])}
              data-testid={`suggest-skill-${item.id}`}
              style={{ color: inscription.bodyColor }}
            >
              {item.label}
              {item.category ? ` · ${item.category}` : ''}
            </Button>
          ))}
        </Group>
      )}
      {setLinks.isError && (
        <Text size="xs" c="red">
          {setLinks.error.message}
        </Text>
      )}
    </Stack>
  );
}

function EvidenceDetailCard({
  profile,
  entryId,
  etag,
  onClose,
}: {
  profile: string;
  entryId: string;
  etag: string;
  onClose: () => void;
}) {
  const entry = useEvidenceEntry(profile, entryId);
  const review = useReviewEvidenceEntry(profile);
  const edit = useEditEvidenceEntry(profile);
  const [editing, setEditing] = useState(false);
  const [showMore, setShowMore] = useState(false);
  const [draft, setDraft] = useState({ title: '', summary: '', date: '', url: '' });

  useEffect(() => {
    setEditing(false);
    setShowMore(false);
  }, [entryId]);

  const detail = entry.data;
  if (entry.isPending) {
    return (
      <Card withBorder radius="md">
        <Center py="md">
          <Loader size="sm" />
        </Center>
      </Card>
    );
  }
  if (entry.isError || !detail) {
    return (
      <Alert color="red" title="加载失败">
        {entry.error?.message ?? '未知错误'}
      </Alert>
    );
  }

  const startEdit = () => {
    setDraft({
      title: detail.title ?? '',
      summary: detail.summary ?? '',
      date: detail.date ?? '',
      url: detail.url ?? '',
    });
    setEditing(true);
  };
  const saveEdit = () => {
    edit.mutate(
      { entryId, body: { fields: draft }, etag },
      { onSuccess: () => setEditing(false) },
    );
  };
  const setField = (field: string, value: string) =>
    edit.mutate({ entryId, body: { fields: { [field]: value } }, etag });

  const aside = (
    <Group gap={4} wrap="nowrap">
      <Badge color="brand" variant="light" size="sm">
        {typeLabel(detail.evidence_type)}
      </Badge>
      {detail.deprecated && (
        <Badge color="red" variant="light" size="sm">
          已废弃
        </Badge>
      )}
    </Group>
  );

  return (
    <InscriptionCard title={detail.title || detail.id} aside={aside} testId="evidence-detail">
      <Stack gap={4}>
        {editing ? (
          <Stack gap="xs" data-testid="evidence-edit-form">
            <TextInput
              label="标题"
              value={draft.title}
              onChange={(event) =>
                setDraft((prev) => ({ ...prev, title: event.currentTarget.value }))
              }
            />
            <TextInput
              label="摘要"
              value={draft.summary}
              onChange={(event) =>
                setDraft((prev) => ({ ...prev, summary: event.currentTarget.value }))
              }
            />
            <Group grow>
              <TextInput
                label="日期"
                value={draft.date}
                placeholder="2026-01-31"
                onChange={(event) =>
                  setDraft((prev) => ({ ...prev, date: event.currentTarget.value }))
                }
              />
              <TextInput
                label="链接"
                value={draft.url}
                onChange={(event) =>
                  setDraft((prev) => ({ ...prev, url: event.currentTarget.value }))
                }
              />
            </Group>
            <Group gap="xs">
              <Button size="compact-sm" onClick={saveEdit} loading={edit.isPending}>
                保存
              </Button>
              <Button size="compact-sm" variant="subtle" onClick={() => setEditing(false)}>
                取消
              </Button>
            </Group>
          </Stack>
        ) : (
          <>
            {detail.summary && <InscriptionRow label="摘要">{detail.summary}</InscriptionRow>}
            <InscriptionRow label="日期">{detail.date || '—'}</InscriptionRow>
          </>
        )}

        <Group gap="xs" mt={4} wrap="wrap" align="center">
          <Text size="xs" style={{ color: inscription.dimColor }}>
            分量
          </Text>
          <Select
            size="xs"
            w={120}
            data={STRENGTH_OPTIONS}
            value={detail.strength || ''}
            onChange={(value) => setField('strength', value ?? '')}
            aria-label="分量"
            disabled={editing}
          />
          <Tooltip label="突破证据额外 +1000 计入技能进阶分" withinPortal>
            <Button
              size="compact-xs"
              variant={detail.breakthrough ? 'light' : 'outline'}
              color="brand"
              aria-pressed={Boolean(detail.breakthrough)}
              disabled={editing || edit.isPending}
              onClick={() =>
                edit.mutate({
                  entryId,
                  // 突破 round-trips as "true"/"false" strings (data-contracts).
                  body: { fields: { breakthrough: detail.breakthrough ? 'false' : 'true' } },
                  etag,
                })
              }
              data-testid="evidence-breakthrough-toggle"
            >
              突破
            </Button>
          </Tooltip>
        </Group>

        <ProvenanceSection detail={detail} />
        <SkillLinkEditor
          profile={profile}
          entryId={entryId}
          linked={detail.skill_refs ?? []}
        />

        {(detail.formatted_content || detail.original_content) && (
          <Stack gap={2} mt="xs">
            <Text size="sm" style={{ color: inscription.titleColor }}>
              正文
            </Text>
            <Text size="sm" style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
              {detail.formatted_content || detail.original_content}
            </Text>
          </Stack>
        )}

        <Button
          size="compact-xs"
          variant="subtle"
          color="gray"
          mt="xs"
          onClick={() => setShowMore((value) => !value)}
          data-testid="evidence-more-toggle"
        >
          {showMore ? '收起 ▲' : '更多 ▼'}
        </Button>
        <Collapse in={showMore}>
          <Stack gap={6} data-testid="evidence-more">
            <InscriptionRow label="置信度">
              <Select
                size="xs"
                w={140}
                data={CONFIDENCE_OPTIONS}
                value={detail.confidence || ''}
                onChange={(value) => setField('confidence', value ?? '')}
                aria-label="置信度"
                disabled={editing}
              />
            </InscriptionRow>
            <Text size="xs" style={{ color: inscription.dimColor, paddingLeft: 80 }}>
              接受/结晶时按来源自动推导;可在此手改
            </Text>
            <InscriptionRow label="公开就绪">
              <Select
                size="xs"
                w={140}
                data={READINESS_OPTIONS}
                value={detail.public_readiness || ''}
                onChange={(value) => setField('public_readiness', value ?? '')}
                aria-label="公开就绪"
                disabled={editing}
              />
            </InscriptionRow>
            {detail.url && <InscriptionRow label="链接">{detail.url}</InscriptionRow>}
            {(detail.source_refs ?? []).length > 0 && (
              <InscriptionRow label="资料">
                {(detail.source_refs ?? []).join('、')}
              </InscriptionRow>
            )}
            {(detail.experience_refs ?? []).length > 0 && (
              <InscriptionRow label="经历">
                {(detail.experience_refs ?? []).join('、')}
              </InscriptionRow>
            )}
            {detail.source_excerpt && (
              <InscriptionRow label="摘录">{detail.source_excerpt}</InscriptionRow>
            )}
            {detail.original_language && (
              <InscriptionRow label="语言">{detail.original_language}</InscriptionRow>
            )}
            {detail.original_content_hash && (
              <InscriptionRow label="原文哈希">{detail.original_content_hash}</InscriptionRow>
            )}
            {detail.replaced_by && (
              <InscriptionRow label="替代条目">{detail.replaced_by}</InscriptionRow>
            )}
            <InscriptionRow label="ID">{detail.id}</InscriptionRow>
          </Stack>
        </Collapse>

        <Group gap="xs" mt="md">
          {detail.deprecated ? (
            <Button
              size="compact-sm"
              color="gray"
              leftSection={<IconRestore size={14} />}
              loading={review.isPending}
              onClick={() => review.mutate({ entryId, body: reviewBody('restore'), etag })}
            >
              恢复
            </Button>
          ) : (
            <>
              {(detail.review_status ?? 'needs_review') !== 'reviewed' && (
                <Button
                  size="compact-sm"
                  color="brand"
                  leftSection={<IconCheck size={14} />}
                  loading={review.isPending}
                  onClick={() => review.mutate({ entryId, body: reviewBody('accept'), etag })}
                  data-testid="evidence-accept"
                >
                  接受
                </Button>
              )}
              <Button
                size="compact-sm"
                color="red"
                variant="light"
                leftSection={<IconTrash size={14} />}
                loading={review.isPending}
                onClick={() => review.mutate({ entryId, body: reviewBody('reject'), etag })}
                data-testid="evidence-reject"
              >
                废弃
              </Button>
            </>
          )}
          {!editing && (
            <Button size="compact-sm" variant="subtle" onClick={startEdit}>
              编辑
            </Button>
          )}
          <Button size="compact-sm" variant="subtle" color="gray" onClick={onClose}>
            关闭
          </Button>
        </Group>
        <MutationErrorAlert
          error={review.error ?? edit.error}
          title="操作失败"
          onRefetch={() => void entry.refetch()}
        />
      </Stack>
    </InscriptionCard>
  );
}

function RiskDetailCard({ risk }: { risk: EvidenceStageRisk }) {
  return (
    <InscriptionCard title={risk.label || risk.skill_id} testId="risk-detail">
      <Stack gap={4}>
        <Group gap="xs">
          <Badge color="orange" variant="light">
            {risk.status}
          </Badge>
          <Badge color="red" variant="outline">
            {risk.risk_level}
          </Badge>
        </Group>
        <InscriptionRow label="原因">{risk.risk_reason}</InscriptionRow>
        <InscriptionRow label="要求">
          {risk.required_strength || '—'}(当前最高 {risk.highest_strength || '未评级'})
        </InscriptionRow>
        <InscriptionRow label="证据">
          {(risk.evidence_refs ?? []).length
            ? (risk.evidence_refs ?? []).join('、')
            : '无关联证据 — 去结晶或录一条'}
        </InscriptionRow>
      </Stack>
    </InscriptionCard>
  );
}

// --- Crystallize wizard -------------------------------------------------------

interface DraftRowState {
  include: boolean;
  strength: string;
}

function CrystallizeWizard({
  profile,
  opened,
  initialPicked,
  onClose,
  onApplied,
}: {
  profile: string;
  opened: boolean;
  /** Candidate key (task id or title) preselected when opening from a card. */
  initialPicked?: string;
  onClose: () => void;
  onApplied: () => void;
}) {
  const candidates = useCrystallizeCandidates(profile);
  const draftMutation = useCrystallizeDraft(profile);
  const applyMutation = useCrystallizeApply(profile);

  const [step, setStep] = useState(0);
  const [picked, setPicked] = useState<ReadonlySet<string>>(new Set());
  const [draft, setDraft] = useState<CrystallizeDraftResponse | null>(null);
  const [draftRows, setDraftRows] = useState<DraftRowState[]>([]);
  const [jobPhase, setJobPhase] = useState('');
  const [jobError, setJobError] = useState('');
  const stopStreamRef = useRef<(() => void) | null>(null);
  const watchdogRef = useRef<number | null>(null);

  const clearPending = useCallback(() => {
    stopStreamRef.current?.();
    stopStreamRef.current = null;
    if (watchdogRef.current !== null) {
      window.clearTimeout(watchdogRef.current);
      watchdogRef.current = null;
    }
  }, []);

  const reset = useCallback(() => {
    clearPending();
    setStep(0);
    setPicked(new Set());
    setDraft(null);
    setDraftRows([]);
    setJobPhase('');
    setJobError('');
    draftMutation.reset();
    applyMutation.reset();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clearPending]);

  // Preselect a candidate when the wizard is opened from its inscription card.
  useEffect(() => {
    if (opened && initialPicked) {
      setPicked(new Set([initialPicked]));
    }
  }, [opened, initialPicked]);

  // Never leak a running stream/timer when the modal closes or unmounts.
  useEffect(() => {
    if (!opened) {
      clearPending();
    }
  }, [opened, clearPending]);
  useEffect(() => clearPending, [clearPending]);

  const items = useMemo(() => candidates.data?.items ?? [], [candidates.data]);

  const togglePick = (task: CrystallizeCandidate, checked: boolean) => {
    setPicked((prev) => {
      const next = new Set(prev);
      if (checked) {
        next.add(task.id || task.title);
      } else {
        next.delete(task.id || task.title);
      }
      return next;
    });
  };

  const adoptDraft = useCallback((payload: CrystallizeDraftResponse) => {
    setDraft(payload);
    const rows = (payload.patch?.evidence_entries ?? []) as Record<string, unknown>[];
    setDraftRows(
      rows.map((row) => ({
        include: true,
        strength: String(row.strength ?? ''),
      })),
    );
    setStep(2);
  }, []);

  const failJob = useCallback(
    (message: string) => {
      clearPending();
      setJobPhase('');
      setJobError(message);
    },
    [clearPending],
  );

  const generate = (useLlm: boolean) => {
    setJobError('');
    const ids = items
      .filter((task) => picked.has(task.id || task.title))
      .map((task) => task.id)
      .filter(Boolean);
    const titles = items
      .filter((task) => picked.has(task.id || task.title) && !task.id)
      .map((task) => task.title);
    if (!useLlm) {
      draftMutation.mutate(
        { task_ids: ids, titles, use_llm: false },
        {
          onSuccess: (payload) => {
            adoptDraft(payload as CrystallizeDraftResponse);
          },
        },
      );
      return;
    }
    setJobPhase('排队中…');
    draftMutation.mutate(
      { task_ids: ids, titles, use_llm: true },
      {
        onSuccess: (payload) => {
          const job = (payload as JobCreateResponse).job_id;
          if (!job) {
            failJob('AI 草稿任务创建失败;可改用规则草稿。');
            return;
          }
          // Client-side last-resort watchdog: the backend caps the job at
          // 120s, so a silent stream past 130s means the SSE connection
          // broke — fail loud instead of spinning forever.
          watchdogRef.current = window.setTimeout(() => {
            failJob('AI 草稿等待超时;请重试,或改用规则草稿(立等可取)。');
          }, 130_000);
          stopStreamRef.current = streamJob(profile, job, {
            onProgress: (frame) => {
              setJobPhase(frame.event?.message || frame.event?.phase || '生成中…');
            },
            onDone: (frame) => {
              clearPending();
              if (frame.result) {
                adoptDraft(frame.result as unknown as CrystallizeDraftResponse);
              } else {
                failJob('AI 草稿没有返回结果;可改用规则草稿。');
              }
            },
            onError: (frame) => {
              failJob(
                frame?.error?.message ?? 'AI 草稿失败(连接中断);可改用规则草稿。',
              );
            },
          });
        },
        onError: (error) => {
          failJob(`AI 草稿任务创建失败:${error.message};可改用规则草稿。`);
        },
      },
    );
  };

  const apply = () => {
    if (!draft) return;
    const patch = structuredClone(draft.patch ?? {}) as { evidence_entries?: Record<string, unknown>[] };
    const rows = patch.evidence_entries ?? [];
    rows.forEach((row, index) => {
      const state = draftRows[index];
      if (!state) return;
      if (state.strength) row.strength = state.strength;
      else delete row.strength;
    });
    applyMutation.mutate(
      {
        patch,
        task_ids: (draft.tasks ?? []).map((task) => task.id ?? '').filter(Boolean),
        titles: (draft.tasks ?? [])
          .filter((task) => !task.id)
          .map((task) => task.title ?? ''),
        include_evidence: draftRows.map((row) => row.include),
        include_nodes: null,
        allow_status_change: false,
      },
      {
        onSuccess: () => {
          onApplied();
          reset();
          onClose();
        },
      },
    );
  };

  const generating = jobPhase !== '';

  return (
    <Modal
      opened={opened}
      onClose={() => {
        reset();
        onClose();
      }}
      title="从已完成任务结晶"
      size="lg"
      data-testid="crystallize-wizard"
    >
      <Stepper active={step} onStepClick={setStep} size="sm" mb="md">
        <Stepper.Step label="选 Done 任务" />
        <Stepper.Step label="生成草稿" />
        <Stepper.Step label="评级入库" />
      </Stepper>

      {step === 0 && (
        <Stack gap="xs">
          {candidates.isPending && (
            <Center py="md">
              <Loader size="sm" />
            </Center>
          )}
          {!candidates.isPending && items.length === 0 && (
            <Text c="dimmed" data-testid="wizard-empty">
              没有待结晶的 Done 任务。
            </Text>
          )}
          {items.map((task) => {
            const key = task.id || task.title;
            return (
              <Card
                key={key}
                withBorder
                radius="md"
                p="xs"
                style={{
                  background: 'rgba(22, 38, 61, 0.55)',
                  borderColor: picked.has(key) ? 'var(--mantine-color-brand-5)' : 'rgba(220, 174, 85, 0.16)',
                }}
              >
                <Group wrap="nowrap" align="flex-start">
                  <Checkbox
                    aria-label={`选择 ${task.title}`}
                    checked={picked.has(key)}
                    onChange={(event) => togglePick(task, event.currentTarget.checked)}
                    data-testid={`wizard-pick-${key}`}
                  />
                  <Stack gap={2} style={{ minWidth: 0 }}>
                    <Text size="sm">{task.title}</Text>
                    <Text size="xs" c="dimmed">
                      {task.completed_on || '无完成日期'}
                      {task.project_id ? ` · ${task.project_id}` : ''}
                    </Text>
                    {(task.blockers ?? []).length > 0 && (
                      <Text size="xs" c="orange">
                        {(task.blockers ?? []).join(' ')}
                      </Text>
                    )}
                  </Stack>
                </Group>
              </Card>
            );
          })}
          <Group justify="flex-end">
            <Button disabled={picked.size === 0} onClick={() => setStep(1)}>
              下一步({picked.size})
            </Button>
          </Group>
        </Stack>
      )}

      {step === 1 && (
        <Stack gap="md">
          <Text size="sm" c="dimmed">
            规则草稿立即生成毛坯(每任务一条,带原文快照);AI 草稿由 LLM 提炼并给出技能建议(最长约 90 秒)。
          </Text>
          {generating && (
            <Group gap="xs" data-testid="wizard-progress">
              <Loader size="sm" />
              <Text size="sm">{jobPhase}</Text>
            </Group>
          )}
          {jobError && (
            <Alert color="red" title="AI 草稿失败" data-testid="wizard-ai-error">
              <Stack gap="xs">
                <Text size="sm">{jobError}</Text>
                <Group>
                  <Button
                    size="compact-sm"
                    variant="default"
                    onClick={() => generate(false)}
                    data-testid="wizard-degrade-rule"
                  >
                    改用规则草稿
                  </Button>
                  <Button
                    size="compact-sm"
                    variant="subtle"
                    onClick={() => generate(true)}
                    data-testid="wizard-retry-ai"
                  >
                    重试 AI 草稿
                  </Button>
                </Group>
              </Stack>
            </Alert>
          )}
          {draftMutation.isError && !jobError && (
            <Alert color="red" title="草稿生成失败">
              {draftMutation.error.message}
            </Alert>
          )}
          <Group>
            <Button
              variant="default"
              onClick={() => generate(false)}
              loading={draftMutation.isPending && !generating}
              disabled={generating}
              data-testid="wizard-rule-draft"
            >
              规则草稿
            </Button>
            <Button
              leftSection={<IconSparkles size={14} />}
              onClick={() => generate(true)}
              disabled={generating || draftMutation.isPending}
              data-testid="wizard-ai-draft"
            >
              AI 草稿
            </Button>
          </Group>
        </Stack>
      )}

      {step === 2 && draft && (
        <Stack gap="xs">
          <Text size="sm" c="dimmed">
            草稿来源:{draft.backend === 'llm' ? 'AI' : '规则'} · 勾选入库条目并定分量(置信度按来源自动推导)
          </Text>
          {((draft.patch?.evidence_entries ?? []) as Record<string, unknown>[]).length === 0 ? (
            <Alert color="yellow" title="草稿为空" data-testid="wizard-empty-draft">
              <Stack gap="xs">
                <Text size="sm">
                  这次没有生成任何证据条目;可以重选任务,或改用规则草稿保底。
                </Text>
                <Group>
                  <Button
                    size="compact-sm"
                    variant="default"
                    onClick={() => {
                      setDraft(null);
                      generate(false);
                    }}
                  >
                    改用规则草稿
                  </Button>
                  <Button size="compact-sm" variant="subtle" onClick={() => setStep(0)}>
                    返回重选
                  </Button>
                </Group>
              </Stack>
            </Alert>
          ) : (
            ((draft.patch?.evidence_entries ?? []) as Record<string, unknown>[]).map((row, index) => (
              <WizardDraftRow
                key={index}
                index={index}
                row={row}
                skillHints={draftSkillHints(draft, index)}
                state={draftRows[index] ?? { include: true, strength: '' }}
                onChange={(next) =>
                  setDraftRows((prev) =>
                    prev.map((state, i) => (i === index ? next : state)),
                  )
                }
              />
            ))
          )}
          {applyMutation.isError && (
            <Alert color="red" title="入库失败">
              {applyMutation.error.message}
            </Alert>
          )}
          <Group justify="flex-end">
            <Button
              color="brand"
              loading={applyMutation.isPending}
              disabled={!draftRows.some((row) => row.include)}
              onClick={apply}
              data-testid="wizard-apply"
            >
              入库并标记已结晶
            </Button>
          </Group>
        </Stack>
      )}
    </Modal>
  );
}

/** Skill ids the draft's node_updates attach to evidence row *index*. */
function draftSkillHints(draft: CrystallizeDraftResponse, index: number): string[] {
  const updates = (draft.patch?.node_updates ?? []) as Record<string, unknown>[];
  const ordinal = `first_${index + 1}`;
  const altOrdinal = `ev_${index + 1}`;
  const hints: string[] = [];
  for (const update of updates) {
    const refs = Array.isArray(update.evidence_refs) ? update.evidence_refs : [];
    if (refs.some((ref) => ref === ordinal || ref === altOrdinal)) {
      const id = String(update.id ?? '').trim();
      if (id && !hints.includes(id)) {
        hints.push(id);
      }
    }
  }
  return hints;
}

function WizardDraftRow({
  index,
  row,
  skillHints,
  state,
  onChange,
}: {
  index: number;
  row: Record<string, unknown>;
  skillHints: string[];
  state: DraftRowState;
  onChange: (next: DraftRowState) => void;
}) {
  const [showSnapshot, setShowSnapshot] = useState(false);
  const summary = String(row.summary ?? '').trim();
  const snapshot = String(row.original_content ?? '').trim();
  const evidenceType = String(row.type ?? 'practice');
  return (
    <Card
      withBorder
      radius="md"
      p="xs"
      data-testid={`wizard-row-${index}`}
      style={{
        background: 'rgba(22, 38, 61, 0.55)',
        borderColor: 'rgba(220, 174, 85, 0.16)',
      }}
    >
      <Group wrap="nowrap" align="flex-start">
        <Checkbox
          aria-label={`入库 ${String(row.title ?? index)}`}
          checked={state.include}
          onChange={(event) =>
            onChange({ ...state, include: event.currentTarget.checked })
          }
        />
        <Stack gap={4} style={{ flex: 1, minWidth: 0 }}>
          <Group gap="xs" wrap="nowrap">
            <Text size="sm" style={{ flex: 1 }}>
              {String(row.title ?? '(无标题)')}
            </Text>
            <Badge size="xs" variant="light" color="brand">
              {typeLabel(evidenceType)}
            </Badge>
          </Group>
          {summary && (
            <Text size="xs" c="dimmed" lineClamp={3} data-testid={`wizard-row-summary-${index}`}>
              {summary}
            </Text>
          )}
          {skillHints.length > 0 && (
            <Group gap={4} wrap="wrap" data-testid={`wizard-row-skills-${index}`}>
              <Text size="xs" c="dimmed">
                技能建议:
              </Text>
              {skillHints.map((id) => (
                <Badge key={id} size="xs" variant="outline" color="brand">
                  {id}
                </Badge>
              ))}
            </Group>
          )}
          <Group gap="xs">
            <Select
              size="xs"
              w={120}
              data={STRENGTH_OPTIONS}
              value={state.strength}
              onChange={(value) => onChange({ ...state, strength: value ?? '' })}
              aria-label="分量"
            />
            {snapshot && (
              <Button
                size="compact-xs"
                variant="subtle"
                onClick={() => setShowSnapshot((value) => !value)}
                data-testid={`wizard-row-snapshot-${index}`}
              >
                {showSnapshot ? '收起快照 ▲' : '原文快照 ▼'}
              </Button>
            )}
          </Group>
          <Collapse in={showSnapshot}>
            <Text
              size="xs"
              c="dimmed"
              style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}
              data-testid={`wizard-row-snapshot-text-${index}`}
            >
              {snapshot.length > 600 ? `${snapshot.slice(0, 600)}…` : snapshot}
            </Text>
          </Collapse>
        </Stack>
      </Group>
    </Card>
  );
}

function CandidateInscriptionCard({
  candidate,
  onCrystallize,
  onClose,
}: {
  candidate: CrystallizeCandidate;
  onCrystallize: (key: string) => void;
  onClose: () => void;
}) {
  const [showSnapshot, setShowSnapshot] = useState(false);
  const blockers = candidate.blockers ?? [];
  return (
    <InscriptionCard
      title={candidate.title || candidate.id}
      aside={
        <Badge color="yellow" variant="light" size="sm">
          待结晶
        </Badge>
      }
      testId="candidate-detail"
    >
      <Stack gap={4}>
        <InscriptionRow label="完成日期">
          {candidate.completed_on || '—'}
        </InscriptionRow>
        <InscriptionRow label="所属项目">
          {candidate.project_id || '未关联项目'}
        </InscriptionRow>
        {candidate.tags && <InscriptionRow label="标签">{candidate.tags}</InscriptionRow>}
        {candidate.context && (
          <InscriptionRow label="背景">{candidate.context}</InscriptionRow>
        )}
        {candidate.why && <InscriptionRow label="为什么">{candidate.why}</InscriptionRow>}
        {candidate.outcome && (
          <InscriptionRow label="结果">{candidate.outcome}</InscriptionRow>
        )}
        {blockers.length > 0 && (
          <Alert color="orange" variant="light" mt="xs" data-testid="candidate-blockers">
            <Text size="xs">{blockers.join(' ')}</Text>
          </Alert>
        )}
        {candidate.snapshot && (
          <>
            <Button
              size="compact-xs"
              variant="subtle"
              color="gray"
              mt="xs"
              onClick={() => setShowSnapshot((value) => !value)}
              data-testid="candidate-snapshot-toggle"
            >
              {showSnapshot ? '收起原文快照 ▲' : '原文快照预览 ▼'}
            </Button>
            <Collapse in={showSnapshot}>
              <Text
                size="xs"
                style={{
                  color: inscription.dimColor,
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
                data-testid="candidate-snapshot"
              >
                {candidate.snapshot.length > 800
                  ? `${candidate.snapshot.slice(0, 800)}…`
                  : candidate.snapshot}
              </Text>
            </Collapse>
          </>
        )}
        <Group gap="xs" mt="md">
          <Button
            size="compact-sm"
            leftSection={<IconSparkles size={14} />}
            onClick={() => onCrystallize(candidate.id || candidate.title)}
            data-testid="candidate-crystallize"
          >
            结晶此任务
          </Button>
          <Button size="compact-sm" variant="subtle" color="gray" onClick={onClose}>
            关闭
          </Button>
        </Group>
      </Stack>
    </InscriptionCard>
  );
}

// --- Page ----------------------------------------------------------------------

export function EvidencePage() {
  const { name = '' } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const stageParam = (searchParams.get('stage') ?? 'review') as Stage;
  const stage: Stage = STAGES.some((item) => item.key === stageParam) ? stageParam : 'review';

  const [query, setQuery] = useState('');
  const [debouncedQuery] = useDebouncedValue(query, 300);
  const [selectedId, setSelectedId] = useState('');
  const [selectedRisk, setSelectedRisk] = useState<EvidenceStageRisk | null>(null);
  const [selectedCandidate, setSelectedCandidate] = useState<CrystallizeCandidate | null>(null);
  const [quickMode, setQuickMode] = useState(false);
  const [cursor, setCursor] = useState(0);
  const [wizardOpen, setWizardOpen] = useState(false);
  const [wizardPick, setWizardPick] = useState('');

  const openWizard = (pick = '') => {
    setWizardPick(pick);
    setWizardOpen(true);
  };

  const stages = useEvidenceStages(name);
  const isDesktop = useMediaQuery('(min-width: 62em)');
  const candidates = useCrystallizeCandidates(name);
  const list = useEvidenceReviewList(name, {
    status: STAGE_TO_LIST_STATUS[stage],
    q: debouncedQuery,
  });
  const reviewAction = useReviewEvidenceEntry(name);
  const editAction = useEditEvidenceEntry(name);

  const etag = list.data?.etag ?? '';
  const allItems = useMemo(() => list.data?.data.items ?? [], [list.data]);
  const items = useMemo(() => {
    if (stage === 'seated') {
      return allItems.filter((item) => (item.usage_count ?? 0) > 0);
    }
    return allItems;
  }, [allItems, stage]);
  const risks = useMemo(() => stages.data?.risks ?? [], [stages.data]);
  const candidateItems = useMemo(
    () => candidates.data?.items ?? [],
    [candidates.data],
  );

  const setStage = (next: Stage) => {
    setSearchParams(next === 'review' ? {} : { stage: next }, { replace: true });
    setSelectedId('');
    setSelectedRisk(null);
    setSelectedCandidate(null);
    setCursor(0);
  };

  // Deep link (?stage=<stage>&focus=<entry_id>, e.g. from the skill-tree
  // inscription card): preselect the entry once its stage list loads.
  const focusParam = searchParams.get('focus') ?? '';
  useEffect(() => {
    if (!focusParam || selectedId === focusParam) {
      return;
    }
    if (items.some((item) => item.id === focusParam)) {
      setSelectedId(focusParam);
      setSelectedRisk(null);
      setSelectedCandidate(null);
    }
  }, [focusParam, items, selectedId]);

  // Keyboard quick-review mode (j/k navigate, a accept, s skip, 1/2/3 grade).
  useEffect(() => {
    if (!quickMode || stage !== 'review' || items.length === 0) {
      return;
    }
    const handler = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      if (target && ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName)) {
        return;
      }
      const current = items[Math.min(cursor, items.length - 1)];
      if (event.key === 'j') {
        setCursor((value) => Math.min(value + 1, items.length - 1));
      } else if (event.key === 'k') {
        setCursor((value) => Math.max(value - 1, 0));
      } else if (event.key === 's') {
        setCursor((value) => Math.min(value + 1, items.length - 1));
      } else if (!current) {
        return;
      } else if (event.key === 'a') {
        reviewAction.mutate(
          { entryId: current.id, body: reviewBody('accept'), etag },
          { onSuccess: () => setCursor((value) => Math.max(0, value - 0)) },
        );
      } else if (['1', '2', '3'].includes(event.key)) {
        const strength = { '1': 'weak', '2': 'medium', '3': 'strong' }[event.key]!;
        editAction.mutate({
          entryId: current.id,
          body: { fields: { strength } },
          etag,
        });
      } else {
        return;
      }
      event.preventDefault();
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [quickMode, stage, items, cursor, etag, reviewAction, editAction]);

  const middlePending =
    stage === 'crystallize'
      ? candidates.isPending
      : stage === 'strengthen'
        ? stages.isPending
        : list.isPending;

  return (
    <Stack gap="md">
      <Group
        justify="space-between"
        wrap="wrap"
        bg="var(--mantine-color-body)"
        style={{
          position: 'sticky',
          top: 56,
          zIndex: 20,
          paddingBlock: 6,
        }}
      >
        <Title order={2}>{name} · 证据</Title>
        <Group gap="xs">
          {stage === 'review' && (
            <Tooltip label="j/k 移动 · a 接受 · s 跳过 · 1/2/3 定分量" withinPortal>
              <Button
                size="compact-sm"
                variant={quickMode ? 'light' : 'subtle'}
                color="brand"
                leftSection={<IconKeyboard size={14} />}
                onClick={() => setQuickMode((value) => !value)}
                data-testid="quick-review-toggle"
              >
                快速评审
              </Button>
            </Tooltip>
          )}
          <Button
            size="compact-sm"
            leftSection={<IconSparkles size={14} />}
            onClick={() => openWizard()}
            data-testid="open-crystallize-wizard"
          >
            从已完成任务结晶
          </Button>
        </Group>
      </Group>

      <Group align="flex-start" wrap="wrap" gap="md">
        <Box_StageColumn>
          <StageNav stages={stages.data} active={stage} onSelect={setStage} />
        </Box_StageColumn>

        <Stack gap="xs" style={{ flex: 1, minWidth: 280 }} data-testid="evidence-list-pane">
          <TextInput
            placeholder="按标题或 ID 搜索…"
            leftSection={<IconSearch size={14} />}
            value={query}
            onChange={(event) => setQuery(event.currentTarget.value)}
            aria-label="搜索证据"
          />
          {quickMode && stage === 'review' && (
            <Text size="xs" c="dimmed" data-testid="quick-review-hint">
              快速评审:j 下一条 · k 上一条 · a 接受 · s 跳过 · 1/2/3 定分量(弱/中/强)
            </Text>
          )}
          {middlePending ? (
            <Center py="xl">
              <Loader />
            </Center>
          ) : stage === 'crystallize' ? (
            candidateItems.length === 0 ? (
              <Text c="dimmed">没有待结晶的 Done 任务。</Text>
            ) : (
              candidateItems.map((task) => (
                <Card
                  key={task.id || task.title}
                  withBorder
                  radius="md"
                  p="xs"
                  onClick={() => {
                    setSelectedCandidate(task);
                    setSelectedId('');
                    setSelectedRisk(null);
                  }}
                  style={{
                    cursor: 'pointer',
                    background: 'rgba(22, 38, 61, 0.55)',
                    borderColor:
                      selectedCandidate && (selectedCandidate.id || selectedCandidate.title) === (task.id || task.title)
                        ? 'var(--mantine-color-brand-5)'
                        : 'rgba(220, 174, 85, 0.16)',
                  }}
                  data-testid={`candidate-${task.id || task.title}`}
                >
                  <Group justify="space-between" wrap="nowrap">
                    <Stack gap={2} style={{ minWidth: 0 }}>
                      <Text size="sm" lineClamp={1}>
                        {task.title}
                      </Text>
                      <Text size="xs" c="dimmed">
                        {task.completed_on || '无完成日期'}
                        {task.project_id ? ` · ${task.project_id}` : ''}
                        {(task.blockers ?? []).length > 0 && ' · 有阻断提示'}
                      </Text>
                    </Stack>
                    <Button
                      size="compact-xs"
                      variant="light"
                      onClick={(event) => {
                        event.stopPropagation();
                        openWizard(task.id || task.title);
                      }}
                    >
                      结晶
                    </Button>
                  </Group>
                </Card>
              ))
            )
          ) : stage === 'strengthen' ? (
            risks.length === 0 ? (
              <Text c="dimmed">没有待补强的技能。</Text>
            ) : (
              risks.map((risk) => (
                <Card
                  key={risk.skill_id}
                  withBorder
                  radius="md"
                  p="xs"
                  onClick={() => {
                    setSelectedRisk(risk);
                    setSelectedId('');
                    setSelectedCandidate(null);
                  }}
                  style={{
                    cursor: 'pointer',
                    background: 'rgba(22, 38, 61, 0.55)',
                    borderColor: selectedRisk?.skill_id === risk.skill_id
                      ? 'var(--mantine-color-brand-5)'
                      : 'rgba(220, 174, 85, 0.16)',
                  }}
                  data-testid={`risk-${risk.skill_id}`}
                >
                  <Group justify="space-between" wrap="nowrap">
                    <Stack gap={2} style={{ minWidth: 0 }}>
                      <Text size="sm">{risk.label || risk.skill_id}</Text>
                      <Text size="xs" c="dimmed" lineClamp={1}>
                        {risk.risk_reason}
                      </Text>
                    </Stack>
                    <Badge color="orange" variant="light" size="sm">
                      {risk.status}
                    </Badge>
                  </Group>
                </Card>
              ))
            )
          ) : items.length === 0 ? (
            <Text c="dimmed">当前过滤条件下没有待处理的证据。</Text>
          ) : (
            items.map((item, index) => (
              <EvidenceRow
                key={item.id}
                item={item}
                active={selectedId === item.id}
                cursor={quickMode && stage === 'review' && index === cursor}
                onSelect={() => {
                  setSelectedId(item.id);
                  setSelectedRisk(null);
                  setSelectedCandidate(null);
                }}
                onDeprecate={() =>
                  reviewAction.mutate({
                    entryId: item.id,
                    body: reviewBody('reject'),
                    etag,
                  })
                }
                onRestore={() =>
                  reviewAction.mutate({
                    entryId: item.id,
                    body: reviewBody('restore'),
                    etag,
                  })
                }
              />
            ))
          )}
        </Stack>

        <Stack
          gap="xs"
          w={{ base: '100%', md: 380 }}
          data-testid="evidence-detail-pane"
          style={
            isDesktop
              ? { position: 'sticky', top: 116, alignSelf: 'flex-start' }
              : undefined
          }
        >
          {selectedId ? (
            <EvidenceDetailCard
              profile={name}
              entryId={selectedId}
              etag={etag}
              onClose={() => setSelectedId('')}
            />
          ) : selectedCandidate ? (
            <CandidateInscriptionCard
              candidate={selectedCandidate}
              onCrystallize={(key) => openWizard(key)}
              onClose={() => setSelectedCandidate(null)}
            />
          ) : selectedRisk ? (
            <RiskDetailCard risk={selectedRisk} />
          ) : (
            <Card
              withBorder
              radius="md"
              p="lg"
              style={{
                background: 'rgba(22, 38, 61, 0.55)',
                borderColor: 'rgba(220, 174, 85, 0.16)',
              }}
            >
              <Group gap="xs">
                <IconLink size={16} color={chrome.gold} />
                <Text size="sm" c="dimmed">
                  选中一条证据查看铭文详情。
                </Text>
              </Group>
            </Card>
          )}
        </Stack>
      </Group>

      <CrystallizeWizard
        profile={name}
        opened={wizardOpen}
        initialPicked={wizardPick}
        onClose={() => setWizardOpen(false)}
        onApplied={() => {
          setStage('review');
        }}
      />
    </Stack>
  );
}

function Box_StageColumn({ children }: { children: ReactNode }) {
  const isDesktop = useMediaQuery('(min-width: 62em)');
  return (
    <Stack
      gap="xs"
      w={{ base: '100%', md: 200 }}
      style={
        isDesktop
          ? { position: 'sticky', top: 116, alignSelf: 'flex-start' }
          : undefined
      }
    >
      {children}
    </Stack>
  );
}

/** /evidence-review → /evidence?stage=review(旧链接不破坏)。 */
export function EvidenceReviewRedirect() {
  const { name = '' } = useParams();
  return (
    <Navigate
      to={`/p/${encodeURIComponent(name)}/evidence?stage=review`}
      replace
    />
  );
}
