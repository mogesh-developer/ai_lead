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
          api.get('/leads')
        ]);
        setStats(statsRes.data);
        setLeads(leadsRes.data);
      } catch (error) {
        console.error("Error fetching analytics data", error);
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

  if (loading) return <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center text-white">Loading Analytics...</div>;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        <h2 className="text-4xl font-bold mb-8 text-white flex items-center">
          <span className="w-2 h-8 bg-gradient-to-b from-blue-400 to-purple-400 rounded mr-3"></span>
          Analytics Dashboard
        </h2>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-xl p-6">
            <h3 className="text-sm font-semibold text-slate-300 mb-2">Conversion Rate</h3>
            <p className="text-4xl font-bold text-green-400">{conversionRate}%</p>
            <p className="text-xs text-slate-400 mt-2">{stats.converted} of {stats.total} leads</p>
          </div>
          <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-xl p-6">
            <h3 className="text-sm font-semibold text-slate-300 mb-2">Outreach Rate</h3>
            <p className="text-4xl font-bold text-blue-400">{outreachRate}%</p>
            <p className="text-xs text-slate-400 mt-2">{stats.outreach_sent} of {stats.total} leads</p>
          </div>
          <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-xl p-6">
            <h3 className="text-sm font-semibold text-slate-300 mb-2">Analysis Rate</h3>
            <p className="text-4xl font-bold text-purple-400">{analysisRate}%</p>
            <p className="text-xs text-slate-400 mt-2">{stats.analyzed} of {stats.total} leads</p>
          </div>
          <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-xl p-6">
            <h3 className="text-sm font-semibold text-slate-300 mb-2">Total Leads</h3>
            <p className="text-4xl font-bold text-slate-200">{stats.total}</p>
            <p className="text-xs text-slate-400 mt-2">Across all sources</p>
          </div>
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Status Distribution */}
          <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-xl p-6">
            <h3 className="text-xl font-semibold text-white mb-6">Lead Status Distribution</h3>
            <div className="space-y-4">
              {Object.entries(statusCounts).map(([status, count]) => (
                <div key={status} className="flex items-center justify-between">
                  <span className="capitalize text-slate-300">{status.replace('_', ' ')}</span>
                  <div className="flex items-center space-x-3">
                    <div className="w-32 bg-slate-700 rounded-full h-2">
                      <div 
                        className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full" 
                        style={{ width: `${stats.total > 0 ? (count / stats.total) * 100 : 0}%` }}
                      ></div>
                    </div>
                    <span className="text-sm font-medium text-slate-200 w-8 text-right">{count}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Top Locations */}
          <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-xl p-6">
            <h3 className="text-xl font-semibold text-white mb-6">Top Locations</h3>
            <div className="space-y-3">
              {Object.entries(locationCounts)
                .sort(([,a], [,b]) => b - a)
                .slice(0, 10)
                .map(([location, count]) => (
                  <div key={location} className="flex items-center justify-between">
                    <span className="text-slate-300">{location}</span>
                    <span className="text-sm font-medium bg-blue-500/20 text-blue-300 px-3 py-1 rounded-full">
                      {count} leads
                    </span>
                  </div>
                ))}
            </div>
          </div>
        </div>

        {/* Top Companies */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-xl p-6 mb-8">
          <h3 className="text-xl font-semibold text-white mb-6">Top Companies</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(companyCounts)
              .sort(([,a], [,b]) => b - a)
              .slice(0, 12)
              .map(([company, count]) => (
                <div key={company} className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg">
                  <span className="text-slate-200 truncate">{company}</span>
                  <span className="text-sm font-medium bg-green-500/20 text-green-300 px-3 py-1 rounded-full ml-2">
                    {count}
                  </span>
                </div>
              ))}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-xl p-6">
          <h3 className="text-xl font-semibold text-white mb-6">Recent Activity</h3>
          <div className="space-y-3">
            {leads.slice(0, 10).map((lead) => (
              <div key={lead.id} className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg hover:bg-slate-700/50 transition-colors">
                <div>
                  <span className="font-medium text-white">{lead.name}</span>
                  <span className="text-slate-400 ml-2">from {lead.company}</span>
                </div>
                <div className="flex items-center space-x-3">
                  <span className={`px-3 py-1 text-xs rounded-full font-medium ${
                    lead.status === 'new' ? 'bg-slate-600 text-slate-200' :
                    lead.status === 'analyzed' ? 'bg-blue-500/20 text-blue-300' :
                    lead.status === 'outreach_sent' ? 'bg-yellow-500/20 text-yellow-300' :
                    lead.status === 'converted' ? 'bg-green-500/20 text-green-300' :
                    'bg-red-500/20 text-red-300'
                  }`}>
                    {lead.status.replace('_', ' ')}
                  </span>
                  <span className="text-sm text-slate-400">
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