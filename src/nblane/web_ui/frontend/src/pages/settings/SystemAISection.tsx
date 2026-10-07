// 系统 · AI 服务: deployment LLM connection and Codex CLI readiness (admin).

import { Badge, Button, Center, Checkbox, Code, Group, Loader, NumberInput, PasswordInput, SimpleGrid, Stack, Text, TextInput } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconCheck, IconDeviceFloppy, IconKey, IconPlugConnected, IconTerminal2 } from '@tabler/icons-react';
import { useEffect, useState } from 'react';

import { useCodexStatus, useSettingsConnection, useUpdateSettingsConnection, useVerifySettingsConnection } from '../../api/hooks';
import type { CodexStatus, LlmConnectionUpdate } from '../../api/types';
import { ErrorAlert, SettingsCard } from './shared';

export function codexStatusLabel(status: CodexStatus): { label: string; color: string } {
  if (!status.installed) return { label: '未安装', color: 'gray' };
  return status.logged_in ? { label: '已安装并登录', color: 'green' } : { label: '已安装,未登录', color: 'yellow' };
}

function ConnectionCard() {
  const connection = useSettingsConnection(true);
  const save = useUpdateSettingsConnection();
  const verify = useVerifySettingsConnection();
  const [baseUrl, setBaseUrl] = useState('');
  const [model, setModel] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [clearApiKey, setClearApiKey] = useState(false);
  const [maxTokens, setMaxTokens] = useState<number | string>(8192);
  const [analysisMaxTokens, setAnalysisMaxTokens] = useState<number | string>(16384);

  useEffect(() => {
    if (connection.data) {
      setBaseUrl(connection.data.base_url);
      setModel(connection.data.model);
      setMaxTokens(connection.data.max_tokens);
      setAnalysisMaxTokens(connection.data.analysis_max_tokens);
      // The API key is deliberately never populated from the response.
      setApiKey('');
      setClearApiKey(false);
    }
  }, [connection.data]);

  if (connection.isPending) return <Center py="xl"><Loader /></Center>;
  if (connection.isError) return <ErrorAlert error={connection.error} />;

  const submit = () => {
    const tokens = (value: number | string) => (typeof value === 'number' ? value : null);
    const body: LlmConnectionUpdate = {
      base_url: baseUrl,
      model,
      api_key: apiKey,
      clear_api_key: clearApiKey,
      max_tokens: tokens(maxTokens),
      analysis_max_tokens: tokens(analysisMaxTokens),
    };
    save.mutate(body, {
      onSuccess: () => {
        setApiKey('');
        setClearApiKey(false);
        notifications.show({ title: '连接设置已保存', message: '运行中的 AI 服务已同步更新', color: 'green' });
      },
    });
  };

  return (
    <SettingsCard icon={<IconPlugConnected size={22} />} title="AI 连接" description="整个部署共用的 OpenAI 兼容服务；保存后立即生效。API Key 只写入服务端，不会回显。">
      <SimpleGrid cols={{ base: 1, sm: 2 }}>
        <TextInput label="Base URL" placeholder="https://api.openai.com/v1" value={baseUrl} onChange={(event) => setBaseUrl(event.currentTarget.value)} />
        <TextInput label="默认模型" placeholder="gpt-4o-mini" value={model} onChange={(event) => setModel(event.currentTarget.value)} />
      </SimpleGrid>
      <PasswordInput label="API Key" description={connection.data.api_key_set ? '服务端已保存 Key；留空表示保留现有值。' : '尚未配置 API Key。'} placeholder="只在新增或更换时填写" value={apiKey} onChange={(event) => setApiKey(event.currentTarget.value)} leftSection={<IconKey size={16} />} />
      <SimpleGrid cols={{ base: 1, sm: 2 }}>
        <NumberInput label="输出上限（token）" description="大多数 AI 动作每次回复的最大长度，默认 8192。" min={256} max={131072} step={1024} thousandSeparator="," value={maxTokens} onChange={setMaxTokens} />
        <NumberInput label="论文分析输出上限（token）" description="快速分析 / 阅读回顾卡专用，默认 16384。越大越完整也越慢。" min={256} max={131072} step={1024} thousandSeparator="," value={analysisMaxTokens} onChange={setAnalysisMaxTokens} />
      </SimpleGrid>
      <Text size="xs" c="dimmed">上限不能超过模型本身的最大输出（例如 qwen3.8-flash 为 131072）；超过时服务商会报错。输出被截断时，「AI 异常」里会提示调高。</Text>
      <Checkbox label="清除服务端 API Key" checked={clearApiKey} onChange={(event) => { setClearApiKey(event.currentTarget.checked); if (event.currentTarget.checked) setApiKey(''); }} />
      <Group>
        <Button leftSection={<IconDeviceFloppy size={16} />} loading={save.isPending} onClick={submit}>保存连接</Button>
        <Button variant="light" leftSection={<IconCheck size={16} />} loading={verify.isPending} onClick={() => verify.mutate(undefined, { onSuccess: (result) => notifications.show({ title: result.ok ? '连接成功' : '连接失败', message: result.detail || (result.ok ? '服务响应正常。' : '服务未通过检查。'), color: result.ok ? 'green' : 'red' }) })}>测试连接</Button>
      </Group>
      <ErrorAlert error={save.error} />
      <ErrorAlert error={verify.error} />
    </SettingsCard>
  );
}

function CodexStatusCard() {
  const status = useCodexStatus();
  if (status.isPending) return <Center py="xl"><Loader /></Center>;
  if (status.isError) return <ErrorAlert error={status.error} />;
  const data = status.data;
  const state = codexStatusLabel(data);
  return (
    <SettingsCard icon={<IconTerminal2 size={22} />} title="Codex CLI" description="深度研读、论文搜索等动作可以交给本机 Codex 执行。安装和登录在服务器终端完成，这里只显示状态。">
      <Group gap="xs">
        <Badge color={state.color} variant="light">{state.label}</Badge>
        <Text size="sm" c="dimmed">{data.version || data.error || '状态未知'}</Text>
      </Group>
      {data.resolved_path && <Text size="xs" c="dimmed">路径 {data.resolved_path}{data.cloud_env_configured ? ` · Cloud 环境 ${data.cloud_env_id}` : ''}</Text>}
      {!data.installed && data.install_command && <Stack gap={4}><Text size="xs" c="dimmed">在服务器上安装：</Text><Code block>{data.install_command}</Code></Stack>}
      {data.installed && !data.logged_in && <Stack gap={4}><Text size="xs" c="dimmed">在服务器上登录：</Text><Code block>codex login</Code></Stack>}
    </SettingsCard>
  );
}

export function SystemAISection() {
  return (
    <Stack gap="lg">
      <ConnectionCard />
      <CodexStatusCard />
      <Text size="xs" c="dimmed">API Key、Codex auth.json 和 token 不会在此页面读取或显示。</Text>
    </Stack>
  );
}
