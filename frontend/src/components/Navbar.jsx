import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(true);
  const location = useLocation();

  const isActive = (path) => {
    return location.pathname === path;
  };

  const navLinks = [
    { path: '/dashboard', label: 'Dashboard', icon: '📊' },
    { path: '/analytics', label: 'Analytics', icon: '📈' },
    { path: '/outreach', label: 'Outreach', icon: '📧' },
    { path: '/search', label: 'Find Leads', icon: '🔍' },
    { path: '/upload', label: 'Upload', icon: '📤' },
    { path: '/web-search', label: 'Web Search', icon: '🌐' },
    { path: '/domain-search', label: 'Domain Search', icon: '🏢' },
    { path: '/guide', label: 'Guide', icon: '📖' }
  ];

  return (
    <>
      {/* Mobile Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed top-4 left-4 z-50 md:hidden text-slate-300 hover:text-white transition-colors"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      {/* Sidebar */}
      <aside className={`fixed left-0 top-0 h-screen w-64 bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 border-r border-slate-700 z-40 transition-transform duration-300 ${
        isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
      }`}>
        {/* Logo Section */}
        <div className="p-6 border-b border-slate-700">
          <Link to="/" className="flex items-center space-x-2 group">
            <div className="text-2xl">⚡</div>
            <div className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent group-hover:from-blue-300 group-hover:to-purple-300 transition-colors">
              LeadAgent
            </div>
          </Link>
        </div>

        {/* Navigation Links */}
        <nav className="p-4 space-y-2">
          {navLinks.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                isActive(link.path)
                  ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-blue-400 border-l-2 border-blue-400'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
              }`}
              onClick={() => window.innerWidth < 768 && setIsOpen(false)}
            >
              <span className="text-xl">{link.icon}</span>
              <span className="font-medium">{link.label}</span>
            </Link>
          ))}
        </nav>

        {/* Footer Section */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-700">
          <div className="text-xs text-slate-400 text-center">
            <p>Lead Outreach</p>
            <p>v1.0.0</p>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Navbar;
