import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout';
import LearnChatPage from './pages/LearnChatPage';
import PlanViewPage from './pages/PlanViewPage';
import TodayPage from './pages/TodayPage';

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/learn" element={<LearnChatPage />} />
          <Route path="/learn/plan" element={<PlanViewPage />} />
          <Route path="/learn/plan/:planId" element={<PlanViewPage />} />
          <Route path="/learn/today" element={<TodayPage />} />
          <Route path="*" element={<Navigate to="/learn" replace />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}