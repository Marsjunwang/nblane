import { AppShell, Badge, Burger, Button, Divider, Group, NavLink, Text, Title } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import {
  IconArrowLeft,
  IconBinaryTree2,
  IconBook2,
  IconCalendarWeek,
  IconCertificate,
  
  IconHeartbeat,
  IconHome,
  IconInbox,
  IconLayoutKanban,
  IconLogout,
  IconRobot,
  IconRocket,
  IconTarget,
  IconTimeline,
  IconUser,
  IconWriting,
  IconZoomQuestion,
} from '@tabler/icons-react';
import { NavLink as RouterNavLink, Link as RouterLink, Outlet, useLocation, useMatch, useNavigate } from 'react-router-dom';

import { useLogout, useMe } from '../api/hooks';

const NAV_ITEMS = [
  { label: '首页', path: 'home', icon: IconHome },
  { label: '看板', path: 'kanban', icon: IconLayoutKanban },
  { label: '技能树', path: 'skill-tree', icon: IconBinaryTree2 },
  { label: '目标', path: 'goals', icon: IconTarget },
  { label: '证据', path: 'evidence', icon: IconCertificate },
  { label: '差距分析', path: 'gap', icon: IconZoomQuestion },
  { label: '周回顾', path: 'review', icon: IconCalendarWeek },
  { label: '项目看板', path: 'project-board', icon: IconTimeline },
  { label: '输出工作室', path: 'studio', icon: IconWriting },
  { label: '公开构建', path: 'public-build', icon: IconRocket },
  { label: '研究台', path: 'research', icon: IconBook2 },
  { label: '收件箱', path: 'inbox', icon: IconInbox },
  { label: '代理活动', path: 'activity', icon: IconRobot },
  { label: '健康', path: 'health', icon: IconHeartbeat },
];

// Wide-viewport policy: every page's main column is centered and capped so
// tables/cards/forms do not stretch into unreadably long rows on 1920+
// monitors. The kanban board is the one page that genuinely uses the full
// width (its columns tile horizontally), so it opts out.
const CONTENT_MAX_WIDTH = 1400;
const FULL_BLEED_SEGMENTS = ['/kanban'];

export function AppLayout() {
  const me = useMe();
  const logout = useLogout();
  const navigate = useNavigate();
  const location = useLocation();
  const [navbarOpened, { toggle: toggleNavbar, close: closeNavbar }] = useDisclosure();
  const profileMatch = useMatch('/p/:name/*');
  const currentProfile = profileMatch?.params.name ?? '';
  const authEnabled = me.data?.auth_enabled ?? false;
  const fullBleed = FULL_BLEED_SEGMENTS.some((segment) => location.pathname.includes(segment));

  return (
    <AppShell
      header={{ height: 56 }}
      navbar={
        profileMatch
          ? { width: 220, breakpoint: 'sm', collapsed: { mobile: !navbarOpened } }
          : undefined
      }
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Group gap="sm">
            {profileMatch && (
              <Burger
                opened={navbarOpened}
                onClick={toggleNavbar}
                hiddenFrom="sm"
                size="sm"
                aria-label="切换导航"
              />
            )}
            <Title order={3}>nblane</Title>
            {currentProfile && (
              <Badge
                color="brand"
                variant="light"
                leftSection={<IconUser size={12} />}
                data-testid="current-profile"
              >
                {currentProfile}
              </Badge>
            )}
          </Group>
          <Group gap="sm">
            <Button
              component={RouterLink}
              to="/assistant"
              variant={location.pathname.startsWith('/assistant') ? 'light' : 'subtle'}
              size="compact-sm"
              leftSection={<IconRobot size={14} />}
            >
              助手
            </Button>
            {me.data && (
              <Text size="sm" c="dimmed">
                {me.data.display_name}
              </Text>
            )}
            {authEnabled && (
              <Button
                variant="subtle"
                size="compact-sm"
                leftSection={<IconLogout size={14} />}
                loading={logout.isPending}
                onClick={() => logout.mutate(undefined, { onSettled: () => navigate('/login') })}
              >
                退出登录
              </Button>
            )}
          </Group>
        </Group>
      </AppShell.Header>
      {profileMatch && (
        <AppShell.Navbar p="sm">
          {NAV_ITEMS.map((item) => {
            const basePath = `/p/${encodeURIComponent(currentProfile)}/${item.path}`;
            return (
              <NavLink
                key={item.path}
                component={RouterNavLink}
                to={basePath}
                label={item.label}
                leftSection={<item.icon size={16} />}
                active={
                  location.pathname === basePath ||
                  location.pathname.startsWith(`${basePath}/`)
                }
                onClick={closeNavbar}
              />
            );
          })}
          <Divider my="sm" />
          <NavLink
            component={RouterNavLink}
            to="/"
            label="档案列表"
            leftSection={<IconArrowLeft size={16} />}
            onClick={closeNavbar}
          />
        </AppShell.Navbar>
      )}
      <AppShell.Main>
        <div
          data-testid="page-container"
          data-layout={fullBleed ? 'wide' : 'capped'}
          style={
            fullBleed
              ? undefined
              : { maxWidth: CONTENT_MAX_WIDTH, marginInline: 'auto', width: '100%' }
          }
        >
          <Outlet />
        </div>
      </AppShell.Main>
    </AppShell>
  );
}
