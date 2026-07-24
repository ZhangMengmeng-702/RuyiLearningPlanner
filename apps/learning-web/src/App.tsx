import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Layout from './components/layout/Layout';
import { useAuth } from './hooks/useAuth';

const LearnChatPage = lazy(() => import('./pages/LearnChatPage'));
const PlanViewPage = lazy(() => import('./pages/PlanViewPage'));
const TodayPage = lazy(() => import('./pages/TodayPage'));
const LoginPage = lazy(() => import('./pages/LoginPage'));
const KbDocPage = lazy(() => import('./pages/KbDocPage'));

const PageLoader = () => (
  <div className="flex items-center justify-center h-full">
    <div className="flex items-center gap-2 text-gray-400">
      <svg className="h-5 w-5 animate-spin text-indigo-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-90" fill="currentColor" d="M4 12a8 8 0 0 1 8-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      加载中...
    </div>
  </div>
);

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { loading, isLoggedIn, authEnabled } = useAuth();
  const location = useLocation();

  if (loading) {
    return <PageLoader />;
  }

  if (authEnabled && !isLoggedIn) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <Layout>
                  <Suspense fallback={<PageLoader />}>
                    <Routes>
                      <Route path="/learn" element={<LearnChatPage />} />
                      <Route path="/learn/plan" element={<PlanViewPage />} />
                      <Route path="/learn/plan/:planId" element={<PlanViewPage />} />
                      <Route path="/learn/today" element={<TodayPage />} />
                      <Route path="/learn/kb/:docId" element={<KbDocPage />} />
                      <Route path="*" element={<Navigate to="/learn" replace />} />
                    </Routes>
                  </Suspense>
                </Layout>
              </ProtectedRoute>
            }
          />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}