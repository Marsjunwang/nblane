import {
  ActionIcon,
  Alert,
  Box,
  Button,
  Center,
  CloseButton,
  FileButton,
  Group,
  Image,
  Loader,
  Paper,
  SegmentedControl,
  SimpleGrid,
  Stack,
  Switch,
  Text,
  Textarea,
  TextInput,
  Tooltip,
} from '@mantine/core';
import { useHotkeys, useMediaQuery } from '@mantine/hooks';
import {
  IconArrowDown,
  IconArrowLeft,
  IconArrowUp,
  IconFileImport,
  IconPhoto,
  IconPlus,
  IconRefresh,
  IconTrash,
} from '@tabler/icons-react';
import { useQueryClient } from '@tanstack/react-query';
import { useState, type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';

import { careerResumeApiUrl, contentMediaUrl, saveCareerResume, uploadCareerPhoto, useCareerWorkspace } from '../../api/hooks';
import type { CareerWorkspaceResponse, ResumeDoc, ResumeRecord } from '../../api/types';
import { ExportMenu, ResumePreview, SaveBadge } from './CareerShared';
import { ImportResumeModal } from './ImportResumeModal';
import {
  RECORD_FIELDS,
  careerHomePath,
  emptyRecord,
  linesToList,
  listToLines,
  mergeImported,
  moveItem,
  sectionTitle,
  type RecordSection,
} from './resumeModel';
import { useAutosave } from './useAutosave';

const TOP_BAR_HEIGHT = 52;
const FORM_WIDTH = 600;

type Edit = (update: (previous: ResumeDoc) => ResumeDoc) => void;

function Section({
  doc,
  sectionKey,
  edit,
  children,
  action,
}: {
  doc: ResumeDoc;
  sectionKey: string;
  edit: Edit;
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <Paper withBorder radius="md" p="md" data-testid={`resume-section-${sectionKey}`}>
      <Group justify="space-between" mb="sm" wrap="nowrap">
        <TextInput
          variant="unstyled"
          aria-label="段落标题"
          value={sectionTitle(doc, sectionKey)}
          onChange={(event) => {
            const value = event.currentTarget.value;
            edit((previous) => ({ ...previous, section_titles: { ...previous.section_titles, [sectionKey]: value } }));
          }}
          styles={{ input: { fontWeight: 700, fontSize: 15 } }}
          style={{ flex: 1 }}
        />
        {action}
      </Group>
      {children}
    </Paper>
  );
}

function RowTools({
  index,
  count,
  onMove,
  onRemove,
  label,
}: {
  index: number;
  count: number;
  onMove: (delta: number) => void;
  onRemove: () => void;
  label: string;
}) {
  return (
    <Group gap={2} wrap="nowrap">
      <ActionIcon size="sm" variant="subtle" color="gray" aria-label={`上移${label}`} disabled={index === 0} onClick={() => onMove(-1)}>
        <IconArrowUp size={14} />
      </ActionIcon>
      <ActionIcon size="sm" variant="subtle" color="gray" aria-label={`下移${label}`} disabled={index === count - 1} onClick={() => onMove(1)}>
        <IconArrowDown size={14} />
      </ActionIcon>
      <ActionIcon size="sm" variant="subtle" color="red" aria-label={`删除${label}`} onClick={onRemove}>
        <IconTrash size={14} />
      </ActionIcon>
    </Group>
  );
}

function RecordCard({
  section,
  record,
  index,
  count,
  onChange,
  onMove,
  onRemove,
}: {
  section: RecordSection;
  record: ResumeRecord;
  index: number;
  count: number;
  onChange: (record: ResumeRecord) => void;
  onMove: (delta: number) => void;
  onRemove: () => void;
}) {
  const fields = RECORD_FIELDS[section];
  const set = (key: string, value: unknown) => onChange({ ...record, [key]: value });
  const groups = record.groups ?? [];
  const setGroup = (groupIndex: number, patch: Partial<{ label: string; bullets: string[] }>) =>
    set(
      'groups',
      groups.map((group, i) => (i === groupIndex ? { ...group, ...patch } : group)),
    );
  const detailed = section !== 'education' || record.bullets.length > 0 || Boolean(record.summary);
  return (
    <Paper withBorder radius="sm" p="sm" bg="var(--mantine-color-dark-7)" data-testid={`resume-record-${section}`}>
      <Stack gap="xs">
        <Group gap="xs" align="flex-end" wrap="nowrap">
          <TextInput
            size="xs"
            label={fields.orgLabel}
            value={String(record[fields.org] ?? '')}
            onChange={(event) => set(fields.org, event.currentTarget.value)}
            style={{ flex: 3 }}
          />
          <TextInput
            size="xs"
            label={fields.roleLabel}
            value={String(record[fields.role] ?? '')}
            onChange={(event) => set(fields.role, event.currentTarget.value)}
            style={{ flex: 3 }}
          />
          <TextInput size="xs" label="开始" placeholder="2022/08" value={record.start} onChange={(event) => set('start', event.currentTarget.value)} style={{ flex: 2 }} />
          <TextInput size="xs" label="结束" placeholder="至今" value={record.end} onChange={(event) => set('end', event.currentTarget.value)} style={{ flex: 2 }} />
          <RowTools index={index} count={count} onMove={onMove} onRemove={onRemove} label="这一条" />
        </Group>
        {detailed && (
          <>
            <Textarea
              size="xs"
              label="条目（每行一条，支持 **加粗**）"
              autosize
              minRows={2}
              maxRows={12}
              value={listToLines(record.bullets)}
              onChange={(event) => set('bullets', linesToList(event.currentTarget.value))}
            />
            {groups.map((group, groupIndex) => (
              <Paper key={groupIndex} withBorder radius="sm" p="xs">
                <Group gap="xs" wrap="nowrap" mb={6}>
                  <TextInput
                    size="xs"
                    placeholder="分组标题，如：具身大模型 / VLA(主线)"
                    aria-label="分组标题"
                    value={group.label}
                    onChange={(event) => setGroup(groupIndex, { label: event.currentTarget.value })}
                    style={{ flex: 1 }}
                  />
                  <RowTools
                    index={groupIndex}
                    count={groups.length}
                    onMove={(delta) => set('groups', moveItem(groups, groupIndex, delta))}
                    onRemove={() => set('groups', groups.filter((_, i) => i !== groupIndex))}
                    label="分组"
                  />
                </Group>
                <Textarea
                  size="xs"
                  aria-label="分组条目"
                  autosize
                  minRows={2}
                  maxRows={12}
                  value={listToLines(group.bullets)}
                  onChange={(event) => setGroup(groupIndex, { bullets: linesToList(event.currentTarget.value) })}
                />
              </Paper>
            ))}
          </>
        )}
        <Group gap="xs">
          {section !== 'education' && (
            <Button size="compact-xs" variant="subtle" leftSection={<IconPlus size={12} />} onClick={() => set('groups', [...groups, { label: '', bullets: [] }])}>
              加分组
            </Button>
          )}
          {!detailed && (
            <Button size="compact-xs" variant="subtle" leftSection={<IconPlus size={12} />} onClick={() => set('bullets', [''])}>
              加条目
            </Button>
          )}
        </Group>
      </Stack>
    </Paper>
  );
}

function RecordSectionEditor({ doc, section, edit }: { doc: ResumeDoc; section: RecordSection; edit: Edit }) {
  const records = doc[section];
  const setRecords = (next: ResumeRecord[]) => edit((previous) => ({ ...previous, [section]: next }));
  return (
    <Section
      doc={doc}
      sectionKey={section}
      edit={edit}
      action={
        <Button size="compact-xs" variant="light" leftSection={<IconPlus size={12} />} onClick={() => setRecords([...records, emptyRecord(section)])} data-testid={`resume-add-${section}`}>
          添加
        </Button>
      }
    >
      <Stack gap="xs">
        {records.length === 0 && (
          <Text size="xs" c="dimmed">
            暂无。点「添加」新增一条，空的段落不会出现在简历里。
          </Text>
        )}
        {records.map((record, index) => (
          <RecordCard
            key={index}
            section={section}
            record={record}
            index={index}
            count={records.length}
            onChange={(next) => setRecords(records.map((item, i) => (i === index ? next : item)))}
            onMove={(delta) => setRecords(moveItem(records, index, delta))}
            onRemove={() => setRecords(records.filter((_, i) => i !== index))}
          />
        ))}
      </Stack>
    </Section>
  );
}

function ResumeForm({
  profile,
  doc,
  photoUrl,
  edit,
}: {
  profile: string;
  doc: ResumeDoc;
  photoUrl: string;
  edit: Edit;
}) {
  const [photoBusy, setPhotoBusy] = useState(false);
  const [photoError, setPhotoError] = useState('');
  const basics = doc.basics;
  const setBasics = (key: string, value: string) => edit((previous) => ({ ...previous, basics: { ...previous.basics, [key]: value } }));
  const upload = (file: File | null) => {
    if (!file) return;
    setPhotoBusy(true);
    setPhotoError('');
    uploadCareerPhoto(profile, file)
      .then((result) => setBasics('photo', result.path))
      .catch((err: unknown) => setPhotoError(err instanceof Error ? err.message : String(err)))
      .finally(() => setPhotoBusy(false));
  };
  return (
    <Stack gap="md" data-testid="resume-form">
      <Paper withBorder radius="md" p="md" data-testid="resume-section-basics">
        <Text fw={700} size="sm" mb="sm">
          基本信息
        </Text>
        <Group align="flex-start" wrap="nowrap" gap="md">
          <Stack gap={6} align="center" style={{ width: 96, flexShrink: 0 }}>
            <Box
              style={{
                width: 90,
                height: 120,
                borderRadius: 6,
                overflow: 'hidden',
                border: '1px solid var(--mantine-color-dark-4)',
                background: 'var(--mantine-color-dark-6)',
              }}
            >
              {photoUrl ? (
                <Image src={photoUrl} alt="简历照片" w={90} h={120} fit="cover" data-testid="resume-photo" />
              ) : (
                <Center h="100%">
                  <IconPhoto size={26} color="var(--mantine-color-dark-2)" />
                </Center>
              )}
            </Box>
            <FileButton accept="image/jpeg,image/png,image/webp" onChange={upload}>
              {(props) => (
                <Button {...props} size="compact-xs" variant="light" loading={photoBusy} data-testid="resume-photo-upload">
                  {photoUrl ? '更换照片' : '上传照片'}
                </Button>
              )}
            </FileButton>
            {basics.photo && (
              <Button size="compact-xs" variant="subtle" color="gray" onClick={() => setBasics('photo', '')}>
                不放照片
              </Button>
            )}
          </Stack>
          <SimpleGrid cols={2} spacing="xs" verticalSpacing="xs" style={{ flex: 1 }}>
            <TextInput size="xs" label="姓名" required value={basics.name} onChange={(event) => setBasics('name', event.currentTarget.value)} data-testid="resume-name" />
            <TextInput size="xs" label="求职头衔" placeholder="具身智能算法工程师" value={basics.title} onChange={(event) => setBasics('title', event.currentTarget.value)} data-testid="resume-title" />
            <TextInput size="xs" label="电话" value={basics.phone} onChange={(event) => setBasics('phone', event.currentTarget.value)} />
            <TextInput size="xs" label="邮箱" value={basics.email} onChange={(event) => setBasics('email', event.currentTarget.value)} />
            <TextInput size="xs" label="所在地" value={basics.location} onChange={(event) => setBasics('location', event.currentTarget.value)} />
            <TextInput size="xs" label="网站 / GitHub" value={basics.website} onChange={(event) => setBasics('website', event.currentTarget.value)} />
            <TextInput
              size="xs"
              label="抬头补充"
              description="年龄、学历等，显示在联系方式前，用 | 分隔"
              value={basics.tagline}
              onChange={(event) => setBasics('tagline', event.currentTarget.value)}
              style={{ gridColumn: 'span 2' }}
            />
          </SimpleGrid>
        </Group>
        {photoError && (
          <Text size="xs" c="red" mt={6}>
            {photoError}
          </Text>
        )}
        <Switch
          mt="sm"
          size="xs"
          label="在公开个人站显示简历页（不含照片）"
          checked={doc.visibility === 'public'}
          onChange={(event) => {
            const checked = event.currentTarget.checked;
            edit((previous) => ({ ...previous, visibility: checked ? 'public' : 'private' }));
          }}
        />
      </Paper>

      <Section doc={doc} sectionKey="summary" edit={edit}>
        <Textarea
          size="sm"
          aria-label="个人概要"
          autosize
          minRows={3}
          maxRows={10}
          value={doc.summary}
          onChange={(event) => {
            const value = event.currentTarget.value;
            edit((previous) => ({ ...previous, summary: value }));
          }}
          data-testid="resume-summary"
        />
      </Section>

      <Section
        doc={doc}
        sectionKey="skills"
        edit={edit}
        action={
          <Button
            size="compact-xs"
            variant="light"
            leftSection={<IconPlus size={12} />}
            onClick={() => edit((previous) => ({ ...previous, skill_groups: [...previous.skill_groups, { label: '', text: '' }] }))}
          >
            添加分类
          </Button>
        }
      >
        <Stack gap="xs">
          {doc.skill_groups.map((group, index) => (
            <Group key={index} gap="xs" wrap="nowrap" align="flex-start">
              <TextInput
                size="xs"
                placeholder="分类"
                aria-label="技能分类"
                value={group.label}
                onChange={(event) => {
                  const value = event.currentTarget.value;
                  edit((previous) => ({
                    ...previous,
                    skill_groups: previous.skill_groups.map((item, i) => (i === index ? { ...item, label: value } : item)),
                  }));
                }}
                style={{ width: 130, flexShrink: 0 }}
              />
              <Textarea
                size="xs"
                aria-label="技能"
                autosize
                minRows={1}
                maxRows={4}
                value={group.text}
                onChange={(event) => {
                  const value = event.currentTarget.value;
                  edit((previous) => ({
                    ...previous,
                    skill_groups: previous.skill_groups.map((item, i) => (i === index ? { ...item, text: value } : item)),
                  }));
                }}
                style={{ flex: 1 }}
              />
              <RowTools
                index={index}
                count={doc.skill_groups.length}
                onMove={(delta) => edit((previous) => ({ ...previous, skill_groups: moveItem(previous.skill_groups, index, delta) }))}
                onRemove={() => edit((previous) => ({ ...previous, skill_groups: previous.skill_groups.filter((_, i) => i !== index) }))}
                label="分类"
              />
            </Group>
          ))}
          <Textarea
            size="xs"
            label={doc.skill_groups.length ? '其他技能（每行一条）' : '技能（每行一条；需要分类可点「添加分类」）'}
            autosize
            minRows={1}
            maxRows={6}
            value={listToLines(doc.skills)}
            onChange={(event) => {
              const value = event.currentTarget.value;
              edit((previous) => ({ ...previous, skills: linesToList(value) }));
            }}
          />
        </Stack>
      </Section>

      <RecordSectionEditor doc={doc} section="experiences" edit={edit} />
      <RecordSectionEditor doc={doc} section="projects" edit={edit} />
      <RecordSectionEditor doc={doc} section="education" edit={edit} />
      <RecordSectionEditor doc={doc} section="outputs" edit={edit} />

      <Section doc={doc} sectionKey="honors" edit={edit}>
        <Textarea
          size="xs"
          aria-label="荣誉与其他"
          description="每行一条"
          autosize
          minRows={2}
          maxRows={8}
          value={listToLines(doc.honors)}
          onChange={(event) => {
            const value = event.currentTarget.value;
            edit((previous) => ({ ...previous, honors: linesToList(value) }));
          }}
        />
      </Section>

      {doc.extra_sections.map((extra, index) => (
        <Paper key={index} withBorder radius="md" p="md">
          <Group justify="space-between" mb="xs" wrap="nowrap">
            <TextInput
              variant="unstyled"
              aria-label="自定义段落标题"
              value={extra.title}
              onChange={(event) => {
                const value = event.currentTarget.value;
                edit((previous) => ({
                  ...previous,
                  extra_sections: previous.extra_sections.map((item, i) => (i === index ? { ...item, title: value } : item)),
                }));
              }}
              styles={{ input: { fontWeight: 700, fontSize: 15 } }}
              style={{ flex: 1 }}
            />
            <CloseButton
              aria-label="删除自定义段落"
              onClick={() => edit((previous) => ({ ...previous, extra_sections: previous.extra_sections.filter((_, i) => i !== index) }))}
            />
          </Group>
          <Textarea
            size="xs"
            aria-label="自定义段落内容（Markdown）"
            autosize
            minRows={2}
            maxRows={10}
            value={extra.body}
            onChange={(event) => {
              const value = event.currentTarget.value;
              edit((previous) => ({
                ...previous,
                extra_sections: previous.extra_sections.map((item, i) => (i === index ? { ...item, body: value } : item)),
              }));
            }}
          />
        </Paper>
      ))}
      <Button
        variant="subtle"
        size="xs"
        leftSection={<IconPlus size={14} />}
        onClick={() => edit((previous) => ({ ...previous, extra_sections: [...previous.extra_sections, { title: '其他', body: '' }] }))}
        style={{ alignSelf: 'flex-start' }}
      >
        添加自定义段落
      </Button>
    </Stack>
  );
}

function ResumeEditorInner({ profile, data }: { profile: string; data: CareerWorkspaceResponse }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const wide = useMediaQuery('(min-width: 1100px)', true);
  const [mobileView, setMobileView] = useState<'form' | 'preview'>('form');
  const [importOpen, setImportOpen] = useState(false);
  const autosave = useAutosave<ResumeDoc>({
    initial: data.resume,
    etag: data.resume_etag,
    save: async (resume, etag, isAutosave) => {
      const result = await saveCareerResume(profile, resume, etag, isAutosave);
      // Keep the overview fresh without remounting the form.
      queryClient.setQueryData(['profiles', profile, 'career'], result);
      return result.resume_etag;
    },
    keepalive: (resume) => ({ url: careerResumeApiUrl(profile), method: 'PUT', body: JSON.stringify({ resume }) }),
  });
  const doc = autosave.value;
  const edit: Edit = (update) => autosave.edit(update);
  const photoUrl = doc.basics.photo ? contentMediaUrl(profile, doc.basics.photo) : '';

  useHotkeys([['mod+S', () => void autosave.flush()]], []);

  const back = async () => {
    await autosave.flush();
    navigate(careerHomePath(profile));
  };

  const topBar = (
    <Group
      justify="space-between"
      wrap="nowrap"
      gap="sm"
      px="md"
      h={TOP_BAR_HEIGHT}
      style={{
        position: 'sticky',
        top: 'var(--app-shell-header-height, 56px)',
        zIndex: 20,
        background: 'var(--mantine-color-body)',
        borderBottom: '1px solid var(--mantine-color-dark-5)',
      }}
    >
      <Group gap="xs" wrap="nowrap" style={{ minWidth: 0 }}>
        <Button size="xs" variant="subtle" color="gray" leftSection={<IconArrowLeft size={15} />} onClick={() => void back()} data-testid="career-back">
          求职工作台
        </Button>
        <Text fw={600} size="sm" truncate>
          主简历
        </Text>
        <SaveBadge state={autosave.state} savedAt={autosave.savedAt} testid="resume-save-state" />
      </Group>
      <Group gap="xs" wrap="nowrap">
        {!wide && (
          <SegmentedControl
            size="xs"
            value={mobileView}
            onChange={(value) => setMobileView(value as 'form' | 'preview')}
            data={[
              { value: 'form', label: '编辑' },
              { value: 'preview', label: '预览' },
            ]}
          />
        )}
        <Button size="xs" variant="default" leftSection={<IconFileImport size={15} />} onClick={() => setImportOpen(true)} data-testid="resume-import">
          导入
        </Button>
        <ExportMenu profile={profile} pdfAvailable={data.pdf_available} source={{}} beforeExport={autosave.flush} />
      </Group>
    </Group>
  );

  return (
    <Box data-testid="resume-editor" style={{ minHeight: 'calc(100vh - 56px)' }}>
      {topBar}
      {autosave.state === 'conflict' && (
        <Alert color="orange" m="md" title="简历已在别处修改">
          <Group justify="space-between">
            <Text size="sm">为避免覆盖，已暂停自动保存。刷新会载入最新版本，本页未保存的修改会丢失。</Text>
            <Button size="xs" variant="default" leftSection={<IconRefresh size={14} />} onClick={() => window.location.reload()}>
              刷新
            </Button>
          </Group>
        </Alert>
      )}
      {autosave.state === 'error' && (
        <Alert color="red" m="md" title="保存失败">
          {autosave.error}
        </Alert>
      )}
      <Group align="flex-start" wrap="nowrap" gap={0}>
        {(wide || mobileView === 'form') && (
          <Box p="md" style={{ width: wide ? FORM_WIDTH : '100%', flexShrink: 0 }}>
            <ResumeForm profile={profile} doc={doc} photoUrl={photoUrl} edit={edit} />
          </Box>
        )}
        {(wide || mobileView === 'preview') && (
          <Box
            p="md"
            style={{
              flex: 1,
              minWidth: 0,
              position: wide ? 'sticky' : undefined,
              top: `calc(var(--app-shell-header-height, 56px) + ${TOP_BAR_HEIGHT}px)`,
              height: `calc(100vh - 56px - ${TOP_BAR_HEIGHT}px)`,
            }}
          >
            <Tooltip label="与导出的 HTML / PDF 使用同一渲染" position="top-end" withinPortal>
              <Text size="xs" c="dimmed" mb={6}>
                A4 预览
              </Text>
            </Tooltip>
            <ResumePreview profile={profile} resume={doc} height="calc(100% - 24px)" />
          </Box>
        )}
      </Group>
      <ImportResumeModal
        profile={profile}
        opened={importOpen}
        aiAvailable={data.ai_available}
        hasResume={data.has_resume}
        onClose={() => setImportOpen(false)}
        onApply={(imported) => {
          edit((previous) => mergeImported(previous, imported));
          setImportOpen(false);
        }}
      />
    </Box>
  );
}

/** Structured master-resume editor (form + live A4 preview, autosaved). */
export function ResumeEditor({ profile }: { profile: string }) {
  const career = useCareerWorkspace(profile);
  if (career.isPending) {
    return (
      <Center py="xl">
        <Loader />
      </Center>
    );
  }
  if (career.isError || !career.data) {
    return (
      <Alert color="red" m="md" title="简历加载失败">
        {career.error?.message}
      </Alert>
    );
  }
  return <ResumeEditorInner profile={profile} data={career.data} />;
}
