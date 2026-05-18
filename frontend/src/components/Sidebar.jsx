import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

// Clean, minimalist icons matching the theme
const SidebarIcons = {
  Chat: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
    </svg>
  ),
  Dashboard: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  ),
  Logout: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
    </svg>
  )
};

export default function Sidebar() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { name: 'AI Copilot', path: '/', icon: <SidebarIcons.Chat /> },
    { name: 'BI Dashboard', path: '/dashboard', icon: <SidebarIcons.Dashboard /> },
  ];

  return (
    <aside className="w-64 bg-qarshi-dark text-white flex flex-col h-screen fixed left-0 top-0 border-r border-qarshi-green/20 z-10">
      {/* Brand Header */}
      <div className="p-6 border-b border-white/5 flex flex-col items-start gap-2">
        <div className="flex items-center gap-3">
          {/* Elegant Botanical Logo Placeholder */}
          <div className="w-8 h-8 rounded-full bg-qarshi-gold flex items-center justify-center text-qarshi-green font-bold text-lg shadow-inner">
            Q
          </div>
          <div>
            <h1 className="font-bold text-base tracking-wide text-white">Qarshi Industries</h1>
            <p className="text-[10px] text-qarshi-gold uppercase font-semibold tracking-wider">BI Copilot System</p>
          </div>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 p-4 space-y-1.5 mt-4">
        {menuItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <button
              key={item.name}
              onClick={() => navigate(item.path)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 group ${
                isActive
                  ? 'bg-gradient-to-r from-qarshi-green to-qarshi-green/80 text-white shadow-md border-l-4 border-qarshi-gold'
                  : 'text-gray-400 hover:bg-white/5 hover:text-white'
              }`}
            >
              <span className={`transition-colors duration-200 ${isActive ? 'text-qarshi-gold' : 'text-gray-400 group-hover:text-white'}`}>
                {item.icon}
              </span>
              {item.name}
            </button>
          );
        })}
      </nav>

      {/* User Bottom Section */}
      <div className="p-4 border-t border-white/5">
        <button
          onClick={() => { logout(); navigate("/login"); }}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-gray-400 hover:bg-red-950/30 hover:text-red-400 transition-all duration-200"
        >
          <SidebarIcons.Logout />
          Logout
        </button>
      </div>
    </aside>
  );
}