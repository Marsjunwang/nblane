import {
  Alert,
  Badge,
  Button,
  Card,
  Group,
  List,
  Progress,
  Stack,
  Text,
  Textarea,
  Title,
} from '@mantine/core';
import { IconInfoCircle } from '@tabler/icons-react';
import { useState } from 'react';
import { useParams } from 'react-router-dom';

import { useGapAnalyze, useGapIntake } from '../api/hooks';
import type { GapAnalysisResult, GapClosureNode } from '../api/types';

const STATUS_COLORS: Record<string, string> = {
  expert: 'teal',
  solid: 'green',
  learning: 'yellow',
  locked: 'gray',
};

function statusColor(status: string): string {
  return STATUS_COLORS[status] ?? 'gray';
}

function NodeRow({ node }: { node: GapClosureNode }) {
  return (
    <Group gap="sm" wrap="nowrap">
      <Badge color={statusColor(node.status)} variant="light">
        {node.status}
      </Badge>
      <Text fw={500}>{node.label || node.id}</Text>
      <Text size="sm" c="dimmed">
        {node.id}
      </Text>
      {node.evidence_count > 0 && (
        <Text size="sm" c="dimmed">
          {node.evidence_count} 条证据
        </Text>
      )}
    </Group>
  );
}

function GapResults({ profile, result }: { profile: string; result: GapAnalysisResult }) {
  const intake = useGapIntake(profile);
  const strong = (result.closure ?? []).filter((node) => !node.is_gap);
  const gaps = (result.closure ?? []).filter((node) => node.is_gap);
  const coveragePct = Math.round(result.coverage * 100);

  return (
    <Stack gap="md">
      <Card withBorder radius="md" padding="lg">
        <Group justify="space-between" align="center">
          <div>
            <Text size="sm" c="dimmed">
              任务
            </Text>
            <Text fw={500}>{result.task}</Text>
          </div>
          <Badge color={result.can_solve ? 'green' : 'yellow'} size="lg" variant="light">
            {result.can_solve ? '可以胜任' : '存在差距'}
          </Badge>
        </Group>
        <Text size="sm" c="dimmed" mt="sm">
          技能覆盖率 {coveragePct}%
        </Text>
        <Progress
          value={coveragePct}
          color={result.can_solve ? 'green' : 'yellow'}
          aria-label="技能覆盖率"
        />
      </Card>

      <Card withBorder radius="md" padding="lg" data-testid="gap-strong-section">
        <Title order={4} mb="sm">
          已具备的技能 ({strong.length})
        </Title>
        {strong.length === 0 ? (
          <Text c="dimmed">闭包内暂无已掌握的技能节点。</Text>
        ) : (
          <Stack gap="xs">
            {strong.map((node) => (
              <NodeRow key={node.id} node={node} />
            ))}
          </Stack>
        )}
      </Card>

      <Card withBorder radius="md" padding="lg" data-testid="gap-missing-section">
        <Title order={4} mb="sm">
          能力差距 ({gaps.length})
        </Title>
        {gaps.length === 0 ? (
          <Text c="dimmed">没有检测到差距,所有相关技能均已掌握。</Text>
        ) : (
          <Stack gap="xs">
            {gaps.map((node) => (
              <Group key={node.id} gap="sm" wrap="nowrap" justify="space-between">
                <NodeRow node={node} />
                <Button
                  size="compact-sm"
                  variant="light"
                  loading={intake.isPending && intake.variables?.node_id === node.id}
                  onClick={() =>
                    intake.mutate({
                      title: `学习 ${node.label || node.id}`,
                      node_id: node.id,
                      why: result.task ?? '',
                      section: 'Queue',
                    })
                  }
                >
                  加入看板
                </Button>
              </Group>
            ))}
          </Stack>
        )}
        {intake.isSuccess && (
          <Alert color="green" mt="sm" title="已创建">
            学习任务已加入看板 Queue。
          </Alert>
        )}
        {intake.isError && (
          <Alert color="red" mt="sm" title="创建失败">
            {intake.error.message}
          </Alert>
        )}
      </Card>

      {(result.next_steps ?? []).length > 0 && (
        <Card withBorder radius="md" padding="lg">
          <Title order={4} mb="sm">
            建议行动
          </Title>
          <List size="sm">
            {(result.next_steps ?? []).map((step) => (
              <List.Item key={step}>{step}</List.Item>
            ))}
          </List>
        </Card>
      )}

      <Alert color="blue" variant="light" icon={<IconInfoCircle size={16} />} title="深度分析">
        LLM 深度分析需要后续异步任务支持,当前版本仅提供规则匹配。
      </Alert>
    </Stack>
  );
}

export function GapPage() {
  const { name = '' } = useParams();
  const analyze = useGapAnalyze(name);
  const [task, setTask] = useState('');
  const [validationError, setValidationError] = useState('');

  const submit = () => {
    if (!task.trim()) {
      setValidationError('请先描述要分析的任务。');
      return;
    }
    setValidationError('');
    analyze.mutate({ task: task.trim(), use_llm: false });
  };

  return (
    <Stack gap="md">
      <Title order={2}>{name} · 差距分析</Title>
      <Textarea
        label="任务描述"
        description="描述一个你想要完成的任务,系统会对照技能树找出已具备的能力和差距。"
        placeholder="例如:用机械臂完成抓取并放置的任务"
        minRows={4}
        autosize
        value={task}
        onChange={(event) => {
          setTask(event.currentTarget.value);
          if (validationError) {
            setValidationError('');
          }
        }}
        error={validationError || undefined}
      />
      <Group>
        <Button onClick={submit} loading={analyze.isPending}>
          分析
        </Button>
      </Group>
      {analyze.isError && (
        <Alert color="red" title="分析失败">
          {analyze.error.message}
        </Alert>
      )}
      {analyze.isSuccess && <GapResults profile={name} result={analyze.data} />}
    </Stack>
  );
}
