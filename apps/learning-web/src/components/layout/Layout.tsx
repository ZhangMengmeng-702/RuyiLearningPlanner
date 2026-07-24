import React, { useEffect } from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { useAuth } from '../../hooks/useAuth';
import { useAppStore } from '../../store/appStore';

export default function Layout({ children }: { children: React.ReactNode }) {
  const { userId } = useAuth();
  const { resetForUser, userId: storeUserId } = useAppStore();

  useEffect(() => {
    if (userId && userId !== storeUserId) {
      resetForUser(userId);
    }
  }, [userId, storeUserId, resetForUser]);

  return (
    <div className="h-screen flex flex-col bg-gray-950 text-gray-100">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-hidden">
          {children}
        </main>
      </div>
    </div>
  );
}