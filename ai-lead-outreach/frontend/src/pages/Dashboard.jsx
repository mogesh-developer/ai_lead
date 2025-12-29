import React, { useEffect, useState } from 'react';
import api from '../api';
import StatCard from '../components/StatCard';
import LeadsTable from '../components/LeadsTable';

const Dashboard = () => {
  const [stats, setStats] = useState({ total: 0, analyzed: 0, outreach_sent: 0, converted: 0 });
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [autopilot, setAutopilot] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, leadsRes, settingsRes] = await Promise.all([
          api.get('/dashboard-stats'),
          api.get('/leads'),
          api.get('/settings')
        ]);
        setStats(statsRes.data);
        setLeads(leadsRes.data);
        setAutopilot(settingsRes.data.autopilot);
      } catch (error) {
        console.error("Error fetching dashboard data", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const toggleAutopilot = async () => {
    try {
      const newState = !autopilot;
      await api.post('/settings', { autopilot: newState });
      setAutopilot(newState);
    } catch (error) {
      console.error("Failed to toggle autopilot", error);
    }
  };

  const refreshLeads = async () => {
    try {
      const leadsRes = await api.get('/leads');
      setLeads(leadsRes.data);
      const statsRes = await api.get('/dashboard-stats');
      setStats(statsRes.data);
    } catch (error) {
      console.error("Error refreshing leads", error);
    }
  };

  if (loading) return <div className="text-center mt-10">Loading Dashboard...</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Dashboard</h2>
        <div className="flex items-center gap-4">
          <button
            onClick={() => window.open('http://localhost:5000/api/export-leads', '_blank')}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition flex items-center"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Export CSV
          </button>
          
          <div className="flex items-center bg-white p-2 rounded shadow">
            <span className="mr-3 font-medium text-gray-700">Autopilot Mode:</span>
            <button
              onClick={toggleAutopilot}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
                autopilot ? 'bg-green-500' : 'bg-gray-200'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  autopilot ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
            <span className={`ml-2 text-sm ${autopilot ? 'text-green-600 font-bold' : 'text-gray-500'}`}>
              {autopilot ? 'ON' : 'OFF'}
            </span>
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">

        <StatCard title="Total Leads" value={stats.total} color="border-blue-500" />
        <StatCard title="Analyzed" value={stats.analyzed} color="border-purple-500" />
        <StatCard title="Outreach Sent" value={stats.outreach_sent} color="border-yellow-500" />
        <StatCard title="Converted" value={stats.converted} color="border-green-500" />
      </div>

      <h3 className="text-xl font-semibold mb-4">Recent Leads</h3>
      <LeadsTable leads={leads} onRefresh={refreshLeads} />
    </div>
  );
};

export default Dashboard;
