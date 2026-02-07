import React, { useState, useEffect } from 'react';
import api from '../api';

const Campaigns = () => {
  const [campaigns, setCampaigns] = useState([]);
  const [newCampaign, setNewCampaign] = useState({ name: '', description: '' });
  const [loading, setLoading] = useState(true);
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const [sequences, setSequences] = useState([]);
  const [newSequence, setNewSequence] = useState({ day_offset: 3, subject: '', body: '' });

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const fetchCampaigns = async () => {
    try {
      const response = await api.get('/campaigns');
      setCampaigns(response.data);
    } catch (error) {
      console.error("Error fetching campaigns", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSequences = async (campaignId) => {
    try {
      const response = await api.get(`/campaigns/${campaignId}/sequences`);
      setSequences(response.data);
    } catch (error) {
      console.error("Error fetching sequences", error);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!newCampaign.name) return;

    try {
      await api.post('/campaigns', newCampaign);
      setNewCampaign({ name: '', description: '' });
      fetchCampaigns();
    } catch (error) {
      console.error("Error creating campaign", error);
    }
  };

  const handleAddSequence = async (e) => {
    e.preventDefault();
    if (!selectedCampaign || !newSequence.subject || !newSequence.body) return;

    try {
      await api.post(`/campaigns/${selectedCampaign.id}/sequences`, newSequence);
      setNewSequence({ day_offset: 3, subject: '', body: '' });
      fetchSequences(selectedCampaign.id);
    } catch (error) {
      console.error("Error adding sequence", error);
    }
  };

  const selectCampaign = (campaign) => {
    setSelectedCampaign(campaign);
    fetchSequences(campaign.id);
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-6">Campaign Management</h2>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Campaign List & Create */}
        <div className="lg:col-span-1 space-y-6">
          {/* Create Campaign Form */}
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-4">Create New Campaign</h3>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Campaign Name</label>
                <input
                  type="text"
                  value={newCampaign.name}
                  onChange={(e) => setNewCampaign({ ...newCampaign, name: e.target.value })}
                  className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
                  placeholder="e.g. Bangalore Tech Startups"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <input
                  type="text"
                  value={newCampaign.description}
                  onChange={(e) => setNewCampaign({ ...newCampaign, description: e.target.value })}
                  className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Optional description"
                />
              </div>
              <button
                type="submit"
                className="w-full bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition"
              >
                Create Campaign
              </button>
            </form>
          </div>

          {/* Campaigns List */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
              <h3 className="text-lg font-semibold text-gray-900">Your Campaigns</h3>
            </div>
            <ul className="divide-y divide-gray-200 max-h-[600px] overflow-y-auto">
              {loading ? (
                <li className="px-6 py-4 text-center">Loading...</li>
              ) : campaigns.length === 0 ? (
                <li className="px-6 py-4 text-center text-gray-500">No campaigns found.</li>
              ) : (
                campaigns.map((campaign) => (
                  <li 
                    key={campaign.id} 
                    onClick={() => selectCampaign(campaign)}
                    className={`px-6 py-4 cursor-pointer hover:bg-blue-50 transition ${selectedCampaign?.id === campaign.id ? 'bg-blue-50 border-l-4 border-blue-600' : ''}`}
                  >
                    <div className="font-medium text-gray-900">{campaign.name}</div>
                    <div className="text-sm text-gray-500">{campaign.description}</div>
                    <div className="text-xs text-gray-400 mt-1">{new Date(campaign.created_at).toLocaleDateString()}</div>
                  </li>
                ))
              )}
            </ul>
          </div>
        </div>

        {/* Right Column: Sequence Editor */}
        <div className="lg:col-span-2">
          {selectedCampaign ? (
            <div className="bg-white rounded-lg shadow-md h-full flex flex-col">
              <div className="px-6 py-4 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
                <div>
                  <h3 className="text-xl font-bold text-gray-900">{selectedCampaign.name}</h3>
                  <p className="text-sm text-gray-500">Email Drip Sequences</p>
                </div>
                <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded">
                  {sequences.length} Steps
                </span>
              </div>
              
              <div className="p-6 flex-grow overflow-y-auto space-y-6">
                {/* Existing Sequences */}
                {sequences.length === 0 ? (
                  <div className="text-center py-10 text-gray-500 border-2 border-dashed border-gray-200 rounded-lg">
                    <p>No follow-up sequences configured.</p>
                    <p className="text-sm">Add a step below to start automating follow-ups.</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {sequences.map((seq, index) => (
                      <div key={seq.id} className="border border-gray-200 rounded-lg p-4 relative">
                        <div className="absolute top-4 right-4 bg-gray-100 text-gray-600 text-xs font-bold px-2 py-1 rounded">
                          Step {index + 1}
                        </div>
                        <h4 className="font-bold text-blue-600 mb-1">
                          Wait {seq.day_offset} days after previous email
                        </h4>
                        <div className="mb-2">
                          <span className="text-xs font-semibold text-gray-500 uppercase">Subject:</span>
                          <p className="text-sm font-medium">{seq.template_subject}</p>
                        </div>
                        <div>
                          <span className="text-xs font-semibold text-gray-500 uppercase">Body:</span>
                          <p className="text-sm text-gray-600 whitespace-pre-wrap bg-gray-50 p-2 rounded mt-1">{seq.template_body}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Add New Sequence Form */}
                <div className="border-t border-gray-200 pt-6 mt-6">
                  <h4 className="text-lg font-semibold mb-4">Add Follow-up Step</h4>
                  <form onSubmit={handleAddSequence} className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Wait Days (after previous email)
                      </label>
                      <input
                        type="number"
                        min="1"
                        value={newSequence.day_offset}
                        onChange={(e) => setNewSequence({ ...newSequence, day_offset: parseInt(e.target.value) })}
                        className="w-32 p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Email Subject</label>
                      <input
                        type="text"
                        value={newSequence.subject}
                        onChange={(e) => setNewSequence({ ...newSequence, subject: e.target.value })}
                        className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
                        placeholder="e.g. Following up on my previous email"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Email Body <span className="text-xs text-gray-500 font-normal">(Use {'{name}'} and {'{company}'} as placeholders)</span>
                      </label>
                      <textarea
                        value={newSequence.body}
                        onChange={(e) => setNewSequence({ ...newSequence, body: e.target.value })}
                        className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500 h-32"
                        placeholder="Hi {name}, just wanted to bump this to the top of your inbox..."
                        required
                      />
                    </div>
                    <button
                      type="submit"
                      className="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700 transition"
                    >
                      Add Sequence Step
                    </button>
                  </form>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 h-full flex items-center justify-center text-gray-500">
              Select a campaign to manage its sequences
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Campaigns;
