import type {
  PublicSiteIntro,
  PublicSitePost,
  PublicSiteResponse,
  PublicSiteSettings,
  PublicSiteWork,
  PublicSiteLive,
} from '../../api/types';

/** Overview with every defaulted list/object filled in (OpenAPI marks them optional). */
export type PublicSiteView = PublicSiteResponse & {
  settings: PublicSiteSettings;
  intro: PublicSiteIntro;
  posts: PublicSitePost[];
  works: PublicSiteWork[];
  errors: string[];
  warnings: string[];
};

export function siteView(data: PublicSiteResponse): PublicSiteView {
  return {
    ...data,
    settings: data.settings ?? {
      show_photo: true,
      show_email: false,
      show_phone: false,
      resume_pdf: false,
      show_projects: false,
      base_url: '',
    },
    intro: data.intro ?? {
      name: data.profile,
      english_name: '',
      title: '',
      summary: '',
      photo: '',
      photo_url: '',
      phone: '',
      email: '',
      has_resume: false,
    },
    posts: data.posts ?? [],
    works: data.works ?? [],
    errors: data.errors ?? [],
    warnings: data.warnings ?? [],
  };
}

export const WORK_TYPE_OPTIONS = [
  { value: 'video', label: '视频' },
  { value: 'paper', label: '论文' },
  { value: 'article', label: '文章' },
  { value: 'demo', label: '演示' },
  { value: 'code', label: '代码' },
  { value: 'talk', label: '演讲' },
  { value: 'other', label: '其他' },
];

export function workTypeLabel(type: string): string {
  return WORK_TYPE_OPTIONS.find((option) => option.value === type)?.label ?? type;
}

export function emptyWork(): PublicSiteWork {
  return {
    id: '',
    title: '',
    type: 'video',
    year: String(new Date().getFullYear()),
    summary: '',
    video: '',
    video_mode: 'embed',
    cover: '',
    links: [],
    status: 'draft',
    featured: false,
  };
}

export type VideoKind = '' | 'local' | 'embed' | 'direct' | 'link';

const EMBED_HOSTS = ['youtube.com', 'm.youtube.com', 'youtu.be', 'vimeo.com', 'player.vimeo.com', 'player.bilibili.com'];
const DIRECT_VIDEO = /\.(mp4|webm)(\?.*)?$/i;

/**
 * How the static site will render a work video (mirrors
 * `_render_video_block` / `_whitelisted_video_embed` in core/public_site.py):
 * local files and whitelisted hosts play inline, anything else is a link.
 */
export function videoKind(src: string): VideoKind {
  const value = src.trim();
  if (!value) return '';
  if (!/^https?:\/\//i.test(value)) return DIRECT_VIDEO.test(value) ? 'local' : 'link';
  let host = '';
  let path = '';
  try {
    const url = new URL(value);
    host = url.hostname.toLowerCase().replace(/^www\./, '');
    path = url.pathname;
  } catch {
    return 'link';
  }
  if (EMBED_HOSTS.includes(host)) return 'embed';
  if ((host === 'bilibili.com' || host === 'm.bilibili.com') && /^\/video\/BV[0-9A-Za-z]{10}/.test(path)) {
    return 'embed';
  }
  return DIRECT_VIDEO.test(path) ? 'direct' : 'link';
}

export function videoHint(work: PublicSiteWork): string {
  const kind = videoKind(work.video);
  if (!kind) return '';
  if (work.video_mode === 'link') return '网站上显示为「观看视频」链接。';
  if (kind === 'link') return '这个网址不支持内嵌播放，网站上会显示为链接。支持 B 站、YouTube、Vimeo 或 mp4/webm。';
  return kind === 'embed' ? '网站上直接内嵌播放。' : '网站上用播放器直接播放。';
}

/** Problems that block saving (the server also enforces titles). */
export function worksIssues(works: PublicSiteWork[]): string[] {
  const issues: string[] = [];
  works.forEach((work, index) => {
    if (!work.title.trim()) issues.push(`第 ${index + 1} 条作品缺少标题`);
    (work.links ?? []).forEach((link) => {
      const url = link.url.trim();
      const scheme = /^([a-z][a-z0-9+.-]*):/i.exec(url)?.[1]?.toLowerCase();
      if (scheme && !['http', 'https', 'mailto'].includes(scheme)) {
        issues.push(`「${work.title || `第 ${index + 1} 条`}」的链接协议 ${scheme}: 不安全`);
      }
    });
  });
  return issues;
}

/** Strip empty link rows before sending. */
export function cleanWorks(works: PublicSiteWork[]): PublicSiteWork[] {
  return works.map((work) => ({
    ...work,
    title: work.title.trim(),
    links: (work.links ?? [])
      .map((link) => ({ label: link.label.trim(), url: link.url.trim() }))
      .filter((link) => link.url),
  }));
}

export function moveItem<T>(items: T[], index: number, delta: number): T[] {
  const target = index + delta;
  if (target < 0 || target >= items.length) return items;
  const next = [...items];
  [next[index], next[target]] = [next[target], next[index]];
  return next;
}

export function liveChangeCount(live: PublicSiteLive): number {
  return (live.added?.length ?? 0) + (live.changed?.length ?? 0) + (live.removed?.length ?? 0);
}

/** One-line summary of what the next deploy changes. */
export function liveSummary(live: PublicSiteLive | null | undefined): string {
  if (!live) return '';
  if (!live.exists) return '线上还没有网站，发布后首次上线。';
  if (live.in_sync) return '线上已是最新。';
  const parts: string[] = [];
  if (live.added?.length) parts.push(`新增 ${live.added.length} 页`);
  if (live.changed?.length) parts.push(`更新 ${live.changed.length} 页`);
  if (live.removed?.length) parts.push(`下线 ${live.removed.length} 页`);
  if (live.pdf_pending) parts.push('简历 PDF 有变化');
  return `待发布：${parts.join('，')}`;
}

export function formatTime(iso: string): string {
  if (!iso) return '';
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso : date.toLocaleString('zh-CN', { hour12: false });
}

/** "blog/a/index.html" → "/blog/a/" for display. */
export function pageLabel(path: string): string {
  return `/${path.replace(/index\.html$/, '')}`;
}
