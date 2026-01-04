import React, { useState, useEffect } from 'react';
import api from '../api';

const DomainSearch = () => {
  const [domain, setDomain] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [message, setMessage] = useState('');
  const [balance, setBalance] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchBalance();
  }, []);

  const fetchBalance = async () => {
    try {
      const res = await api.get('/snov-balance');
      setBalance(res.data);
    } catch (err) {
      console.error("Failed to fetch balance", err);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    console.log("Starting domain search for:", domain);
    setLoading(true);
    setResults([]);
    setMessage('');
    try {
      console.log("Sending request to /search-domain");
      const response = await api.post('/search-domain', { domain });
      console.log("Response received:", response);
      setResults(response.data.leads);
      setMessage(response.data.message);
      fetchBalance(); // Update balance after search
    } catch (error) {
      console.error("Domain search failed", error);
      if (error.response) {
          console.error("Error response data:", error.response.data);
          console.error("Error response status:", error.response.status);
      }
      const errorMsg = error.response?.data?.error || "Search failed. Please check your Snov.io credentials.";
      setMessage(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveLeads = async () => {
    if (results.length === 0) return;
    setSaving(true);
    try {
      const res = await api.post('/save-domain-leads', { leads: results });
      setMessage(`Successfully saved ${res.data.count} leads to database.`);
    } catch (err) {
      console.error("Failed to save leads", err);
      setMessage("Failed to save leads to database.");
    } finally {
      setSaving(false);
    }
  };

  const handleExportCSV = () => {
    if (results.length === 0) return;
    const headers = ['Email', 'Name/Company', 'Position', 'Source'];
    const csvContent = [
      headers.join(','),
      ...results.map(r => [r.email, r.company, r.position, r.source].map(f => `"${f || ''}"`).join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    if (link.download !== undefined) {
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', `leads_${domain}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-xl p-8 mb-8">
          <div className="mb-8 flex justify-between items-start">
            <div>
              <h2 className="text-4xl font-bold text-white mb-2 flex items-center">
                <span className="w-2 h-8 bg-gradient-to-b from-blue-400 to-purple-400 rounded mr-3"></span>
                Domain Email Finder
              </h2>
              <p className="text-slate-300 text-lg">Discover all emails associated with a company domain using advanced lookup services.</p>
            </div>
            {balance && (
              <div className="bg-slate-700/50 p-4 rounded-lg border border-slate-600 text-right">
                <p className="text-sm text-slate-400">Snov.io Credits</p>
                <p className="text-xl font-bold text-white">{balance.balance} / {balance.limit || '∞'}</p>
                {balance.expires && <p className="text-xs text-slate-500">Resets: {new Date(balance.expires * 1000).toLocaleDateString()}</p>}
              </div>
            )}
          </div>
          <form onSubmit={handleSearch} className="space-y-6">
            <div>
              <label className="block text-sm font-semibold text-slate-200 mb-3">Domain Name</label>
              <div className="relative">
                <input
                  type="text"
                  value={domain}
                  onChange={(e) => setDomain(e.target.value)}
                  placeholder="e.g. apple.com, google.com, microsoft.com"
                  className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-400/20 transition-all"
                  required
                />
              </div>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 disabled:from-slate-600 disabled:to-slate-600 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 shadow-lg"
            >
              {loading ? 'Searching...' : 'Search Domain'}
            </button>
          </form>
        </div>

        {message && (
          <div className={`p-4 rounded-lg mb-6 border ${message.includes('failed') || message.includes('error') ? 'bg-red-900/20 border-red-700 text-red-300' : 'bg-green-900/20 border-green-700 text-green-300'}`}>
            {message}
          </div>
        )}

        {results.length > 0 && (
          <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-xl overflow-hidden">
            <div className="p-8 border-b border-slate-700 flex justify-between items-center">
              <h3 className="text-2xl font-bold text-white">Found {results.length} Email(s)</h3>
              <div className="space-x-4">
                <button
                  onClick={handleExportCSV}
                  className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
                >
                  Export CSV
                </button>
                <button
                  onClick={handleSaveLeads}
                  disabled={saving}
                  className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-slate-600 text-white rounded-lg transition-colors"
                >
                  {saving ? 'Saving...' : 'Save to Leads'}
                </button>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-slate-700/50 border-b border-slate-700">
                    <th className="px-6 py-4 text-left text-sm font-semibold text-slate-200">Name</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-slate-200">Email</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-slate-200">Position</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((lead, index) => (
                    <tr key={index} className="border-b border-slate-700 hover:bg-slate-700/30 transition-colors">
                      <td className="px-6 py-4 text-sm text-white font-medium">{lead.company || 'N/A'}</td>
                      <td className="px-6 py-4 text-sm text-blue-400">{lead.email}</td>
                      <td className="px-6 py-4 text-sm text-slate-300">{lead.position || 'N/A'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DomainSearch;
