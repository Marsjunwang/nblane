import { BrowserRouter, Route, Routes } from 'react-router-dom';

import { RequireAuth } from './auth/RequireAuth';
import { AppLayout } from './components/AppLayout';
import { ActivityPage } from './pages/ActivityPage';
import { AssistantPage } from './pages/AssistantPage';
import { EvidencePage, EvidenceReviewRedirect } from './pages/EvidencePage';
import { GapPage } from './pages/GapPage';
import { GoalsPage } from './pages/GoalsPage';
import { HealthPage } from './pages/HealthPage';
import { HomePage } from './pages/HomePage';
import { InboxPage } from './pages/InboxPage';
import { KanbanPage } from './pages/KanbanPage';
import { LoginPage } from './pages/LoginPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { ProfilesPage } from './pages/ProfilesPage';
import { ProjectBoardPage } from './pages/ProjectBoardPage';
import { PublicBuildPage } from './pages/PublicBuildPage';
import { ResearchPage } from './pages/ResearchPage';
import { ReviewPage } from './pages/ReviewPage';
import { SkillTreePage } from './pages/SkillTreePage';
import { StudioPage } from './pages/StudioPage';

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
          <Route path="/p/:name/home" element={<HomePage />} />
          <Route path="/p/:name/health" element={<HealthPage />} />
          <Route path="/p/:name/activity" element={<ActivityPage />} />
          <Route path="/p/:name/inbox" element={<InboxPage />} />
          <Route path="/p/:name/kanban" element={<KanbanPage />} />
          <Route path="/p/:name/skill-tree" element={<SkillTreePage />} />
          <Route path="/p/:name/goals" element={<GoalsPage />} />
          <Route path="/p/:name/evidence" element={<EvidencePage />} />
          {/* Legacy route: the review queue merged into the Evidence page. */}
          <Route path="/p/:name/evidence-review" element={<EvidenceReviewRedirect />} />
          <Route path="/p/:name/gap" element={<GapPage />} />
          <Route path="/p/:name/review" element={<ReviewPage />} />
          <Route path="/p/:name/project-board" element={<ProjectBoardPage />} />
          <Route path="/p/:name/studio" element={<StudioPage />} />
          <Route path="/p/:name/public-build" element={<PublicBuildPage />} />
          <Route path="/p/:name/research" element={<ResearchPage />} />
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}
