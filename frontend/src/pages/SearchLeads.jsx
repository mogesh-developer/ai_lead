import React, { useState, useEffect } from 'react';
import api from '../api';
import { useNavigate } from 'react-router-dom';
import { HiPaperAirplane } from 'react-icons/hi';

const SearchLeads = () => {
  const [industry, setIndustry] = useState('');
  const [location, setLocation] = useState('');
  const [url, setUrl] = useState('');
  const [keywords, setKeywords] = useState('');
  const [domain, setDomain] = useState('');
  const [activeTab, setActiveTab] = useState('search'); // 'search', 'scrape', 'keyword', or 'domain'
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [selectedLeads, setSelectedLeads] = useState(new Set());
  const [timer, setTimer] = useState(60);
  const [isTimerActive, setIsTimerActive] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    let interval = null;
    if (isTimerActive && timer > 0) {
      interval = setInterval(() => {
        setTimer((prevTimer) => prevTimer - 1);
      }, 1000);
    } else if (isTimerActive && timer === 0) {
      // Timer finished, auto-confirm all
      handleAutoConfirm();
    }
    return () => clearInterval(interval);
  }, [isTimerActive, timer]);

  const startSelection = (leads) => {
    // Select all by default initially? Or none? 
    // User said: "if we not select the wated lead all leads will be selected"
    // This implies default is ALL, or default is NONE and timeout selects ALL.
    // Let's default to NONE selected manually, but timeout selects ALL.
    setSelectedLeads(new Set()); 
    setTimer(60);
    setIsTimerActive(true);
  };

  const handleQuickOutreach = async (lead) => {
    try {
      const saveRes = await api.post('/leads', { 
        leads: [{
          ...lead,
          status: 'pending'
        }] 
      });
      const savedLeadId = saveRes.data.ids[0];
      navigate(`/lead/${savedLeadId}`);
    } catch (err) {
      console.error("Quick outreach failed", err);
    }
  };

  const handleAutoConfirm = async () => {
    setIsTimerActive(false);
    if (!results || !results.leads) return;
    
    // If user hasn't selected anything, select ALL. 
    // If user has selected some, do we add only those? 
    // "if we not select the wated lead all leads will be selected" -> implies fallback to all.
    // But if I selected 2 out of 10, I probably only want those 2.
    // So: If selectedLeads is empty, add ALL. Else add selected.
    
    let leadsToConfirm = [];
    if (selectedLeads.size === 0) {
        leadsToConfirm = results.leads;
        // alert("Timer expired! Auto-selecting ALL leads.");
    } else {
        leadsToConfirm = results.leads.filter((_, index) => selectedLeads.has(index));
        // alert("Timer expired! Confirming your selection.");
    }
    
    await confirmLeads(leadsToConfirm);
  };

  const confirmLeads = async (leadsToSave) => {
    try {
        setLoading(true);
        await api.post('/leads/bulk', { leads: leadsToSave });
        navigate('/dashboard');
    } catch (error) {
        console.error("Failed to save leads", error);
        alert("Failed to save leads");
    } finally {
        setLoading(false);
        setResults(null);
        setIsTimerActive(false);
    }
  };

  const handleManualConfirm = async () => {
      if (selectedLeads.size === 0) {
          if(!window.confirm("No leads selected. This will cancel the import. Are you sure?")) return;
          setResults(null);
          setIsTimerActive(false);
          return;
      }
      const leadsToConfirm = results.leads.filter((_, index) => selectedLeads.has(index));
      await confirmLeads(leadsToConfirm);
  };

  const toggleSelection = (index) => {
      const newSelection = new Set(selectedLeads);
      if (newSelection.has(index)) {
          newSelection.delete(index);
      } else {
          newSelection.add(index);
      }
      setSelectedLeads(newSelection);
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResults(null);
    try {
      const response = await api.post('/search-leads', { industry, location });
      // If API returned an explicit error
      if (response.data && response.data.error) {
        console.error("Search API error", response.data);
        alert("Search failed: " + (response.data.details || response.data.error));
        setResults({ leads: [] });
        return;
      }

      const data = response.data || {};
      // Normalize: ensure there's a leads array
      const leads = Array.isArray(data.leads) ? data.leads : (data.leads || []);
      setResults({ ...data, leads });

      if (leads.length > 0) {
        startSelection(leads);
      } else {
        // No leads found: show helpful message to user
        alert("No leads found for this query. Try broader keywords or a different location.");
      }
    } catch (error) {
      console.error("Search failed", error);
      const msg = error.response?.data?.error || error.message || 'Unknown error';
      alert("Search failed: " + msg);
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
      if (response.data.leads && response.data.leads.length > 0) {
        startSelection(response.data.leads);
    }
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
      if (response.data.leads && response.data.leads.length > 0) {
        startSelection(response.data.leads);
    }
    } finally {
      setLoading(false);
    }
  };

  const handleDomainSearch = async (e) => {
    e.preventDefault();
    if (!domain) return;
    setLoading(true);
    try {
      const response = await api.post('/search-domain', { domain });
      setResults(response.data);
      if (response.data.leads && response.data.leads.length > 0) {
        startSelection(response.data.leads);
      }
    } catch (error) {
      console.error("Domain search failed", error);
      alert("Snov.io domain search failed. Ensure API keys are in .env");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto mt-10">
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
          <button
            className={`py-2 px-4 font-medium ${activeTab === 'domain' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500'}`}
            onClick={() => setActiveTab('domain')}
          >
            Snov.io Domain Hunt
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
        ) : activeTab === 'keyword' ? (
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
        ) : (
          <form onSubmit={handleDomainSearch} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Company Domain</label>
              <input
                type="text"
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                placeholder="e.g. microsoft.com"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2"
                required
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 disabled:bg-gray-400"
            >
              {loading ? 'Hunting Domain...' : 'Hunt with Snov.io'}
            </button>
          </form>
        )}
      </div>

      {results && results.leads && (
        <div className="bg-white p-6 rounded-lg shadow-md border-2 border-blue-100">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-green-600">
                Found {results.leads.length} Potential Leads
            </h3>
            {isTimerActive && (
                <div className="text-red-600 font-bold text-xl animate-pulse">
                    Auto-confirm in: {timer}s
                </div>
            )}
          </div>
          
          <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-800">
             Select the leads you want to keep. If you don't select any, ALL leads will be added automatically when the timer expires.
          </div>

          {results.leads.length === 0 ? (
            <div className="p-6 text-center text-gray-500">
              No leads were found for your query. Try broader keywords, a nearby city, or switch to Scraper/Keyword search.
            </div>
          ) : (
            <>
              <div className="space-y-2 max-h-96 overflow-y-auto mb-4">
                {results.leads.map((lead, index) => (
                <div 
                  key={index} 
                  className={`p-3 border rounded flex items-start gap-3 cursor-pointer transition-colors ${selectedLeads.has(index) ? 'bg-blue-50 border-blue-300' : 'hover:bg-gray-50'}`}
                  onClick={() => toggleSelection(index)}
                >
                  {/* Handled by parent div click */}
                  <input 
                      type="checkbox" 
                      checked={selectedLeads.has(index)}
                      onChange={() => {}}
                      className="mt-1 h-4 w-4 text-blue-600 rounded"
                  />
                  <div className="flex-grow">
                      <p className="font-bold text-gray-800">{lead.company || "Unknown Company"}</p>
                      <p className="text-sm text-gray-600">
                          {lead.name} • {lead.email || "No Email"} • {lead.phone || "No Phone"}
                      </p>
                      <p className="text-xs text-gray-400 mt-1">{lead.location}</p>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleQuickOutreach(lead);
                    }}
                    className="bg-green-100 text-green-700 px-3 py-1.5 rounded-lg text-xs font-bold hover:bg-green-200 flex items-center gap-1"
                  >
                    <HiPaperAirplane className="w-3.5 h-3.5 rotate-45" />
                    Outreach
                  </button>
                </div>
              ))}
              </div>

              <div className="flex gap-3">
                <button
                    onClick={handleManualConfirm}
                    className="flex-1 bg-green-600 text-white py-3 rounded-md hover:bg-green-700 font-bold shadow-lg"
                >
                    Confirm Selection ({selectedLeads.size})
                </button>
                <button
                    onClick={() => {
                        setIsTimerActive(false);
                        setResults(null);
                    }}
                    className="px-6 py-3 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 font-medium"
                >
                    Cancel
                </button>
              </div>
            </>
          )}
      </div>
    )}
  </div>
  );
};

export default SearchLeads;
