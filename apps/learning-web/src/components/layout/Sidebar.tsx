import React from 'react';
import { NavLink } from 'react-router-dom';

const NAV_ITEMS = [
  { path: '/learn', label: '对话规划', emoji: '💬' },
  { path: '/learn/plan', label: '计划看板', emoji: '📋' },
  { path: '/learn/today', label: '今日任务', emoji: '📝' },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-56 border-r border-gray-700/50 bg-gray-900/80 flex flex-col flex-shrink-0">
      <div className="h-14 flex items-center px-5 border-b border-gray-700/50">
        <span className="text-indigo-400 font-bold text-lg">Ruyi</span>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        {NAV_ITEMS.map(item => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/learn'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
              }`
            }
          >
            <span>{item.emoji}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
};