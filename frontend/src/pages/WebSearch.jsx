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
  const [resultsPerPage, setResultsPerPage] = useState(10);
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
      const serverError = error.response?.data?.error || error.message || 'Cleaning failed';
      const details = error.response?.data?.details;
      const hint = error.response?.data?.hint;
      let msg = serverError;
      if (details) msg += `: ${details}`;
      if (hint) msg += ` — ${hint}`;
      setMessage(msg);
    } finally {
      setExtracting(false);
    }
  };

  const handleSaveLeads = async () => {
    if (extractedLeads.length === 0) return;
    setLoading(true);
    try {
      const response = await api.post('/save-extracted-leads', { leads: extractedLeads });
      console.log("Save response:", response.data);
      console.log("Full response object:", JSON.stringify(response.data, null, 2));
      
      const saved = response.data.saved || 0;
      const failed = response.data.failed || 0;
      const failedLeads = response.data.failed_leads || [];
      const errors = response.data.errors || [];
      
      console.log("Saved count:", saved);
      console.log("Failed count:", failed);
      console.log("Failed leads:", failedLeads);
      console.log("Error messages:", errors);
      
      // Build detailed message
      let messageText = `✓ Saved ${saved}/${extractedLeads.length} leads`;
      
      if (failed > 0) {
        messageText += `\n\n❌ ${failed} lead(s) failed:\n`;
        const leadsToShow = failedLeads && failedLeads.length > 0 ? failedLeads : errors;
        
        if (Array.isArray(leadsToShow)) {
          leadsToShow.slice(0, 5).forEach((item, idx) => {
            if (item.name && item.email) {
              // It's a failed_leads object
              messageText += `• ${item.name} (${item.email})\n  Reason: ${item.reason}\n`;
            } else {
              // It's an error string
              messageText += `• ${item}\n`;
            }
          });
          if (leadsToShow.length > 5) {
            messageText += `• ... and ${leadsToShow.length - 5} more\n`;
          }
        }
      }
      
      setMessage(messageText);
      
      // Show detailed error modal if there are failures
      if (failed > 0) {
        console.warn("Failed leads details:", failedLeads);
        console.warn("Error details:", errors);
        alert(`Saved ${saved} leads successfully!\n\nFailed: ${failed} leads\n\nCheck console (F12) for details.`);
      }
      
      // Clear extracted leads after save
      if (saved > 0) {
        setTimeout(() => {
          setExtractedLeads([]);
          if (failed === 0) {
            setMessage(`✓ All ${saved} leads saved successfully!`);
          }
        }, 1500);
      }
    } catch (error) {
      console.error("Saving leads failed", error);
      console.error("Error response:", error.response?.data);
      const errorMsg = error.response?.data?.error || error.message || "Failed to save leads to database.";
      setMessage(`✗ Error: ${errorMsg}`);
      alert(`Error saving leads:\n${errorMsg}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveWithoutCleanup = async () => {
    if (extractedLeads.length === 0) return;
    setLoading(true);
    try {
      const response = await api.post('/save-extracted-leads-no-validation', { leads: extractedLeads });
      console.log("Save (no validation) response:", response.data);
      
      const saved = response.data.saved || 0;
      const failed = response.data.failed || 0;
      
      const messageText = `✓ Saved ${saved}/${extractedLeads.length} leads (without validation)`;
      setMessage(messageText);
      
      if (failed > 0) {
        alert(`Saved ${saved} leads successfully!\n\nNote: ${failed} lead(s) had issues (duplicates or database constraints).`);
      }
      
      // Clear extracted leads after save
      if (saved > 0) {
        setTimeout(() => {
          setExtractedLeads([]);
        }, 1500);
      }
    } catch (error) {
      console.error("Saving leads (no validation) failed", error);
      const errorMsg = error.response?.data?.error || error.message || "Failed to save leads to database.";
      setMessage(`✗ Error: ${errorMsg}`);
      alert(`Error saving leads:\n${errorMsg}`);
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
    <div className="space-y-8 max-w-6xl mx-auto pb-20">
      {/* Header */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
        <div className="flex justify-between items-center mb-2">
          <h2 className="text-3xl font-extrabold text-gray-900 tracking-tight flex items-center gap-3">
            <div className="bg-blue-600 p-2 rounded-xl text-white">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
            </div>
            AI Advanced Discovery
          </h2>
        </div>
        <p className="text-gray-500 font-medium">Search the web and let AI extract qualified leads for you with precision.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left: Search Configuration */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <h3 className="text-sm font-bold text-gray-400 mb-6 uppercase tracking-widest">Search Configuration</h3>
            <form onSubmit={handleSearch} className="space-y-5">
              <div>
                <label className="block text-xs font-bold text-gray-600 uppercase mb-2">Main Query</label>
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="e.g. Roofers in Miami"
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>

              <div className="pt-2">
                <button 
                  type="button" 
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="flex items-center gap-2 text-xs font-bold text-blue-600 hover:text-blue-800 transition-colors uppercase"
                >
                  {showAdvanced ? 'Hide Advanced Settings' : 'Show Advanced Settings'}
                  <svg className={`w-4 h-4 transition-transform ${showAdvanced ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                </button>
              </div>

              {showAdvanced && (
                <div className="space-y-4 pt-2 animate-fade-in">
                  <div>
                    <label className="block text-[10px] font-bold text-gray-400 uppercase mb-1">Exact Phrase</label>
                    <input
                      type="text"
                      value={advanced.exactPhrase}
                      onChange={(e) => setAdvanced({...advanced, exactPhrase: e.target.value})}
                      placeholder='"gmail.com"'
                      className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-gray-400 uppercase mb-1">Exclude Words</label>
                    <input
                      type="text"
                      value={advanced.noneWords}
                      onChange={(e) => setAdvanced({...advanced, noneWords: e.target.value})}
                      placeholder="-jobs -hiring"
                      className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-gray-400 uppercase mb-1">Target Site</label>
                    <input
                      type="text"
                      value={advanced.site}
                      onChange={(e) => setAdvanced({...advanced, site: e.target.value})}
                      placeholder="linkedin.com"
                      className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm"
                    />
                  </div>
                </div>
              )}

              <div className="flex items-center justify-between pt-4">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-gray-400 uppercase">Limit</span>
                  <select
                    value={resultsPerPage}
                    onChange={(e) => setResultsPerPage(parseInt(e.target.value))}
                    className="bg-gray-100 border-none rounded-lg text-xs font-bold py-1 px-2"
                  >
                    {[5, 10, 15, 20, 50].map(v => <option key={v} value={v}>{v}</option>)}
                  </select>
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-200 text-white font-bold py-3 px-6 rounded-xl transition-all shadow-lg shadow-blue-200 flex items-center gap-2"
                >
                  {loading ? 'Searching...' : 'Search'}
                </button>
              </div>
            </form>
          </div>

          <div className="bg-gradient-to-br from-indigo-900 to-blue-900 rounded-2xl shadow-xl p-6 text-white">
            <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
              <svg className="w-5 h-5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>
              AI Magic Paste
            </h3>
            <p className="text-blue-100 text-sm mb-4 leading-relaxed">Have messy results from somewhere else? Paste them here and let AI structure them into valid leads.</p>
            <textarea
              value={pasteText}
              onChange={(e) => setPasteText(e.target.value)}
              placeholder="Paste content here..."
              className="w-full h-32 p-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-blue-300/50 text-sm focus:ring-blue-400 focus:border-transparent mb-4"
            />
            <button
              onClick={handleAIExtract}
              disabled={extracting || !pasteText}
              className="w-full bg-white text-blue-900 hover:bg-blue-50 disabled:bg-white/20 disabled:text-blue-300 font-bold py-3 rounded-xl transition-all shadow-lg"
            >
              {extracting ? 'Processing...' : 'Run Extraction'}
            </button>
          </div>
        </div>

        {/* Right: Results Display */}
        <div className="lg:col-span-2 space-y-6">
          {results.length > 0 && (
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-extrabold text-gray-900">Search Results</h3>
                <div className="flex gap-2">
                  <button 
                    onClick={copyToClipboard}
                    disabled={selectedResults.length === 0}
                    className="text-xs font-bold bg-gray-100 text-gray-600 px-4 py-2 rounded-lg hover:bg-gray-200 disabled:opacity-50"
                  >
                    Copy
                  </button>
                  <button 
                    onClick={handleAIClean}
                    disabled={selectedResults.length === 0 || extracting}
                    className="text-xs font-bold bg-blue-50 text-blue-700 px-4 py-2 rounded-lg hover:bg-blue-100 disabled:opacity-50"
                  >
                    AI Clean Selected
                  </button>
                </div>
              </div>

              <div className="space-y-4">
                {results.map((result, index) => (
                  <div key={index} className="flex items-start gap-4 p-4 rounded-xl hover:bg-gray-50 transition-colors border border-transparent hover:border-gray-100 group">
                    <input 
                      type="checkbox" 
                      checked={selectedResults.includes(index)}
                      onChange={() => toggleSelect(index)}
                      className="mt-1.5 w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <div className="flex-grow">
                      <a href={result.href} target="_blank" rel="noopener noreferrer" className="block text-base font-bold text-gray-900 group-hover:text-blue-600 transition-colors">
                        {result.title}
                      </a>
                      <p className="text-[10px] text-gray-400 mt-0.5 truncate max-w-md">{result.href}</p>
                      <p className="text-sm text-gray-600 mt-2 leading-relaxed">{result.body}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {extractedLeads.length > 0 && (
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
              <div className="px-8 py-5 border-b border-gray-50 flex justify-between items-center bg-gray-50/50">
                <h3 className="text-lg font-bold text-gray-900">Qualified Leads Found</h3>
                <div className="flex gap-2">
                  <button
                    onClick={handleSaveLeads}
                    disabled={loading}
                    className="bg-green-600 hover:bg-green-700 text-white py-2 px-6 rounded-xl font-bold text-xs shadow-lg shadow-green-100"
                  >
                    {loading ? 'Saving...' : 'Add to Database'}
                  </button>
                </div>
              </div>
              <div className="p-0 overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="bg-gray-50/50 border-b border-gray-100">
                      <th className="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase">Company</th>
                      <th className="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase">Email</th>
                      <th className="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase">Confidence</th>
                      <th className="px-6 py-4 text-[10px] font-bold text-gray-400 uppercase">Verify</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {extractedLeads.map((lead, i) => (
                      <tr key={i} className="hover:bg-blue-50/30 transition-colors">
                        <td className="px-6 py-4">
                          <p className="font-bold text-gray-900 text-sm">{lead.company_name || lead.company || 'N/A'}</p>
                          <p className="text-[10px] text-gray-400 truncate max-w-[150px]">{lead.official_website || lead.website || 'N/A'}</p>
                        </td>
                        <td className="px-6 py-4">
                          <p className="text-sm text-gray-600">{lead.email || 'N/A'}</p>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase ${
                            (lead.confidence_score === 'High' || lead.confidence >= 80) ? 'bg-green-100 text-green-700' : 
                            (lead.confidence_score === 'Medium' || lead.confidence >= 50) ? 'bg-yellow-100 text-yellow-700' : 
                            'bg-red-100 text-red-700'
                          }`}>
                            {lead.confidence_score || (lead.confidence ? `${lead.confidence}%` : 'N/A')}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          {lead.email && lead.email !== 'null' && (
                            <button
                              onClick={() => handleVerifyEmail(lead.email, i)}
                              disabled={verifying[i]}
                              className={`text-[10px] font-bold py-1 px-3 rounded-lg border transition-all ${
                                lead.verification 
                                  ? (lead.verification.valid ? 'bg-green-600 border-green-600 text-white' : 'bg-red-600 border-red-600 text-white')
                                  : 'bg-white border-gray-200 text-gray-600 hover:border-blue-300 hover:text-blue-600'
                              }`}
                            >
                              {verifying[i] ? '...' : lead.verification ? (lead.verification.valid ? 'Valid' : 'Invalid') : 'Verify'}
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {message && (
            <div className={`p-4 rounded-xl border text-sm font-medium animate-fade-in ${
              message.includes('Error') || message.includes('failed') ? 'bg-red-50 border-red-100 text-red-700' : 'bg-green-50 border-green-100 text-green-700'
            }`}>
              {message}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WebSearch;
