import {
  Alert,
  Anchor,
  Badge,
  Button,
  Card,
  Checkbox,
  Code,
  CopyButton,
  Group,
  List,
  Modal,
  Select,
  Stack,
  Stepper,
  Switch,
  Text,
  TextInput,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconBrandWechat,
  IconCheck,
  IconCloudUpload,
  IconCopy,
  IconDatabase,
  IconDownload,
  IconFolderShare,
  IconKey,
  IconPlugConnected,
  IconRefresh,
  IconRobot,
  IconTerminal2,
} from '@tabler/icons-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';

import {
  useAgentToken,
  useConfigureAgentToken,
  useMe,
  useProfiles,
  useBackupStatus,
  useGenerateBackupKey,
  useInitBackupTarget,
  useOpenClawGateway,
  useOpenClawSetup,
  useRunBackup,
  useSaveBackupRemote,
  useSetBackupTimer,
  useStartOpenClawJob,
  useTestBackupRemote,
} from '../../api/hooks';
import { ApiError } from '../../api/client';
import type { AgentTokenStatus, BackupRemoteTest, BackupTarget, OpenClawSetupStatus } from '../../api/types';
import { ErrorAlert, SettingsCard } from '../../pages/settings/shared';

function errorToast(title: string) {
  return { onError: (error: Error) => notifications.show({ title, message: error.message, color: 'red' }) };
}

export function formatWhen(iso: string): string {
  if (!iso) return '';
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso : date.toLocaleString();
}

/** GitHub "new repository" / "deploy keys" links derived from an SSH URL. */
export function githubLinks(url: string): { newRepo: string; deployKeys: string } | null {
  const match = /^(?:git@github\.com:|ssh:\/\/git@github\.com\/)([^/]+)\/(.+?)(?:\.git)?$/.exec(url.trim());
  if (!match) return null;
  return { newRepo: 'https://github.com/new', deployKeys: `https://github.com/${match[1]}/${match[2]}/settings/keys/new` };
}

// ----------------------------------------------------------------- backup

function RemoteWizard({ target }: { target: BackupTarget }) {
  const init = useInitBackupTarget();
  const keygen = useGenerateBackupKey();
  const test = useTestBackupRemote();
  const save = useSaveBackupRemote();
  const [url, setUrl] = useState('');
  const [result, setResult] = useState<BackupRemoteTest | null>(null);
  const [privateConfirmed, setPrivateConfirmed] = useState(false);
  const publicKey = keygen.data?.public_key || target.public_key;
  const links = githubLinks(url);
  const active = !target.is_git ? 0 : !publicKey ? 1 : result?.ok ? 3 : 2;
  const needsManualConfirm = result?.ok && result.visibility !== 'hidden';
  return (
    <Stack gap="xs">
    <Stepper active={active} orientation="vertical" size="sm" allowNextStepsSelect={false}>
      <Stepper.Step label="纳入 git" description="把目录变成本机 git 仓库（已忽略可重建的 venv 和临时文件）">
        <Button size="xs" mt="xs" loading={init.isPending} onClick={() => init.mutate(target.id, errorToast('初始化失败'))}>初始化仓库</Button>
      </Stepper.Step>
      <Stepper.Step label="新建私有仓库并添加部署密钥" description="每个仓库一把独立密钥，私钥只留在服务器上">
        <Stack gap="xs" mt="xs">
          <List size="sm" spacing={4}>
            <List.Item>在 GitHub（或 Gitee 等支持 SSH 的平台）<Anchor href="https://github.com/new" target="_blank" rel="noopener noreferrer">新建仓库</Anchor>，可见性选 <b>Private</b>，不要勾选 README。</List.Item>
            <List.Item>生成密钥后，把公钥加到该仓库 Settings → Deploy keys，勾选 <b>Allow write access</b>。</List.Item>
          </List>
          <Button size="xs" w="fit-content" leftSection={<IconKey size={14} />} loading={keygen.isPending} onClick={() => keygen.mutate(target.id, errorToast('生成密钥失败'))}>生成部署密钥</Button>
        </Stack>
      </Stepper.Step>
      <Stepper.Step label="填写地址并测试" description="只做检查，不会改动任何东西">
        <Stack gap="xs" mt="xs">
          {publicKey && (
            <Card withBorder padding="xs" radius="sm">
              <Group justify="space-between" wrap="nowrap" align="flex-start">
                <Code block style={{ wordBreak: 'break-all', whiteSpace: 'pre-wrap', flex: 1 }}>{publicKey}</Code>
                <CopyButton value={publicKey}>
                  {({ copied, copy }) => <Button size="compact-xs" variant="light" leftSection={copied ? <IconCheck size={12} /> : <IconCopy size={12} />} onClick={copy}>{copied ? '已复制' : '复制公钥'}</Button>}
                </CopyButton>
              </Group>
            </Card>
          )}
          <TextInput
            label="仓库 SSH 地址"
            placeholder="git@github.com:你的用户名/openclaw-workspace.git"
            value={url}
            onChange={(event) => { setUrl(event.currentTarget.value); setResult(null); setPrivateConfirmed(false); }}
          />
          {links && <Text size="xs"><Anchor href={links.deployKeys} target="_blank" rel="noopener noreferrer">打开这个仓库的 Deploy keys 页面</Anchor></Text>}
          <Button size="xs" w="fit-content" disabled={!url.trim()} loading={test.isPending} onClick={() => test.mutate({ targetId: target.id, url }, { onSuccess: setResult, ...errorToast('测试失败') })}>测试连接</Button>
        </Stack>
      </Stepper.Step>
      <Stepper.Step label="保存并首次推送">
        <Stack gap="xs" mt="xs">
          <Text size="sm">推送内容包含个人记忆（如 USER.md、MEMORY.md、memory/ 日记），请确认仓库只对你自己可见。</Text>
          {needsManualConfirm && <Checkbox label="我已在远端确认这个仓库是 Private" checked={privateConfirmed} onChange={(event) => setPrivateConfirmed(event.currentTarget.checked)} />}
          <Button size="xs" w="fit-content" leftSection={<IconCloudUpload size={14} />} disabled={Boolean(needsManualConfirm && !privateConfirmed)} loading={save.isPending} onClick={() => save.mutate({ targetId: target.id, url }, { onSuccess: () => notifications.show({ title: '远端已保存', message: '已完成首次推送', color: 'green' }), ...errorToast('保存失败') })}>保存并推送</Button>
        </Stack>
      </Stepper.Step>
    </Stepper>
    {/* Outside the stepper: a passing test advances the step and would hide it. */}
    {result && <Alert color={result.ok ? 'green' : 'red'} variant="light">{result.message}</Alert>}
    </Stack>
  );
}

function TargetRow({ target }: { target: BackupTarget }) {
  const run = useRunBackup();
  const [wizard, setWizard] = useState(false);
  const healthy = Boolean(target.remote_url) && target.ahead === 0 && (target.commit_mode === 'push_only' || target.dirty === 0);
  const lastRun = target.last_run;
  return (
    <Card withBorder radius="sm" padding="md">
      <Stack gap="xs">
        <Group justify="space-between" align="flex-start">
          <div>
            <Group gap="xs"><Text fw={600}>{target.label}</Text>
              {!target.exists ? <Badge color="gray" variant="light">目录不存在</Badge>
                : !target.remote_url ? <Badge color="orange" variant="light">只在本机</Badge>
                : healthy ? <Badge color="green" variant="light">已同步</Badge>
                : <Badge color="yellow" variant="light">待推送</Badge>}
            </Group>
            <Text size="xs" c="dimmed">{target.description}</Text>
            <Text size="xs" c="dimmed" ff="monospace">{target.path}</Text>
          </div>
          <Group gap="xs">
            {target.remote_url && <Button size="xs" variant="light" leftSection={<IconCloudUpload size={14} />} loading={run.isPending} onClick={() => run.mutate(target.id, { onSuccess: (value) => { const item = value.results[0] as { ok?: boolean; error?: string } | undefined; notifications.show({ title: item?.ok ? '备份完成' : '备份失败', message: item?.error || target.label, color: item?.ok ? 'green' : 'red' }); }, ...errorToast('备份失败') })}>立即备份</Button>}
            {!target.remote_url && target.exists && <Button size="xs" onClick={() => setWizard((value) => !value)}>{wizard ? '收起' : '添加私有远端'}</Button>}
          </Group>
        </Group>
        {target.is_git && (
          <Text size="xs" c="dimmed">
            {target.remote_url ? `远端 ${target.remote_url}` : '还没有远端：机器损坏时这些数据会丢失。'}
            {target.ahead > 0 && ` · ${target.ahead} 个提交未推送`}
            {target.dirty > 0 && ` · ${target.dirty} 处改动未提交${target.commit_mode === 'push_only' ? '（应用写入时会自动提交，残留项请到车间查看）' : '（下次备份会自动快照）'}`}
            {target.last_commit_at && ` · 最近提交 ${formatWhen(target.last_commit_at)}`}
          </Text>
        )}
        {lastRun?.at && <Text size="xs" c={lastRun.ok ? 'dimmed' : 'red'}>上次备份 {formatWhen(lastRun.at)}：{lastRun.ok ? (lastRun.committed ? '已快照并推送' : '已推送') : lastRun.error}</Text>}
        {wizard && !target.remote_url && <RemoteWizard target={target} />}
      </Stack>
    </Card>
  );
}

export function BackupSection() {
  const status = useBackupStatus();
  const timer = useSetBackupTimer();
  if (status.isPending) return null;
  if (status.isError) return <ErrorAlert error={status.error} />;
  const data = status.data;
  return (
    <SettingsCard icon={<IconDatabase size={22} />} title="数据备份" description="nblane 数据和已接入 agent 的工作区各是一个独立的私有 git 仓库：备份统一，仓库分开。">
        {data.targets.map((target) => <TargetRow key={target.id} target={target} />)}
        <Group justify="space-between">
          <div>
            <Switch
              label={`每日自动备份（${data.timer.schedule}，在 OpenClaw 记忆整理之后）`}
              checked={data.timer.enabled}
              disabled={timer.isPending}
              onChange={(event) => timer.mutate(event.currentTarget.checked, errorToast('设置定时备份失败'))}
            />
            <Text size="xs" c="dimmed" ml={46}>
              工作区每天整体快照并推送；nblane 数据只推送应用已提交的内容。{data.timer.next_run && `下次 ${data.timer.next_run}`}
            </Text>
          </div>
          <Button size="xs" variant="subtle" leftSection={<IconRefresh size={14} />} loading={status.isFetching} onClick={() => status.refetch()}>刷新</Button>
        </Group>
        {data.data_git && !data.data_git.autopush && <Text size="xs" c="orange">nblane 数据未开启写入即推送（NBLANE_DATA_GIT_AUTOPUSH），只能依赖每日备份。</Text>}
    </SettingsCard>
  );
}

// ----------------------------------------------------------------- agent

function JobLog({ job }: { job: OpenClawSetupStatus['job'] }) {
  if (!job?.status) return null;
  const log = job.log ?? [];
  const color = job.status === 'failed' ? 'red' : job.status === 'done' ? 'green' : 'blue';
  const title = { install: '安装', connect: '接入', migrate: '迁移工作区', weixin: '微信渠道' }[job.kind] ?? job.kind;
  return (
    <Alert color={color} variant="light" title={`${title}：${job.status === 'running' ? '进行中…' : job.status === 'done' ? '完成' : '失败'}`}>
      {job.error && <Text size="sm" mb={4}>{job.error}</Text>}
      <Text component="pre" size="xs" style={{ whiteSpace: 'pre-wrap', maxHeight: 220, overflow: 'auto', margin: 0 }}>{log.slice(-40).join('\n')}</Text>
    </Alert>
  );
}

function StatusLine({ ok, label, detail }: { ok: boolean; label: string; detail?: string }) {
  return (
    <Group gap={6} wrap="nowrap">
      <Badge size="sm" color={ok ? 'green' : 'gray'} variant="light">{ok ? '✓' : '—'}</Badge>
      <Text size="sm">{label}</Text>
      {detail && <Text size="xs" c="dimmed" style={{ wordBreak: 'break-all' }}>{detail}</Text>}
    </Group>
  );
}

export const AGENT_TOKEN_ERRORS: Record<string, string> = {
  agent_account_missing: '服务账号不存在：先在 设置 → 账号管理 新建一个助手账号。',
  not_agent_account: '这个账号没有标记为助手，不能给它自动配置 token。',
  auth_not_configured: '还没开启登录（NBLANE_AUTH_FILE），助手不需要 token。',
  token_verify_failed: '写入后校验失败，已恢复原文件并作废新 token，旧 token 仍可用。',
  agent_forbidden: '助手账号不能操作自己的凭据，请用管理员账号。',
};

export function agentTokenError(error: unknown): string {
  if (error instanceof ApiError && AGENT_TOKEN_ERRORS[error.code]) return AGENT_TOKEN_ERRORS[error.code];
  return error instanceof Error ? error.message : String(error);
}

function tokenBadge(data: AgentTokenStatus): { color: string; label: string } {
  if (!data.account_exists) return { color: 'red', label: '账号不存在' };
  if (!data.account_is_agent) return { color: 'orange', label: '账号未标记为助手' };
  if (!data.configured) return { color: 'gray', label: '未配置' };
  if (!data.token_valid) return { color: 'red', label: 'token 已失效' };
  return { color: 'green', label: data.created ? `已配置 token（创建于 ${formatWhen(data.created)}）` : '已配置 token' };
}

/** 服务账号凭据: mint the assistant token and write api.env server-side. */
export function AgentTokenCard() {
  const me = useMe();
  const authEnabled = Boolean(me.data?.auth_enabled);
  const status = useAgentToken(authEnabled);
  const configure = useConfigureAgentToken();
  const [confirming, setConfirming] = useState(false);
  // Without login the assistant needs no token: nothing to configure.
  if (!authEnabled || status.isPending) return null;
  if (status.isError) return <ErrorAlert error={status.error} />;
  const data = status.data;
  const badge = tokenBadge(data);
  const rotate = data.configured && data.token_valid;
  const blocked = !data.account_exists || !data.account_is_agent;
  const close = () => { setConfirming(false); configure.reset(); };
  const submit = () => configure.mutate(undefined, {
    onSuccess: () => {
      setConfirming(false);
      notifications.show({ title: '已配置', message: '已配置，助手下次调用即用新 token', color: 'green' });
    },
  });
  return (
    <Card withBorder radius="sm" padding="md" component="section" aria-label="服务账号凭据">
      <Stack gap="xs">
        <Group gap="xs">
          <IconKey size={16} />
          <Text fw={600} size="sm">服务账号凭据</Text>
        </Group>
        <Group gap="xs">
          <Text size="sm">账号 <Code>{data.account}</Code></Text>
          <Badge color={badge.color} variant="light">{badge.label}</Badge>
          {data.password_fallback && <Badge color="gray" variant="outline">保留密码备用</Badge>}
        </Group>
        <Text size="xs" c="dimmed">凭据写入服务器 <Code>{data.env_path}</Code>，明文不经过浏览器。</Text>
        <Button w="fit-content" size="xs" variant={rotate ? 'light' : 'filled'} leftSection={<IconKey size={14} />} disabled={blocked} onClick={() => setConfirming(true)}>
          {rotate ? '轮换 token' : '生成并配置 token'}
        </Button>
      </Stack>
      <Modal opened={confirming} onClose={close} title={rotate ? '轮换助手 token？' : '生成并配置 token？'} centered>
        <Stack gap="md">
          <Text size="sm">
            {rotate
              ? `为 ${data.account} 生成新 token 并写入 ${data.env_path}；校验通过后作废旧 token。`
              : `为 ${data.account} 生成 token 并写入 ${data.env_path}，文件里的其它内容保持不变。`}
          </Text>
          {configure.isError && <Alert color="red" variant="light">{agentTokenError(configure.error)}</Alert>}
          <Group justify="flex-end">
            <Button variant="default" onClick={close}>取消</Button>
            <Button loading={configure.isPending} onClick={submit}>{rotate ? '轮换' : '生成并配置'}</Button>
          </Group>
        </Stack>
      </Modal>
    </Card>
  );
}

export function AgentSection() {
  const status = useOpenClawSetup();
  const profileList = useProfiles();
  const profiles = profileList.data ?? [];
  const job = useStartOpenClawJob();
  const gateway = useOpenClawGateway();
  const [profile, setProfile] = useState('');
  const [reuseLlm, setReuseLlm] = useState(true);
  if (status.isPending) return null;
  if (status.isError) return <ErrorAlert error={status.error} />;
  const data = status.data;
  const running = data.job?.status === 'running';
  const chosen = profile || data.connected_profile || profiles[0]?.name || '';
  const start = (kind: 'install' | 'connect' | 'migrate' | 'weixin') => job.mutate({ kind, profile: chosen, reuseLlm }, errorToast('无法开始'));
  const ready = data.installed && data.configured;
  return (
    <SettingsCard icon={<IconRobot size={22} />} title="个人 Agent" description="nblane 是 agent 背后的成长档案：agent 通过 MCP 读写，结构化改动进入审批。目前适配 OpenClaw，其它支持 MCP 的 agent 可用下方配置片段接入。">
        <Group gap="xs">
          <Badge color={ready ? 'green' : 'gray'} variant="light">{ready ? `OpenClaw ${data.version}` : data.installed ? '已安装，未初始化' : '未安装'}</Badge>
          {data.profile && <Badge color="violet" variant="outline">隔离 profile：{data.profile}</Badge>}
          {ready && <Badge color={data.gateway_reachable ? 'green' : 'red'} variant="light">网关 {data.gateway_reachable ? `运行中 :${data.gateway_port}` : '未运行'}</Badge>}
        </Group>
        {data.foreign_root && <Alert color="orange" variant="light" title="只读">这个 OpenClaw 已接入另一个 nblane 数据目录（{data.foreign_root}），这里不能修改它。开发环境请用 scripts/dev-web.sh --isolated 启动。</Alert>}
        <JobLog job={data.job} />
        {profiles.length > 1 && <Select w={260} label="接入的档案" value={chosen} onChange={(value) => setProfile(value ?? '')} data={profiles.map((item) => ({ value: item.name, label: item.name }))} />}

        {!ready && (
          <Stack gap="xs">
            <Text size="sm">将安装经过验证的 OpenClaw {data.pinned_version}（npm 全局安装到服务用户目录），网关只监听本机 {data.gateway_port} 端口，工作区直接放在 <Code>{data.target_workspace}</Code>，并自动接入 nblane。</Text>
            {!data.node_supported && <Text size="xs" c="red">需要 Node 24.16+ 或 26.1+，当前为 {data.node_version || '未安装'}。</Text>}
            <Checkbox
              label={data.llm_reusable ? `模型复用 nblane 的 AI 连接（${data.llm_model}）` : '模型复用 nblane 的 AI 连接（尚未配置，可安装后在 OpenClaw 控制台添加）'}
              checked={reuseLlm && data.llm_reusable}
              disabled={!data.llm_reusable}
              onChange={(event) => setReuseLlm(event.currentTarget.checked)}
            />
            <Text size="xs" c="dimmed">Key 只在服务端通过环境变量交给 OpenClaw，不出现在命令行或页面上。更多服务商（如 Kimi Code 订阅）在 OpenClaw 控制台添加。</Text>
            <Button w="fit-content" leftSection={<IconDownload size={16} />} disabled={running || !data.node_supported || (!data.installed && !data.npm_available)} loading={job.isPending} onClick={() => start('install')}>一键安装 OpenClaw</Button>
          </Stack>
        )}

        {ready && (
          <Stack gap={6}>
            <StatusLine ok={Boolean(data.connected_profile)} label="已接入 nblane" detail={data.connected_profile && `档案 ${data.connected_profile}`} />
            <StatusLine ok={data.corpus_present} label="档案语料（OpenClaw 记忆检索可直接命中）" />
            <StatusLine ok={data.workspace_in_agent_root} label="工作区在统一数据目录" detail={data.workspace} />
            <StatusLine ok={data.weixin_installed} label="微信渠道插件" />
            <Group gap="xs" mt="xs">
              <Button size="xs" leftSection={<IconPlugConnected size={14} />} disabled={running} loading={job.isPending && job.variables?.kind === 'connect'} onClick={() => start('connect')}>{data.connected_profile ? '重新接入 / 刷新语料' : '接入 nblane'}</Button>
              {!data.workspace_in_agent_root && data.workspace_exists && (
                <Button size="xs" variant="light" leftSection={<IconFolderShare size={14} />} disabled={running} onClick={() => { if (window.confirm(`把工作区移动到 ${data.target_workspace}？\n\n会先备份整个 OpenClaw 状态目录，然后短暂停止网关（微信会断开约 10 秒），旧路径保留为软链接。`)) start('migrate'); }}>迁移到统一数据目录</Button>
              )}
              {!data.weixin_installed && <Button size="xs" variant="light" leftSection={<IconBrandWechat size={14} />} disabled={running} onClick={() => { if (window.confirm('安装腾讯维护的微信渠道插件并重启网关？')) start('weixin'); }}>安装微信渠道</Button>}
              <Button size="xs" variant="subtle" disabled={running} loading={gateway.isPending} onClick={() => gateway.mutate(data.gateway_reachable ? 'restart' : 'start', errorToast('网关操作失败'))}>{data.gateway_reachable ? '重启网关' : '启动网关'}</Button>
            </Group>
            {data.weixin_installed && (
              <Text size="xs" c="dimmed">
                微信扫码登录：到 <Anchor component={Link} to="/workshop"><IconTerminal2 size={12} /> 车间终端</Anchor> 运行 <Code>{data.weixin_login_command}</Code>，或在 OpenClaw 控制台的 Channels 页面扫码。
              </Text>
            )}
          </Stack>
        )}

        <AgentTokenCard />

        <details>
          <summary><Text span size="xs" c="dimmed">其它 agent（Claude Code、Cursor、nanobot 等）的 MCP 配置片段</Text></summary>
          <Code block mt="xs">{JSON.stringify({ mcpServers: { nblane: data.mcp_entry } }, null, 2)}</Code>
        </details>
    </SettingsCard>
  );
}

/** Settings → 系统 → 助手与备份. */
export function AgentsAndBackupSection() {
  return (
    <Stack gap="lg">
      <AgentSection />
      <BackupSection />
    </Stack>
  );
}
