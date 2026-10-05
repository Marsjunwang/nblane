import { useParams } from 'react-router-dom';

import { CareerHome } from '../components/career/CareerHome';
import { ResumeEditor } from '../components/career/ResumeEditor';
import { TargetWorkspace } from '../components/career/TargetWorkspace';

/**
 * Career workspace: `/p/:name/career` is the home (master resume card +
 * target jobs), `/career/resume` the structured resume editor and
 * `/career/jobs/<id>` one target job (JD match + tailored draft).
 */
export function CareerWorkspacePage() {
  const { name = '', '*': rest = '' } = useParams();
  const parts = rest.split('/').filter(Boolean);
  if (parts[0] === 'resume') return <ResumeEditor profile={name} />;
  if (parts[0] === 'jobs' && parts[1]) {
    const draftId = decodeURIComponent(parts[1]);
    return <TargetWorkspace key={draftId} profile={name} draftId={draftId} />;
  }
  return <CareerHome profile={name} />;
}
