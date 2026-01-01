import React, { useEffect, useState } from 'react';
import api from '../api';
import StatCard from '../components/StatCard';

const Dashboard = () => {
  const [stats, setStats] = useState({ 
    total: 0, 
    analyzed: 0, 
    outreach_sent: 0, 
    converted: 0
  });
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [autopilot, setAutopilot] = useState(false);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsRes, leadsRes, settingsRes] = await Promise.all([
        api.get('/dashboard-stats').catch(() => ({ data: { total: 0, analyzed: 0, outreach_sent: 0, converted: 0 } })),
        api.get('/leads').catch(() => ({ data: { leads: [] } })),
        api.get('/settings').catch(() => ({ data: { autopilot: false } }))
      ]);

      console.log("Dashboard Stats Response:", statsRes.data);
      console.log("Leads Response:", leadsRes.data);
      
      setStats(statsRes.data || { total: 0, analyzed: 0, outreach_sent: 0, converted: 0 });
      // Handle both array and object response formats
      const leadsData = leadsRes.data?.leads || leadsRes.data || [];
      console.log("Processed leads data:", leadsData);
      setLeads(Array.isArray(leadsData) ? leadsData.slice(0, 10) : []);
      setAutopilot(settingsRes.data?.autopilot || false);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching dashboard data", error);
      setLoading(false);
    }
  };

  const toggleAutopilot = async () => {
    try {
      const newState = !autopilot;
      await api.post('/settings', { autopilot: newState });
      setAutopilot(newState);
    } catch (error) {
      console.error("Failed to toggle autopilot", error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-white text-lg">Loading Dashboard...</p>
        </div>
      </div>
    );
  }

  const conversionRate = stats.total > 0 ? Math.round((stats.converted / stats.total) * 100) : 0;
  const successRate = stats.analyzed > 0 ? Math.round((stats.outreach_sent / stats.analyzed) * 100) : 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="bg-slate-800/50 backdrop-blur-md border-b border-slate-700 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-6 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-white">Dashboard</h1>
            <p className="text-slate-400 text-sm mt-1">Real-time lead management & analytics</p>
          </div>
          <div className="flex items-center space-x-6">
            <div className="flex items-center bg-slate-700/50 px-4 py-2 rounded-lg border border-slate-600">
              <span className="text-slate-300 text-sm font-medium mr-3">Autopilot:</span>
              <button
                onClick={toggleAutopilot}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-all duration-300 focus:outline-none ${
                  autopilot 
                    ? 'bg-gradient-to-r from-green-500 to-emerald-600' 
                    : 'bg-slate-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-300 shadow-lg ${
                    autopilot ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
              <span className={`ml-3 text-sm font-semibold ${autopilot ? 'text-emerald-400' : 'text-slate-400'}`}>
                {autopilot ? 'ACTIVE' : 'INACTIVE'}
              </span>
            </div>
            <button
              onClick={fetchDashboardData}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors duration-200 text-sm font-medium"
            >
              ↻ Refresh
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard 
            title="Total Leads" 
            value={stats.total || 0} 
            icon="📊"
            trend="+12%"
            color="blue"
          />
          <StatCard 
            title="Analyzed" 
            value={stats.analyzed || 0}
            icon="✓"
            trend={`${successRate}%`}
            color="purple"
          />
          <StatCard 
            title="Outreach Sent" 
            value={stats.outreach_sent || 0}
            icon="📧"
            trend="+8%"
            color="yellow"
          />
          <StatCard 
            title="Converted" 
            value={stats.converted || 0}
            icon="🎯"
            trend={`${conversionRate}%`}
            color="green"
          />
        </div>

        {/* Key Metrics Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-gradient-to-br from-slate-800 to-slate-700 rounded-lg p-6 border border-slate-600">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-white font-semibold">Conversion Rate</h3>
              <span className="text-3xl font-bold text-emerald-400">{conversionRate}%</span>
            </div>
            <div className="w-full bg-slate-600 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-emerald-500 to-emerald-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${conversionRate}%` }}
              ></div>
            </div>
            <p className="text-slate-400 text-xs mt-2">{stats.converted || 0} of {stats.total || 0} leads converted</p>
          </div>

          <div className="bg-gradient-to-br from-slate-800 to-slate-700 rounded-lg p-6 border border-slate-600">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-white font-semibold">Success Rate</h3>
              <span className="text-3xl font-bold text-blue-400">{successRate}%</span>
            </div>
            <div className="w-full bg-slate-600 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-blue-500 to-blue-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${successRate}%` }}
              ></div>
            </div>
            <p className="text-slate-400 text-xs mt-2">{stats.outreach_sent || 0} of {stats.analyzed || 0} leads reached</p>
          </div>
        </div>

        {/* Recent Leads Table */}
        <div className="bg-gradient-to-br from-slate-800 to-slate-700 rounded-lg border border-slate-600 overflow-hidden shadow-xl">
          <div className="px-6 py-4 border-b border-slate-600 bg-slate-800/50">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-bold text-white">Recent Leads</h2>
              <span className="text-slate-400 text-sm">{leads.length} leads</span>
            </div>
          </div>
          <div className="overflow-x-auto">
            {leads.length > 0 ? (
              <table className="w-full">
                <thead>
                  <tr className="bg-slate-700/50 border-b border-slate-600">
                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">Name</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">Email</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">Company</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-600">
                  {leads.map((lead, idx) => (
                    <tr key={idx} className="hover:bg-slate-700/30 transition-colors">
                      <td className="px-6 py-4 text-sm text-white font-medium">{lead.name || 'N/A'}</td>
                      <td className="px-6 py-4 text-sm text-slate-300">{lead.email || 'N/A'}</td>
                      <td className="px-6 py-4 text-sm text-slate-300">{lead.company || 'N/A'}</td>
                      <td className="px-6 py-4 text-sm">
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                          lead.status === 'converted' ? 'bg-emerald-500/20 text-emerald-400' :
                          lead.status === 'contacted' ? 'bg-blue-500/20 text-blue-400' :
                          'bg-slate-600 text-slate-300'
                        }`}>
                          {lead.status || 'pending'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm">
                        <a href={`/lead/${lead.id}`} className="text-blue-400 hover:text-blue-300 font-medium transition-colors">View →</a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="px-6 py-12 text-center">
                <p className="text-slate-400">No leads yet. Start by uploading or searching for leads.</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
