import React, { useEffect, useState } from 'react';
import api from '../api';
import StatCard from '../components/StatCard';
import LeadsTable from '../components/LeadsTable';
import Card from '../components/ui/Card';
import Skeleton from '../components/ui/Skeleton';
import { 
  HiUsers, 
  HiOutlinePaperAirplane, 
  HiOutlineChatAlt2, 
  HiEye, 
  HiLightningBolt, 
  HiRefresh,
  HiDownload,
  HiTrendingUp
} from 'react-icons/hi';

const Dashboard = () => {
  const [stats, setStats] = useState({ 
    total: 0, 
    analyzed: 0, 
    outreach_sent: 0, 
    converted: 0,
    opened: 0,
    replied: 0
  });
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [autopilot, setAutopilot] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setRefreshing(true);
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
      setRefreshing(false);
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
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Show lightweight skeletons if refreshing
  const showSkeletons = refreshing && leads.length === 0;

  const openRate = stats.outreach_sent > 0 ? (stats.opened / stats.outreach_sent * 100).toFixed(1) : 0;
  const replyRate = stats.outreach_sent > 0 ? (stats.replied / stats.outreach_sent * 100).toFixed(1) : 0;

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Outreach Command Center</h1>
          <p className="text-gray-500 text-sm mt-1">Manage your leads and automated sequences from one place.</p>
        </div>
        
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={fetchData}
            disabled={refreshing}
            className="p-2 text-gray-500 hover:text-blue-600 bg-white rounded-lg border border-gray-200 shadow-sm transition-all flex items-center gap-2 text-sm font-medium"
          >
            <HiRefresh className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>

          <div className="h-8 border-l border-gray-200 mx-1 hidden md:block"></div>

          <button
            onClick={() => window.open('http://localhost:5000/api/export-leads', '_blank')}
            className="px-4 py-2 bg-white text-gray-700 border border-gray-200 rounded-lg shadow-sm hover:bg-gray-50 transition-all flex items-center gap-2 text-sm font-medium"
          >
            <HiDownload className="w-4 h-4" />
            Export Data
          </button>
          
          <div className="flex items-center bg-white px-4 py-2 rounded-lg border border-gray-200 shadow-sm">
            <div className="flex items-center gap-2 mr-4">
              <div className={`w-2 h-2 rounded-full ${autopilot ? 'bg-green-500 animate-pulse' : 'bg-gray-300'}`}></div>
              <span className="text-sm font-medium text-gray-700">Autopilot</span>
            </div>
            <button
              onClick={toggleAutopilot}
              className={`relative inline-flex h-5 w-10 items-center rounded-full transition-colors focus:outline-none ${
                autopilot ? 'bg-blue-600' : 'bg-gray-200'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white shadow-sm transition-transform ${
                  autopilot ? 'translate-x-[1.375rem]' : 'translate-x-0.5'
                }`}
              />
            </button>
          </div>
        </div>
      </div>
      
      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          title="Total Leads" 
          value={stats.total} 
          icon={HiUsers} 
          color="blue" 
          trend="up" 
          trendValue={12} 
        />
        <StatCard 
          title="Outreach Sent" 
          value={stats.outreach_sent} 
          icon={HiOutlinePaperAirplane} 
          color="yellow" 
        />
        <StatCard 
          title="Emails Opened" 
          value={stats.opened} 
          icon={HiEye} 
          color="purple" 
          trend="up" 
          trendValue={openRate} 
        />
        <StatCard 
          title="Responses" 
          value={stats.replied} 
          icon={HiOutlineChatAlt2} 
          color="green" 
          trend="up" 
          trendValue={replyRate}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Content: Leads Table */}
        <div className="lg:col-span-2 space-y-6">
          <Card header={<div className="flex items-center justify-between"><h3 className="font-semibold text-gray-900 flex items-center gap-2"><HiLightningBolt className="text-orange-500 w-5 h-5" />Active Leads</h3><span className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded font-medium">{leads.length} Active</span></div>}>
            {showSkeletons ? (
              <div className="space-y-4">
                <Skeleton className="h-6 w-56" />
                <Skeleton className="h-40 w-full" />
              </div>
            ) : (
              <LeadsTable leads={leads} onRefresh={fetchData} loading={refreshing} />
            )}
          </Card>
        </div>

        {/* Sidebar: Activity & Performance */}
        <div className="space-y-8">
          {/* Performance Summary Cards */}
          <div className="bg-gradient-to-br from-blue-600 to-indigo-700 rounded-xl shadow-lg p-6 text-white">
            <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
              <HiTrendingUp className="w-5 h-5" />
              Campaign health
            </h3>
            <p className="text-blue-100 text-sm mb-6">Your outreach efforts are trending upwards.</p>
            
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Open Rate</span>
                  <span className="font-bold">{openRate}%</span>
                </div>
                <div className="w-full bg-blue-900/30 rounded-full h-2">
                  <div className="bg-white rounded-full h-2" style={{ width: `${Math.min(openRate, 100)}%` }}></div>
                </div>
              </div>
              
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Reply Rate</span>
                  <span className="font-bold">{replyRate}%</span>
                </div>
                <div className="w-full bg-blue-900/30 rounded-full h-2">
                  <div className="bg-green-400 rounded-full h-2" style={{ width: `${Math.min(replyRate, 100)}%` }}></div>
                </div>
              </div>
            </div>
          </div>

          {/* Activity Feed */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
              Recent Activity
            </h3>
            <div className="space-y-6">
              {leads.filter(l => l.last_outreach_at).slice(0, 5).map((lead, i) => (
                <div key={i} className="flex gap-4">
                  <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${
                    lead.replied ? 'bg-green-500' : lead.opened ? 'bg-purple-500' : 'bg-yellow-500'
                  }`}></div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {lead.replied ? 'Responded to' : lead.opened ? 'Opened email' : 'Sent outreach to'} {lead.name || lead.email}
                    </p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {new Date(lead.last_outreach_at).toLocaleDateString()} at {new Date(lead.last_outreach_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                    </p>
                  </div>
                </div>
              ))}
              {leads.filter(l => l.last_outreach_at).length === 0 && (
                <p className="text-center text-gray-400 text-sm py-4">No recent outreach activity</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
