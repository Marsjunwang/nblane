import { Alert, Badge, Button, FileButton, Group, Loader, Modal, SegmentedControl, Stack, Text, Textarea } from '@mantine/core';
import { IconFileImport, IconSparkles, IconUpload } from '@tabler/icons-react';
import { useEffect, useRef, useState } from 'react';

import { importCareerFile, importCareerText } from '../../api/hooks';
import type { CareerImportPreview, CareerStructureResult, ResumeDoc } from '../../api/types';
import { runContentJob, type ContentJobHandle } from '../content/contentJobs';
import { ResumePreview } from './CareerShared';
import { resumeStats } from './resumeModel';

const METHOD_LABELS: Record<string, string> = {
  markdown: '按 Markdown 结构识别',
  html: '按 HTML 结构识别',
  llm: 'AI 识别',
  text: '纯文本（未识别出结构）',
};

/**
 * Upload / paste → preview → explicit target. Nothing is written until the
 * user picks 写入主简历 (merged into the form, then autosaved).
 */
export function ImportResumeModal({
  profile,
  opened,
  aiAvailable,
  hasResume,
  onClose,
  onApply,
}: {
  profile: string;
  opened: boolean;
  aiAvailable: boolean;
  hasResume: boolean;
  onClose: () => void;
  onApply: (resume: ResumeDoc) => void;
}) {
  const [mode, setMode] = useState<'file' | 'paste'>('file');
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState('');
  const [error, setError] = useState('');
  const [preview, setPreview] = useState<CareerImportPreview | null>(null);
  const [resume, setResume] = useState<ResumeDoc | null>(null);
  const [method, setMethod] = useState('');
  const jobRef = useRef<ContentJobHandle<CareerStructureResult> | null>(null);

  useEffect(() => {
    if (!opened) {
      jobRef.current?.cancel();
      setPreview(null);
      setResume(null);
      setError('');
      setText('');
      setBusy(false);
    }
  }, [opened]);

  const accept = (result: CareerImportPreview) => {
    setPreview(result);
    setResume(result.resume ?? null);
    setMethod(result.method);
    setError(result.error && !result.text ? result.error : '');
  };

  const run = (task: Promise<CareerImportPreview>) => {
    setBusy(true);
    setError('');
    task
      .then(accept)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setBusy(false));
  };

  const recognize = () => {
    if (!preview?.text) return;
    setBusy(true);
    setError('');
    const job = runContentJob<CareerStructureResult>(profile, 'career-structure', { text: preview.text }, setProgress);
    jobRef.current = job;
    job.result
      .then((result) => {
        setResume(result.resume);
        setMethod('llm');
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setBusy(false));
  };

  return (
    <Modal opened={opened} onClose={onClose} title="导入简历" size="xl" centered>
      <Stack gap="md" data-testid="career-import">
        {!preview ? (
          <>
            <SegmentedControl
              value={mode}
              onChange={(value) => setMode(value as 'file' | 'paste')}
              data={[
                { value: 'file', label: '上传文件' },
                { value: 'paste', label: '粘贴文本' },
              ]}
            />
            {mode === 'file' ? (
              <Stack gap="xs" align="flex-start">
                <Text size="sm" c="dimmed">
                  支持 Markdown、HTML、PDF、DOCX、TXT。Markdown / HTML 会按标题结构直接识别字段；PDF / DOCX 先提取文字，再由 AI 识别。
                </Text>
                <FileButton accept=".md,.markdown,.html,.htm,.pdf,.docx,.txt" onChange={(file) => file && run(importCareerFile(profile, file))}>
                  {(props) => (
                    <Button {...props} leftSection={busy ? <Loader size={14} /> : <IconUpload size={16} />} disabled={busy} data-testid="career-import-file">
                      选择文件
                    </Button>
                  )}
                </FileButton>
              </Stack>
            ) : (
              <Stack gap="xs">
                <Textarea
                  aria-label="简历文本"
                  placeholder="粘贴简历 Markdown、HTML 或纯文本"
                  autosize
                  minRows={10}
                  maxRows={20}
                  value={text}
                  onChange={(event) => setText(event.currentTarget.value)}
                  data-testid="career-import-text"
                />
                <Group justify="flex-end">
                  <Button onClick={() => run(importCareerText(profile, text))} disabled={!text.trim() || busy} loading={busy} data-testid="career-import-parse">
                    识别
                  </Button>
                </Group>
              </Stack>
            )}
          </>
        ) : (
          <>
            <Group justify="space-between">
              <Group gap="xs">
                <Badge variant="light" color={resume ? 'teal' : 'gray'} style={{ textTransform: 'none' }}>
                  {METHOD_LABELS[method] ?? method}
                </Badge>
                {preview.filename && (
                  <Text size="xs" c="dimmed">
                    {preview.filename}
                  </Text>
                )}
              </Group>
              <Button size="xs" variant="subtle" onClick={() => setPreview(null)}>
                重新选择
              </Button>
            </Group>
            {resume ? (
              <>
                <Text size="sm" data-testid="career-import-stats">
                  {resume.basics.name} · {resumeStats(resume)}
                </Text>
                <ResumePreview profile={profile} resume={resume} height={460} />
              </>
            ) : (
              <Stack gap="xs">
                <Text size="sm" c="dimmed">
                  没有识别出简历结构。{aiAvailable ? '可以让 AI 按字段整理（只搬运原文，不改写）。' : '未配置 LLM，可改用 Markdown 粘贴。'}
                </Text>
                <Textarea value={preview.text} readOnly autosize minRows={6} maxRows={14} aria-label="提取的文字" />
                {aiAvailable && (
                  <Button
                    leftSection={busy ? <Loader size={14} /> : <IconSparkles size={16} />}
                    onClick={recognize}
                    disabled={busy}
                    variant="light"
                    data-testid="career-import-ai"
                  >
                    {busy ? progress || 'AI 识别中…' : 'AI 识别字段'}
                  </Button>
                )}
              </Stack>
            )}
            {resume && (
              <>
                {hasResume && (
                  <Alert color="yellow" p="xs">
                    <Text size="xs">写入后会替换主简历的内容（照片和公开设置保留）。之前的版本可在 Git 备份里找回。</Text>
                  </Alert>
                )}
                <Group justify="flex-end">
                  <Button variant="default" onClick={onClose}>
                    取消
                  </Button>
                  <Button leftSection={<IconFileImport size={16} />} onClick={() => onApply(resume)} data-testid="career-import-apply">
                    写入主简历
                  </Button>
                </Group>
              </>
            )}
          </>
        )}
        {error && (
          <Alert color="red" p="xs">
            <Text size="xs">{error}</Text>
          </Alert>
        )}
      </Stack>
    </Modal>
  );
}
