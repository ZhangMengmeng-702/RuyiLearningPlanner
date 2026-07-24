import React, { useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { useNavigate } from 'react-router-dom';

interface HeaderProps {
  title?: string;
}

export const Header: React.FC<HeaderProps> = ({ title = '如意学习规划助手' }) => {
  const { username, isLoggedIn, logout } = useAuth();
  const [showMenu, setShowMenu] = useState(false);
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (e) {
      console.error('登出失败:', e);
    }
  };

  return (
    <header className="h-14 border-b border-gray-700/50 bg-gray-900/80 backdrop-blur flex items-center px-6 flex-shrink-0">
      <h1 className="text-white font-bold text-lg">{title}</h1>
      <div className="ml-auto flex items-center gap-4">
        {isLoggedIn && username && (
          <div className="relative">
            <button
              onClick={() => setShowMenu(!showMenu)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-gray-800 transition-colors"
            >
              <div className="w-7 h-7 rounded-full bg-indigo-600 flex items-center justify-center text-white text-sm font-medium">
                {username.charAt(0).toUpperCase()}
              </div>
              <span className="text-gray-300 text-sm">{username}</span>
              <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            {showMenu && (
              <div className="absolute right-0 top-full mt-1 w-40 bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-50">
                <button
                  onClick={handleLogout}
                  className="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-white rounded-t-lg transition-colors"
                >
                  退出登录
                </button>
              </div>
            )}
          </div>
        )}
        <span className="text-gray-500 text-sm">v1.0</span>
      </div>
    </header>
  );
};