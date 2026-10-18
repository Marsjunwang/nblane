import { useQuery } from '@tanstack/react-query';
import { apiGet, apiPost } from '../../api/client';
import { contentCoverCandidateUrl, contentMediaUrl } from '../../api/hooks';
import type { ImageRun } from './imageTypes';

export const imageApiPath = (profile: string) => `/profiles/${encodeURIComponent(profile)}/content/images`;
export const imageQueryKey = (profile: string, slug: string) => ['profiles', profile, 'content', 'images', slug];
export function useImageRuns(profile: string, slug: string) {
  return useQuery({ queryKey: imageQueryKey(profile, slug), queryFn: () => apiGet<{ runs: ImageRun[] }>(`${imageApiPath(profile)}?${new URLSearchParams({ slug })}`), refetchInterval: 3000 });
}
export function imageUrl(profile: string, path: string) {
  return path.startsWith('blog/.candidates/') ? contentCoverCandidateUrl(profile, path) : contentMediaUrl(profile, path);
}
export async function uploadImageReference(profile: string, slug: string, file: File) {
  if (file.size > 12 * 1024 * 1024) throw new Error('参考图超过 12 MB，请先缩小。');
  const data_url = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(new Error('读取图片失败，请重试。'));
    reader.readAsDataURL(file);
  });
  return apiPost<{ path: string }>(`${imageApiPath(profile)}/reference`, { slug, data_url });
}
