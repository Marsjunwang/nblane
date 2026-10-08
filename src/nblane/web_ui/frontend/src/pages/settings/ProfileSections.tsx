// 档案 sections: settings that only affect the selected profile. Each section
// edits a local draft and saves once through the sticky SaveBar.

import { Autocomplete, Badge, Button, Center, Checkbox, Group, Loader, SegmentedControl, Select, SimpleGrid, Stack, Table, Text, TextInput } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconBook2, IconLanguage, IconRoute, IconSettings, IconTerminal2 } from '@tabler/icons-react';
import { useMemo, useState } from 'react';

import { usePatchProfileCodexSettings, usePatchProfileSettings, useProfileCodexSettings, useProfileSettings } from '../../api/hooks';
import { useResearchAIConfig } from '../../api/researchHooks';
import type { CodexSettingsPatch, ProfileSettingsPatch } from '../../api/types';
import { ErrorAlert, SaveBar, SettingsCard, preferenceString, settingString, useDraft, useReportDirty } from './shared';

type Preferences = Record<string, unknown> | undefined;
type ActionDraft = { backend: string; llm_model: string; codex_model: string; codex_effort: string };
type ActionMeta = { key: string; label: string; description: string };

/** Mirrors core/web_preferences.py AI_ACTION_DEFAULT_BACKENDS. */
const DEFAULT_BACKEND: Record<string, 'llm' | 'codex'> = {
  'research.paper_search_codex': 'codex',
  'research.paper_qa': 'codex',
  'research.paper_deep_read_codex': 'codex',
  'research.paper_compare_codex': 'codex',
};

/** Mirrors core/ai/backends.py _codex_reasoning_effort_for_action defaults. */
const DEFAULT_EFFORT: Record<string, string> = {
  'research.paper_deep_read_codex': 'high',
  'research.paper_search_codex': 'medium',
};

const EFFORT_LABELS: Record<string, string> = { low: '低', medium: '中', high: '高', xhigh: '极高' };
const EMPTY_DRAFT: ActionDraft = { backend: '', llm_model: '', codex_model: '', codex_effort: '' };

export const RESEARCH_ACTIONS: ActionMeta[] = [
  { key: 'research.paper_translate', label: '论文翻译', description: '段落、当前页和全文翻译中交给 AI 的部分。' },
  { key: 'research.paper_explain_selection', label: '选区解释', description: '解释 Reader 中选中的内容。' },
  { key: 'research.paper_qa', label: '论文问答', description: '针对当前论文进行问答。' },
  { key: 'research.paper_source_guide', label: '快速分析', description: '论文概览页的快速分析与导读。' },
  { key: 'research.paper_review_card', label: '阅读回顾卡', description: '整理阅读回顾，不写入证据池。' },
  { key: 'research.paper_deep_read_codex', label: '深度研读', description: '长文档深读，耗时数分钟。' },
  { key: 'research.paper_search_codex', label: '论文搜索', description: '扩展论文库的搜索与检索。' },
  { key: 'research.paper_compare_codex', label: '论文比较', description: '比较多篇论文的内容与差异。' },
  { key: 'research.paper_claim_extract', label: '观点提取', description: '按需提取论文观点，仅作为 AI 输出。' },
];

export const OTHER_ACTIONS: ActionMeta[] = [
  { key: 'kanban.task_alignment', label: '任务对齐', description: '把任务与技能、目标做关联建议。' },
  { key: 'kanban.subtasks', label: '子任务拆分', description: '将看板任务拆成可执行步骤。' },
  { key: 'project.suggest_refs', label: '项目引用建议', description: '为项目补充相关引用和关联。' },
  { key: 'dashboard.goal_skill_match', label: '目标与技能匹配', description: '分析目标与技能树的相关性。' },
  { key: 'dashboard.daily_brief', label: '每日简报', description: '生成当天的工作摘要。' },
  { key: 'evidence.crystallize', label: '证据结晶', description: '把完成的任务整理成证据草稿。' },
];

function actionDrafts(preferences: Preferences, actions: ActionMeta[]): Record<string, ActionDraft> {
  return Object.fromEntries(actions.map(({ key }) => [key, {
    backend: preferenceString(preferences, 'ai', 'actions', key, 'backend'),
    llm_model: preferenceString(preferences, 'ai', 'actions', key, 'llm_model'),
    codex_model: preferenceString(preferences, 'ai', 'actions', key, 'codex_model'),
    codex_effort: preferenceString(preferences, 'ai', 'actions', key, 'codex_effort'),
  }]));
}

function isCustomized(value: ActionDraft | undefined): boolean {
  return Boolean(value && (value.backend || value.llm_model || value.codex_model || value.codex_effort));
}

const backendLabel = (value: string) => (value === 'codex' ? 'Codex' : '兼容 API');

/**
 * One row per AI action. Rows that were customized when the section loaded
 * are listed; the rest hide behind 「显示全部」 so the table stays short.
 */
function ActionTable({ profile, actions, saved, value, onChange }: { profile: string; actions: ActionMeta[]; saved: Record<string, ActionDraft>; value: Record<string, ActionDraft>; onChange: (key: string, next: ActionDraft) => void }) {
  const [showAll, setShowAll] = useState(false);
  const defaults = useResearchAIConfig(profile);
  const customized = actions.filter(({ key }) => isCustomized(saved[key]));
  const rows = showAll ? actions : customized;
  const defaultModel = (backend: string) =>
    backend === 'codex' ? defaults.data?.codex_default_model || 'Codex CLI 默认' : defaults.data?.llm_default_model || 'AI 连接的默认模型';
  const defaultEffort = (key: string) => {
    const effort = DEFAULT_EFFORT[key] || defaults.data?.codex_default_effort || '';
    return effort ? `默认（${EFFORT_LABELS[effort] ?? effort}）` : '默认（Codex CLI）';
  };
  const suggestions = defaults.data?.codex_model_suggestions ?? [];
  return (
    <Stack gap="xs">
      {rows.length > 0 && (
        <Table verticalSpacing="xs" layout="fixed">
          <Table.Thead>
            <Table.Tr>
              <Table.Th w="30%">动作</Table.Th>
              <Table.Th w="22%">执行方式</Table.Th>
              <Table.Th>模型</Table.Th>
              <Table.Th w="18%">推理强度</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {rows.map((action) => {
              const draft = { ...EMPTY_DRAFT, ...value[action.key] };
              const fallback = DEFAULT_BACKEND[action.key] ?? 'llm';
              const effective = draft.backend || fallback;
              const modelKey = effective === 'codex' ? 'codex_model' : 'llm_model';
              return (
                <Table.Tr key={action.key}>
                  <Table.Td><Text size="sm" fw={600}>{action.label}</Text><Text size="xs" c="dimmed">{action.description}</Text></Table.Td>
                  <Table.Td>
                    <Select
                      aria-label={`${action.label}执行方式`}
                      size="xs"
                      value={draft.backend}
                      allowDeselect={false}
                      onChange={(next) => onChange(action.key, { ...draft, backend: next ?? '' })}
                      data={[{ value: '', label: `默认（${backendLabel(fallback)}）` }, { value: 'llm', label: '兼容 API' }, { value: 'codex', label: 'Codex' }]}
                    />
                  </Table.Td>
                  <Table.Td>
                    {effective === 'codex' ? (
                      <Autocomplete
                        aria-label={`${action.label}模型`}
                        size="xs"
                        placeholder={`默认：${defaultModel(effective)}`}
                        value={draft.codex_model}
                        data={suggestions}
                        onChange={(next) => onChange(action.key, { ...draft, codex_model: next })}
                      />
                    ) : (
                      <TextInput
                        aria-label={`${action.label}模型`}
                        size="xs"
                        placeholder={`默认：${defaultModel(effective)}`}
                        value={draft[modelKey]}
                        onChange={(event) => onChange(action.key, { ...draft, [modelKey]: event.currentTarget.value })}
                      />
                    )}
                  </Table.Td>
                  <Table.Td>
                    {effective === 'codex' ? (
                      <Select
                        aria-label={`${action.label}推理强度`}
                        size="xs"
                        value={draft.codex_effort}
                        allowDeselect={false}
                        onChange={(next) => onChange(action.key, { ...draft, codex_effort: next ?? '' })}
                        data={[
                          { value: '', label: defaultEffort(action.key) },
                          ...['low', 'medium', 'high', 'xhigh'].map((effort) => ({ value: effort, label: EFFORT_LABELS[effort] })),
                        ]}
                      />
                    ) : (
                      <Text size="xs" c="dimmed">仅 Codex</Text>
                    )}
                  </Table.Td>
                </Table.Tr>
              );
            })}
          </Table.Tbody>
        </Table>
      )}
      <Group gap="xs">
        {!showAll && customized.length === 0 && <Text size="sm" c="dimmed">全部 {actions.length} 个动作都跟随默认。</Text>}
        {actions.length > customized.length && (
          <Button size="xs" variant="subtle" onClick={() => setShowAll((current) => !current)}>
            {showAll ? '只看已修改' : `显示全部 ${actions.length} 项`}
          </Button>
        )}
      </Group>
    </Stack>
  );
}

function useProfileSave(profile: string, title: string) {
  const save = usePatchProfileSettings(profile);
  return {
    save,
    run: (patch: ProfileSettingsPatch) =>
      save.mutate(patch, { onSuccess: () => notifications.show({ title, message: profile, color: 'green' }) }),
  };
}

function Loading({ query }: { query: { isPending: boolean; isError: boolean; error: Error | null } }) {
  if (query.isPending) return <Center py="xl"><Loader /></Center>;
  if (query.isError) return <ErrorAlert error={query.error} />;
  return null;
}

// --- 通用 -------------------------------------------------------------------------

export function ProfileGeneralSection({ profile }: { profile: string }) {
  const preferences = useProfileSettings(profile);
  const value = preferences.data?.preferences;
  const source = useMemo(() => ({
    ui_lang: preferenceString(value, 'ai', 'llm', 'ui_lang'),
    reply_lang: preferenceString(value, 'ai', 'llm', 'reply_lang'),
  }), [value]);
  const { draft, setDraft, dirty, reset } = useDraft(source);
  const { save, run } = useProfileSave(profile, '通用设置已保存');
  useReportDirty(dirty);
  if (!preferences.data) return <Loading query={preferences} />;
  return (
    <Stack gap="lg">
      <SettingsCard icon={<IconLanguage size={22} />} title="语言" description="界面文案和 AI 回复使用的语言。">
        <SimpleGrid cols={{ base: 1, sm: 2 }}>
          <Select label="界面语言" placeholder="跟随部署默认" value={draft.ui_lang || null} onChange={(next) => setDraft({ ...draft, ui_lang: next ?? '' })} data={[{ value: 'zh', label: '中文' }, { value: 'en', label: 'English' }]} clearable />
          <Select label="AI 回复语言" placeholder="自动" value={draft.reply_lang || null} onChange={(next) => setDraft({ ...draft, reply_lang: next ?? '' })} data={[{ value: 'auto', label: '自动' }, { value: 'zh', label: '中文' }, { value: 'en', label: 'English' }]} clearable />
        </SimpleGrid>
      </SettingsCard>
      <SaveBar dirty={dirty} saving={save.isPending} error={save.error} onDiscard={reset} onSave={() => run({ ai: { llm: draft } })} />
    </Stack>
  );
}

// --- 研究与阅读 ----------------------------------------------------------------------

const READER_DEFAULTS = {
  default_mode: 'pdf', default_scale: 'fit-width', default_side_panel: 'collapsed',
  default_active_tab: 'notes', default_left_rail: 'open', default_left_tab: 'outline',
  default_translation_source: true, default_target_lang: 'zh', default_translation_layout: 'flow',
  compare_split_ratio: 50, panel_width: 340,
};
type ReaderDefaults = typeof READER_DEFAULTS;

const LOCAL_ROUTE_SCOPES = [
  { key: 'selection', label: '选区翻译', description: '划词、选中句子或单段。' },
  { key: 'visible', label: '当前页翻译', description: 'Reader 中可见页面的段落。' },
  { key: 'full', label: '全文翻译', description: '整篇论文；本地 1.8B 较慢，建议用 AI。' },
];
const LOCAL_ROUTE_DEFAULTS: Record<string, string> = { selection: 'local', visible: 'local', full: 'ai' };

export function ProfileResearchSection({ profile }: { profile: string }) {
  const preferences = useProfileSettings(profile);
  const value = preferences.data?.preferences;
  const source = useMemo(() => {
    const research = value?.research as Record<string, unknown> | undefined;
    const reader = research?.reader && typeof research.reader === 'object' ? (research.reader as Partial<ReaderDefaults>) : {};
    return {
      reader: { ...READER_DEFAULTS, ...reader } as ReaderDefaults,
      routes: Object.fromEntries(LOCAL_ROUTE_SCOPES.map(({ key }) => [key, preferenceString(value, 'ai', 'local_translation', key) || LOCAL_ROUTE_DEFAULTS[key]])) as Record<string, string>,
      actions: actionDrafts(value, RESEARCH_ACTIONS),
    };
  }, [value]);
  const { draft, setDraft, dirty, reset } = useDraft(source);
  const { save, run } = useProfileSave(profile, '研究与阅读设置已保存');
  useReportDirty(dirty);
  if (!preferences.data) return <Loading query={preferences} />;
  const reader = draft.reader;
  const setReader = (key: keyof ReaderDefaults, next: string | number | boolean) => setDraft({ ...draft, reader: { ...reader, [key]: next } });
  return (
    <Stack gap="lg">
      <SettingsCard icon={<IconBook2 size={22} />} title="Reader 默认值" description="新打开一篇论文时的初始状态；论文已保存的阅读位置和模式永远优先。">
        <SimpleGrid cols={{ base: 1, sm: 2 }}>
          <Select label="默认模式" value={reader.default_mode} allowDeselect={false} onChange={(next) => setReader('default_mode', next ?? 'pdf')} data={[{ value: 'pdf', label: 'PDF' }, { value: 'translation', label: '翻译' }, { value: 'compare', label: '对照' }]} />
          <Select label="默认缩放" value={reader.default_scale} allowDeselect={false} onChange={(next) => setReader('default_scale', next ?? 'fit-width')} data={[{ value: 'fit-width', label: '适合宽度' }, { value: 'fit-page', label: '适合页面' }, { value: 'actual', label: '实际大小' }]} />
          <Select label="左侧导航栏" value={reader.default_left_rail} allowDeselect={false} onChange={(next) => setReader('default_left_rail', next ?? 'open')} data={[{ value: 'open', label: '默认展开' }, { value: 'collapsed', label: '默认收起' }]} />
          <Select label="左侧默认页签" value={reader.default_left_tab} allowDeselect={false} onChange={(next) => setReader('default_left_tab', next ?? 'outline')} data={[{ value: 'outline', label: '大纲' }, { value: 'thumbnails', label: '缩略图' }]} />
          <Select label="右侧面板" value={reader.default_side_panel} allowDeselect={false} onChange={(next) => setReader('default_side_panel', next ?? 'collapsed')} data={[{ value: 'collapsed', label: '默认收起' }, { value: 'open', label: '默认展开' }]} />
          <Select label="右侧默认页签" value={reader.default_active_tab} allowDeselect={false} onChange={(next) => setReader('default_active_tab', next ?? 'notes')} data={[{ value: 'notes', label: '笔记' }, { value: 'translation', label: '翻译' }, { value: 'review', label: '回顾' }]} />
          <TextInput label="右侧面板宽度" type="number" min={260} max={520} value={String(reader.panel_width)} onChange={(event) => setReader('panel_width', Number(event.currentTarget.value) || 340)} description="260–520 px" />
          <TextInput label="对照分栏比例" type="number" min={20} max={80} value={String(reader.compare_split_ratio)} onChange={(event) => setReader('compare_split_ratio', Number(event.currentTarget.value) || 50)} description="左侧原文占比 20–80" />
        </SimpleGrid>
      </SettingsCard>
      <SettingsCard icon={<IconRoute size={22} />} title="翻译" description="单词始终先查本地词典。本地模型由管理员在「系统 → 本地服务」启用；没启用或失败时一律走 AI。">
        <SimpleGrid cols={{ base: 1, sm: 2 }}>
          <TextInput label="目标语言" value={reader.default_target_lang} onChange={(event) => setReader('default_target_lang', event.currentTarget.value)} placeholder="zh" />
          <Select label="译文布局" value={reader.default_translation_layout} allowDeselect={false} onChange={(next) => setReader('default_translation_layout', next ?? 'flow')} data={[{ value: 'flow', label: '流式' }, { value: 'overlay', label: '叠加' }]} />
        </SimpleGrid>
        <Checkbox label="译文中默认显示原文" checked={reader.default_translation_source} onChange={(event) => setReader('default_translation_source', event.currentTarget.checked)} />
        <SimpleGrid cols={{ base: 1, sm: 3 }}>
          {LOCAL_ROUTE_SCOPES.map((scope) => (
            <Stack key={scope.key} gap={4}>
              <Text size="sm" fw={600}>{scope.label}</Text>
              <SegmentedControl aria-label={`${scope.label}翻译方式`} size="xs" value={draft.routes[scope.key]} onChange={(next) => setDraft({ ...draft, routes: { ...draft.routes, [scope.key]: next } })} data={[{ value: 'local', label: '本地模型' }, { value: 'ai', label: 'AI' }]} />
              <Text size="xs" c="dimmed">{scope.description}</Text>
            </Stack>
          ))}
        </SimpleGrid>
      </SettingsCard>
      <SettingsCard icon={<IconSettings size={22} />} title="研究 AI" description="论文库、论文概览和 Reader 里的 AI 动作用什么执行、用哪个模型；留空跟随默认。">
        <ActionTable profile={profile} actions={RESEARCH_ACTIONS} saved={source.actions} value={draft.actions} onChange={(key, next) => setDraft({ ...draft, actions: { ...draft.actions, [key]: next } })} />
      </SettingsCard>
      <SaveBar
        dirty={dirty}
        saving={save.isPending}
        error={save.error}
        onDiscard={reset}
        onSave={() => run({ ai: { local_translation: draft.routes, actions: draft.actions }, research: { reader: draft.reader } })}
      />
    </Stack>
  );
}

// --- AI 路由 ----------------------------------------------------------------------

export function ProfileAIRoutingSection({ profile }: { profile: string }) {
  const preferences = useProfileSettings(profile);
  const codex = useProfileCodexSettings(profile);
  const value = preferences.data?.preferences;
  const actionsSource = useMemo(() => actionDrafts(value, OTHER_ACTIONS), [value]);
  const codexValue = codex.data?.settings;
  const codexSource = useMemo(() => ({
    bin_path: settingString(codexValue, 'bin_path'),
    cloud_env_id: settingString(codexValue, 'cloud_env_id'),
    model: settingString(codexValue, 'model'),
    branch: settingString(codexValue, 'branch'),
    timeout_seconds: settingString(codexValue, 'timeout_seconds'),
  }), [codexValue]);
  const actions = useDraft(actionsSource);
  const codexDraft = useDraft(codexSource);
  const saveActions = usePatchProfileSettings(profile);
  const saveCodex = usePatchProfileCodexSettings(profile);
  const dirty = actions.dirty || codexDraft.dirty;
  useReportDirty(dirty);
  if (!preferences.data) return <Loading query={preferences} />;
  if (!codex.data) return <Loading query={codex} />;

  const save = async () => {
    try {
      if (actions.dirty) await saveActions.mutateAsync({ ai: { actions: actions.draft } });
      if (codexDraft.dirty) {
        const c = codexDraft.draft;
        const patch: CodexSettingsPatch = {
          bin_path: c.bin_path || null,
          cloud_env_id: c.cloud_env_id || null,
          model: c.model || null,
          branch: c.branch || null,
          timeout_seconds: c.timeout_seconds ? Number(c.timeout_seconds) : null,
        };
        await saveCodex.mutateAsync(patch);
      }
      notifications.show({ title: 'AI 路由已保存', message: profile, color: 'green' });
    } catch {
      // The SaveBar shows the mutation error.
    }
  };
  const c = codexDraft.draft;
  const setCodex = (key: keyof typeof c, next: string) => codexDraft.setDraft({ ...c, [key]: next });
  return (
    <Stack gap="lg">
      <SettingsCard icon={<IconSettings size={22} />} title="工作流 AI" description="看板、项目、首页和证据中的 AI 动作用什么执行、用哪个模型；研究相关的在「研究与阅读」。">
        <ActionTable profile={profile} actions={OTHER_ACTIONS} saved={actionsSource} value={actions.draft} onChange={(key, next) => actions.setDraft({ ...actions.draft, [key]: next })} />
      </SettingsCard>
      <SettingsCard icon={<IconTerminal2 size={22} />} title="Codex 运行参数" description="选了 Codex 的动作使用这些参数；留空跟随 Codex CLI 默认。认证仍由 Codex CLI 管理。">
        <SimpleGrid cols={{ base: 1, sm: 2 }}>
          <TextInput label="默认模型" value={c.model} onChange={(event) => setCodex('model', event.currentTarget.value)} placeholder="Codex CLI 默认" />
          <TextInput label="超时（秒）" type="number" min={5} value={c.timeout_seconds} onChange={(event) => setCodex('timeout_seconds', event.currentTarget.value)} />
          <TextInput label="Codex 路径" value={c.bin_path} onChange={(event) => setCodex('bin_path', event.currentTarget.value)} placeholder="codex" />
          <TextInput label="Cloud 环境 ID" value={c.cloud_env_id} onChange={(event) => setCodex('cloud_env_id', event.currentTarget.value)} />
          <TextInput label="分支名" value={c.branch} onChange={(event) => setCodex('branch', event.currentTarget.value)} placeholder="main" />
        </SimpleGrid>
        {codexValue && Object.values(codexSource).some(Boolean) && <Group gap={6}><Badge size="xs" variant="light">已自定义</Badge><Text size="xs" c="dimmed">清空字段并保存即可恢复默认。</Text></Group>}
      </SettingsCard>
      <SaveBar
        dirty={dirty}
        saving={saveActions.isPending || saveCodex.isPending}
        error={saveActions.error ?? saveCodex.error}
        onDiscard={() => { actions.reset(); codexDraft.reset(); }}
        onSave={() => void save()}
      />
    </Stack>
  );
}
