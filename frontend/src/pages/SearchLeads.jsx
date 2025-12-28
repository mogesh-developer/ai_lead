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
      // Navigate removed to show results on the same page
      // if (response.data.leads && response.data.leads.length > 0) {
      //   navigate('/leads');
      // }
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
    <div className="max-w-2xl mx-auto mt-10">
      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <h2 className="text-2xl font-bold mb-6">Find Leads</h2>

        <div className="flex border-b mb-6">
          <button
            className={`py-2 px-4 font-medium ${activeTab === 'search' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500'}`}
            onClick={() => setActiveTab('search')}
          >
            AI Discovery (Search)
          </button>
          <button
            className={`py-2 px-4 font-medium ${activeTab === 'scrape' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500'}`}
            onClick={() => setActiveTab('scrape')}
          >
            Web Scraper (URL)
          </button>
          <button
            className={`py-2 px-4 font-medium ${activeTab === 'keyword' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500'}`}
            onClick={() => setActiveTab('keyword')}
          >
            Keyword Search
          </button>
        </div>

        {activeTab === 'search' ? (
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Industry / Keyword</label>
                <input
                  type="text"
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value)}
                  placeholder="e.g. Digital Marketing"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Location</label>
                <input
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="e.g. Chennai"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2"
                  required
                />
              </div>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400"
            >
              {loading ? 'AI Agent Searching...' : 'Find Leads'}
            </button>
          </form>
        ) : activeTab === 'scrape' ? (
          <form onSubmit={handleScrape} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Website URL</label>
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://example.com/contact"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2"
                required
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-purple-600 text-white py-2 px-4 rounded-md hover:bg-purple-700 disabled:bg-gray-400"
            >
              {loading ? 'Scraping Website...' : 'Scrape Leads'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleKeywordSearch} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Keywords</label>
              <input
                type="text"
                value={keywords}
                onChange={(e) => setKeywords(e.target.value)}
                placeholder="e.g. SaaS companies with remote teams"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2"
                required
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 disabled:bg-gray-400"
            >
              {loading ? 'AI Agent Searching...' : 'Find Leads by Keyword'}
            </button>
          </form>
        )}
      </div>

      {results && (

        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold text-green-600 mb-4">{results.message}</h3>
          <div className="space-y-2">
            {results.leads.map((lead, index) => (
              <div key={index} className="border-b pb-2 last:border-0">
                <p className="font-medium">{lead.company}</p>
                <p className="text-sm text-gray-500">{lead.name} | {lead.email} | {lead.phone}</p>
              </div>
            ))}
          </div>
          <button
            onClick={() => navigate('/dashboard')}
            className="mt-4 w-full bg-gray-100 text-gray-800 py-2 rounded hover:bg-gray-200"
          >
            Go to Dashboard to Analyze
          </button>
        </div>
      )}
    </div>
  );
};

export default SearchLeads;
