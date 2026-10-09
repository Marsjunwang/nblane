// Settings shell: 系统 (deployment-wide, admin only, changes apply at once),
// 档案 (per profile, edited as a draft and saved via the SaveBar) and 账号
// (the signed-in user, visible to everyone, not tied to a profile).
// Each section has its own URL: /settings/<section>?profile=<name>.

import { Alert, Box, Center, Group, Loader, NavLink, Paper, Select, Stack, Text, Title } from '@mantine/core';
import { IconBook2, IconCpu, IconStairsUp, IconUserCircle, IconUsers, IconLanguage, IconPlugConnected, IconRobot, IconRoute, IconTerminal2 } from '@tabler/icons-react';
import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import { Link, Navigate, useNavigate, useParams, useSearchParams } from 'react-router-dom';

import { useMe, useProfiles } from '../api/hooks';
import { AgentsAndBackupSection } from '../components/settings/AgentSetupSections';
import { chrome } from '../theme';
import { AccountsSection, MyAccountSection } from './settings/AccountSections';
import { LocalServicesSection } from './settings/LocalServicesSection';
import { ProfileAIRoutingSection, ProfileGeneralSection, ProfileResearchSection, ProfileSkillProgressionSection } from './settings/ProfileSections';
import { SettingsDirtyContext, ErrorAlert } from './settings/shared';
import { SystemAISection } from './settings/SystemAISection';
import { WorkshopSection } from './settings/WorkshopSection';

type Section = {
  key: string;
  label: string;
  description: string;
  icon: ReactNode;
  scope: 'system' | 'profile' | 'user';
  render: (profile: string) => ReactNode;
};

const SECTIONS: Section[] = [
  { key: 'ai-service', label: 'AI 服务', description: 'AI 连接与 Codex CLI 状态', icon: <IconPlugConnected size={16} />, scope: 'system', render: () => <SystemAISection /> },
  { key: 'local-services', label: '本地服务', description: '本地翻译模型与 GROBID', icon: <IconCpu size={16} />, scope: 'system', render: () => <LocalServicesSection /> },
  { key: 'workshop', label: '车间终端', description: '网页终端、手机快捷输入与 Happy', icon: <IconTerminal2 size={16} />, scope: 'system', render: () => <WorkshopSection /> },
  { key: 'agents', label: '助手与备份', description: '个人 Agent 安装接入与数据备份', icon: <IconRobot size={16} />, scope: 'system', render: () => <AgentsAndBackupSection /> },
  { key: 'accounts', label: '账号管理', description: '用户、密码重置与助手 token', icon: <IconUsers size={16} />, scope: 'system', render: () => <AccountsSection /> },
  { key: 'general', label: '通用', description: '界面与 AI 回复语言', icon: <IconLanguage size={16} />, scope: 'profile', render: (profile) => <ProfileGeneralSection key={profile} profile={profile} /> },
  { key: 'research', label: '研究与阅读', description: 'Reader 默认值、翻译、研究 AI', icon: <IconBook2 size={16} />, scope: 'profile', render: (profile) => <ProfileResearchSection key={profile} profile={profile} /> },
  { key: 'ai-routing', label: 'AI 路由', description: '工作流 AI 与 Codex 参数', icon: <IconRoute size={16} />, scope: 'profile', render: (profile) => <ProfileAIRoutingSection key={profile} profile={profile} /> },
  { key: 'skill-progression', label: '技能进阶', description: '证据分值与晋升门槛', icon: <IconStairsUp size={16} />, scope: 'profile', render: (profile) => <ProfileSkillProgressionSection key={profile} profile={profile} /> },
  { key: 'account', label: '我的账号', description: '修改密码、登出所有设备', icon: <IconUserCircle size={16} />, scope: 'user', render: () => <MyAccountSection /> },
];

const LEAVE_PROMPT = '有未保存的修改，确定离开吗？';

export function SettingsPage() {
  const me = useMe();
  const profiles = useProfiles();
  const { section: sectionKey = '' } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [dirty, setDirty] = useState(false);
  const reportDirty = useCallback((value: boolean) => setDirty(value), []);

  useEffect(() => {
    if (!dirty) return undefined;
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); };
    window.addEventListener('beforeunload', warn);
    return () => window.removeEventListener('beforeunload', warn);
  }, [dirty]);

  const isAdmin = me.data?.role === 'admin';
  const visible = useMemo(() => SECTIONS.filter((item) => item.scope !== 'system' || isAdmin), [isAdmin]);
  const names = useMemo(() => (profiles.data ?? []).map((item) => item.name), [profiles.data]);
  const requestedProfile = searchParams.get('profile') ?? '';
  const profile = names.includes(requestedProfile) ? requestedProfile : names[0] ?? '';

  if (me.isPending || profiles.isPending) return <Center py="xl"><Loader /></Center>;
  if (me.isError) return <ErrorAlert error={me.error} />;
  if (profiles.isError) return <ErrorAlert error={profiles.error} />;

  const section = visible.find((item) => item.key === sectionKey);
  if (!section) return <Navigate to={`/settings/${visible[0].key}${profile ? `?profile=${encodeURIComponent(profile)}` : ''}`} replace />;

  const hrefFor = (key: string, nextProfile = profile) => `/settings/${key}${nextProfile ? `?profile=${encodeURIComponent(nextProfile)}` : ''}`;
  const go = (href: string) => {
    if (dirty && !window.confirm(LEAVE_PROMPT)) return;
    setDirty(false);
    navigate(href);
  };
  const groups: Array<{ scope: Section['scope']; title: string; hint: string }> = [
    ...(isAdmin ? [{ scope: 'system' as const, title: '系统', hint: '整个部署共用，修改立即生效' }] : []),
    { scope: 'profile', title: '档案', hint: '只影响所选档案，修改后保存' },
    { scope: 'user', title: '账号', hint: '当前登录的账号' },
  ];

  const profileSelect = names.length > 0 && (
    <Select
      aria-label="编辑档案"
      size="xs"
      value={profile}
      allowDeselect={false}
      onChange={(next) => next && go(hrefFor(section.scope === 'profile' ? section.key : 'general', next))}
      data={names.map((name) => ({ value: name, label: name }))}
    />
  );

  const nav = (
    <Stack gap="md">
      {groups.map((group) => (
        <Stack key={group.scope} gap={4}>
          <Text size="xs" fw={700} c={chrome.goldText}>{group.title}</Text>
          <Text size="xs" c="dimmed" mb={2}>{group.hint}</Text>
          {group.scope === 'profile' && profileSelect}
          {visible.filter((item) => item.scope === group.scope).map((item) => (
            <NavLink
              key={item.key}
              component={Link}
              to={hrefFor(item.key)}
              onClick={(event) => { event.preventDefault(); if (item.key !== section.key) go(hrefFor(item.key)); }}
              active={item.key === section.key}
              label={item.label}
              description={item.description}
              leftSection={item.icon}
              variant="light"
            />
          ))}
        </Stack>
      ))}
    </Stack>
  );

  const content = section.scope === 'profile' && !profile
    ? <Alert color="gray" title="暂无可编辑档案">当前账号没有可访问的档案。</Alert>
    : section.render(profile);

  return (
    <SettingsDirtyContext.Provider value={reportDirty}>
      <Stack gap="lg">
        <div>
          <Title order={2}>设置</Title>
          <Text c="dimmed" size="sm">{section.scope === 'profile' && profile ? `档案 ${profile} · ${section.label}` : `${section.scope === 'user' ? '账号' : '系统'} · ${section.label}`}</Text>
        </div>
        <Group align="flex-start" gap="lg" wrap="nowrap">
          <Paper withBorder radius="md" p="sm" w={240} visibleFrom="sm" style={{ position: 'sticky', top: 16, flexShrink: 0 }} component="nav" aria-label="设置目录">
            {nav}
          </Paper>
          <Box style={{ flex: 1, minWidth: 0 }}>
            <Stack gap="md">
              <Group hiddenFrom="sm" gap="xs" grow>
                <Select
                  aria-label="设置分区"
                  size="xs"
                  value={section.key}
                  allowDeselect={false}
                  onChange={(next) => next && go(hrefFor(next))}
                  data={groups.map((group) => ({ group: group.title, items: visible.filter((item) => item.scope === group.scope).map((item) => ({ value: item.key, label: item.label })) }))}
                />
                {section.scope === 'profile' && profileSelect}
              </Group>
              {content}
            </Stack>
          </Box>
        </Group>
      </Stack>
    </SettingsDirtyContext.Provider>
  );
}
