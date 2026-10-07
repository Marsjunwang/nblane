// 系统 · 车间终端: the ttyd + tmux web terminal (install / take over, terminal
// options) and the Happy Coder setup guide (admin).

import { Accordion, Alert, Anchor, Badge, Button, Card, Center, Code, Divider, Group, List, Loader, NumberInput, SegmentedControl, SimpleGrid, Stack, Switch, Text, TextInput } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconDeviceFloppy, IconDeviceMobile, IconDownload, IconPlayerPlay, IconPlayerStop, IconRefresh, IconRestore, IconTerminal2, IconTrash } from '@tabler/icons-react';
import { useState } from 'react';

import { useUninstallWorkshop, useUpdateWorkshopSettings, useWorkshopLogs, useWorkshopService, useWorkshopServiceAction } from '../../api/hooks';
import type { WorkshopServiceStatus, WorkshopSettings } from '../../api/types';
import { ErrorAlert, SettingsCard, useDraft } from './shared';

const onError = (title: string) => ({ onError: (error: Error) => notifications.show({ title, message: error.message, color: 'red' }) });

const STATE: Record<string, { label: string; color: string }> = {
  running: { label: '运行中', color: 'green' },
  starting: { label: '启动中', color: 'yellow' },
  stopped: { label: '已停止', color: 'gray' },
  failed: { label: '启动失败', color: 'red' },
  legacy: { label: '运行中（手动配置）', color: 'blue' },
  external: { label: '运行中（外部进程）', color: 'blue' },
  not_installed: { label: '未安装', color: 'gray' },
};
const PHASE: Record<string, string> = { binary: '准备 ttyd', unit: '写入配置与服务', start: '启动服务' };

function ServiceCard({ data, refetch, fetching }: { data: WorkshopServiceStatus; refetch: () => void; fetching: boolean }) {
  const action = useWorkshopServiceAction();
  const uninstall = useUninstallWorkshop();
  const [showLogs, setShowLogs] = useState(false);
  const logs = useWorkshopLogs(showLogs);
  const state = STATE[data.state] ?? { label: data.state, color: 'gray' };
  const installing = data.install.status === 'running';
  const pending = (name: string) => action.isPending && action.variables === name;
  const takeover = data.state === 'legacy' || data.state === 'external';
  const remove = () => {
    if (!window.confirm('停止并移除车间服务？ttyd 和设置会保留，之后可以重新安装。')) return;
    const endSessions = window.confirm('同时结束车间 tmux 里正在运行的程序吗？\n\n「确定」= 结束全部会话；「取消」= 保留会话（下次启动后还在）。');
    uninstall.mutate(endSessions, onError('移除失败'));
  };
  return (
    <SettingsCard icon={<IconTerminal2 size={22} />} title="车间终端服务" description="ttyd 把 tmux 会话变成网页终端，只监听 127.0.0.1；浏览器经 nblane 登录验证后由 /terminal/ 访问（仅管理员）。">
      <Group gap="xs">
        <Badge color={state.color} variant="light">{state.label}</Badge>
        <Badge variant="outline" color="gray">ttyd {data.ttyd_version}{data.ttyd_installed ? '' : ' · 未就绪'}</Badge>
        {data.tmux_version && <Badge variant="outline" color="gray">{data.tmux_version}</Badge>}
        <Text size="xs" c="dimmed">{data.upstream} · 单元 {data.unit}</Text>
      </Group>
      {data.managed && (
        <Text size="xs" c="dimmed">
          tmux 独立服务器 <Code>tmux -L {data.tmux_socket}</Code>（不读 ~/.tmux.conf），会话 {data.session}{data.session_alive ? ' 运行中' : ' 未创建（首次打开车间时创建）'}。重启或改设置只重启 ttyd，会话里的程序不受影响。
        </Text>
      )}
      {takeover && (
        <Alert color="blue" variant="light" title="当前车间不是由 nblane 管理">
          点「接管」后：ttyd 由设置页统一配置，tmux 改用独立配置和独立服务器（不再读写 ~/.tmux.conf）。车间里会开一个新会话；旧会话仍在默认 tmux 服务器里，可在新终端中运行 <Code>TMUX= tmux attach -t workshop</Code> 取回（前缀 TMUX= 允许在车间里嵌套打开）。
        </Alert>
      )}
      {installing && <Text size="xs" c="dimmed">{PHASE[data.install.phase] ?? '处理中'}…</Text>}
      {data.install.status === 'failed' && <Alert color="red" variant="light">{data.install.error}</Alert>}
      {data.blocker && !data.managed && <Text size="xs" c="orange">暂不能一键安装：{data.blocker}</Text>}
      <Group gap="xs">
        {!data.managed && (
          <Button size="xs" leftSection={<IconDownload size={14} />} disabled={Boolean(data.blocker) || installing} loading={pending('install') || installing} onClick={() => action.mutate('install', onError(takeover ? '接管失败' : '安装失败'))}>
            {takeover ? '接管' : '一键安装'}
          </Button>
        )}
        {data.managed && data.state !== 'running' && data.state !== 'starting' && <Button size="xs" leftSection={<IconPlayerPlay size={14} />} loading={pending('start')} onClick={() => action.mutate('start', onError('启动失败'))}>启动</Button>}
        {data.managed && (data.state === 'running' || data.state === 'starting') && <Button size="xs" variant="default" leftSection={<IconPlayerStop size={14} />} loading={pending('stop')} onClick={() => action.mutate('stop', onError('停止失败'))}>停止</Button>}
        {data.managed && data.state === 'running' && <Button size="xs" variant="default" leftSection={<IconRefresh size={14} />} loading={pending('restart')} onClick={() => action.mutate('restart', onError('重启失败'))}>重启 ttyd</Button>}
        {data.unit_state.installed && <Button size="xs" variant="subtle" onClick={() => setShowLogs((value) => !value)}>{showLogs ? '收起日志' : '查看日志'}</Button>}
        {data.managed && <Button size="xs" variant="subtle" color="red" leftSection={<IconTrash size={14} />} loading={uninstall.isPending} onClick={remove}>移除服务</Button>}
        <Button size="xs" variant="subtle" leftSection={<IconRefresh size={14} />} loading={fetching} onClick={refetch}>刷新</Button>
      </Group>
      {showLogs && <Card withBorder radius="sm" padding="xs"><Text component="pre" size="xs" style={{ whiteSpace: 'pre-wrap', maxHeight: 260, overflow: 'auto', margin: 0 }}>{logs.data?.text || (logs.isPending ? '加载中…' : '暂无日志')}</Text></Card>}
      {data.caddy_legacy_route && (
        <Alert color="orange" variant="light" title="公网入口仍是旧的 basic_auth 直连">
          <Stack gap={6}>
            <Text size="sm">Caddy 还把 /terminal/ 直接转给 ttyd，会绕过 nblane 登录，并在页面里多弹一次密码。改成转给 nblane（需要 root）：</Text>
            <Code block>{`# /etc/caddy/Caddyfile：删掉 redir /terminal … 和整个 handle /terminal/* { … } 块，
# /terminal/ 会落到兜底的 reverse_proxy 127.0.0.1:8504，由 nblane 校验管理员登录。
sudo cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.bak.$(date +%Y%m%d-%H%M%S)
sudoedit /etc/caddy/Caddyfile
sudo caddy validate --config /etc/caddy/Caddyfile && sudo systemctl reload caddy`}</Code>
          </Stack>
        </Alert>
      )}
      <ManualSteps data={data} />
    </SettingsCard>
  );
}

function ManualSteps({ data }: { data: WorkshopServiceStatus }) {
  return (
    <Accordion variant="contained" radius="sm">
      <Accordion.Item value="manual">
        <Accordion.Control><Text size="sm">一键安装做不了的部分（需要 root 或网络受限时）</Text></Accordion.Control>
        <Accordion.Panel>
          <List type="ordered" size="sm" spacing="sm">
            <List.Item>
              <Text size="sm">安装 tmux{data.tmux_version ? `（已安装 ${data.tmux_version}）` : ''}：</Text>
              <Code block>sudo apt-get install -y tmux</Code>
            </List.Item>
            <List.Item>
              <Text size="sm">让服务用户的 systemd --user 常驻（开机自启、退出登录不停）{data.user_manager ? '（已就绪）' : ''}：</Text>
              <Code block>sudo loginctl enable-linger $USER</Code>
            </List.Item>
            <List.Item>
              <Text size="sm">下载失败时手动放置 ttyd {data.ttyd_version}（{data.arch}）{data.ttyd_installed ? '（已就绪）' : ''}，然后回来点「一键安装」：</Text>
              <Code block>{`mkdir -p "$(dirname ${data.ttyd_path})"
curl -fL -o ${data.ttyd_path} ${data.ttyd_download_url}
echo "${data.ttyd_sha256 || '<sha256>'}  ${data.ttyd_path}" | sha256sum -c -
chmod +x ${data.ttyd_path}`}</Code>
              <Text size="xs" c="dimmed">国内服务器访问 GitHub 慢时，在 curl 前加 https_proxy=…（与服务使用的代理一致）。</Text>
            </List.Item>
            <List.Item>
              <Text size="sm">公网访问：反向代理（Caddy / Nginx）只需把整个站点转给 nblane（127.0.0.1:8504），不要单独把 ttyd 端口 {data.port} 暴露出去。</Text>
            </List.Item>
          </List>
        </Accordion.Panel>
      </Accordion.Item>
    </Accordion>
  );
}

const RENDERERS = [
  { value: 'canvas', label: 'Canvas' },
  { value: 'webgl', label: 'WebGL' },
  { value: 'dom', label: 'DOM' },
];

function SettingsFormCard({ data }: { data: WorkshopServiceStatus }) {
  const { draft, setDraft, dirty, reset } = useDraft<WorkshopSettings>(data.settings);
  const save = useUpdateWorkshopSettings();
  const set = <K extends keyof WorkshopSettings>(key: K, value: WorkshopSettings[K]) => setDraft((prev) => ({ ...prev, [key]: value }));
  const num = (key: keyof WorkshopSettings) => (value: string | number) => {
    if (typeof value === 'number') set(key, value as never);
  };
  const isDefault = JSON.stringify(draft) === JSON.stringify(data.defaults);
  const submit = () =>
    save.mutate(draft, {
      onSuccess: (result) => {
        const applied = result.applied;
        const parts = [
          applied?.tmux_reloaded ? 'tmux 已重载' : '',
          applied?.ttyd_restarted ? 'ttyd 已重启（会话保留，页面会自动重连）' : '',
          applied?.reattach_needed ? '滚动方式需要刷新车间页面后生效' : '',
        ].filter(Boolean);
        notifications.show({ title: '车间设置已保存', message: parts.join('；') || (data.managed ? '已生效。字号在重新打开车间时生效。' : '服务未由 nblane 管理，安装 / 接管后生效。'), color: 'green' });
      },
    });
  return (
    <SettingsCard icon={<IconDeviceMobile size={22} />} title="终端显示与输入" description="默认值来自手机实测：Canvas 渲染 + 字形缩放修复安卓上汉字糊字；关掉 tmux 备用屏幕后，手机才能上下滑动翻历史。">
      <SimpleGrid cols={{ base: 1, sm: 2 }}>
        <NumberInput label="手机字号" description="触屏设备打开车间时使用" min={10} max={40} value={draft.font_size_mobile} onChange={num('font_size_mobile')} />
        <NumberInput label="电脑字号" min={10} max={40} value={draft.font_size_desktop} onChange={num('font_size_desktop')} />
      </SimpleGrid>
      <Stack gap={4}>
        <Text size="sm" fw={500}>渲染方式</Text>
        <SegmentedControl w="fit-content" aria-label="渲染方式" value={draft.renderer} onChange={(value) => set('renderer', value)} data={RENDERERS} />
        <Text size="xs" c="dimmed">Canvas 最稳；WebGL 滚动最快，但部分安卓 GPU 会糊字；DOM 最慢、兼容性最好。</Text>
      </Stack>
      <Switch label="超宽字形缩放回格子（修复中文/符号叠字）" checked={draft.rescale_glyphs} onChange={(event) => set('rescale_glyphs', event.currentTarget.checked)} />
      <Divider />
      <Switch
        label="浏览器原生滚动（手机可滑动翻历史）"
        description="关闭 tmux 备用屏幕，内容写进网页终端自己的滚动区。代价：全屏程序退出后，旧画面会留在历史里。"
        checked={draft.native_scroll}
        onChange={(event) => set('native_scroll', event.currentTarget.checked)}
      />
      <Switch
        label="tmux 鼠标模式"
        description="开启后可点选 tmux 窗格、拖动调整大小，但手机上的滑动会变成选字而不是滚动。"
        checked={draft.mouse}
        onChange={(event) => set('mouse', event.currentTarget.checked)}
      />
      <Switch label="显示 tmux 状态栏" checked={draft.status_bar} onChange={(event) => set('status_bar', event.currentTarget.checked)} />
      <SimpleGrid cols={{ base: 1, sm: 3 }}>
        <NumberInput label="网页滚动行数" min={1000} max={100000} step={1000} value={draft.scrollback} onChange={num('scrollback')} />
        <NumberInput label="tmux 历史行数" min={1000} max={200000} step={1000} value={draft.history_limit} onChange={num('history_limit')} />
        <NumberInput label="Esc 等待（毫秒）" description="越小 Esc 越跟手" min={0} max={500} value={draft.escape_time_ms} onChange={num('escape_time_ms')} />
      </SimpleGrid>
      <TextInput label="新会话工作目录" description="留空 = 服务用户的 home 目录；只影响新建的 tmux 会话" placeholder="/home/ubuntu/nblane" value={draft.cwd} onChange={(event) => set('cwd', event.currentTarget.value)} />
      <Group gap="xs">
        <Button size="xs" leftSection={<IconDeviceFloppy size={14} />} disabled={!dirty} loading={save.isPending} onClick={submit}>保存并应用</Button>
        {dirty && <Button size="xs" variant="default" onClick={reset}>放弃修改</Button>}
        <Button size="xs" variant="subtle" leftSection={<IconRestore size={14} />} disabled={isDefault} onClick={() => setDraft(data.defaults)}>恢复默认</Button>
      </Group>
      <ErrorAlert error={save.error} />
    </SettingsCard>
  );
}

function HappyCard({ data }: { data: WorkshopServiceStatus }) {
  const happy = data.happy;
  return (
    <SettingsCard icon={<IconDeviceMobile size={22} />} title="Happy Coder（手机看 Claude Code / Codex）" description="开源的手机客户端：把 Agent 会话渲染成聊天界面，权限请求和出错会推送到手机。车间负责终端，Happy 负责看进度和审批。">
      <Group gap="xs">
        <Badge color={happy.installed ? 'green' : 'gray'} variant="light">{happy.installed ? 'CLI 已安装' : 'CLI 未安装'}</Badge>
        {happy.installed && <Badge color={happy.paired ? 'green' : 'yellow'} variant="light">{happy.paired ? '已配对手机' : '未配对'}</Badge>}
        {happy.installed && <Badge color={happy.daemon_running ? 'green' : 'gray'} variant="outline">{happy.daemon_running ? '后台服务运行中' : '后台服务未运行'}</Badge>}
      </Group>
      <List type="ordered" size="sm" spacing="sm">
        <List.Item>
          <Text size="sm">手机安装 Happy App（App Store / Google Play 搜索「Happy Codex Claude Code」），或用网页版。</Text>
        </List.Item>
        <List.Item>
          <Text size="sm">服务器安装 CLI（在车间终端里运行即可）{happy.installed ? '——已完成' : ''}：</Text>
          <Code block>npm install -g happy</Code>
          <Text size="xs" c="dimmed">npm 包 happy 的仓库是 github.com/slopus/happy；旧包名 happy-coder 已停更。</Text>
        </List.Item>
        <List.Item>
          <Text size="sm">首次配对（需要第二块屏幕：在电脑上打开车间或 SSH 运行，用手机 App 扫终端里的二维码）{happy.paired ? '——已完成' : ''}：</Text>
          <Code block>happy auth login</Code>
        </List.Item>
        <List.Item>
          <Text size="sm">日常在车间里用 happy 代替原命令，手机上就能看到同一个会话：</Text>
          <Code block>{`happy            # 代替 claude
happy codex      # 代替 codex
happy --continue # 继续当前目录最近的 Claude 会话
happy --resume   # 从列表选一个历史 Claude 会话继续`}</Code>
          <Text size="xs" c="dimmed">同一个 Claude 会话不要同时开两个进程（先退出 tmux 里的 claude，再 happy --resume），否则记录会分叉。</Text>
        </List.Item>
        <List.Item>
          <Text size="sm">可选：让手机能直接新开会话{happy.daemon_running ? '——已在运行' : ''}：</Text>
          <Code block>happy daemon start</Code>
        </List.Item>
      </List>
      <Text size="xs" c="dimmed">
        会话内容经 Happy 的中继服务器同步（端到端加密，服务器看不到明文）。详见 <Anchor href="https://happy.engineering/" target="_blank" rel="noopener noreferrer" size="xs">happy.engineering</Anchor> · <Anchor href="https://github.com/slopus/happy" target="_blank" rel="noopener noreferrer" size="xs">GitHub</Anchor>。
      </Text>
    </SettingsCard>
  );
}

export function WorkshopSection() {
  const status = useWorkshopService();
  if (status.isPending) return <Center py="xl"><Loader /></Center>;
  if (status.isError) return <ErrorAlert error={status.error} />;
  return (
    <Stack gap="lg">
      <ServiceCard data={status.data} refetch={() => void status.refetch()} fetching={status.isFetching} />
      <SettingsFormCard data={status.data} />
      <HappyCard data={status.data} />
    </Stack>
  );
}
