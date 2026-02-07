import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { HiPaperAirplane } from 'react-icons/hi';
import api from '../api';

const LeadsTable = ({ leads = [], onRefresh, loading = false }) => {
  const [selectedLeads, setSelectedLeads] = useState([]);
  const [processing, setProcessing] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [sortBy, setSortBy] = useState('id');
  const [sortOrder, setSortOrder] = useState('desc');

  // Filtered and sorted leads
  const filteredLeads = useMemo(() => {
    let filtered = leads.filter(lead => {
      const matchesSearch = !searchTerm || 
        lead.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        lead.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        lead.company?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        lead.location?.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesStatus = !statusFilter || lead.status === statusFilter;
      
      return matchesSearch && matchesStatus;
    });

    // Sort
    filtered.sort((a, b) => {
      let aVal = a[sortBy];
      let bVal = b[sortBy];
      
      if (sortBy === 'trust_score') {
        aVal = aVal || 0;
        bVal = bVal || 0;
      }
      
      if (typeof aVal === 'string') {
        aVal = aVal.toLowerCase();
        bVal = bVal.toLowerCase();
      }
      
      if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

    return filtered;
  }, [leads, searchTerm, statusFilter, sortBy, sortOrder]);

  const handleSort = (column) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('asc');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'new': return 'bg-gray-100 text-gray-800';
      case 'analyzed': return 'bg-blue-100 text-blue-800';
      case 'outreach_sent': return 'bg-yellow-100 text-yellow-800';
      case 'responded': return 'bg-green-100 text-green-800';
      case 'converted': return 'bg-purple-100 text-purple-800';
      case 'skipped': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedLeads(leads.map(l => l.id));
    } else {
      setSelectedLeads([]);
    }
  };

  const handleSelectOne = (id) => {
    if (selectedLeads.includes(id)) {
      setSelectedLeads(selectedLeads.filter(lId => lId !== id));
    } else {
      setSelectedLeads([...selectedLeads, id]);
    }
  };

  const handleQuickAnalyze = async (id) => {
    try {
      await api.post(`/analyze/${id}`);
      if (onRefresh) onRefresh();
    } catch (error) {
      console.error("Quick analysis failed", error);
    }
  };

  const handleBulkAnalyze = async () => {
    setProcessing(true);
    try {
      await Promise.all(selectedLeads.map(id => api.post(`/analyze/${id}`)));
      if (onRefresh) onRefresh();
      setSelectedLeads([]);
    } catch (error) {
      console.error("Bulk analysis failed", error);
    } finally {
      setProcessing(false);
    }
  };

  const handleBulkOutreach = async () => {
    if (!window.confirm(`Send AI-personalized outreach to ${selectedLeads.length} leads?`)) return;
    setProcessing(true);
    try {
      // Use the newly enhanced bulk endpoint with mode='ai'
      const response = await api.post('/bulk-outreach', { 
        lead_ids: selectedLeads,
        mode: 'ai' 
      });
      alert(`Outreach process complete!\nSent: ${response.data.sent}\nFailed: ${response.data.failed}${response.data.dry_runs > 0 ? `\n(Note: ${response.data.dry_runs} were dry runs)` : ''}`);
      if (onRefresh) onRefresh();
      setSelectedLeads([]);
    } catch (error) {
      console.error("Bulk outreach failed", error);
      alert("Bulk outreach failed. Check console for details.");
    } finally {
      setProcessing(false);
    }
  };

  const handleSingleOutreach = async (id) => {
    if (!window.confirm("Send AI-personalized outreach to this lead?")) return;
    try {
      const res = await api.post(`/outreach/${id}`, { outreach_type: 'ai' });
      alert("Outreach sent successfully!");
      if (onRefresh) onRefresh();
    } catch (error) {
      console.error("Outreach failed", error);
      alert("Outreach failed: " + (error.response?.data?.error || error.message));
    }
  };

  const handleExportCSV = () => {
    if (leads.length === 0) return;
    
    const headers = ['ID', 'Name', 'Email', 'Phone', 'Company', 'Location', 'Status', 'Trust Score'];
    const csvContent = [
      headers.join(','),
      ...leads.map(lead => [
        lead.id,
        `"${lead.name || ''}"`,
        `"${lead.email || ''}"`,
        `"${lead.phone || ''}"`,
        `"${lead.company || ''}"`,
        `"${lead.location || ''}"`,
        lead.status,
        lead.trust_score
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    if (link.download !== undefined) {
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', 'leads_export.csv');
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <div className="space-y-4">
          <div className="h-6 bg-gray-200 rounded animate-pulse w-44" />
          <div className="h-40 bg-gray-200 rounded animate-pulse w-full" />
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-0 overflow-hidden">
      {/* Filters and Search */}
      <div className="p-4 border-b border-gray-100 bg-gray-50/30">
        <div className="flex flex-wrap gap-4 mb-4">
          <div className="flex-1 min-w-64">
            <div className="relative">
              <input
                type="text"
                placeholder="Search leads..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-sm"
              />
              <svg className="w-5 h-5 text-gray-400 absolute left-3 top-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-sm bg-white"
          >
            <option value="">All Statuses</option>
            <option value="new">New</option>
            <option value="analyzed">Analyzed</option>
            <option value="outreach_sent">Outreach Sent</option>
            <option value="responded">Responded</option>
            <option value="converted">Converted</option>
            <option value="skipped">Skipped</option>
          </select>
        </div>
        
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <span className="text-xs font-medium text-gray-500 px-2 py-1 bg-gray-100 rounded-md">
              {selectedLeads.length} selected
            </span>
            {selectedLeads.length > 0 && (
              <div className="flex gap-2">
                <button 
                  onClick={handleBulkAnalyze}
                  disabled={processing}
                  className="px-3 py-1.5 bg-blue-600 text-white text-xs font-semibold rounded-lg hover:bg-blue-700 disabled:opacity-50 shadow-sm transition-all"
                >
                  {processing ? '...' : 'Analyze'}
                </button>
                <button 
                  onClick={handleBulkOutreach}
                  disabled={processing}
                  className="px-3 py-1.5 bg-green-600 text-white text-xs font-semibold rounded-lg hover:bg-green-700 disabled:opacity-50 shadow-sm transition-all"
                >
                  {processing ? '...' : 'Send Outreach'}
                </button>
              </div>
            )}
          </div>
          <button 
            onClick={handleExportCSV}
            className="px-3 py-1.5 border border-gray-200 text-gray-600 text-xs font-semibold rounded-lg hover:bg-gray-50 transition-all flex items-center gap-1"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Export
          </button>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-100">
          <thead className="bg-gray-50/50">
            <tr>
              <th className="px-6 py-4 text-left">
                <input 
                  type="checkbox" 
                  onChange={handleSelectAll}
                  checked={filteredLeads.length > 0 && selectedLeads.length === filteredLeads.length}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500/20"
                />
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors" onClick={() => handleSort('name')}>
                <div className="flex items-center gap-1">
                  Lead Info
                  {sortBy === 'name' && (sortOrder === 'asc' ? '↑' : '↓')}
                </div>
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" onClick={() => handleSort('company')}>
                Company {sortBy === 'company' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" onClick={() => handleSort('status')}>
                Status {sortBy === 'status' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" onClick={() => handleSort('trust_score')}>
                Trust {sortBy === 'trust_score' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-50">
            {filteredLeads.map((lead) => (
              <tr key={lead.id} className="hover:bg-blue-50/30 transition-colors group">
                <td className="px-6 py-4 whitespace-nowrap">
                  <input 
                    type="checkbox" 
                    checked={selectedLeads.includes(lead.id)}
                    onChange={() => handleSelectOne(lead.id)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500/20"
                  />
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold text-xs">
                      {lead.name ? lead.name[0] : (lead.email ? lead.email[0].toUpperCase() : '?')}
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-semibold text-gray-900">{lead.name || 'Unknown'}</div>
                      <div className="text-xs text-gray-500">{lead.email}</div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-700">{lead.company || lead.location || '-'}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2.5 py-1 inline-flex text-xs leading-5 font-semibold rounded-full border ${
                    lead.status === 'responded' ? 'bg-green-50 border-green-100 text-green-700' :
                    lead.status === 'outreach_sent' ? 'bg-yellow-50 border-yellow-100 text-yellow-700' :
                    lead.status === 'analyzed' ? 'bg-blue-50 border-blue-100 text-blue-700' :
                    'bg-gray-50 border-gray-100 text-gray-600'
                  }`}>
                    {lead.status?.replace('_', ' ')}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center gap-1.5">
                    <div className={`w-2 h-2 rounded-full ${
                      (lead.trust_score || 0) > 70 ? 'bg-green-500' : 
                      (lead.trust_score || 0) > 40 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}></div>
                    <span className="text-sm font-medium text-gray-900">{lead.trust_score || 0}%</span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <div className="flex items-center gap-2">
                    <Link 
                      to={`/lead/${lead.id}`} 
                      title="View Details" 
                      className="text-blue-600 hover:text-blue-900 bg-blue-50 px-3 py-1.5 rounded-lg border border-blue-100 transition-all font-bold text-xs"
                    >
                      View
                    </Link>
                    <Link 
                      to={`/lead/${lead.id}?action=outreach`} 
                      title="Send Personalized Outreach"
                      className="text-white hover:bg-green-700 bg-green-600 px-3 py-1.5 rounded-lg border border-green-700 transition-all font-bold text-xs shadow-sm shadow-green-100 flex items-center gap-1.5"
                    >
                      <HiPaperAirplane className="w-3.5 h-3.5 rotate-45" />
                      Outreach
                    </Link>
                    <button 
                      onClick={() => handleQuickAnalyze(lead.id)}
                      title="Run Matrix Analysis"
                      className="text-purple-600 hover:text-purple-900 bg-purple-50 px-3 py-1.5 rounded-lg border border-purple-100 transition-all font-bold text-xs"
                    >
                      Analyze
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default LeadsTable;
