// Redirects retired Streamlit page URLs to their SPA routes.
//
// Streamlit served pages at `/<Page_Name>` (from `pages/<n>_<Page_Name>.py`)
// and some sidecar links still point at `/pages/<n>_<Page_Name>.py`. The main
// domain now serves the SPA, so these bookmarks and links must keep working.

import { Center, Loader } from '@mantine/core';
import { Navigate, useParams, useSearchParams } from 'react-router-dom';

import { useProfiles } from '../api/hooks';
import { NotFoundPage } from './NotFoundPage';

/** Streamlit page slug → SPA path under `/p/:name/` (or an absolute path). */
const LEGACY_PAGES: Record<string, string> = {
  skill_tree: 'skill-tree',
  evidence_review: 'evidence',
  gap_analysis: 'home',
  kanban: 'projects',
  team_view: 'home',
  profile_health: 'evidence',
  output_studio: 'studio',
  research: 'research',
  agent_activity: 'activity',
  public_build: 'public-build',
  project_board: 'projects',
  settings: '/settings',
};

/** `Skill_Tree`, `1_Skill_Tree.py` or `pages/1_Skill_Tree.py` → `skill_tree`. */
export function legacyPageKey(raw: string): string {
  return raw
    .replace(/^.*\//, '')
    .replace(/\.py$/i, '')
    .replace(/^\d+_/, '')
    .toLowerCase();
}

export function LegacyStreamlitRedirect() {
  const { legacyPage = '', legacyFile = '' } = useParams();
  const [searchParams] = useSearchParams();
  const target = LEGACY_PAGES[legacyPageKey(legacyFile || legacyPage)];
  const profiles = useProfiles();

  if (!target) return <NotFoundPage />;
  if (target.startsWith('/')) return <Navigate to={target} replace />;

  const requested = searchParams.get('profile') ?? '';
  if (!requested && profiles.isPending) {
    return (
      <Center py="xl">
        <Loader />
      </Center>
    );
  }
  const names = (profiles.data ?? []).map((p) => p.name);
  const profile = requested || (names.length === 1 ? names[0] : '');
  if (!profile) return <Navigate to="/" replace />;
  return <Navigate to={`/p/${encodeURIComponent(profile)}/${target}`} replace />;
}
