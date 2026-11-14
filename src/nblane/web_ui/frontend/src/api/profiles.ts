import { useMutation, useQueryClient } from '@tanstack/react-query';

import { apiPost } from './client';
import type { components } from './schema';

export type ProfileCreateRequest = components['schemas']['ProfileCreateRequest'];
type ProfileCreateResponse = components['schemas']['ProfileCreateResponse'];

export function useCreateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: ProfileCreateRequest) => apiPost<ProfileCreateResponse>('/profiles', body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['profiles'] }),
  });
}
