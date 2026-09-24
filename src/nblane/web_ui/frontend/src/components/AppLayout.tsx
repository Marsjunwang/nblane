import { AppShell, Badge, Burger, Button, Divider, Group, NavLink, Text, Title, Tooltip } from '@mantine/core';
import { useDisclosure, useLocalStorage, useMediaQuery } from '@mantine/hooks';
import {
  IconArrowLeft,
  IconBinaryTree2,
  IconBook2,
  IconCalendarWeek,
  IconCertificate,
  IconChevronsLeft,
  IconChevronsRight,

  IconHome,
  IconInbox,
  IconLogout,
  IconRobot,
  IconRocket,
  IconTerminal2,
  IconTimeline,
  IconUser,
  IconWriting,
  IconZoomQuestion,
} from '@tabler/icons-react';
import { NavLink as RouterNavLink, Link as RouterLink, Outlet, useLocation, useMatch, useNavigate } from 'react-router-dom';

import { useLogout, useMe } from '../api/hooks';
import { chrome } from '../theme';

const NAV_ITEMS = [
  { label: '首页', path: 'home', icon: IconHome },
  { label: '项目', path: 'projects', icon: IconTimeline },
  { label: '技能树', path: 'skill-tree', icon: IconBinaryTree2 },
  { label: '证据', path: 'evidence', icon: IconCertificate },
  { label: '差距分析', path: 'gap', icon: IconZoomQuestion },
  { label: '周回顾', path: 'review', icon: IconCalendarWeek },
  { label: '输出工作室', path: 'studio', icon: IconWriting },
  { label: '公开构建', path: 'public-build', icon: IconRocket },
  { label: '研究台', path: 'research', icon: IconBook2 },
  { label: '收件箱', path: 'inbox', icon: IconInbox },
  { label: '代理活动', path: 'activity', icon: IconRobot },
];

// Wide-viewport policy: every page's main column is centered and capped so
// tables/cards/forms do not stretch into unreadably long rows on 1920+
// monitors. The home starmap (immersive, one continuous indigo surface), the
// projects board (swimlane columns tile horizontally) and the workshop
// terminal (xterm fills the viewport) genuinely use the full width, so they
// opt out.
const CONTENT_MAX_WIDTH = 1400;
const FULL_BLEED_SEGMENTS = ['/home', '/projects', '/workshop'];
// The home starmap additionally drops the AppShell padding entirely: no
// visible frame or color seam around the chart-indigo canvas.
const IMMERSIVE_SEGMENTS = ['/home'];

// Icon-rail sidebar (2026-09-23 dark unification): desktop default is a 56px
// icon-only rail with tooltip labels and a gold active indicator; a toggle
// temporarily expands it to the full labeled rail (persisted). On mobile the
// navbar stays the labelled off-canvas drawer it always was.
const RAIL_WIDTH_COLLAPSED = 56;
const RAIL_WIDTH_EXPANDED = 220;
const MOBILE_DRAWER_WIDTH = 260;
const RAIL_EXPANDED_STORAGE_KEY = 'nblane.nav.rail.expanded';

export function AppLayout() {
  const me = useMe();
  const logout = useLogout();
  const navigate = useNavigate();
  const location = useLocation();
  const [navbarOpened, { toggle: toggleNavbar, close: closeNavbar }] = useDisclosure();
  const [railExpanded, setRailExpanded] = useLocalStorage({
    key: RAIL_EXPANDED_STORAGE_KEY,
    defaultValue: false,
  });
  const isDesktop = useMediaQuery('(min-width: 48em)') ?? true;
  const profileMatch = useMatch('/p/:name/*');
  const currentProfile = profileMatch?.params.name ?? '';
  const authEnabled = me.data?.auth_enabled ?? false;
  const fullBleed = FULL_BLEED_SEGMENTS.some((segment) => location.pathname.includes(segment));
  const immersive = IMMERSIVE_SEGMENTS.some((segment) => location.pathname.includes(segment));
  const railWidth = railExpanded ? RAIL_WIDTH_EXPANDED : RAIL_WIDTH_COLLAPSED;
  // Mobile drawer entries always carry labels; the desktop rail shows them
  // only while expanded.
  const showLabels = railExpanded || !isDesktop;

  const renderNavLink = (item: { label: string; path: string; icon: typeof IconHome }) => {
    const basePath = item.path.startsWith('/')
      ? item.path
      : `/p/${encodeURIComponent(currentProfile)}/${item.path}`;
    const active =
      item.path !== '/' &&
      (location.pathname === basePath || location.pathname.startsWith(`${basePath}/`));
    return (
      <Tooltip
        key={item.path}
        label={item.label}
        position="right"
        withinPortal
        disabled={showLabels}
      >
        <NavLink
          component={RouterNavLink}
          to={basePath}
          label={showLabels ? item.label : undefined}
          aria-label={item.label}
          leftSection={<item.icon size={18} />}
          active={active}
          onClick={closeNavbar}
          styles={{
            root: {
              borderRadius: showLabels ? undefined : 'var(--mantine-radius-sm)',
              ...(active ? { boxShadow: `inset 2px 0 0 ${chrome.gold}` } : {}),
            },
            section: { marginInlineEnd: showLabels ? undefined : 0 },
          }}
        />
      </Tooltip>
    );
  };

  return (
    <AppShell
      header={{ height: 56 }}
      navbar={
        profileMatch
          ? {
              width: { base: MOBILE_DRAWER_WIDTH, sm: railWidth },
              breakpoint: 'sm',
              collapsed: { mobile: !navbarOpened },
            }
          : undefined
      }
      padding={immersive ? 0 : 'md'}
    >
      <AppShell.Header style={{ background: chrome.panelBg }}>
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
              to="/workshop"
              variant={location.pathname.startsWith('/workshop') ? 'light' : 'subtle'}
              size="compact-sm"
              leftSection={<IconTerminal2 size={14} />}
            >
              车间
            </Button>
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
        <AppShell.Navbar p={showLabels ? 'sm' : 'xs'} style={{ background: chrome.panelBg }}>
          {NAV_ITEMS.map(renderNavLink)}
          <Divider my="sm" />
          {renderNavLink({ label: '档案列表', path: '/', icon: IconArrowLeft })}
          {isDesktop && (
            <>
              <Divider my="sm" />
              <Tooltip
                label={railExpanded ? '收起导航' : '展开导航'}
                position="right"
                withinPortal
                disabled={showLabels}
              >
                <NavLink
                  component="button"
                  label={showLabels ? (railExpanded ? '收起导航' : '展开导航') : undefined}
                  aria-label={railExpanded ? '收起导航' : '展开导航'}
                  leftSection={
                    railExpanded ? <IconChevronsLeft size={18} /> : <IconChevronsRight size={18} />
                  }
                  onClick={() => setRailExpanded((value) => !value)}
                  data-testid="rail-toggle"
                  styles={{ section: { marginInlineEnd: showLabels ? undefined : 0 } }}
                />
              </Tooltip>
            </>
          )}
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
