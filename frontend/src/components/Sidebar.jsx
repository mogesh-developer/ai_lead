import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  HiChartBar, 
  HiUsers, 
  HiSearch, 
  HiTemplate, 
  HiMail, 
  HiUpload, 
  HiGlobeAlt, 
  HiCog,
  HiBriefcase,
  HiViewGrid,
  HiStar,
  HiTag,
  HiCloudUpload,
  HiBeaker,
  HiShieldCheck,
  HiBell
} from 'react-icons/hi';

const Sidebar = () => {
  const location = useLocation();

  const menuItems = [
    { name: 'Dashboard', path: '/dashboard', icon: HiViewGrid },
    { name: 'Leads List', path: '/dashboard', icon: HiUsers },
    { name: 'Outreach', path: '/campaigns', icon: HiMail },
    { name: 'Templates', path: '/templates', icon: HiTemplate },
    { name: 'Analytics', path: '/analytics', icon: HiChartBar },
    { name: 'Enhanced Analytics', path: '/enhanced-analytics', icon: HiChartBar },
  ];

  const advancedItems = [
    { name: 'Lead Scoring', path: '/lead-scoring', icon: HiStar },
    { name: 'Lead Enrichment', path: '/lead-enrichment', icon: HiUsers },
    { name: 'Lead Tagging', path: '/lead-tagging', icon: HiTag },
    { name: 'Lead Validation', path: '/lead-validation', icon: HiShieldCheck },
    { name: 'CRM Integration', path: '/crm-integration', icon: HiCloudUpload },
    { name: 'A/B Testing', path: '/ab-testing', icon: HiBeaker },
    { name: 'Reminders', path: '/reminders', icon: HiBell },
  ];

  const discoveryItems = [
    { name: 'Web Search', path: '/web-search', icon: HiSearch },
    { name: 'Bulk Scrape', path: '/bulk-scrape', icon: HiGlobeAlt },
    { name: 'Upload Leads', path: '/upload', icon: HiUpload },
    { name: 'Justdial Scraper', path: '/justdial', icon: HiSearch },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <div className="w-64 bg-gray-900 text-white h-screen flex flex-col fixed left-0 top-0 overflow-hidden shadow-xl border-r border-gray-800">
      <div className="p-6 flex-shrink-0 border-b border-gray-800/50">
        <Link to="/" className="flex items-center gap-2 text-xl font-bold text-blue-400 hover:text-blue-300 transition-colors">
          <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center text-white shadow-lg">
            AI
          </div>
          <span>LeadReach</span>
        </Link>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-8 scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800 hover:scrollbar-thumb-gray-500 scroll-smooth">
        <div>
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4 px-2">Main Menu</p>
          <div className="space-y-1">
            {menuItems.map((item) => (
              <Link
                key={item.name}
                to={item.path}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${
                  isActive(item.path) 
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/20 border border-blue-500/30' 
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white hover:border-gray-700 border border-transparent'
                }`}
              >
                <item.icon className="w-5 h-5 flex-shrink-0" />
                <span className="font-medium text-sm truncate">{item.name}</span>
              </Link>
            ))}
          </div>
        </div>

        <div>
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4 px-2">Advanced Features</p>
          <div className="space-y-1">
            {advancedItems.map((item) => (
              <Link
                key={item.name}
                to={item.path}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${
                  isActive(item.path) 
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/20 border border-blue-500/30' 
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white hover:border-gray-700 border border-transparent'
                }`}
              >
                <item.icon className="w-5 h-5 flex-shrink-0" />
                <span className="font-medium text-sm truncate">{item.name}</span>
              </Link>
            ))}
          </div>
        </div>

        <div>
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4 px-2">Lead Discovery</p>
          <div className="space-y-1">
            {discoveryItems.map((item) => (
              <Link
                key={item.name}
                to={item.path}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${
                  isActive(item.path) 
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/20 border border-blue-500/30' 
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white hover:border-gray-700 border border-transparent'
                }`}
              >
                <item.icon className="w-5 h-5 flex-shrink-0" />
                <span className="font-medium text-sm truncate">{item.name}</span>
              </Link>
            ))}
          </div>
        </div>
      </div>

      <div className="p-4 border-t border-gray-800/50 flex-shrink-0">
        <Link 
          to="/guide" 
          className="flex items-center gap-3 px-3 py-2.5 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-all duration-200 border border-transparent hover:border-gray-700"
        >
          <HiCog className="w-5 h-5 flex-shrink-0" />
          <span className="text-sm">User Guide</span>
        </Link>
      </div>
    </div>
  );
};

export default Sidebar;