import React, { useEffect, useState } from 'react';
import api from '../api';

const Analytics = () => {
  const [stats, setStats] = useState({ total: 0, analyzed: 0, outreach_sent: 0, converted: 0 });
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, leadsRes] = await Promise.all([
          api.get('/dashboard-stats'),
          api.get('/leads?per_page=10000')
        ]);
        setStats(statsRes.data);
        // Handle both response formats (object with leads property or direct array)
        const leadsData = leadsRes.data?.leads || leadsRes.data || [];
        setLeads(Array.isArray(leadsData) ? leadsData : []);
        console.log("Analytics - Stats:", statsRes.data);
        console.log("Analytics - Leads:", leadsData);
      } catch (error) {
        console.error("Error fetching analytics data", error);
        setStats({ total: 0, analyzed: 0, outreach_sent: 0, converted: 0 });
        setLeads([]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Calculate additional metrics
  const conversionRate = stats.total > 0 ? ((stats.converted / stats.total) * 100).toFixed(1) : 0;
  const outreachRate = stats.total > 0 ? ((stats.outreach_sent / stats.total) * 100).toFixed(1) : 0;
  const analysisRate = stats.total > 0 ? ((stats.analyzed / stats.total) * 100).toFixed(1) : 0;

  // Group leads by status
  const statusCounts = leads.reduce((acc, lead) => {
    acc[lead.status] = (acc[lead.status] || 0) + 1;
    return acc;
  }, {});

  // Group leads by location
  const locationCounts = leads.reduce((acc, lead) => {
    const location = lead.location || 'Unknown';
    acc[location] = (acc[location] || 0) + 1;
    return acc;
  }, {});

  // Group leads by company
  const companyCounts = leads.reduce((acc, lead) => {
    const company = lead.company || 'Unknown';
    acc[company] = (acc[company] || 0) + 1;
    return acc;
  }, {});

  if (loading) return (
    <div className="w-full h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin text-blue-400 text-4xl mb-4">⏳</div>
        <p className="text-white text-lg">Loading Analytics...</p>
      </div>
    </div>
  );

  return (
    <div className="w-full h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-800 to-slate-900 border-b border-slate-700 px-8 py-6 flex-shrink-0">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-2">
          📊 Analytics Dashboard
        </h1>
        <p className="text-slate-400 text-sm">Comprehensive lead insights and performance metrics</p>
      </div>

      {/* Main Content */}
      <div className="flex-grow overflow-y-auto px-8 py-8 scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-slate-700">

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-gradient-to-br from-slate-800/80 to-slate-700/50 border border-slate-700 rounded-xl shadow-xl p-6 hover:border-slate-600 transition-all">
            <h3 className="text-sm font-bold text-slate-300 mb-3 uppercase tracking-wider">🎯 Conversion Rate</h3>
            <p className="text-5xl font-bold bg-gradient-to-r from-emerald-400 to-green-400 bg-clip-text text-transparent">{conversionRate}%</p>
            <p className="text-xs text-slate-400 mt-2">{stats.converted} of {stats.total} leads</p>
          </div>
          <div className="bg-gradient-to-br from-slate-800/80 to-slate-700/50 border border-slate-700 rounded-xl shadow-xl p-6 hover:border-slate-600 transition-all">
            <h3 className="text-sm font-bold text-slate-300 mb-3 uppercase tracking-wider">📧 Outreach Rate</h3>
            <p className="text-5xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">{outreachRate}%</p>
            <p className="text-xs text-slate-400 mt-2">{stats.outreach_sent} of {stats.total} leads</p>
          </div>
          <div className="bg-gradient-to-br from-slate-800/80 to-slate-700/50 border border-slate-700 rounded-xl shadow-xl p-6 hover:border-slate-600 transition-all">
            <h3 className="text-sm font-bold text-slate-300 mb-3 uppercase tracking-wider">✓ Analysis Rate</h3>
            <p className="text-5xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">{analysisRate}%</p>
            <p className="text-xs text-slate-400 mt-2">{stats.analyzed} of {stats.total} leads</p>
          </div>
          <div className="bg-gradient-to-br from-slate-800/80 to-slate-700/50 border border-slate-700 rounded-xl shadow-xl p-6 hover:border-slate-600 transition-all">
            <h3 className="text-sm font-bold text-slate-300 mb-3 uppercase tracking-wider">📊 Total Leads</h3>
            <p className="text-5xl font-bold text-slate-200">{stats.total}</p>
            <p className="text-xs text-slate-400 mt-2">Across all sources</p>
          </div>
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Status Distribution */}
          <div className="bg-gradient-to-br from-slate-800/80 to-slate-700/50 border border-slate-700 rounded-xl shadow-xl p-6">
            <h3 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-6">📈 Lead Status Distribution</h3>
            <div className="space-y-5">
              {Object.entries(statusCounts).map(([status, count]) => (
                <div key={status} className="flex items-center justify-between">
                  <span className="capitalize text-slate-300 font-medium">{status.replace('_', ' ')}</span>
                  <div className="flex items-center space-x-3">
                    <div className="w-40 bg-slate-700 rounded-full h-3">
                      <div 
                        className="bg-gradient-to-r from-blue-500 to-purple-500 h-3 rounded-full transition-all duration-500 shadow-lg" 
                        style={{ width: `${stats.total > 0 ? (count / stats.total) * 100 : 0}%` }}
                      ></div>
                    </div>
                    <span className="text-sm font-bold text-slate-200 w-12 text-right">{count}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Top Locations */}
          <div className="bg-gradient-to-br from-slate-800/80 to-slate-700/50 border border-slate-700 rounded-xl shadow-xl p-6">
            <h3 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-6">🌍 Top Locations</h3>
            <div className="space-y-3">
              {Object.entries(locationCounts)
                .sort(([,a], [,b]) => b - a)
                .slice(0, 10)
                .map(([location, count]) => (
                  <div key={location} className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg hover:bg-slate-700/50 transition-all">
                    <span className="text-slate-300 font-medium">{location}</span>
                    <span className="text-sm font-bold bg-blue-500/20 text-blue-300 px-3 py-1 rounded-full border border-blue-500/30">
                      {count}
                    </span>
                  </div>
                ))}
            </div>
          </div>
        </div>

        {/* Top Companies */}
        <div className="bg-gradient-to-br from-slate-800/80 to-slate-700/50 border border-slate-700 rounded-xl shadow-xl p-6 mb-8">
          <h3 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-6">🏢 Top Companies</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(companyCounts)
              .sort(([,a], [,b]) => b - a)
              .slice(0, 12)
              .map(([company, count]) => (
                <div key={company} className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg hover:bg-slate-700/50 transition-all border border-slate-700">
                  <span className="text-slate-200 truncate font-medium">{company}</span>
                  <span className="text-sm font-bold bg-emerald-500/20 text-emerald-300 px-3 py-1 rounded-full ml-2 border border-emerald-500/30">
                    {count}
                  </span>
                </div>
              ))}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-gradient-to-br from-slate-800/80 to-slate-700/50 border border-slate-700 rounded-xl shadow-xl p-6">
          <h3 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-6">⚡ Recent Activity</h3>
          <div className="space-y-3">
            {leads.slice(0, 10).map((lead) => (
              <div key={lead.id} className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg hover:bg-slate-700/50 transition-colors border border-slate-700">
                <div>
                  <span className="font-bold text-white">{lead.company}</span>
                  <span className="text-slate-400 ml-2 text-sm">{lead.email}</span>
                </div>
                <div className="flex items-center space-x-3">
                  <span className={`px-3 py-1 text-xs font-bold rounded-full border ${
                    lead.status === 'new' ? 'bg-slate-600/50 text-slate-200 border-slate-500' :
                    lead.status === 'analyzed' ? 'bg-blue-500/20 text-blue-300 border-blue-500/30' :
                    lead.status === 'outreach_sent' ? 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30' :
                    lead.status === 'converted' ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' :
                    'bg-red-500/20 text-red-300 border-red-500/30'
                  }`}>
                    {lead.status.replace('_', ' ')}
                  </span>
                  <span className="text-sm font-semibold text-slate-400 bg-slate-700/50 px-3 py-1 rounded">
                    {lead.trust_score > 0 ? `${lead.trust_score}%` : '-'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;