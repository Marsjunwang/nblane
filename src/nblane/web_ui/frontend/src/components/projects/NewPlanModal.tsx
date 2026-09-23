// 新建计划 — one lightweight modal over the plan-templates API: pick a
// built-in template (or re-run one from the profile's usage history, most
// recent first), optionally override title/start, instantiate into a
// habit-plan case + habit.

import {
  Badge,
  Button,
  Group,
  Modal,
  Stack,
  Text,
  TextInput,
  UnstyledButton,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconLeaf } from '@tabler/icons-react';
import { useEffect, useState } from 'react';

import { useInstantiatePlanTemplate, usePlanTemplates } from '../../api/hooks';
import { MutationErrorAlert } from '../ConflictAlert';
import { boardPalette } from './palette';

export function NewPlanModal({
  profile,
  opened,
  onClose,
}: {
  profile: string;
  opened: boolean;
  onClose: () => void;
}) {
  const templates = usePlanTemplates(profile);
  const instantiate = useInstantiatePlanTemplate(profile);
  const [selectedId, setSelectedId] = useState('');
  const [title, setTitle] = useState('');
  const [start, setStart] = useState('');

  // Reset the form each time the modal opens; default to the first builtin.
  useEffect(() => {
    if (!opened) {
      return;
    }
    const first = templates.data?.data.builtin?.[0];
    setSelectedId((current) => current || first?.id || '');
    setTitle('');
    setStart('');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened, templates.data]);

  const builtin = templates.data?.data.builtin ?? [];
  const history = templates.data?.data.history ?? [];
  const selected = builtin.find((template) => template.id === selectedId);

  const pick = (templateId: string, templateTitle: string) => {
    setSelectedId(templateId);
    if (!title || builtin.some((template) => template.title === title)) {
      setTitle(templateTitle);
    }
  };

  const submit = () => {
    if (!selectedId) {
      return;
    }
    instantiate.mutate(
      {
        body: {
          template_id: selectedId,
          title: title.trim(),
          start: start.trim(),
          habit_id: '',
          goal_refs: [],
        },
        etag: templates.data?.etag ?? '',
      },
      {
        onSuccess: ({ data }) => {
          notifications.show({
            color: 'green',
            title: '计划已创建',
            message:
              `已创建「${data.case?.title || title}」` +
              (data.warnings?.length ? `;注意:${data.warnings.join('、')}` : ''),
          });
          onClose();
        },
      },
    );
  };

  return (
    <Modal opened={opened} onClose={onClose} centered title="新建计划" size="lg">
      <Stack gap="sm" data-testid="new-plan-modal">
        <Text size="sm" c="dimmed">
          选择一个习惯计划模板,实例化为项目泳道 + 习惯打卡。
        </Text>
        <Stack gap="xs">
          {builtin.map((template) => (
            <UnstyledButton
              key={template.id}
              onClick={() => pick(template.id, template.title ?? '')}
              data-testid={`plan-template-${template.id}`}
              style={{
                display: 'block',
                padding: '8px 12px',
                borderRadius: 8,
                border: `1px solid ${
                  selectedId === template.id ? boardPalette.selectedBorder : 'var(--mantine-color-gray-3)'
                }`,
                background:
                  selectedId === template.id ? 'rgba(234, 197, 126, 0.08)' : undefined,
              }}
            >
              <Group justify="space-between" wrap="nowrap">
                <div style={{ minWidth: 0 }}>
                  <Text fw={600} size="sm">
                    {template.title || template.id}
                  </Text>
                  {template.summary && (
                    <Text size="xs" c="dimmed" lineClamp={1}>
                      {template.summary}
                    </Text>
                  )}
                </div>
                <Group gap={4} style={{ flexShrink: 0 }}>
                  <Badge size="sm" variant="light" color="brand">
                    {template.duration_days} 天
                  </Badge>
                  <Badge size="sm" variant="outline" color="gray">
                    {template.milestones?.length ?? 0} 里程碑
                  </Badge>
                </Group>
              </Group>
            </UnstyledButton>
          ))}
        </Stack>
        {history.length > 0 && (
          <Stack gap={4}>
            <Text size="xs" c="dimmed">
              最近使用
            </Text>
            <Group gap={4} wrap="wrap">
              {history.map((entry) => (
                <Badge
                  key={`${entry.template_id}-${entry.used_at}`}
                  size="lg"
                  variant={selectedId === entry.template_id ? 'filled' : 'outline'}
                  color="gray"
                  leftSection={<IconLeaf size={12} />}
                  style={{ cursor: 'pointer' }}
                  onClick={() => pick(entry.template_id, entry.title)}
                  data-testid={`plan-history-${entry.template_id}`}
                >
                  {entry.title || entry.template_id}
                  {entry.used_at ? ` · ${entry.used_at.slice(0, 10)}` : ''}
                </Badge>
              ))}
            </Group>
          </Stack>
        )}
        <Group grow align="flex-start">
          <TextInput
            label="计划标题(留空用模板名)"
            value={title}
            onChange={(event) => setTitle(event.currentTarget.value)}
            placeholder={selected?.title ?? ''}
            data-testid="plan-title-input"
          />
          <TextInput
            label="开始日期(留空为今天)"
            type="date"
            value={start}
            onChange={(event) => setStart(event.currentTarget.value)}
            data-testid="plan-start-input"
          />
        </Group>
        <MutationErrorAlert
          error={instantiate.error}
          title="创建计划失败"
          onRefetch={() => void templates.refetch()}
        />
        <Group justify="flex-end">
          <Button variant="subtle" onClick={onClose}>
            取消
          </Button>
          <Button
            onClick={submit}
            loading={instantiate.isPending}
            disabled={!selectedId}
            data-testid="plan-instantiate-submit"
          >
            创建计划
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}
