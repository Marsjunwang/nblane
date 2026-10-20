import { Alert, Badge, Button, FileButton, Group, Loader, Modal, Paper, Select, SimpleGrid, Stack, Text, Textarea } from '@mantine/core';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef, useState } from 'react';
import { apiGet, apiPost } from '../../api/client';
import type { ContentMedia } from '../../api/types';
import { ImagePreview } from './ImagePreview';
import { imageApiPath, imageQueryKey, imageUrl, uploadImageReference, useImageRuns } from './imageApi';
import type { ImageEditRequest, ImageRun, ImageTarget } from './imageTypes';

export function ImageWorkspace({ profile, slug, opened, request, enabled, media, draft, onClose, onApply, canApply, retarget }: {
  profile: string; slug: string; opened: boolean; request: ImageEditRequest | null; enabled: boolean;
  media: ContentMedia[]; draft: { title: string; summary: string; tags: string[]; body: string };
  onClose: () => void; canApply: (target: ImageTarget) => boolean;
  onApply: (target: ImageTarget, path: string) => boolean;
  retarget?: (target: ImageTarget, appliedPath: string) => ImageTarget | null;
}) {
  const queryClient = useQueryClient();
  const runs = useImageRuns(profile, slug);
  const [form, setForm] = useState<ImageEditRequest | null>(request);
  const [instruction, setInstruction] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [notice, setNotice] = useState('');
  const formTop = useRef<HTMLDivElement>(null);
  const quality = form?.reference && form.quality === 'ultra' ? 'high' : form?.quality ?? 'standard';
  const aspect = form?.aspect ?? (form?.mode === 'edit' ? 'original' : '16:9');
  const dimensions = useQuery({
    queryKey: ['image-size', profile, slug, form?.mode, form?.reference, quality, aspect],
    queryFn: () => apiGet<{ width: number; height: number; supports_4k: boolean }>(`${imageApiPath(profile)}/size?${new URLSearchParams({ slug, mode: form!.mode, reference: form!.reference, quality, aspect })}`),
    enabled: opened && !!form && (aspect !== 'original' || !!form.reference), retry: false,
  });
  useEffect(() => { setForm(request); setInstruction(request?.instruction ?? ''); setError(''); setNotice(''); }, [request]);
  const refresh = () => queryClient.invalidateQueries({ queryKey: imageQueryKey(profile, slug) });
  const fail = (err: unknown) => setError(err instanceof Error ? err.message : String(err));
  const edit = (next: ImageEditRequest) => {
    setForm(next); setInstruction(next.instruction ?? ''); setError(''); setNotice('');
    formTop.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };
  const generate = async () => {
    if (!form) return;
    setBusy(true); setError(''); setNotice('');
    try {
      await apiPost(`/profiles/${encodeURIComponent(profile)}/jobs`, { kind: 'content-image', input: { ...draft, ...form, quality, aspect, slug, instruction } });
      setNotice('任务已提交，关闭面板不影响生成；候选将显示在下方。');
      await refresh();
    } catch (err) { fail(err); } finally { setBusy(false); }
  };
  const selectReference = (reference: string) => setForm((current) => current ? {
    ...current, reference, quality: reference && current.quality === 'ultra' ? 'high' : current.quality,
    aspect: !reference && (current.aspect ?? (current.mode === 'edit' ? 'original' : '16:9')) === 'original' ? '16:9' : current.aspect,
  } : current);
  const upload = async (file: File | null) => {
    if (!file) return;
    setUploading(true); setError('');
    try {
      const result = await uploadImageReference(profile, slug, file);
      selectReference(result.path);
    } catch (err) { fail(err); } finally { setUploading(false); }
  };
  const candidateTarget = (run: ImageRun, candidate: ImageRun['candidates'][number]) =>
    candidate.applied_path ? retarget?.(run.request.target, candidate.applied_path) ?? run.request.target : run.request.target;
  const accept = async (run: ImageRun, candidate: ImageRun['candidates'][number], asMedia = false) => {
    const target: ImageTarget = asMedia ? { kind: 'media' } : candidateTarget(run, candidate);
    if (!canApply(target)) { setError('原图已改变、被删除或当前处于 MD 模式。候选已保留，可保存为新媒体后再插入。'); return; }
    setBusy(true); setError('');
    try {
      const result = await apiPost<{ path: string }>(`${imageApiPath(profile)}/accept`, { slug, run_id: run.id, candidate_path: candidate.candidate_path });
      // Recheck after the request: the writer may have changed the target meanwhile.
      if (!onApply(target, result.path)) setError('原图已改变；结果已保存到媒体库，没有覆盖当前内容。');
      else setNotice(target.kind === 'media' ? '已保存为新媒体图片。' : target.kind === 'cover' ? '已更新封面，正在自动保存。' : '已替换当前图片，可用撤销恢复。');
      await queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'content', 'media', slug] });
      await refresh();
    } catch (err) { fail(err); } finally { setBusy(false); }
  };
  const discard = async (run: ImageRun, candidatePath = '') => {
    // A discarded candidate is deleted from disk; a misclick would lose a
    // paid generation. Failed-run records carry no image, so no prompt.
    if (candidatePath && !window.confirm('丢弃这张候选图？丢弃后无法找回（已保存到媒体库的不受影响）。')) return;
    setBusy(true); setError('');
    try { await apiPost(`${imageApiPath(profile)}/discard`, { slug, run_id: run.id, candidate_path: candidatePath }); await refresh(); }
    catch (err) { fail(err); } finally { setBusy(false); }
  };
  const mediaOptions = media.filter((item) => item.kind === 'image').map((item) => ({ value: item.path, label: item.name }));
  return <Modal opened={opened} onClose={onClose} title="图片工作台" closeButtonProps={{ 'aria-label': '关闭图片工作台', size: 44 }} size="min(1100px, 96vw)" data-testid="image-workspace">
    <Stack gap="md">
      {error && <Alert color="red">{error}</Alert>}
      {notice && <Alert color="blue">{notice}</Alert>}
      {!enabled && <Alert color="yellow">未配置图像服务，仍可查看和使用已有候选。</Alert>}
      {form && <Paper withBorder p="md" ref={formTop}>
        <Stack>
          <Text fw={600}>{form.mode === 'cover' ? '生成封面' : '修改图片'}</Text>
          <Text size="sm" c="dimmed">{form.mode === 'cover' ? '根据文章主题生成封面插画，可添加参考图。' : '以参考图为基础，保留未要求改变的内容，默认沿用原图比例，也可选择其他输出比例。'}</Text>
          {form.reference && <ImagePreview src={imageUrl(profile, form.reference)} alt="参考图" height={260} />}
          <Group align="end">
            <Select label="从媒体选择参考图" placeholder="选择已有图片" searchable clearable data={mediaOptions} value={mediaOptions.some((item) => item.value === form.reference) ? form.reference : null}
              onChange={(value) => selectReference(value ?? '')} style={{ flex: 1, minWidth: 180 }} />
            <FileButton accept="image/png,image/jpeg,image/webp,image/gif" onChange={(file) => void upload(file)}>{(props) => <Button mih={44} {...props} variant="default" loading={uploading}>上传参考图</Button>}</FileButton>
            {form.reference && <Button mih={44} variant="subtle" onClick={() => selectReference('')}>移除参考图</Button>}
          </Group>
          <SimpleGrid cols={{ base: 1, sm: 2 }}>
            <Select label="清晰度" allowDeselect={false} value={quality} data={[
              { value: 'standard', label: '标准 · 约 100 万像素' },
              { value: 'high', label: '高清 · 约 400 万像素' },
              ...(dimensions.data?.supports_4k ? [{ value: 'ultra', label: '超清 4K · 约 1600 万像素' }] : []),
            ]} onChange={(value) => setForm({ ...form, quality: value as ImageEditRequest['quality'] })} />
            <Select label="输出比例" allowDeselect={false} value={aspect} data={[
              { value: 'original', label: '保持原图比例', disabled: !form.reference },
              ...['16:9', '1:1', '4:3', '3:4', '9:16'].map((value) => ({ value, label: value })),
            ]} onChange={(value) => setForm({ ...form, aspect: value as ImageEditRequest['aspect'] })} />
          </SimpleGrid>
          {dimensions.data && <Text size="sm" c="dimmed">输出尺寸：{dimensions.data.width} × {dimensions.data.height} 像素{aspect === 'original' ? ' · 按原图比例自动适配清晰度' : ''}</Text>}
          {dimensions.isFetching && <Text size="sm" c="dimmed">正在计算输出尺寸…</Text>}
          {dimensions.error && <Alert color="red">{dimensions.error.message}</Alert>}
          <Textarea label={form.mode === 'cover' ? '画面描述（可选）' : '修改要求'} placeholder="例如：保留人物和全部文字，去掉左右黑边" autosize minRows={3} maxRows={10} maxLength={4000} value={instruction} onChange={(event) => setInstruction(event.currentTarget.value)} />
          {form.mode === 'edit' && <Group gap="xs">{['提高清晰度，保留所有原有内容', '调整背景，保留主体和文字', '修改图中文字：'].map((value) => <Button mih={44} key={value} size="xs" variant="subtle" onClick={() => setInstruction(value)}>{value.split('，')[0]}</Button>)}</Group>}
          <Button mih={44} onClick={() => void generate()} loading={busy} disabled={!enabled || uploading || !dimensions.data || dimensions.isFetching || !!dimensions.error || (form.mode === 'edit' && (!form.reference || !instruction.trim()))}>{form.mode === 'cover' ? '生成封面候选' : '生成修改图'}</Button>
        </Stack>
      </Paper>}
      <Group justify="space-between"><Text fw={600}>图片任务与候选</Text><Button mih={44} variant="subtle" onClick={() => void refresh()}>刷新</Button></Group>
      {runs.isPending && <Loader size="sm" />}
      {runs.error && <Alert color="red">候选列表读取失败：{runs.error.message}</Alert>}
      {runs.data?.runs.length === 0 && <Text c="dimmed">还没有图片任务。生成后的候选会保留在这里，刷新后也能找回。</Text>}
      {runs.data?.runs.map((run) => <Paper key={run.id} withBorder p="md" data-testid="image-run">
        <Stack gap="sm">
          <Group><Badge>{run.request.mode === 'cover' ? '封面生成' : '图片修改'}</Badge><Text size="sm">{run.request.instruction || '根据文章主题生成'}</Text>{run.output_size && <Badge variant="outline">{run.output_size.replace('*', ' × ')} 像素</Badge>}</Group>
          {run.status === 'running' && <Group><Loader size="sm" /><Text>正在生成，关闭面板不影响任务…</Text></Group>}
          {run.status === 'failed' && <Alert color="red">{run.error}</Alert>}
          {run.candidates.map((candidate) => <Stack key={candidate.candidate_path} gap="sm">
            <SimpleGrid cols={{ base: 1, sm: run.reference ? 2 : 1 }}>
              {run.reference && <Stack gap={4}><Text size="sm">原图</Text><ImagePreview src={imageUrl(profile, run.reference)} alt="原图" height={280} /></Stack>}
              <Stack gap={4}><Text size="sm">{candidate.applied_path ? '候选（已保存到媒体）' : '候选 · 尚未应用'}</Text><ImagePreview src={imageUrl(profile, candidate.candidate_path)} before={run.reference ? imageUrl(profile, run.reference) : undefined} alt="候选图片" height={280} /></Stack>
            </SimpleGrid>
            <Text size="xs" c="dimmed">点击图片可放大、查看 100% 原尺寸；对比图可切换原图与修改后。</Text>
            <Group gap="xs">
              <Button mih={44} disabled={busy} onClick={() => void accept(run, candidate)}>{run.request.target.kind === 'block' ? '替换这张图' : run.request.target.kind === 'cover' ? '用作封面' : '保存为新图片'}</Button>
              {run.request.target.kind !== 'media' && <Button mih={44} variant="default" disabled={busy} onClick={() => void accept(run, candidate, true)}>保存为新媒体</Button>}
              <Button mih={44} variant="default" disabled={busy || !enabled} onClick={() => { edit({ mode: 'edit', quality: run.request.quality === 'ultra' ? 'high' : run.request.quality, aspect: 'original', reference: candidate.candidate_path, target: candidateTarget(run, candidate) }); setNotice('基于所选候选继续修改；原图和已有候选会保留。'); }}>继续修改</Button>
              <Button mih={44} variant="subtle" disabled={busy} onClick={() => void discard(run, candidate.candidate_path)}>丢弃候选</Button>
            </Group>
          </Stack>)}
          {run.status !== 'running' && <Group>
            <Button mih={44} variant="subtle" disabled={!enabled} onClick={() => edit({ ...run.request, reference: run.reference || run.request.reference })}>重新生成（同一参考图与要求）</Button>
            {run.status === 'failed' && <Button mih={44} variant="subtle" disabled={busy} onClick={() => void discard(run)}>移除失败记录</Button>}
          </Group>}
        </Stack>
      </Paper>)}
    </Stack>
  </Modal>;
}
