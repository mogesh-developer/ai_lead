import React, { useState } from 'react';
import api from '../api';

const WebSearch = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);

  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResults([]);
    try {
      const response = await api.post('/web-search', { query });
      setResults(response.data.results);
    } catch (error) {
      console.error("Web search failed", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto mt-10">
      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <h2 className="text-2xl font-bold mb-6">Web Search</h2>
        <form onSubmit={handleSearch} className="space-y-4">
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
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </form>
      </div>

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
