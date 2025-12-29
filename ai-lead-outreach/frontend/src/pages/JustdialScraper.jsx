import React, { useState } from 'react';
import api from '../api';

const JustdialScraper = () => {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [leads, setLeads] = useState([]);
  const [error, setError] = useState('');

  const handleScrape = async (e) => {
    e.preventDefault();
    if (!url.trim()) return;

    setLoading(true);
    setLeads([]);
    setError('');

    try {
      const response = await api.post('/scrape-justdial', { url });
      setLeads(response.data.leads);
      if (response.data.leads.length === 0) {
        setError("No leads found. Please check the URL or try a different category.");
      }
    } catch (err) {
      console.error("Scraping failed", err);
      setError("Failed to scrape Justdial. " + (err.response?.data?.error || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleSaveLead = async (lead) => {
    try {
        const leadData = {
            name: lead.company,
            email: lead.email || '', // Justdial rarely shows emails directly
            phone: lead.phone,
            company: lead.company,
            location: lead.address,
            source: 'justdial_scraper',
            status: 'new',
            notes: `Rating: ${lead.rating} | Source: Justdial`
        };
        await api.post('/leads', leadData);
        alert(`Saved lead: ${lead.company}`);
    } catch (e) {
        alert("Failed to save lead: " + e.message);
    }
  };

  const handleSaveAll = async () => {
      let count = 0;
      for (const lead of leads) {
          try {
            const leadData = {
                name: lead.company,
                email: lead.email || '',
                phone: lead.phone,
                company: lead.company,
                location: lead.address,
                source: 'justdial_scraper',
                status: 'new',
                notes: `Rating: ${lead.rating} | Source: Justdial`
            };
            await api.post('/leads', leadData);
            count++;
          } catch (e) {
              console.error("Failed to save", lead.company);
          }
      }
      alert(`Saved ${count} leads successfully!`);
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h2 className="text-2xl font-bold mb-6 text-orange-600">Justdial Power Scraper</h2>
      
      <div className="bg-white p-6 rounded-lg shadow-md mb-8">
        <p className="text-gray-600 mb-4">
          Enter a Justdial category URL (e.g., <code>https://www.justdial.com/Chennai/Nursery-Gardens</code>). 
          The system will use advanced browser automation to extract business details.
        </p>
        <form onSubmit={handleScrape} className="flex gap-4">
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className="flex-grow p-3 border rounded focus:ring-orange-500 focus:border-orange-500"
            placeholder="https://www.justdial.com/City/Category"
            required
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-orange-600 text-white px-6 py-3 rounded hover:bg-orange-700 transition disabled:bg-orange-400 font-semibold"
          >
            {loading ? 'Scraping (this takes time)...' : 'Start Scraping'}
          </button>
        </form>
        {error && <p className="text-red-500 mt-2">{error}</p>}
      </div>

      {leads.length > 0 && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
            <h3 className="font-semibold text-gray-900">Found {leads.length} Businesses</h3>
            <button 
                onClick={handleSaveAll}
                className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700"
            >
                Save All Leads
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Company</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rating</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Phone</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Address</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                {leads.map((lead, idx) => (
                    <tr key={idx}>
                    <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                            {lead.image && (
                                <img src={lead.image} alt="" className="h-10 w-10 rounded-full mr-3 object-cover" />
                            )}
                            <div>
                                <div className="text-sm font-medium text-gray-900">{lead.company}</div>
                            </div>
                        </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                        <span className="px-2 py-1 text-xs font-bold rounded bg-green-100 text-green-800">
                        {lead.rating} ★
                        </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {lead.phone}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate" title={lead.address}>
                        {lead.address}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <button 
                            onClick={() => handleSaveLead(lead)}
                            className="text-blue-600 hover:text-blue-900 font-medium"
                        >
                            Save
                        </button>
                    </td>
                    </tr>
                ))}
                </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default JustdialScraper;
