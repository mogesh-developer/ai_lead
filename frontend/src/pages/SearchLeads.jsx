import React, { useState } from 'react';
import api from '../api';
import { useNavigate } from 'react-router-dom';

const SearchLeads = () => {
  const [industry, setIndustry] = useState('');
  const [location, setLocation] = useState('');
  const [url, setUrl] = useState('');
  const [keywords, setKeywords] = useState('');
  const [activeTab, setActiveTab] = useState('search'); // 'search', 'scrape', or 'keyword'
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const navigate = useNavigate();

  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResults(null);
    try {
      const response = await api.post('/search-leads', { industry, location });
      setResults(response.data);
      console.log('Search results:', response.data);
      // Navigate to leads page to show the newly found leads
      if (response.data.leads && response.data.leads.length > 0) {
        navigate('/leads');
      }
    } catch (error) {
      console.error("Search failed", error);
    } finally {
      setLoading(false);
    }
  };

  const handleScrape = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResults(null);
    try {
      const response = await api.post('/scrape-url', { url });
      setResults(response.data);
    } catch (error) {
      console.error("Scrape failed", error);
    } finally {
      setLoading(false);
    }
  };

  const handleKeywordSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResults(null);
    try {
      const response = await api.post('/keyword-search', { keywords });
      setResults(response.data);
    } catch (error) {
      console.error("Keyword search failed", error);
    } finally {
      setLoading(false);
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

            {results && (
              <div className="mt-8 p-6 bg-slate-700/50 rounded-xl border border-slate-600">
                <h3 className="text-xl font-bold text-white mb-4">📊 Search Results</h3>
                <pre className="text-slate-300 text-sm overflow-auto max-h-60 bg-slate-900 p-4 rounded border border-slate-700 font-mono">
                  {JSON.stringify(results, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SearchLeads;
