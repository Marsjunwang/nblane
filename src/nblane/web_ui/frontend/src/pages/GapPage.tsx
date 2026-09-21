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
import { IconAlertTriangle, IconInfoCircle } from '@tabler/icons-react';
import { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';

import { useGapAnalyze, useGapDeepAnalyze, useGapIntake } from '../api/hooks';
import { streamJob } from '../api/jobs';
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

/** Backend job phases -> Chinese label + coarse progress percentage. */
const DEEP_PHASES: Record<string, { label: string; pct: number }> = {
  queued: { label: '排队中', pct: 10 },
  starting: { label: '启动中', pct: 20 },
  routing: { label: '路由中', pct: 55 },
  merging: { label: '合并中', pct: 85 },
  done: { label: '完成', pct: 100 },
};

function deepPhase(phase: string): { label: string; pct: number } {
  return DEEP_PHASES[phase] ?? { label: phase || '进行中', pct: 40 };
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
  const isDeep = result.analysis_mode === 'rule+llm';
  const llmRoots = result.roots_from_llm ?? [];
  const ruleRoots = result.roots_from_rule ?? [];

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
          <Group gap="xs">
            {isDeep && (
              <Badge color="violet" size="lg" variant="light">
                LLM 深度分析
              </Badge>
            )}
            <Badge color={result.can_solve ? 'green' : 'yellow'} size="lg" variant="light">
              {result.can_solve ? '可以胜任' : '存在差距'}
            </Badge>
          </Group>
        </Group>
        <Text size="sm" c="dimmed" mt="sm">
          技能覆盖率 {coveragePct}%
        </Text>
        <Progress
          value={coveragePct}
          color={result.can_solve ? 'green' : 'yellow'}
          aria-label="技能覆盖率"
        />
        {isDeep && (
          <Text size="sm" c="dimmed" mt="sm" data-testid="gap-root-origins">
            根因来源:规则 {ruleRoots.length} 项
            {ruleRoots.length > 0 && `(${ruleRoots.join(', ')})`} · LLM {llmRoots.length} 项
            {llmRoots.length > 0 && `(${llmRoots.join(', ')})`}
            {result.learned_merged && ' · LLM 关键词已并入学习库,后续规则匹配会更准'}
          </Text>
        )}
      </Card>

      {result.llm_router_error && (
        <Alert
          color="yellow"
          variant="light"
          icon={<IconAlertTriangle size={16} />}
          title="LLM 不可用,已回退为规则分析"
          data-testid="gap-llm-degraded"
        >
          {result.llm_router_error}
        </Alert>
      )}

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

      {!isDeep && (
        <Alert color="blue" variant="light" icon={<IconInfoCircle size={16} />} title="深度分析">
          以上为规则匹配结果。点击「深度分析(LLM)」可让大模型重新路由任务、
          发现规则漏掉的技能根因(约需 1 分钟)。
        </Alert>
      )}
    </Stack>
  );
}

interface DeepJobProgress {
  jobId: string;
  phase: string;
  message: string;
}

export function GapPage() {
  const { name = '' } = useParams();
  const analyze = useGapAnalyze(name);
  const deepAnalyze = useGapDeepAnalyze(name);
  const [task, setTask] = useState('');
  const [validationError, setValidationError] = useState('');
  const [deepJob, setDeepJob] = useState<DeepJobProgress | null>(null);
  const [deepResult, setDeepResult] = useState<GapAnalysisResult | null>(null);
  const [deepError, setDeepError] = useState<{ code: string; message: string } | null>(null);
  const stopStreamRef = useRef<(() => void) | null>(null);

  const stopStream = () => {
    stopStreamRef.current?.();
    stopStreamRef.current = null;
  };

  // Cancel the SSE subscription on unmount and whenever the profile route
  // changes; a stale stream must never write another profile's state.
  useEffect(() => {
    setDeepJob(null);
    setDeepResult(null);
    setDeepError(null);
    return stopStream;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [name]);

  const startDeep = () => {
    if (!task.trim()) {
      setValidationError('请先描述要分析的任务。');
      return;
    }
    setValidationError('');
    stopStream();
    setDeepJob(null);
    setDeepResult(null);
    setDeepError(null);
    deepAnalyze.mutate(
      { task: task.trim(), use_llm: true },
      {
        onSuccess: (created) => {
          const jobId = created.job_id;
          setDeepJob({ jobId, phase: created.job.phase || 'queued', message: '' });
          stopStreamRef.current = streamJob(name, jobId, {
            onProgress: (frame) => {
              setDeepJob((prev) =>
                prev && prev.jobId === jobId
                  ? {
                      jobId,
                      phase: frame.event?.phase || frame.job?.phase || prev.phase,
                      message: frame.event?.message || prev.message,
                    }
                  : prev,
              );
            },
            onDone: (frame) => {
              stopStream();
              setDeepJob(null);
              if (frame.result) {
                setDeepResult(frame.result as unknown as GapAnalysisResult);
              } else {
                setDeepError({ code: 'empty_result', message: '任务完成但未返回结果,请重试。' });
              }
            },
            onError: (frame) => {
              stopStream();
              setDeepJob(null);
              setDeepError(
                frame?.error ?? {
                  code: 'stream_error',
                  message: '进度流中断,请稍后重试。',
                },
              );
            },
          });
        },
      },
    );
  };

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
        <Button
          variant="light"
          color="violet"
          onClick={startDeep}
          loading={deepAnalyze.isPending}
          disabled={Boolean(deepJob)}
        >
          深度分析(LLM)
        </Button>
      </Group>
      {analyze.isError && (
        <Alert color="red" title="分析失败">
          {analyze.error.message}
        </Alert>
      )}
      {deepAnalyze.isError && (
        <Alert color="red" title="创建深度分析任务失败">
          {deepAnalyze.error.message}
        </Alert>
      )}
      {deepJob && (
        <Card withBorder radius="md" padding="lg" data-testid="gap-deep-progress">
          <Group justify="space-between" align="center">
            <Text fw={500}>深度分析(LLM)进行中</Text>
            <Badge color="violet" variant="light">
              {deepPhase(deepJob.phase).label}
            </Badge>
          </Group>
          <Progress
            value={deepPhase(deepJob.phase).pct}
            color="violet"
            animated
            mt="sm"
            aria-label="深度分析进度"
          />
          <Text size="sm" c="dimmed" mt="xs">
            LLM 正在路由任务到技能节点,通常需要 30–60 秒,可留在本页等待。
          </Text>
        </Card>
      )}
      {deepError && (
        <Alert color="red" title="深度分析失败" data-testid="gap-deep-error">
          {deepError.message}
        </Alert>
      )}
      {analyze.isSuccess && <GapResults profile={name} result={analyze.data} />}
      {deepResult && <GapResults profile={name} result={deepResult} />}
    </Stack>
  );
}
