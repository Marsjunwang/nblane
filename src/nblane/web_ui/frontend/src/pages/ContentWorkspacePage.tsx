import { Center, Loader } from '@mantine/core';
import { lazy, Suspense } from 'react';
import { Navigate, useLocation, useParams, useSearchParams } from 'react-router-dom';

import { ContentLibrary } from '../components/content/ContentLibrary';
import { contentEditorPath } from '../components/content/contentDraft';

// The editor pulls in BlockNote/KaTeX/Mermaid; keep it out of the library
// chunk so the post list loads without them.
const ContentEditor = lazy(() =>
  import('../components/content/ContentEditor').then((m) => ({ default: m.ContentEditor })),
);

/**
 * Content workspace: `/p/:name/content` is the post library and
 * `/p/:name/content/<slug>` the full-screen editor for one post. The editor
 * is keyed by slug so switching posts always starts from a clean mount.
 */
export function ContentWorkspacePage() {
  const { name = '', '*': rest = '' } = useParams();
  const [searchParams] = useSearchParams();
  const location = useLocation();
  // Pre-redesign deep links used ?post=<slug>.
  const legacy = searchParams.get('post');
  if (legacy && !rest) {
    return <Navigate to={contentEditorPath(name, legacy)} replace state={location.state} />;
  }
  const slug = rest
    .split('/')
    .filter(Boolean)
    .map((part) => decodeURIComponent(part))
    .join('/');
  if (!slug) return <ContentLibrary profile={name} />;
  return (
    <Suspense fallback={<Center py="xl"><Loader /></Center>}>
      <ContentEditor key={slug} profile={name} slug={slug} />
    </Suspense>
  );
}
