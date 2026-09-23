// 新建项目 — plain (non-plan) case creation, ported from the retired
// ProjectBoardPage CreateCaseCard so no capability is lost with the old
// page. Habit-plan creation lives in NewPlanModal instead.

import {
  Button,
  Group,
  Modal,
  MultiSelect,
  Select,
  Stack,
  Textarea,
  TextInput,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconPlus } from '@tabler/icons-react';
import { useEffect, useState } from 'react';

import { useCreateProjectCase, useProjectBoard } from '../../api/hooks';
import type { ProjectRefOption } from '../../api/types';
import { MutationErrorAlert } from '../ConflictAlert';
import { KIND_LABELS } from './lanes';

const VISIBILITY_LABELS: Record<string, string> = {
  private: '私有',
  public: '公开',
};

function labeledData(labels: Record<string, string>, keys: string[]) {
  return keys.map((key) => ({ value: key, label: labels[key] ?? key }));
}

function goalOptions(options: ProjectRefOption[] | undefined) {
  return (options ?? []).map((option) => ({ value: option.id, label: option.label || option.id }));
}

export function NewProjectModal({
  profile,
  opened,
  onClose,
  onCreated,
}: {
  profile: string;
  opened: boolean;
  onClose: () => void;
  /** Called with the new case id (so the page can open its edit drawer). */
  onCreated?: (caseId: string) => void;
}) {
  const board = useProjectBoard(profile);
  const create = useCreateProjectCase(profile);
  const [title, setTitle] = useState('');
  const [caseId, setCaseId] = useState('');
  const [kind, setKind] = useState('internal');
  const [visibility, setVisibility] = useState('private');
  const [summary, setSummary] = useState('');
  const [goalRefs, setGoalRefs] = useState<string[]>([]);

  useEffect(() => {
    if (opened) {
      setTitle('');
      setCaseId('');
      setKind('internal');
      setVisibility('private');
      setSummary('');
      setGoalRefs([]);
    }
  }, [opened]);

  const submit = () => {
    if (!title.trim()) {
      return;
    }
    create.mutate(
      {
        body: {
          title: title.trim(),
          id: caseId.trim(),
          status: 'active',
          kind,
          visibility,
          summary: summary.trim(),
          goal_refs: goalRefs,
          evidence_refs: [],
          habit_id: '',
        },
        etag: board.data?.etag ?? '',
      },
      {
        onSuccess: (result) => {
          notifications.show({
            color: 'green',
            title: '已创建',
            message: `项目「${result.case?.title || title}」已创建。`,
          });
          onCreated?.(result.case?.id ?? '');
          onClose();
        },
      },
    );
  };

  return (
    <Modal opened={opened} onClose={onClose} centered title="新建项目" size="lg">
      <Stack gap="sm" data-testid="create-case-form">
        <Group grow align="flex-start">
          <TextInput
            label="标题"
            value={title}
            onChange={(event) => setTitle(event.currentTarget.value)}
            required
          />
          <TextInput
            label="ID（留空自动生成）"
            value={caseId}
            onChange={(event) => setCaseId(event.currentTarget.value)}
          />
        </Group>
        <Group grow align="flex-start">
          <Select
            label="类型"
            data={labeledData(KIND_LABELS, Object.keys(KIND_LABELS))}
            value={kind}
            onChange={(value) => setKind(value ?? 'internal')}
          />
          <Select
            label="可见性"
            data={labeledData(VISIBILITY_LABELS, Object.keys(VISIBILITY_LABELS))}
            value={visibility}
            onChange={(value) => setVisibility(value ?? 'private')}
          />
        </Group>
        <Textarea
          label="摘要"
          value={summary}
          onChange={(event) => setSummary(event.currentTarget.value)}
          minRows={2}
        />
        <MultiSelect
          label="关联目标"
          data={goalOptions(board.data?.data.options?.goals)}
          value={goalRefs}
          onChange={setGoalRefs}
        />
        <MutationErrorAlert
          error={create.error}
          title="创建失败"
          onRefetch={() => void board.refetch()}
        />
        <Group justify="flex-end">
          <Button variant="subtle" onClick={onClose}>
            取消
          </Button>
          <Button
            leftSection={<IconPlus size={14} />}
            onClick={submit}
            loading={create.isPending}
            disabled={!title.trim()}
          >
            创建项目
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}
