import { Alert, Button, Card, FileInput, Group, Loader, Stack, Tabs, Text, Textarea, TextInput, Title } from '@mantine/core';
import { IconBriefcase, IconFileUpload, IconSparkles } from '@tabler/icons-react';
import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { useCareerDraftExport, useCareerDraftSave, useCareerMatch, useCareerResumeSave, useCareerWorkspace } from '../api/hooks';

export function CareerWorkspacePage() {
  const { name = '' } = useParams();
  const career = useCareerWorkspace(name);
  const saveResume = useCareerResumeSave(name);
  const match = useCareerMatch(name);
  const saveDraft = useCareerDraftSave(name);
  const exportDraft = useCareerDraftExport(name);
  const [jd, setJd] = useState('');
  const [resumeText, setResumeText] = useState('');
  const [target, setTarget] = useState('target-role');
  const [draft, setDraft] = useState('');
  const [uploadError, setUploadError] = useState('');
  const [exportNotice, setExportNotice] = useState('');
  if (career.isPending) return <Group justify="center" py="xl"><Loader /></Group>;
  if (career.isError || !career.data) return <Alert color="red" title="求职工作台加载失败">{career.error?.message}</Alert>;
  const data = career.data.data;
  const resume = resumeText || data.resume_markdown;
  const runMatch = () => match.mutate({ resume_md: resume, jd_text: jd }, { onSuccess: (result) => setDraft(`<!-- Target: ${target} -->\n\n${resume}\n\n## 针对 JD 的人工修改提示\n\n${result.analysis.strengthen.map((item) => `- ${item}`).join('\n')}`) });
  const upload = async (file: File | null) => {
    if (!file) return;
    const form = new FormData(); form.append('file', file);
    const response = await fetch(`/api/v1/profiles/${encodeURIComponent(name)}/career/resume/upload`, { method: 'POST', body: form });
    const result = await response.json();
    if (result.error) setUploadError(result.error); else setResumeText(result.text || '');
  };
  return <Stack gap="lg" data-testid="career-workspace" style={{ maxWidth: 1440, margin: '0 auto', width: '100%' }}>
    <Group justify="space-between" align="flex-end" wrap="wrap"><div><Title order={2}><IconBriefcase size={24} style={{ verticalAlign: 'middle', marginRight: 8 }} />求职工作台</Title><Text size="sm" c="dimmed" mt={4}>简历、JD 匹配和定制草稿在一个可恢复的工作区完成。</Text></div><Button component={Link} to={`/p/${encodeURIComponent(name)}/content`} variant="subtle">内容工作台</Button></Group>
    <Tabs defaultValue="match"><Tabs.List><Tabs.Tab value="match" leftSection={<IconSparkles size={15} />}>JD 匹配</Tabs.Tab><Tabs.Tab value="resume">主简历</Tabs.Tab><Tabs.Tab value="drafts">定制草稿</Tabs.Tab></Tabs.List>
      <Tabs.Panel value="match" pt="md"><Group align="flex-start" grow wrap="wrap"><Card withBorder style={{ flex: '1 1 520px' }}><Stack><Textarea label="当前简历" value={resume} minRows={16} onChange={(e) => setResumeText(e.currentTarget.value)} /><Text size="xs" c="dimmed">可直接粘贴临时简历，或在“主简历”中保存结构化资料。</Text><Textarea label="职位描述（JD）" value={jd} minRows={12} onChange={(e) => setJd(e.currentTarget.value)} data-testid="career-jd" /><Button onClick={runMatch} loading={match.isPending} disabled={!resume.trim() || !jd.trim()} data-testid="career-match">开始匹配</Button></Stack></Card><Card withBorder style={{ flex: '1 1 360px' }}><Title order={4}>匹配结果</Title>{match.data ? <Stack mt="sm"><Text size="lg">匹配度 {match.data.analysis.score}%</Text><Text>{match.data.analysis.summary}</Text><Text size="sm"><b>已覆盖：</b>{match.data.analysis.covered.join('、') || '暂无'}</Text><Text size="sm"><b>真实缺口：</b>{match.data.analysis.gaps.join('、') || '暂无'}</Text></Stack> : <Text c="dimmed" mt="sm">输入 JD 后开始分析。分析只使用当前简历和 JD。</Text>}</Card></Group></Tabs.Panel>
      <Tabs.Panel value="resume" pt="md"><Card withBorder><Stack><TextInput label="姓名" value={String((data.resume.basics as Record<string, unknown> | undefined)?.name ?? '')} onChange={() => {}} /><FileInput label="上传 PDF / DOCX / TXT" leftSection={<IconFileUpload size={15} />} accept=".pdf,.docx,.txt" onChange={upload} /><Textarea label="简历摘要" minRows={14} value={resumeText || data.resume_markdown} onChange={(e) => setResumeText(e.currentTarget.value)} /><Button onClick={() => saveResume.mutate({ resume: { ...data.resume, summary: resumeText }, etag: data.resume_etag })} loading={saveResume.isPending}>保存主简历</Button>{uploadError && <Alert color="yellow">{uploadError}</Alert>}</Stack></Card></Tabs.Panel>
      <Tabs.Panel value="drafts" pt="md"><Card withBorder><Stack><TextInput label="目标岗位标识" value={target} onChange={(e) => setTarget(e.currentTarget.value)} /><Textarea label="定制简历草稿（人工确认后保存）" minRows={18} value={draft} onChange={(e) => setDraft(e.currentTarget.value)} /><Button disabled={!draft.trim()} onClick={() => saveDraft.mutate({ target, markdown: draft })} loading={saveDraft.isPending}>保存定制草稿</Button>{exportNotice && <Alert color="green">{exportNotice}</Alert>}{data.drafts.map((item) => <Group key={item.id} justify="space-between"><Text size="sm">{item.target} · 已保存</Text><Button size="compact-xs" variant="subtle" onClick={() => exportDraft.mutate(item.id, { onSuccess: (result) => setExportNotice(`已导出：${result.html_path}`) })}>导出 HTML + Markdown</Button></Group>)}</Stack></Card></Tabs.Panel>
    </Tabs>
  </Stack>;
}
