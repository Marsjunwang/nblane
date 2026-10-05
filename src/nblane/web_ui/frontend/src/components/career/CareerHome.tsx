import { Alert, Badge, Button, Center, Group, Image, Loader, Modal, Paper, Stack, Table, Text, TextInput, Title } from '@mantine/core';
import { IconBriefcase, IconFileText, IconPencil, IconPlus } from '@tabler/icons-react';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { createCareerDraft, useCareerWorkspace } from '../../api/hooks';
import type { CareerDraft } from '../../api/types';
import { ExportMenu } from './CareerShared';
import { careerResumePath, careerTargetPath, cleanDraftId, resumeStats } from './resumeModel';

function formatDate(seconds: number): string {
  return seconds ? new Date(seconds * 1000).toLocaleDateString('zh-CN') : '';
}

function scoreBadge(draft: CareerDraft) {
  const score = draft.analysis?.score;
  if (typeof score !== 'number') return <Text size="xs" c="dimmed">未匹配</Text>;
  const color = score >= 75 ? 'teal' : score >= 50 ? 'yellow' : 'red';
  return (
    <Badge variant="light" color={color}>
      匹配 {score}
    </Badge>
  );
}

/** Career workspace home: the master resume card and one row per target job. */
export function CareerHome({ profile }: { profile: string }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const career = useCareerWorkspace(profile);
  const [createOpen, setCreateOpen] = useState(false);
  const [target, setTarget] = useState('');
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState('');

  if (career.isPending) {
    return (
      <Center py="xl">
        <Loader />
      </Center>
    );
  }
  if (career.isError || !career.data) {
    return (
      <Alert color="red" title="求职工作台加载失败">
        {career.error?.message}
      </Alert>
    );
  }
  const data = career.data;
  const resume = data.resume;

  const create = () => {
    const id = cleanDraftId(target);
    if (!id) return;
    setCreating(true);
    setCreateError('');
    // A new target starts as a copy of the master resume; tailoring is explicit.
    createCareerDraft(profile, { target: id, markdown: data.resume_markdown })
      .then((draft) => {
        void queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'career'] });
        navigate(careerTargetPath(profile, draft.id));
      })
      .catch((err: unknown) => setCreateError(err instanceof Error ? err.message : String(err)))
      .finally(() => setCreating(false));
  };

  return (
    <Stack gap="lg" data-testid="career-workspace" maw={1100} mx="auto" w="100%">
      <Group justify="space-between" align="flex-end">
        <div>
          <Title order={2}>
            <IconBriefcase size={24} style={{ verticalAlign: 'middle', marginRight: 8 }} />
            求职工作台
          </Title>
          <Text size="sm" c="dimmed" mt={4}>
            一份主简历，按岗位做 JD 匹配和定制版本。AI 只读简历、JD 和你的证据库，不会改动主简历。
          </Text>
        </div>
      </Group>

      <Paper withBorder radius="md" p="lg" data-testid="career-resume-card">
        <Group justify="space-between" align="flex-start" wrap="nowrap">
          <Group align="flex-start" wrap="nowrap" gap="md">
            {data.photo_url && <Image src={data.photo_url} alt="简历照片" w={54} h={72} radius="sm" fit="cover" />}
            <Stack gap={4}>
              <Group gap="xs">
                <IconFileText size={18} />
                <Text fw={700}>主简历</Text>
                <Badge variant="light" color={resume.visibility === 'public' ? 'teal' : 'gray'}>
                  {resume.visibility === 'public' ? '公开站可见' : '私有'}
                </Badge>
              </Group>
              {data.has_resume ? (
                <>
                  <Text size="sm">
                    {resume.basics.name}
                    {resume.basics.title ? ` · ${resume.basics.title}` : ''}
                  </Text>
                  <Text size="xs" c="dimmed" data-testid="career-resume-stats">
                    {resumeStats(resume)}
                  </Text>
                </>
              ) : (
                <Text size="sm" c="dimmed">
                  还没有内容。导入已有简历（Markdown / HTML / PDF / DOCX），或直接按段落填写。
                </Text>
              )}
            </Stack>
          </Group>
          <Group gap="xs" wrap="nowrap">
            {data.has_resume && <ExportMenu profile={profile} pdfAvailable={data.pdf_available} source={{}} />}
            <Button component={Link} to={careerResumePath(profile)} leftSection={<IconPencil size={15} />} data-testid="career-edit-resume">
              {data.has_resume ? '编辑' : '开始填写'}
            </Button>
          </Group>
        </Group>
      </Paper>

      <Stack gap="sm">
        <Group justify="space-between">
          <Text fw={700}>目标岗位</Text>
          <Button
            leftSection={<IconPlus size={15} />}
            variant="light"
            onClick={() => setCreateOpen(true)}
            disabled={!data.has_resume}
            data-testid="career-new-target"
          >
            新建岗位
          </Button>
        </Group>
        {data.drafts.length === 0 ? (
          <Paper withBorder radius="md" p="lg">
            <Text size="sm" c="dimmed">
              {data.has_resume
                ? '还没有目标岗位。新建一个，粘贴 JD，做匹配分析并生成定制简历。'
                : '先完善主简历，再为具体岗位做匹配。'}
            </Text>
          </Paper>
        ) : (
          <Table highlightOnHover verticalSpacing="sm" data-testid="career-target-table">
            <Table.Thead>
              <Table.Tr>
                <Table.Th>岗位</Table.Th>
                <Table.Th>JD</Table.Th>
                <Table.Th>匹配</Table.Th>
                <Table.Th>更新</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {data.drafts.map((draft) => (
                <Table.Tr
                  key={draft.id}
                  style={{ cursor: 'pointer' }}
                  onClick={() => navigate(careerTargetPath(profile, draft.id))}
                  data-testid="career-target-row"
                >
                  <Table.Td>
                    <Text fw={600} size="sm">
                      {draft.target}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Text size="xs" c="dimmed" lineClamp={1} maw={420}>
                      {draft.jd_text || '未填写'}
                    </Text>
                  </Table.Td>
                  <Table.Td>{scoreBadge(draft)}</Table.Td>
                  <Table.Td>
                    <Text size="xs" c="dimmed">
                      {formatDate(draft.updated_at)}
                    </Text>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        )}
      </Stack>

      <Modal opened={createOpen} onClose={() => setCreateOpen(false)} title="新建目标岗位" centered>
        <Stack gap="sm">
          <TextInput
            label="岗位标识"
            description="用作文件名，如：智元-VLA算法"
            value={target}
            onChange={(event) => setTarget(event.currentTarget.value)}
            onKeyDown={(event) => event.key === 'Enter' && create()}
            data-autofocus
            data-testid="career-new-target-name"
          />
          {target && cleanDraftId(target) !== target.trim() && (
            <Text size="xs" c="dimmed">
              将保存为：{cleanDraftId(target)}
            </Text>
          )}
          {createError && (
            <Alert color="red" p="xs">
              <Text size="xs">{createError}</Text>
            </Alert>
          )}
          <Group justify="flex-end">
            <Button variant="default" onClick={() => setCreateOpen(false)}>
              取消
            </Button>
            <Button onClick={create} loading={creating} disabled={!cleanDraftId(target)} data-testid="career-new-target-confirm">
              创建
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  );
}
