import React, { useState } from 'react';
import api from '../api';

const SearchLeads = () => {
  const [industry, setIndustry] = useState('');
  const [location, setLocation] = useState('');
  const [url, setUrl] = useState('');
  const [keywords, setKeywords] = useState('');
  const [activeTab, setActiveTab] = useState('search'); // 'search', 'scrape', or 'keyword'
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [message, setMessage] = useState('');
  const [lastAction, setLastAction] = useState('search');
  const [saving, setSaving] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResults(null);
    setMessage('');
    try {
      const response = await api.post('/search-leads', { industry, location });
      setResults(response.data);
      setLastAction('search');
      setMessage(response.data.message || `Found ${response.data.count || 0} leads`);
      console.log('Search results:', response.data);
    } catch (error) {
      console.error('Search failed', error);
      setMessage(error.response?.data?.error || 'Discovery failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleScrape = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResults(null);
    setMessage('');
    try {
      const response = await api.post('/scrape-url', { url });
      setResults(response.data);
      setLastAction('scrape');
      setMessage(response.data.message || `Scraped ${response.data.count || 0} items.`);
    } catch (error) {
      console.error('Scrape failed', error);
      setMessage(error.response?.data?.error || 'Scrape failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeywordSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResults(null);
    setMessage('');
    try {
      const response = await api.post('/keyword-search', { keywords });
      setResults(response.data);
      setLastAction('keyword');
      setMessage(response.data.message || `Checked ${response.data.total_keywords || 0} keywords`);
    } catch (error) {
      console.error('Keyword search failed', error);
      setMessage(error.response?.data?.error || 'Keyword search failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveLeads = async (leads) => {
    if (!leads || leads.length === 0) return;
    setSaving(true);
    try {
      const res = await api.post('/save-domain-leads', { leads });
      setMessage(res.data.message || `Saved ${res.data.count || leads.length} leads.`);
    } catch (error) {
      console.error('Saving leads failed', error);
      setMessage(error.response?.data?.error || 'Save failed.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="w-full h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-800 to-slate-900 border-b border-slate-700 px-8 py-6 flex-shrink-0">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-2">
          🔍 Find Leads
        </h1>
        <p className="text-slate-400 text-lg">Search, scrape, or discover leads using multiple methods</p>
      </div>

      {/* Main Content */}
      <div className="flex-grow overflow-y-auto px-8 py-8 scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-slate-700">
        <div className="max-w-4xl mx-auto">
          <div className="bg-slate-800/80 border border-slate-700 rounded-2xl shadow-2xl p-8">

            <div className="flex border-b border-slate-700 mb-8 gap-1">
              <button
                className={`py-3 px-6 font-bold transition-all duration-200 ${
                  activeTab === 'search' 
                    ? 'text-blue-400 border-b-2 border-blue-400' 
                    : 'text-slate-400 hover:text-slate-300'
                }`}
                onClick={() => setActiveTab('search')}
              >
                🤖 AI Discovery
              </button>
              <button
                className={`py-3 px-6 font-bold transition-all duration-200 ${
                  activeTab === 'scrape' 
                    ? 'text-blue-400 border-b-2 border-blue-400' 
                    : 'text-slate-400 hover:text-slate-300'
                }`}
                onClick={() => setActiveTab('scrape')}
              >
                🌐 Web Scraper
              </button>
              <button
                className={`py-3 px-6 font-bold transition-all duration-200 ${
                  activeTab === 'keyword' 
                    ? 'text-blue-400 border-b-2 border-blue-400' 
                    : 'text-slate-400 hover:text-slate-300'
                }`}
                onClick={() => setActiveTab('keyword')}
              >
                🔎 Keyword Search
              </button>
            </div>

            {activeTab === 'search' && (
              <form onSubmit={handleSearch} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-bold text-slate-200 mb-3">Industry / Keyword</label>
                    <input
                      type="text"
                      value={industry}
                      onChange={(e) => setIndustry(e.target.value)}
                      placeholder="e.g. Digital Marketing"
                      className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-slate-200 mb-3">Location</label>
                    <input
                      type="text"
                      value={location}
                      onChange={(e) => setLocation(e.target.value)}
                      placeholder="e.g. New York, USA"
                      className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
                      required
                    />
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 disabled:from-slate-600 disabled:to-slate-600 text-white font-bold py-3 px-6 rounded-lg transition-all duration-200 shadow-lg"
                >
                  {loading ? '⏳ Searching...' : '🚀 Search Leads'}
                </button>
              </form>
            )}

            {activeTab === 'scrape' && (
              <form onSubmit={handleScrape} className="space-y-6">
                <div>
                  <label className="block text-sm font-bold text-slate-200 mb-3">Website URL</label>
                  <input
                    type="url"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="e.g. https://example.com/team"
                    className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
                    required
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-700 hover:to-purple-600 disabled:from-slate-600 disabled:to-slate-600 text-white font-bold py-3 px-6 rounded-lg transition-all duration-200 shadow-lg"
                >
                  {loading ? '⏳ Scraping...' : '🕷️ Scrape Website'}
                </button>
              </form>
            )}

            {activeTab === 'keyword' && (
              <form onSubmit={handleKeywordSearch} className="space-y-6">
                <div>
                  <label className="block text-sm font-bold text-slate-200 mb-3">Keywords (comma-separated)</label>
                  <textarea
                    value={keywords}
                    onChange={(e) => setKeywords(e.target.value)}
                    placeholder="e.g. CEO, marketing director, sales manager"
                    rows="4"
                    className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all resize-none"
                    required
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-700 hover:to-emerald-600 disabled:from-slate-600 disabled:to-slate-600 text-white font-bold py-3 px-6 rounded-lg transition-all duration-200 shadow-lg"
                >
                  {loading ? '⏳ Searching...' : '📋 Find by Keywords'}
                </button>
              </form>
            )}

            {message && (
              <div className="mt-6 px-4 py-3 rounded-lg text-sm border text-slate-100 bg-slate-900/60 border-slate-700">
                {message}
              </div>
            )}

            {lastAction === 'search' && results?.leads?.length > 0 && (
              <div className="mt-8 bg-slate-800 border border-slate-700 rounded-xl shadow-xl overflow-hidden">
                <div className="p-6 border-b border-slate-700 flex flex-wrap items-center justify-between gap-3">
                  <h3 className="text-2xl font-bold text-white">🤖 AI Discovery ({results.count || results.leads.length})</h3>
                  <button
                    onClick={() => handleSaveLeads(results.leads)}
                    disabled={saving}
                    className="text-sm bg-green-600 hover:bg-green-700 disabled:bg-slate-600 text-white px-4 py-2 rounded-lg transition-colors"
                  >
                    {saving ? 'Saving...' : 'Save Leads'}
                  </button>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-slate-700/50 border-b border-slate-700">
                        <th className="px-4 py-3 text-left font-semibold text-slate-200">Company</th>
                        <th className="px-4 py-3 text-left font-semibold text-slate-200">Email</th>
                        <th className="px-4 py-3 text-left font-semibold text-slate-200">Position</th>
                        <th className="px-4 py-3 text-left font-semibold text-slate-200">Source</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-700">
                      {results.leads.map((lead, index) => (
                        <tr key={index} className="hover:bg-slate-700/30 transition-colors">
                          <td className="px-4 py-3 font-medium text-white">{lead.company || 'N/A'}</td>
                          <td className="px-4 py-3 text-blue-400">{lead.email}</td>
                          <td className="px-4 py-3 text-slate-300">{lead.position || 'N/A'}</td>
                          <td className="px-4 py-3 text-slate-300">{lead.source || 'AI search'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {lastAction === 'scrape' && results && (
              <div className="mt-8 bg-slate-800 border border-slate-700 rounded-xl shadow-xl p-6 space-y-4">
                <div className="flex flex-wrap items-center gap-3 justify-between">
                  <div>
                    <h3 className="text-2xl font-bold text-white">🌐 Web Scraper</h3>
                    <p className="text-sm text-slate-400">{results.url}</p>
                  </div>
                  <button
                    onClick={() => handleSaveLeads(results.leads)}
                    disabled={saving || !results.leads?.length}
                    className="text-sm bg-green-600 hover:bg-green-700 disabled:bg-slate-600 text-white px-4 py-2 rounded-lg transition-colors"
                  >
                    {saving ? 'Saving...' : 'Save Scraped Leads'}
                  </button>
                </div>
                <div className="grid lg:grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-slate-300">Emails ({results.emails?.length || 0})</p>
                    <ul className="text-slate-200 text-sm space-y-1 max-h-48 overflow-auto">
                      {results.emails?.length > 0 ? (
                        results.emails.map((email, index) => (
                          <li key={index} className="truncate font-mono">{email}</li>
                        ))
                      ) : (
                        <li className="text-slate-500">No emails found</li>
                      )}
                    </ul>
                  </div>
                  <div>
                    <p className="text-sm text-slate-300">Phones ({results.phones?.length || 0})</p>
                    <ul className="text-slate-200 text-sm space-y-1 max-h-48 overflow-auto">
                      {results.phones?.length > 0 ? (
                        results.phones.map((phone, index) => (
                          <li key={index} className="truncate font-mono">{phone}</li>
                        ))
                      ) : (
                        <li className="text-slate-500">No phone numbers found</li>
                      )}
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {lastAction === 'keyword' && results && (
              <div className="mt-8 bg-slate-800 border border-slate-700 rounded-xl shadow-xl p-6 space-y-6">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-2xl font-bold text-white">🔎 Keyword Search</h3>
                  <span className="text-sm text-slate-400">Total leads: {results.total_leads || 0}</span>
                </div>
                <div className="space-y-4">
                  {results.keywords?.map((entry, idx) => (
                    <div key={idx} className="p-4 bg-slate-900/80 rounded-lg border border-slate-700">
                      <div className="flex flex-wrap justify-between items-center gap-2">
                        <div>
                          <p className="text-sm text-slate-400">Keyword</p>
                          <p className="text-lg font-semibold text-white">{entry.keyword}</p>
                          <p className="text-xs text-slate-500">Query: {entry.query}</p>
                        </div>
                        <button
                          onClick={() => handleSaveLeads(entry.leads)}
                          disabled={saving || !entry.leads?.length}
                          className="text-sm bg-green-600 hover:bg-green-700 disabled:bg-slate-600 text-white px-4 py-2 rounded-lg transition-colors"
                        >
                          {saving ? 'Saving...' : 'Save Leads'}
                        </button>
                      </div>
                      <p className="text-sm text-slate-300">Leads: {entry.count}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SearchLeads;
