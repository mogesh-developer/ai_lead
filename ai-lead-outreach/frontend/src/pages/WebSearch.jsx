import React, { useState, useRef, useEffect } from 'react';
import api from '../api';

const WebSearch = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [logs, setLogs] = useState([]);
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

  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResults([]);
    setLogs([]);
    
    addLog(`Initiating web search for: "${query}"`, 'system');
    
    try {
      addLog('Sending request to search engine...', 'info');
      const response = await api.post('/web-search', { query });
      const searchResults = response.data.results;
      
      setResults(searchResults);
      
      if (searchResults.length > 0) {
        addLog(`Success: Found ${searchResults.length} results.`, 'success');
        searchResults.forEach((res, idx) => {
            addLog(`[${idx+1}] ${res.title} - ${res.href}`, 'info');
        });
      } else {
        addLog('No results found.', 'warning');
      }
      
    } catch (error) {
      console.error("Web search failed", error);
      addLog(`Error: ${error.message}`, 'error');
    } finally {
      setLoading(false);
      addLog('Search completed.', 'system');
    }
  };

  return (
    <div className="max-w-6xl mx-auto mt-10 p-6">
      <h2 className="text-2xl font-bold mb-6">AI Discovery (Web Search)</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Input Section */}
        <div className="bg-white p-6 rounded-lg shadow-md h-full">
            <h3 className="text-lg font-semibold mb-4">Search Parameters</h3>
            <form onSubmit={handleSearch} className="space-y-4 flex flex-col h-full">
            <div>
                <label className="block text-sm font-medium text-gray-700">Search Query</label>
                <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g. Best pizza in New York"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2"
                required
                />
            </div>
            <div className="flex-grow"></div>
            <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 mt-4"
            >
                {loading ? 'Searching...' : 'Search'}
            </button>
            </form>
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
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Search Results</h3>
          <div className="space-y-4">
            {results.map((result, index) => (
              <div key={index} className="border-b pb-2 last:border-0">
                <a href={result.href} target="_blank" rel="noopener noreferrer" className="text-xl font-medium text-blue-600 hover:underline">
                  {result.title}
                </a>
                <p className="text-sm text-gray-600">{result.href}</p>
                <p className="text-gray-700 mt-1">{result.body}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default WebSearch;
