import React, { useState } from 'react';
import api from '../api';

const WebSearch = () => {
  const [query, setQuery] = useState('');
  const [advanced, setAdvanced] = useState({ 
    site: '', 
    filetype: '', 
    exactPhrase: '', 
    anyWords: '', 
    noneWords: '' 
  });
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [selectedResults, setSelectedResults] = useState([]);
  
  // AI Extraction state
  const [pasteText, setPasteText] = useState('');
  const [extracting, setExtracting] = useState(false);
  const [extractedLeads, setExtractedLeads] = useState([]);
  const [message, setMessage] = useState('');
  const [verifying, setVerifying] = useState({});

  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResults([]);
    setSelectedResults([]);
    try {
      const response = await api.post('/web-search', { query, advanced });
      setResults(response.data.results);
    } catch (error) {
      console.error("Web search failed", error);
    } finally {
      setLoading(false);
    }
  };

  const toggleSelectAll = () => {
    if (selectedResults.length === results.length) {
      setSelectedResults([]);
    } else {
      setSelectedResults(results.map((_, i) => i));
    }
  };

  const toggleSelect = (index) => {
    if (selectedResults.includes(index)) {
      setSelectedResults(selectedResults.filter(i => i !== index));
    } else {
      setSelectedResults([...selectedResults, index]);
    }
  };

  const copyToClipboard = () => {
    const textToCopy = results
      .filter((_, i) => selectedResults.includes(i))
      .map(r => `${r.title}\n${r.href}\n${r.body}\n`)
      .join('\n---\n\n');
    
    navigator.clipboard.writeText(textToCopy);
    alert('Copied to clipboard!');
  };

  const handleAIExtract = async () => {
    if (!pasteText) return;
    setExtracting(true);
    setMessage('');
    try {
      const response = await api.post('/ai-extract', { text: pasteText });
      setExtractedLeads(response.data.leads);
      setMessage(response.data.message);
    } catch (error) {
      console.error("AI Extraction failed", error);
      setMessage("Extraction failed. Check your Gemini API key.");
    } finally {
      setExtracting(false);
    }
  };

  const handleAIClean = async () => {
    const selectedData = results.filter((_, i) => selectedResults.includes(i));
    if (selectedData.length === 0) return;
    
    setExtracting(true);
    setMessage('');
    try {
      const response = await api.post('/clean-search-results', { results: selectedData });
      setExtractedLeads(response.data.leads);
      setMessage(`AI cleaned ${response.data.leads.length} leads from your search results.`);
    } catch (error) {
      console.error("AI Cleaning failed", error);
      setMessage("Cleaning failed. Check your Gemini API key.");
    } finally {
      setExtracting(false);
    }
  };

  const handleSaveLeads = async () => {
    if (extractedLeads.length === 0) return;
    setLoading(true);
    try {
      const response = await api.post('/save-extracted-leads', { leads: extractedLeads });
      setMessage(response.data.message);
    } catch (error) {
      console.error("Saving leads failed", error);
      setMessage("Failed to save leads to database.");
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyEmail = async (email, index) => {
    if (!email || email === 'null') return;
    setVerifying(prev => ({ ...prev, [index]: true }));
    try {
      const response = await api.post('/verify-email', { email });
      const result = response.data;
      
      // Update the extracted lead with verification info
      const updatedLeads = [...extractedLeads];
      updatedLeads[index] = { 
        ...updatedLeads[index], 
        verification: result 
      };
      setExtractedLeads(updatedLeads);
    } catch (error) {
      console.error("Email verification failed", error);
    } finally {
      setVerifying(prev => ({ ...prev, [index]: false }));
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-6xl mx-auto space-y-8 pb-20">
        {/* Search Section */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-xl p-8">
          <div className="mb-8">
            <h2 className="text-4xl font-bold text-white mb-2 flex items-center">
              <span className="w-2 h-8 bg-gradient-to-b from-blue-400 to-purple-400 rounded mr-3"></span>
              Advanced Web Search
            </h2>
            <p className="text-slate-300">Search the web and let AI extract qualified leads for you</p>
          </div>
          <form onSubmit={handleSearch} className="space-y-6">
            <div>
              <label className="block text-sm font-semibold text-slate-200 mb-3">Search Query</label>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g. Marketing agencies in London, SaaS companies in USA"
                className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-400/20"
                required
              />
            </div>

            <button 
              type="button" 
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="text-sm text-blue-400 hover:text-blue-300 font-medium transition-colors"
            >
              {showAdvanced ? '▼ Hide Advanced Options' : '▶ Show Advanced Options'}
            </button>

            {showAdvanced && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-6 bg-slate-700/50 rounded-lg">
                <div className="md:col-span-2">
                  <label className="block text-xs font-semibold text-slate-300 mb-2">This exact word or phrase:</label>
                  <input
                    type="text"
                    value={advanced.exactPhrase}
                    onChange={(e) => setAdvanced({...advanced, exactPhrase: e.target.value})}
                    placeholder='e.g. "gmail.com"'
                    className="w-full px-3 py-2 bg-slate-600 border border-slate-500 rounded text-white placeholder-slate-400 text-sm focus:outline-none focus:border-blue-400"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-2">Any of these words:</label>
                  <input
                    type="text"
                    value={advanced.anyWords}
                    onChange={(e) => setAdvanced({...advanced, anyWords: e.target.value})}
                    placeholder="e.g. marketing OR sales"
                    className="w-full px-3 py-2 bg-slate-600 border border-slate-500 rounded text-white placeholder-slate-400 text-sm focus:outline-none focus:border-blue-400"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-2">None of these words:</label>
                  <input
                    type="text"
                    value={advanced.noneWords}
                    onChange={(e) => setAdvanced({...advanced, noneWords: e.target.value})}
                    placeholder="e.g. -jobs -hiring"
                    className="w-full px-3 py-2 bg-slate-600 border border-slate-500 rounded text-white placeholder-slate-400 text-sm focus:outline-none focus:border-blue-400"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-2">Site or domain:</label>
                  <input
                    type="text"
                    value={advanced.site}
                    onChange={(e) => setAdvanced({...advanced, site: e.target.value})}
                    placeholder="e.g. linkedin.com"
                    className="w-full px-3 py-2 bg-slate-600 border border-slate-500 rounded text-white placeholder-slate-400 text-sm focus:outline-none focus:border-blue-400"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-2">Filetype:</label>
                  <input
                    type="text"
                    value={advanced.filetype}
                    onChange={(e) => setAdvanced({...advanced, filetype: e.target.value})}
                    placeholder="e.g. pdf, xlsx"
                    className="w-full px-3 py-2 bg-slate-600 border border-slate-500 rounded text-white placeholder-slate-400 text-sm focus:outline-none focus:border-blue-400"
                  />
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 disabled:from-slate-600 disabled:to-slate-600 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 shadow-lg"
            >
              {loading ? 'Searching...' : 'Search'}
            </button>
          </form>
        </div>

        {/* Results Section */}
        {results.length > 0 && (
          <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-xl p-8">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
              <h3 className="text-2xl font-bold text-white">Search Results ({results.length})</h3>
              <div className="flex flex-wrap gap-2">
                <button 
                  onClick={toggleSelectAll}
                  className="text-sm bg-slate-700 hover:bg-slate-600 px-3 py-2 rounded-lg text-slate-200 transition-colors"
                >
                  {selectedResults.length === results.length ? 'Deselect All' : 'Select All'}
                </button>
                <button 
                  onClick={copyToClipboard}
                  disabled={selectedResults.length === 0}
                  className="text-sm bg-green-600 hover:bg-green-700 disabled:bg-slate-600 text-white px-3 py-2 rounded-lg transition-colors disabled:cursor-not-allowed"
                >
                  Copy Selected
                </button>
                <button 
                  onClick={handleAIClean}
                  disabled={selectedResults.length === 0 || extracting}
                  className="text-sm bg-purple-600 hover:bg-purple-700 disabled:bg-slate-600 text-white px-3 py-2 rounded-lg transition-colors disabled:cursor-not-allowed"
                >
                  {extracting ? 'Cleaning...' : 'Clean with AI'}
                </button>
              </div>
            </div>
            
            <div className="space-y-4">
              {results.map((result, index) => (
                <div key={index} className="flex items-start space-x-4 border-b border-slate-700 pb-4 last:border-0">
                  <input 
                    type="checkbox" 
                    checked={selectedResults.includes(index)}
                    onChange={() => toggleSelect(index)}
                    className="mt-2 rounded border-slate-600 bg-slate-700 accent-blue-500 cursor-pointer"
                  />
                  <div className="flex-grow">
                    <a href={result.href} target="_blank" rel="noopener noreferrer" className="text-lg font-semibold text-blue-400 hover:text-blue-300 transition-colors">
                      {result.title}
                    </a>
                    <p className="text-xs text-slate-400 mt-1 truncate">{result.href}</p>
                    <p className="text-slate-300 mt-2 text-sm">{result.body}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* AI Extraction Section */}
        <div className="bg-slate-800 border border-blue-600/30 rounded-xl shadow-xl p-8">
          <h2 className="text-2xl font-bold text-white mb-2 flex items-center">
            <span className="w-2 h-6 bg-gradient-to-b from-blue-400 to-purple-400 rounded mr-3"></span>
            AI Paste & Extract
          </h2>
          <p className="text-slate-300 mb-6">Paste messy search results or text. AI will clean and extract leads into your database.</p>
          
          <textarea
            value={pasteText}
            onChange={(e) => setPasteText(e.target.value)}
            placeholder="Paste your copied results here..."
            className="w-full h-40 p-4 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-400/20 mb-4"
          />
          
          <button
            onClick={handleAIExtract}
            disabled={extracting || !pasteText}
            className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 disabled:from-slate-600 disabled:to-slate-600 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 shadow-lg"
          >
            {extracting ? 'AI is cleaning and extracting...' : 'Clean & Extract Leads with AI'}
          </button>

          {message && (
            <div className="mt-4 p-4 bg-green-900/20 border border-green-700 text-green-300 rounded-lg text-sm">
              {message}
            </div>
          )}

          {extractedLeads.length > 0 && (
            <div className="mt-8 space-y-6">
              <div className="flex justify-between items-center">
                <h3 className="text-xl font-bold text-white">Extracted Leads ({extractedLeads.length})</h3>
                <button
                  onClick={handleSaveLeads}
                  disabled={loading}
                  className="bg-green-600 hover:bg-green-700 disabled:bg-slate-600 text-white py-2 px-6 rounded-lg font-semibold text-sm transition-colors disabled:cursor-not-allowed"
                >
                  {loading ? 'Saving...' : 'Save All to Database'}
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-slate-700/50 border-b border-slate-700">
                      <th className="px-4 py-3 text-left font-semibold text-slate-200">Company</th>
                      <th className="px-4 py-3 text-left font-semibold text-slate-200">Website</th>
                      <th className="px-4 py-3 text-left font-semibold text-slate-200">Email</th>
                      <th className="px-4 py-3 text-left font-semibold text-slate-200">Phone</th>
                      <th className="px-4 py-3 text-left font-semibold text-slate-200">Confidence</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-700">
                    {extractedLeads.map((lead, i) => (
                      <tr key={i} className="hover:bg-slate-700/30 transition-colors">
                        <td className="px-4 py-3 font-medium text-white">{lead.company_name || lead.company}</td>
                        <td className="px-4 py-3 text-blue-400 truncate max-w-xs">
                          <a href={lead.official_website || lead.website} target="_blank" rel="noopener noreferrer" className="hover:text-blue-300">
                            {lead.official_website || lead.website}
                          </a>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center space-x-2">
                            <span className="text-slate-300">{lead.email || 'N/A'}</span>
                            {lead.email && lead.email !== 'null' && (
                              <button
                                onClick={() => handleVerifyEmail(lead.email, i)}
                                disabled={verifying[i]}
                                className={`text-[10px] px-2 py-1 rounded font-medium transition-colors ${
                                  lead.verification 
                                    ? (lead.verification.valid ? 'bg-green-500/20 text-green-300' : 'bg-red-500/20 text-red-300')
                                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                                }`}
                              >
                                {verifying[i] ? '...' : lead.verification ? (lead.verification.valid ? 'Valid' : 'Invalid') : 'Verify'}
                              </button>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-slate-300">{lead.phone_number || lead.phone || 'N/A'}</td>
                        <td className="px-4 py-3">
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                            lead.confidence_score === 'High' ? 'bg-green-500/20 text-green-300' : 
                            lead.confidence_score === 'Medium' ? 'bg-yellow-500/20 text-yellow-300' : 
                            'bg-red-500/20 text-red-300'
                          }`}>
                            {lead.confidence_score || 'N/A'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WebSearch;
