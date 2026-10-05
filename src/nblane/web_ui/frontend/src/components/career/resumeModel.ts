// Pure helpers over the structured resume (core/resume_doc.py owns the shape;
// the server normalizes on save, so the form may hold blank rows mid-edit).

import type { ResumeDoc, ResumeRecord } from '../../api/types';

export type RecordSection = 'experiences' | 'projects' | 'outputs' | 'education';

/** Per-section field names: [organisation field, role field] + labels. */
export const RECORD_FIELDS: Record<RecordSection, { org: string; role: string; orgLabel: string; roleLabel: string }> = {
  experiences: { org: 'company', role: 'role', orgLabel: '单位', roleLabel: '职位' },
  projects: { org: 'name', role: 'role', orgLabel: '项目', roleLabel: '角色' },
  outputs: { org: 'title', role: 'role', orgLabel: '成果', roleLabel: '说明' },
  education: { org: 'school', role: 'degree', orgLabel: '学校', roleLabel: '专业 / 学位' },
};

export const DEFAULT_TITLES: Record<string, string> = {
  summary: '个人概要',
  skills: '专业技能',
  experiences: '工作经历',
  projects: '项目经历',
  outputs: '成果',
  education: '教育经历',
  honors: '荣誉与其他',
};

export function emptyRecord(section: RecordSection): ResumeRecord {
  const { org, role } = RECORD_FIELDS[section];
  return { [org]: '', [role]: '', start: '', end: '', summary: '', bullets: [], groups: [] } as ResumeRecord;
}

export function sectionTitle(doc: ResumeDoc, key: string): string {
  return doc.section_titles?.[key] || DEFAULT_TITLES[key] || key;
}

export function moveItem<T>(items: T[], index: number, delta: number): T[] {
  const target = index + delta;
  if (target < 0 || target >= items.length) return items;
  const next = items.slice();
  const [item] = next.splice(index, 1);
  next.splice(target, 0, item);
  return next;
}

/** Textarea ⇄ list: keep blank lines while typing; the server drops them on save. */
export function linesToList(text: string): string[] {
  return text.split('\n');
}

export function listToLines(items: string[] | undefined): string {
  return (items ?? []).join('\n');
}

/** Imported resume replaces the content; identity, visibility and photo stay. */
export function mergeImported(current: ResumeDoc, imported: ResumeDoc): ResumeDoc {
  return {
    ...current,
    ...imported,
    profile: current.profile,
    visibility: current.visibility,
    basics: { ...imported.basics, photo: imported.basics.photo || current.basics.photo },
  };
}

export function resumeStats(doc: ResumeDoc): string {
  const parts = [
    doc.experiences.length ? `经历 ${doc.experiences.length} 段` : '',
    doc.projects.length ? `项目 ${doc.projects.length} 个` : '',
    doc.education.length ? `教育 ${doc.education.length} 段` : '',
    doc.skill_groups.length || doc.skills.length ? `技能 ${doc.skill_groups.length + doc.skills.length} 项` : '',
    doc.honors.length ? `荣誉 ${doc.honors.length} 条` : '',
  ].filter(Boolean);
  return parts.join(' · ') || '只有基本信息';
}

export function careerHomePath(profile: string): string {
  return `/p/${encodeURIComponent(profile)}/career`;
}

export function careerResumePath(profile: string): string {
  return `${careerHomePath(profile)}/resume`;
}

export function careerTargetPath(profile: string, id: string): string {
  return `${careerHomePath(profile)}/jobs/${encodeURIComponent(id)}`;
}

/** Mirrors core/career_workspace.clean_draft_id so the UI can predict the id. */
export function cleanDraftId(target: string): string {
  return target
    .trim()
    .replace(/[^a-zA-Z0-9一-鿿_-]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 80);
}
