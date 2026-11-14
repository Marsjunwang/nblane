import { Alert, Button, Group, Modal, Select, Stack, Stepper, Text, TextInput } from '@mantine/core';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { useSchemas } from '../api/hooks';
import { useCreateProfile } from '../api/profiles';

export function ProfileCreateDialog({ onClose }: { onClose: () => void }) {
  const navigate = useNavigate();
  const schemas = useSchemas();
  const create = useCreateProfile();
  const [step, setStep] = useState(0);
  const [name, setName] = useState('');
  const [schema, setSchema] = useState<string | null>(null);
  const [northStar, setNorthStar] = useState('');
  const [goal, setGoal] = useState('');
  const [project, setProject] = useState('');
  const [task, setTask] = useState('');
  const [validation, setValidation] = useState('');
  const [confirmClose, setConfirmClose] = useState(false);
  const options = (schemas.data ?? []).map((item) => ({ value: item.name, label: item.domain || item.name }));
  const chosen = schema ?? options[0]?.value ?? null;
  const dirty = Boolean(name || northStar || goal || project || task || schema);

  const next = () => {
    if (!name.trim() || !chosen) {
      setValidation('请填写档案名并选择领域。');
      return;
    }
    if (/[\\/\r\n]/.test(name) || ['.', '..', 'template'].includes(name.trim())) {
      setValidation('请使用普通名称，不要包含斜杠或保留名称。');
      return;
    }
    setValidation('');
    setStep(1);
  };
  const submit = () => {
    if (!chosen) return;
    if ((project.trim() || task.trim()) && !goal.trim()) {
      setValidation('请先写下阶段目标，再添加项目和任务。');
      return;
    }
    setValidation('');
    setConfirmClose(false);
    create.mutate({ name: name.trim(), schema: chosen, north_star: northStar.trim(), goal_title: goal.trim(), project_title: project.trim(), task_title: task.trim() }, {
      onSuccess: (result) => {
        onClose();
        navigate(`/p/${encodeURIComponent(result.name)}/${result.has_first_plan ? 'projects' : 'home'}`);
      },
    });
  };

  return (
    <Modal opened onClose={() => { if (!create.isPending) { if (dirty) setConfirmClose(true); else onClose(); } }} title="创建成长档案" size="lg" closeOnClickOutside={false} closeOnEscape={!create.isPending} withCloseButton={!create.isPending}>
      <form onSubmit={(event) => { event.preventDefault(); if (step === 0) next(); else submit(); }}>
        <Stack gap="md">
          <Stepper active={step} size="sm" allowNextStepsSelect={false}>
            <Stepper.Step label="档案与领域" />
            <Stepper.Step label="从第一步开始" />
          </Stepper>
          {step === 0 ? (
            <>
              <TextInput label="档案名" description="可以用你的名字；用于区分自己的工作区。" value={name} onChange={(event) => setName(event.currentTarget.value)} maxLength={80} required data-autofocus />
              <Select label="领域" data={options} value={chosen} onChange={setSchema} disabled={schemas.isPending || schemas.isError} allowDeselect={false} required placeholder={schemas.isPending ? '正在加载领域…' : '选择领域'} />
              {schemas.isError && <Alert color="red" title="领域加载失败"><Stack gap="xs"><Text size="sm">{schemas.error.message}</Text><Button variant="subtle" onClick={() => void schemas.refetch()}>重试</Button></Stack></Alert>}
              {chosen && <Text size="sm" c="dimmed">{schemas.data?.find((item) => item.name === chosen)?.description}</Text>}
              <Text size="sm" c="dimmed">新档案默认私有。先选择起点，之后逐步积累项目和证据。</Text>
            </>
          ) : (
            <>
              <TextInput label="北极星" description="长期想成为怎样的人？也可以以后再写。" placeholder="例如：能独立完成机器人产品的研究与交付" value={northStar} onChange={(event) => setNorthStar(event.currentTarget.value)} maxLength={2000} disabled={create.isPending} />
              <TextInput label="阶段目标" description="接下来 4 到 8 周想完成什么？选填。" placeholder="例如：完成第一个可演示的原型" value={goal} onChange={(event) => setGoal(event.currentTarget.value)} maxLength={200} disabled={create.isPending} />
              <TextInput label="首个项目" description="留空时使用阶段目标的名称。" value={project} onChange={(event) => setProject(event.currentTarget.value)} maxLength={200} disabled={create.isPending} />
              <TextInput label="第一件任务" description="创建后放入项目的待办栏。选填。" placeholder="例如：整理需求和验收标准" value={task} onChange={(event) => setTask(event.currentTarget.value)} maxLength={300} disabled={create.isPending} />
            </>
          )}
          {(validation || create.isError) && <Alert color="red" title="还没有创建">{validation || create.error?.message}</Alert>}
          {confirmClose && (
            <Alert title="保留这次填写？">
              <Stack gap="xs"><Text size="sm">关闭后会丢弃尚未创建的档案内容。</Text><Group><Button variant="subtle" onClick={() => setConfirmClose(false)}>继续填写</Button><Button variant="outline" onClick={onClose}>放弃并关闭</Button></Group></Stack>
            </Alert>
          )}
          <Group justify="space-between">
            {step > 0 ? <Button variant="subtle" onClick={() => setStep(0)} disabled={create.isPending}>上一步</Button> : <span />}
            <Button type="submit" loading={create.isPending} disabled={!chosen || schemas.isError}>{step === 0 ? '下一步' : '创建档案'}</Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}
