import { Button } from '@mantine/core';
import { IconArrowLeft } from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';

// Settings and the assistant live outside /p/<profile>/…, so the profile
// navbar is gone there. AppLayout remembers the last business page per tab;
// these pages offer a one-click way back to it.
const LAST_WORK_PATH_KEY = 'nblane.nav.lastWorkPath';

const PAGE_LABELS: Array<[string, string]> = [
  ['home', '首页'],
  ['projects', '项目'],
  ['skill-tree', '技能树'],
  ['evidence', '证据'],
  ['research', '研究台'],
  ['content', '内容工作台'],
  ['career', '求职工作台'],
  ['public-build', '公开站点'],
];

export function isWorkPath(pathname: string): boolean {
  return /^\/p\/[^/]+\//.test(pathname);
}

export function rememberWorkPath(path: string): void {
  try {
    window.sessionStorage.setItem(LAST_WORK_PATH_KEY, path);
  } catch {
    // Storage blocked (private mode): the fallback target still works.
  }
}

export function lastWorkPath(): string {
  try {
    const value = window.sessionStorage.getItem(LAST_WORK_PATH_KEY) ?? '';
    return isWorkPath(value) ? value : '';
  } catch {
    return '';
  }
}

/** Profile home of the remembered page, or the profile list. */
export function lastWorkHome(): string {
  const match = /^\/p\/([^/]+)\//.exec(lastWorkPath());
  return match ? `/p/${match[1]}/home` : '/';
}

export function workPathLabel(path: string): string {
  const segment = /^\/p\/[^/?#]+\/([^/?#]+)/.exec(path)?.[1] ?? '';
  return PAGE_LABELS.find(([key]) => key === segment)?.[1] ?? '档案列表';
}

export function BackToWorkButton({ confirmLeave }: { confirmLeave?: () => boolean }) {
  const navigate = useNavigate();
  const target = lastWorkPath() || '/';
  return (
    <Button
      variant="subtle"
      size="compact-sm"
      leftSection={<IconArrowLeft size={14} />}
      data-testid="back-to-work"
      onClick={() => {
        if (confirmLeave && !confirmLeave()) return;
        navigate(target);
      }}
    >
      返回{workPathLabel(target)}
    </Button>
  );
}
