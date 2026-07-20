import React from 'react';
import { NavLink } from 'react-router-dom';

const NAV_ITEMS = [
  { path: '/learn', label: '💬 对话规划', icon: '💬' },
  { path: '/learn/plan', label: '📋 计划看板', icon: '📋' },
  { path: '/learn/today', label: '✅ 今日任务', icon: '✅' },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="h-screen flex bg-gray-950 text-gray-100">
      {/* 左侧导航 */}
      <nav className="w-60 bg-gray-900 border-r border-gray-800 flex flex-col">
        <div className="p-5 border-b border-gray-800">
          <div className="text-xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
            🎯 学习规划助手
          </div>
          <div className="text-xs text-gray-500 mt-1">Hermes Agent</div>
        </div>
        <div className="flex-1 p-3 space-y-1">
          {NAV_ITEMS.map(item => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/learn'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-xl text-sm transition-colors ${
                  isActive
                    ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
                }`
              }
            >
              <span className="text-lg">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </div>
        <div className="p-4 border-t border-gray-800 text-xs text-gray-600">
          Ruyi Learning Planner v0.1
        </div>
      </nav>

      {/* 主内容区 */}
      <main className="flex-1 overflow-hidden">
        {children}
      </main>
    </div>
  );
}