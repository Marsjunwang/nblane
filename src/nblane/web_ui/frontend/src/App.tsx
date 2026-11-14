import { BrowserRouter, Navigate, Route, Routes, useParams, useSearchParams } from 'react-router-dom';

import { RequireAuth } from './auth/RequireAuth';
import { AppLayout } from './components/AppLayout';
import { PageBoundary, retryableLazy } from './components/PageBoundary';
import { EvidenceStageRedirect, ProjectsRedirect } from './pages/LegacyDomainRedirects';
import { HomePage } from './pages/HomePage';
import { LoginPage } from './pages/LoginPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { LegacyStreamlitRedirect } from './pages/LegacyStreamlitRedirect';
import { ProfilesPage } from './pages/ProfilesPage';

// The blog editor pulls in BlockNote/KaTeX/Mermaid; keep it out of the
// main bundle so other pages do not pay for it.
const ContentWorkspacePage = retryableLazy(() =>
  import('./pages/ContentWorkspacePage').then((m) => ({ default: m.ContentWorkspacePage })),
);
const CareerWorkspacePage = retryableLazy(() => import('./pages/CareerWorkspacePage').then((m) => ({ default: m.CareerWorkspacePage })));
const AssistantPage = retryableLazy(() => import('./pages/AssistantPage').then((m) => ({ default: m.AssistantPage })));
const EvidencePage = retryableLazy(() => import('./pages/EvidencePage').then((m) => ({ default: m.EvidencePage })));
const MiniPage = retryableLazy(() => import('./pages/MiniPage').then((m) => ({ default: m.MiniPage })));
const ProjectsPage = retryableLazy(() => import('./pages/ProjectsPage').then((m) => ({ default: m.ProjectsPage })));
const PublicBuildPage = retryableLazy(() => import('./pages/PublicBuildPage').then((m) => ({ default: m.PublicBuildPage })));
const ResearchPage = retryableLazy(() => import('./pages/ResearchPage').then((m) => ({ default: m.ResearchPage })));
const ResearchSourcesPage = retryableLazy(() => import('./pages/ResearchSourcesPage').then((m) => ({ default: m.ResearchSourcesPage })));
const PaperReaderPage = retryableLazy(() => import('./pages/PaperReaderPage').then((m) => ({ default: m.PaperReaderPage })));
const PaperOverviewPage = retryableLazy(() => import('./pages/PaperOverviewPage').then((m) => ({ default: m.PaperOverviewPage })));
const PaperLibraryPage = retryableLazy(() => import('./pages/PaperLibraryPage').then((m) => ({ default: m.PaperLibraryPage })));
const SettingsPage = retryableLazy(() => import('./pages/SettingsPage').then((m) => ({ default: m.SettingsPage })));
const SkillTreePage = retryableLazy(() => import('./pages/SkillTreePage').then((m) => ({ default: m.SkillTreePage })));
const WorkshopPage = retryableLazy(() => import('./pages/WorkshopPage').then((m) => ({ default: m.WorkshopPage })));


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
        {/* Compact always-on-top view (小窗): auth but no app shell. */}
        <Route
          path="/p/:name/mini"
          element={
            <RequireAuth>
              <PageBoundary><MiniPage /></PageBoundary>
            </RequireAuth>
          }
        />
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
          <Route path="/settings/:section" element={<SettingsPage />} />
          <Route path="/workshop" element={<WorkshopPage />} />
          <Route path="/p/:name/home" element={<HomePage />} />
          {/* Legacy route: the health page dissolved — 证据风险 lives under
              证据「待补强」; GET /health API stays for openclaw/CLI. */}
          <Route path="/p/:name/health" element={<EvidenceStageRedirect stage="strengthen" />} />
          {/* Legacy route: the kanban board merged into the Projects page. */}
          <Route path="/p/:name/kanban" element={<ProjectsRedirect />} />
          <Route path="/p/:name/skill-tree" element={<SkillTreePage />} />
          {/* Legacy route: the goals page is absorbed by the home starmap
              星表 catalog (design: home-editing-starmap-design.md §6). */}
          <Route path="/p/:name/goals" element={<GoalsRedirect />} />
          <Route path="/p/:name/evidence" element={<EvidencePage />} />
          {/* Legacy route: the review queue merged into the Evidence page. */}
          <Route path="/p/:name/evidence-review" element={<EvidenceStageRedirect stage="review" />} />
          {/* Legacy route: the project board merged into the Projects page. */}
          <Route path="/p/:name/project-board" element={<ProjectsRedirect />} />
          <Route path="/p/:name/projects" element={<ProjectsPage />} />
          <Route path="/p/:name/content/*" element={<ContentWorkspacePage />} />
          <Route path="/p/:name/career/*" element={<CareerWorkspacePage />} />
          <Route path="/p/:name/public-build" element={<PublicBuildPage />} />
          <Route path="/p/:name/research" element={<ResearchPage />} />
          <Route path="/p/:name/research/library" element={<PaperLibraryPage />} />
          {/* The overview is the paper landing page; ?mode= deep links on it redirect to /read. */}
          <Route path="/p/:name/research/papers/:sourceId" element={<PaperOverviewPage />} />
          <Route path="/p/:name/research/papers/:sourceId/read" element={<PaperReaderPage />} />
          <Route path="/p/:name/research/sources" element={<ResearchSourcesPage />} />
          {/* Retired Streamlit URLs (/Skill_Tree, /pages/1_Skill_Tree.py) keep
              working now that the main domain serves the SPA. */}
          <Route path="/pages/:legacyFile" element={<LegacyStreamlitRedirect />} />
          <Route path="/:legacyPage" element={<LegacyStreamlitRedirect />} />
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}
