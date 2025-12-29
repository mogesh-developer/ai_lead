import React, { useState, useRef, useEffect } from 'react';
import api from '../api';

const BulkScrape = () => {
  const [urls, setUrls] = useState('');
  const [keyword, setKeyword] = useState('');
  const [mode, setMode] = useState('urls'); // 'urls' or 'keyword'
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState('');
  const terminalRef = useRef(null);

  // Auto-scroll terminal
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logs]);

  const addLog = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, { time: timestamp, message, type }]);
  };

  const handleScrape = async (e) => {
    e.preventDefault();
    if (mode === 'urls' && !urls.trim()) return;
    if (mode === 'keyword' && !keyword.trim()) return;

    setLoading(true);
    setResults([]);
    setLogs([]);
    setError('');
    
    if (mode === 'keyword') {
        addLog(`Searching for official sites matching: "${keyword}"...`, 'system');
        try {
            // Step 1: Search for URLs
            const searchResponse = await api.post('/web-search', { query: keyword });
            const searchResults = searchResponse.data.results;
            
            if (!searchResults || searchResults.length === 0) {
                addLog('No results found for this keyword.', 'warning');
                setLoading(false);
                return;
            }

            addLog(`Found ${searchResults.length} potential official sites. Starting scrape...`, 'info');
            
            // Step 2: Scrape each URL one by one
            for (let i = 0; i < searchResults.length; i++) {
                const site = searchResults[i];
                const url = site.href;
                
                addLog(`[${i+1}/${searchResults.length}] Scraping ${site.title || url}...`, 'info');
                
                try {
                    const response = await api.post('/bulk-scrape-simple', { urls: [url] });
                    const result = response.data.results[0];
                    
                    if (result.status === 'success') {
                        const emailCount = result.emails ? result.emails.length : 0;
                        const phoneCount = result.phones ? result.phones.length : 0;
                        
                        if (emailCount > 0 || phoneCount > 0) {
                            addLog(`✓ Success: Found ${emailCount} emails`, 'success');
                        } else {
                            addLog(`⚠ Warning: No contacts found`, 'warning');
                        }
                        setResults(prev => [...prev, result]);
                    } else {
                        addLog(`✗ Failed: ${result.error || result.status}`, 'error');
                        setResults(prev => [...prev, result]);
                    }
                } catch (err) {
                    addLog(`✗ Error scraping ${url}: ${err.message}`, 'error');
                }
            }
            
        } catch (err) {
            addLog(`✗ Error: ${err.message}`, 'error');
        }
    } else {
        // URL Mode
        const urlList = urls.split(/[\n,]+/).map(u => u.trim()).filter(u => u);
        addLog(`Starting scrape job for ${urlList.length} URLs...`, 'system');

        for (let i = 0; i < urlList.length; i++) {
            const url = urlList[i];
            addLog(`[${i+1}/${urlList.length}] Scraping ${url}...`, 'info');
            
            try {
                const response = await api.post('/bulk-scrape-simple', { urls: [url] });
                const result = response.data.results[0];
                
                if (result.status === 'success') {
                    const emailCount = result.emails ? result.emails.length : 0;
                    const phoneCount = result.phones ? result.phones.length : 0;
                    
                    if (emailCount > 0 || phoneCount > 0) {
                        addLog(`✓ Success: Found ${emailCount} emails, ${phoneCount} phones`, 'success');
                    } else {
                        addLog(`⚠ Warning: No contacts found on page`, 'warning');
                    }
                    setResults(prev => [...prev, result]);
                } else {
                    addLog(`✗ Failed: ${result.error}`, 'error');
                    setResults(prev => [...prev, result]);
                }
            } catch (err) {
                addLog(`✗ Error scraping ${url}: ${err.message}`, 'error');
            }
        }
    }
    
    addLog('Job completed.', 'system');
    setLoading(false);
  };

  const handleSaveLead = async (result) => {
    if (!result.emails || result.emails.length === 0) return;
    
    try {
        const leadData = {
            name: "Contact from " + result.title,
            email: result.emails[0],
            phone: result.phones && result.phones.length > 0 ? result.phones[0] : '',
            company: result.title,
            location: 'Unknown',
            source: 'bulk_scraper',
            status: 'new'
        };
        await api.post('/leads', leadData);
        addLog(`Saved lead: ${result.title}`, 'success');
        alert(`Saved lead: ${result.title}`);
    } catch (e) {
        alert("Failed to save lead: " + e.message);
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h2 className="text-2xl font-bold mb-6">Bulk Scraper (No AI)</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Input Section */}
        <div className="bg-white p-6 rounded-lg shadow-md h-full">
            <div className="flex space-x-4 mb-4 border-b pb-2">
                <button 
                    className={`pb-2 font-medium ${mode === 'urls' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}
                    onClick={() => setMode('urls')}
                >
                    Paste URLs
                </button>
                <button 
                    className={`pb-2 font-medium ${mode === 'keyword' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}
                    onClick={() => setMode('keyword')}
                >
                    Search Keyword
                </button>
            </div>

            <form onSubmit={handleScrape} className="flex flex-col h-full">
            {mode === 'urls' ? (
                <>
                    <p className="text-gray-600 mb-2 text-sm">Paste a list of website URLs below (one per line).</p>
                    <textarea
                        value={urls}
                        onChange={(e) => setUrls(e.target.value)}
                        className="w-full p-3 border rounded focus:ring-blue-500 focus:border-blue-500 flex-grow font-mono text-sm mb-4"
                        placeholder="example.com&#10;https://another-site.com"
                        style={{ minHeight: '200px' }}
                        required={mode === 'urls'}
                    />
                </>
            ) : (
                <>
                    <p className="text-gray-600 mb-2 text-sm">Enter a keyword (e.g., "Digital Marketing Agencies in Chennai"). We will find official websites and scrape them, skipping directories like 'Top 10' lists.</p>
                    <input
                        type="text"
                        value={keyword}
                        onChange={(e) => setKeyword(e.target.value)}
                        className="w-full p-3 border rounded focus:ring-blue-500 focus:border-blue-500 mb-4"
                        placeholder="e.g. Software Companies in Bangalore"
                        required={mode === 'keyword'}
                    />
                    <div className="flex-grow"></div>
                </>
            )}
            
            <div className="flex justify-end mt-4">
                <button
                type="submit"
                disabled={loading}
                className="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700 transition disabled:bg-green-400 w-full sm:w-auto"
                >
                {loading ? 'Processing...' : (mode === 'urls' ? 'Start Scraping' : 'Find & Scrape')}
                </button>
            </div>
            </form>
            {error && <p className="text-red-500 mt-2">{error}</p>}
        </div>

        {/* Terminal Output Section */}
        <div className="bg-black rounded-lg shadow-md p-4 font-mono text-sm h-full flex flex-col" style={{ minHeight: '300px', maxHeight: '500px' }}>
            <div className="flex justify-between items-center mb-2 border-b border-gray-700 pb-2">
                <span className="text-gray-400">Terminal Output</span>
                <span className="text-xs text-gray-500">{loading ? 'Running...' : 'Idle'}</span>
            </div>
            <div ref={terminalRef} className="overflow-y-auto flex-grow space-y-1">
                {logs.length === 0 && <div className="text-gray-600 italic">Waiting for input...</div>}
                {logs.map((log, idx) => (
                    <div key={idx} className={`${
                        log.type === 'error' ? 'text-red-400' : 
                        log.type === 'success' ? 'text-green-400' : 
                        log.type === 'warning' ? 'text-yellow-400' : 
                        log.type === 'system' ? 'text-blue-400' : 'text-gray-300'
                    }`}>
                        <span className="text-gray-600 mr-2">[{log.time}]</span>
                        {log.message}
                    </div>
                ))}
                {loading && <div className="text-gray-500 animate-pulse">_</div>}
            </div>
        </div>
      </div>

      {/* Results Table */}
      {results.length > 0 && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
            <h3 className="font-semibold text-gray-900">Scraping Results Table</h3>
          </div>
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Website</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Found Contacts</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {results.map((res, idx) => (
                <tr key={idx}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-600">
                    <a href={res.url} target="_blank" rel="noopener noreferrer" className="hover:underline">{res.url}</a>
                    <div className="text-xs text-gray-500">{res.title}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      res.status === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {res.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {res.emails && res.emails.length > 0 && (
                      <div className="mb-1">
                        <span className="font-semibold text-xs text-gray-400">Emails:</span>
                        <div className="text-gray-900">{res.emails.join(', ')}</div>
                      </div>
                    )}
                    {res.phones && res.phones.length > 0 && (
                      <div>
                        <span className="font-semibold text-xs text-gray-400">Phones:</span>
                        <div className="text-gray-900">{res.phones.join(', ')}</div>
                      </div>
                    )}
                    {(!res.emails?.length && !res.phones?.length) && <span className="text-gray-400">-</span>}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {res.emails && res.emails.length > 0 && (
                        <button 
                            onClick={() => handleSaveLead(res)}
                            className="text-blue-600 hover:text-blue-900 font-medium"
                        >
                            Save Lead
                        </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default BulkScrape;
