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

  if (loading) return <div className="text-center mt-10">Loading Analytics...</div>;

  return (
    <div>
      <h2 className="text-3xl font-bold mb-8 text-center">Analytics Dashboard</h2>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-700">Conversion Rate</h3>
          <p className="text-3xl font-bold text-green-600">{conversionRate}%</p>
          <p className="text-sm text-gray-500">{stats.converted} of {stats.total} leads</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-700">Outreach Rate</h3>
          <p className="text-3xl font-bold text-blue-600">{outreachRate}%</p>
          <p className="text-sm text-gray-500">{stats.outreach_sent} of {stats.total} leads</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-700">Analysis Rate</h3>
          <p className="text-3xl font-bold text-purple-600">{analysisRate}%</p>
          <p className="text-sm text-gray-500">{stats.analyzed} of {stats.total} leads</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-700">Total Leads</h3>
          <p className="text-3xl font-bold text-gray-600">{stats.total}</p>
          <p className="text-sm text-gray-500">Across all sources</p>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Status Distribution */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-xl font-semibold mb-4">Lead Status Distribution</h3>
          <div className="space-y-3">
            {Object.entries(statusCounts).map(([status, count]) => (
              <div key={status} className="flex items-center justify-between">
                <span className="capitalize text-gray-700">{status.replace('_', ' ')}</span>
                <div className="flex items-center space-x-2">
                  <div className="w-24 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full" 
                      style={{ width: `${stats.total > 0 ? (count / stats.total) * 100 : 0}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-medium">{count}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Locations */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-xl font-semibold mb-4">Top Locations</h3>
          <div className="space-y-3">
            {Object.entries(locationCounts)
              .sort(([,a], [,b]) => b - a)
              .slice(0, 10)
              .map(([location, count]) => (
                <div key={location} className="flex items-center justify-between">
                  <span className="text-gray-700">{location}</span>
                  <span className="text-sm font-medium bg-blue-100 text-blue-800 px-2 py-1 rounded">
                    {count} leads
                  </span>
                </div>
              ))}
          </div>
        </div>
      </div>

      {/* Top Companies */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-xl font-semibold mb-4">Top Companies</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(companyCounts)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 12)
            .map(([company, count]) => (
              <div key={company} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <span className="text-gray-700 truncate">{company}</span>
                <span className="text-sm font-medium bg-green-100 text-green-800 px-2 py-1 rounded ml-2">
                  {count}
                </span>
              </div>
            ))}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="mt-8 bg-white p-6 rounded-lg shadow">
        <h3 className="text-xl font-semibold mb-4">Recent Activity</h3>
        <div className="space-y-3">
          {leads.slice(0, 10).map((lead) => (
            <div key={lead.id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <div>
                <span className="font-medium">{lead.name}</span>
                <span className="text-gray-500 ml-2">from {lead.company}</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className={`px-2 py-1 text-xs rounded-full ${
                  lead.status === 'new' ? 'bg-gray-100 text-gray-800' :
                  lead.status === 'analyzed' ? 'bg-blue-100 text-blue-800' :
                  lead.status === 'outreach_sent' ? 'bg-yellow-100 text-yellow-800' :
                  lead.status === 'converted' ? 'bg-green-100 text-green-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {lead.status.replace('_', ' ')}
                </span>
                <span className="text-sm text-gray-500">
                  {lead.trust_score > 0 ? `${lead.trust_score}%` : '-'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Analytics;