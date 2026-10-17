import { Alert, Box, Button, FileButton, Group, Image, Loader, Paper, SimpleGrid, Stack, Text, TextInput } from '@mantine/core';
import { IconCheck, IconPhotoAi, IconTrash, IconX } from '@tabler/icons-react';
import { useEffect, useRef, useState } from 'react';

import { contentCoverCandidateUrl, discardCoverCandidate, usePromoteCoverCandidate } from '../../api/hooks';
import type { ContentCoverCandidate, ContentCoverResult } from '../../api/types';
import { runContentJob, type ContentJobHandle } from './contentJobs';

/**
 * AI cover generation: images are staged as candidates (blog/.candidates);
 * 「用作封面」 moves one into the post's media and sets the draft cover,
 * 「丢弃」 deletes it. The post file is only written by the next autosave.
 */
export function AICoverGenerator({
  profile,
  slug,
  enabled,
  draft,
  onUseCover,
}: {
  profile: string;
  slug: string;
  enabled: boolean;
  draft: { title: string; summary: string; tags: string[]; body: string };
  onUseCover: (path: string) => void;
}) {
  const [brief, setBrief] = useState('');
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState('');
  const [error, setError] = useState('');
  const [candidates, setCandidates] = useState<ContentCoverCandidate[]>([]);
  const [referenceImage, setReferenceImage] = useState('');
  const [referenceImageName, setReferenceImageName] = useState('');
  const jobRef = useRef<ContentJobHandle<ContentCoverResult> | null>(null);
  const promote = usePromoteCoverCandidate(profile);

  useEffect(() => () => jobRef.current?.cancel(), []);

  const generate = () => {
    jobRef.current?.cancel();
    setRunning(true);
    setError('');
    setProgress('');
    const job = runContentJob<ContentCoverResult>(
      profile,
      'content-cover',
      { slug, brief, title: draft.title, summary: draft.summary, tags: draft.tags, body: draft.body, reference_image: referenceImage },
      setProgress,
    );
    jobRef.current = job;
    job.result
      .then((result) => setCandidates((previous) => [...result.candidates, ...previous]))
      .catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setRunning(false));
  };

  const use = (candidate: ContentCoverCandidate) =>
    promote.mutate(
      { slug, candidatePath: candidate.candidate_path },
      {
        onSuccess: (result) => {
          setCandidates((previous) => previous.filter((item) => item.candidate_path !== candidate.candidate_path));
          onUseCover(result.path);
        },
        onError: (err) => setError(err.message),
      },
    );

  const discard = (candidate: ContentCoverCandidate) => {
    setCandidates((previous) => previous.filter((item) => item.candidate_path !== candidate.candidate_path));
    void discardCoverCandidate(profile, candidate.candidate_path).catch(() => undefined);
  };

  const handleReferenceImageSelected = (file: File | null) => {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      const dataUrl = e.target?.result as string;
      setReferenceImage(dataUrl);
      setReferenceImageName(file.name);
      setError('');
    };
    reader.onerror = () => {
      setError('上传参考图失败，请重试。');
    };
    reader.readAsDataURL(file);
  };

  return (
    <Paper withBorder p="sm" radius="md" data-testid="content-ai-cover">
      <Stack gap="sm">
        <Text size="sm" fw={600}>
          AI 生成封面
        </Text>
        {!enabled ? (
          <Text size="xs" c="dimmed">
            未配置图像服务（VISUAL_API_KEY / DASHSCOPE_API_KEY），封面生成不可用。
          </Text>
        ) : (
          <>
            <TextInput
              size="xs"
              placeholder="画面描述（可选），如：夜色中的机械臂，冷色调"
              aria-label="封面画面描述"
              value={brief}
              onChange={(event) => setBrief(event.currentTarget.value)}
            />
            <Group gap="xs" grow>
              <Button
                size="xs"
                variant="light"
                leftSection={running ? <Loader size={12} /> : <IconPhotoAi size={15} />}
                onClick={generate}
                disabled={running}
                data-testid="content-ai-cover-run"
              >
                {running ? '生成中…' : '生成封面'}
              </Button>
              <FileButton
                accept="image/*"
                onChange={handleReferenceImageSelected}
                disabled={running}
              >
                {(props) => (
                  <Button
                    size="xs"
                    variant="default"
                    {...props}
                    disabled={running}
                    title="上传一张已生成的图，作为参考进行迭代修改"
                  >
                    {referenceImageName ? `已上传: ${referenceImageName}` : '参考图'}
                  </Button>
                )}
              </FileButton>
              {referenceImage && (
                <Button
                  size="xs"
                  variant="subtle"
                  color="gray"
                  leftSection={<IconX size={13} />}
                  onClick={() => {
                    setReferenceImage('');
                    setReferenceImageName('');
                  }}
                  disabled={running}
                >
                  清除
                </Button>
              )}
            </Group>
            <Text size="xs" c="dimmed">
              {running ? progress || '约 30–90 秒' : referenceImage ? '✓ 参考图已选择，基于此图迭代生成' : '基于标题、摘要和标签生成，图中不含文字。'}
            </Text>
          </>
        )}
        {error && (
          <Alert color="red" p="xs">
            <Text size="xs">{error}</Text>
          </Alert>
        )}
        {candidates.length > 0 && (
          <SimpleGrid cols={1} spacing="xs">
            {candidates.map((candidate) => (
              <Box key={candidate.candidate_path} data-testid="content-ai-cover-candidate">
                <Image
                  src={contentCoverCandidateUrl(profile, candidate.candidate_path)}
                  radius="sm"
                  alt="封面候选"
                  fit="cover"
                  mah={170}
                />
                <Group gap="xs" mt={6} grow>
                  <Button
                    size="compact-xs"
                    leftSection={<IconCheck size={13} />}
                    onClick={() => use(candidate)}
                    loading={promote.isPending}
                    data-testid="content-ai-cover-use"
                  >
                    用作封面
                  </Button>
                  <Button
                    size="compact-xs"
                    variant="default"
                    leftSection={<IconTrash size={13} />}
                    onClick={() => discard(candidate)}
                  >
                    丢弃
                  </Button>
                </Group>
              </Box>
            ))}
          </SimpleGrid>
        )}
      </Stack>
    </Paper>
  );
}
