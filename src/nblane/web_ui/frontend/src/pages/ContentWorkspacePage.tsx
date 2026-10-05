import { Navigate, useLocation, useParams, useSearchParams } from 'react-router-dom';

import { ContentEditor } from '../components/content/ContentEditor';
import { ContentLibrary } from '../components/content/ContentLibrary';
import { contentEditorPath } from '../components/content/contentDraft';

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
  return <ContentEditor key={slug} profile={name} slug={slug} />;
}
