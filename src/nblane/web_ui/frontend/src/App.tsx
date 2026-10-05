import { Center, Loader } from '@mantine/core';
import { lazy, Suspense } from 'react';
import { BrowserRouter, Navigate, Route, Routes, useParams, useSearchParams } from 'react-router-dom';

import { RequireAuth } from './auth/RequireAuth';
import { AppLayout } from './components/AppLayout';
import { ActivityPage } from './pages/ActivityPage';
import { CareerWorkspacePage } from './pages/CareerWorkspacePage';
import { AssistantPage } from './pages/AssistantPage';
import { EvidencePage, EvidenceReviewRedirect, HealthRedirect } from './pages/EvidencePage';
import { HomePage } from './pages/HomePage';
import { InboxPage } from './pages/InboxPage';
import { LoginPage } from './pages/LoginPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { ProfilesPage } from './pages/ProfilesPage';
import { KanbanRedirect, ProjectBoardRedirect, ProjectsPage } from './pages/ProjectsPage';
import { PublicBuildPage } from './pages/PublicBuildPage';
import { ResearchPage } from './pages/ResearchPage';
import { PaperReaderPage } from './pages/PaperReaderPage';
import { SettingsPage } from './pages/SettingsPage';
import { SkillTreePage } from './pages/SkillTreePage';
import { StudioPage } from './pages/StudioPage';
import { WorkshopPage } from './pages/WorkshopPage';

// The blog editor pulls in BlockNote/KaTeX/Mermaid; keep it out of the
// main bundle so other pages do not pay for it.
const ContentWorkspacePage = lazy(() =>
  import('./pages/ContentWorkspacePage').then((m) => ({ default: m.ContentWorkspacePage })),
);


/** /goals → /home(目标管理由星图星表吸收,旧链接保留 query 串不破坏)。 */
function GoalsRedirect() {
  const { name = '' } = useParams();
  const [searchParams] = useSearchParams();
  const search = searchParams.toString();
  return (
    <Navigate to={`/p/${encodeURIComponent(name)}/home${search ? `?${search}` : ''}`} replace />
  );
}

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          element={
            <RequireAuth>
              <AppLayout />
            </RequireAuth>
          }
        >
          <Route path="/" element={<ProfilesPage />} />
          <Route path="/assistant" element={<AssistantPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/workshop" element={<WorkshopPage />} />
          <Route path="/p/:name/home" element={<HomePage />} />
          {/* Legacy route: the health page dissolved — 证据风险 lives under
              证据「待补强」; GET /health API stays for openclaw/CLI. */}
          <Route path="/p/:name/health" element={<HealthRedirect />} />
          <Route path="/p/:name/activity" element={<ActivityPage />} />
          <Route path="/p/:name/inbox" element={<InboxPage />} />
          {/* Legacy route: the kanban board merged into the Projects page. */}
          <Route path="/p/:name/kanban" element={<KanbanRedirect />} />
          <Route path="/p/:name/skill-tree" element={<SkillTreePage />} />
          {/* Legacy route: the goals page is absorbed by the home starmap
              星表 catalog (design: home-editing-starmap-design.md §6). */}
          <Route path="/p/:name/goals" element={<GoalsRedirect />} />
          <Route path="/p/:name/evidence" element={<EvidencePage />} />
          {/* Legacy route: the review queue merged into the Evidence page. */}
          <Route path="/p/:name/evidence-review" element={<EvidenceReviewRedirect />} />
          {/* Legacy route: the project board merged into the Projects page. */}
          <Route path="/p/:name/project-board" element={<ProjectBoardRedirect />} />
          <Route path="/p/:name/projects" element={<ProjectsPage />} />
          <Route path="/p/:name/studio" element={<StudioPage />} />
          <Route path="/p/:name/content/*" element={<Suspense fallback={<Center py="xl"><Loader /></Center>}><ContentWorkspacePage /></Suspense>} />
          <Route path="/p/:name/career/*" element={<CareerWorkspacePage />} />
          <Route path="/p/:name/public-build" element={<PublicBuildPage />} />
          <Route path="/p/:name/research" element={<ResearchPage />} />
          <Route path="/p/:name/research/papers/:sourceId" element={<PaperReaderPage />} />
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}
