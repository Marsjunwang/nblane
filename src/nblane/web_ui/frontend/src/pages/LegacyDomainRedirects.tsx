import { Navigate, useParams, useSearchParams } from 'react-router-dom';

/** Lightweight redirects must not eagerly import their destination pages. */
export function ProjectsRedirect() {
  const { name = '' } = useParams();
  const [params] = useSearchParams();
  const search = params.toString();
  return <Navigate to={`/p/${encodeURIComponent(name)}/projects${search ? `?${search}` : ''}`} replace />;
}

export function EvidenceStageRedirect({ stage }: { stage: 'review' | 'strengthen' }) {
  const { name = '' } = useParams();
  return <Navigate to={`/p/${encodeURIComponent(name)}/evidence?stage=${stage}`} replace />;
}
